# tests/agent_1a/test_pdf_extractor.py
"""
Tests unitaires pour l'extracteur PDF
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from src.agent_1a.tools.pdf_extractor import (
    NCCode,
    ExtractedContent,
    extract_pdf_content
)


# ============================================================================
# TESTS DES MODÈLES PYDANTIC
# ============================================================================

def test_nc_code_creation():
    """Teste la création d'un code NC"""
    nc_code = NCCode(
        code="7206",
        context="Iron and steel products",
        page=1,
        confidence=0.95
    )
    
    assert nc_code.code == "7206"
    assert nc_code.context == "Iron and steel products"
    assert nc_code.page == 1
    assert nc_code.confidence == 0.95


def test_nc_code_default_confidence():
    """Teste la valeur par défaut de confidence"""
    nc_code = NCCode(
        code="7206",
        context="Test",
        page=1
    )
    
    assert nc_code.confidence == 1.0  # Valeur par défaut


def test_extracted_content_creation():
    """Teste la création d'un contenu extrait"""
    nc_code = NCCode(code="7206", context="Test", page=1)
    
    content = ExtractedContent(
        file_path="data/documents/doc.pdf",
        text="Extracted text content",
        nc_codes=[nc_code],
        tables=[{"header": ["Col1", "Col2"], "rows": [["A", "B"]]}],
        metadata={"author": "Test"},
        page_count=10,
        status="success",
        error=None
    )
    
    assert content.file_path == "data/documents/doc.pdf"
    assert content.text == "Extracted text content"
    assert len(content.nc_codes) == 1
    assert len(content.tables) == 1
    assert content.page_count == 10
    assert content.status == "success"


def test_extracted_content_with_error():
    """Teste la création d'un contenu avec erreur"""
    content = ExtractedContent(
        file_path="data/documents/missing.pdf",
        text="",
        nc_codes=[],
        tables=[],
        metadata={},
        page_count=0,
        status="error",
        error="File not found"
    )
    
    assert content.status == "error"
    assert content.error == "File not found"
    assert content.page_count == 0


# ============================================================================
# TESTS DE extract_pdf_content
# ============================================================================

@pytest.mark.asyncio
async def test_extract_pdf_content_file_not_found():
    """Teste l'extraction d'un fichier inexistant"""
    
    with patch("pathlib.Path.exists", return_value=False):
        result = await extract_pdf_content("data/documents/missing.pdf")
        
        assert result.status == "error"
        assert "File not found" in result.error
        assert result.page_count == 0
        assert len(result.nc_codes) == 0


@pytest.mark.asyncio
async def test_extract_pdf_content_success():
    """Teste l'extraction réussie d'un PDF"""
    
    # Mock d'une page PDF
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "This document contains NC code 7206 for iron products."
    mock_page.extract_tables.return_value = [
        [["Header1", "Header2"], ["Value1", "Value2"]]
    ]
    
    # Mock du PDF
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page, mock_page]  # 2 pages
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock()
    
    mock_stat = MagicMock()
    mock_stat.st_size = 1024  # 1 KB
    
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.stat", return_value=mock_stat):
            with patch("pdfplumber.open", return_value=mock_pdf):
                result = await extract_pdf_content("data/documents/test.pdf")
                
                assert result.status == "success"
                assert result.page_count == 2
                assert "7206" in result.text
                assert len(result.nc_codes) > 0
                assert len(result.tables) > 0


@pytest.mark.asyncio
async def test_extract_pdf_content_no_nc_codes():
    """Teste l'extraction d'un PDF sans codes NC"""
    
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "This is a document without any NC codes."
    mock_page.extract_tables.return_value = []
    
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock()
    
    mock_stat = MagicMock()
    mock_stat.st_size = 1024
    
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.stat", return_value=mock_stat):
            with patch("pdfplumber.open", return_value=mock_pdf):
                result = await extract_pdf_content(
                    "data/documents/test.pdf",
                    extract_nc_codes=True
                )
                
                assert result.status == "success"
                assert len(result.nc_codes) == 0


@pytest.mark.asyncio
async def test_extract_pdf_content_skip_tables():
    """Teste l'extraction sans extraction de tableaux"""
    
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Test content"
    mock_page.extract_tables.return_value = [["Header"], ["Value"]]
    
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock()
    
    mock_stat = MagicMock()
    mock_stat.st_size = 1024
    
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.stat", return_value=mock_stat):
            with patch("pdfplumber.open", return_value=mock_pdf):
                result = await extract_pdf_content(
                    "data/documents/test.pdf",
                    extract_tables=False
                )
                
                assert result.status == "success"
                assert len(result.tables) == 0  # Pas de tableaux extraits


@pytest.mark.asyncio
async def test_extract_pdf_content_exception():
    """Teste la gestion d'une exception"""
    
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pdfplumber.open", side_effect=Exception("PDF corrupted")):
            result = await extract_pdf_content("data/documents/test.pdf")
            
            assert result.status == "error"
            assert "PDF corrupted" in result.error



@pytest.mark.asyncio
async def test_extract_pdf_content_empty_pages():
    """Teste l'extraction d'un PDF avec pages vides"""
    
    mock_page = MagicMock()
    mock_page.extract_text.return_value = None  # Page vide
    mock_page.extract_tables.return_value = []
    
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page, mock_page]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock()
    
    mock_stat = MagicMock()
    mock_stat.st_size = 1024
    
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.stat", return_value=mock_stat):
            with patch("pdfplumber.open", return_value=mock_pdf):
                result = await extract_pdf_content("data/documents/test.pdf")
                
                assert result.status == "success"
                assert result.page_count == 2
                assert result.text == ""  # Pas de texte extrait


@pytest.mark.asyncio
async def test_extract_pdf_content_metadata():
    """Teste l'extraction des métadonnées PDF"""
    
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Test content"
    mock_page.extract_tables.return_value = []
    
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.metadata = {
        'Author': 'Test Author',
        'Title': 'Test Document',
        'CreationDate': '2024-01-24'
    }
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock()
    
    mock_stat = MagicMock()
    mock_stat.st_size = 1024
    
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.stat", return_value=mock_stat):
            with patch("pdfplumber.open", return_value=mock_pdf):
                result = await extract_pdf_content("data/documents/test.pdf")
                
                assert result.status == "success"
                # Les métadonnées devraient être incluses
                assert 'pdf_metadata' in result.metadata or len(result.metadata) > 0


# ============================================================================
# TESTS D'INTÉGRATION
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_extract_pdf_content_real_file():
    """Teste l'extraction d'un vrai fichier PDF (test d'intégration)"""
    
    # Ce test nécessite un vrai fichier PDF
    # À adapter selon les fichiers de test disponibles
    
    test_file = "data/test_documents/sample.pdf"
    
    if Path(test_file).exists():
        result = await extract_pdf_content(test_file)
        
        assert result.status == "success"
        assert result.page_count > 0
        assert len(result.text) > 0
    else:
        pytest.skip(f"Test file {test_file} not found")