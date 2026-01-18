# tests/agent_1a/test_agent_1a.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.agent_1a.agent import run_agent_1a_eurlex_scenario_2, create_agent_1a


@pytest.mark.asyncio
async def test_run_agent_1a_eurlex_scenario_2_success():
    """Teste l'exécution réussie de l'Agent 1A Scénario 2."""
    with patch("src.agent_1a.agent.search_eurlex") as mock_search:
        with patch("src.storage.database.get_session") as mock_session:
            with patch("src.storage.repositories.DocumentRepository") as mock_repo_class:
                # Mock de la recherche EUR-Lex
                mock_search_result = MagicMock()
                mock_search_result.status = "success"
                mock_search_result.documents = [
                    MagicMock(
                        url="http://example.com/doc1.pdf",
                        pdf_url="http://example.com/doc1.pdf",
                        title="Doc 1",
                        celex_number="32023R0956",
                        metadata={"remote_hash": "hash123"}
                     )
                ]
                mock_search.return_value = mock_search_result
                
                # Mock du repository
                mock_repo = MagicMock()
                mock_repo.find_by_url.return_value = None  # Document n'existe pas
                mock_repo_class.return_value = mock_repo
                
                result = await run_agent_1a_eurlex_scenario_2(keyword="CBAM", max_documents=5)
                
                assert result is not None
                assert mock_search.called


@pytest.mark.asyncio
async def test_run_agent_1a_eurlex_scenario_2_search_error():
    """Teste la gestion d'une erreur lors de la recherche EUR-Lex."""
    with patch("src.agent_1a.agent.search_eurlex") as mock_search:
        mock_search_result = MagicMock()
        mock_search_result.status = "error"
        mock_search_result.error = "Search failed"
        mock_search.return_value = mock_search_result
        
        result = await run_agent_1a_eurlex_scenario_2(keyword="CBAM")
        
        assert result["status"] == "error"
        assert "search failed" in result["error"].lower()


@pytest.mark.asyncio
async def test_run_agent_1a_eurlex_scenario_2_no_documents():
    """Teste le cas où aucun document n'est trouvé."""
    with patch("src.agent_1a.agent.search_eurlex") as mock_search:
        mock_search_result = MagicMock()
        mock_search_result.status = "success"
        mock_search_result.documents = []
        mock_search.return_value = mock_search_result
        
        with patch("src.storage.database.get_session"):
            with patch("src.storage.repositories.DocumentRepository"):
                result = await run_agent_1a_eurlex_scenario_2(keyword="CBAM")
                
                assert result is not None


def test_create_agent_1a():
    """Teste la création de l'Agent 1A."""
    with patch("src.agent_1a.agent.ChatAnthropic"):
        with patch("src.agent_1a.agent.get_agent_1a_tools") as mock_tools:
            with patch("src.agent_1a.agent.create_react_agent") as mock_create:
                mock_tools.return_value = []
                mock_agent = MagicMock()
                mock_create.return_value = mock_agent
                
                agent = create_agent_1a()
                
                assert agent is not None
                assert mock_tools.called
                assert mock_create.called
