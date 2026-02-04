"""
Tests unitaires pour le module data_sources
===========================================
Date: 04/02/2026
"""

import pytest
import sys
from pathlib import Path

# Ajouter le dossier backend au path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from src.agent_1a.data_sources import (
    should_collect_from_source,
    is_source_enabled,
    get_source_config,
    get_enabled_data_sources,
    get_regulatory_sources,
    get_climate_sources,
    SOURCE_NAME_MAPPING,
)
from src.storage.database import get_session
from src.storage.models import DataSource


class TestShouldCollectFromSource:
    """Tests pour should_collect_from_source"""
    
    def test_eurlex_check(self):
        """Test vérification EUR-Lex"""
        result = should_collect_from_source("eurlex")
        assert isinstance(result, bool)
    
    def test_openmeteo_check(self):
        """Test vérification OpenMeteo"""
        result = should_collect_from_source("openmeteo")
        assert isinstance(result, bool)
    
    def test_unknown_source(self):
        """Test source inconnue"""
        result = should_collect_from_source("source_inconnue_xyz")
        # Par défaut retourne True
        assert result == True
    
    def test_acled_check(self):
        """Test vérification ACLED"""
        result = should_collect_from_source("acled")
        assert isinstance(result, bool)


class TestIsSourceEnabled:
    """Tests pour is_source_enabled"""
    
    def test_enabled_source(self):
        """Test source activée"""
        result = is_source_enabled("EUR-Lex")
        assert isinstance(result, bool)
    
    def test_nonexistent_source(self):
        """Test source inexistante"""
        result = is_source_enabled("source_inexistante")
        assert isinstance(result, bool)


class TestGetSourceConfig:
    """Tests pour get_source_config"""
    
    def test_get_eurlex_config(self):
        """Test config EUR-Lex"""
        config = get_source_config("eurlex")
        
        if config:
            assert config is not None
    
    def test_get_nonexistent_config(self):
        """Test config source inexistante"""
        config = get_source_config("source_inexistante")
        assert config is None


class TestGetEnabledDataSources:
    """Tests pour get_enabled_data_sources"""
    
    def test_returns_list(self):
        """Test retourne une liste"""
        sources = get_enabled_data_sources()
        assert isinstance(sources, list)
    
    def test_all_sources_active(self):
        """Test toutes sources actives"""
        sources = get_enabled_data_sources()
        
        for source in sources:
            if hasattr(source, 'is_active'):
                assert source.is_active == True


class TestGetRegulatorySourcesource:
    """Tests pour get_regulatory_sources"""
    
    def test_returns_list(self):
        """Test retourne une liste"""
        sources = get_regulatory_sources()
        assert isinstance(sources, list)
    
    def test_all_regulatory_type(self):
        """Test type regulatory"""
        sources = get_regulatory_sources()
        
        for source in sources:
            if hasattr(source, 'risk_type'):
                assert source.risk_type == "regulatory"


class TestGetClimateSources:
    """Tests pour get_climate_sources"""
    
    def test_returns_list(self):
        """Test retourne une liste"""
        sources = get_climate_sources()
        assert isinstance(sources, list)


class TestSourceNameMapping:
    """Tests pour SOURCE_NAME_MAPPING"""
    
    def test_mapping_defined(self):
        """Test mapping défini"""
        assert SOURCE_NAME_MAPPING is not None
        assert isinstance(SOURCE_NAME_MAPPING, dict)
    
    def test_eurlex_mapping(self):
        """Test mapping eurlex"""
        assert "eurlex" in SOURCE_NAME_MAPPING
        assert SOURCE_NAME_MAPPING["eurlex"] == "EUR-Lex"
    
    def test_openmeteo_mapping(self):
        """Test mapping openmeteo"""
        assert "openmeteo" in SOURCE_NAME_MAPPING
        assert SOURCE_NAME_MAPPING["openmeteo"] == "OpenMeteo"


class TestDataSourceModel:
    """Tests pour le modèle DataSource"""
    
    def test_datasource_in_db(self):
        """Test sources en BDD"""
        session = get_session()
        count = session.query(DataSource).count()
        
        assert count >= 1
    
    def test_datasource_fields(self):
        """Test champs DataSource"""
        session = get_session()
        source = session.query(DataSource).first()
        
        if source:
            assert hasattr(source, 'id')
            assert hasattr(source, 'name')
            assert hasattr(source, 'is_active')
            assert hasattr(source, 'risk_type')


class TestSourceToggle:
    """Tests pour toggle des sources"""
    
    def test_coherence_bdd_function(self):
        """Test cohérence BDD et fonction"""
        session = get_session()
        source = session.query(DataSource).filter(
            DataSource.name == "EUR-Lex"
        ).first()
        
        if source:
            expected = source.is_active
            result = should_collect_from_source("eurlex")
            assert result == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
