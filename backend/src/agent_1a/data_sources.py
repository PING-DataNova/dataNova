"""
Gestionnaire de sources de données pour l'Agent 1A (V2)

Ce module permet à l'Agent 1A de lire les sources depuis:
1. La table DataSource en base de données (prioritaire)
2. Les fichiers JSON de configuration (fallback)

L'administrateur peut activer/désactiver des sources via l'API admin.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
import structlog

from src.storage.database import SessionLocal
from src.storage.datasource_repository import DataSourceRepository
from src.storage.models import DataSource

logger = structlog.get_logger()


# Mapping entre noms courts utilisés dans le code et noms en BDD
SOURCE_NAME_MAPPING = {
    "eurlex": "EUR-Lex",
    "eur-lex": "EUR-Lex",
    "openmeteo": "OpenMeteo",
    "open-meteo": "OpenMeteo",
    "acled": "ACLED",
    "who": "WHO Disease Outbreak News",
    "who_don": "WHO Disease Outbreak News",
}


def _normalize_source_name(source_name: str) -> str:
    """
    Normalise un nom de source pour correspondre à celui en BDD.
    
    Args:
        source_name: Nom court (eurlex) ou nom complet (EUR-Lex)
        
    Returns:
        Nom tel qu'il est stocké en BDD
    """
    # D'abord essayer le mapping
    normalized = SOURCE_NAME_MAPPING.get(source_name.lower())
    if normalized:
        return normalized
    
    # Sinon retourner tel quel
    return source_name


def get_enabled_data_sources(risk_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Récupère les sources de données activées depuis la BDD.
    
    Args:
        risk_type: Filtrer par type de risque (regulatory, climate, geopolitical, sanitary)
                   Si None, retourne toutes les sources activées
                   
    Returns:
        Liste de dictionnaires avec les infos de chaque source
    """
    try:
        db = SessionLocal()
        repo = DataSourceRepository(db)
        
        if risk_type:
            sources = repo.get_by_risk_type(risk_type)
            # Filtrer pour ne garder que les activées
            sources = [s for s in sources if s.is_active]
        else:
            sources = repo.get_active()
        
        result = []
        for s in sources:
            result.append({
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "source_type": s.source_type,
                "risk_type": s.risk_type,
                "base_url": s.base_url,
                "api_key_env_var": s.api_key_env_var,
                "config": s.config,
                "is_enabled": s.is_active  # Note: modèle utilise is_active
            })
        
        db.close()
        logger.info("data_sources_loaded_from_db", count=len(result), risk_type=risk_type)
        return result
        
    except Exception as e:
        logger.error("data_sources_db_error", error=str(e))
        return []


def get_regulatory_sources() -> List[Dict[str, Any]]:
    """Retourne les sources réglementaires activées (EUR-Lex, etc.)"""
    return get_enabled_data_sources(risk_type="regulatory")


def get_climate_sources() -> List[Dict[str, Any]]:
    """Retourne les sources climatiques activées (OpenMeteo, etc.)"""
    return get_enabled_data_sources(risk_type="climate")


def get_geopolitical_sources() -> List[Dict[str, Any]]:
    """Retourne les sources géopolitiques activées (ACLED, etc.)"""
    return get_enabled_data_sources(risk_type="geopolitical")


def get_sanitary_sources() -> List[Dict[str, Any]]:
    """Retourne les sources sanitaires activées (WHO, etc.)"""
    return get_enabled_data_sources(risk_type="sanitary")


def is_source_enabled(source_name: str) -> bool:
    """
    Vérifie si une source spécifique est activée.
    
    Args:
        source_name: Nom de la source (ex: "eurlex", "openmeteo")
        
    Returns:
        True si la source est activée, False sinon
    """
    try:
        db = SessionLocal()
        repo = DataSourceRepository(db)
        
        # Normaliser le nom pour correspondre à la BDD
        db_name = _normalize_source_name(source_name)
        source = repo.get_by_name(db_name)
        is_enabled = source is not None and source.is_active  # Note: modèle utilise is_active
        
        db.close()
        return is_enabled
        
    except Exception as e:
        logger.error("source_check_error", source=source_name, error=str(e))
        # En cas d'erreur, on considère la source comme activée (fallback sécurisé)
        return True


def get_source_config(source_name: str) -> Optional[Dict[str, Any]]:
    """
    Récupère la configuration d'une source spécifique.
    
    Args:
        source_name: Nom de la source
        
    Returns:
        Configuration de la source ou None si non trouvée
    """
    try:
        db = SessionLocal()
        repo = DataSourceRepository(db)
        
        # Normaliser le nom pour correspondre à la BDD
        db_name = _normalize_source_name(source_name)
        source = repo.get_by_name(db_name)
        if source:
            config = {
                "id": source.id,
                "name": source.name,
                "description": source.description,
                "source_type": source.source_type,
                "risk_type": source.risk_type,
                "base_url": source.base_url,
                "api_key_env_var": source.api_key_env_var,
                "config": source.config,
                "is_enabled": source.is_active,  # Note: modèle utilise is_active
                "refresh_frequency": source.refresh_frequency,
                "priority": source.priority
            }
            db.close()
            return config
        
        db.close()
        return None
        
    except Exception as e:
        logger.error("source_config_error", source=source_name, error=str(e))
        return None


def update_source_fetch_status(source_name: str, status: str, error: Optional[str] = None) -> bool:
    """
    Met à jour le statut de la dernière collecte d'une source.
    
    Args:
        source_name: Nom de la source
        status: Statut (success, error, partial)
        error: Message d'erreur si applicable
        
    Returns:
        True si mise à jour réussie
    """
    try:
        db = SessionLocal()
        repo = DataSourceRepository(db)
        
        # Normaliser le nom pour correspondre à la BDD
        db_name = _normalize_source_name(source_name)
        source = repo.get_by_name(db_name)
        if source:
            repo.update_fetch_status(source.id, status, error)
            db.close()
            logger.info("source_status_updated", source=source_name, status=status)
            return True
        
        db.close()
        return False
        
    except Exception as e:
        logger.error("source_status_update_error", source=source_name, error=str(e))
        return False


def increment_source_documents_count(source_name: str, count: int = 1) -> bool:
    """
    Incrémente le compteur de documents d'une source.
    
    Args:
        source_name: Nom de la source
        count: Nombre de documents à ajouter
        
    Returns:
        True si mise à jour réussie
    """
    try:
        db = SessionLocal()
        repo = DataSourceRepository(db)
        
        # Normaliser le nom pour correspondre à la BDD
        db_name = _normalize_source_name(source_name)
        source = repo.get_by_name(db_name)
        if source:
            repo.increment_documents_count(source.id, count)
            db.close()
            return True
        
        db.close()
        return False
        
    except Exception as e:
        logger.error("source_count_update_error", source=source_name, error=str(e))
        return False


# ============================================================================
# Fonctions de fallback vers fichiers JSON (rétrocompatibilité)
# ============================================================================

def load_eurlex_domains_config_from_json() -> Dict:
    """
    Charge la configuration des domaines EUR-Lex depuis le fichier JSON.
    Utilisé en fallback si la BDD n'est pas disponible.
    
    Returns:
        Dict: Configuration des domaines
    """
    config_path = Path(__file__).parent.parent.parent / "config" / "eurlex_domains.json"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("eurlex_domains_config_not_found", path=str(config_path))
        return {}
    except json.JSONDecodeError as e:
        logger.error("eurlex_domains_config_invalid", error=str(e))
        return {}


def load_sources_config_from_json() -> Dict:
    """
    Charge la configuration des sources depuis le fichier JSON.
    Utilisé en fallback si la BDD n'est pas disponible.
    
    Returns:
        Dict: Configuration des sources
    """
    config_path = Path(__file__).parent.parent.parent / "config" / "sources.json"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("sources_config_not_found", path=str(config_path))
        return {}
    except json.JSONDecodeError as e:
        logger.error("sources_config_invalid", error=str(e))
        return {}


# ============================================================================
# Fonction hybride : BDD avec fallback JSON
# ============================================================================

def should_collect_from_source(source_name: str) -> bool:
    """
    Détermine si l'Agent 1A doit collecter depuis une source.
    
    Vérifie d'abord la BDD, puis fallback sur les fichiers JSON.
    
    Args:
        source_name: Nom de la source (eurlex, openmeteo, acled, who)
        
    Returns:
        True si la source doit être collectée
    """
    # 1. Essayer la BDD
    source = get_source_config(source_name)
    if source is not None:
        return source.get("is_enabled", False)
    
    # 2. Fallback: fichier sources.json
    json_config = load_sources_config_from_json()
    if json_config:
        sources_list = json_config.get("sources", [])
        for s in sources_list:
            if s.get("name") == source_name:
                return s.get("enabled", True)
    
    # 3. Par défaut, on collecte
    logger.warning("source_not_found_default_enabled", source=source_name)
    return True


def get_all_sources_to_collect() -> List[str]:
    """
    Retourne la liste de toutes les sources à collecter.
    
    Returns:
        Liste des noms de sources activées
    """
    sources = get_enabled_data_sources()
    
    if sources:
        return [s["name"] for s in sources]
    
    # Fallback: retourner les sources par défaut
    return ["eurlex", "openmeteo"]
