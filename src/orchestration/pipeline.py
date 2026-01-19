"""
Pipeline de coordination des agents

Orchestration du workflow: Agent 1A → Agent 1B → [UI Validation] → Agent 2 → Notifications

"""

import json
from pathlib import Path

import structlog

from src.config import settings
from src.storage.database import get_session
from src.storage.repositories import CompanyProfileRepository

logger = structlog.get_logger()


def run_pipeline():
    """
    Exécute le pipeline Agent 1A → Agent 1B (Phase 2-3).
    
    Workflow:
    1. Charger la configuration (sources CBAM)
    2. Lancer Agent 1A pour scraper et détecter les nouveaux documents
    3. Pour chaque nouveau document:
       - Lancer Agent 1B pour analyser
       - Sauvegarder Analysis avec validation_status="pending"
    4. Logger les statistiques d'exécution
    
    Notes:
    - Pas de notifications ici (Phase 4 uniquement après Agent 2)
    - UI poll GET /api/analyses?validation_status=pending pour validation
    - Agent 2 sera déclenché après validation UI (Phase 4)
    """
    
    logger.info("pipeline_démarré")
    
    try:
        # TODO (DEV 3): Implémenter le pipeline complet
        
        # 1. Charger la configuration
        logger.info("chargement_configuration")
        sources = load_sources_config()
        company_profile = load_company_profile()
        
        # 2. Lancer Agent 1A
        logger.info("lancement_agent_1a")
        new_documents = run_agent_1a_pipeline(sources)
        logger.info("agent_1a_terminé", nb_documents=len(new_documents))
        
        # 3. Analyser chaque document avec Agent 1B
        # Note: Agent 1B sauvegarde lui-même via son outil save_analysis()
        analyses_count = 0
        for doc in new_documents:
            logger.info("analyse_document", document_id=doc["id"])
            run_agent_1b_pipeline(doc, company_profile)
            analyses_count += 1
        
        logger.info(
            "pipeline_terminé",
            nb_documents_analysés=len(new_documents),
            nb_analyses=analyses_count
        )
        
        return {
            "status": "success",
            "documents_analyzed": len(new_documents),
            "analyses_created": analyses_count
        }
        
    except Exception as e:
        logger.error("pipeline_erreur", error=str(e), exc_info=True)
        raise


def load_sources_config() -> list:
    """
    Charge la configuration des sources à surveiller depuis sources_config.json.
    
    Returns:
        Liste des sources activées (enabled=True)
    """
    config_path = settings.data_dir / "sources_config.json"
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        # Retourner uniquement les sources activées
        enabled_sources = []
        for source in config_data.get("sources", []):
            if source.get("enabled", False):
                enabled_sources.append(source)
        
        logger.info(
            "sources_chargées",
            total=len(config_data.get("sources", [])),
            enabled=len(enabled_sources)
        )
        
        return enabled_sources
        
    except FileNotFoundError:
        logger.error("sources_config_introuvable", path=str(config_path))
        return []
    except json.JSONDecodeError as e:
        logger.error("sources_config_json_invalide", error=str(e))
        return []


def load_company_profile() -> dict:
    """
    Charge le profil de l'entreprise depuis la base de données.
    
    Utilise settings.default_company_profile pour identifier l'entreprise.
    
    Returns:
        Dictionnaire avec les données du profil ou {} si non trouvé
    """
    session = get_session()
    repo = CompanyProfileRepository(session)
    
    try:
        profile = repo.find_by_name(settings.default_company_profile)
        
        if not profile:
            logger.warning(
                "profil_entreprise_introuvable",
                name=settings.default_company_profile
            )
            return {}
        
        logger.info(
            "profil_entreprise_chargé",
            company=profile.company_name,
            nc_codes=len(profile.nc_codes or [])
        )
        
        # Convertir le modèle en dict 
        return {
            "id": profile.id,
            "company_name": profile.company_name,
            "nc_codes": profile.nc_codes or [],
            "keywords": profile.keywords or [],
            "regulations": profile.regulations or [],
            "contact_emails": profile.contact_emails or [],
            "config": profile.config or {}
        }
        
    except Exception as e:
        logger.error("erreur_chargement_profil", error=str(e))
        return {}
    finally:
        session.close()


def run_agent_1a_pipeline(sources: list) -> list:
    """
    Exécute Agent 1A pour toutes les sources configurées.
    
    Agent 1A utilise son outil save_document_data() pour sauvegarder.
    """
    import asyncio
    from src.agent_1a.agent import run_agent_1a_eurlex
    
    logger.info("agent_1a_pipeline_started", nb_sources=len(sources))
    
    all_documents = []
    
    for source in sources:
        try:
            keyword = source.get("keyword", "CBAM")
            max_docs = source.get("max_documents", 10)
            
            logger.info("processing_source", keyword=keyword, max_docs=max_docs)
            
            # Exécuter l'agent 1A de manière asynchrone
            result = asyncio.run(run_agent_1a_eurlex(keyword, max_documents=max_docs))
            
            if result["status"] == "success":
                documents = result["output"].get("documents", [])
                all_documents.extend(documents)
                logger.info("source_processed", keyword=keyword, nb_docs=len(documents))
            else:
                logger.error("source_failed", keyword=keyword, error=result.get("error"))
        
        except Exception as e:
            logger.error("source_error", keyword=source.get("keyword"), error=str(e))
    
    logger.info("agent_1a_pipeline_completed", total_documents=len(all_documents))
    return all_documents


def run_agent_1b_pipeline(document: dict, company_profile: dict) -> None:
    """
    Exécute Agent 1B pour analyser un document.
    
    Agent 1B utilise son outil save_analysis() pour sauvegarder lui-même
    dans la table 'analyses' avec validation_status="pending".
    """
    from src.agent_1b.agent import run_agent_1b
    
    logger.info("agent_1b_analysis_started", document_id=document.get("id"))
    
    try:
        # L'agent 1B n'est pas encore implémenté
        # Pour l'instant, on log juste l'intention
        logger.warning("agent_1b_not_implemented", document_id=document.get("id"))
        # TODO: Décommenter quand Agent 1B sera implémenté
        # result = run_agent_1b(document["id"], company_profile)
        # logger.info("agent_1b_analysis_completed", document_id=document["id"], result=result)
    
    except Exception as e:
        logger.error("agent_1b_error", document_id=document.get("id"), error=str(e))

