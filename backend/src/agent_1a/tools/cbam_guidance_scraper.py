"""
CBAM Guidance Documents Scraper

Récupère les documents Guidance, FAQs, Templates depuis le site officiel CBAM
URL: https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism/cbam-legislation-and-guidance_en

Utilise Scrapy pour le scraping robuste avec anti-blocage
"""

import asyncio
import subprocess
import json
import tempfile
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()

# ========================================
# MODÈLES PYDANTIC
# ========================================

class CbamDocument(BaseModel):
    """Modèle pour un document CBAM"""
    title: str
    url: str
    date: Optional[str] = None
    size: Optional[str] = None
    category: str  # guidance, faq, template, default_values, tool
    language: str = "en"
    format: str  # PDF, XLSX, ZIP

class CbamSearchResult(BaseModel):
    """Modèle pour le résultat de recherche CBAM"""
    status: str
    total_found: int
    documents: List[CbamDocument]
    error: Optional[str] = None

# ========================================
# SPIDER SCRAPY
# ========================================

CBAM_SPIDER_CODE = '''
import scrapy
import json
import re

class CbamGuidanceSpider(scrapy.Spider):
    name = 'cbam_guidance'
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 2,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'AUTOTHROTTLE_MAX_DELAY': 5,
        'LOG_LEVEL': 'INFO',
    }
    
    def __init__(self, categories='all', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.categories = categories.split(',') if categories != 'all' else ['all']
        self.start_urls = [
            'https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism/cbam-legislation-and-guidance_en'
        ]
        self.documents = []
    
    def parse(self, response):
        """Parse la page principale CBAM Legislation and Guidance"""
        
        # Extraire tous les liens de téléchargement (English uniquement)
        download_links = response.css('a[id^="ecl-file-"]')
        
        for link in download_links:
            # Ignorer les traductions (contiennent 'translation' dans l'ID)
            link_id = link.attrib.get('id', '')
            if 'translation' in link_id:
                continue
            
            url = response.urljoin(link.attrib.get('href', ''))
            
            # Extraire le titre (chercher dans le conteneur parent)
            title = ''
            container = link.xpath('ancestor::div[contains(@class, "ecl-file")]')
            if container:
                title_elem = container.xpath('.//div[contains(@class, "ecl-file__title")]//text()')
                if title_elem:
                    title = ' '.join(title_elem.getall()).strip()
            
            # Extraire la taille
            size = ''
            meta_elem = container.xpath('.//div[contains(@class, "ecl-file__meta")]//text()')
            if meta_elem:
                meta_text = ' '.join(meta_elem.getall())
                size_match = re.search(r'\\(([^)]+)\\)', meta_text)
                if size_match:
                    size = size_match.group(1)
            
            # Déterminer la catégorie
            category = self._determine_category(title, url)
            
            # Déterminer le format
            format_type = self._determine_format(url, size)
            
            # Filtrer par catégorie si nécessaire
            if 'all' not in self.categories and category not in self.categories:
                continue
            
            doc = {
                'title': title,
                'url': url,
                'date': None,  # Les dates ne sont pas dans le HTML, à extraire manuellement
                'size': size,
                'category': category,
                'language': 'en',
                'format': format_type
            }
            
            self.documents.append(doc)
            yield doc
    
    def _determine_category(self, title: str, url: str) -> str:
        """Détermine la catégorie du document"""
        title_lower = title.lower()
        
        if 'guidance' in title_lower:
            return 'guidance'
        elif 'question' in title_lower or 'q&a' in title_lower or 'q & a' in title_lower:
            return 'faq'
        elif 'template' in title_lower or 'example' in title_lower:
            return 'template'
        elif 'default value' in title_lower:
            return 'default_values'
        elif 'assessment tool' in title_lower:
            return 'tool'
        else:
            return 'other'
    
    def _determine_format(self, url: str, size: str) -> str:
        """Détermine le format du document"""
        if 'PDF' in size.upper() or url.endswith('.pdf'):
            return 'PDF'
        elif 'XLSX' in size.upper() or 'XLS' in size.upper() or url.endswith('.xlsx'):
            return 'XLSX'
        elif 'ZIP' in size.upper() or url.endswith('.zip'):
            return 'ZIP'
        else:
            return 'UNKNOWN'
    
    def closed(self, reason):
        """Callback appelé à la fin du scraping"""
        self.logger.info(f'Spider closed: {reason}. Total documents: {len(self.documents)}')
'''

# ========================================
# FONCTION PRINCIPALE
# ========================================

async def search_cbam_guidance(
    categories: str = 'all',
    max_results: int = 50
) -> CbamSearchResult:
    """
    Rechercher des documents CBAM Guidance
    
    Args:
        categories: Catégories à récupérer (all, guidance, faq, template, default_values, tool)
                   Peut être une liste séparée par des virgules: "guidance,faq"
        max_results: Nombre maximum de résultats à retourner
        
    Returns:
        CbamSearchResult: Objet contenant le statut et la liste des documents
    """
    logger.info("cbam_guidance_search_started", categories=categories, max_results=max_results)
    
    try:
        results = await _run_scrapy_spider(categories, max_results)
        
        # Convertir en objets Pydantic
        documents = [CbamDocument(**doc) for doc in results]
        
        logger.info("cbam_guidance_search_completed", count=len(documents))
        
        return CbamSearchResult(
            status="success",
            total_found=len(documents),
            documents=documents
        )
        
    except Exception as e:
        logger.error("cbam_guidance_search_failed", error=str(e))
        return CbamSearchResult(
            status="error",
            total_found=0,
            documents=[],
            error=str(e)
        )

# ========================================
# FONCTION INTERNE (exécution Scrapy)
# ========================================

async def _run_scrapy_spider(categories: str, max_results: int) -> List[Dict]:
    """
    Exécute le spider Scrapy dans un subprocess isolé
    
    Args:
        categories: Catégories à récupérer
        max_results: Nombre maximum de résultats
        
    Returns:
        Liste de dictionnaires contenant les documents
    """
    # Créer un fichier temporaire pour le spider
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as spider_file:
        spider_file.write(CBAM_SPIDER_CODE)
        spider_path = spider_file.name
    
    # Créer un fichier temporaire pour les résultats
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as output_file:
        output_path = output_file.name
    
    try:
        # Commande Scrapy
        cmd = [
            'scrapy', 'runspider', spider_path,
            '-o', output_path,
            '-a', f'categories={categories}',
            '--loglevel=INFO'
        ]
        
        # Exécuter Scrapy dans un subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Scrapy failed: {stderr.decode()}")
        
        # Lire les résultats
        with open(output_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Limiter le nombre de résultats
        return results[:max_results]
        
    finally:
        # Nettoyer les fichiers temporaires
        import os
        try:
            os.unlink(spider_path)
            os.unlink(output_path)
        except:
            pass

# ========================================
# FONCTION POUR LANGCHAIN TOOL
# ========================================

def search_cbam_guidance_sync(categories: str = 'all', max_results: int = 50) -> str:
    """
    Version synchrone pour LangChain Tool
    
    Args:
        categories: Catégories à récupérer (all, guidance, faq, template, default_values, tool)
        max_results: Nombre maximum de résultats
        
    Returns:
        JSON string avec les résultats
    """
    result = asyncio.run(search_cbam_guidance(categories, max_results))
    return json.dumps(result.model_dump(), indent=2)
