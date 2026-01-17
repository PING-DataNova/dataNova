"""
Agent 1A - Collecte et analyse de documents réglementaires via EUR-Lex (SCÉNARIO 2 OPTIMISÉ)

Version EUR-Lex : Recherche directement sur EUR-Lex au lieu de la page Commission

Agent ReAct utilisant Claude 3.5 Sonnet avec 3 outils :
- EUR-Lex Searcher : Recherche de documents sur EUR-Lex par mot-clé
- Document Fetcher : Téléchargement de documents
- PDF Extractor : Extraction de contenu (texte, tableaux, codes NC)

SCÉNARIO 2 : Vérification avant téléchargement + Sauvegarde en BDD

Responsable: Dev 1

Note: Le résumé des documents est généré par Agent 1B (Phase 3)
Agent 1A se concentre uniquement sur la collecte et l'extraction du contenu
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
import structlog
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from src.config import settings

# Charger les variables d'environnement depuis .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from .tools import get_agent_1a_tools
from .tools.eurlex_scraper import search_eurlex
from .tools.document_fetcher import fetch_document
from .tools.pdf_extractor import extract_pdf_content

logger = structlog.get_logger()


def create_agent_1a(
    model_name: str = "claude-3-haiku-20240307",
    temperature: float = 0.1,
    max_tokens: int = 4096
):
    """
    Crée l'Agent 1A avec Claude 3.5 Haiku et ses outils.

    Args:
        model_name: Modèle Anthropic à utiliser
        temperature: Température de génération (0.0 = déterministe)
        max_tokens: Nombre maximum de tokens
    
    Returns:
        Agent LangGraph prêt à l'emploi
    """
    logger.info("agent_1a_initialization_started", model=model_name)
    
    # 1. Initialiser le modèle Claude
    llm = ChatAnthropic(
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=settings.anthropic_api_key,
        timeout=60,
        max_retries=1
    )
    
    # 2. Récupérer les outils
    tools = get_agent_1a_tools()
    logger.info("agent_1a_tools_loaded", tool_count=len(tools))
    
    # 3. Créer le prompt système
    system_prompt = """Tu es l'Agent 1A, spécialisé dans la collecte automatisée de documents réglementaires via EUR-Lex.

WORKFLOW COMPLET :
1. Rechercher sur EUR-Lex avec search_eurlex_tool (mot-clé fourni par l'utilisateur)
2. Pour CHAQUE document trouvé :
   a. Télécharger le PDF avec fetch_document_tool (utiliser pdf_url si disponible, sinon url)
   b. Extraire le contenu avec extract_pdf_content_tool
3. Retourner le JSON final avec TOUS les documents enrichis

RÈGLES IMPORTANTES :
- Traiter TOUS les documents trouvés (ou jusqu'à la limite spécifiée)
- Format de sortie : JSON avec la structure exacte demandée
- Ne pas arrêter tant que tous les documents n'ont pas été traités
- Utiliser pdf_url en priorité pour le téléchargement

FORMAT DE SORTIE ATTENDU :
{
  "documents": [
    {
      "title": "...",
      "celex_number": "32023R0956",
      "document_type": "REGULATION|DIRECTIVE|DECISION|PROPOSAL",
      "publication_date": "YYYY-MM-DDTHH:MM:SS",
      "url": "...",
      "pdf_url": "...",
      "status": "ACTIVE_LAW|PROPOSAL|DECISION"
    }
  ]
}"""
    
    # 4. Créer l'agent avec LangGraph
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt
    )
    
    logger.info("agent_1a_initialization_completed")
    return agent


async def run_agent_1a_eurlex_scenario_2(
    keyword: str = "CBAM",
    max_documents: int = 10
) -> dict:
    """
    Exécute l'Agent 1A avec Scénario 2 optimisé :
    - Scrape EUR-Lex
    - Vérifie les documents existants en BDD
    - Télécharge SEULEMENT les nouveaux/modifiés
    - Extrait le contenu
    - Sauvegarde en BDD
    
    Args:
        keyword: Mot-clé de recherche (CBAM, EUDR, CSRD, etc.)
        max_documents: Nombre maximum de documents à traiter
    
    Returns:
        dict: Résultat avec résumé et documents traités
    """
    logger.info("agent_1a_eurlex_scenario_2_started", keyword=keyword, max_documents=max_documents)
    
    try:
        from src.storage.database import get_session
        from src.storage.repositories import DocumentRepository
        from datetime import datetime
        import hashlib
        
        # ====================================================================
        # ÉTAPE 1 : SCRAPER EUR-LEX
        # ====================================================================
        logger.info("step_1_scraping", keyword=keyword)
        
        search_results = await search_eurlex(keyword, max_results=max_documents)
        
        if search_results.status != "success":
            logger.error("eurlex_search_failed", error=search_results.error)
            return {
                "status": "error",
                "keyword": keyword,
                "error": f"EUR-Lex search failed: {search_results.error}"
            }
        
        logger.info("step_1_completed", documents_found=len(search_results.documents))
        
        # ====================================================================
        # ÉTAPE 2 : VÉRIFIER LES DOCUMENTS EXISTANTS EN BDD
        # ====================================================================
        logger.info("step_2_checking_existing_documents")
        
        session = get_session()
        repo = DocumentRepository(session)
        
        documents_to_process = []
        documents_unchanged = []
        
        try:
            for doc in search_results.documents:
                url = str(doc.url)
                
                # Chercher en BDD
                existing_doc = repo.find_by_url(url)
                
                if existing_doc:
                    # Document existe : comparer les hash
                    if existing_doc.hash_sha256 == doc.metadata.get("remote_hash"):
                        # Hash identique : document inchangé
                        logger.info("document_unchanged", url=url)
                        documents_unchanged.append(doc)
                    else:
                        # Hash différent : document modifié
                        logger.info("document_modified", url=url)
                        documents_to_process.append(doc)
                else:
                    # Document n'existe pas : nouveau
                    logger.info("document_new", url=url)
                    documents_to_process.append(doc)
            
            logger.info(
                "step_2_completed",
                total=len(search_results.documents),
                to_process=len(documents_to_process),
                unchanged=len(documents_unchanged)
            )
            
            # ====================================================================
            # ÉTAPE 3 : TÉLÉCHARGER ET TRAITER LES DOCUMENTS NOUVEAUX/MODIFIÉS
            # ====================================================================
            logger.info("step_3_downloading_and_processing", count=len(documents_to_process))
            
            documents_processed = []
            
            for doc in documents_to_process:
                try:
                    # Télécharger le PDF
                    pdf_url = str(doc.pdf_url) if doc.pdf_url else str(doc.url)
                    logger.info("downloading_document", celex=doc.celex_number, url=pdf_url)
                    
                    fetch_result = await fetch_document(pdf_url, output_dir="data/documents")
                    
                    if not fetch_result.success:
                        logger.error("document_fetch_failed", url=pdf_url, error=fetch_result.error)
                        continue
                    
                    fetched_doc = fetch_result.document
                    logger.info("document_downloaded", celex=doc.celex_number, size=fetched_doc.file_size)
                    
                    # Extraire le contenu
                    logger.info("extracting_content", celex=doc.celex_number)
                    extracted = await extract_pdf_content(fetched_doc.file_path)
                    
                    if extracted.status != "success":
                        logger.error("document_extraction_failed", file=fetched_doc.file_path, error=extracted.error)
                        continue
                    
                    logger.info(
                        "content_extracted",
                        celex=doc.celex_number,
                        text_length=len(extracted.text),
                        nc_codes=len(extracted.nc_codes)
                    )
                    
                    # ================================================================
                    # ÉTAPE 4 : SAUVEGARDER EN BDD
                    # ================================================================
                    logger.info("saving_to_database", celex=doc.celex_number)
                    
                    # Convertir publication_date en datetime si c'est une string ISO
                    pub_date = None
                    if doc.publication_date:
                        if isinstance(doc.publication_date, str):
                            try:
                                pub_date = datetime.fromisoformat(doc.publication_date.replace('Z', '+00:00'))
                            except (ValueError, AttributeError):
                                pub_date = None
                        elif isinstance(doc.publication_date, datetime):
                            pub_date = doc.publication_date
                    
                    document, db_status = repo.upsert_document(
                        source_url=str(doc.url),
                        hash_sha256=fetched_doc.hash_sha256,
                        title=doc.title,
                        content=extracted.text,
                        nc_codes=[code.code for code in extracted.nc_codes],
                        regulation_type="CBAM",
                        publication_date=pub_date,
                        document_metadata={
                            "celex_number": doc.celex_number,
                            "document_type": doc.document_type,
                            "status": doc.status,
                            "pdf_url": str(doc.pdf_url) if doc.pdf_url else None,
                            "file_size": fetched_doc.file_size,
                            "nc_codes_count": len(extracted.nc_codes)
                        }
                    )
                    
                    logger.info("document_saved", document_id=document.id, status=db_status)
                    
                    documents_processed.append({
                        "document_id": document.id,
                        "title": document.title,
                        "celex_number": doc.celex_number,
                        "status": db_status,
                        "nc_codes_count": len(extracted.nc_codes),
                        "content_length": len(extracted.text)
                    })
                    
                except Exception as e:
                    logger.error("document_processing_error", error=str(e), url=str(doc.url), exc_info=True)
                    continue
            
            repo.commit()
            logger.info("step_3_completed", documents_processed=len(documents_processed))
            
            # ====================================================================
            # RÉSULTAT FINAL
            # ====================================================================
            logger.info(
                "agent_1a_eurlex_scenario_2_completed",
                processed=len(documents_processed),
                status="success"
            )
            
            return {
                "status": "success",
                "keyword": keyword,
                "summary": {
                    "total_found": len(search_results.documents),
                    "documents_processed": len(documents_processed),
                    "documents_unchanged": len(documents_unchanged)
                },
                "documents_processed": documents_processed
            }
            
        except Exception as e:
            repo.rollback()
            logger.error("agent_1a_eurlex_scenario_2_error", error=str(e), exc_info=True)
            return {
                "status": "error",
                "keyword": keyword,
                "error": str(e)
            }
        finally:
            session.close()
    
    except Exception as e:
        logger.error("agent_1a_eurlex_scenario_2_error", error=str(e), exc_info=True)
        return {
            "status": "error",
            "keyword": keyword,
            "error": str(e)
        }


# Pour tester l'agent directement
if __name__ == "__main__":
    import asyncio
    
    async def test_agent():
        print("=" * 80)
        print("🤖 TEST AGENT 1A EUR-LEX - SCÉNARIO 2 OPTIMISÉ (SANS RÉSUMÉ)")
        print("=" * 80)
        
        result = await run_agent_1a_eurlex_scenario_2(keyword="CBAM", max_documents=3)
        
        if result["status"] == "error":
            print(f"\n❌ Erreur: {result['error']}")
        else:
            print(f"\n✅ Exécution réussie\n")
            print(f"📊 Résumé:")
            print(f"  - Total trouvés: {result['summary']['total_found']}")
            print(f"  - Traités: {result['summary']['documents_processed']}")
            print(f"  - Inchangés (skippés): {result['summary']['documents_unchanged']}")
            
            print(f"\n📄 Documents traités:\n")
            for i, doc in enumerate(result['documents_processed'], 1):
                print(f"{i}. {doc['title'][:60]}...")
                print(f"   CELEX: {doc['celex_number']}")
                print(f"   Status: {doc['status']}")
                print(f"   Codes NC: {doc['nc_codes_count']}")
                print(f"   Taille: {doc['content_length']} caractères")
                print()
        
        print("=" * 80)
        print("✅ Test terminé !")
        print("=" * 80)
    
    asyncio.run(test_agent())