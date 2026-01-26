"""
Agent 1A - Pipeline Combiné EUR-Lex + CBAM Guidance

Collecte les documents depuis deux sources :
1. EUR-Lex : Lois et règlements (CBAM, EUDR, CSRD)
2. CBAM Guidance : Documents officiels CBAM (Guidance, FAQs, Templates)
"""

import asyncio
import structlog
from typing import Dict, List
from datetime import datetime
import hashlib

from .tools.scraper import search_eurlex
from .tools.cbam_guidance_scraper import search_cbam_guidance
from .tools.document_fetcher import fetch_document
from .tools.pdf_extractor import extract_pdf_content

logger = structlog.get_logger()

# ========================================
# PIPELINE COMBINÉ
# ========================================

async def run_agent_1a_combined(
    keyword: str = "CBAM",
    max_eurlex_documents: int = 10,
    cbam_categories: str = "all",
    max_cbam_documents: int = 50
) -> Dict:
    """
    Pipeline combiné Agent 1A : EUR-Lex + CBAM Guidance
    
    Collecte et traite les documents depuis deux sources en parallèle :
    1. EUR-Lex : Lois et règlements
    2. CBAM Guidance : Documents officiels
    
    Args:
        keyword: Mot-clé pour EUR-Lex (CBAM, EUDR, CSRD)
        max_eurlex_documents: Nombre max de documents EUR-Lex
        cbam_categories: Catégories CBAM (all, guidance, faq, template, default_values, tool)
        max_cbam_documents: Nombre max de documents CBAM
        
    Returns:
        dict: Résultat avec statistiques et documents traités
    """
    logger.info(
        "agent_1a_combined_started",
        keyword=keyword,
        max_eurlex=max_eurlex_documents,
        cbam_categories=cbam_categories,
        max_cbam=max_cbam_documents
    )
    
    try:
        from src.storage.database import get_session
        from src.storage.repositories import DocumentRepository
        
        # ====================================================================
        # ÉTAPE 1 : SCRAPING PARALLÈLE (EUR-Lex + CBAM)
        # ====================================================================
        logger.info("step_1_parallel_scraping")
        
        # Lancer les deux scrapers en parallèle
        eurlex_task = search_eurlex(keyword, max_results=max_eurlex_documents)
        cbam_task = search_cbam_guidance(categories=cbam_categories, max_results=max_cbam_documents)
        
        eurlex_results, cbam_results = await asyncio.gather(eurlex_task, cbam_task)
        
        # Vérifier les résultats
        if eurlex_results.status != "success":
            logger.error("eurlex_search_failed", error=eurlex_results.error)
        
        if cbam_results.status != "success":
            logger.error("cbam_search_failed", error=cbam_results.error)
        
        total_found = len(eurlex_results.documents) + len(cbam_results.documents)
        
        logger.info(
            "step_1_completed",
            eurlex_count=len(eurlex_results.documents),
            cbam_count=len(cbam_results.documents),
            total=total_found
        )
        
        # ====================================================================
        # ÉTAPE 2 : VÉRIFIER LES DOCUMENTS EXISTANTS EN BDD
        # ====================================================================
        logger.info("step_2_checking_existing_documents")
        
        session = get_session()
        repo = DocumentRepository(session)
        
        documents_to_process = []
        documents_unchanged = []
        
        try:
            # Vérifier EUR-Lex documents
            for doc in eurlex_results.documents:
                # Utiliser pdf_url pour télécharger le PDF au lieu du HTML
                url = str(doc.pdf_url) if doc.pdf_url else str(doc.url)
                existing_doc = repo.find_by_url(url)
                
                if existing_doc:
                    if existing_doc.hash_sha256 == doc.metadata.get("remote_hash"):
                        documents_unchanged.append(doc)
                        logger.info("document_unchanged", celex=doc.celex_number)
                        continue
                
                documents_to_process.append({
                    'source': 'eurlex',
                    'doc': doc,
                    'url': url
                })
            
            # Vérifier CBAM documents
            for doc in cbam_results.documents:
                url = str(doc.url)
                existing_doc = repo.find_by_url(url)
                
                if existing_doc:
                    # Pour CBAM, on vérifie juste l'existence (pas de hash remote)
                    documents_unchanged.append(doc)
                    logger.info("document_unchanged", title=doc.title)
                    continue
                
                documents_to_process.append({
                    'source': 'cbam',
                    'doc': doc,
                    'url': url
                })
            
            logger.info(
                "step_2_completed",
                to_process=len(documents_to_process),
                unchanged=len(documents_unchanged)
            )
            
        finally:
            session.close()
        
        # ====================================================================
        # ÉTAPE 3 : TÉLÉCHARGEMENT DES DOCUMENTS
        # ====================================================================
        logger.info("step_3_downloading", count=len(documents_to_process))
        
        downloaded_files = []
        download_errors = []
        
        for item in documents_to_process:
            try:
                doc = item['doc']
                url = item['url']
                source = item['source']
                
                # Identifier le document
                if source == 'eurlex':
                    doc_id = doc.celex_number
                else:
                    doc_id = doc.title[:50]
                
                logger.info("downloading_document", source=source, id=doc_id)
                
                # Vérifier si le document existe déjà en BDD pour éviter téléchargement inutile
                session_check = get_session()
                repo_check = DocumentRepository(session_check)
                existing_doc_check = repo_check.find_by_url(url)
                session_check.close()
                
                # Utiliser skip_if_exists et existing_hash pour optimiser
                fetch_result = await fetch_document(
                    url, 
                    output_dir="data/documents",
                    skip_if_exists=True,
                    existing_hash=existing_doc_check.hash_sha256 if existing_doc_check else None
                )
                
                if not fetch_result.success:
                    raise Exception(fetch_result.error or "Download failed")
                
                # Si le document est inchangé, on skip le téléchargement
                if fetch_result.document.status == "skipped":
                    logger.info("document_skipped", source=source, id=doc_id, reason="unchanged")
                    continue
                
                file_path = fetch_result.document.file_path
                
                downloaded_files.append({
                    'source': source,
                    'doc': doc,
                    'file_path': file_path,
                    'url': url
                })
                
                logger.info("document_downloaded", source=source, id=doc_id, path=file_path)
                
            except Exception as e:
                logger.error("download_failed", source=source, id=doc_id, error=str(e))
                download_errors.append({
                    'source': source,
                    'doc': doc,
                    'error': str(e)
                })
        
        logger.info(
            "step_3_completed",
            downloaded=len(downloaded_files),
            errors=len(download_errors)
        )
        
        # ====================================================================
        # ÉTAPE 4 : EXTRACTION DU CONTENU (PDFs uniquement)
        # ====================================================================
        logger.info("step_4_extracting", count=len(downloaded_files))
        
        extracted_documents = []
        extraction_errors = []
        
        for item in downloaded_files:
            try:
                doc = item['doc']
                file_path = item['file_path']
                source = item['source']
                
                # Identifier le document
                if source == 'eurlex':
                    doc_id = doc.celex_number
                else:
                    doc_id = doc.title[:50]
                
                # Extraire seulement les PDFs
                if not file_path.endswith('.pdf'):
                    doc_format = doc.format if hasattr(doc, 'format') else 'UNKNOWN'
                    logger.info("skipping_non_pdf", source=source, id=doc_id, format=doc_format)
                    continue
                
                logger.info("extracting_content", source=source, id=doc_id)
                
                content = await extract_pdf_content(file_path)
                
                extracted_documents.append({
                    'source': source,
                    'doc': doc,
                    'file_path': file_path,
                    'content': content,
                    'url': item['url']
                })
                
                logger.info(
                    "content_extracted",
                    source=source,
                    id=doc_id,
                    pages=content.page_count,
                    nc_codes=len(content.nc_codes)
                )
                
            except Exception as e:
                logger.error("extraction_failed", source=source, id=doc_id, error=str(e))
                extraction_errors.append({
                    'source': source,
                    'doc': doc,
                    'error': str(e)
                })
        
        logger.info(
            "step_4_completed",
            extracted=len(extracted_documents),
            errors=len(extraction_errors)
        )
        
        # ====================================================================
        # ÉTAPE 5 : SAUVEGARDE EN BASE DE DONNÉES
        # ====================================================================
        logger.info("step_5_saving_to_database", count=len(extracted_documents))
        
        session = get_session()
        repo = DocumentRepository(session)
        
        saved_count = 0
        save_errors = []
        
        try:
            for item in extracted_documents:
                try:
                    doc = item['doc']
                    content = item['content']
                    file_path = item['file_path']
                    url = item['url']
                    source = item['source']
                    
                    # Calculer le hash du fichier
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    
                    # Préparer les métadonnées selon la source
                    # Note: content est un objet ExtractedContent (Pydantic), pas un dict
                    if source == 'eurlex':
                        metadata = {
                            'source': 'eurlex',
                            'celex_number': doc.celex_number,
                            'document_type': doc.document_type,
                            'pages': content.page_count,
                            'tables': len(content.tables),
                            'file_path': file_path
                        }
                        regulation_type = 'CBAM'  # EUR-Lex documents are CBAM-related
                        nc_codes = [nc.code for nc in content.nc_codes]  # Extraire les codes NC
                        pub_date = doc.publication_date  # EurlexDocument utilise publication_date, pas date
                    else:  # cbam
                        metadata = {
                            'source': 'cbam_guidance',
                            'format': doc.format,
                            'size': doc.size,
                            'category': doc.category,
                            'pages': content.page_count,
                            'file_path': file_path
                        }
                        regulation_type = 'CBAM'
                        nc_codes = [nc.code for nc in content.nc_codes]  # Extraire les codes NC
                        pub_date = getattr(doc, 'date', None)
                    
                    # Sauvegarder avec upsert_document
                    saved_doc, status = repo.upsert_document(
                        source_url=url,
                        hash_sha256=file_hash,
                        title=doc.title,
                        content=content.text,  # Attribut text, pas .get('text')
                        nc_codes=nc_codes,
                        regulation_type=regulation_type,
                        publication_date=pub_date,
                        document_metadata=metadata
                    )
                    saved_count += 1
                    
                    logger.info("document_saved", source=source, title=doc.title[:50], status=status, doc_id=saved_doc.id)
                    
                except Exception as e:
                    logger.error("save_failed", source=source, title=doc.title[:50], error=str(e))
                    save_errors.append({
                        'source': source,
                        'doc': doc,
                        'error': str(e)
                    })
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error("database_transaction_failed", error=str(e))
            raise
        finally:
            session.close()
        
        logger.info("step_5_completed", saved=saved_count, errors=len(save_errors))
        
        # ====================================================================
        # RÉSULTAT FINAL
        # ====================================================================
        
        result = {
            "status": "success",
            "keyword": keyword,
            "cbam_categories": cbam_categories,
            "sources": {
                "eurlex": {
                    "found": len(eurlex_results.documents),
                    "processed": len([x for x in extracted_documents if x['source'] == 'eurlex'])
                },
                "cbam_guidance": {
                    "found": len(cbam_results.documents),
                    "processed": len([x for x in extracted_documents if x['source'] == 'cbam'])
                }
            },
            "total_found": total_found,
            "documents_processed": saved_count,
            "documents_unchanged": len(documents_unchanged),
            "download_errors": len(download_errors),
            "extraction_errors": len(extraction_errors),
            "save_errors": len(save_errors)
        }
        
        logger.info("agent_1a_combined_completed", result=result)
        
        return result
        
    except Exception as e:
        logger.error("agent_1a_combined_failed", error=str(e))
        return {
            "status": "error",
            "keyword": keyword,
            "error": str(e)
        }
