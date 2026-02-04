"""
Routes pour les réglementations (frontend Dashboard)
Adapté pour utiliser Document + RiskAnalysis comme modèles de données
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from pydantic import BaseModel

from src.api.deps import get_db
from src.storage.models import Document, RiskAnalysis, PertinenceCheck

router = APIRouter(prefix="/regulations", tags=["Regulations"])


# ========================================
# Schémas de réponse
# ========================================

class RegulationResponse(BaseModel):
    id: str
    title: str
    description: str
    status: str
    type: Optional[str] = None
    dateCreated: datetime
    reference: Optional[str] = None
    confidence: Optional[float] = None
    matched_keywords: Optional[dict] = None  # Peut être un dict complexe
    matched_nc_codes: Optional[List[str]] = None
    llm_reasoning: Optional[str] = None
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None

    class Config:
        from_attributes = True


class RegulationListResponse(BaseModel):
    regulations: List[RegulationResponse]
    total: int
    page: int
    limit: int


class UpdateRegulationStatusRequest(BaseModel):
    status: str
    comment: Optional[str] = None


class RegulationStatsResponse(BaseModel):
    total: int
    pending: int
    validated: int
    rejected: int


# ========================================
# Fonctions de mapping
# ========================================

def map_document_to_regulation(doc: Document) -> RegulationResponse:
    """
    Convertit un Document en format Regulation pour le frontend
    """
    
    # Récupérer l'analyse de risque associée si elle existe
    risk_analysis = doc.risk_analysis if hasattr(doc, 'risk_analysis') else None
    pertinence = doc.pertinence_check if hasattr(doc, 'pertinence_check') else None
    
    # Déterminer le statut
    status = "pending"
    if risk_analysis:
        status = "validated"
    elif pertinence:
        if pertinence.decision == "NON":
            status = "rejected"
        else:
            status = "pending"
    
    # Extraire les informations de l'analyse
    llm_reasoning = None
    risk_level = None
    risk_score = None
    confidence = None
    
    if risk_analysis:
        llm_reasoning = risk_analysis.reasoning
        risk_level = risk_analysis.risk_level
        risk_score = risk_analysis.risk_score
    
    if pertinence:
        confidence = pertinence.confidence
    
    return RegulationResponse(
        id=doc.id,
        title=doc.title,
        description=doc.content[:500] if doc.content else "",
        status=status,
        type=doc.event_type,
        dateCreated=doc.created_at,
        reference=doc.source_url,
        confidence=confidence,
        matched_keywords=pertinence.matched_elements if pertinence and pertinence.matched_elements else None,
        matched_nc_codes=None,
        llm_reasoning=llm_reasoning,
        risk_level=risk_level,
        risk_score=risk_score
    )


# ========================================
# Endpoints
# ========================================

@router.get("", response_model=RegulationListResponse)
def get_regulations(
    status: Optional[str] = Query(None, description="Filtrer par statut: all, pending, validated, rejected"),
    search: Optional[str] = Query(None, description="Recherche dans le titre"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Récupère la liste des réglementations avec filtres.
    """
    
    # Construire la requête de base avec eager loading
    query = db.query(Document).options(
        joinedload(Document.pertinence_check),
        joinedload(Document.risk_analysis)
    )
    
    # Filtrer par recherche dans le titre
    if search:
        query = query.filter(Document.title.ilike(f"%{search}%"))
    
    # Récupérer tous les documents d'abord pour filtrer par statut
    all_docs = query.order_by(Document.created_at.desc()).all()
    
    # Filtrer par statut
    filtered_docs = []
    for doc in all_docs:
        doc_status = "pending"
        if doc.risk_analysis:
            doc_status = "validated"
        elif doc.pertinence_check and doc.pertinence_check.decision == "NON":
            doc_status = "rejected"
        
        if status and status != 'all':
            if status == doc_status:
                filtered_docs.append(doc)
        else:
            filtered_docs.append(doc)
    
    # Total après filtrage
    total = len(filtered_docs)
    
    # Pagination
    offset = (page - 1) * limit
    paginated_docs = filtered_docs[offset:offset + limit]
    
    # Convertir en format frontend
    regulations = [map_document_to_regulation(doc) for doc in paginated_docs]
    
    return RegulationListResponse(
        regulations=regulations,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/stats", response_model=RegulationStatsResponse)
def get_regulation_stats(db: Session = Depends(get_db)):
    """
    Récupère les statistiques des réglementations.
    """
    
    total = db.query(Document).count()
    validated = db.query(RiskAnalysis).count()
    
    # Documents rejetés (pertinence = NON)
    rejected = db.query(PertinenceCheck).filter(
        PertinenceCheck.decision == "NON"
    ).count()
    
    # Pending = total - validated - rejected
    pending = max(0, total - validated - rejected)
    
    return RegulationStatsResponse(
        total=total,
        pending=pending,
        validated=validated,
        rejected=rejected
    )


@router.get("/{id}", response_model=RegulationResponse)
def get_regulation_by_id(
    id: str,
    db: Session = Depends(get_db)
):
    """
    Récupère une réglementation spécifique par son ID.
    """
    doc = db.query(Document).options(
        joinedload(Document.pertinence_check),
        joinedload(Document.risk_analysis)
    ).filter(Document.id == id).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    return map_document_to_regulation(doc)


@router.put("/{id}/status", response_model=RegulationResponse)
def update_regulation_status(
    id: str,
    request: UpdateRegulationStatusRequest,
    db: Session = Depends(get_db)
):
    """
    Met à jour le statut d'une réglementation.
    Note: Dans ce système, le statut est dérivé de l'existence d'une analyse.
    """
    doc = db.query(Document).options(
        joinedload(Document.pertinence_check),
        joinedload(Document.risk_analysis)
    ).filter(Document.id == id).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    # Le statut est principalement informatif dans ce système
    # L'action réelle serait de marquer pour relecture, etc.
    
    return map_document_to_regulation(doc)
