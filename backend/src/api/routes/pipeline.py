"""
Routes pour déclencher manuellement le pipeline de veille réglementaire.

Utile pour les démos et les tests sans attendre le scheduler hebdomadaire.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import structlog

from src.orchestration.pipeline import run_pipeline

logger = structlog.get_logger()

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


class PipelineRequest(BaseModel):
    """Paramètres pour déclencher le pipeline."""
    keyword: str = "CBAM"
    max_eurlex_documents: int = 10
    cbam_categories: str = "all"
    max_cbam_documents: int = 50


class PipelineStatus(BaseModel):
    """Statut du pipeline."""
    status: str
    message: str
    details: Optional[dict] = None


# Variable globale pour suivre si un pipeline est en cours
_pipeline_running = False


@router.post("/trigger", response_model=PipelineStatus)
async def trigger_pipeline(
    request: PipelineRequest = PipelineRequest(),
    background_tasks: BackgroundTasks = None
):
    """
    Déclenche manuellement le pipeline de veille réglementaire.
    
    Le pipeline s'exécute en arrière-plan pour ne pas bloquer la requête.
    
    - **keyword**: Mot-clé de recherche EUR-Lex (CBAM, EUDR, CSRD, etc.)
    - **max_eurlex_documents**: Nombre max de documents EUR-Lex à collecter
    - **cbam_categories**: Catégories CBAM (all, guidance, faq, legislation)
    - **max_cbam_documents**: Nombre max de documents CBAM
    """
    global _pipeline_running
    
    if _pipeline_running:
        raise HTTPException(
            status_code=409,
            detail="Un pipeline est déjà en cours d'exécution. Veuillez patienter."
        )
    
    logger.info(
        "pipeline_trigger_requested",
        keyword=request.keyword,
        max_eurlex=request.max_eurlex_documents,
        cbam_categories=request.cbam_categories
    )
    
    # Lancer en arrière-plan
    background_tasks.add_task(
        _run_pipeline_background,
        request.keyword,
        request.max_eurlex_documents,
        request.cbam_categories,
        request.max_cbam_documents
    )
    
    return PipelineStatus(
        status="started",
        message="Pipeline démarré en arrière-plan",
        details={
            "keyword": request.keyword,
            "max_eurlex_documents": request.max_eurlex_documents,
            "cbam_categories": request.cbam_categories,
            "max_cbam_documents": request.max_cbam_documents
        }
    )


@router.post("/trigger-sync", response_model=PipelineStatus)
async def trigger_pipeline_sync(request: PipelineRequest = PipelineRequest()):
    """
    Déclenche le pipeline de façon SYNCHRONE (bloquant).
    
    Attend la fin de l'exécution avant de retourner le résultat.
    Utile pour les tests et le debugging.
    
    ⚠️ Peut prendre plusieurs minutes selon le nombre de documents.
    """
    global _pipeline_running
    
    if _pipeline_running:
        raise HTTPException(
            status_code=409,
            detail="Un pipeline est déjà en cours d'exécution. Veuillez patienter."
        )
    
    _pipeline_running = True
    
    try:
        logger.info("pipeline_sync_started", keyword=request.keyword)
        
        result = run_pipeline(
            keyword=request.keyword,
            max_eurlex_documents=request.max_eurlex_documents,
            cbam_categories=request.cbam_categories,
            max_cbam_documents=request.max_cbam_documents
        )
        
        logger.info("pipeline_sync_completed", result=result)
        
        return PipelineStatus(
            status="completed",
            message="Pipeline terminé avec succès",
            details=result
        )
        
    except Exception as e:
        logger.error("pipeline_sync_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'exécution du pipeline: {str(e)}"
        )
    finally:
        _pipeline_running = False


@router.get("/status", response_model=PipelineStatus)
async def get_pipeline_status():
    """
    Vérifie si un pipeline est actuellement en cours d'exécution.
    """
    global _pipeline_running
    
    if _pipeline_running:
        return PipelineStatus(
            status="running",
            message="Un pipeline est en cours d'exécution"
        )
    
    return PipelineStatus(
        status="idle",
        message="Aucun pipeline en cours"
    )


def _run_pipeline_background(
    keyword: str,
    max_eurlex_documents: int,
    cbam_categories: str,
    max_cbam_documents: int
):
    """Exécute le pipeline en arrière-plan."""
    global _pipeline_running
    _pipeline_running = True
    
    try:
        logger.info("pipeline_background_started", keyword=keyword)
        
        result = run_pipeline(
            keyword=keyword,
            max_eurlex_documents=max_eurlex_documents,
            cbam_categories=cbam_categories,
            max_cbam_documents=max_cbam_documents
        )
        
        logger.info("pipeline_background_completed", result=result)
        
    except Exception as e:
        logger.error("pipeline_background_failed", error=str(e), exc_info=True)
    finally:
        _pipeline_running = False
