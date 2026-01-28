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


# Variable globale pour suivre si l'Agent 1 est en cours
_agent1_running = False


@router.post("/agent1/trigger", response_model=PipelineStatus)
async def trigger_agent1(
    request: PipelineRequest = PipelineRequest(),
    background_tasks: BackgroundTasks = None
):
    """
    Déclenche l'Agent 1 (collecte et analyse des documents réglementaires).
    
    L'Agent 1 comprend:
    - **Agent 1A**: Collecte des documents depuis EUR-Lex et CBAM
    - **Agent 1B**: Analyse de pertinence avec le profil entreprise
    
    Paramètres:
    - **keyword**: Mot-clé de recherche (CBAM, EUDR, CSRD, etc.)
    - **max_eurlex_documents**: Nombre max de documents EUR-Lex
    - **cbam_categories**: Catégories CBAM (all, guidance, faq, legislation)
    - **max_cbam_documents**: Nombre max de documents CBAM
    """
    global _agent1_running
    
    if _agent1_running:
        raise HTTPException(
            status_code=409,
            detail="L'Agent 1 est déjà en cours d'exécution. Veuillez patienter."
        )
    
    # Compter les documents existants
    from src.storage.database import get_session
    from src.storage.repositories import DocumentRepository, AnalysisRepository
    
    session = get_session()
    try:
        doc_repo = DocumentRepository(session)
        analysis_repo = AnalysisRepository(session)
        
        docs_before = doc_repo.count_by_status()
        total_docs = sum(docs_before.values())
        total_analyses = len(analysis_repo.find_by_validation_status("pending"))
    finally:
        session.close()
    
    logger.info(
        "agent1_trigger_requested",
        keyword=request.keyword,
        max_eurlex=request.max_eurlex_documents,
        cbam_categories=request.cbam_categories
    )
    
    # Lancer en arrière-plan
    background_tasks.add_task(
        _run_agent1_background,
        request.keyword,
        request.max_eurlex_documents,
        request.cbam_categories,
        request.max_cbam_documents
    )
    
    return PipelineStatus(
        status="started",
        message=f"✅ Agent 1 démarré - Recherche '{request.keyword}'",
        details={
            "keyword": request.keyword,
            "max_eurlex_documents": request.max_eurlex_documents,
            "cbam_categories": request.cbam_categories,
            "max_cbam_documents": request.max_cbam_documents,
            "documents_in_db_before": total_docs,
            "analyses_pending_before": total_analyses,
            "note": "Utilisez GET /api/pipeline/agent1/status pour suivre la progression"
        }
    )


@router.post("/agent1/trigger-sync", response_model=PipelineStatus)
async def trigger_agent1_sync(request: PipelineRequest = PipelineRequest()):
    """
    Déclenche l'Agent 1 de façon SYNCHRONE (bloquant).
    
    Attend la fin de l'exécution avant de retourner le résultat complet.
    ⚠️ Peut prendre plusieurs minutes selon le nombre de documents.
    """
    global _agent1_running
    
    if _agent1_running:
        raise HTTPException(
            status_code=409,
            detail="L'Agent 1 est déjà en cours d'exécution. Veuillez patienter."
        )
    
    _agent1_running = True
    
    try:
        logger.info("agent1_sync_started", keyword=request.keyword)
        
        result = run_pipeline(
            keyword=request.keyword,
            max_eurlex_documents=request.max_eurlex_documents,
            cbam_categories=request.cbam_categories,
            max_cbam_documents=request.max_cbam_documents
        )
        
        logger.info("agent1_sync_completed", result=result)
        
        # Construire un message clair
        agent1a = result.get("agent_1a", {})
        agent1b = result.get("agent_1b", {})
        
        docs_processed = agent1a.get("documents_processed", 0)
        docs_found = agent1a.get("total_found", 0)
        analyses_created = agent1b.get("documents_analyzed", 0)
        relevant_count = agent1b.get("relevant_count", 0)
        
        return PipelineStatus(
            status="completed",
            message=f"✅ Agent 1 terminé - {docs_found} docs trouvés, {docs_processed} traités, {analyses_created} analyses créées ({relevant_count} pertinentes)",
            details=result
        )
        
    except Exception as e:
        logger.error("agent1_sync_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"❌ Erreur Agent 1: {str(e)}"
        )
    finally:
        _agent1_running = False


@router.get("/agent1/status", response_model=PipelineStatus)
async def get_agent1_status():
    """
    Vérifie si l'Agent 1 est en cours d'exécution et donne des statistiques.
    """
    global _agent1_running
    
    # Récupérer des stats depuis la base
    from src.storage.database import get_session
    from src.storage.repositories import DocumentRepository, AnalysisRepository
    
    session = get_session()
    try:
        doc_repo = DocumentRepository(session)
        analysis_repo = AnalysisRepository(session)
        
        docs_by_status = doc_repo.count_by_status()
        total_docs = sum(docs_by_status.values())
        
        pending_analyses = len(analysis_repo.find_by_validation_status("pending"))
        approved_analyses = len(analysis_repo.find_by_validation_status("approved"))
        rejected_analyses = len(analysis_repo.find_by_validation_status("rejected"))
    finally:
        session.close()
    
    if _agent1_running:
        return PipelineStatus(
            status="running",
            message="⏳ L'Agent 1 est en cours d'exécution...",
            details={
                "documents_total": total_docs,
                "documents_by_status": docs_by_status,
                "analyses_pending": pending_analyses,
                "analyses_approved": approved_analyses
            }
        )
    
    return PipelineStatus(
        status="idle",
        message="Agent 1 prêt",
        details={
            "documents_total": total_docs,
            "documents_by_status": docs_by_status,
            "analyses_pending": pending_analyses,
            "analyses_approved": approved_analyses,
            "analyses_rejected": rejected_analyses
        }
    )


def _run_agent1_background(
    keyword: str,
    max_eurlex_documents: int,
    cbam_categories: str,
    max_cbam_documents: int
):
    """Exécute l'Agent 1 (pipeline complet) en arrière-plan."""
    global _agent1_running
    _agent1_running = True
    
    try:
        logger.info("agent1_background_started", keyword=keyword)
        
        result = run_pipeline(
            keyword=keyword,
            max_eurlex_documents=max_eurlex_documents,
            cbam_categories=cbam_categories,
            max_cbam_documents=max_cbam_documents
        )
        
        logger.info("agent1_background_completed", result=result)
        
    except Exception as e:
        logger.error("agent1_background_failed", error=str(e), exc_info=True)
    finally:
        _agent1_running = False


# ============================================================
# AGENT 2 - Analyse d'impact
# ============================================================

_agent2_running = False


class Agent2Request(BaseModel):
    """Paramètres pour déclencher l'Agent 2."""
    analysis_id: Optional[str] = None  # Si fourni, analyse uniquement cette analyse
    limit: int = 10  # Nombre max d'analyses à traiter


@router.post("/agent2/trigger", response_model=PipelineStatus)
async def trigger_agent2(
    request: Agent2Request = Agent2Request(),
    background_tasks: BackgroundTasks = None
):
    """
    Déclenche l'Agent 2 pour analyser l'impact des réglementations validées.
    
    L'Agent 2 traite les analyses avec validation_status='approved' et génère
    des ImpactAssessments.
    
    - **analysis_id**: (optionnel) ID d'une analyse spécifique à traiter
    - **limit**: Nombre max d'analyses à traiter (défaut: 10)
    """
    global _agent2_running
    
    if _agent2_running:
        raise HTTPException(
            status_code=409,
            detail="L'Agent 2 est déjà en cours d'exécution. Veuillez patienter."
        )
    
    # Compter les analyses à traiter AVANT de lancer
    from src.storage.database import get_session
    from src.storage.repositories import AnalysisRepository, ImpactAssessmentRepository
    
    session = get_session()
    try:
        analysis_repo = AnalysisRepository(session)
        impact_repo = ImpactAssessmentRepository(session)
        
        # Compter les analyses validées
        approved_analyses = analysis_repo.find_by_validation_status("approved")
        total_approved = len(approved_analyses)
        
        # Compter celles qui n'ont pas encore d'impact assessment
        pending_analyses = []
        for analysis in approved_analyses[:request.limit]:
            existing_impact = impact_repo.find_by_analysis_id(analysis.id)
            if not existing_impact:
                pending_analyses.append(analysis)
        
        analyses_to_process = len(pending_analyses)
        
        if analyses_to_process == 0 and not request.analysis_id:
            return PipelineStatus(
                status="skipped",
                message="⚠️ Aucune analyse à traiter",
                details={
                    "reason": "Toutes les analyses validées ont déjà un impact assessment, ou aucune analyse n'est validée",
                    "total_approved": total_approved,
                    "already_processed": total_approved,
                    "tip": "Validez d'abord des réglementations via l'interface (statut 'approved')"
                }
            )
    finally:
        session.close()
    
    logger.info(
        "agent2_trigger_requested",
        analysis_id=request.analysis_id,
        limit=request.limit,
        analyses_to_process=analyses_to_process
    )
    
    background_tasks.add_task(
        _run_agent2_background,
        request.analysis_id,
        request.limit
    )
    
    return PipelineStatus(
        status="started",
        message=f"✅ Agent 2 démarré - {analyses_to_process} analyse(s) à traiter",
        details={
            "analysis_id": request.analysis_id,
            "limit": request.limit,
            "total_approved": total_approved,
            "analyses_to_process": analyses_to_process,
            "note": "Utilisez GET /api/pipeline/agent2/status pour suivre la progression"
        }
    )


@router.post("/agent2/trigger-sync", response_model=PipelineStatus)
async def trigger_agent2_sync(request: Agent2Request = Agent2Request()):
    """
    Déclenche l'Agent 2 de façon SYNCHRONE (bloquant).
    
    Attend la fin de l'exécution avant de retourner le résultat.
    """
    global _agent2_running
    
    if _agent2_running:
        raise HTTPException(
            status_code=409,
            detail="L'Agent 2 est déjà en cours d'exécution. Veuillez patienter."
        )
    
    _agent2_running = True
    
    try:
        from src.agent_2.agent import Agent2
        
        logger.info("agent2_sync_started", analysis_id=request.analysis_id)
        
        agent = Agent2()
        
        if request.analysis_id:
            result = agent.analyze_impact(request.analysis_id)
        else:
            result = agent.run(validation_status="approved", limit=request.limit)
        
        logger.info("agent2_sync_completed")
        
        # Extraire le contenu de la réponse
        messages = result.get("messages", [])
        content = ""
        if messages:
            last_msg = messages[-1].content
            if isinstance(last_msg, list):
                content = " ".join([
                    item.get("text", "") 
                    for item in last_msg 
                    if isinstance(item, dict) and item.get("type") == "text"
                ])
            else:
                content = str(last_msg)
        
        return PipelineStatus(
            status="completed",
            message="Agent 2 terminé avec succès",
            details={"response": content[:1000] if content else "No response"}
        )
        
    except Exception as e:
        logger.error("agent2_sync_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'exécution de l'Agent 2: {str(e)}"
        )
    finally:
        _agent2_running = False


@router.get("/agent2/status", response_model=PipelineStatus)
async def get_agent2_status():
    """
    Vérifie si l'Agent 2 est actuellement en cours d'exécution et donne des stats.
    """
    global _agent2_running
    
    # Récupérer des stats depuis la base
    from src.storage.database import get_session
    from src.storage.repositories import AnalysisRepository, ImpactAssessmentRepository
    
    session = get_session()
    try:
        analysis_repo = AnalysisRepository(session)
        impact_repo = ImpactAssessmentRepository(session)
        
        # Stats
        approved_analyses = analysis_repo.find_by_validation_status("approved")
        total_approved = len(approved_analyses)
        
        # Compter les impact assessments existants
        from src.storage.models import ImpactAssessment
        total_impacts = session.query(ImpactAssessment).count()
        
    finally:
        session.close()
    
    if _agent2_running:
        return PipelineStatus(
            status="running",
            message="⏳ L'Agent 2 est en cours d'exécution...",
            details={
                "analyses_approved": total_approved,
                "impact_assessments_created": total_impacts
            }
        )
    
    return PipelineStatus(
        status="idle",
        message="Agent 2 prêt",
        details={
            "analyses_approved": total_approved,
            "impact_assessments_created": total_impacts,
            "pending": max(0, total_approved - total_impacts)
        }
    )


def _run_agent2_background(analysis_id: Optional[str], limit: int):
    """Exécute l'Agent 2 en arrière-plan."""
    global _agent2_running
    _agent2_running = True
    
    try:
        from src.agent_2.agent import Agent2
        
        logger.info("agent2_background_started", analysis_id=analysis_id)
        
        agent = Agent2()
        
        if analysis_id:
            result = agent.analyze_impact(analysis_id)
        else:
            result = agent.run(validation_status="approved", limit=limit)
        
        logger.info("agent2_background_completed", result=str(result)[:500])
        
    except Exception as e:
        logger.error("agent2_background_failed", error=str(e), exc_info=True)
    finally:
        _agent2_running = False


# Note: L'ancien endpoint /status a été remplacé par /agent1/status et /agent2/status
