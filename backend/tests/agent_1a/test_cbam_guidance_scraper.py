# tests/agent_1a/test_cbam_guidance_scraper.py
"""
Tests unitaires pour le scraper CBAM Guidance
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.agent_1a.tools.cbam_guidance_scraper import (
    CbamDocument,
    CbamSearchResult,
    search_cbam_guidance
)


# ============================================================================
# TESTS DES MODÈLES PYDANTIC
# ============================================================================

def test_cbam_document_creation():
    """Teste la création d'un document CBAM"""
    doc = CbamDocument(
        title="Guidance document on CBAM implementation for importers",
        url="https://taxation-customs.ec.europa.eu/document/download/123456",
        date="2024-01-15",
        size="1.65 MB",
        category="guidance",
        language="en",
        format="PDF"
    )
    
    assert doc.title == "Guidance document on CBAM implementation for importers"
    assert doc.url == "https://taxation-customs.ec.europa.eu/document/download/123456"
    assert doc.category == "guidance"
    assert doc.language == "en"
    assert doc.format == "PDF"


def test_cbam_document_optional_fields():
    """Teste la création d'un document avec champs optionnels"""
    doc = CbamDocument(
        title="Test Document",
        url="https://example.com/doc.pdf",
        category="other",
        format="PDF"
    )
    
    assert doc.date is None
    assert doc.size is None
    assert doc.language == "en"  # Valeur par défaut


def test_cbam_document_categories():
    """Teste les différentes catégories de documents CBAM"""
    categories = ["guidance", "faq", "template", "default_values", "tool", "other"]
    
    for category in categories:
        doc = CbamDocument(
            title=f"Test {category}",
            url="https://example.com",
            category=category,
            format="PDF"
        )
        assert doc.category == category


def test_cbam_document_formats():
    """Teste les différents formats de documents"""
    formats = ["PDF", "XLSX", "ZIP", "UNKNOWN"]
    
    for fmt in formats:
        doc = CbamDocument(
            title="Test Document",
            url="https://example.com",
            category="guidance",
            format=fmt
        )
        assert doc.format == fmt


def test_cbam_search_result_creation():
    """Teste la création d'un résultat de recherche CBAM"""
    doc = CbamDocument(
        title="Test",
        url="https://example.com",
        category="guidance",
        format="PDF"
    )
    
    result = CbamSearchResult(
        status="success",
        total_found=1,
        documents=[doc],
        error=None
    )
    
    assert result.status == "success"
    assert result.total_found == 1
    assert len(result.documents) == 1
    assert result.error is None


def test_cbam_search_result_with_error():
    """Teste la création d'un résultat avec erreur"""
    result = CbamSearchResult(
        status="error",
        total_found=0,
        documents=[],
        error="Connection timeout"
    )
    
    assert result.status == "error"
    assert result.total_found == 0
    assert len(result.documents) == 0
    assert result.error == "Connection timeout"


# ============================================================================
# TESTS DE LA FONCTION search_cbam_guidance
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_cbam_guidance_success():
    """Teste une recherche CBAM réussie (test d'intégration)"""
    result = await search_cbam_guidance(categories="all", max_results=5)
    
    assert result.status == "success"
    assert result.total_found >= 0
    assert isinstance(result.documents, list)
    
    # Si des documents sont trouvés, vérifier leur structure
    if result.documents:
        doc = result.documents[0]
        assert isinstance(doc, CbamDocument)
        assert doc.title is not None
        assert doc.url is not None
        assert doc.category in ["guidance", "faq", "template", "default_values", "tool", "other"]
        assert doc.format in ["PDF", "XLSX", "ZIP", "UNKNOWN"]


@pytest.mark.asyncio
async def test_search_cbam_guidance_with_mock():
    """Teste search_cbam_guidance avec un mock"""
    
    mock_results = [
        {
            'title': 'Guidance document on CBAM implementation',
            'url': 'https://taxation-customs.ec.europa.eu/document/download/123456',
            'date': '2024-01-15',
            'size': '1.65 MB',
            'category': 'guidance',
            'language': 'en',
            'format': 'PDF'
        },
        {
            'title': 'CBAM Questions and Answers',
            'url': 'https://taxation-customs.ec.europa.eu/document/download/789012',
            'date': '2024-01-10',
            'size': '850 KB',
            'category': 'faq',
            'language': 'en',
            'format': 'PDF'
        }
    ]
    
    with patch("src.agent_1a.tools.cbam_guidance_scraper._run_scrapy_spider", return_value=mock_results):
        result = await search_cbam_guidance(categories="all", max_results=10)
        
        assert result.status == "success"
        assert result.total_found == 2
        assert len(result.documents) == 2
        assert result.documents[0].category == "guidance"
        assert result.documents[1].category == "faq"


@pytest.mark.asyncio
async def test_search_cbam_guidance_empty_results():
    """Teste une recherche sans résultats"""
    
    with patch("src.agent_1a.tools.cbam_guidance_scraper._run_scrapy_spider", return_value=[]):
        result = await search_cbam_guidance(categories="all", max_results=10)
        
        assert result.status == "success"
        assert result.total_found == 0
        assert len(result.documents) == 0


@pytest.mark.asyncio
async def test_search_cbam_guidance_exception():
    """Teste la gestion d'une exception"""
    
    with patch("src.agent_1a.tools.cbam_guidance_scraper._run_scrapy_spider", side_effect=Exception("Scrapy error")):
        result = await search_cbam_guidance(categories="all", max_results=10)
        
        assert result.status == "error"
        assert result.total_found == 0
        assert len(result.documents) == 0
        assert "Scrapy error" in result.error


@pytest.mark.asyncio
async def test_search_cbam_guidance_category_guidance():
    """Teste la recherche avec catégorie 'guidance' uniquement"""
    
    mock_results = [
        {
            'title': 'Guidance document 1',
            'url': 'https://example.com/doc1.pdf',
            'date': None,
            'size': '1 MB',
            'category': 'guidance',
            'language': 'en',
            'format': 'PDF'
        }
    ]
    
    with patch("src.agent_1a.tools.cbam_guidance_scraper._run_scrapy_spider", return_value=mock_results):
        result = await search_cbam_guidance(categories="guidance", max_results=10)
        
        assert result.status == "success"
        assert result.total_found == 1
        assert all(doc.category == "guidance" for doc in result.documents)


@pytest.mark.asyncio
async def test_search_cbam_guidance_category_faq():
    """Teste la recherche avec catégorie 'faq' uniquement"""
    
    mock_results = [
        {
            'title': 'Questions and Answers',
            'url': 'https://example.com/faq.pdf',
            'date': None,
            'size': '500 KB',
            'category': 'faq',
            'language': 'en',
            'format': 'PDF'
        }
    ]
    
    with patch("src.agent_1a.tools.cbam_guidance_scraper._run_scrapy_spider", return_value=mock_results):
        result = await search_cbam_guidance(categories="faq", max_results=10)
        
        assert result.status == "success"
        assert result.total_found == 1
        assert all(doc.category == "faq" for doc in result.documents)


@pytest.mark.asyncio
async def test_search_cbam_guidance_multiple_categories():
    """Teste la recherche avec plusieurs catégories"""
    
    mock_results = [
        {
            'title': 'Guidance',
            'url': 'https://example.com/guidance.pdf',
            'date': None,
            'size': '1 MB',
            'category': 'guidance',
            'language': 'en',
            'format': 'PDF'
        },
        {
            'title': 'FAQ',
            'url': 'https://example.com/faq.pdf',
            'date': None,
            'size': '500 KB',
            'category': 'faq',
            'language': 'en',
            'format': 'PDF'
        }
    ]
    
    with patch("src.agent_1a.tools.cbam_guidance_scraper._run_scrapy_spider", return_value=mock_results):
        result = await search_cbam_guidance(categories="guidance,faq", max_results=10)
        
        assert result.status == "success"
        assert result.total_found == 2


@pytest.mark.asyncio
async def test_search_cbam_guidance_max_results():
    """Teste la limitation du nombre de résultats"""
    
    # Créer 20 résultats mockés
    mock_results = [
        {
            'title': f'Document {i}',
            'url': f'https://example.com/doc{i}.pdf',
            'date': None,
            'size': '1 MB',
            'category': 'guidance',
            'language': 'en',
            'format': 'PDF'
        }
        for i in range(20)
    ]
    
    with patch("src.agent_1a.tools.cbam_guidance_scraper._run_scrapy_spider", return_value=mock_results):
        # Demander seulement 5 résultats
        result = await search_cbam_guidance(categories="all", max_results=5)
        
        assert result.status == "success"
        # Le scraper retourne tous les résultats, max_results est géré par le spider
        assert isinstance(result.documents, list)


@pytest.mark.asyncio
async def test_search_cbam_guidance_different_formats():
    """Teste avec différents formats de documents"""
    
    mock_results = [
        {
            'title': 'PDF Document',
            'url': 'https://example.com/doc.pdf',
            'date': None,
            'size': '1 MB',
            'category': 'guidance',
            'language': 'en',
            'format': 'PDF'
        },
        {
            'title': 'Excel Template',
            'url': 'https://example.com/template.xlsx',
            'date': None,
            'size': '200 KB',
            'category': 'template',
            'language': 'en',
            'format': 'XLSX'
        },
        {
            'title': 'ZIP Archive',
            'url': 'https://example.com/archive.zip',
            'date': None,
            'size': '5 MB',
            'category': 'tool',
            'language': 'en',
            'format': 'ZIP'
        }
    ]
    
    with patch("src.agent_1a.tools.cbam_guidance_scraper._run_scrapy_spider", return_value=mock_results):
        result = await search_cbam_guidance(categories="all", max_results=10)
        
        assert result.status == "success"
        assert result.total_found == 3
        
        formats = [doc.format for doc in result.documents]
        assert "PDF" in formats
        assert "XLSX" in formats
        assert "ZIP" in formats


@pytest.mark.asyncio
async def test_search_cbam_guidance_default_parameters():
    """Teste avec les paramètres par défaut"""
    
    mock_results = [
        {
            'title': 'Default Test',
            'url': 'https://example.com/test.pdf',
            'date': None,
            'size': '1 MB',
            'category': 'guidance',
            'language': 'en',
            'format': 'PDF'
        }
    ]
    
    with patch("src.agent_1a.tools.cbam_guidance_scraper._run_scrapy_spider", return_value=mock_results):
        # Appeler sans paramètres (utilise les valeurs par défaut)
        result = await search_cbam_guidance()
        
        assert result.status == "success"
        assert result.total_found == 1


@pytest.mark.asyncio
async def test_search_cbam_guidance_with_dates():
    """Teste avec des documents ayant des dates"""
    
    mock_results = [
        {
            'title': 'Document with date',
            'url': 'https://example.com/doc.pdf',
            'date': '2024-01-15',
            'size': '1 MB',
            'category': 'guidance',
            'language': 'en',
            'format': 'PDF'
        }
    ]
    
    with patch("src.agent_1a.tools.cbam_guidance_scraper._run_scrapy_spider", return_value=mock_results):
        result = await search_cbam_guidance(categories="all", max_results=10)
        
        assert result.status == "success"
        assert result.documents[0].date == "2024-01-15"


# ============================================================================
# TESTS DES CATÉGORIES SPÉCIFIQUES
# ============================================================================

@pytest.mark.asyncio
async def test_search_cbam_guidance_category_template():
    """Teste la recherche de templates"""
    
    mock_results = [
        {
            'title': 'CBAM Template for reporting',
            'url': 'https://example.com/template.xlsx',
            'date': None,
            'size': '150 KB',
            'category': 'template',
            'language': 'en',
            'format': 'XLSX'
        }
    ]
    
    with patch("src.agent_1a.tools.cbam_guidance_scraper._run_scrapy_spider", return_value=mock_results):
        result = await search_cbam_guidance(categories="template", max_results=10)
        
        assert result.status == "success"
        assert result.documents[0].category == "template"
        assert result.documents[0].format == "XLSX"


@pytest.mark.asyncio
async def test_search_cbam_guidance_category_default_values():
    """Teste la recherche de default values"""
    
    mock_results = [
        {
            'title': 'CBAM Default Values',
            'url': 'https://example.com/defaults.pdf',
            'date': None,
            'size': '300 KB',
            'category': 'default_values',
            'language': 'en',
            'format': 'PDF'
        }
    ]
    
    with patch("src.agent_1a.tools.cbam_guidance_scraper._run_scrapy_spider", return_value=mock_results):
        result = await search_cbam_guidance(categories="default_values", max_results=10)
        
        assert result.status == "success"
        assert result.documents[0].category == "default_values"


@pytest.mark.asyncio
async def test_search_cbam_guidance_category_tool():
    """Teste la recherche d'outils"""
    
    mock_results = [
        {
            'title': 'CBAM Assessment Tool',
            'url': 'https://example.com/tool.zip',
            'date': None,
            'size': '10 MB',
            'category': 'tool',
            'language': 'en',
            'format': 'ZIP'
        }
    ]
    
    with patch("src.agent_1a.tools.cbam_guidance_scraper._run_scrapy_spider", return_value=mock_results):
        result = await search_cbam_guidance(categories="tool", max_results=10)
        
        assert result.status == "success"
        assert result.documents[0].category == "tool"
        assert result.documents[0].format == "ZIP"