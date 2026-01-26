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
