# tests/agent_1a/conftest.py
"""
Fixtures partagées pour les tests de l'Agent 1A
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime
from pathlib import Path


# ============================================================================
# FIXTURES POUR LES DOCUMENTS EUR-LEX
# ============================================================================

@pytest.fixture
def sample_eurlex_document():
    """Fixture pour un document EUR-Lex type"""
    doc = MagicMock()
    doc.celex_number = "32023R0956"
    doc.title = "Regulation (EU) 2023/956 establishing a carbon border adjustment mechanism"
    doc.url = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R0956"
    doc.pdf_url = "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32023R0956"
    doc.document_type = "Regulation"
    doc.source = "eurlex"
    doc.keyword = "CBAM"
    doc.publication_date = datetime(2023, 5, 16)
    doc.status = "ACTIVE_LAW"
    doc.metadata = {
        "remote_hash": "abc123def456",
        "scraped_at": "2024-01-24T10:00:00"
    }
    return doc


@pytest.fixture
def sample_eurlex_search_result(sample_eurlex_document):
    """Fixture pour un résultat de recherche EUR-Lex"""
    result = MagicMock()
    result.status = "success"
    result.total_found = 1
    result.documents = [sample_eurlex_document]
    result.error = None
    return result


@pytest.fixture
def empty_eurlex_search_result():
    """Fixture pour un résultat de recherche EUR-Lex vide"""
    result = MagicMock()
    result.status = "success"
    result.total_found = 0
    result.documents = []
    result.error = None
    return result


@pytest.fixture
def error_eurlex_search_result():
    """Fixture pour un résultat de recherche EUR-Lex avec erreur"""
    result = MagicMock()
    result.status = "error"
    result.total_found = 0
    result.documents = []
    result.error = "Connection timeout"
    return result


# ============================================================================
# FIXTURES POUR LES DOCUMENTS CBAM GUIDANCE
# ============================================================================

@pytest.fixture
def sample_cbam_document():
    """Fixture pour un document CBAM Guidance type"""
    doc = MagicMock()
    doc.title = "Guidance document on CBAM implementation for importers"
    doc.url = "https://taxation-customs.ec.europa.eu/document/download/123456"
    doc.date = "2024-01-15"
    doc.size = "1.65 MB"
    doc.category = "guidance"
    doc.language = "en"
    doc.format = "PDF"
    return doc


@pytest.fixture
def sample_cbam_search_result(sample_cbam_document):
    """Fixture pour un résultat de recherche CBAM Guidance"""
    result = MagicMock()
    result.status = "success"
    result.total_found = 1
    result.documents = [sample_cbam_document]
    result.error = None
    return result


@pytest.fixture
def empty_cbam_search_result():
    """Fixture pour un résultat de recherche CBAM vide"""
    result = MagicMock()
    result.status = "success"
    result.total_found = 0
    result.documents = []
    result.error = None
    return result


# ============================================================================
# FIXTURES POUR LE TÉLÉCHARGEMENT
# ============================================================================

@pytest.fixture
def sample_fetched_document():
    """Fixture pour un document téléchargé"""
    doc = MagicMock()
    doc.url = "https://example.com/doc.pdf"
    doc.file_path = "data/documents/doc.pdf"
    doc.hash_sha256 = "abc123def456789012345678901234567890123456789012345678901234"
    doc.file_size = 1024000
    doc.content_type = "application/pdf"
    doc.status = "downloaded"
    doc.downloaded_at = datetime.now()
    doc.metadata = {}
    return doc


@pytest.fixture
def sample_fetch_result(sample_fetched_document):
    """Fixture pour un résultat de téléchargement réussi"""
    result = MagicMock()
    result.url = "https://example.com/doc.pdf"
    result.success = True
    result.document = sample_fetched_document
    result.error = None
    return result


@pytest.fixture
def error_fetch_result():
    """Fixture pour un résultat de téléchargement avec erreur"""
    result = MagicMock()
    result.url = "https://example.com/doc.pdf"
    result.success = False
    result.document = None
    result.error = "Download failed: Connection timeout"
    return result


# ============================================================================
# FIXTURES POUR L'EXTRACTION PDF
# ============================================================================

@pytest.fixture
def sample_nc_code():
    """Fixture pour un code NC"""
    nc = MagicMock()
    nc.code = "7206"
    nc.context = "Iron and steel products, non-alloy"
    nc.page = 5
    nc.confidence = 0.95
    return nc


@pytest.fixture
def sample_extracted_content(sample_nc_code):
    """Fixture pour un contenu PDF extrait"""
    content = MagicMock()
    content.file_path = "data/documents/doc.pdf"
    content.text = "This Regulation establishes a carbon border adjustment mechanism (CBAM)..."
    content.nc_codes = [sample_nc_code]
    content.tables = [
        {
            "page": 10,
            "headers": ["CN Code", "Description", "Rate"],
            "rows": [
                ["7206", "Iron and steel", "25%"],
                ["7207", "Semi-finished products", "25%"]
            ]
        }
    ]
    content.metadata = {
        "pdf_metadata": {
            "Author": "European Commission",
            "Title": "CBAM Regulation",
            "CreationDate": "2023-05-16"
        }
    }
    content.page_count = 45
    content.status = "success"
    content.error = None
    return content


@pytest.fixture
def error_extracted_content():
    """Fixture pour un contenu PDF avec erreur"""
    content = MagicMock()
    content.file_path = "data/documents/missing.pdf"
    content.text = ""
    content.nc_codes = []
    content.tables = []
    content.metadata = {}
    content.page_count = 0
    content.status = "error"
    content.error = "File not found: data/documents/missing.pdf"
    return content


# ============================================================================
# FIXTURES POUR LA BASE DE DONNÉES
# ============================================================================

@pytest.fixture
def mock_database_session():
    """Fixture pour une session de base de données mockée"""
    session = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    session.query = MagicMock()
    return session


@pytest.fixture
def mock_document_repository():
    """Fixture pour un repository de documents mocké"""
    repo = MagicMock()
    repo.find_by_url = MagicMock(return_value=None)
    repo.find_by_hash = MagicMock(return_value=None)
    repo.upsert_document = MagicMock(return_value=(MagicMock(id="doc123"), "created"))
    return repo


@pytest.fixture
def mock_existing_document():
    """Fixture pour un document existant en BDD"""
    doc = MagicMock()
    doc.id = "existing123"
    doc.title = "Existing Document"
    doc.source_url = "https://example.com/existing.pdf"
    doc.hash_sha256 = "existing_hash_123"
    doc.regulation_type = "CBAM"
    doc.workflow_status = "raw"
    doc.status = "new"
    doc.created_at = datetime.now()
    return doc


# ============================================================================
# FIXTURES POUR LES TESTS D'INTÉGRATION
# ============================================================================

@pytest.fixture
def test_data_dir(tmp_path):
    """Fixture pour un répertoire de données de test temporaire"""
    data_dir = tmp_path / "data" / "documents"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def sample_pdf_file(test_data_dir):
    """Fixture pour créer un fichier PDF de test"""
    pdf_path = test_data_dir / "test.pdf"
    # Créer un fichier PDF minimal (juste pour les tests)
    pdf_path.write_bytes(b"%PDF-1.4\n%EOF")
    return str(pdf_path)


# ============================================================================
# FIXTURES POUR LES MOCKS HTTP
# ============================================================================

@pytest.fixture
def mock_httpx_response():
    """Fixture pour une réponse HTTP mockée"""
    response = MagicMock()
    response.status_code = 200
    response.content = b"fake pdf content"
    response.headers = {
        'Content-Type': 'application/pdf',
        'Content-Length': '16',
        'ETag': '"abc123def456789012345678901234567890123456789012345678901234"'
    }
    response.raise_for_status = MagicMock()
    return response


# ============================================================================
# HOOKS PYTEST
# ============================================================================

def pytest_configure(config):
    """Configuration pytest"""
    config.addinivalue_line(
        "markers", "integration: Tests d'intégration nécessitant internet"
    )
    config.addinivalue_line(
        "markers", "slow: Tests lents"
    )
    config.addinivalue_line(
        "markers", "database: Tests nécessitant une base de données"
    )


def pytest_collection_modifyitems(config, items):
    """Modifier les items de test collectés"""
    # Ajouter automatiquement le marqueur 'slow' aux tests d'intégration
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(pytest.mark.slow)
