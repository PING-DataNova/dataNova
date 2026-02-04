"""
Routes pour les impact assessments (Agent 2 - Dashboard Décideur)
Adapté pour utiliser RiskAnalysis comme modèle de données
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from pydantic import BaseModel

from src.api.deps import get_db
from src.storage.models import RiskAnalysis, Document, PertinenceCheck

router = APIRouter(prefix="/impacts", tags=["Impact Assessments"])


# ========================================
# Schémas de réponse
# ========================================

class ImpactAssessmentResponse(BaseModel):
    id: str
    analysis_id: str
    regulation_title: str
    regulation_type: Optional[str] = None
    risk_main: str
    impact_level: str
    risk_details: str
    modality: Optional[str] = None
    deadline: Optional[str] = None
    recommendation: str
    llm_reasoning: Optional[str] = None
    created_at: datetime
    category: str = "Réglementations"

    class Config:
        from_attributes = True


class ImpactAssessmentListResponse(BaseModel):
    impacts: List[ImpactAssessmentResponse]
    total: int
    page: int
    limit: int


class DashboardStatsResponse(BaseModel):
    total_regulations: int
    total_impacts: int
    high_risks: int
    medium_risks: int
    low_risks: int
    critical_deadlines: int
    pending_percentage: float
    approved_percentage: float
    average_score: float  # Score moyen réel de la base (0-100)
    by_risk_type: dict


class AffectedEntity(BaseModel):
    id: str
    name: str
    risk_score: float
    reasoning: str
    weather_summary: Optional[str] = None
    business_interruption_score: Optional[float] = None


class RiskDetailResponse(BaseModel):
    """Réponse détaillée pour un risque spécifique"""
    id: str
    analysis_id: str
    
    # Informations sur le document source
    regulation_title: str
    regulation_type: Optional[str] = None
    source_url: Optional[str] = None
    source_excerpt: Optional[str] = None
    
    # Niveaux de risque
    risk_level: str
    risk_score: float  # Score 0-100
    impact_level: str
    supply_chain_impact: Optional[str] = None
    
    # Description
    impacts_description: str
    reasoning: Optional[str] = None
    
    # Entités affectées
    affected_sites: List[AffectedEntity] = []
    affected_suppliers: List[AffectedEntity] = []
    
    # Recommandations
    recommendations: str
    
    # Métadonnées
    created_at: datetime
    category: str = "Réglementations"
    
    # Analyse météo si disponible
    weather_risk_summary: Optional[dict] = None
    
    class Config:
        from_attributes = True


# ========================================
# Fonctions de mapping
# ========================================

def map_risk_to_impact(risk: RiskAnalysis) -> ImpactAssessmentResponse:
    """
    Convertit un RiskAnalysis en format ImpactAssessment pour le frontend
    """
    doc = risk.document
    
    # Mapper risk_level vers impact_level
    level_mapping = {
        'Critique': 'critique',
        'critique': 'critique', 
        'CRITIQUE': 'critique',
        'Fort': 'eleve',
        'fort': 'eleve',
        'Élevé': 'eleve',
        'eleve': 'eleve',
        'Moyen': 'moyen',
        'moyen': 'moyen',
        'Faible': 'faible',
        'faible': 'faible'
    }
    
    impact_level = level_mapping.get(risk.risk_level, 'moyen')
    
    # Déterminer la catégorie basée sur le type de document
    category = "Réglementations"
    if doc and doc.event_type:
        if 'climat' in doc.event_type.lower() or 'weather' in doc.event_type.lower():
            category = "Climat"
        elif 'geo' in doc.event_type.lower() or 'conflict' in doc.event_type.lower():
            category = "Géopolitique"
    
    return ImpactAssessmentResponse(
        id=risk.id,
        analysis_id=risk.id,
        regulation_title=doc.title if doc else "Document inconnu",
        regulation_type=doc.event_type if doc else None,
        risk_main=risk.impacts_description[:200] if risk.impacts_description else "",
        impact_level=impact_level,
        risk_details=risk.reasoning or "",
        modality=risk.supply_chain_impact,
        deadline=None,  # À extraire des métadonnées si disponible
        recommendation=risk.recommendations or "",
        llm_reasoning=risk.reasoning,
        created_at=risk.created_at,
        category=category
    )


# ========================================
# Endpoints
# ========================================

@router.get("", response_model=ImpactAssessmentListResponse)
def get_impacts(
    impact_level: Optional[str] = Query(None, description="Filtrer par niveau: faible, moyen, eleve, critique"),
    risk_main: Optional[str] = Query(None, description="Filtrer par type de risque"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Récupère la liste des analyses de risque pour le Dashboard.
    """
    
    # Construire la requête de base avec eager loading
    query = db.query(RiskAnalysis).options(
        joinedload(RiskAnalysis.document)
    )
    
    # Filtrer par niveau de risque
    if impact_level:
        level_mapping = {
            'critique': ['Critique', 'critique', 'CRITIQUE'],
            'eleve': ['Fort', 'fort', 'Élevé', 'eleve'],
            'moyen': ['Moyen', 'moyen'],
            'faible': ['Faible', 'faible']
        }
        levels = level_mapping.get(impact_level, [impact_level])
        query = query.filter(RiskAnalysis.risk_level.in_(levels))
    
    # Compter le total
    total = query.count()
    
    # Pagination
    offset = (page - 1) * limit
    risks = query.order_by(RiskAnalysis.created_at.desc()).offset(offset).limit(limit).all()
    
    # Convertir en format frontend
    impact_list = [map_risk_to_impact(risk) for risk in risks]
    
    return ImpactAssessmentListResponse(
        impacts=impact_list,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/stats/dashboard", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Récupère les statistiques pour le dashboard.
    """
    
    # Total documents
    total_docs = db.query(Document).count()
    
    # Total analyses
    total_analyses = db.query(RiskAnalysis).count()
    
    # Comptage par niveau
    high_count = db.query(RiskAnalysis).filter(
        RiskAnalysis.risk_level.in_(['Critique', 'critique', 'Fort', 'fort', 'CRITIQUE'])
    ).count()
    
    medium_count = db.query(RiskAnalysis).filter(
        RiskAnalysis.risk_level.in_(['Moyen', 'moyen'])
    ).count()
    
    low_count = db.query(RiskAnalysis).filter(
        RiskAnalysis.risk_level.in_(['Faible', 'faible'])
    ).count()
    
    # Calculer le score moyen réel (risk_score est sur 10, on convertit en 100)
    analyses = db.query(RiskAnalysis).all()
    if analyses:
        scores = [a.risk_score for a in analyses if a.risk_score is not None]
        avg_score = (sum(scores) / len(scores) * 10) if scores else 0  # Convertir 0-10 en 0-100
    else:
        avg_score = 0
    
    return DashboardStatsResponse(
        total_regulations=total_docs,
        total_impacts=total_analyses,
        high_risks=high_count,
        medium_risks=medium_count,
        low_risks=low_count,
        critical_deadlines=high_count,
        pending_percentage=0.0,
        approved_percentage=100.0 if total_analyses > 0 else 0.0,
        average_score=round(avg_score, 1),
        by_risk_type={
            "reglementaire": total_analyses,
            "climat": 0,
            "geopolitique": 0
        }
    )


@router.get("/stats/timeline")
def get_timeline_stats(db: Session = Depends(get_db)):
    """
    Récupère les statistiques de timeline.
    """
    risks = db.query(RiskAnalysis).order_by(RiskAnalysis.created_at.desc()).limit(30).all()
    
    timeline = {}
    for risk in risks:
        date_key = risk.created_at.strftime("%Y-%m") if risk.created_at else "unknown"
        if date_key not in timeline:
            timeline[date_key] = {"total": 0, "eleve": 0, "moyen": 0, "faible": 0}
        timeline[date_key]["total"] += 1
        
        if risk.risk_level in ['Critique', 'critique', 'Fort', 'fort']:
            timeline[date_key]["eleve"] += 1
        elif risk.risk_level in ['Moyen', 'moyen']:
            timeline[date_key]["moyen"] += 1
        else:
            timeline[date_key]["faible"] += 1
    
    return {"timeline": timeline}


@router.get("/{id}", response_model=ImpactAssessmentResponse)
def get_impact_by_id(
    id: str,
    db: Session = Depends(get_db)
):
    """
    Récupère une analyse de risque spécifique par son ID.
    """
    risk = db.query(RiskAnalysis).options(
        joinedload(RiskAnalysis.document)
    ).filter(RiskAnalysis.id == id).first()
    
    if not risk:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    
    return map_risk_to_impact(risk)


@router.get("/{id}/details", response_model=RiskDetailResponse)
def get_risk_details(
    id: str,
    db: Session = Depends(get_db)
):
    """
    Récupère les détails complets d'une analyse de risque incluant:
    - Sites impactés
    - Fournisseurs impactés
    - Recommandations détaillées
    - Analyse météo
    """
    import json
    
    risk = db.query(RiskAnalysis).options(
        joinedload(RiskAnalysis.document)
    ).filter(RiskAnalysis.id == id).first()
    
    if not risk:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    
    doc = risk.document
    
    # Mapper risk_level vers impact_level
    level_mapping = {
        'Critique': 'critique',
        'critique': 'critique', 
        'CRITIQUE': 'critique',
        'Fort': 'eleve',
        'fort': 'eleve',
        'Élevé': 'eleve',
        'eleve': 'eleve',
        'Moyen': 'moyen',
        'moyen': 'moyen',
        'Faible': 'faible',
        'faible': 'faible'
    }
    impact_level = level_mapping.get(risk.risk_level, 'moyen')
    
    # Catégorie
    category = "Réglementations"
    if doc and doc.event_type:
        if 'climat' in doc.event_type.lower() or 'weather' in doc.event_type.lower():
            category = "Climat"
        elif 'geo' in doc.event_type.lower() or 'conflict' in doc.event_type.lower():
            category = "Géopolitique"
    
    # Parser les sites affectés
    affected_sites = []
    if risk.affected_sites:
        try:
            sites_data = json.loads(risk.affected_sites) if isinstance(risk.affected_sites, str) else risk.affected_sites
            for site in sites_data:
                affected_sites.append(AffectedEntity(
                    id=site.get('id', ''),
                    name=site.get('name', 'Unknown'),
                    risk_score=site.get('risk_score', 0),
                    reasoning=site.get('reasoning', ''),
                    weather_summary=None,
                    business_interruption_score=site.get('business_interruption_score', 0)
                ))
        except json.JSONDecodeError:
            pass
    
    # Parser les fournisseurs affectés
    affected_suppliers = []
    if risk.affected_suppliers:
        try:
            suppliers_data = json.loads(risk.affected_suppliers) if isinstance(risk.affected_suppliers, str) else risk.affected_suppliers
            for supplier in suppliers_data:
                affected_suppliers.append(AffectedEntity(
                    id=supplier.get('id', ''),
                    name=supplier.get('name', 'Unknown'),
                    risk_score=supplier.get('risk_score', 0),
                    reasoning=supplier.get('reasoning', ''),
                    weather_summary=None,
                    business_interruption_score=supplier.get('business_interruption_score', 0)
                ))
        except json.JSONDecodeError:
            pass
    
    # Parser les métadonnées pour les infos météo
    weather_risk_summary = None
    source_url = None
    source_excerpt = None
    if risk.analysis_metadata:
        try:
            metadata = json.loads(risk.analysis_metadata) if isinstance(risk.analysis_metadata, str) else risk.analysis_metadata
            weather_risk_summary = metadata.get('weather_risk_summary')
            if 'source' in metadata:
                source_url = metadata['source'].get('url')
                source_excerpt = metadata['source'].get('excerpt')
        except json.JSONDecodeError:
            pass
    
    return RiskDetailResponse(
        id=risk.id,
        analysis_id=risk.id,
        regulation_title=doc.title if doc else "Document inconnu",
        regulation_type=doc.event_type if doc else None,
        source_url=source_url,
        source_excerpt=source_excerpt,
        risk_level=risk.risk_level or "Moyen",
        risk_score=round(risk.risk_score * 10, 1) if risk.risk_score else 0,  # Convertir 0-10 en 0-100
        impact_level=impact_level,
        supply_chain_impact=risk.supply_chain_impact,
        impacts_description=risk.impacts_description or "",
        reasoning=risk.reasoning,
        affected_sites=affected_sites,
        affected_suppliers=affected_suppliers,
        recommendations=risk.recommendations or "",
        created_at=risk.created_at,
        category=category,
        weather_risk_summary=weather_risk_summary
    )

