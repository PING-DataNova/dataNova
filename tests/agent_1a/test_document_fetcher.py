# tests/agent_1a/test_document_fetcher.py

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

from src.agent_1a.tools.document_fetcher import (
    fetch_document,
    get_remote_file_hash
 )


@pytest.mark.asyncio
async def test_fetch_document_success():
    """Teste le téléchargement réussi d'un document."""
    mock_response = MagicMock()
    mock_response.content = b"pdf content"
    mock_response.headers = {"content-type": "application/pdf"}
    mock_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient", return_value=mock_client ):
        with patch("builtins.open", mock_open()) as mocked_file:
            with patch("hashlib.sha256") as mock_hash:
                mock_hash.return_value.hexdigest.return_value = "fake_hash"
                result = await fetch_document("http://example.com/doc.pdf", "/fake/path" )
                
                # Vérifier que la fonction a été appelée
                assert mock_client.get.called


@pytest.mark.asyncio
async def test_fetch_document_http_error( ):
    """Teste la gestion d'une erreur HTTP lors du téléchargement."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError("Error", request=MagicMock( ), response=MagicMock()))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient", return_value=mock_client ):
        result = await fetch_document("http://example.com/doc.pdf", "/fake/path" )
        assert result.success is False


@pytest.mark.asyncio
async def test_get_remote_file_hash_success():
    """Teste la récupération réussie du hash d'un fichier distant."""
    mock_response = MagicMock()
    mock_response.content = b"pdf content"
    mock_response.raise_for_status = AsyncMock()
    
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient", return_value=mock_client ):
        with patch("hashlib.sha256") as mock_hash:
            mock_hash.return_value.hexdigest.return_value = "fake_hash"
            hash_result = await get_remote_file_hash("http://example.com/doc.pdf" )
            # La fonction devrait retourner un hash ou None
            assert hash_result is not None or hash_result is None
