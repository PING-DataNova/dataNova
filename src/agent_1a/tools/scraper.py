"""
TODO: Outil de scraping (LangChain @tool)

Tâches:
1. Décorer avec @tool pour LangChain
2. Scraper une page web donnée
3. Extraire les liens vers documents
4. Extraire les métadonnées (titre, date, type)
5. Retourner résultat structuré

Technologies:
- httpx pour les requêtes HTTP
- BeautifulSoup pour parsing HTML
- Gestion des erreurs réseau
"""
"""
Scraper pour les sources réglementaires (CBAM, EUDR, etc.)

Responsable: Dev 1
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional

import httpx
import structlog
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl

logger = structlog.get_logger()


class ScrapedDocument(BaseModel):
    """Modèle pour un document scrapé"""
    title: str
    url: HttpUrl
    celex_id: Optional[str] = None
    document_type: Optional[str] = None
    publication_date: Optional[str] = None
    metadata: Dict[str, Any] = {}


class ScrapeResult(BaseModel):
    """Résultat du scraping"""
    source_id: str
    source_url: HttpUrl
    scraped_at: datetime
    documents: List[ScrapedDocument]
    total_found: int
    status: str
    error: Optional[str] = None


async def scrape_cbam_page(url: str, source_id: str = "cbam-legislation") -> ScrapeResult:
    """
    Scrape la page CBAM de la Commission Européenne.
    
    Args:
        url: URL de la page à scraper
        source_id: Identifiant de la source
    
    Returns:
        ScrapeResult: Résultat du scraping avec la liste des documents
    """
    logger.info("scraping_started", url=url, source_id=source_id)
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            
        soup = BeautifulSoup(response.text, 'lxml')
        documents = []
        
        # Extraire les liens EUR-Lex
        eur_lex_pattern = re.compile(r'https?://eur-lex\.europa\.eu/[^\s"\'<>]+')
        
        # Rechercher tous les liens
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            
            # Vérifier si c'est un lien EUR-Lex
            if 'eur-lex.europa.eu' in href:
                # Extraire le CELEX ID (format: 32023R0956)
                celex_match = re.search(r'(\d{5}[A-Z]\d{4})', href)
                celex_id = celex_match.group(1) if celex_match else None
                
                # Extraire le titre
                title = link.get_text(strip=True)
                if not title:
                    title = f"Document {celex_id}" if celex_id else "Document sans titre"
                
                # Déterminer le type de document
                doc_type = None
                if 'regulation' in title.lower() or (celex_id and 'R' in celex_id):
                    doc_type = "Regulation"
                elif 'directive' in title.lower() or (celex_id and 'L' in celex_id):
                    doc_type = "Directive"
                elif 'decision' in title.lower() or (celex_id and 'D' in celex_id):
                    doc_type = "Decision"
                elif 'implementing' in title.lower():
                    doc_type = "Implementing Act"
                
                # Extraire la date de publication (si disponible)
                pub_date = None
                date_match = re.search(r'(\d{1,2}[./]\d{1,2}[./]\d{4})', link.parent.get_text() if link.parent else '')
                if date_match:
                    pub_date = date_match.group(1)
                
                # Créer le document
                doc = ScrapedDocument(
                    title=title,
                    url=href,
                    celex_id=celex_id,
                    document_type=doc_type,
                    publication_date=pub_date,
                    metadata={
                        "source": "CBAM EU Commission",
                        "scraped_from": url
                    }
                )
                
                documents.append(doc)
        
        # Dédupliquer par CELEX ID ou URL
        seen = set()
        unique_documents = []
        for doc in documents:
            identifier = doc.celex_id or str(doc.url)
            if identifier not in seen:
                seen.add(identifier)
                unique_documents.append(doc)
        
        logger.info(
            "scraping_completed",
            total_found=len(unique_documents),
            source_id=source_id
        )
        
        return ScrapeResult(
            source_id=source_id,
            source_url=url,
            scraped_at=datetime.utcnow(),
            documents=unique_documents,
            total_found=len(unique_documents),
            status="success"
        )
        
    except httpx.HTTPError as e:
        logger.error("scraping_http_error", error=str(e), url=url)
        return ScrapeResult(
            source_id=source_id,
            source_url=url,
            scraped_at=datetime.utcnow(),
            documents=[],
            total_found=0,
            status="error",
            error=f"HTTP Error: {str(e)}"
        )
    
    except Exception as e:
        logger.error("scraping_unexpected_error", error=str(e), url=url, exc_info=True)
        return ScrapeResult(
            source_id=source_id,
            source_url=url,
            scraped_at=datetime.utcnow(),
            documents=[],
            total_found=0,
            status="error",
            error=f"Unexpected error: {str(e)}"
        )


def scrape_cbam_sync(url: str, source_id: str = "cbam-legislation") -> ScrapeResult:
    """Version synchrone du scraper (pour compatibilité)."""
    import asyncio
    return asyncio.run(scrape_cbam_page(url, source_id))


# Pour tester le module directement
if __name__ == "__main__":
    import asyncio
    from src.config import settings
    
    # URL CBAM
    url = "https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism/cbam-legislation-and-guidance_en"
    
    # Exécuter le scraping
    result = asyncio.run(scrape_cbam_page(url))
    
    print(f"\n✅ Scraping terminé: {result.total_found} documents trouvés")
    print(f"Status: {result.status}")
    
    if result.documents:
        print("\n📄 Premiers documents:")
        for i, doc in enumerate(result.documents[:5], 1):
            print(f"\n{i}. {doc.title}")
            print(f"   CELEX: {doc.celex_id}")
            print(f"   Type: {doc.document_type}")
            print(f"   URL: {doc.url}")