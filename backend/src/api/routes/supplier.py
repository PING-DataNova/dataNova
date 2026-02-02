"""
Routes API pour l'analyse de fournisseurs (Agent 1A - Scénario 2)
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import asyncio
import structlog

from src.storage.database import SessionLocal
from src.storage.models import SupplierAnalysis
from src.agent_1a.agent import run_agent_1a_for_supplier

logger = structlog.get_logger()

router = APIRouter(prefix="/supplier", tags=["Supplier Analysis"])


# ============================================================================
# SCHEMAS PYDANTIC
# ============================================================================

class SupplierAnalysisRequest(BaseModel):
    """Requête d'analyse fournisseur"""
    name: str = Field(..., min_length=1, description="Nom du fournisseur")
    country: str = Field(..., min_length=1, description="Pays du fournisseur")
    city: Optional[str] = Field(None, description="Ville")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude GPS")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude GPS")
    materials: List[str] = Field(..., min_length=1, description="Matières fournies")
    nc_codes: Optional[List[str]] = Field(default=[], description="Codes douaniers NC")
    criticality: Optional[str] = Field(
        default="Standard", 
        description="Niveau de criticité",
        pattern="^(Standard|Important|Critique)$"
    )
    annual_volume: Optional[float] = Field(None, ge=0, description="Volume annuel en euros")


class RegulatoryRiskItem(BaseModel):
    """Risque réglementaire détecté"""
    celex_id: str
    title: str
    publication_date: Optional[str] = None
    document_type: Optional[str] = None
    source_url: str
    matched_keyword: str
    relevance: str  # high, medium, low


class WeatherRiskItem(BaseModel):
    """Alerte météo détectée"""
    alert_type: str
    severity: str
    date: str
    value: float
    threshold: float
    unit: str
    description: str
    supply_chain_risk: str


class RecommendationItem(BaseModel):
    """Recommandation d'action"""
    type: str  # regulatory, weather, general
    priority: str  # high, medium, low
    action: str
    details: str


class SupplierInfo(BaseModel):
    """Informations du fournisseur"""
    name: str
    country: str
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    nc_codes: List[str] = []
    materials: List[str] = []
    criticality: str = "Standard"
    annual_volume: Optional[float] = None


class SupplierAnalysisResponse(BaseModel):
    """Réponse d'analyse fournisseur"""
    id: str
    status: str  # pending, completed, error
    supplier_info: SupplierInfo
    regulatory_risks: dict
    weather_risks: dict
    risk_score: float
    risk_level: str  # Faible, Moyen, Fort, Critique
    recommendations: List[RecommendationItem]
    processing_time_ms: int
    created_at: str


class SupplierAnalysisListResponse(BaseModel):
    """Liste paginée des analyses"""
    analyses: List[SupplierAnalysisResponse]
    total: int
    page: int
    limit: int


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_risk_level(score: float) -> str:
    """Convertit le score en niveau de risque"""
    if score >= 8.0:
        return "Critique"
    elif score >= 6.0:
        return "Fort"
    elif score >= 4.0:
        return "Moyen"
    else:
        return "Faible"


def db_to_response(analysis: SupplierAnalysis) -> SupplierAnalysisResponse:
    """Convertit un enregistrement DB en réponse API"""
    extra = analysis.extra_metadata or {}
    
    return SupplierAnalysisResponse(
        id=str(analysis.id),
        status=analysis.status or "completed",
        supplier_info=SupplierInfo(
            name=analysis.supplier_name,
            country=analysis.supplier_country,
            city=analysis.supplier_city,
            latitude=analysis.latitude,
            longitude=analysis.longitude,
            nc_codes=extra.get("nc_codes", []),
            materials=extra.get("materials", []),
            criticality=extra.get("criticality", "Standard"),
            annual_volume=extra.get("annual_volume")
        ),
        regulatory_risks={
            "count": extra.get("regulatory_risks_count", 0),
            "items": extra.get("regulatory_risks", [])
        },
        weather_risks={
            "count": extra.get("weather_risks_count", 0),
            "items": extra.get("weather_risks", [])
        },
        risk_score=analysis.risk_score or 0.0,
        risk_level=calculate_risk_level(analysis.risk_score or 0.0),
        recommendations=extra.get("recommendations", []),
        processing_time_ms=extra.get("processing_time_ms", 0),
        created_at=analysis.created_at.isoformat() if analysis.created_at else ""
    )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/analyze", response_model=SupplierAnalysisResponse)
async def analyze_supplier(request: SupplierAnalysisRequest):
    """
    Lance une analyse de risques pour un fournisseur.
    
    Cette analyse :
    1. Recherche les réglementations EUR-Lex pertinentes pour les matières
    2. Récupère les alertes météo pour la localisation
    3. Calcule un score de risque global
    4. Génère des recommandations
    """
    import time
    start_time = time.time()
    
    logger.info(
        "supplier_analysis_started",
        name=request.name,
        country=request.country,
        materials=request.materials
    )
    
    try:
        # Construire le dict supplier_info pour l'agent
        supplier_info = {
            "name": request.name,
            "country": request.country,
            "city": request.city,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "materials": request.materials,
            "nc_codes": request.nc_codes or [],
            "criticality": request.criticality or "Standard",
            "annual_volume": request.annual_volume
        }
        
        # Appeler l'agent 1A pour l'analyse fournisseur
        result = await run_agent_1a_for_supplier(
            supplier_info=supplier_info,
            save_to_db=True
        )
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Extraire les données collectées
        collected = result.get("collected_data", {})
        regulatory = collected.get("regulatory", {})
        weather = collected.get("weather", {})
        
        # Calculer le score de risque basique (avant Agent 1B)
        reg_count = regulatory.get("count", 0)
        weather_count = weather.get("count", 0)
        
        # Score simple: plus de risques = score plus élevé
        base_score = min(10.0, (reg_count * 0.5) + (weather_count * 0.8))
        
        # Ajuster selon la criticité
        criticality_multiplier = {
            "Standard": 1.0,
            "Important": 1.2,
            "Critique": 1.5
        }
        risk_score = min(10.0, base_score * criticality_multiplier.get(request.criticality or "Standard", 1.0))
        
        # Générer des recommandations basiques
        recommendations = []
        
        if reg_count > 0:
            recommendations.append({
                "type": "regulatory",
                "priority": "high" if reg_count >= 3 else "medium",
                "action": f"Vérifier la conformité aux {reg_count} réglementation(s) détectée(s)",
                "details": "Demander les certificats de conformité au fournisseur."
            })
        
        if weather_count > 0:
            high_severity = sum(1 for w in weather.get("items", []) if w.get("severity") in ["high", "critical"])
            recommendations.append({
                "type": "weather",
                "priority": "high" if high_severity > 0 else "medium",
                "action": f"Anticiper les {weather_count} alerte(s) météo",
                "details": "Prévoir un stock de sécurité de 2-3 semaines."
            })
        
        # Construire la réponse
        response = SupplierAnalysisResponse(
            id=result.get("analysis_id", ""),
            status="completed",
            supplier_info=SupplierInfo(
                name=request.name,
                country=request.country,
                city=request.city,
                latitude=request.latitude or result.get("supplier_info", {}).get("latitude"),
                longitude=request.longitude or result.get("supplier_info", {}).get("longitude"),
                nc_codes=request.nc_codes or [],
                materials=request.materials,
                criticality=request.criticality or "Standard",
                annual_volume=request.annual_volume
            ),
            regulatory_risks={
                "count": reg_count,
                "items": regulatory.get("items", [])
            },
            weather_risks={
                "count": weather_count,
                "items": weather.get("items", [])
            },
            risk_score=round(risk_score, 2),
            risk_level=calculate_risk_level(risk_score),
            recommendations=recommendations,
            processing_time_ms=processing_time_ms,
            created_at=datetime.now().isoformat()
        )
        
        logger.info(
            "supplier_analysis_completed",
            id=response.id,
            risk_score=response.risk_score,
            processing_time_ms=processing_time_ms
        )
        
        return response
            
    except Exception as e:
        logger.error("supplier_analysis_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")


@router.get("/analyses", response_model=SupplierAnalysisListResponse)
async def list_analyses(
    page: int = Query(1, ge=1, description="Numéro de page"),
    limit: int = Query(10, ge=1, le=100, description="Éléments par page"),
    country: Optional[str] = Query(None, description="Filtrer par pays"),
    risk_level: Optional[str] = Query(None, description="Filtrer par niveau de risque")
):
    """
    Liste les analyses de fournisseurs avec pagination et filtres.
    """
    db = SessionLocal()
    try:
        query = db.query(SupplierAnalysis).filter(SupplierAnalysis.status == "completed")
        
        # Filtres
        if country:
            query = query.filter(SupplierAnalysis.supplier_country.ilike(f"%{country}%"))
        
        if risk_level:
            # Convertir le niveau en plage de scores
            if risk_level == "Critique":
                query = query.filter(SupplierAnalysis.risk_score >= 8.0)
            elif risk_level == "Fort":
                query = query.filter(SupplierAnalysis.risk_score >= 6.0, SupplierAnalysis.risk_score < 8.0)
            elif risk_level == "Moyen":
                query = query.filter(SupplierAnalysis.risk_score >= 4.0, SupplierAnalysis.risk_score < 6.0)
            elif risk_level == "Faible":
                query = query.filter(SupplierAnalysis.risk_score < 4.0)
        
        # Total
        total = query.count()
        
        # Pagination
        offset = (page - 1) * limit
        analyses = query.order_by(SupplierAnalysis.created_at.desc()).offset(offset).limit(limit).all()
        
        return SupplierAnalysisListResponse(
            analyses=[db_to_response(a) for a in analyses],
            total=total,
            page=page,
            limit=limit
        )
        
    finally:
        db.close()


@router.get("/analyses/{analysis_id}", response_model=SupplierAnalysisResponse)
async def get_analysis(analysis_id: str):
    """
    Récupère les détails d'une analyse spécifique.
    """
    db = SessionLocal()
    try:
        analysis = db.query(SupplierAnalysis).filter(SupplierAnalysis.id == analysis_id).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analyse non trouvée")
        
        return db_to_response(analysis)
        
    finally:
        db.close()


@router.delete("/analyses/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """
    Supprime une analyse.
    """
    db = SessionLocal()
    try:
        analysis = db.query(SupplierAnalysis).filter(SupplierAnalysis.id == analysis_id).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analyse non trouvée")
        
        db.delete(analysis)
        db.commit()
        
        return {"message": "Analyse supprimée", "id": analysis_id}
        
    finally:
        db.close()
