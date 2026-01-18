# tests/agent_1b/test_semantic_analyzer.py

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import json

from src.agent_1b.tools.semantic_analyzer import analyze_document_relevance


@pytest.fixture
def mock_company_profile():
    """Fixture pour un profil d'entreprise de test."""
    return {
        "company_id": "GMG-001",
        "name": "Globex Manufacturing Group",
        "description": "Un conglomérat multinational.",
        "keywords": ["acier", "aluminium", "produits chimiques"],
        "nc_codes": ["720711", "760110"],
        "monitored_regulations": ["CBAM", "REACH"]
    }


@pytest.mark.asyncio
async def test_analyze_document_relevance_relevant(mock_company_profile):
    """Teste l'analyse d'un document jugé pertinent."""
    content = "Ce document concerne les nouvelles régulations sur l'importation d'acier et d'aluminium."
    title = "Réglement sur l'acier et l'aluminium"
    nc_codes = ["720711", "760110"]
    
    # Mock de la réponse de l'API
    mock_response = MagicMock()
    response_dict = {
        "is_relevant": True,
        "confidence": 0.95,
        "matched_keywords": ["acier", "aluminium"],
        "matched_nc_codes": ["720711", "760110"],
        "summary": "Document sur l'acier",
        "reasoning": "Mentionne explicitement l'acier"
    }
    mock_response.content = json.dumps(response_dict)
    
    with patch("src.agent_1b.tools.semantic_analyzer.ChatAnthropic") as MockChatAnthropic:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        MockChatAnthropic.return_value = mock_llm
        
        result = await analyze_document_relevance(content, title, mock_company_profile, nc_codes)
        
        assert result.is_relevant is True
        assert result.confidence == 0.95


@pytest.mark.asyncio
async def test_analyze_document_relevance_empty_content(mock_company_profile):
    """Teste l'analyse avec un contenu vide."""
    result = await analyze_document_relevance("", "Title", mock_company_profile)
    
    assert result.is_relevant is False
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_analyze_document_relevance_api_error(mock_company_profile):
    """Teste la gestion d'une erreur de l'API."""
    content = "Test content"
    title = "Test Title"
    
    with patch("src.agent_1b.tools.semantic_analyzer.ChatAnthropic") as MockChatAnthropic:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("API Error")
        MockChatAnthropic.return_value = mock_llm
        
        result = await analyze_document_relevance(content, title, mock_company_profile)
        
        assert result.is_relevant is False
        assert result.confidence == 0.0
