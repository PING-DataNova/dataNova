# tests/agent_1a/test_agent.py
"""
Tests unitaires pour l'Agent 1A - Pipeline combiné EUR-Lex + CBAM Guidance
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from datetime import datetime
from pathlib import Path

# Import de la fonction à tester
from src.agent_1a.agent import run_agent_1a_combined


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_eurlex_result():
    """Mock du résultat de recherche EUR-Lex"""
    mock_doc = MagicMock()
    mock_doc.celex_number = "32023R0956"
    mock_doc.title = "Regulation (EU) 2023/956 - CBAM"
    mock_doc.url = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R0956"
    mock_doc.pdf_url = "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32023R0956"
    mock_doc.document_type = "Regulation"
    mock_doc.source = "eurlex"
    mock_doc.keyword = "CBAM"
    mock_doc.publication_date = datetime(2023, 5, 16)
    mock_doc.status = "ACTIVE_LAW"
    mock_doc.metadata = {"remote_hash": "abc123"}
    
    mock_result = MagicMock()
    mock_result.status = "success"
    mock_result.total_found = 1
    mock_result.documents = [mock_doc]
    mock_result.error = None
    
    return mock_result


@pytest.fixture
def mock_cbam_result():
    """Mock du résultat de recherche CBAM Guidance"""
    mock_doc = MagicMock()
    mock_doc.title = "CBAM Guidance Document"
    mock_doc.url = "https://taxation-customs.ec.europa.eu/document/download/123456"
    mock_doc.date = "2024-01-15"
    mock_doc.size = "1.65 MB"
    mock_doc.category = "guidance"
    mock_doc.language = "en"
    mock_doc.format = "PDF"
    
    mock_result = MagicMock()
    mock_result.status = "success"
    mock_result.total_found = 1
    mock_result.documents = [mock_doc]
    mock_result.error = None
    
    return mock_result


@pytest.fixture
def mock_fetch_result():
    """Mock du résultat de téléchargement"""
    mock_doc = MagicMock()
    mock_doc.url = "https://example.com/doc.pdf"
    mock_doc.file_path = "data/documents/doc.pdf"
    mock_doc.hash_sha256 = "def456"
    mock_doc.file_size = 1024000
    mock_doc.content_type = "application/pdf"
    mock_doc.status = "downloaded"
    mock_doc.downloaded_at = datetime.now()
    mock_doc.metadata = {}
    
    mock_result = MagicMock()
    mock_result.url = "https://example.com/doc.pdf"
    mock_result.success = True
    mock_result.document = mock_doc
    mock_result.error = None
    
    return mock_result


@pytest.fixture
def mock_extracted_content():
    """Mock du contenu extrait d'un PDF"""
    mock_nc_code = MagicMock()
    mock_nc_code.code = "7206"
    mock_nc_code.context = "Iron and steel"
    mock_nc_code.page = 1
    mock_nc_code.confidence = 1.0
    
    mock_content = MagicMock()
    mock_content.file_path = "data/documents/doc.pdf"
    mock_content.text = "This is the extracted text content..."
    mock_content.nc_codes = [mock_nc_code]
    mock_content.tables = []
    mock_content.metadata = {}
    mock_content.page_count = 10
    mock_content.status = "success"
    mock_content.error = None
    
    return mock_content


# ============================================================================
# TESTS DU PIPELINE COMPLET
# ============================================================================

@pytest.mark.asyncio
async def test_run_agent_1a_combined_success(
    mock_eurlex_result,
    mock_cbam_result,
    mock_fetch_result,
    mock_extracted_content
):
    """Teste l'exécution réussie du pipeline complet"""
    
    with patch("src.agent_1a.agent.search_eurlex") as mock_search_eurlex:
        with patch("src.agent_1a.agent.search_cbam_guidance") as mock_search_cbam:
            with patch("src.agent_1a.agent.fetch_document") as mock_fetch:
                with patch("src.agent_1a.agent.extract_pdf_content") as mock_extract:
                    with patch("src.storage.database.get_session") as mock_get_session:
                        with patch("builtins.open", mock_open(read_data=b"fake pdf content")):
                            # Configuration des mocks
                            mock_search_eurlex.return_value = mock_eurlex_result
                            mock_search_cbam.return_value = mock_cbam_result
                            mock_fetch.return_value = mock_fetch_result
                            mock_extract.return_value = mock_extracted_content
                            
                            # Mock de la session et du repository
                            mock_session = MagicMock()
                            mock_repo = MagicMock()
                            mock_repo.find_by_url.return_value = None  # Pas de document existant
                            mock_repo.upsert_document.return_value = (MagicMock(id="doc123"), "created")
                            
                            mock_get_session.return_value = mock_session
                            mock_session.commit = MagicMock()
                            mock_session.rollback = MagicMock()
                            mock_session.close = MagicMock()
                            
                            with patch("src.storage.repositories.DocumentRepository", return_value=mock_repo):
                                # Exécution
                                result = await run_agent_1a_combined(
                                    keyword="CBAM",
                                    max_eurlex_documents=5,
                                    cbam_categories="all",
                                    max_cbam_documents=10
                                )
                                
                                # Vérifications
                                assert result is not None
                                assert result["status"] == "success"
                                assert result["keyword"] == "CBAM"
                                assert result["total_found"] == 2
                                assert result["documents_processed"] == 2
                                assert "sources" in result
                                assert "eurlex" in result["sources"]
                                assert "cbam_guidance" in result["sources"]


@pytest.mark.asyncio
async def test_run_agent_1a_combined_no_documents():
    """Teste le cas où aucun document n'est trouvé"""
    
    # Mock résultats vides
    mock_empty_eurlex = MagicMock()
    mock_empty_eurlex.status = "success"
    mock_empty_eurlex.documents = []
    
    mock_empty_cbam = MagicMock()
    mock_empty_cbam.status = "success"
    mock_empty_cbam.documents = []
    
    with patch("src.agent_1a.agent.search_eurlex", return_value=mock_empty_eurlex):
        with patch("src.agent_1a.agent.search_cbam_guidance", return_value=mock_empty_cbam):
            with patch("src.storage.database.get_session") as mock_get_session:
                mock_session = MagicMock()
                mock_repo = MagicMock()
                mock_get_session.return_value = mock_session
                
                with patch("src.storage.repositories.DocumentRepository", return_value=mock_repo):
                    result = await run_agent_1a_combined(keyword="NONEXISTENT")
                    
                    assert result["status"] == "success"
                    assert result["total_found"] == 0
                    assert result["documents_processed"] == 0


@pytest.mark.asyncio
async def test_run_agent_1a_combined_eurlex_error():
    """Teste la gestion d'une erreur EUR-Lex"""
    
    mock_error_eurlex = MagicMock()
    mock_error_eurlex.status = "error"
    mock_error_eurlex.error = "Connection timeout"
    mock_error_eurlex.documents = []
    
    mock_success_cbam = MagicMock()
    mock_success_cbam.status = "success"
    mock_success_cbam.documents = []
    
    with patch("src.agent_1a.agent.search_eurlex", return_value=mock_error_eurlex):
        with patch("src.agent_1a.agent.search_cbam_guidance", return_value=mock_success_cbam):
            with patch("src.storage.database.get_session") as mock_get_session:
                mock_session = MagicMock()
                mock_repo = MagicMock()
                mock_get_session.return_value = mock_session
                
                with patch("src.storage.repositories.DocumentRepository", return_value=mock_repo):
                    result = await run_agent_1a_combined(keyword="CBAM")
                    
                    # L'agent devrait continuer malgré l'erreur EUR-Lex
                    assert result["status"] == "success"
                    assert result["total_found"] == 0


@pytest.mark.asyncio
async def test_run_agent_1a_combined_download_error(mock_eurlex_result, mock_cbam_result):
    """Teste la gestion d'une erreur de téléchargement"""
    
    mock_fetch_error = MagicMock()
    mock_fetch_error.success = False
    mock_fetch_error.error = "Download failed"
    mock_fetch_error.document = None
    
    with patch("src.agent_1a.agent.search_eurlex", return_value=mock_eurlex_result):
        with patch("src.agent_1a.agent.search_cbam_guidance", return_value=mock_cbam_result):
            with patch("src.agent_1a.agent.fetch_document", return_value=mock_fetch_error):
                with patch("src.storage.database.get_session") as mock_get_session:
                    mock_session = MagicMock()
                    mock_repo = MagicMock()
                    mock_repo.find_by_url.return_value = None
                    mock_get_session.return_value = mock_session
                    
                    with patch("src.storage.repositories.DocumentRepository", return_value=mock_repo):
                        result = await run_agent_1a_combined(keyword="CBAM")
                        
                        assert result["status"] == "success"
                        assert result["download_errors"] == 2  # 2 documents, 2 erreurs


@pytest.mark.asyncio
async def test_run_agent_1a_combined_document_unchanged(mock_eurlex_result):
    """Teste le cas où un document existe déjà et est inchangé"""
    
    mock_empty_cbam = MagicMock()
    mock_empty_cbam.status = "success"
    mock_empty_cbam.documents = []
    
    with patch("src.agent_1a.agent.search_eurlex", return_value=mock_eurlex_result):
        with patch("src.agent_1a.agent.search_cbam_guidance", return_value=mock_empty_cbam):
            with patch("src.storage.database.get_session") as mock_get_session:
                mock_session = MagicMock()
                mock_repo = MagicMock()
                
                # Mock document existant avec même hash
                mock_existing_doc = MagicMock()
                mock_existing_doc.hash_sha256 = "abc123"
                mock_repo.find_by_url.return_value = mock_existing_doc
                
                mock_get_session.return_value = mock_session
                
                with patch("src.storage.repositories.DocumentRepository", return_value=mock_repo):
                    result = await run_agent_1a_combined(keyword="CBAM")
                    
                    assert result["status"] == "success"
                    assert result["documents_unchanged"] == 1
                    assert result["documents_processed"] == 0


@pytest.mark.asyncio
async def test_run_agent_1a_combined_exception_handling():
    """Teste la gestion d'une exception globale"""
    
    with patch("src.agent_1a.agent.search_eurlex", side_effect=Exception("Unexpected error")):
        result = await run_agent_1a_combined(keyword="CBAM")
        
        assert result["status"] == "error"
        assert "error" in result
        assert "Unexpected error" in result["error"]


# ============================================================================
# TESTS DES PARAMÈTRES
# ============================================================================

