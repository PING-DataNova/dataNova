"""
Tests pour le module scraper.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.agent_1a.tools.scraper import scrape_cbam_page


@pytest.mark.asyncio
async def test_scrape_cbam_page_success():
    """Test du scraping réussi."""
    
    # Mock HTML response
    mock_html = """
    <html>
        <body>
            <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R0956">
                Regulation (EU) 2023/956 - CBAM
            </a>
            <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023L1234">
                Directive (EU) 2023/1234
            </a>
        </body>
    </html>
    """
    
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = await scrape_cbam_page("https://test.com")
        
        assert result.status == "success"
        assert result.total_found >= 2
        assert any(doc.celex_id == "32023R0956" for doc in result.documents)


@pytest.mark.asyncio
async def test_scrape_cbam_page_network_error():
    """Test de gestion d'erreur réseau."""
    
    with patch("httpx.AsyncClient.get", side_effect=Exception("Network error")):
        result = await scrape_cbam_page("https://test.com")
        
        assert result.status == "error"
        assert "error" in result.error.lower()
        assert result.total_found == 0