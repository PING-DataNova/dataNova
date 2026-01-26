# src/agent_1a/tools/scraper.py

import scrapy
from scrapy.crawler import CrawlerProcess
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import re
from urllib.parse import quote
from pydantic import BaseModel
import json
import tempfile
import subprocess
import sys

import structlog

logger = structlog.get_logger()

# ========================================
# MODÈLES PYDANTIC
# ========================================

class EurlexDocument(BaseModel):
    """Modèle pour un document EUR-Lex"""
    celex_number: Optional[str]
    title: str
    url: str
    pdf_url: Optional[str]
    document_type: str
    source: str = "eurlex"
    keyword: str
    publication_date: Optional[datetime] = None
    status: str = "ACTIVE_LAW"
    metadata: Dict = {}

class SearchResult(BaseModel):
    """Modèle pour le résultat de recherche"""
    status: str
    total_found: int
    documents: List[EurlexDocument]
    error: Optional[str] = None

# ========================================
# SPIDER SCRAPY
# ========================================

class EurlexSpider(scrapy.Spider):
    """Spider Scrapy pour EUR-Lex"""
    name = 'eurlex'
    
    def __init__(self, keyword: str, max_results: int = 10, output_file: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyword = keyword
        self.max_results = max_results
        self.output_file = output_file
        self.results = []
        
    def start_requests(self):
        url = f"https://eur-lex.europa.eu/search.html?text={quote(self.keyword)}&type=quick&lang=en"
        yield scrapy.Request(url, callback=self.parse)
    
    def parse(self, response):
        # Extraire les résultats
        result_links = response.css('a[id^="cellar_"]')
        
        for i, link in enumerate(result_links):
            if i >= self.max_results:
                break
                
            title = link.css('::text').get()
            url = link.css('::attr(href)').get()
            
            if not title or not url:
                continue
            
            # Extraire CELEX
            celex = self._extract_celex(url)
            
            # Construire résultat
            result = {
                'celex_number': celex,
                'title': title.strip(),
                'url': response.urljoin(url),
                'pdf_url': f"https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:{celex}" if celex else None,
                'document_type': self._extract_type(title),
                'source': 'eurlex',
                'keyword': self.keyword,
                'publication_date': None,
                'status': 'ACTIVE_LAW',
                'metadata': {
                    'scraped_at': datetime.now().isoformat()
                }
            }
            
            self.results.append(result)
            yield result
    
    def _extract_celex(self, url):
        if 'CELEX:' in url:
            match = re.search(r'CELEX:([A-Z0-9]+)', url)
            if match:
                return match.group(1)
        return None
    
    def _extract_type(self, title):
        if 'Regulation' in title:
            return 'REGULATION'
        elif 'Directive' in title:
            return 'DIRECTIVE'
        elif 'Decision' in title:
            return 'DECISION'
        return 'OTHER'
    
    def closed(self, reason):
        """Appelé quand le spider se ferme - sauvegarder les résultats"""
        if self.output_file:
            with open(self.output_file, 'w') as f:
                json.dump(self.results, f)

# ========================================
# FONCTION PRINCIPALE (API publique)
# ========================================

async def search_eurlex(keyword: str, max_results: int = 10) -> SearchResult:
    """
    Rechercher des documents EUR-Lex
    
    Args:
        keyword: Mot-clé de recherche (ex: "CBAM", "EUDR", "CSRD")
        max_results: Nombre maximum de résultats à retourner
        
    Returns:
        SearchResult: Objet contenant le statut et la liste des documents
    """
    logger.info("eurlex_search_started", keyword=keyword, max_results=max_results)
    
    try:
        results = await _run_scrapy_spider(keyword, max_results)
        
        # Convertir en objets Pydantic
        documents = [EurlexDocument(**doc) for doc in results]
        
        logger.info("eurlex_search_completed", count=len(documents))
        
        return SearchResult(
            status="success",
            total_found=len(documents),
            documents=documents
        )
        
    except Exception as e:
        logger.error("eurlex_search_failed", error=str(e))
        return SearchResult(
            status="error",
            total_found=0,
            documents=[],
            error=str(e)
        )

# ========================================
# FONCTION INTERNE (exécution Scrapy)
# ========================================

async def _run_scrapy_spider(keyword: str, max_results: int) -> List[Dict]:
    """
    Exécuter le spider Scrapy dans un subprocess séparé
    """
    # Créer un fichier temporaire pour les résultats
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_file = f.name
    
    # Créer un script Python temporaire pour exécuter le spider
    spider_script = f"""
import sys
import scrapy
from scrapy.crawler import CrawlerProcess
from urllib.parse import quote
import json
import re
from datetime import datetime

class EurlexSpider(scrapy.Spider):
    name = 'eurlex'
    
    def __init__(self, keyword, max_results, output_file, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyword = keyword
        self.max_results = int(max_results)
        self.output_file = output_file
        self.results = []
        
    def start_requests(self):
        url = f"https://eur-lex.europa.eu/search.html?text={{quote(self.keyword)}}&type=quick&lang=en"
        yield scrapy.Request(url, callback=self.parse)
    
    def parse(self, response):
        result_links = response.css('a[id^="cellar_"]')
        
        for i, link in enumerate(result_links):
            if i >= self.max_results:
                break
                
            title = link.css('::text').get()
            url = link.css('::attr(href)').get()
            
            if not title or not url:
                continue
            
            celex = self._extract_celex(url)
            
            result = {{
                'celex_number': celex,
                'title': title.strip(),
                'url': response.urljoin(url),
                'pdf_url': f"https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:{{celex}}" if celex else None,
                'document_type': self._extract_type(title),
                'source': 'eurlex',
                'keyword': self.keyword,
                'publication_date': None,
                'status': 'ACTIVE_LAW',
                'metadata': {{
                    'scraped_at': datetime.now().isoformat()
                }}
            }}
            
            self.results.append(result)
            yield result
    
    def _extract_celex(self, url):
        if 'CELEX:' in url:
            match = re.search(r'CELEX:([A-Z0-9]+)', url)
            if match:
                return match.group(1)
        return None
    
    def _extract_type(self, title):
        if 'Regulation' in title:
            return 'REGULATION'
        elif 'Directive' in title:
            return 'DIRECTIVE'
        elif 'Decision' in title:
            return 'DECISION'
        return 'OTHER'
    
    def closed(self, reason):
        with open(self.output_file, 'w') as f:
            json.dump(self.results, f)

if __name__ == '__main__':
    keyword = sys.argv[1]
    max_results = int(sys.argv[2])
    output_file = sys.argv[3]
    
    process = CrawlerProcess(settings={{
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'RETRY_TIMES': 3,
        'LOG_LEVEL': 'ERROR',
        'ROBOTSTXT_OBEY': False,
        'COOKIES_ENABLED': True,
        'DOWNLOADER_MIDDLEWARES': {{
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
        }}
    }})
    
    process.crawl(EurlexSpider, keyword=keyword, max_results=max_results, output_file=output_file)
    process.start()
"""
    
    # Sauvegarder le script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        script_file = f.name
        f.write(spider_script)
    
    try:
        # Exécuter le script dans un subprocess
        process = await asyncio.create_subprocess_exec(
            sys.executable, script_file, keyword, str(max_results), output_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error("spider_execution_failed", stderr=stderr.decode())
            return []
        
        # Lire les résultats
        try:
            with open(output_file, 'r') as f:
                results = json.load(f)
            return results
        except Exception as e:
            logger.error("results_loading_failed", error=str(e))
            return []
            
    finally:
        # Nettoyer les fichiers temporaires
        import os
        try:
            os.unlink(script_file)
            os.unlink(output_file)
        except:
            pass
