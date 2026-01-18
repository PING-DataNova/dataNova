# tests/agent_1b/test_company_loader.py

import pytest
import json
from unittest.mock import mock_open, patch, MagicMock
from pathlib import Path

from src.agent_1b.tools.company_loader import load_company_profile


@pytest.fixture
def mock_company_profile_data():
    """Fixture pour fournir des données de profil d'entreprise simulées."""
    return {
        "company_id": "GMG-001",
        "company_name": "Globex Manufacturing Group",
        "description": "Un conglomérat multinational.",
        "keywords": ["acier", "aluminium", "produits chimiques"],
        "nc_codes": ["720711", "760110"],
        "monitored_regulations": ["CBAM", "REACH"]
    }


def test_load_company_profile_success(mock_company_profile_data):
    """Teste le chargement réussi d'un profil d'entreprise."""
    mock_json_str = json.dumps(mock_company_profile_data)
    
    # Mock Path pour éviter les problèmes de chemin
    mock_profile_file = MagicMock(spec=Path)
    mock_profile_file.name = "gmg_001.json"
    
    with patch("src.agent_1b.tools.company_loader.Path") as MockPath:
        mock_path_instance = MagicMock()
        MockPath.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.glob.return_value = [mock_profile_file]
        
        with patch("builtins.open", mock_open(read_data=mock_json_str)):
            profile = load_company_profile("GMG-001")
            
            assert profile["company_id"] == "GMG-001"
            assert profile["company_name"] == "Globex Manufacturing Group"
            assert "acier" in profile["keywords"]
            assert "720711" in profile["nc_codes"]


def test_load_company_profile_not_found():
    """Teste la gestion de l'erreur lorsque le profil n'existe pas."""
    with patch("src.agent_1b.tools.company_loader.Path") as MockPath:
        mock_path_instance = MagicMock()
        MockPath.return_value = mock_path_instance
        mock_path_instance.exists.return_value = False
        
        with pytest.raises(FileNotFoundError):
            load_company_profile("NON-EXISTENT")


def test_load_company_profile_json_decode_error():
    """Teste la gestion d'une erreur de décodage JSON."""
    mock_profile_file = MagicMock(spec=Path)
    mock_profile_file.name = "gmg_001.json"
    
    with patch("src.agent_1b.tools.company_loader.Path") as MockPath:
        mock_path_instance = MagicMock()
        MockPath.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.glob.return_value = [mock_profile_file]
        
        with patch("builtins.open", mock_open(read_data="{invalid_json")):
            # La fonction devrait continuer et retourner None si aucun profil valide n'est trouvé
            with pytest.raises(FileNotFoundError):
                load_company_profile("GMG-001")
