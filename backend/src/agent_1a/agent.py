"""
Agent 1A - Pipeline EUR-Lex

Collecte les documents réglementaires depuis EUR-Lex :
- Approche par DOMAINES (Option 3 - CDC) : collecte générique sans filtrage métier
- Approche par MOT-CLÉ (legacy) : recherche ciblée par réglementation

L'Agent 1A collecte et stocke. L'Agent 1B filtre la pertinence.
"""

import asyncio
import structlog
import json
import os
import time
from typing import Dict, List, Optional
from datetime import datetime
import hashlib

from .tools.scraper import search_eurlex, search_eurlex_by_domain, load_eurlex_domains_config
from .tools.document_fetcher import fetch_document
from .tools.pdf_extractor import extract_pdf_content
from .tools.weather import OpenMeteoClient, Location

logger = structlog.get_logger()


# ========================================
# SCÉNARIO 1 : COLLECTE AUTOMATIQUE COMPLÈTE (conforme CDC)
# ========================================

async def run_agent_1a_full_collection(
    company_profile_path: str = "data/company_profiles/Hutchinson_SA.json",
    sites_config_path: str = "config/sites_locations.json",
    min_publication_year: int = 2000,
    max_documents_per_keyword: int = 10,
    max_keywords: int = 0,  # 0 = tous les mots-clés
    save_to_db: bool = True
) -> Dict:
    """
    Scénario 1 : Collecte automatique complète pour l'entreprise.
    
    Cette fonction :
    1. Lit le profil entreprise pour extraire les mots-clés pertinents
    2. Recherche sur EUR-Lex avec ces mots-clés
    3. Télécharge et extrait les PDFs
    4. Collecte la météo pour tous les sites (usines, fournisseurs, ports)
    5. Sauvegarde tout en BDD
    
    Args:
        company_profile_path: Chemin vers le profil entreprise JSON
        sites_config_path: Chemin vers la config des sites
        min_publication_year: Année minimum de publication (défaut: 2000)
        max_documents_per_keyword: Max documents par mot-clé (défaut: 10)
        save_to_db: Sauvegarder en BDD (défaut: True)
        
    Returns:
        dict: Résultat avec statistiques
    """
    start_time = time.time()
    
    logger.info(
        "agent_1a_full_collection_started",
        company_profile=company_profile_path,
        sites_config=sites_config_path
    )
    
    # ====================================================================
    # ÉTAPE 1 : CHARGER LE PROFIL ENTREPRISE ET EXTRAIRE LES MOTS-CLÉS
    # ====================================================================
    logger.info("step_1_loading_company_profile")
    
    try:
        with open(company_profile_path, 'r', encoding='utf-8') as f:
            company_profile = json.load(f)
    except FileNotFoundError:
        logger.error("company_profile_not_found", path=company_profile_path)
        return {"status": "error", "error": f"Profil non trouvé: {company_profile_path}"}
    
    # Extraire les mots-clés depuis le profil
    keywords = _extract_keywords_from_profile(company_profile)
    
    # Limiter le nombre de mots-clés si demandé (pour les tests)
    if max_keywords > 0:
        keywords = keywords[:max_keywords]
        logger.info("keywords_limited", max_keywords=max_keywords)
    
    logger.info("step_1_completed", keywords_extracted=len(keywords), keywords=keywords[:10])
    
    # ====================================================================
    # ÉTAPE 2 : COLLECTE EUR-LEX PAR MOTS-CLÉS
    # ====================================================================
    logger.info("step_2_eurlex_collection", keywords_count=len(keywords))
    
    from src.storage.database import SessionLocal
    from src.storage.models import Document
    
    all_documents = []
    seen_celexes = set()
    download_errors = 0
    extraction_errors = 0
    
    for keyword in keywords:
        try:
            # Rechercher sur EUR-Lex
            result = await search_eurlex(
                keyword=keyword,
                max_results=max_documents_per_keyword,
                consolidated_only=True  # Préférence pour les textes consolidés (CELEX préfixe 0)
            )
            
            docs = result.documents if hasattr(result, 'documents') else []
            
            for doc in docs:
                celex = getattr(doc, 'celex_id', '') or getattr(doc, 'celex_number', '') or ''
                
                # Éviter les doublons
                if celex and celex in seen_celexes:
                    continue
                seen_celexes.add(celex)
                
                # Vérifier l'année de publication
                pub_date = getattr(doc, 'publication_date', None)
                if pub_date:
                    try:
                        year = pub_date.year if hasattr(pub_date, 'year') else int(str(pub_date)[:4])
                        if year < min_publication_year:
                            continue
                    except:
                        pass
                
                all_documents.append({
                    'eurlex_doc': doc,
                    'matched_keyword': keyword,
                    'celex': celex
                })
                
        except Exception as e:
            logger.warning("eurlex_search_error", keyword=keyword, error=str(e))
    
    logger.info("step_2_eurlex_completed", unique_documents=len(all_documents))
    
    # ====================================================================
    # ÉTAPE 3 : TÉLÉCHARGER ET EXTRAIRE LES PDFs
    # ====================================================================
    logger.info("step_3_downloading_pdfs", count=len(all_documents))
    
    documents_saved = []
    db = SessionLocal() if save_to_db else None
    
    try:
        for doc_info in all_documents:
            eurlex_doc = doc_info['eurlex_doc']
            keyword = doc_info['matched_keyword']
            celex = doc_info['celex']
            
            try:
                pdf_url = getattr(eurlex_doc, 'pdf_url', None)
                title = getattr(eurlex_doc, 'title', '') or ''
                eurlex_url = getattr(eurlex_doc, 'eurlex_url', '') or getattr(eurlex_doc, 'url', '') or ''
                doc_type = getattr(eurlex_doc, 'document_type', '') or ''
                
                content = ""
                local_path = None
                doc_hash = None
                
                # Télécharger le PDF si disponible
                MAX_PDF_SIZE_MB = 10  # Ignorer les PDFs > 10MB pour éviter les timeouts
                if pdf_url:
                    try:
                        fetch_result = await fetch_document(str(pdf_url), output_dir="data/documents")
                        if fetch_result and fetch_result.success and fetch_result.document:
                            local_path = fetch_result.document.file_path
                            doc_hash = fetch_result.document.hash_sha256
                            
                            # Vérifier la taille du fichier
                            file_size_mb = os.path.getsize(local_path) / (1024 * 1024)
                            if file_size_mb > MAX_PDF_SIZE_MB:
                                logger.warning("pdf_too_large_skipping", celex=celex, size_mb=round(file_size_mb, 2))
                                # On garde quand même le doc mais sans extraction
                            else:
                                # Extraire le contenu
                                extracted = await extract_pdf_content(local_path)
                                if isinstance(extracted, dict):
                                    content = extracted.get("text", "")[:50000]  # Limiter
                    except Exception as e:
                        download_errors += 1
                        logger.warning("pdf_download_error", celex=celex, error=str(e))
                
                # Générer un hash si pas de PDF
                if not doc_hash:
                    source_url = str(pdf_url) if pdf_url else eurlex_url
                    doc_hash = hashlib.sha256(source_url.encode()).hexdigest()
                
                # Sauvegarder en BDD
                if save_to_db and db:
                    # Vérifier si le document existe déjà
                    existing = db.query(Document).filter(Document.hash_sha256 == doc_hash).first()
                    if existing:
                        continue
                    
                    new_doc = Document(
                        title=title[:500],
                        source_url=str(pdf_url) if pdf_url else eurlex_url[:1000],
                        event_type="regulation",
                        event_subtype=doc_type or "EUR-LEX",
                        hash_sha256=doc_hash,
                        content=content,
                        summary=title,
                        status="new",
                        extra_metadata={
                            "celex_id": celex,
                            "matched_keyword": keyword,
                            "local_path": local_path,
                            "collection_mode": "automatic"
                        }
                    )
                    
                    db.add(new_doc)
                    documents_saved.append({
                        "celex": celex,
                        "title": title[:80],
                        "keyword": keyword
                    })
                    
                    logger.info("document_saved", celex=celex, title=title[:50])
                    
            except Exception as e:
                extraction_errors += 1
                logger.warning("document_processing_error", celex=celex, error=str(e))
        
        if save_to_db and db:
            db.commit()
            
    except Exception as e:
        if db:
            db.rollback()
        logger.error("step_3_failed", error=str(e))
    finally:
        if db:
            db.close()
    
    logger.info("step_3_completed", documents_saved=len(documents_saved))
    
    # ====================================================================
    # ÉTAPE 4 : COLLECTE MÉTÉO POUR TOUS LES SITES
    # ====================================================================
    logger.info("step_4_weather_collection")
    
    weather_alerts = []
    sites_processed = 0
    
    try:
        with open(sites_config_path, 'r', encoding='utf-8') as f:
            sites_config = json.load(f)
    except FileNotFoundError:
        logger.warning("sites_config_not_found", path=sites_config_path)
        sites_config = {}
    
    # Collecter tous les sites (Hutchinson + fournisseurs + ports)
    all_sites = []
    
    # Sites Hutchinson
    hutchinson_sites = sites_config.get("hutchinson_sites", [])
    all_sites.extend(hutchinson_sites)
    
    # Fournisseurs critiques
    critical_suppliers = sites_config.get("critical_suppliers", [])
    all_sites.extend(critical_suppliers)
    
    # Ports/hubs logistiques
    logistics_hubs = sites_config.get("logistics_hubs", [])
    all_sites.extend(logistics_hubs)
    
    logger.info("step_4_sites_loaded", 
                hutchinson=len(hutchinson_sites),
                suppliers=len(critical_suppliers),
                hubs=len(logistics_hubs),
                total=len(all_sites))
    
    # Collecter la météo pour chaque site
    weather_client = OpenMeteoClient(forecast_days=16)
    
    db = SessionLocal() if save_to_db else None
    
    try:
        for site in all_sites:
            site_id = site.get("site_id", "unknown")
            lat = site.get("latitude")
            lon = site.get("longitude")
            city = site.get("city", "")
            country = site.get("country", "")
            name = site.get("name", site_id)
            
            if lat is None or lon is None:
                continue
            
            try:
                # Créer l'objet Location requis par get_forecast
                location = Location(
                    site_id=site_id,
                    name=name,
                    city=city,
                    country=country,
                    latitude=lat,
                    longitude=lon,
                    site_type=site.get("type", "manufacturing"),
                    criticality=site.get("criticality", "normal")
                )
                
                # Récupérer les prévisions
                forecast = await weather_client.get_forecast(location)
                
                if forecast:
                    sites_processed += 1
                    
                    # Détecter les alertes (méthode de la classe)
                    alerts = weather_client.detect_alerts(forecast)
                    
                    for alert in alerts:
                        # alert est un objet WeatherAlert (Pydantic), pas un dict
                        alert_data = {
                            "site_id": site_id,
                            "city": city,
                            "alert_type": alert.alert_type,
                            "severity": alert.severity,
                            "date": str(alert.date),
                            "value": alert.value,
                            "threshold": alert.threshold,
                            "message": alert.description
                        }
                        weather_alerts.append(alert_data)
                        
                        # Sauvegarder l'alerte en BDD
                        if save_to_db and db:
                            from src.storage.models import WeatherAlert as WeatherAlertModel
                            weather_alert_db = WeatherAlertModel(
                                site_id=site_id,
                                site_name=name,
                                city=city,
                                country=country,
                                latitude=lat,
                                longitude=lon,
                                site_type=site.get("type", "manufacturing"),
                                site_criticality=site.get("criticality", "normal"),
                                alert_type=alert.alert_type,
                                severity=alert.severity,
                                alert_date=alert.date,
                                value=alert.value,
                                threshold=alert.threshold,
                                unit=alert.unit,
                                description=alert.description,
                                supply_chain_risk=alert.supply_chain_risk,
                                forecast_data={},
                                status="new"
                            )
                            db.add(weather_alert_db)
                            
            except Exception as e:
                logger.warning("weather_fetch_error", site_id=site_id, error=str(e))
        
        if save_to_db and db:
            db.commit()
            
    except Exception as e:
        if db:
            db.rollback()
        logger.error("step_4_failed", error=str(e))
    finally:
        if db:
            db.close()
    
    logger.info("step_4_completed", 
                sites_processed=sites_processed,
                alerts_detected=len(weather_alerts))
    
    # ====================================================================
    # RÉSULTAT FINAL
    # ====================================================================
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    result = {
        "status": "success",
        "mode": "full_collection",
        "company_profile": os.path.basename(company_profile_path),
        "eurlex": {
            "keywords_used": keywords,
            "documents_found": len(all_documents),
            "documents_saved": len(documents_saved),
            "download_errors": download_errors,
            "extraction_errors": extraction_errors
        },
        "weather": {
            "sites_monitored": len(all_sites),
            "sites_processed": sites_processed,
            "alerts_detected": len(weather_alerts)
        },
        "processing_time_ms": processing_time_ms
    }
    
    logger.info(
        "agent_1a_full_collection_completed",
        documents_saved=len(documents_saved),
        weather_alerts=len(weather_alerts),
        processing_time_ms=processing_time_ms
    )
    
    return result


def _extract_keywords_from_profile(profile: Dict) -> List[str]:
    """
    Extrait les mots-clés pertinents pour EUR-Lex depuis le profil entreprise.
    
    Catégories extraites :
    - Matériaux (caoutchouc, élastomères, acier, aluminium...)
    - Codes NC/HS
    - Secteurs d'activité
    - Réglementations surveillées (CBAM, EUDR, CSRD...)
    """
    keywords = set()
    
    # 1. Secteurs et segments
    company = profile.get("company", {})
    industry = company.get("industry", {})
    
    sector = industry.get("sector", "")
    if sector:
        # Extraire les mots clés du secteur
        for word in ["rubber", "elastomer", "materials", "sealing", "automotive"]:
            if word.lower() in sector.lower():
                keywords.add(word)
    
    segments = industry.get("segments", [])
    for segment in segments:
        # "Automotive sealing & NVH" -> "automotive sealing", "NVH"
        keywords.add(segment.split("&")[0].strip().lower())
    
    # 2. Matériaux (supply chain)
    supply_chain = profile.get("supply_chain", {})
    
    # Caoutchouc naturel
    natural_rubber = supply_chain.get("natural_rubber", {})
    if natural_rubber:
        keywords.add("natural rubber")
        keywords.add("rubber")
        for supplier in natural_rubber.get("suppliers", []):
            nc_code = supplier.get("nc_code", "")
            if nc_code:
                keywords.add(nc_code)
    
    # Caoutchouc synthétique
    synthetic_rubber = supply_chain.get("synthetic_rubber", {})
    if synthetic_rubber:
        keywords.add("synthetic rubber")
        keywords.add("EPDM")
        keywords.add("SBR")
        for supplier in synthetic_rubber.get("suppliers", []):
            nc_code = supplier.get("nc_code", "")
            if nc_code:
                keywords.add(nc_code)
    
    # Métaux et additifs
    metals = supply_chain.get("metals_and_additives", {})
    for material in metals.get("critical_materials", []):
        desc = material.get("description", "")
        if desc:
            keywords.add(desc.lower())
        hs_code = material.get("hs_code", "")
        if hs_code:
            keywords.add(hs_code)
    
    # 3. Codes NC explicites
    nc_codes = profile.get("nc_codes", {})
    for item in nc_codes.get("imports", []):
        code = item.get("code", "")
        if code:
            keywords.add(code)
    
    # 4. Réglementations surveillées
    regulatory = profile.get("regulatory_intelligence", {})
    
    # CBAM
    cbam = regulatory.get("cbam", {})
    if cbam:
        keywords.add("CBAM")
        keywords.add("carbon border")
    
    # EUDR
    eudr = regulatory.get("eudr", {})
    if eudr:
        keywords.add("EUDR")
        keywords.add("deforestation")
    
    # CSRD
    csrd = regulatory.get("csrd", {})
    if csrd:
        keywords.add("CSRD")
        keywords.add("sustainability reporting")
    
    # Trade defense
    trade_defense = regulatory.get("trade_defense_and_sanctions", {})
    if trade_defense:
        keywords.add("anti-dumping")
        keywords.add("countervailing")
    
    # 5. Mots-clés génériques importants
    keywords.add("automotive")
    keywords.add("aerospace")
    keywords.add("elastomer")
    keywords.add("sealing")
    keywords.add("emissions")
    keywords.add("carbon")
    
    # Nettoyer et filtrer
    clean_keywords = []
    for kw in keywords:
        kw = str(kw).strip()
        if kw and len(kw) >= 2:  # Ignorer les trop courts
            clean_keywords.append(kw)
    
    # Limiter et trier par pertinence (mots plus spécifiques d'abord)
    clean_keywords = sorted(clean_keywords, key=len, reverse=True)[:25]
    
    return clean_keywords


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


# ========================================
# ANALYSE PONCTUELLE FOURNISSEUR (Mode Supplier)
# ========================================

async def run_agent_1a_for_supplier(
    supplier_info: Dict,
    save_to_db: bool = True
) -> Dict:
    """
    Analyse ponctuelle des risques pour un fournisseur spécifique.
    
    Cette fonction est appelée via l'API quand un utilisateur remplit
    le formulaire "Analyse de risques fournisseur" dans l'interface.
    
    Elle collecte AUTOMATIQUEMENT les risques réglementaires ET météorologiques
    pour donner une vue complète des risques liés à ce fournisseur.
    
    Args:
        supplier_info: Informations du fournisseur
            {
                "name": "Thai Rubber Co.",
                "country": "Thailand",
                "city": "Bangkok",
                "latitude": 13.7563,  # Optionnel, sera géocodé si absent
                "longitude": 100.5018,  # Optionnel
                "nc_codes": ["4001", "400121", "400122"],
                "materials": ["Caoutchouc naturel", "Latex"],
                "criticality": "Important",  # Critique, Important, Standard
                "annual_volume": 2500000  # En euros, optionnel
            }
        save_to_db: Sauvegarder l'analyse en base de données
        
    Returns:
        dict: Résultat complet de l'analyse
            {
                "id": "uuid",
                "supplier_info": {...},
                "regulatory_risks": [...],
                "weather_risks": [...],
                "risk_score": 6.5,
                "risk_level": "Moyen",
                "recommendations": [...],
                "status": "completed"
            }
    """
    import time
    start_time = time.time()
    
    logger.info(
        "agent_1a_supplier_started",
        supplier_name=supplier_info.get("name"),
        country=supplier_info.get("country"),
        city=supplier_info.get("city")
    )
    
    # Extraire les informations
    supplier_name = supplier_info.get("name", "Unknown Supplier")
    country = supplier_info.get("country", "")
    city = supplier_info.get("city", "")
    latitude = supplier_info.get("latitude")
    longitude = supplier_info.get("longitude")
    nc_codes = supplier_info.get("nc_codes", [])
    materials = supplier_info.get("materials", [])
    criticality = supplier_info.get("criticality", "Standard")
    annual_volume = supplier_info.get("annual_volume")
    
    # Liste des IDs de documents sauvegardés (pour lier à supplier_analyses)
    saved_document_ids = []
    
    # ====================================================================
    # ÉTAPE 1 : COLLECTE DES RISQUES RÉGLEMENTAIRES (EUR-Lex)
    # ====================================================================
    logger.info("step_1_regulatory_search", keywords=materials + nc_codes)
    
    regulatory_risks = []
    
    try:
        from .tools.scraper import search_eurlex
        from .tools.document_fetcher import fetch_document
        from .tools.pdf_extractor import extract_pdf_content
        from src.storage.database import SessionLocal
        from src.storage.models import Document
        
        seen_celexes = set()
        documents_to_save = []
        
        # Rechercher sur EUR-Lex pour chaque matière principale
        for keyword in materials[:3]:  # Limiter à 3 matières principales
            try:
                result = await search_eurlex(
                    keyword=keyword,
                    max_results=5,  # 5 par matière
                    consolidated_only=True
                )
                
                docs = result.documents if hasattr(result, 'documents') else []
                
                for doc in docs:
                    celex = getattr(doc, 'celex_id', '') or getattr(doc, 'celex_number', '') or ''
                    if celex and celex not in seen_celexes:
                        seen_celexes.add(celex)
                        title = getattr(doc, 'title', '') or ''
                        pdf_url = getattr(doc, 'pdf_url', None)
                        eurlex_url = getattr(doc, 'eurlex_url', '') or getattr(doc, 'url', '') or ''
                        
                        doc_info = {
                            "celex_id": celex,
                            "title": title,
                            "publication_date": str(getattr(doc, 'publication_date', '')) if getattr(doc, 'publication_date', None) else None,
                            "document_type": getattr(doc, 'document_type', ''),
                            "source_url": eurlex_url,
                            "pdf_url": str(pdf_url) if pdf_url else None,
                            "matched_keyword": keyword,
                            "relevance": "high" if any(m.lower() in title.lower() for m in materials) else "medium"
                        }
                        
                        regulatory_risks.append(doc_info)
                        documents_to_save.append((doc, doc_info))
                        
            except Exception as e:
                logger.warning("regulatory_search_error", keyword=keyword, error=str(e))
        
        # Télécharger et sauvegarder les documents dans la table documents
        logger.info("step_1b_saving_documents", count=len(documents_to_save))
        
        db = SessionLocal()
        try:
            for eurlex_doc, doc_info in documents_to_save[:10]:  # Limiter à 10 documents
                try:
                    pdf_url = doc_info.get("pdf_url")
                    source_url = pdf_url or doc_info.get("source_url", "")
                    
                    # Télécharger le PDF si disponible
                    content = ""
                    local_path_str = None
                    doc_hash = None
                    
                    if pdf_url:
                        try:
                            fetch_result = await fetch_document(pdf_url, output_dir="data/documents")
                            if fetch_result and fetch_result.success and fetch_result.document:
                                local_path_str = fetch_result.document.file_path
                                doc_hash = fetch_result.document.hash_sha256
                                # extract_pdf_content est async
                                extracted = await extract_pdf_content(local_path_str)
                                content = extracted.get("text", "")[:10000] if isinstance(extracted, dict) else ""
                        except Exception as e:
                            logger.warning("pdf_download_error", url=pdf_url, error=str(e))
                    
                    # Si pas de hash (pas de PDF), générer un hash à partir de l'URL
                    if not doc_hash:
                        import hashlib
                        doc_hash = hashlib.sha256(source_url.encode()).hexdigest()
                    
                    # Créer l'entrée dans la table documents
                    new_doc = Document(
                        title=doc_info.get("title", "")[:500],
                        source_url=source_url[:1000] if source_url else "",
                        event_type="regulation",
                        event_subtype=doc_info.get("document_type", "EUR-LEX"),
                        publication_date=None,  # TODO: parser la date
                        hash_sha256=doc_hash,  # Hash du fichier ou de l'URL
                        content=content,
                        summary=doc_info.get("title", ""),
                        status="new",
                        extra_metadata={
                            "celex_id": doc_info.get("celex_id"),
                            "matched_keyword": doc_info.get("matched_keyword"),
                            "relevance": doc_info.get("relevance"),
                            "supplier_analysis": supplier_name,
                            "local_path": local_path_str  # String, pas objet
                        }
                    )
                    
                    db.add(new_doc)
                    db.flush()  # Pour obtenir l'ID
                    saved_document_ids.append(str(new_doc.id))
                    
                    # Mettre à jour doc_info avec l'ID
                    doc_info["document_id"] = str(new_doc.id)
                    
                    logger.info("document_saved_for_supplier", 
                               doc_id=new_doc.id, 
                               title=doc_info.get("title", "")[:50])
                    
                except Exception as e:
                    logger.warning("document_save_error", error=str(e))
            
            db.commit()
            logger.info("step_1b_completed", documents_saved=len(saved_document_ids))
            
        except Exception as e:
            db.rollback()
            logger.error("step_1b_failed", error=str(e))
        finally:
            db.close()
        
        logger.info("step_1_completed", regulatory_risks_found=len(regulatory_risks))
        
    except Exception as e:
        logger.error("step_1_failed", error=str(e))
    
    # ====================================================================
    # ÉTAPE 2 : COLLECTE DES RISQUES MÉTÉOROLOGIQUES (Open-Meteo)
    # ====================================================================
    logger.info("step_2_weather_search", city=city, country=country)
    
    weather_risks = []
    
    try:
        from .tools.weather import OpenMeteoClient, Location
        
        # Si pas de coordonnées, essayer de géocoder
        if not latitude or not longitude:
            # Utiliser des coordonnées connues pour les grandes villes
            city_coords = {
                "bangkok": (13.7563, 100.5018),
                "shanghai": (31.2304, 121.4737),
                "mumbai": (19.0760, 72.8777),
                "mexico city": (19.4326, -99.1332),
                "sao paulo": (-23.5505, -46.6333),
                "paris": (48.8566, 2.3522),
                "berlin": (52.5200, 13.4050),
                "tokyo": (35.6762, 139.6503),
                "seoul": (37.5665, 126.9780),
                "singapore": (1.3521, 103.8198),
            }
            city_lower = city.lower() if city else ""
            if city_lower in city_coords:
                latitude, longitude = city_coords[city_lower]
            else:
                # Coordonnées par défaut basées sur le pays
                country_coords = {
                    "thailand": (13.7563, 100.5018),
                    "china": (31.2304, 121.4737),
                    "india": (19.0760, 72.8777),
                    "mexico": (19.4326, -99.1332),
                    "brazil": (-23.5505, -46.6333),
                    "france": (48.8566, 2.3522),
                    "germany": (52.5200, 13.4050),
                    "japan": (35.6762, 139.6503),
                    "vietnam": (10.8231, 106.6297),
                    "indonesia": (-6.2088, 106.8456),
                }
                country_lower = country.lower() if country else ""
                if country_lower in country_coords:
                    latitude, longitude = country_coords[country_lower]
        
        if latitude and longitude:
            # Créer la localisation
            location = Location(
                site_id=f"supplier-{supplier_name.replace(' ', '-')[:20]}",
                name=supplier_name,  # Champ requis
                city=city or "Unknown",
                country=country[:2].upper() if country else "XX",
                latitude=latitude,
                longitude=longitude,
                site_type="supplier",
                criticality="high" if criticality == "Critique" else "normal"
            )
            
            # Récupérer les prévisions météo (forecast_days est configuré dans le client)
            client = OpenMeteoClient(forecast_days=16)
            forecast = await client.get_forecast(location)
            
            if forecast:
                # Analyser les alertes (detect_alerts prend un seul forecast)
                alerts = client.detect_alerts(forecast)
                
                for alert in alerts:
                    weather_risks.append({
                        "alert_type": alert.alert_type,
                        "severity": alert.severity,
                        "date": str(alert.date),
                        "value": alert.value,
                        "threshold": alert.threshold,
                        "unit": alert.unit,
                        "description": alert.description,
                        "supply_chain_risk": alert.supply_chain_risk
                    })
            
            logger.info("step_2_completed", weather_alerts_found=len(weather_risks))
        else:
            logger.warning("step_2_skipped", reason="no_coordinates")
            
    except Exception as e:
        logger.error("step_2_failed", error=str(e))
    
    # ====================================================================
    # ÉTAPE 3 : SAUVEGARDE EN BASE DE DONNÉES (données brutes collectées)
    # ====================================================================
    # Note: Le scoring et l'analyse seront faits par l'Agent 1B
    analysis_id = None
    
    if save_to_db:
        logger.info("step_3_save_to_db")
        
        try:
            from src.storage.database import SessionLocal
            from src.storage.models import SupplierAnalysis
            
            db = SessionLocal()
            try:
                processing_time = int((time.time() - start_time) * 1000)
                
                analysis = SupplierAnalysis(
                    supplier_name=supplier_name,
                    country=country,
                    city=city,
                    latitude=latitude,
                    longitude=longitude,
                    nc_codes=nc_codes,
                    materials=materials,
                    criticality=criticality,
                    annual_volume=annual_volume,
                    regulatory_risks_count=len(regulatory_risks),
                    regulatory_risks=regulatory_risks,
                    weather_risks_count=len(weather_risks),
                    weather_risks=weather_risks,
                    # Pas de score - ce sera l'Agent 1B qui le calculera
                    risk_score=None,
                    risk_level="pending_analysis",  # En attente d'analyse par 1B
                    recommendations=[],  # Sera rempli par 1B
                    status="collected",  # Statut = collecté, pas encore analysé
                    processing_time_ms=processing_time,
                    # Liste des IDs de documents sauvegardés dans la table documents
                    extra_metadata={
                        "document_ids": saved_document_ids,
                        "documents_saved_count": len(saved_document_ids)
                    }
                )
                
                db.add(analysis)
                db.commit()
                db.refresh(analysis)
                analysis_id = analysis.id
                
                logger.info("step_3_completed", 
                           analysis_id=analysis_id,
                           documents_linked=len(saved_document_ids))
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error("step_3_failed", error=str(e))
    
    # ====================================================================
    # RÉSULTAT FINAL (données collectées uniquement)
    # ====================================================================
    
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    result = {
        "analysis_id": str(analysis_id) if analysis_id else None,
        "status": "collected",  # Collecté, prêt pour analyse par 1B
        "supplier_info": {
            "name": supplier_name,
            "country": country,
            "city": city,
            "latitude": latitude,
            "longitude": longitude,
            "nc_codes": nc_codes,
            "materials": materials,
            "criticality": criticality,
            "annual_volume": annual_volume
        },
        "collected_data": {
            "regulatory": {
                "count": len(regulatory_risks),
                "items": regulatory_risks
            },
            "weather": {
                "count": len(weather_risks),
                "items": weather_risks
            },
            "document_ids": saved_document_ids,  # IDs des documents sauvegardés
            "documents_saved_count": len(saved_document_ids)
        },
        "processing_time_ms": processing_time_ms,
        "next_step": "Agent 1B analysis pending"  # Indique que 1B doit prendre le relais
    }
    
    logger.info(
        "agent_1a_supplier_collection_completed",
        supplier=supplier_name,
        regulatory_count=len(regulatory_risks),
        weather_count=len(weather_risks),
        processing_time_ms=processing_time_ms,
        analysis_id=str(analysis_id) if analysis_id else None
    )
    
    return result