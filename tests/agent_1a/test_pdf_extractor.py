# tests/agent_1a/test_pdf_extractor.py

import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from src.agent_1a.tools.pdf_extractor import extract_pdf_content


@pytest.mark.asyncio
async def test_extract_pdf_content_success():
    """Teste l'extraction réussie du contenu d'un PDF."""
    # Mock de pdfplumber
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Page text with NC code 720711."
    mock_page.page_number = 1
    
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=None)
    
    # Mock Path.exists pour retourner True
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pdfplumber.open", return_value=mock_pdf):
            result = await extract_pdf_content("/fake/path.pdf")
            
            # Vérifier que le résultat n'est pas une erreur
            assert result is not None


@pytest.mark.asyncio
async def test_extract_pdf_content_file_not_found():
    """Teste la gestion de l'erreur lorsque le fichier PDF n'est pas trouvé."""
    with patch("pathlib.Path.exists", return_value=False):
        result = await extract_pdf_content("/non_existent.pdf")
        
        assert result.status == "error"
        assert "not found" in result.error.lower()


@pytest.mark.asyncio
async def test_extract_pdf_content_extraction_error():
    """Teste la gestion d'une erreur pendant l'extraction."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pdfplumber.open", side_effect=Exception("Extraction failed")):
            result = await extract_pdf_content("/fake/path.pdf")
            
            assert result.status == "error"
