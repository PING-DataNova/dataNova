"""Tests pour l'orchestration du pipeline Agent 1A → Agent 1B."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.orchestration.pipeline import run_pipeline, load_company_profile
from src.storage.models import Document


class TestPipeline:
    """Tests du pipeline complet"""
    
    @patch('src.orchestration.pipeline.asyncio.run')
    @patch('src.orchestration.pipeline.get_session')
    @patch('src.orchestration.pipeline.Agent1B')
    def test_pipeline_success(self, mock_agent1b, mock_get_session, mock_asyncio_run):
        """Test du pipeline avec succès complet"""
        
        # Mock Agent 1A result
        mock_asyncio_run.return_value = {
            "status": "success",
            "documents_processed": 5,
            "documents_unchanged": 2,
            "sources": {
                "eurlex": {"found": 3, "processed": 3},
                "cbam_guidance": {"found": 4, "processed": 2}
            }
        }
        
        # Mock session et documents
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        # Créer des documents mock
        mock_doc = Mock(spec=Document)
        mock_doc.id = "doc-123"
        mock_doc.title = "Test Document"
        mock_doc.content = "Test content"
        mock_doc.regulation_type = "CBAM"
        mock_doc.workflow_status = "raw"
        
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_doc]
        
        # Mock Agent 1B
        mock_analysis = Mock()
        mock_analysis.is_relevant = True
        mock_analysis.relevance_score.criticality.value = "HIGH"
        mock_analysis.created_at = datetime.utcnow()
        
        mock_agent1b.return_value.analyze_document.return_value = mock_analysis
        
        # Mock process_and_display_analysis
        with patch('src.orchestration.pipeline.process_and_display_analysis', return_value="analysis-123"):
            result = run_pipeline()
        
        # Vérifications
        assert result["status"] == "success"
        assert result["agent_1a"]["documents_processed"] == 5
        assert result["agent_1b"]["documents_analyzed"] == 1
        assert result["agent_1b"]["relevant_count"] == 1
        
        # Vérifier que le workflow_status a été mis à jour
        assert mock_doc.workflow_status == "analyzed"
        mock_session.commit.assert_called()
    
    @patch('src.orchestration.pipeline.asyncio.run')
    def test_pipeline_agent1a_fails(self, mock_asyncio_run):
        """Test quand Agent 1A échoue"""
        
        # Mock Agent 1A failure
        mock_asyncio_run.return_value = {
            "status": "error",
            "error": "Connection failed"
        }
        
        result = run_pipeline()
        
        # Le pipeline doit retourner une erreur
        assert result["status"] == "error"
        assert "Agent 1A failed" in result["error"]
    
    @patch('src.orchestration.pipeline.asyncio.run')
    @patch('src.orchestration.pipeline.get_session')
    def test_pipeline_no_documents_to_analyze(self, mock_get_session, mock_asyncio_run):
        """Test quand il n'y a pas de documents à analyser"""
        
        # Mock Agent 1A success
        mock_asyncio_run.return_value = {
            "status": "success",
            "documents_processed": 0,
            "sources": {
                "eurlex": {"found": 0, "processed": 0},
                "cbam_guidance": {"found": 0, "processed": 0}
            }
        }
        
        # Mock session sans documents
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.return_value = []
        
        result = run_pipeline()
        
        assert result["status"] == "success"
        assert result["agent_1b"]["documents_analyzed"] == 0
    
    @patch('src.orchestration.pipeline.asyncio.run')
    @patch('src.orchestration.pipeline.get_session')
    @patch('src.orchestration.pipeline.Agent1B')
    def test_pipeline_agent1b_partial_failure(self, mock_agent1b, mock_get_session, mock_asyncio_run):
        """Test quand Agent 1B échoue sur certains documents mais continue"""
        
        # Mock Agent 1A success
        mock_asyncio_run.return_value = {
            "status": "success",
            "documents_processed": 2,
            "sources": {
                "eurlex": {"found": 2, "processed": 2},
                "cbam_guidance": {"found": 0, "processed": 0}
            }
        }
        
        # Mock session avec 2 documents
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        doc1 = Mock(spec=Document)
        doc1.id = "doc-1"
        doc1.title = "Doc 1"
        doc1.content = "Content 1"
        doc1.regulation_type = "CBAM"
        
        doc2 = Mock(spec=Document)
        doc2.id = "doc-2"
        doc2.title = "Doc 2"
        doc2.content = "Content 2"
        doc2.regulation_type = "CBAM"
        
        mock_session.query.return_value.filter.return_value.all.return_value = [doc1, doc2]
        
        # Agent 1B échoue sur le premier, réussit sur le second
        mock_analysis = Mock()
        mock_analysis.is_relevant = False
        mock_analysis.relevance_score.criticality.value = "LOW"
        mock_analysis.created_at = datetime.utcnow()
        
        mock_agent1b.return_value.analyze_document.side_effect = [
            Exception("Analysis failed"),
            mock_analysis
        ]
        
        with patch('src.orchestration.pipeline.process_and_display_analysis', return_value="analysis-123"):
            result = run_pipeline()
        
        # Le pipeline doit continuer malgré l'erreur
        assert result["status"] == "success"
        assert result["agent_1b"]["errors"] == 1
        assert result["agent_1b"]["documents_analyzed"] == 1


class TestLoadCompanyProfile:
    """Tests du chargement du profil entreprise"""
    
    @patch('src.orchestration.pipeline.get_session')
    def test_load_company_profile_success(self, mock_get_session):
        """Test du chargement réussi du profil depuis la BDD"""
        
        from src.orchestration.pipeline import load_company_profile
        
        # Mock session et profil
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        mock_profile = Mock()
        mock_profile.id = "profile-123"
        mock_profile.company_name = "Hutchinson SA"
        mock_profile.active = True
        mock_profile.nc_codes = ["7318159090", "4016999097"]
        mock_profile.keywords = ["caoutchouc", "joint"]
        mock_profile.regulations = ["CBAM", "EUDR"]
        mock_profile.contact_emails = ["contact@hutchinson.com"]
        mock_profile.config = {}
        
        mock_repo = Mock()
        mock_repo.find_by_name.return_value = mock_profile
        
        with patch('src.orchestration.pipeline.CompanyProfileRepository', return_value=mock_repo):
            profile = load_company_profile("Hutchinson SA")
        
        assert profile["company_name"] == "Hutchinson SA"
        assert profile["company_id"] == "profile-123"
        assert len(profile["nc_codes"]) == 2
        assert "CBAM" in profile["regulations"]
    
    @patch('src.orchestration.pipeline.get_session')
    def test_load_company_profile_not_found(self, mock_get_session):
        """Test quand le profil n'existe pas en BDD"""
        
        from src.orchestration.pipeline import load_company_profile
        
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        mock_repo = Mock()
        mock_repo.find_by_name.return_value = None
        
        with patch('src.orchestration.pipeline.CompanyProfileRepository', return_value=mock_repo):
            with pytest.raises(ValueError, match="non trouvé en BDD"):
                load_company_profile("Unknown Company")
    
    @patch('src.orchestration.pipeline.get_session')
    def test_load_company_profile_inactive(self, mock_get_session):
        """Test quand le profil est désactivé"""
        
        from src.orchestration.pipeline import load_company_profile
        
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        mock_profile = Mock()
        mock_profile.company_name = "Inactive Corp"
        mock_profile.active = False
        
        mock_repo = Mock()
        mock_repo.find_by_name.return_value = mock_profile
        
        with patch('src.orchestration.pipeline.CompanyProfileRepository', return_value=mock_repo):
            with pytest.raises(ValueError, match="désactivé"):
                load_company_profile("Inactive Corp")
