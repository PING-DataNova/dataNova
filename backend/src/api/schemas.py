"""
Schémas Pydantic pour l'API
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class RegulationResponse(BaseModel):
    """
    Réglementation pour le frontend (= Document + Analysis)
    Mapping: Backend Analysis → Frontend Regulation
    """
    id: str  # analysis.id
    title: str  # document.title
    description: str  # document.content (tronqué) ou llm_reasoning
    status: str  # validation_status: pending → pending, approved → validated
    type: str  # document.regulation_type
    dateCreated: datetime  # document.created_at
    reference: str  # document.source_url
    
    # Champs additionnels pour l'UI juridique
    confidence: Optional[float] = None  # analysis.confidence
    matched_keywords: Optional[List[str]] = None  # analysis.matched_keywords
    matched_nc_codes: Optional[List[str]] = None  # analysis.matched_nc_codes
    llm_reasoning: Optional[str] = None  # analysis.llm_reasoning
    
    class Config:
        from_attributes = True


class RegulationListResponse(BaseModel):
    """Liste paginée de réglementations"""
    regulations: List[RegulationResponse]
    total: int
    page: int
    limit: int


class UpdateRegulationStatusRequest(BaseModel):
    """Requête de mise à jour du statut"""
    status: str  # validated, rejected, to-review
    comment: Optional[str] = None


class RegulationStatsResponse(BaseModel):
    """Statistiques des réglementations"""
    total: int
    by_status: dict
    recent_count: int
    high_priority: int


# ========================================
# Schémas pour Agent 2 - Impact Assessments
# ========================================

class ImpactAssessmentResponse(BaseModel):
    """
    Impact Assessment pour le Dashboard Décideur
    Mapping: Backend ImpactAssessment → Frontend Impact
    """
    id: str  # impact_assessment.id
    analysis_id: str  # impact_assessment.analysis_id
    regulation_title: str  # document.title (via analysis)
    regulation_type: Optional[str] = None  # document.regulation_type
    
    # Métriques d'impact (Agent 2)
    risk_main: str  # fiscal, operationnel, conformite, reputationnel, juridique
    impact_level: str  # faible, moyen, eleve
    risk_details: str  # Description textuelle de l'impact
    modality: str  # certificat, reporting, taxe, quota, interdiction, autorisation
    deadline: str  # Format: "MM-YYYY"
    
    # Recommandations et analyse LLM
    recommendation: str  # Actions recommandées par Agent 2
    llm_reasoning: Optional[str] = None  # Raisonnement détaillé du LLM
    
    # Métadonnées
    created_at: datetime  # Date de création de l'analyse d'impact
    
    class Config:
        from_attributes = True


class ImpactAssessmentListResponse(BaseModel):
    """Liste paginée d'impact assessments"""
    impacts: List[ImpactAssessmentResponse]
    total: int
    page: int
    limit: int


class DashboardStatsResponse(BaseModel):
    """
    Statistiques pour le Dashboard Décideur
    """
    # Totaux
    total_regulations: int  # Nombre de réglementations validées
    total_impacts: int  # Nombre d'impacts analysés
    
    # Par niveau d'impact
    high_risks: int  # Risques élevés
    medium_risks: int  # Risques moyens
    low_risks: int  # Risques faibles
    
    # Deadlines
    critical_deadlines: int  # Nombre de deadlines critiques (< 6 mois)
    
    # Pourcentages workflow
    pending_percentage: float  # % en cours
    approved_percentage: float  # % validées
    
    # Répartition par type de risque
    by_risk_type: dict  # {'fiscal': X, 'operationnel': Y, ...}
