"""
Agent 1A - Pipeline EUR-Lex

Collecte les documents réglementaires depuis EUR-Lex :
- Approche par DOMAINES (Option 3 - CDC) : collecte générique sans filtrage métier
- Approche par MOT-CLÉ (legacy) : recherche ciblée par réglementation

L'Agent 1A collecte et stocke. L'Agent 1B filtre la pertinence.
"""

import asyncio
import structlog
from typing import Dict, List, Optional
from datetime import datetime
import hashlib

from .tools.scraper import search_eurlex, search_eurlex_by_domain, load_eurlex_domains_config
from .tools.document_fetcher import fetch_document
from .tools.pdf_extractor import extract_pdf_content

logger = structlog.get_logger()


# ========================================
# NOUVEAU PIPELINE : COLLECTE PAR DOMAINES (Option 3 - CDC)
# ========================================

async def run_agent_1a_by_domain(
    domains: List[str] = None,
    document_types: List[str] = None,
    max_age_days: int = 365,
    max_documents: int = 50
) -> Dict:
    """
    Pipeline Agent 1A : Collecte par DOMAINES (conforme CDC)
    
    Collecte TOUS les documents réglementaires correspondant aux critères,
    sans filtrage par mot-clé de réglementation spécifique.
    
    C'est l'Agent 1B qui déterminera ensuite si chaque document est
    pertinent pour Hutchinson.
    
    Args:
        domains: Liste des codes de domaines EUR-Lex (ex: ["15", "13", "11"])
                 Si None, utilise les domaines activés dans config/eurlex_domains.json
        document_types: Types de documents (ex: ["R", "L", "D"] pour Règlements, Directives, Décisions)
                       Si None, utilise les types activés dans la config
        max_age_days: Âge maximum des documents en jours (défaut: 365 = 1 an)
        max_documents: Nombre max de documents à récupérer (défaut: 50)
        
    Returns:
        dict: Résultat avec statistiques et documents traités
    """
    logger.info(
        "agent_1a_domain_started",
        domains=domains,
        document_types=document_types,
        max_age_days=max_age_days,
        max_documents=max_documents
    )
    
    try:
        from src.storage.database import get_session
        from src.storage.repositories import DocumentRepository
        
        # ====================================================================
        # ÉTAPE 1 : RECHERCHE EUR-LEX PAR DOMAINES
        # ====================================================================
        logger.info("step_1_domain_search")
        
        eurlex_results = await search_eurlex_by_domain(
            domains=domains,
            document_types=document_types,
            max_age_days=max_age_days,
            max_results=max_documents
        )
        
        if eurlex_results.status != "success":
            logger.error("domain_search_failed", error=eurlex_results.error)
            return {
                "status": "error",
                "mode": "domain",
                "error": eurlex_results.error
            }
        
        total_found = len(eurlex_results.documents)
        total_available = eurlex_results.total_available
        
        logger.info(
            "step_1_completed",
            documents_found=total_found,
            total_available_on_eurlex=total_available
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
            for doc in eurlex_results.documents:
                url = str(doc.pdf_url) if doc.pdf_url else str(doc.url)
                existing_doc = repo.find_by_url(url)
                
                if existing_doc:
                    documents_unchanged.append(doc)
                    logger.debug("document_unchanged", celex=doc.celex_number)
                    continue
                
                documents_to_process.append({
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
                doc_id = doc.celex_number or doc.title[:50]
                
                logger.info("downloading_document", id=doc_id)
                
                fetch_result = await fetch_document(
                    url, 
                    output_dir="data/documents",
                    skip_if_exists=False
                )
                
                if not fetch_result.success:
                    raise Exception(fetch_result.error or "Download failed")
                
                file_path = fetch_result.document.file_path
                
                downloaded_files.append({
                    'doc': doc,
                    'file_path': file_path,
                    'url': url
                })
                
                logger.info("document_downloaded", id=doc_id, path=file_path)
                
            except Exception as e:
                logger.error("download_failed", id=doc_id, error=str(e))
                download_errors.append({
                    'doc': doc,
                    'error': str(e)
                })
        
        logger.info(
            "step_3_completed",
            downloaded=len(downloaded_files),
            errors=len(download_errors)
        )
        
        # ====================================================================
        # ÉTAPE 4 : EXTRACTION DU CONTENU PDF
        # ====================================================================
        logger.info("step_4_extracting", count=len(downloaded_files))
        
        extracted_documents = []
        extraction_errors = []
        
        for item in downloaded_files:
            try:
                doc = item['doc']
                file_path = item['file_path']
                doc_id = doc.celex_number or doc.title[:50]
                
                if not file_path.endswith('.pdf'):
                    logger.info("skipping_non_pdf", id=doc_id)
                    continue
                
                logger.info("extracting_content", id=doc_id)
                
                content = await extract_pdf_content(file_path)
                
                extracted_documents.append({
                    'doc': doc,
                    'file_path': file_path,
                    'content': content,
                    'url': item['url']
                })
                
                logger.info(
                    "content_extracted",
                    id=doc_id,
                    pages=content.page_count,
                    nc_codes=len(content.nc_codes)
                )
                
            except Exception as e:
                logger.error("extraction_failed", id=doc_id, error=str(e))
                extraction_errors.append({
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
                    
                    # Calculer le hash du fichier
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    
                    # Préparer les métadonnées
                    metadata = {
                        'source': 'eurlex',
                        'collection_mode': 'domain',  # Nouveau : indique le mode de collecte
                        'celex_number': doc.celex_number,
                        'document_type': doc.document_type,
                        'pages': content.page_count,
                        'tables': len(content.tables),
                        'file_path': file_path,
                        'nc_codes': [nc.code for nc in content.nc_codes]
                    }
                    
                    # Ajouter les infos du document extrait si disponibles
                    publication_date = None
                    if content.document_info:
                        doc_info = content.document_info
                        metadata['document_number'] = doc_info.document_number
                        metadata['document_subtype'] = doc_info.document_subtype
                        metadata['issuing_body'] = doc_info.issuing_body
                        metadata['publication_series'] = doc_info.publication_series
                        publication_date = doc_info.publication_date
                    
                    if publication_date is None:
                        publication_date = doc.publication_date
                    
                    # Sauvegarder avec regulation_type = "TO_CLASSIFY" (sera classé par Agent 1B)
                    saved_doc, status = repo.upsert_document(
                        source_url=url,
                        hash_sha256=file_hash,
                        title=doc.title,
                        content=content.text,
                        nc_codes=[nc.code for nc in content.nc_codes],
                        regulation_type="TO_CLASSIFY",  # L'Agent 1B classifiera
                        publication_date=publication_date,
                        document_metadata=metadata
                    )
                    saved_count += 1
                    
                    logger.info("document_saved", title=doc.title[:50], status=status, doc_id=saved_doc.id)
                    
                except Exception as e:
                    logger.error("save_failed", title=doc.title[:50], error=str(e))
                    save_errors.append({
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
            "mode": "domain",
            "domains_searched": domains or "config_default",
            "document_types": document_types or "config_default",
            "max_age_days": max_age_days,
            "total_available_on_eurlex": total_available,
            "documents_found": total_found,
            "documents_processed": saved_count,
            "documents_unchanged": len(documents_unchanged),
            "download_errors": len(download_errors),
            "extraction_errors": len(extraction_errors),
            "save_errors": len(save_errors)
        }
        
        logger.info("agent_1a_domain_completed", result=result)
        
        return result
        
    except Exception as e:
        logger.error("agent_1a_domain_failed", error=str(e))
        return {
            "status": "error",
            "mode": "domain",
            "error": str(e)
        }


# ========================================
# PIPELINE LEGACY : PAR MOT-CLÉ (conservé pour compatibilité)
# ========================================

async def run_agent_1a(
    keyword: str = "CBAM",
    max_documents: int = 10,
    subdomains: List[str] = None,
    consolidated_only: bool = False
) -> Dict:
    """
    Pipeline Agent 1A : EUR-Lex par mot-clé (LEGACY)
    
    ⚠️ Cette fonction est conservée pour compatibilité.
    Préférez run_agent_1a_by_domain() pour une collecte conforme au CDC.
    
    Collecte et traite les documents réglementaires depuis EUR-Lex.
    
    Args:
        keyword: Mot-clé de recherche (CBAM, EUDR, CSRD, etc.)
        max_documents: Nombre max de documents à récupérer
        subdomains: Liste des sous-domaines EUR-Lex (LEGISLATION, CONSLEG, PREP_ACT)
        consolidated_only: Si True, récupère uniquement les textes consolidés
                          (texte original + toutes modifications fusionnées)
        
    Returns:
        dict: Résultat avec statistiques et documents traités
    """
    if subdomains is None:
        subdomains = ["LEGISLATION", "CONSLEG", "PREP_ACT"]
    
    logger.info(
        "agent_1a_started",

        keyword=keyword,
        max_documents=max_documents,
        subdomains=subdomains,
        consolidated_only=consolidated_only
    )
    
    try:
        from src.storage.database import get_session
        from src.storage.repositories import DocumentRepository
        
        # ====================================================================
        # ÉTAPE 1 : RECHERCHE EUR-LEX
        # ====================================================================
        logger.info("step_1_eurlex_search", consolidated_only=consolidated_only)
        
        eurlex_results = await search_eurlex(
            keyword, 
            max_results=max_documents,
            subdomains=subdomains,
            consolidated_only=consolidated_only
        )
        
        if eurlex_results.status != "success":
            logger.error("eurlex_search_failed", error=eurlex_results.error)
            return {
                "status": "error",
                "keyword": keyword,
                "error": eurlex_results.error
            }
        
        total_found = len(eurlex_results.documents)
        total_available = eurlex_results.total_available
        
        logger.info(
            "step_1_completed",
            eurlex_count=total_found,
            total_available_on_eurlex=total_available
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
            for doc in eurlex_results.documents:
                url = str(doc.pdf_url) if doc.pdf_url else str(doc.url)
                existing_doc = repo.find_by_url(url)
                
                if existing_doc:
                    documents_unchanged.append(doc)
                    logger.info("document_unchanged", celex=doc.celex_number, title=doc.title[:50])
                    continue
                
                documents_to_process.append({
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
                doc_id = doc.celex_number or doc.title[:50]
                
                logger.info("downloading_document", id=doc_id)
                
                fetch_result = await fetch_document(
                    url, 
                    output_dir="data/documents",
                    skip_if_exists=False
                )
                
                if not fetch_result.success:
                    raise Exception(fetch_result.error or "Download failed")
                
                file_path = fetch_result.document.file_path
                
                downloaded_files.append({
                    'doc': doc,
                    'file_path': file_path,
                    'url': url
                })
                
                logger.info("document_downloaded", id=doc_id, path=file_path)
                
            except Exception as e:
                logger.error("download_failed", id=doc_id, error=str(e))
                download_errors.append({
                    'doc': doc,
                    'error': str(e)
                })
        
        logger.info(
            "step_3_completed",
            downloaded=len(downloaded_files),
            errors=len(download_errors)
        )
        
        # ====================================================================
        # ÉTAPE 4 : EXTRACTION DU CONTENU PDF
        # ====================================================================
        logger.info("step_4_extracting", count=len(downloaded_files))
        
        extracted_documents = []
        extraction_errors = []
        
        for item in downloaded_files:
            try:
                doc = item['doc']
                file_path = item['file_path']
                doc_id = doc.celex_number or doc.title[:50]
                
                if not file_path.endswith('.pdf'):
                    logger.info("skipping_non_pdf", id=doc_id)
                    continue
                
                logger.info("extracting_content", id=doc_id)
                
                content = await extract_pdf_content(file_path)
                
                extracted_documents.append({
                    'doc': doc,
                    'file_path': file_path,
                    'content': content,
                    'url': item['url']
                })
                
                logger.info(
                    "content_extracted",
                    id=doc_id,
                    pages=content.page_count,
                    nc_codes=len(content.nc_codes)
                )
                
            except Exception as e:
                logger.error("extraction_failed", id=doc_id, error=str(e))
                extraction_errors.append({
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
                    
                    # Calculer le hash du fichier
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    
                    # Préparer les métadonnées
                    metadata = {
                        'source': 'eurlex',
                        'celex_number': doc.celex_number,
                        'document_type': doc.document_type,
                        'pages': content.page_count,
                        'tables': len(content.tables),
                        'file_path': file_path,
                        'nc_codes': [nc.code for nc in content.nc_codes]
                    }
                    
                    # Ajouter les infos du document extrait si disponibles
                    publication_date = None
                    if content.document_info:
                        doc_info = content.document_info
                        metadata['document_number'] = doc_info.document_number
                        metadata['document_subtype'] = doc_info.document_subtype
                        metadata['issuing_body'] = doc_info.issuing_body
                        metadata['publication_series'] = doc_info.publication_series
                        # Utiliser la date extraite du PDF
                        publication_date = doc_info.publication_date
                    
                    # Fallback sur la date du document EUR-Lex si pas trouvée dans le PDF
                    if publication_date is None:
                        publication_date = doc.publication_date
                    
                    # Sauvegarder
                    saved_doc, status = repo.upsert_document(
                        source_url=url,
                        hash_sha256=file_hash,
                        title=doc.title,
                        content=content.text,
                        nc_codes=[nc.code for nc in content.nc_codes],
                        regulation_type=keyword,
                        publication_date=publication_date,
                        document_metadata=metadata
                    )
                    saved_count += 1
                    
                    logger.info("document_saved", title=doc.title[:50], status=status, doc_id=saved_doc.id)
                    
                except Exception as e:
                    logger.error("save_failed", title=doc.title[:50], error=str(e))
                    save_errors.append({
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
            "subdomains": subdomains,
            "total_available_on_eurlex": total_available,  # Nombre total sur EUR-Lex
            "documents_found": total_found,  # Nombre récupéré (limité par max_documents)
            "documents_processed": saved_count,
            "documents_unchanged": len(documents_unchanged),
            "download_errors": len(download_errors),
            "extraction_errors": len(extraction_errors),
            "save_errors": len(save_errors)
        }
        
        logger.info("agent_1a_completed", result=result)
        
        return result
        
    except Exception as e:
        logger.error("agent_1a_failed", error=str(e))
        return {
            "status": "error",
            "keyword": keyword,
            "error": str(e)
        }


# ========================================
# PIPELINE COMBINÉ (LEGACY)
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


# ========================================
# PIPELINE MULTI-SECTEURS (NOUVEAU)
# ========================================

async def run_agent_1a_multi_sectors(
    sectors: List[str],
    max_documents_per_sector: int = 10,
    consolidated_only: bool = True
) -> Dict:
    """
    Pipeline Agent 1A : Recherche multi-secteurs
    
    Recherche des réglementations pour plusieurs secteurs/activités en parallèle,
    dédoublonne les résultats, et détecte automatiquement le type de réglementation.
    
    Args:
        sectors: Liste des secteurs/activités à rechercher 
                 Ex: ["rubber", "automotive", "aerospace", "polymer"]
        max_documents_per_sector: Nombre max de documents par secteur
        consolidated_only: Si True, récupère uniquement les textes consolidés (recommandé)
        
    Returns:
        dict: Résultat avec statistiques et documents traités
    """
    from .tools.scraper import detect_regulation
    
    logger.info(
        "agent_1a_multi_sectors_started",
        sectors=sectors,
        max_documents_per_sector=max_documents_per_sector,
        consolidated_only=consolidated_only
    )
    
    try:
        from src.storage.database import get_session
        from src.storage.repositories import DocumentRepository
        
        # ====================================================================
        # ÉTAPE 1 : RECHERCHE EUR-LEX POUR CHAQUE SECTEUR
        # ====================================================================
        logger.info("step_1_multi_sector_search", sectors=sectors)
        
        all_documents = []  # Liste de tous les documents trouvés
        seen_urls = set()   # Pour dédoublonner par URL
        seen_celex = set()  # Pour dédoublonner par CELEX
        sector_stats = {}   # Stats par secteur
        
        for sector in sectors:
            logger.info("searching_sector", sector=sector)
            
            eurlex_results = await search_eurlex(
                sector, 
                max_results=max_documents_per_sector,
                consolidated_only=consolidated_only
            )
            
            sector_found = 0
            sector_deduplicated = 0
            
            if eurlex_results.status == "success":
                for doc in eurlex_results.documents:
                    url = str(doc.pdf_url) if doc.pdf_url else str(doc.url)
                    celex = doc.celex_number
                    
                    # Dédoublonnage : skip si déjà vu
                    if url in seen_urls or (celex and celex in seen_celex):
                        sector_deduplicated += 1
                        logger.debug("document_deduplicated", celex=celex, sector=sector)
                        continue
                    
                    # Marquer comme vu
                    seen_urls.add(url)
                    if celex:
                        seen_celex.add(celex)
                    
                    # Ajouter avec le secteur source
                    all_documents.append({
                        'doc': doc,
                        'url': url,
                        'sector': sector
                    })
                    sector_found += 1
            
            sector_stats[sector] = {
                'found': len(eurlex_results.documents) if eurlex_results.status == "success" else 0,
                'unique': sector_found,
                'deduplicated': sector_deduplicated,
                'total_available': eurlex_results.total_available if eurlex_results.status == "success" else 0
            }
            
            logger.info(
                "sector_search_completed",
                sector=sector,
                found=sector_stats[sector]['found'],
                unique=sector_found,
                deduplicated=sector_deduplicated
            )
        
        total_unique = len(all_documents)
        
        logger.info(
            "step_1_completed",
            total_unique_documents=total_unique,
            sector_stats=sector_stats
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
            for item in all_documents:
                doc = item['doc']
                url = item['url']
                existing_doc = repo.find_by_url(url)
                
                if existing_doc:
                    documents_unchanged.append(item)
                    logger.debug("document_unchanged", celex=doc.celex_number)
                    continue
                
                documents_to_process.append(item)
            
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
                doc_id = doc.celex_number or doc.title[:50]
                
                logger.info("downloading_document", id=doc_id)
                
                fetch_result = await fetch_document(
                    url, 
                    output_dir="data/documents",
                    skip_if_exists=False
                )
                
                if not fetch_result.success:
                    raise Exception(fetch_result.error or "Download failed")
                
                file_path = fetch_result.document.file_path
                
                downloaded_files.append({
                    'doc': doc,
                    'file_path': file_path,
                    'url': url,
                    'sector': item['sector']
                })
                
                logger.info("document_downloaded", id=doc_id, path=file_path)
                
            except Exception as e:
                logger.error("download_failed", id=doc_id, error=str(e))
                download_errors.append({
                    'doc': doc,
                    'error': str(e)
                })
        
        logger.info(
            "step_3_completed",
            downloaded=len(downloaded_files),
            errors=len(download_errors)
        )
        
        # ====================================================================
        # ÉTAPE 4 : EXTRACTION DU CONTENU PDF
        # ====================================================================
        logger.info("step_4_extracting", count=len(downloaded_files))
        
        extracted_documents = []
        extraction_errors = []
        
        for item in downloaded_files:
            try:
                doc = item['doc']
                file_path = item['file_path']
                doc_id = doc.celex_number or doc.title[:50]
                
                if not file_path.endswith('.pdf'):
                    logger.info("skipping_non_pdf", id=doc_id)
                    continue
                
                logger.info("extracting_content", id=doc_id)
                
                content = await extract_pdf_content(file_path)
                
                extracted_documents.append({
                    'doc': doc,
                    'file_path': file_path,
                    'content': content,
                    'url': item['url'],
                    'sector': item['sector']
                })
                
                logger.info(
                    "content_extracted",
                    id=doc_id,
                    pages=content.page_count,
                    nc_codes=len(content.nc_codes)
                )
                
            except Exception as e:
                logger.error("extraction_failed", id=doc_id, error=str(e))
                extraction_errors.append({
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
        regulation_stats = {}  # Stats par réglementation détectée
        
        try:
            for item in extracted_documents:
                try:
                    doc = item['doc']
                    content = item['content']
                    file_path = item['file_path']
                    url = item['url']
                    sector = item['sector']
                    
                    # Calculer le hash du fichier
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    
                    # Détecter la réglementation depuis le titre
                    regulation_type = detect_regulation(doc.title, content.text)
                    
                    # Stats par réglementation
                    if regulation_type not in regulation_stats:
                        regulation_stats[regulation_type] = 0
                    regulation_stats[regulation_type] += 1
                    
                    # Préparer les métadonnées
                    metadata = {
                        'source': 'eurlex',
                        'celex_number': doc.celex_number,
                        'document_type': doc.document_type,
                        'pages': content.page_count,
                        'tables': len(content.tables),
                        'file_path': file_path,
                        'nc_codes': [nc.code for nc in content.nc_codes],
                        'search_sector': sector  # Secteur qui a trouvé ce document
                    }
                    
                    # Ajouter les infos du document extrait si disponibles
                    publication_date = None
                    if content.document_info:
                        doc_info = content.document_info
                        metadata['document_number'] = doc_info.document_number
                        metadata['document_subtype'] = doc_info.document_subtype
                        metadata['issuing_body'] = doc_info.issuing_body
                        metadata['publication_series'] = doc_info.publication_series
                        publication_date = doc_info.publication_date
                    
                    # Fallback sur la date du document EUR-Lex
                    if publication_date is None:
                        publication_date = doc.publication_date
                    
                    # Sauvegarder avec la réglementation détectée
                    saved_doc, status = repo.upsert_document(
                        source_url=url,
                        hash_sha256=file_hash,
                        title=doc.title,
                        content=content.text,
                        nc_codes=[nc.code for nc in content.nc_codes],
                        regulation_type=regulation_type,  # CBAM, EUDR, CSRD, etc.
                        publication_date=publication_date,
                        document_metadata=metadata
                    )
                    saved_count += 1
                    
                    logger.info(
                        "document_saved",
                        title=doc.title[:50],
                        status=status,
                        doc_id=saved_doc.id,
                        regulation=regulation_type,
                        sector=sector
                    )
                    
                except Exception as e:
                    logger.error("save_failed", title=doc.title[:50], error=str(e))
                    save_errors.append({
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
            "sectors": sectors,
            "consolidated_only": consolidated_only,
            "sector_stats": sector_stats,
            "regulation_stats": regulation_stats,
            "total_unique_documents": total_unique,
            "documents_processed": saved_count,
            "documents_unchanged": len(documents_unchanged),
            "download_errors": len(download_errors),
            "extraction_errors": len(extraction_errors),
            "save_errors": len(save_errors)
        }
        
        logger.info("agent_1a_multi_sectors_completed", result=result)
        
        return result
        
    except Exception as e:
        logger.error("agent_1a_multi_sectors_failed", error=str(e))
        return {
            "status": "error",
            "sectors": sectors,
            "error": str(e)
        }


# ========================================
# NOUVEAU PIPELINE : COLLECTE DEPUIS PROFIL ENTREPRISE (CDC CONFORME)
# ========================================

async def run_agent_1a_from_profile(
    profile_path: str = None,
    max_documents_per_keyword: int = 20,
    max_total_documents: int = 100,
    priority_threshold: int = 2,
    min_publication_year: int = 2000,
    save_to_db: bool = True
) -> Dict:
    """
    Pipeline Agent 1A conforme au CDC : Collecte depuis le profil entreprise.
    
    Cette fonction :
    1. Lit le profil JSON de l'entreprise (ex: Hutchinson_SA.json)
    2. Extrait automatiquement les mots-clés pertinents :
       - Codes NC/HS (nomenclature douanière)
       - Matières premières
       - Secteurs d'activité
       - Pays fournisseurs
    3. Recherche sur EUR-Lex avec ces mots-clés
    4. Collecte les documents SANS filtrage par nom de réglementation
    
    L'Agent 1B déterminera ensuite quelles réglementations (CBAM, REACH, etc.)
    sont pertinentes pour chaque document.
    
    Args:
        profile_path: Chemin vers le fichier JSON du profil entreprise.
                     Si None, utilise data/company_profiles/Hutchinson_SA.json
        max_documents_per_keyword: Max documents à récupérer par mot-clé (défaut: 20)
        max_total_documents: Max total de documents uniques (défaut: 100)
        priority_threshold: Inclure mots-clés de priorité <= N (défaut: 2 = codes NC + matières)
                           1 = codes NC uniquement
                           2 = codes NC + matières + produits
                           3 = + secteurs + pays
        min_publication_year: Année minimale de publication (défaut: 2000)
                             Les documents publiés avant cette date sont ignorés
        save_to_db: Sauvegarder en base de données (défaut: True)
        
    Returns:
        dict: Résultat avec statistiques et documents traités
    """
    from .tools.keyword_extractor import (
        extract_keywords_from_profile,
        get_eurlex_search_keywords,
        get_default_profile_path
    )
    from .tools.scraper import search_eurlex
    
    logger.info(
        "agent_1a_from_profile_started",
        profile_path=profile_path,
        max_per_keyword=max_documents_per_keyword,
        max_total=max_total_documents,
        priority=priority_threshold,
        min_publication_year=min_publication_year
    )
    
    # ====================================================================
    # ÉTAPE 1 : EXTRACTION DES MOTS-CLÉS DU PROFIL
    # ====================================================================
    logger.info("step_1_extracting_keywords")
    
    if profile_path is None:
        profile_path = get_default_profile_path()
    
    company_keywords = extract_keywords_from_profile(profile_path)
    
    if not company_keywords:
        logger.error("profile_extraction_failed", path=profile_path)
        return {
            "status": "error",
            "mode": "company_profile",
            "error": f"Failed to extract keywords from profile: {profile_path}"
        }
    
    # Obtenir les mots-clés prioritaires
    search_keywords = get_eurlex_search_keywords(
        company_keywords,
        max_keywords=30,
        priority_threshold=priority_threshold
    )
    
    logger.info(
        "step_1_completed",
        company=company_keywords.company_name,
        total_keywords_available=len(company_keywords.get_all_keywords()),
        keywords_selected=len(search_keywords),
        keywords=search_keywords[:10]  # Log les 10 premiers
    )
    
    # ====================================================================
    # ÉTAPE 2 : RECHERCHE EUR-LEX PAR MOT-CLÉ
    # ====================================================================
    logger.info("step_2_eurlex_search", keywords_count=len(search_keywords))
    
    all_documents = {}  # Clé = CELEX, pour dédoublonner
    keyword_stats = {}
    
    for keyword in search_keywords:
        try:
            logger.info("searching_keyword", keyword=keyword)
            
            # Recherche EUR-Lex
            result = await search_eurlex(
                keyword=keyword,
                max_results=max_documents_per_keyword,
                consolidated_only=False
            )
            
            if result.status == "success":
                docs_found = len(result.documents)
                keyword_stats[keyword] = {
                    "found": docs_found,
                    "total_available": result.total_available
                }
                
                # Ajouter les documents (dédoublonnés par CELEX, en privilégiant les versions consolidées)
                for doc in result.documents:
                    celex = doc.celex_number or doc.title
                    
                    # Extraire le numéro de base (sans préfixe 0 ou 3)
                    # Ex: "02017R0649" et "32017R0649" -> "2017R0649"
                    base_celex = celex[1:] if celex and len(celex) > 1 and celex[0] in '03' else celex
                    
                    # Vérifier si c'est une version consolidée (préfixe 0)
                    is_consolidated = celex.startswith('0') if celex else False
                    
                    if base_celex not in all_documents:
                        # Nouveau document
                        all_documents[base_celex] = {
                            "doc": doc,
                            "keywords": [keyword],
                            "is_consolidated": is_consolidated,
                            "original_celex": celex
                        }
                    else:
                        # Document déjà vu - ajouter le keyword
                        all_documents[base_celex]["keywords"].append(keyword)
                        
                        # Si la nouvelle version est consolidée et l'ancienne ne l'est pas, remplacer
                        if is_consolidated and not all_documents[base_celex].get("is_consolidated", False):
                            logger.info(
                                "replacing_with_consolidated",
                                old_celex=all_documents[base_celex].get("original_celex"),
                                new_celex=celex
                            )
                            all_documents[base_celex]["doc"] = doc
                            all_documents[base_celex]["is_consolidated"] = True
                            all_documents[base_celex]["original_celex"] = celex
                
                logger.info(
                    "keyword_completed",
                    keyword=keyword,
                    found=docs_found,
                    total_unique_so_far=len(all_documents)
                )
            else:
                keyword_stats[keyword] = {"error": result.error}
                logger.warning("keyword_failed", keyword=keyword, error=result.error)
            
            # Arrêter si on a assez de documents
            if len(all_documents) >= max_total_documents:
                logger.info("max_documents_reached", count=len(all_documents))
                break
                
        except Exception as e:
            logger.error("keyword_search_error", keyword=keyword, error=str(e))
            keyword_stats[keyword] = {"error": str(e)}
    
    logger.info(
        "step_2_completed",
        keywords_processed=len(keyword_stats),
        unique_documents=len(all_documents)
    )
    
    # ====================================================================
    # ÉTAPE 2b : FILTRAGE PAR DATE DE PUBLICATION
    # ====================================================================
    # Ne garder que les documents publiés à partir de min_publication_year (paramètre)
    
    filtered_documents = {}
    filtered_out_count = 0
    
    for base_celex, data in all_documents.items():
        doc = data["doc"]
        
        # Vérifier la date de publication
        if doc.publication_date:
            try:
                pub_year = doc.publication_date.year if hasattr(doc.publication_date, 'year') else int(str(doc.publication_date)[:4])
                if pub_year < min_publication_year:
                    logger.debug(
                        "document_filtered_by_date",
                        celex=data.get("original_celex", base_celex),
                        publication_year=pub_year,
                        min_year=min_publication_year
                    )
                    filtered_out_count += 1
                    continue
            except (ValueError, TypeError):
                pass  # Si on ne peut pas parser la date, on garde le document
        
        filtered_documents[base_celex] = data
    
    logger.info(
        "step_2b_date_filtering_completed",
        before=len(all_documents),
        after=len(filtered_documents),
        filtered_out=filtered_out_count,
        min_year=min_publication_year
    )
    
    all_documents = filtered_documents
    
    # ====================================================================
    # ÉTAPE 3 : TÉLÉCHARGEMENT DES DOCUMENTS
    # ====================================================================
    logger.info("step_3_downloading", count=len(all_documents))
    
    downloaded_files = []
    download_errors = []
    
    for celex, data in list(all_documents.items())[:max_total_documents]:
        doc = data["doc"]
        keywords_matched = data["keywords"]
        doc_id = celex[:30]
        
        try:
            # Obtenir l'URL PDF
            pdf_url = doc.pdf_url or (doc.html_url.replace('/HTML/', '/PDF/') if doc.html_url else None)
            
            if not pdf_url:
                logger.warning("no_pdf_url", id=doc_id)
                continue
            
            logger.info("downloading", id=doc_id)
            
            fetch_result = await fetch_document(pdf_url)
            
            # Extraire le chemin du fichier depuis le résultat
            if fetch_result and fetch_result.success and fetch_result.document:
                file_path = fetch_result.document.file_path
                downloaded_files.append({
                    "doc": doc,
                    "file_path": file_path,
                    "url": pdf_url,
                    "keywords_matched": keywords_matched
                })
                logger.info("downloaded", id=doc_id, path=file_path)
            else:
                error_msg = fetch_result.error if fetch_result else "fetch_failed"
                download_errors.append({"doc": doc, "error": error_msg})
                
        except Exception as e:
            logger.error("download_error", id=doc_id, error=str(e))
            download_errors.append({"doc": doc, "error": str(e)})
    
    logger.info(
        "step_3_completed",
        downloaded=len(downloaded_files),
        errors=len(download_errors)
    )
    
    # ====================================================================
    # ÉTAPE 4 : EXTRACTION DU CONTENU PDF
    # ====================================================================
    logger.info("step_4_extracting", count=len(downloaded_files))
    
    extracted_documents = []
    extraction_errors = []
    
    for item in downloaded_files:
        doc = item["doc"]
        file_path = item["file_path"]
        doc_id = doc.celex_number or doc.title[:30]
        
        try:
            if not file_path.endswith('.pdf'):
                logger.info("skipping_non_pdf", id=doc_id)
                continue
            
            content = await extract_pdf_content(file_path)
            
            extracted_documents.append({
                "doc": doc,
                "file_path": file_path,
                "content": content,
                "url": item["url"],
                "keywords_matched": item["keywords_matched"]
            })
            
            logger.info(
                "extracted",
                id=doc_id,
                pages=content.page_count,
                nc_codes=len(content.nc_codes)
            )
            
        except Exception as e:
            logger.error("extraction_error", id=doc_id, error=str(e))
            extraction_errors.append({"doc": doc, "error": str(e)})
    
    logger.info(
        "step_4_completed",
        extracted=len(extracted_documents),
        errors=len(extraction_errors)
    )
    
    # ====================================================================
    # ÉTAPE 5 : SAUVEGARDE EN BASE DE DONNÉES
    # ====================================================================
    saved_count = 0
    save_errors = []
    
    if save_to_db and extracted_documents:
        logger.info("step_5_saving", count=len(extracted_documents))
        
        try:
            from src.storage.database import get_session
            from src.storage.repositories import DocumentRepository
            
            session = get_session()
            repo = DocumentRepository(session)
            
            for item in extracted_documents:
                try:
                    doc = item["doc"]
                    content = item["content"]
                    file_path = item["file_path"]
                    keywords_matched = item["keywords_matched"]
                    
                    # Calculer hash du fichier
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    
                    # Métadonnées
                    metadata = {
                        "collection_mode": "company_profile",
                        "company_name": company_keywords.company_name,
                        "company_id": company_keywords.company_id,
                        "celex_number": doc.celex_number,
                        "document_type": doc.document_type or "UNKNOWN",
                        "keywords_matched": keywords_matched,
                        "priority_threshold": priority_threshold,
                        "collected_at": datetime.now().isoformat(),
                        "nc_codes_found": [nc.code for nc in content.nc_codes[:20]] if content.nc_codes else [],
                        "page_count": content.page_count,
                        "pdf_path": file_path,
                        "source": doc.source,
                        "status": doc.status
                    }
                    
                    # Sauvegarder avec upsert_document
                    saved_doc, status = repo.upsert_document(
                        source_url=item["url"],
                        hash_sha256=file_hash,
                        title=doc.title,
                        content=content.text[:50000] if content.text else "",
                        nc_codes=[nc.code for nc in content.nc_codes[:100]] if content.nc_codes else [],
                        regulation_type="TO_CLASSIFY",  # Agent 1B classifiera
                        publication_date=doc.publication_date,
                        document_metadata=metadata
                    )
                    
                    saved_count += 1
                    logger.info("saved", celex=doc.celex_number, id=saved_doc.id, status=status)
                    
                except Exception as e:
                    logger.error("save_error", celex=doc.celex_number, error=str(e))
                    save_errors.append({"doc": doc, "error": str(e)})
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error("db_transaction_failed", error=str(e))
        finally:
            session.close()
        
        logger.info("step_5_completed", saved=saved_count, errors=len(save_errors))
    else:
        logger.info("step_5_skipped", reason="save_to_db=False or no documents")
    
    # ====================================================================
    # RÉSULTAT FINAL
    # ====================================================================
    result = {
        "status": "success",
        "mode": "company_profile",
        "company": {
            "name": company_keywords.company_name,
            "id": company_keywords.company_id,
            "profile_path": profile_path
        },
        "keywords": {
            "extracted_total": len(company_keywords.get_all_keywords()),
            "used_for_search": len(search_keywords),
            "priority_threshold": priority_threshold,
            "list": search_keywords
        },
        "keyword_stats": keyword_stats,
        "documents": {
            "unique_found": len(all_documents),
            "downloaded": len(downloaded_files),
            "extracted": len(extracted_documents),
            "saved": saved_count
        },
        "errors": {
            "download": len(download_errors),
            "extraction": len(extraction_errors),
            "save": len(save_errors)
        }
    }
    
    logger.info("agent_1a_from_profile_completed", result=result)
    
    return result


# ========================================
# COLLECTE MÉTÉOROLOGIQUE (CDC CONFORME)
# ========================================

async def run_agent_1a_weather(
    sites_config_path: str = None,
    forecast_days: int = 16,
    save_to_db: bool = True
) -> Dict:
    """
    Pipeline Agent 1A - Collecte des alertes météorologiques.
    
    Cette fonction :
    1. Charge les localisations des sites (usines, fournisseurs, ports)
    2. Récupère les prévisions météo via Open-Meteo API (16 jours)
    3. Détecte les alertes (neige, pluie, vent, températures extrêmes)
    4. Sauvegarde les alertes en base de données
    
    Args:
        sites_config_path: Chemin vers le fichier JSON des sites.
                          Si None, utilise config/sites_locations.json
        forecast_days: Nombre de jours de prévisions (max 16)
        save_to_db: Sauvegarder en base de données (défaut: True)
        
    Returns:
        dict: Résultat avec statistiques et alertes
    """
    import json
    from pathlib import Path
    from .tools.weather import (
        Location,
        fetch_weather_for_sites,
        WeatherAlert as WeatherAlertModel
    )
    
    logger.info(
        "agent_1a_weather_started",
        sites_config_path=sites_config_path,
        forecast_days=forecast_days,
        save_to_db=save_to_db
    )
    
    # ====================================================================
    # ÉTAPE 1 : CHARGEMENT DES SITES
    # ====================================================================
    logger.info("step_1_loading_sites")
    
    if sites_config_path is None:
        sites_config_path = Path(__file__).parent.parent.parent / "config" / "sites_locations.json"
    else:
        sites_config_path = Path(sites_config_path)
    
    if not sites_config_path.exists():
        logger.error("sites_config_not_found", path=str(sites_config_path))
        return {
            "status": "error",
            "error": f"Sites config not found: {sites_config_path}"
        }
    
    with open(sites_config_path, "r", encoding="utf-8") as f:
        sites_data = json.load(f)
    
    locations = []
    
    # Sites Hutchinson
    for site in sites_data.get("hutchinson_sites", []):
        locations.append(Location(
            site_id=site["site_id"],
            name=site["name"],
            city=site["city"],
            country=site["country"],
            latitude=site["latitude"],
            longitude=site["longitude"],
            site_type=site.get("site_type", "manufacturing"),
            criticality=site.get("criticality", "normal"),
        ))
    
    # Fournisseurs
    for supplier in sites_data.get("suppliers", []):
        locations.append(Location(
            site_id=supplier["site_id"],
            name=supplier["name"],
            city=supplier["city"],
            country=supplier["country"],
            latitude=supplier["latitude"],
            longitude=supplier["longitude"],
            site_type="supplier",
            criticality=supplier.get("criticality", "normal"),
        ))
    
    # Ports
    for port in sites_data.get("ports", []):
        locations.append(Location(
            site_id=port["site_id"],
            name=port["name"],
            city=port["city"],
            country=port["country"],
            latitude=port["latitude"],
            longitude=port["longitude"],
            site_type="port",
            criticality=port.get("criticality", "high"),
        ))
    
    logger.info("step_1_completed", sites_count=len(locations))
    
    # ====================================================================
    # ÉTAPE 2 : RÉCUPÉRATION DES PRÉVISIONS MÉTÉO
    # ====================================================================
    logger.info("step_2_fetching_weather", sites_count=len(locations), forecast_days=forecast_days)
    
    forecasts, alerts = await fetch_weather_for_sites(locations, forecast_days=forecast_days)
    
    logger.info(
        "step_2_completed",
        forecasts_count=len(forecasts),
        alerts_count=len(alerts)
    )
    
    # ====================================================================
    # ÉTAPE 3 : SAUVEGARDE EN BASE DE DONNÉES
    # ====================================================================
    saved_count = 0
    save_errors = []
    
    if save_to_db and alerts:
        logger.info("step_3_saving_alerts", count=len(alerts))
        
        from src.storage.database import SessionLocal
        from src.storage.models import WeatherAlert as WeatherAlertDB
        
        db = SessionLocal()
        
        try:
            for alert in alerts:
                try:
                    # Créer l'enregistrement en BDD
                    db_alert = WeatherAlertDB(
                        site_id=alert.location.site_id,
                        site_name=alert.location.name,
                        city=alert.location.city,
                        country=alert.location.country,
                        latitude=alert.location.latitude,
                        longitude=alert.location.longitude,
                        site_type=alert.location.site_type,
                        site_criticality=alert.location.criticality,
                        alert_type=alert.alert_type,
                        severity=alert.severity,
                        alert_date=alert.date,
                        value=alert.value,
                        threshold=alert.threshold,
                        unit=alert.unit,
                        description=alert.description,
                        supply_chain_risk=alert.supply_chain_risk,
                        status="new"
                    )
                    
                    db.add(db_alert)
                    db.commit()
                    
                    saved_count += 1
                    logger.info(
                        "alert_saved",
                        site=alert.location.site_id,
                        type=alert.alert_type,
                        severity=alert.severity,
                        date=str(alert.date)
                    )
                    
                except Exception as e:
                    db.rollback()
                    logger.error("alert_save_error", site=alert.location.site_id, error=str(e))
                    save_errors.append({"alert": alert, "error": str(e)})
        
        finally:
            db.close()
        
        logger.info("step_3_completed", saved=saved_count, errors=len(save_errors))
    else:
        logger.info("step_3_skipped", reason="save_to_db=False or no alerts")
    
    # ====================================================================
    # RÉSULTAT FINAL
    # ====================================================================
    
    # Statistiques par sévérité
    severity_stats = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for alert in alerts:
        severity_stats[alert.severity] += 1
    
    # Statistiques par type
    type_stats = {}
    for alert in alerts:
        type_stats[alert.alert_type] = type_stats.get(alert.alert_type, 0) + 1
    
    result = {
        "status": "success",
        "mode": "weather_monitoring",
        "sites": {
            "total": len(locations),
            "forecasts_fetched": len(forecasts)
        },
        "alerts": {
            "total": len(alerts),
            "saved": saved_count,
            "by_severity": severity_stats,
            "by_type": type_stats
        },
        "forecast_days": forecast_days,
        "errors": {
            "save": len(save_errors)
        }
    }
    
    logger.info("agent_1a_weather_completed", result=result)
    
    return result