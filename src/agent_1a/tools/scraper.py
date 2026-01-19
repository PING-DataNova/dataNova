"""
EUR-Lex Scraper - Recherche et extraction de documents réglementaires

Scrape directement EUR-Lex avec Playwright pour contourner AWS WAF.

Responsable: Dev 1
"""

import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, quote

import httpx
import structlog
from langchain.tools import tool
import json
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl
from playwright.async_api import async_playwright

logger = structlog.get_logger()

# User-Agent pour éviter les blocages
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Mapping des types de documents CELEX
CELEX_DOCUMENT_TYPES = {
    'R': 'REGULATION',
    'D': 'DIRECTIVE',
    'A': 'OPINION',
    'C': 'COMMUNICATION',
    'E': 'DECISION',
    'L': 'LEGISLATION',
}

# Types de documents à inclure (seulement Regulations et Directives)
ALLOWED_DOCUMENT_TYPES = {'R', 'D'}


def _get_document_type_from_celex(celex_number: str) -> str:
    """Extrait le type de document depuis le code CELEX (6ème caractère)"""
    if not celex_number or len(celex_number) < 6:
        return "UNKNOWN"
    doc_type_char = celex_number[5].upper()
    return CELEX_DOCUMENT_TYPES.get(doc_type_char, "UNKNOWN")


def _should_include_document(celex_number: Optional[str]) -> bool:
    """Filtre: garde seulement Regulations (R) et Directives (D)"""
    if not celex_number or len(celex_number) < 6:
        return False
    doc_type_char = celex_number[5].upper()
    should_include = doc_type_char in ALLOWED_DOCUMENT_TYPES
    if not should_include:
        doc_type = CELEX_DOCUMENT_TYPES.get(doc_type_char, "UNKNOWN")
        logger.debug("document_filtered_out", celex=celex_number, type=doc_type)
    return should_include


class EURLexDocument(BaseModel):
    """Modèle pour un document EUR-Lex"""
    title: str
    celex_number: Optional[str] = None
    document_type: str  # REGULATION, DIRECTIVE, DECISION, PROPOSAL, etc.
    publication_date: Optional[str] = None  # Format ISO 8601
    url: HttpUrl  # URL de la page du document
    pdf_url: Optional[HttpUrl] = None  # URL directe du PDF
    summary: Optional[str] = None
    status: str = "UNKNOWN"  # ACTIVE_LAW, PROPOSAL, etc.
    metadata: Dict[str, Any] = {}


class EURLexSearchResult(BaseModel):
    """Résultat de recherche EUR-Lex"""
    keyword: str
    search_url: HttpUrl
    scraped_at: datetime
    documents: List[EURLexDocument]
    total_found: int
    status: str
    error: Optional[str] = None


async def search_eurlex(
    keyword: str,
    max_results: int = 50,
    language: str = "en"
) -> EURLexSearchResult:
    """
    Recherche des documents sur EUR-Lex avec Playwright (contourne AWS WAF).
    
    Args:
        keyword: Mot-clé de recherche (ex: "CBAM", "EUDR", "CSRD")
        max_results: Nombre maximum de résultats à récupérer
        language: Langue de recherche (en, fr, de, etc.)
    
    Returns:
        EURLexSearchResult: Résultats de la recherche
    """
    logger.info("eurlex_search_started", keyword=keyword, max_results=max_results, method="playwright")
    
    # Construire l'URL de recherche
    search_url = f"https://eur-lex.europa.eu/search.html?text={quote(keyword)}&lang={language}&type=quick&scope=EURLEX"
    
    try:
        # Utiliser Playwright pour contourner AWS WAF
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Naviguer vers la page (timeout augmenté + domcontentloaded au lieu de networkidle)
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            
            # Attendre que les résultats soient chargés (liens avec id "cellar_X")
            try:
                await page.wait_for_selector('a[id^="cellar_"]', timeout=30000)
            except Exception:
                logger.warning("eurlex_no_results_found", keyword=keyword)
            
            # Récupérer le contenu HTML
            content = await page.content()
            await browser.close()
        
        soup = BeautifulSoup(content, 'lxml')
        documents = []
        
        # Extraire le nombre total de résultats
        # Chercher dans tous les éléments contenant "Results"
        total_found = 0
        
        # Méthode 1 : Chercher dans les labels
        total_text = soup.find('label', string=re.compile(r'Results.*of.*\d+', re.IGNORECASE))
        if total_text:
            match = re.search(r'of\s+(\d+)', total_text.text)
            if match:
                total_found = int(match.group(1))
        
        # Méthode 2 : Chercher dans tout le texte de la page
        if total_found == 0:
            page_text = soup.get_text()
            match = re.search(r'Results\s+\d+\s*-\s*\d+\s+of\s+(\d+)', page_text, re.IGNORECASE)
            if match:
                total_found = int(match.group(1))
        
        logger.info("eurlex_total_found", total=total_found)
        
        # Extraire les résultats de la page
        # Les documents ont des IDs comme "cellar_1", "cellar_2", etc.
        result_links = soup.find_all('a', id=re.compile(r'^cellar_\d+$'))
        
        for idx, link in enumerate(result_links[:max_results], 1):
            try:
                # Titre
                title = link.get_text(strip=True)
                
                # URL de la page du document
                doc_url = urljoin(search_url, link.get('href', ''))
                
                # Trouver le conteneur parent immédiat pour ce document spécifique
                # Ne pas aller trop loin pour éviter de mélanger les métadonnées
                parent = link.find_parent()
                
                # Chercher le conteneur de résultat (généralement 2-3 niveaux au-dessus)
                result_container = parent
                for _ in range(3):
                    if result_container:
                        result_container = result_container.find_parent()
                    else:
                        break
                
                # Extraire le CELEX depuis les liens PDF/HTML
                celex_number = None
                pdf_url = None
                
                # Chercher les liens PDF et HTML dans le conteneur de résultat spécifique
                if result_container:
                    celex_links = result_container.find_all('a', attrs={'hint': re.compile(r'CELEX:')})
                    
                    for celex_link in celex_links:
                        hint = celex_link.get('hint', '')
                        celex_match = re.search(r'CELEX:(\d{5}[A-Z]\d{4})', hint)
                        if celex_match:
                            celex_number = celex_match.group(1)
                            
                            # Si c'est un lien PDF, construire l'URL du PDF
                            if 'pdf' in hint.lower():
                                pdf_url = f"https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:{celex_number}"
                            break
                
                # Si pas trouvé, essayer d'extraire depuis l'URL du document
                if not celex_number:
                    doc_href = link.get('href', '')
                    celex_match = re.search(r'CELEX:(\d{5}[A-Z]\d{4})', doc_href)
                    if celex_match:
                        celex_number = celex_match.group(1)
                        pdf_url = f"https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:{celex_number}"
                
                # ✅ FILTRAGE: Ignorer opinions (A) et communications (C)
                if not _should_include_document(celex_number):
                    continue
                
                # Extraire la date de publication
                pub_date = None
                
                # Méthode 1 : Chercher une date dans le titre (ex: "18 December 2024")
                date_in_title = re.search(r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})', title, re.IGNORECASE)
                if date_in_title:
                    day, month_name, year = date_in_title.groups()
                    month_map = {
                        'january': 1, 'february': 2, 'march': 3, 'april': 4,
                        'may': 5, 'june': 6, 'july': 7, 'august': 8,
                        'september': 9, 'october': 10, 'november': 11, 'december': 12
                    }
                    month = month_map.get(month_name.lower())
                    if month:
                        try:
                            dt = datetime(int(year), month, int(day))
                            pub_date = dt.isoformat()
                        except ValueError:
                            pass
                
                # Méthode 2 : Chercher un lien avec une date à côté du document (dans le même parent)
                if not pub_date and result_container:
                    # Chercher tous les liens avec format DD/MM/YYYY dans ce conteneur
                    date_links = result_container.find_all('a', string=re.compile(r'^\d{2}/\d{2}/\d{4}$'))
                    if date_links:
                        # Prendre la première date trouvée
                        date_str = date_links[0].get_text(strip=True)
                        pub_date = _parse_eurlex_date(date_str)
                
                # Méthode 3 : Chercher "Date of document:" dans le conteneur
                if not pub_date and result_container:
                    container_text = result_container.get_text()
                    date_match = re.search(r'Date of document:\s*(\d{2}/\d{2}/\d{4})', container_text)
                    if date_match:
                        pub_date = _parse_eurlex_date(date_match.group(1))
                
                # Déterminer le type de document depuis CELEX
                doc_type = _get_document_type_from_celex(celex_number)
                
                # Déterminer le statut
                status = _determine_eurlex_status(result_container, doc_type)
                
                # Créer le document
                doc = EURLexDocument(
                    title=title,
                    celex_number=celex_number,
                    document_type=doc_type,
                    publication_date=pub_date,
                    url=doc_url,
                    pdf_url=pdf_url,
                    summary=None,
                    status=status,
                    metadata={
                        "source": "EUR-Lex Search",
                        "keyword": keyword,
                        "result_position": idx
                    }
                )
                
                documents.append(doc)
                
            except Exception as e:
                logger.warning("eurlex_document_extraction_error", error=str(e), index=idx)
                continue
        
        logger.info(
            "eurlex_search_completed",
            keyword=keyword,
            documents_extracted=len(documents),
            total_available=total_found
        )
        
        return EURLexSearchResult(
            keyword=keyword,
            search_url=search_url,
            scraped_at=datetime.now(timezone.utc),
            documents=documents,
            total_found=total_found,
            status="success"
        )
        
    except httpx.HTTPError as e:
        logger.error("eurlex_search_http_error", error=str(e), keyword=keyword)
        return EURLexSearchResult(
            keyword=keyword,
            search_url=search_url,
            scraped_at=datetime.now(timezone.utc),
            documents=[],
            total_found=0,
            status="error",
            error=f"HTTP Error: {str(e)}"
        )
    
    except Exception as e:
        logger.error("eurlex_search_unexpected_error", error=str(e), keyword=keyword, exc_info=True)
        return EURLexSearchResult(
            keyword=keyword,
            search_url=search_url,
            scraped_at=datetime.now(timezone.utc),
            documents=[],
            total_found=0,
            status="error",
            error=f"Unexpected error: {str(e)}"
        )


def _parse_eurlex_date(date_str: str) -> Optional[str]:
    """
    Parse une date EUR-Lex (format DD/MM/YYYY) en ISO 8601.
    
    Args:
        date_str: Date au format DD/MM/YYYY
    
    Returns:
        str: Date au format ISO 8601 ou None
    """
    try:
        # Format: DD/MM/YYYY
        match = re.match(r'(\d{2})/(\d{2})/(\d{4})', date_str)
        if match:
            day, month, year = match.groups()
            dt = datetime(int(year), int(month), int(day))
            return dt.isoformat()
    except Exception:
        pass
    return None


def _determine_eurlex_document_type(title: str, celex_number: Optional[str]) -> str:
    """
    Détermine le type de document EUR-Lex.
    
    Returns:
        str: REGULATION, DIRECTIVE, DECISION, PROPOSAL, OPINION, etc.
    """
    title_lower = title.lower()
    
    # Vérifier les mots-clés dans le titre
    if 'proposal' in title_lower or 'com(' in title_lower:
        return "PROPOSAL"
    elif 'implementing regulation' in title_lower:
        return "IMPLEMENTING_REGULATION"
    elif 'regulation' in title_lower or (celex_number and 'R' in celex_number):
        return "REGULATION"
    elif 'directive' in title_lower or (celex_number and 'L' in celex_number):
        return "DIRECTIVE"
    elif 'decision' in title_lower or (celex_number and 'D' in celex_number):
        return "DECISION"
    elif 'opinion' in title_lower:
        return "OPINION"
    elif 'communication' in title_lower:
        return "COMMUNICATION"
    elif 'report' in title_lower:
        return "REPORT"
    else:
        return "DOCUMENT"


def _determine_eurlex_status(parent_element, doc_type: str) -> str:
    """
    Détermine le statut du document EUR-Lex.
    
    Returns:
        str: ACTIVE_LAW, PROPOSAL, IN_FORCE, UNKNOWN
    """
    if parent_element:
        # Chercher "In force" dans le texte
        if parent_element.find(string=re.compile(r'In force', re.IGNORECASE)):
            return "ACTIVE_LAW"
    
    # Basé sur le type
    if doc_type == "PROPOSAL":
        return "PROPOSAL"
    elif doc_type in ["REGULATION", "DIRECTIVE", "IMPLEMENTING_REGULATION"]:
        return "ACTIVE_LAW"
    elif doc_type == "DECISION":
        return "DECISION"
    else:
        return "UNKNOWN"


@tool
async def search_eurlex_tool(keyword: str = "CBAM", max_results: int = 10) -> str:
    """Recherche EUR-Lex. Retourne JSON: {documents:[{title,celex_number,url,pdf_url,document_type,date,status}]}"""
    result = await search_eurlex(keyword, max_results)
    
    return json.dumps({
        "status": result.status,
        "keyword": result.keyword,
        "total_found": result.total_found,
        "documents_returned": len(result.documents),
        "documents": [
            {
                "title": doc.title,
                "celex_number": doc.celex_number,
                "document_type": doc.document_type,
                "publication_date": doc.publication_date,
                "url": str(doc.url),
                "pdf_url": str(doc.pdf_url) if doc.pdf_url else None,
                "summary": doc.summary,
                "status": doc.status
            }
            for doc in result.documents
        ],
        "error": result.error
    }, ensure_ascii=False, indent=2)


def search_eurlex_sync(keyword: str, max_results: int = 50) -> EURLexSearchResult:
    """Version synchrone du scraper EUR-Lex."""
    import asyncio
    return asyncio.run(search_eurlex(keyword, max_results))


# Pour tester le module directement
if __name__ == "__main__":
    import asyncio
    
    async def test_eurlex():
        print("=" * 80)
        print("🔍 TEST EUR-LEX SCRAPER - Recherche CBAM")
        print("=" * 80)
        
        # Rechercher les documents CBAM
        result = await search_eurlex("CBAM", max_results=5)
        
        print(f"\n✅ Recherche terminée")
        print(f"Total trouvé: {result.total_found} documents")
        print(f"Extraits: {len(result.documents)} documents\n")
        
        # Afficher les premiers résultats
        for i, doc in enumerate(result.documents, 1):
            print(f"\n{'='*60}")
            print(f"Document {i}: {doc.title[:80]}...")
            print(f"{'='*60}")
            print(f"CELEX: {doc.celex_number}")
            print(f"Type: {doc.document_type}")
            print(f"Status: {doc.status}")
            print(f"Date: {doc.publication_date}")
            print(f"URL: {doc.url}")
            print(f"PDF: {doc.pdf_url}")
        
        print("\n" + "=" * 80)
        print("✅ Test terminé !")
        print("=" * 80)
    
    asyncio.run(test_eurlex())