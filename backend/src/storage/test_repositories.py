# tests/storage/test_repositories.py

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.storage.models import Base, Document, Analysis
from src.storage.repositories import DocumentRepository, AnalysisRepository


@pytest.fixture(scope="module")
def db_engine():
    """Fixture pour créer un moteur de base de données en mémoire."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Fixture pour créer une session de base de données."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(autouse=True)
def clear_tables(db_session):
    """Nettoie les tables avant chaque test."""
    db_session.query(Analysis).delete()
    db_session.query(Document).delete()
    db_session.commit()


@pytest.fixture
def doc_repo(db_session):
    """Fixture pour le DocumentRepository."""
    return DocumentRepository(db_session)


@pytest.fixture
def analysis_repo(db_session):
    """Fixture pour le AnalysisRepository."""
    return AnalysisRepository(db_session)


# --- Tests pour DocumentRepository ---

def test_add_and_get_document(doc_repo, db_session):
    """Teste l'ajout et la récupération d'un document."""
    new_doc = Document(
        title="Test Doc",
        source_url="http://example.com/test",
        hash_sha256="hash123",
        workflow_status="raw"
     )
    doc_repo.add(new_doc)
    
    retrieved_doc = doc_repo.get_document_by_source_url("http://example.com/test" )
    
    assert retrieved_doc is not None
    assert retrieved_doc.title == "Test Doc"
    assert retrieved_doc.hash_sha256 == "hash123"


def test_update_document(doc_repo, db_session):
    """Teste la mise à jour d'un document."""
    doc = Document(title="Original Title", source_url="http://example.com/update", workflow_status="raw" )
    doc_repo.add(doc)
    
    doc.workflow_status = "analyzed"
    doc_repo.update(doc)
    
    updated_doc = doc_repo.get_document_by_source_url("http://example.com/update" )
    assert updated_doc.workflow_status == "analyzed"


def test_get_pending_documents(doc_repo, db_session):
    """Teste la récupération des documents en attente d'analyse."""
    doc1 = Document(source_url="url1", workflow_status="raw")
    doc2 = Document(source_url="url2", workflow_status="analyzed")
    doc3 = Document(source_url="url3", workflow_status="raw")
    
    db_session.add_all([doc1, doc2, doc3])
    db_session.commit()
    
    pending_docs = doc_repo.get_pending_documents(limit=10)
    
    assert len(pending_docs) == 2
    assert {d.source_url for d in pending_docs} == {"url1", "url3"}


# --- Tests pour AnalysisRepository ---

def test_add_analysis(analysis_repo, doc_repo, db_session):
    """Teste l'ajout d'une nouvelle analyse."""
    doc = Document(source_url="url_for_analysis", workflow_status="raw")
    doc_repo.add(doc)
    
    analysis = Analysis(
        document_id=doc.id,
        company_id="GMG-001",
        is_relevant=True,
        confidence=0.9
    )
    analysis_repo.add(analysis)
    
    # Vérifier que l'analyse a été ajoutée
    added_analysis = db_session.query(Analysis).filter_by(document_id=doc.id).one_or_none()
    assert added_analysis is not None
    assert added_analysis.is_relevant is True
    assert added_analysis.confidence == 0.9
