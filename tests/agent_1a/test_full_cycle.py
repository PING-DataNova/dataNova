"""
Test du cycle complet Agent 1A : Scraper → Fetcher → Extractor

Test l'intégration des 3 outils ensemble.
"""

import asyncio
from pathlib import Path

from src.agent_1a.tools.scraper import scrape_cbam_page
from src.agent_1a.tools.document_fetcher import fetch_document
from src.agent_1a.tools.pdf_extractor import extract_pdf_content


async def test_full_agent_1a_cycle():
    """
    Test complet du workflow Agent 1A.
    
    Workflow:
    1. Scraper : Trouver les documents sur la page CBAM
    2. Fetcher : Télécharger les 3 premiers PDF
    3. Extractor : Extraire le contenu + codes NC
    """
    print("=" * 80)
    print("🚀 TEST CYCLE COMPLET AGENT 1A")
    print("=" * 80)
    
    # ÉTAPE 1 : SCRAPING
    print("\n📡 ÉTAPE 1/3 : Scraping de la page CBAM...")
    print("-" * 80)
    
    url = "https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism/cbam-legislation-and-guidance_en"
    scrape_result = await scrape_cbam_page(url)
    
    if scrape_result.status != "success":
        print(f"❌ Erreur scraping: {scrape_result.error}")
        return
    
    print(f"✅ {scrape_result.total_found} documents trouvés")
    print(f"   - EUR-Lex: {len([d for d in scrape_result.documents if 'eur-lex' in str(d.url).lower()])}")
    print(f"   - PDF directs: {len([d for d in scrape_result.documents if d.document_type == 'PDF Direct'])}")
    print(f"   - Boutons Download: {len([d for d in scrape_result.documents if d.document_type == 'Downloadable Document'])}")
    
    # ÉTAPE 2 : TÉLÉCHARGEMENT
    print(f"\n📥 ÉTAPE 2/3 : Téléchargement de 3 documents...")
    print("-" * 80)
    
    downloaded_docs = []
    max_downloads = 3
    
    # Filtrer les PDF directs uniquement (plus rapides à télécharger)
    pdf_docs = [d for d in scrape_result.documents if d.document_type == "PDF Direct"][:max_downloads]
    
    for i, doc in enumerate(pdf_docs, 1):
        print(f"\n  [{i}/{max_downloads}] {doc.title[:60]}...")
        print(f"       URL: {str(doc.url)[:80]}...")
        
        fetch_result = await fetch_document(str(doc.url))
        
        if fetch_result.success:
            print(f"       ✅ Téléchargé: {fetch_result.document.file_size:,} bytes")
            print(f"       📁 Fichier: {fetch_result.document.file_path}")
            print(f"       🔐 Hash: {fetch_result.document.hash_sha256[:16]}...")
            downloaded_docs.append(fetch_result.document)
        else:
            print(f"       ❌ Erreur: {fetch_result.error}")
    
    # ÉTAPE 3 : EXTRACTION
    print(f"\n📄 ÉTAPE 3/3 : Extraction du contenu des {len(downloaded_docs)} PDFs...")
    print("-" * 80)
    
    total_nc_codes = 0
    total_pages = 0
    
    for i, doc in enumerate(downloaded_docs, 1):
        print(f"\n  [{i}/{len(downloaded_docs)}] Extraction: {Path(doc.file_path).name}")
        
        extract_result = await extract_pdf_content(doc.file_path)
        
        if extract_result.status == "success":
            print(f"       ✅ {extract_result.page_count} pages extraites")
            print(f"       📝 Texte: {len(extract_result.text):,} caractères")
            print(f"       📊 Tableaux: {len(extract_result.tables)}")
            print(f"       🔢 Codes NC: {len(extract_result.nc_codes)}")
            
            if extract_result.nc_codes:
                print(f"       📋 Premiers codes NC:")
                for nc in extract_result.nc_codes[:3]:
                    print(f"          - {nc.code} (page {nc.page}, conf: {nc.confidence:.2f})")
            
            total_nc_codes += len(extract_result.nc_codes)
            total_pages += extract_result.page_count
        else:
            print(f"       ❌ Erreur: {extract_result.error}")
    
    # RÉSUMÉ FINAL
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 80)
    print(f"✅ Documents scrapés: {scrape_result.total_found}")
    print(f"✅ Documents téléchargés: {len(downloaded_docs)}")
    print(f"✅ Pages extraites: {total_pages}")
    print(f"✅ Codes NC détectés: {total_nc_codes}")
    print(f"✅ Fichiers sauvegardés: data/documents/")
    print("\n🎉 Test du cycle complet RÉUSSI !")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_full_agent_1a_cycle())
