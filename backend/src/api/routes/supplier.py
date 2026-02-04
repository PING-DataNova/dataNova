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
from src.storage.models import SupplierAnalysis, Supplier, SupplierRelationship, HutchinsonSite
from src.agent_1a.agent import run_agent_1a_for_supplier
import json

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


# ============================================================================
# ENDPOINTS FOURNISSEURS (lecture de la BDD)
# ============================================================================

from src.storage.models import Supplier, SupplierRelationship, HutchinsonSite
import json


class SupplierDBResponse(BaseModel):
    """Réponse fournisseur depuis la BDD"""
    id: str
    name: str
    code: str
    country: str
    region: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sector: str
    products_supplied: List[str] = []
    company_size: Optional[str] = None
    certifications: List[str] = []
    financial_health: Optional[str] = None
    active: bool = True
    
    # Données business
    annual_purchase_volume: Optional[float] = None
    daily_delivery_value: Optional[float] = None
    average_stock_at_hutchinson_days: Optional[int] = None
    switch_time_days: Optional[int] = None
    criticality_score: Optional[int] = None
    can_increase_capacity: bool = False
    
    # Métadonnées enrichies
    employee_count: Optional[int] = None
    annual_revenue_usd: Optional[float] = None
    founded_year: Optional[int] = None


class SupplierDetailDBResponse(SupplierDBResponse):
    """Réponse détaillée avec relations"""
    sites_served: List[dict] = []
    risk_exposure: dict = {}


def map_supplier_from_db(supplier: Supplier) -> SupplierDBResponse:
    """Convertit un Supplier ORM en SupplierDBResponse"""
    products = []
    if supplier.products_supplied:
        try:
            products = json.loads(supplier.products_supplied) if isinstance(supplier.products_supplied, str) else supplier.products_supplied
        except:
            pass
    
    certifications = []
    if supplier.certifications:
        try:
            certifications = json.loads(supplier.certifications) if isinstance(supplier.certifications, str) else supplier.certifications
        except:
            pass
    
    employee_count = None
    annual_revenue_usd = None
    founded_year = None
    if supplier.extra_metadata:
        try:
            metadata = json.loads(supplier.extra_metadata) if isinstance(supplier.extra_metadata, str) else supplier.extra_metadata
            employee_count = metadata.get('employee_count')
            annual_revenue_usd = metadata.get('annual_revenue_usd')
            founded_year = metadata.get('founded_year')
        except:
            pass
    
    return SupplierDBResponse(
        id=supplier.id,
        name=supplier.name,
        code=supplier.code,
        country=supplier.country,
        region=supplier.region,
        city=supplier.city,
        address=supplier.address,
        latitude=supplier.latitude,
        longitude=supplier.longitude,
        sector=supplier.sector,
        products_supplied=products,
        company_size=supplier.company_size,
        certifications=certifications,
        financial_health=supplier.financial_health,
        active=supplier.active if supplier.active is not None else True,
        annual_purchase_volume=supplier.annual_purchase_volume,
        daily_delivery_value=supplier.daily_delivery_value,
        average_stock_at_hutchinson_days=supplier.average_stock_at_hutchinson_days,
        switch_time_days=supplier.switch_time_days,
        criticality_score=supplier.criticality_score,
        can_increase_capacity=supplier.can_increase_capacity if supplier.can_increase_capacity else False,
        employee_count=employee_count,
        annual_revenue_usd=annual_revenue_usd,
        founded_year=founded_year
    )


@router.get("/db/list")
async def get_suppliers_from_db(
    country: Optional[str] = None,
    sector: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """
    Récupère la liste des fournisseurs depuis la base de données.
    """
    db = SessionLocal()
    try:
        query = db.query(Supplier).filter(Supplier.active == True)
        
        if country:
            query = query.filter(Supplier.country.ilike(f"%{country}%"))
        
        if sector:
            query = query.filter(Supplier.sector.ilike(f"%{sector}%"))
        
        suppliers = query.limit(limit).all()
        
        return {
            "suppliers": [map_supplier_from_db(s) for s in suppliers],
            "total": len(suppliers)
        }
    finally:
        db.close()


@router.get("/db/{supplier_id}")
async def get_supplier_detail_from_db(supplier_id: str):
    """
    Récupère les détails complets d'un fournisseur par son ID.
    """
    db = SessionLocal()
    try:
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        
        if not supplier:
            raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
        
        # Récupérer les relations avec les sites
        relationships = db.query(SupplierRelationship).filter(
            SupplierRelationship.supplier_id == supplier_id
        ).all()
        
        sites_served = []
        for rel in relationships:
            site = db.query(HutchinsonSite).filter(HutchinsonSite.id == rel.hutchinson_site_id).first()
            if site:
                # Récupérer les produits fournis depuis products_supplied
                products = []
                if rel.products_supplied:
                    try:
                        products = json.loads(rel.products_supplied) if isinstance(rel.products_supplied, str) else rel.products_supplied
                    except:
                        pass
                
                sites_served.append({
                    "site_id": site.id,
                    "site_name": site.name,
                    "site_country": site.country,
                    "criticality": rel.criticality,
                    "products_supplied": products,
                    "is_sole_supplier": rel.is_sole_supplier,
                    "has_backup_supplier": rel.has_backup_supplier,
                    "lead_time_days": rel.lead_time_days,
                    "annual_volume": rel.annual_volume
                })
        
        # Construire la réponse détaillée
        base_response = map_supplier_from_db(supplier)
        
        # Calculer l'exposition au risque
        critical_sites = len([s for s in sites_served if s.get('criticality') == 'Critique'])
        sole_supplier_sites = len([s for s in sites_served if s.get('is_sole_supplier')])
        
        risk_exposure = {
            "total_sites_served": len(sites_served),
            "critical_relationships": critical_sites,
            "sole_supplier_for": sole_supplier_sites,
            "backup_coverage": len([s for s in sites_served if s.get('has_backup_supplier')]),
            "risk_level": "eleve" if sole_supplier_sites > 0 or critical_sites >= 3 else "moyen" if critical_sites > 0 else "faible"
        }
        
        return {
            **base_response.model_dump(),
            "sites_served": sites_served,
            "risk_exposure": risk_exposure
        }
    finally:
        db.close()


@router.get("/db/by-name/{name}")
async def get_supplier_by_name_from_db(name: str):
    """
    Recherche un fournisseur par son nom (partiel).
    """
    db = SessionLocal()
    try:
        supplier = db.query(Supplier).filter(
            Supplier.name.ilike(f"%{name}%")
        ).first()
        
        if not supplier:
            raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
        
        return map_supplier_from_db(supplier)
    finally:
        db.close()
