"""
Routes pour les analyses (réglementations pour le frontend)
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from src.api.deps import get_db
from src.api.schemas import (
    RegulationListResponse,
    RegulationResponse,
    UpdateRegulationStatusRequest,
    RegulationStatsResponse
)
from src.storage.models import Analysis, Document
from src.storage.repositories import AnalysisRepository

router = APIRouter(prefix="/regulations", tags=["Regulations"])


def map_analysis_to_regulation(analysis: Analysis) -> RegulationResponse:
    """
    Convertit une Analysis backend en Regulation frontend
    
    Mapping des statuts:
    - pending → pending
    - approved → validated
    - rejected → rejected
    """
    doc = analysis.document
    
    # Mapper le statut backend → frontend
    status_mapping = {
        'pending': 'pending',
        'approved': 'validated',
        'rejected': 'rejected'
    }
    
    return RegulationResponse(
        id=analysis.id,
        title=doc.title,
        description=doc.content[:500] if doc.content else analysis.llm_reasoning or "",
        status=status_mapping.get(analysis.validation_status, analysis.validation_status),
        type=doc.regulation_type,
        dateCreated=doc.created_at,
        reference=doc.source_url,
        confidence=analysis.confidence,
        matched_keywords=analysis.matched_keywords,
        matched_nc_codes=analysis.matched_nc_codes,
        llm_reasoning=analysis.llm_reasoning
    )


@router.get("", response_model=RegulationListResponse)
def get_regulations(
    status: Optional[str] = Query(None, description="Filtrer par statut: all, pending, validated, rejected, to-review"),
    search: Optional[str] = Query(None, description="Recherche dans le titre"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Récupère la liste des réglementations avec filtres.
    
    Retourne les analyses avec leurs documents associés.
    """
    
    # Construire la requête de base avec eager loading du document
    query = db.query(Analysis).join(Document).options(joinedload(Analysis.document))
    
    # Filtrer par statut
    if status and status != 'all':
        # Mapper le statut frontend → backend
        status_mapping = {
            'pending': 'pending',
            'validated': 'approved',
            'rejected': 'rejected',
            'to-review': 'pending'  # to-review = pending dans notre système
        }
        backend_status = status_mapping.get(status, status)
        query = query.filter(Analysis.validation_status == backend_status)
    
    # Filtrer par recherche dans le titre
    if search:
        query = query.filter(Document.title.ilike(f"%{search}%"))
    
    # Compter le total
    total = query.count()
    
    # Pagination
    offset = (page - 1) * limit
    analyses = query.order_by(Analysis.created_at.desc()).offset(offset).limit(limit).all()
    
    # Convertir en format frontend
    regulations = [map_analysis_to_regulation(analysis) for analysis in analyses]
    
    return RegulationListResponse(
        regulations=regulations,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/{id}", response_model=RegulationResponse)
def get_regulation_by_id(
    id: str,
    db: Session = Depends(get_db)
):
    """
    Récupère une réglementation spécifique par son ID (analysis.id)
    """
    analysis = db.query(Analysis).options(joinedload(Analysis.document)).filter(Analysis.id == id).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Réglementation non trouvée")
    
    return map_analysis_to_regulation(analysis)


@router.put("/{id}/status", response_model=RegulationResponse)
def update_regulation_status(
    id: str,
    request: UpdateRegulationStatusRequest,
    db: Session = Depends(get_db)
):
    """
    Met à jour le statut de validation d'une réglementation.
    
    Utilisé par l'équipe juridique pour valider/rejeter les analyses.
    """
    analysis = db.query(Analysis).options(joinedload(Analysis.document)).filter(Analysis.id == id).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Réglementation non trouvée")
    
    # Mapper le statut frontend → backend
    status_mapping = {
        'validated': 'approved',
        'rejected': 'rejected',
        'to-review': 'pending'
    }
    
    backend_status = status_mapping.get(request.status, request.status)
    
    # Mettre à jour l'analyse
    analysis.validation_status = backend_status
    analysis.validation_comment = request.comment
    analysis.validated_by = "juriste@hutchinson.com"  # TODO: récupérer l'utilisateur authentifié
    analysis.validated_at = datetime.utcnow()
    
    # Mettre à jour le workflow du document
    if backend_status == 'approved':
        analysis.document.workflow_status = 'validated'
        analysis.document.validated_at = datetime.utcnow()
    elif backend_status == 'rejected':
        analysis.document.workflow_status = 'rejected_analysis'
    
    db.commit()
    db.refresh(analysis)
    
    return map_analysis_to_regulation(analysis)


@router.get("/stats", response_model=RegulationStatsResponse)
def get_regulation_stats(db: Session = Depends(get_db)):
    """
    Récupère les statistiques des réglementations.
    """
    total = db.query(Analysis).count()
    
    # Compter par statut
    pending_count = db.query(Analysis).filter(Analysis.validation_status == 'pending').count()
    approved_count = db.query(Analysis).filter(Analysis.validation_status == 'approved').count()
    rejected_count = db.query(Analysis).filter(Analysis.validation_status == 'rejected').count()
    
    # Compter les récentes (dernière semaine)
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_count = db.query(Analysis).filter(Analysis.created_at >= week_ago).count()
    
    # Priorités hautes (confidence > 0.8)
    high_priority = db.query(Analysis).filter(
        Analysis.confidence > 0.8,
        Analysis.validation_status == 'pending'
    ).count()
    
    return RegulationStatsResponse(
        total=total,
        by_status={
            'pending': pending_count,
            'validated': approved_count,
            'rejected': rejected_count
        },
        recent_count=recent_count,
        high_priority=high_priority
    )
