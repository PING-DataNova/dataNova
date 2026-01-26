"""
Pipeline de coordination des agents

Orchestration du workflow: Agent 1A → Agent 1B → Notifications
"""

import asyncio
import structlog
from typing import Dict

from src.storage.database import get_session
from src.storage.models import Document
from src.agent_1a.agent import run_agent_1a_combined
from src.agent_1b.agent import Agent1B
from src.agent_1b.display import process_and_display_analysis

logger = structlog.get_logger()


def run_pipeline(
    keyword: str = "CBAM",
    max_eurlex_documents: int = 10,
    cbam_categories: str = "all",
    max_cbam_documents: int = 50
) -> Dict:
    """
    Exécute le pipeline complet de veille réglementaire.
    
    Workflow:
    1. Lancer Agent 1A pour collecter les nouveaux documents
    2. Si Agent 1A réussit → Charger le profil entreprise
    3. Récupérer les documents NON ANALYSÉS (workflow_status = 'raw')
    4. Pour chaque document:
       - Lancer Agent 1B pour l'analyser
       - Mettre à jour workflow_status = 'analyzed'
    5. Retourner les statistiques
    
    Args:
        keyword: Mot-clé pour EUR-Lex (CBAM, EUDR, CSRD)
        max_eurlex_documents: Nombre max de documents EUR-Lex
        cbam_categories: Catégories CBAM (all, guidance, faq, etc.)
        max_cbam_documents: Nombre max de documents CBAM
        
    Returns:
        dict: Résultat avec statistiques complètes
    """
    
    logger.info("pipeline_started")
    
    try:
        # ====================================================================
        # ÉTAPE 1 : AGENT 1A - COLLECTE DES DOCUMENTS
        # ====================================================================
        logger.info("step_1_launching_agent_1a")
        
        result_1a = asyncio.run(run_agent_1a_combined(
            keyword=keyword,
            max_eurlex_documents=max_eurlex_documents,
            cbam_categories=cbam_categories,
            max_cbam_documents=max_cbam_documents
        ))
        
        # Vérifier si Agent 1A a réussi
        if result_1a.get("status") != "success":
            error_msg = result_1a.get("error", "Unknown error")
            logger.error("agent_1a_failed", error=error_msg)
            raise Exception(f"Agent 1A failed: {error_msg}")
        
        logger.info(
            "agent_1a_completed",
            documents_processed=result_1a.get("documents_processed", 0),
            documents_unchanged=result_1a.get("documents_unchanged", 0)
        )
        
        # ====================================================================
        # ÉTAPE 2 : CHARGER LE PROFIL ENTREPRISE
        # ====================================================================
        logger.info("step_2_loading_company_profile")
        
        company_profile = load_company_profile()
        
        logger.info(
            "company_profile_loaded",
            company=company_profile.get("company_name"),
            keywords=len(company_profile.get("keywords", [])),
            nc_codes=len(company_profile.get("nc_codes", {}))
        )
        
        # ====================================================================
        # ÉTAPE 3 : RÉCUPÉRER LES DOCUMENTS NON ANALYSÉS
        # ====================================================================
        logger.info("step_3_fetching_unanalyzed_documents")
        
        session = get_session()
        
        try:
            # Chercher les documents avec workflow_status = 'raw'
            unanalyzed_docs = session.query(Document).filter(
                Document.workflow_status == "raw"
            ).all()
            
            logger.info(
                "unanalyzed_documents_found",
                count=len(unanalyzed_docs)
            )
            
            if len(unanalyzed_docs) == 0:
                logger.info("no_documents_to_analyze")
                return {
                    "status": "success",
                    "agent_1a": result_1a,
                    "agent_1b": {
                        "documents_analyzed": 0,
                        "relevant_count": 0,
                        "critical_count": 0
                    }
                }
            
            # ====================================================================
            # ÉTAPE 4 : AGENT 1B - ANALYSE DES DOCUMENTS
            # ====================================================================
            logger.info("step_4_launching_agent_1b", count=len(unanalyzed_docs))
            
            agent = Agent1B(company_profile)
            
            analyses_created = []
            relevant_count = 0
            critical_count = 0
            analysis_errors = []
            
            for idx, doc in enumerate(unanalyzed_docs, 1):
                try:
                    logger.info(
                        "analyzing_document",
                        index=f"{idx}/{len(unanalyzed_docs)}",
                        document_id=doc.id,
                        title=doc.title[:60]
                    )
                    
                    # Analyser le document
                    analysis = agent.analyze_document(
                        document_id=doc.id,
                        document_content=doc.content or "",
                        document_title=doc.title,
                        regulation_type=doc.regulation_type or "CBAM"
                    )
                    
                    # Sauvegarder l'analyse en BDD
                    analysis_id = process_and_display_analysis(analysis, save_to_db=True)
                    
                    if analysis_id:
                        analyses_created.append(analysis_id)
                    
                    # Compter les stats
                    if analysis.is_relevant:
                        relevant_count += 1
                    if analysis.relevance_score.criticality.value == "CRITICAL":
                        critical_count += 1
                    
                    # Mettre à jour le workflow_status
                    doc.workflow_status = "analyzed"
                    doc.analyzed_at = analysis.analysis_timestamp
                    session.commit()
                    
                    logger.info(
                        "document_analyzed",
                        document_id=doc.id,
                        is_relevant=analysis.is_relevant,
                        criticality=analysis.relevance_score.criticality.value
                    )
                    
                except Exception as e:
                    logger.error(
                        "analysis_failed",
                        document_id=doc.id,
                        error=str(e),
                        exc_info=True
                    )
                    analysis_errors.append({
                        "document_id": doc.id,
                        "error": str(e)
                    })
                    session.rollback()
            
            logger.info(
                "agent_1b_completed",
                analyzed=len(analyses_created),
                relevant=relevant_count,
                critical=critical_count,
                errors=len(analysis_errors)
            )
            
            # ====================================================================
            # RÉSULTAT FINAL
            # ====================================================================
            
            result = {
                "status": "success",
                "agent_1a": result_1a,
                "agent_1b": {
                    "documents_analyzed": len(analyses_created),
                    "relevant_count": relevant_count,
                    "critical_count": critical_count,
                    "errors": len(analysis_errors)
                }
            }
            
            logger.info("pipeline_completed", result=result)
            
            return result
            
        finally:
            session.close()
        
    except Exception as e:
        logger.error("pipeline_failed", error=str(e), exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


def load_company_profile(company_name: str = "HUTCHINSON") -> dict:
    """
    Charge le profil de l'entreprise depuis la base de données.
    
    Args:
        company_name: Nom de l'entreprise (défaut: Hutchinson SA)
    
    Returns:
        dict: Profil entreprise formatté pour Agent 1B
        
    Raises:
        ValueError: Si le profil n'existe pas en BDD
    """
    from src.storage.repositories import CompanyProfileRepository
    
    session = get_session()
    
    try:
        repo = CompanyProfileRepository(session)
        profile = repo.find_by_name(company_name)
        
        if not profile:
            raise ValueError(
                f"Profil entreprise '{company_name}' non trouvé en BDD. "
                f"Exécutez d'abord: python scripts/init_db.py"
            )
        
        if not profile.active:
            raise ValueError(f"Profil entreprise '{company_name}' est désactivé")
        
        return {
            "company_id": profile.id,
            "company_name": profile.company_name,
            "nc_codes": profile.nc_codes or [],
            "keywords": profile.keywords or [],
            "regulations": profile.regulations or ["CBAM"],
            "contact_emails": profile.contact_emails or [],
            "config": profile.config or {}
        }
    
    finally:
        session.close()
