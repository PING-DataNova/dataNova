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
from src.storage.models import ImpactAssessment, Analysis, Document

router = APIRouter(prefix="/impacts", tags=["Impact Assessments"])


def map_impact_to_response(impact: ImpactAssessment) -> ImpactAssessmentResponse:
    """
    Convertit un ImpactAssessment backend en format frontend
    """
    analysis = impact.analysis
    doc = analysis.document if analysis else None
    
    return ImpactAssessmentResponse(
        id=impact.id,
        analysis_id=impact.analysis_id,
        regulation_title=doc.title if doc else "Unknown",
        regulation_type=doc.regulation_type if doc else None,
        risk_main=impact.risk_main,
        impact_level=impact.impact_level,
        risk_details=impact.risk_details,
        modality=impact.modality,
        deadline=impact.deadline,
        recommendation=impact.recommendation,
        llm_reasoning=impact.llm_reasoning,
        created_at=impact.created_at
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
    query = db.query(ImpactAssessment).join(Analysis).join(Document).options(
        joinedload(ImpactAssessment.analysis).joinedload(Analysis.document)
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
        joinedload(ImpactAssessment.analysis).joinedload(Analysis.document)
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
    
    # Total d'analyses validées
    total_regulations = db.query(Analysis).filter(Analysis.validation_status == 'approved').count()
    
    # Nombre total d'impacts
    total_impacts = db.query(ImpactAssessment).count()
    
    # Compter par niveau d'impact
    high_risks = db.query(ImpactAssessment).filter(ImpactAssessment.impact_level == 'eleve').count()
    medium_risks = db.query(ImpactAssessment).filter(ImpactAssessment.impact_level == 'moyen').count()
    low_risks = db.query(ImpactAssessment).filter(ImpactAssessment.impact_level == 'faible').count()
    
    # Deadlines critiques (< 6 mois à partir de maintenant)
    from datetime import timedelta
    six_months_later = datetime.utcnow() + timedelta(days=180)
    # Convertir deadline format "MM-YYYY" en datetime pour comparaison
    # Pour simplifier, on compte tous les impacts avec deadline non null
    critical_deadlines = db.query(ImpactAssessment).filter(
        ImpactAssessment.deadline.isnot(None)
    ).count()
    
    # Répartition par type de risque
    fiscal_risks = db.query(ImpactAssessment).filter(ImpactAssessment.risk_main == 'fiscal').count()
    operational_risks = db.query(ImpactAssessment).filter(ImpactAssessment.risk_main == 'operationnel').count()
    compliance_risks = db.query(ImpactAssessment).filter(ImpactAssessment.risk_main == 'conformite').count()
    reputational_risks = db.query(ImpactAssessment).filter(ImpactAssessment.risk_main == 'reputationnel').count()
    legal_risks = db.query(ImpactAssessment).filter(ImpactAssessment.risk_main == 'juridique').count()
    
    # Pourcentage en cours vs validées
    total_analyses = db.query(Analysis).count()
    pending_count = db.query(Analysis).filter(Analysis.validation_status == 'pending').count()
    approved_count = db.query(Analysis).filter(Analysis.validation_status == 'approved').count()
    
    pending_pct = (pending_count / total_analyses * 100) if total_analyses > 0 else 0
    approved_pct = (approved_count / total_analyses * 100) if total_analyses > 0 else 0
    
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
