"""
Agent 1A Pipeline - Orchestration manuelle sans ReAct

Version optimisée sans LangGraph ReAct pour éviter rate limits.
Workflow déterministe : search → fetch → extract → summarize

Avantages vs ReAct:
- Pas de réinjection de contexte massif
- Contrôle total du débit API
- LLM appelé uniquement pour résumés (1 appel/doc)
- 3-5x plus rapide
- Aucun risque de rate limit

Responsable: Dev 1
"""

import asyncio
import os
from pathlib import Path
from typing import List, Dict, Any
import structlog
from dotenv import load_dotenv

# Charger variables d'environnement
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Import des fonctions d'outils (versions async)
from .tools.scraper import search_eurlex
from .tools.document_fetcher import fetch_document
from .tools.pdf_extractor import PDFExtractor
from .tools.summarizer import generate_summary_tool

logger = structlog.get_logger()


class Agent1APipeline:
    """
    Pipeline manuel pour Agent 1A (sans ReAct).
    
    Workflow:
    1. search_eurlex(keyword) → documents list
    2. Pour chaque doc:
       - fetch_document(url) → file_path
       - extract_pdf(file_path) → text_preview + nc_codes
       - generate_summary(text_preview) → summary
    3. Return enriched documents
    """
    
    def __init__(self):
        """Initialiser les outils du pipeline."""
        self.extractor = PDFExtractor()
        logger.info("agent_1a_pipeline_initialized", mode="manual_orchestration")
    
    async def run(
        self,
        keyword: str = "CBAM",
        max_documents: int = 10
    ) -> Dict[str, Any]:
        """
        Exécute le pipeline complet.
        
        Args:
            keyword: Mot-clé EUR-Lex (CBAM, EUDR, CSRD, etc.)
            max_documents: Nombre maximum de documents à traiter
        
        Returns:
            dict: {"status": "success", "documents": [...], "stats": {...}}
        """
        logger.info("pipeline_started", keyword=keyword, max_documents=max_documents)
        
        try:
            # ÉTAPE 1 : Recherche EUR-Lex
            logger.info("step_1_search_eurlex", keyword=keyword)
            search_result = await search_eurlex(keyword=keyword, max_results=max_documents)
            
            if not hasattr(search_result, 'documents'):
                return {
                    "status": "error",
                    "error": "EUR-Lex search failed",
                    "documents": []
                }
            
            documents = search_result.documents
            logger.info("step_1_completed", documents_found=len(documents))
            
            if not documents:
                return {
                    "status": "success",
                    "documents": [],
                    "stats": {"keyword": keyword, "documents_found": 0}
                }
            
            # ÉTAPE 2-5 : Traiter chaque document
            enriched_docs = []
            
            for idx, doc in enumerate(documents, 1):
                doc_title = doc.title if hasattr(doc, 'title') else doc.get("title", "")
                logger.info("processing_document", index=idx, total=len(documents), title=doc_title[:50])
                
                try:
                    enriched_doc = await self._process_document(doc, idx)
                    enriched_docs.append(enriched_doc)
                except Exception as e:
                    logger.error("document_processing_error", index=idx, error=str(e), exc_info=True)
                    # Ajouter quand même le doc avec erreur
                    if hasattr(doc, 'model_dump'):
                        base_doc = doc.model_dump()
                    elif hasattr(doc, 'dict'):
                        base_doc = doc.dict()
                    else:
                        base_doc = {**doc}
                    enriched_docs.append({
                        **base_doc,
                        "status": "error",
                        "error": str(e)
                    })
            
            logger.info("pipeline_completed", 
                       total_documents=len(enriched_docs),
                       successful=len([d for d in enriched_docs if d.get("status") != "error"]))
            
            return {
                "status": "success",
                "keyword": keyword,
                "documents": enriched_docs,
                "stats": {
                    "total": len(enriched_docs),
                    "successful": len([d for d in enriched_docs if d.get("status") != "error"]),
                    "errors": len([d for d in enriched_docs if d.get("status") == "error"])
                }
            }
        
        except Exception as e:
            logger.error("pipeline_error", error=str(e), exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "documents": []
            }
    
    async def _process_document(self, doc: Dict[str, Any], index: int) -> Dict[str, Any]:
        """
        Traite un document : télécharge → extrait → résume.
        
        Args:
            doc: Document EUR-Lex de base (peut être dict ou EURLexDocument)
            index: Index du document (pour logs)
        
        Returns:
            dict: Document enrichi avec summary, file_path, nc_codes, etc.
        """
        # Convertir en dict si c'est un objet Pydantic
        if hasattr(doc, 'model_dump'):
            enriched = doc.model_dump()
        elif hasattr(doc, 'dict'):
            enriched = doc.dict()
        else:
            enriched = {**doc}  # Copier métadonnées de base
        
        # ÉTAPE 2 : Télécharger PDF
        pdf_url = enriched.get("pdf_url")
        if not pdf_url:
            doc_title = enriched.get("title", "")[:50]
            logger.warning("no_pdf_url", index=index, title=doc_title)
            enriched["status"] = "no_pdf"
            return enriched
        
        # Convertir pydantic HttpUrl en string si nécessaire
        pdf_url_str = str(pdf_url)
        
        logger.info("step_2_fetch_pdf", index=index)
        fetch_result = await fetch_document(pdf_url_str)
        
        if not fetch_result.success or not fetch_result.document:
            enriched["status"] = "fetch_failed"
            enriched["error"] = fetch_result.error
            return enriched
        
        file_path = fetch_result.document.file_path
        enriched["file_path"] = file_path
        enriched["file_size"] = fetch_result.document.file_size
        enriched["hash_sha256"] = fetch_result.document.hash_sha256
        
        # ÉTAPE 3 : Extraire contenu PDF
        logger.info("step_3_extract_pdf", index=index, file_path=file_path)
        extract_result = self.extractor.extract_from_file(file_path)
        
        if "error" in extract_result:
            enriched["status"] = "extraction_failed"
            enriched["error"] = extract_result["error"]
            return enriched
        
        # Sauvegarder texte complet sur disque
        text_path = str(Path(file_path).with_suffix(".txt"))
        Path(text_path).write_text(extract_result["text"], encoding="utf-8")
        
        enriched["text_path"] = text_path
        enriched["text_chars"] = len(extract_result["text"])
        enriched["nc_codes"] = extract_result.get("nc_codes", [])[:50]  # Limiter
        enriched["amounts"] = extract_result.get("amounts", [])[:20]
        enriched["pages"] = extract_result.get("metadata", {}).get("pages", 0)
        
        # ÉTAPE 4 : Générer résumé (seul appel LLM)
        logger.info("step_4_generate_summary", index=index)
        
        # Utiliser preview seulement (8k chars max)
        text_preview = extract_result["text"][:8000]
        if len(extract_result["text"]) > 8000:
            text_preview += "\n[...contenu tronqué...]"
        
        try:
            summary = await generate_summary_tool.ainvoke({
                "document_content": text_preview,
                "document_title": enriched.get("title", "Document")
            })
            enriched["summary"] = summary
            enriched["status"] = "completed"
        except Exception as e:
            logger.error("summary_generation_error", index=index, error=str(e), exc_info=True)
            enriched["summary"] = f"Error: {str(e)}"
            enriched["status"] = "summary_failed"
        
        return enriched


# ═══════════════════════════════════════════════════════════
# FONCTIONS PUBLIQUES (API similaire à agent.py)
# ═══════════════════════════════════════════════════════════

async def run_agent_1a_pipeline(
    keyword: str = "CBAM",
    max_documents: int = 10
) -> Dict[str, Any]:
    """
    Exécute l'Agent 1A en mode pipeline (sans ReAct).
    
    Args:
        keyword: Mot-clé de recherche EUR-Lex
        max_documents: Nombre maximum de documents à traiter
    
    Returns:
        dict: {"status": "success", "documents": [...], "stats": {...}}
    """
    pipeline = Agent1APipeline()
    return await pipeline.run(keyword=keyword, max_documents=max_documents)


async def run_agent_1a_simple_pipeline(
    keyword: str = "CBAM",
    max_documents: int = 5
) -> Dict[str, Any]:
    """
    Version simplifiée pour obtenir directement les documents enrichis.
    
    Args:
        keyword: Mot-clé de recherche EUR-Lex
        max_documents: Nombre maximum de documents
    
    Returns:
        dict: {"documents": [...]} ou {"error": "..."}
    """
    result = await run_agent_1a_pipeline(keyword, max_documents)
    
    if result["status"] == "success":
        return {"documents": result["documents"], "stats": result.get("stats")}
    else:
        return {"error": result.get("error"), "documents": []}


# Pour tester le pipeline directement
if __name__ == "__main__":
    async def test_pipeline():
        print("=" * 80)
        print("🚀 TEST AGENT 1A PIPELINE - Orchestration manuelle (sans ReAct)")
        print("=" * 80)
        
        # Test : Rechercher 3 documents CBAM
        result = await run_agent_1a_simple_pipeline(keyword="CBAM", max_documents=3)
        
        if "error" in result:
            print(f"\n❌ Erreur: {result['error']}")
        else:
            docs = result.get("documents", [])
            stats = result.get("stats", {})
            
            print(f"\n✅ Pipeline terminé!")
            print(f"📊 Stats: {stats.get('total')} documents, {stats.get('successful')} succès, {stats.get('errors')} erreurs\n")
            
            # Afficher les documents
            for i, doc in enumerate(docs, 1):
                print(f"\n{'='*60}")
                print(f"[{i}] {doc.get('title', 'Sans titre')}")
                print(f"CELEX: {doc.get('celex_number', 'N/A')}")
                print(f"Type: {doc.get('document_type', 'N/A')}")
                print(f"Status: {doc.get('status', 'N/A')}")
                
                # Date
                pub_date = doc.get('publication_date', 'N/A')
                if pub_date != 'N/A' and 'T' in str(pub_date):
                    pub_date = pub_date.split('T')[0]
                print(f"Date: {pub_date}")
                
                # Fichiers
                if doc.get("file_path"):
                    print(f"PDF: {doc['file_path']}")
                if doc.get("text_path"):
                    print(f"Text: {doc['text_path']}")
                
                # NC codes
                nc_codes = doc.get("nc_codes", [])
                if nc_codes:
                    print(f"NC Codes: {', '.join(nc_codes[:10])}")
                
                # Résumé
                print(f"\nRésumé:")
                print(f"{doc.get('summary', 'Pas de résumé')}")
        
        print("\n" + "=" * 80)
        print("✅ Test terminé !")
        print("=" * 80)
    
    asyncio.run(test_pipeline())
