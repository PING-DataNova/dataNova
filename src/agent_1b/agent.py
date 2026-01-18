"""
Agent 1B - Analyse de Pertinence et Génération de Résumé

Analyse la pertinence des documents collectés par l'Agent 1A.
Génère des résumés contextualisés et crée des analyses en BDD.

Responsable: Dev 1
Dépend de: Agent 1A (Phase 2)
Chemin final: src/agent_1b/agent.py
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import structlog
import asyncio
from src.storage.database import get_session
from src.storage.repositories import DocumentRepository, AnalysisRepository
from src.agent_1b.tools.semantic_analyzer import analyze_document_relevance
from src.agent_1b.tools.company_loader import load_company_profile, extract_analysis_profile
from src.storage.models import Document, Analysis

logger = structlog.get_logger()


async def run_agent_1b(
    company_id: str,
    max_documents: int = 10,
    company_profile: Optional[Dict[str, Any]] = None,
    skip_analyzed: bool = True
) -> dict:
    """
    Exécute l'Agent 1B sur les documents en attente d'analyse.
    
    Workflow:
    1. Charger le profil d'entreprise depuis data/company_profiles/
    2. Récupérer les documents avec workflow_status="raw"
    3. Pour chaque document:
       - Analyser la pertinence
       - Générer un résumé
       - Créer une Analysis en BDD
       - Mettre à jour le workflow_status
    4. Retourner un résumé d'exécution
    
    Args:
        company_id: ID de l'entreprise (ex: "GMG-001")
        max_documents: Nombre maximum de documents à traiter
        company_profile: Profil personnalisé (charge depuis company_id si None)
        skip_analyzed: Ignorer les documents déjà analysés
    
    Returns:
        dict: Résumé d'exécution avec statistiques
    """
    
    logger.info(
        "agent_1b_started",
        company_id=company_id,
        max_documents=max_documents,
        skip_analyzed=skip_analyzed
    )
    
    session = get_session()
    doc_repo = DocumentRepository(session)
    analysis_repo = AnalysisRepository(session)
    
    try:
        # ====================================================================
        # ÉTAPE 0 : CHARGER LE PROFIL D'ENTREPRISE
        # ====================================================================
        logger.info("step_0_loading_company_profile", company_id=company_id)
        
        if company_profile is None:
            try:
                company_data = load_company_profile(company_id)
                company_profile = extract_analysis_profile(company_data)
                logger.info(
                    "step_0_company_profile_loaded",
                    company_name=company_profile.get("name"),
                    keywords_count=len(company_profile.get("keywords", [])),
                    nc_codes_count=len(company_profile.get("nc_codes", []))
                )
            except FileNotFoundError as e:
                logger.error("step_0_company_profile_not_found", error=str(e))
                return {
                    "status": "error",
                    "error": f"Profil d'entreprise {company_id} non trouvé: {e}"
                }
        
        # ====================================================================
        # ÉTAPE 1 : RÉCUPÉRER LES DOCUMENTS EN ATTENTE
        # ====================================================================
        logger.info("step_1_fetching_pending_documents")
        
        # Requête pour récupérer les documents non analysés
        query = session.query(Document).filter_by(workflow_status="raw")
        
        if skip_analyzed:
            # Récupérer les IDs des documents déjà analysés
            analyzed_doc_ids = session.query(Analysis.document_id).distinct().all()
            analyzed_ids = [doc_id[0] for doc_id in analyzed_doc_ids]
            
            if analyzed_ids:
                query = query.filter(~Document.id.in_(analyzed_ids))
        
        pending_documents = query.limit(max_documents).all()
        
        logger.info("step_1_completed", documents_found=len(pending_documents))
        
        if not pending_documents:
            logger.info("no_pending_documents")
            return {
                "status": "success",
                "message": "Aucun document en attente d'analyse",
                "documents_processed": 0,
                "documents_relevant": 0,
                "documents_irrelevant": 0,
                "analyses_created": []
            }
        
        # ====================================================================
        # ÉTAPE 2 : ANALYSER CHAQUE DOCUMENT
        # ====================================================================
        logger.info("step_2_analyzing_documents", count=len(pending_documents))
        
        analyses_created = []
        documents_relevant = 0
        documents_irrelevant = 0
        errors = []
        
        for idx, doc in enumerate(pending_documents, 1):
            try:
                logger.info(
                    "analyzing_document",
                    document_index=idx,
                    document_id=doc.id,
                    title=doc.title[:60]
                )
                
                # Extraire les codes NC du JSON
                nc_codes = []
                if doc.nc_codes:
                    if isinstance(doc.nc_codes, str):
                        nc_codes = json.loads(doc.nc_codes)
                    else:
                        nc_codes = doc.nc_codes
                
                # Extraire les métadonnées
                document_metadata = {}
                if doc.document_metadata:
                    if isinstance(doc.document_metadata, str):
                        document_metadata = json.loads(doc.document_metadata)
                    else:
                        document_metadata = doc.document_metadata
                
                # Analyser la pertinence
                analysis_result = await analyze_document_relevance(
                    content=doc.content,
                    title=doc.title,
                    company_profile=company_profile,
                    nc_codes=nc_codes,
                    #document_metadata=document_metadata
                )
                
                logger.info(
                    "document_analyzed",
                    document_id=doc.id,
                    is_relevant=analysis_result.is_relevant,
                    confidence=analysis_result.confidence,
                    matched_keywords_count=len(analysis_result.matched_keywords),
                    matched_nc_codes_count=len(analysis_result.matched_nc_codes)
                )
                
                # ================================================================
                # ÉTAPE 3 : CRÉER L'ANALYSIS EN BDD
                # ================================================================
                logger.info("creating_analysis", document_id=doc.id)
                
                # Créer manuellement l'Analysis
                analysis = Analysis(
                    document_id=doc.id,
                    is_relevant=analysis_result.is_relevant,
                    confidence=analysis_result.confidence,
                    matched_keywords=json.dumps(analysis_result.matched_keywords),
                    matched_nc_codes=json.dumps(analysis_result.matched_nc_codes),
                    llm_reasoning=f"Summary: {analysis_result.summary}\n\nReasoning: {analysis_result.reasoning}",
                    validation_status="pending"
                )

                
                session.add(analysis)
                session.flush()
                
                logger.info("analysis_created", analysis_id=analysis.id, document_id=doc.id)
                
                # ================================================================
                # ÉTAPE 4 : METTRE À JOUR LE DOCUMENT
                # ================================================================
                logger.info("updating_document_workflow", document_id=doc.id)
                
                doc.workflow_status = "analyzed"
                session.add(doc)
                
                analyses_created.append({
                    "document_id": doc.id,
                    "analysis_id": analysis.id,
                    "title": doc.title,
                    "is_relevant": analysis_result.is_relevant,
                    "confidence": analysis_result.confidence,
                    "matched_keywords": analysis_result.matched_keywords,
                    "matched_nc_codes": analysis_result.matched_nc_codes,
                    "summary": analysis_result.summary[:100] + "..." if len(analysis_result.summary) > 100 else analysis_result.summary
                })
                
                if analysis_result.is_relevant:
                    documents_relevant += 1
                else:
                    documents_irrelevant += 1
                
                logger.info("document_processed", document_id=doc.id)
                
            except Exception as e:
                logger.error(
                    "document_processing_error",
                    document_id=doc.id,
                    error=str(e),
                    exc_info=True
                )
                errors.append({
                    "document_id": doc.id,
                    "title": doc.title,
                    "error": str(e)
                })
                continue
        
        # ====================================================================
        # ÉTAPE 5 : SAUVEGARDER LES CHANGEMENTS
        # ====================================================================
        logger.info("step_5_saving_changes", analyses_count=len(analyses_created))
        
        session.commit()
        
        logger.info(
            "agent_1b_completed",
            documents_processed=len(analyses_created),
            documents_relevant=documents_relevant,
            documents_irrelevant=documents_irrelevant,
            errors_count=len(errors)
        )
        
        # ====================================================================
        # RÉSULTAT FINAL
        # ====================================================================
        return {
            "status": "success",
            "company_id": company_id,
            "company_name": company_profile.get("name"),
            "documents_processed": len(analyses_created),
            "documents_relevant": documents_relevant,
            "documents_irrelevant": documents_irrelevant,
            "analyses_created": analyses_created,
            "errors": errors if errors else None
        }
    
    except Exception as e:
        session.rollback()
        logger.error("agent_1b_error", error=str(e), exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }
    
    finally:
        session.close()


# ============================================================================
# POUR TESTER L'AGENT 1B DIRECTEMENT
# ============================================================================

async def test_agent_1b():
    """Test l'Agent 1B avec un profil réel"""
    
    print("=" * 80)
    print("🤖 TEST AGENT 1B - ANALYSE DE PERTINENCE")
    print("=" * 80)
    
    result = await run_agent_1b(
        company_id="GMG-001",
        max_documents=5
    )
    
    print(f"\n✅ Exécution terminée\n")
    print(f"📊 Résumé:")
    print(f"  - Entreprise: {result.get('company_name')}")
    print(f"  - Documents traités: {result.get('documents_processed', 0)}")
    print(f"  - Documents pertinents: {result.get('documents_relevant', 0)}")
    print(f"  - Documents non-pertinents: {result.get('documents_irrelevant', 0)}")
    
    if result.get('analyses_created'):
        print(f"\n📄 Analyses créées:\n")
        for analysis in result['analyses_created']:
            print(f"  • {analysis['title'][:60]}...")
            print(f"    Pertinent: {analysis['is_relevant']}")
            print(f"    Confiance: {analysis['confidence']:.2f}")
            print(f"    Résumé: {analysis['summary'][:80]}...")
            print()
    
    if result.get('errors'):
        print(f"\n⚠️ Erreurs ({len(result['errors'])}):\n")
        for error in result['errors']:
            print(f"  • {error['title'][:60]}: {error['error']}")
    
    print("\n" + "=" * 80)
    print("✅ Test terminé !")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_agent_1b())