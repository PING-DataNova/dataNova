"""
Routes pour l'analyse ponctuelle de risques fournisseurs.

Endpoint principal: POST /api/supplier/analyze
Permet à un utilisateur d'analyser les risques liés à un fournisseur spécifique.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from src.api.deps import get_db
from src.api.schemas import (
    SupplierAnalysisRequest,
    SupplierAnalysisResponse,
    SupplierAnalysisListResponse,
    SupplierInfoResponse,
    RegulatoryRisksResponse,
    WeatherRisksResponse,
    RegulatoryRiskItem,
    WeatherRiskItem,
    RecommendationItem
)
from src.storage.models import SupplierAnalysis
from src.agent_1a.agent import run_agent_1a_for_supplier

router = APIRouter(prefix="/supplier", tags=["Supplier Analysis"])


@router.post("/analyze", response_model=SupplierAnalysisResponse)
async def analyze_supplier(
    request: SupplierAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyse les risques pour un fournisseur spécifique.
    
    Cette route déclenche une analyse complète incluant:
    - Risques réglementaires (recherche EUR-Lex)
    - Risques météorologiques (prévisions Open-Meteo sur 16 jours)
    - Calcul du score de risque global
    - Génération de recommandations
    
    L'analyse est sauvegardée en base de données pour historique.
    """
    try:
        # Convertir la requête en dict pour l'agent
        supplier_info = {
            "name": request.name,
            "country": request.country,
            "city": request.city,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "nc_codes": request.nc_codes,
            "materials": request.materials,
            "criticality": request.criticality,
            "annual_volume": request.annual_volume
        }
        
        # Lancer l'analyse (Agent 1A mode supplier)
        result = await run_agent_1a_for_supplier(
            supplier_info=supplier_info,
            save_to_db=True
        )
        
        # Convertir le résultat en réponse Pydantic
        response = SupplierAnalysisResponse(
            id=result.get("id"),
            status=result.get("status", "completed"),
            supplier_info=SupplierInfoResponse(**result.get("supplier_info", {})),
            regulatory_risks=RegulatoryRisksResponse(
                count=result.get("regulatory_risks", {}).get("count", 0),
                items=[RegulatoryRiskItem(**item) for item in result.get("regulatory_risks", {}).get("items", [])]
            ),
            weather_risks=WeatherRisksResponse(
                count=result.get("weather_risks", {}).get("count", 0),
                items=[WeatherRiskItem(**item) for item in result.get("weather_risks", {}).get("items", [])]
            ),
            risk_score=result.get("risk_score", 0.0),
            risk_level=result.get("risk_level", "Faible"),
            recommendations=[RecommendationItem(**rec) for rec in result.get("recommendations", [])],
            processing_time_ms=result.get("processing_time_ms", 0)
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse du fournisseur: {str(e)}"
        )


@router.get("/analyses", response_model=SupplierAnalysisListResponse)
def get_supplier_analyses(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    country: Optional[str] = Query(None, description="Filtrer par pays"),
    risk_level: Optional[str] = Query(None, description="Filtrer par niveau de risque"),
    db: Session = Depends(get_db)
):
    """
    Récupère l'historique des analyses fournisseurs.
    
    Permet de consulter les analyses précédentes avec filtres optionnels.
    """
    query = db.query(SupplierAnalysis).filter(SupplierAnalysis.status == "completed")
    
    # Filtres optionnels
    if country:
        query = query.filter(SupplierAnalysis.country.ilike(f"%{country}%"))
    if risk_level:
        query = query.filter(SupplierAnalysis.risk_level == risk_level)
    
    # Compter le total
    total = query.count()
    
    # Pagination et tri
    analyses = query.order_by(SupplierAnalysis.created_at.desc()) \
        .offset((page - 1) * limit) \
        .limit(limit) \
        .all()
    
    # Convertir en réponses
    items = []
    for analysis in analyses:
        items.append(SupplierAnalysisResponse(
            id=analysis.id,
            status=analysis.status,
            supplier_info=SupplierInfoResponse(
                name=analysis.supplier_name,
                country=analysis.country,
                city=analysis.city,
                latitude=analysis.latitude,
                longitude=analysis.longitude,
                nc_codes=analysis.nc_codes or [],
                materials=analysis.materials or [],
                criticality=analysis.criticality,
                annual_volume=analysis.annual_volume
            ),
            regulatory_risks=RegulatoryRisksResponse(
                count=analysis.regulatory_risks_count or 0,
                items=[RegulatoryRiskItem(**item) for item in (analysis.regulatory_risks or [])]
            ),
            weather_risks=WeatherRisksResponse(
                count=analysis.weather_risks_count or 0,
                items=[WeatherRiskItem(**item) for item in (analysis.weather_risks or [])]
            ),
            risk_score=analysis.risk_score or 0.0,
            risk_level=analysis.risk_level or "Faible",
            recommendations=[RecommendationItem(**rec) for rec in (analysis.recommendations or [])],
            processing_time_ms=analysis.processing_time_ms or 0
        ))
    
    return SupplierAnalysisListResponse(
        analyses=items,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/analyses/{analysis_id}", response_model=SupplierAnalysisResponse)
def get_supplier_analysis(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    """
    Récupère une analyse fournisseur spécifique par son ID.
    """
    analysis = db.query(SupplierAnalysis).filter(SupplierAnalysis.id == analysis_id).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    
    return SupplierAnalysisResponse(
        id=analysis.id,
        status=analysis.status,
        supplier_info=SupplierInfoResponse(
            name=analysis.supplier_name,
            country=analysis.country,
            city=analysis.city,
            latitude=analysis.latitude,
            longitude=analysis.longitude,
            nc_codes=analysis.nc_codes or [],
            materials=analysis.materials or [],
            criticality=analysis.criticality,
            annual_volume=analysis.annual_volume
        ),
        regulatory_risks=RegulatoryRisksResponse(
            count=analysis.regulatory_risks_count or 0,
            items=[RegulatoryRiskItem(**item) for item in (analysis.regulatory_risks or [])]
        ),
        weather_risks=WeatherRisksResponse(
            count=analysis.weather_risks_count or 0,
            items=[WeatherRiskItem(**item) for item in (analysis.weather_risks or [])]
        ),
        risk_score=analysis.risk_score or 0.0,
        risk_level=analysis.risk_level or "Faible",
        recommendations=[RecommendationItem(**rec) for rec in (analysis.recommendations or [])],
        processing_time_ms=analysis.processing_time_ms or 0
    )


@router.delete("/analyses/{analysis_id}")
def delete_supplier_analysis(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    """
    Supprime une analyse fournisseur.
    """
    analysis = db.query(SupplierAnalysis).filter(SupplierAnalysis.id == analysis_id).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    
    db.delete(analysis)
    db.commit()
    
    return {"message": "Analyse supprimée", "id": analysis_id}
