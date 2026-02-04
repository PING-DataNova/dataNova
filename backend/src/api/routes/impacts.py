"""
Routes pour les impact assessments (Agent 2 - Dashboard Décideur)
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from src.api.deps import get_db
from src.api.schemas import (
    ImpactAssessmentResponse,
    ImpactAssessmentListResponse,
    DashboardStatsResponse
)
from src.storage.models import ImpactAssessment, Analysis, Document, PertinenceCheck, RiskAnalysis

router = APIRouter(prefix="/impacts", tags=["Impact Assessments"])


def map_impact_to_response(impact: ImpactAssessment) -> ImpactAssessmentResponse:
    """
    Convertit un ImpactAssessment backend en format frontend
    """
    # The current DB models use RiskAnalysis / PertinenceCheck. Map defensively.
    analysis = getattr(impact, "pertinence_check", None)
    doc = getattr(analysis, "document", None) if analysis else None

    # Map fields with fallbacks to avoid AttributeErrors across branches
    analysis_id = getattr(impact, "pertinence_check_id", None) or (analysis.id if analysis else None)
    regulation_title = getattr(doc, "title", None) or "Unknown"
    regulation_type = getattr(doc, "event_subtype", None) or getattr(doc, "regulation_type", None)

    # Impact metrics
    risk_main = getattr(impact, "risk_level", "unknown")
    impact_level = getattr(impact, "supply_chain_impact", None) or getattr(impact, "risk_level", "unknown")
    risk_details = getattr(impact, "impacts_description", "")

    # Recommendations / modality / deadline best-effort mapping
    recommendation = getattr(impact, "recommendations", "")
    modality = "autre"
    deadline = None

    return ImpactAssessmentResponse(
        id=impact.id,
        analysis_id=analysis_id,
        regulation_title=regulation_title,
        regulation_type=regulation_type,
        risk_main=risk_main,
        impact_level=impact_level,
        risk_details=risk_details,
        modality=modality,
        deadline=deadline,
        recommendation=recommendation if isinstance(recommendation, str) else str(recommendation),
        llm_reasoning=getattr(impact, "reasoning", None),
        created_at=getattr(impact, "created_at")
    )


@router.get("", response_model=ImpactAssessmentListResponse)
def get_impacts(
    impact_level: Optional[str] = Query(None, description="Filtrer par niveau: faible, moyen, eleve"),
    risk_main: Optional[str] = Query(None, description="Filtrer par type de risque: fiscal, operationnel, conformite, reputationnel, juridique"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Récupère la liste des impact assessments avec filtres.
    
    Utilisé par le Dashboard Décideur pour afficher les impacts analysés par Agent 2.
    """
    
    # Construire la requête de base avec eager loading
    # Eager-load related analysis->document where available
    query = db.query(ImpactAssessment).options(
        joinedload(ImpactAssessment.pertinence_check).joinedload(Analysis.document)
    )
    
    # Filtrer par niveau d'impact
    if impact_level:
        query = query.filter(ImpactAssessment.impact_level == impact_level)
    
    # Filtrer par type de risque
    if risk_main:
        query = query.filter(ImpactAssessment.risk_main == risk_main)
    
    # Compter le total
    total = query.count()
    
    # Pagination
    offset = (page - 1) * limit
    impacts = query.order_by(ImpactAssessment.created_at.desc()).offset(offset).limit(limit).all()
    
    # Convertir en format frontend
    impact_list = [map_impact_to_response(impact) for impact in impacts]
    
    return ImpactAssessmentListResponse(
        impacts=impact_list,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/{id}", response_model=ImpactAssessmentResponse)
def get_impact_by_id(
    id: str,
    db: Session = Depends(get_db)
):
    """
    Récupère un impact assessment spécifique par son ID.
    """
    impact = db.query(ImpactAssessment).options(
        joinedload(ImpactAssessment.pertinence_check).joinedload(Analysis.document)
    ).filter(ImpactAssessment.id == id).first()
    
    if not impact:
        raise HTTPException(status_code=404, detail="Impact assessment non trouvé")
    
    return map_impact_to_response(impact)


@router.get("/stats/dashboard", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Récupère les statistiques pour le Dashboard Décideur.
    
    Retourne:
    - Total de réglementations suivies
    - Nombre de risques élevés
    - Deadlines critiques (< 6 mois)
    - Répartition par niveau d'impact
    - Répartition par type de risque
    """
    
    # Use current models defensively (PertinenceCheck / RiskAnalysis)
    try:
        total_regulations = db.query(PertinenceCheck).count()
    except Exception:
        total_regulations = 0

    # Nombre total d'impacts
    try:
        total_impacts = db.query(RiskAnalysis).count()
    except Exception:
        total_impacts = 0

    # Compter par niveau d'impact (map to risk_level / supply_chain_impact)
    try:
        high_risks = db.query(RiskAnalysis).filter(RiskAnalysis.risk_level == 'Fort').count()
        medium_risks = db.query(RiskAnalysis).filter(RiskAnalysis.risk_level == 'Moyen').count()
        low_risks = db.query(RiskAnalysis).filter(RiskAnalysis.risk_level == 'Faible').count()
    except Exception:
        high_risks = medium_risks = low_risks = 0
    
    # Deadlines critiques: not available on current RiskAnalysis model — return 0
    critical_deadlines = 0

    # Répartition par type de risque: not present in current model, return zeros
    fiscal_risks = 0
    operational_risks = 0
    compliance_risks = 0
    reputational_risks = 0
    legal_risks = 0
    
    # Pourcentage en cours vs validées — not available in current schema, return 0 if unknown
    pending_pct = 0
    approved_pct = 0
    
    return DashboardStatsResponse(
        total_regulations=total_regulations,
        total_impacts=total_impacts,
        high_risks=high_risks,
        medium_risks=medium_risks,
        low_risks=low_risks,
        critical_deadlines=critical_deadlines,
        pending_percentage=round(pending_pct, 1),
        approved_percentage=round(approved_pct, 1),
        by_risk_type={
            'fiscal': fiscal_risks,
            'operationnel': operational_risks,
            'conformite': compliance_risks,
            'reputationnel': reputational_risks,
            'juridique': legal_risks
        }
    )


@router.get("/stats/timeline", response_model=dict)
def get_timeline_stats(db: Session = Depends(get_db)):
    """
    Récupère la répartition des impacts par deadline (pour graphique timeline).
    """
    
    # Récupérer tous les impacts avec leurs deadlines
    impacts = db.query(ImpactAssessment.deadline, ImpactAssessment.impact_level).all()
    
    # Grouper par deadline
    timeline = {}
    for impact in impacts:
        if impact.deadline:
            if impact.deadline not in timeline:
                timeline[impact.deadline] = {'total': 0, 'eleve': 0, 'moyen': 0, 'faible': 0}
            timeline[impact.deadline]['total'] += 1
            timeline[impact.deadline][impact.impact_level] += 1
    
    return {
        'timeline': timeline
    }
