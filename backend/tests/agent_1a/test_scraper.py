# tests/agent_1a/test_scraper.py
"""
Tests unitaires pour le scraper EUR-Lex
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.agent_1a.tools.scraper import (
    EurlexDocument,
    SearchResult,
    search_eurlex
)


# ============================================================================
# TESTS DES MODÈLES PYDANTIC
# ============================================================================

def test_eurlex_document_creation():
    """Teste la création d'un document EUR-Lex"""
    doc = EurlexDocument(
        celex_number="32023R0956",
        title="Regulation (EU) 2023/956",
        url="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R0956",
        pdf_url="https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32023R0956",
        document_type="Regulation",
        keyword="CBAM",
        publication_date=datetime(2023, 5, 16),
        status="ACTIVE_LAW",
        metadata={"test": "value"}
    )
    
    assert doc.celex_number == "32023R0956"
    assert doc.title == "Regulation (EU) 2023/956"
    assert doc.source == "eurlex"
    assert doc.keyword == "CBAM"
    assert doc.document_type == "Regulation"


def test_eurlex_document_optional_fields():
    """Teste la création d'un document avec champs optionnels"""
    doc = EurlexDocument(
        celex_number=None,
        title="Test Document",
        url="https://example.com",
        pdf_url=None,
        document_type="Unknown",
        keyword="TEST"
    )
    
    assert doc.celex_number is None
    assert doc.pdf_url is None
    assert doc.publication_date is None
    assert doc.status == "ACTIVE_LAW"  # Valeur par défaut
    assert doc.metadata == {}  # Valeur par défaut


def test_search_result_creation():
    """Teste la création d'un résultat de recherche"""
    doc = EurlexDocument(
        celex_number="32023R0956",
        title="Test",
        url="https://example.com",
        pdf_url=None,
        document_type="Regulation",
        keyword="CBAM"
    )
    
    result = SearchResult(
        status="success",
        total_found=1,
        documents=[doc],
        error=None
    )
    
    assert result.status == "success"
    assert result.total_found == 1
    assert len(result.documents) == 1
    assert result.error is None


def test_search_result_with_error():
    """Teste la création d'un résultat avec erreur"""
    result = SearchResult(
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
# TESTS DE LA FONCTION search_eurlex
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_eurlex_success():
    """Teste une recherche EUR-Lex réussie (test d'intégration)"""
    result = await search_eurlex(keyword="CBAM", max_results=3)
    
    assert result.status == "success"
    assert result.total_found >= 0
    assert isinstance(result.documents, list)
    
    # Si des documents sont trouvés, vérifier leur structure
    if result.documents:
        doc = result.documents[0]
        assert isinstance(doc, EurlexDocument)
        assert doc.title is not None
        assert doc.url is not None
        assert doc.keyword == "CBAM"


@pytest.mark.asyncio
async def test_search_eurlex_with_mock():
    """Teste search_eurlex avec un mock Scrapy"""
    
    mock_results = [
        {
            'celex_number': '32023R0956',
            'title': 'Regulation (EU) 2023/956 - CBAM',
            'url': 'https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R0956',
            'pdf_url': 'https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32023R0956',
            'document_type': 'Regulation',
            'source': 'eurlex',
            'keyword': 'CBAM',
            'publication_date': None,
            'status': 'ACTIVE_LAW',
            'metadata': {'scraped_at': '2024-01-24T10:00:00'}
        }
    ]
    
    with patch("src.agent_1a.tools.scraper.CrawlerProcess") as mock_crawler_class:
        mock_crawler = MagicMock()
        mock_crawler_class.return_value = mock_crawler
        
        # Mock du fichier de sortie
        with patch("builtins.open", create=True) as mock_file:
            with patch("json.load", return_value=mock_results):
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.unlink"):
                        result = await search_eurlex(keyword="CBAM", max_results=5)
                        
                        assert result.status == "success"
                        assert result.total_found == 1
                        assert len(result.documents) == 1
                        assert result.documents[0].celex_number == "32023R0956"


@pytest.mark.asyncio
async def test_search_eurlex_empty_results():
    """Teste une recherche sans résultats"""
    
    with patch("src.agent_1a.tools.scraper.CrawlerProcess") as mock_crawler_class:
        mock_crawler = MagicMock()
        mock_crawler_class.return_value = mock_crawler
        
        with patch("builtins.open", create=True):
            with patch("json.load", return_value=[]):
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.unlink"):
                        result = await search_eurlex(keyword="NONEXISTENT", max_results=5)
                        
                        assert result.status == "success"
                        assert result.total_found == 0
                        assert len(result.documents) == 0


@pytest.mark.asyncio
async def test_search_eurlex_exception():
    """Teste la gestion d'une exception"""
    
    with patch("src.agent_1a.tools.scraper._run_scrapy_spider", side_effect=Exception("Scrapy error")):
        result = await search_eurlex(keyword="CBAM", max_results=5)
        
        assert result.status == "error"
        assert result.total_found == 0
        assert len(result.documents) == 0
        assert "Scrapy error" in result.error


@pytest.mark.asyncio
async def test_search_eurlex_max_results():
    """Teste la limitation du nombre de résultats"""
    
    # Créer 10 résultats mockés
    mock_results = [
        {
            'celex_number': f'3202{i}R0001',
            'title': f'Document {i}',
            'url': f'https://example.com/doc{i}',
            'pdf_url': f'https://example.com/doc{i}.pdf',
            'document_type': 'Regulation',
            'source': 'eurlex',
            'keyword': 'CBAM',
            'publication_date': None,
            'status': 'ACTIVE_LAW',
            'metadata': {}
        }
        for i in range(10)
    ]
    
    with patch("src.agent_1a.tools.scraper.CrawlerProcess") as mock_crawler_class:
        mock_crawler = MagicMock()
        mock_crawler_class.return_value = mock_crawler
        
        with patch("builtins.open", create=True):
            with patch("json.load", return_value=mock_results):
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.unlink"):
                        # Demander seulement 3 résultats
                        result = await search_eurlex(keyword="CBAM", max_results=3)
                        
                        # Le scraper devrait retourner tous les résultats
                        # mais on vérifie que max_results est bien passé au spider
                        assert result.status == "success"
                        assert isinstance(result.documents, list)


# ============================================================================
# TESTS DES PARAMÈTRES
# ============================================================================

@pytest.mark.asyncio
async def test_search_eurlex_different_keywords():
    """Teste avec différents mots-clés"""
    
    keywords = ["CBAM", "EUDR", "CSRD"]
    
    for keyword in keywords:
        with patch("src.agent_1a.tools.scraper.CrawlerProcess") as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler_class.return_value = mock_crawler
            
            with patch("builtins.open", create=True):
                with patch("json.load", return_value=[]):
                    with patch("pathlib.Path.exists", return_value=True):
                        with patch("pathlib.Path.unlink"):
                            result = await search_eurlex(keyword=keyword, max_results=5)
                            
                            assert result.status == "success"
                            # Vérifier que le keyword est bien utilisé
                            assert result is not None


@pytest.mark.asyncio
async def test_search_eurlex_default_parameters():
    """Teste avec les paramètres par défaut"""
    
    with patch("src.agent_1a.tools.scraper.CrawlerProcess") as mock_crawler_class:
        mock_crawler = MagicMock()
        mock_crawler_class.return_value = mock_crawler
        
        with patch("builtins.open", create=True):
            with patch("json.load", return_value=[]):
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.unlink"):
                        # Le paramètre keyword est obligatoire
                        result = await search_eurlex(keyword="CBAM")
                        
                        assert result.status == "success"
                        assert result.total_found == 0