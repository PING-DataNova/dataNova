"""
Service centralisé de gestion des catégories de risques.

Ce module charge les catégories depuis un fichier JSON persistant
et fournit des helpers utilisés par tous les composants backend.

Pour ajouter une nouvelle catégorie de risque:
1. Ajouter via l'API admin POST /api/admin/risk-categories
2. Ou éditer directement config/risk_categories.json
3. Tout le système (Agent 1B, impacts, notifications, frontend) s'adapte automatiquement.
"""

import json
import os
import threading
from typing import Dict, List, Optional, Any
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)

# Chemin vers le fichier de configuration
_CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
_RISK_CATEGORIES_FILE = _CONFIG_DIR / "risk_categories.json"

# Cache thread-safe
_lock = threading.Lock()
_categories_cache: Optional[List[Dict[str, Any]]] = None
_cache_mtime: float = 0


def _load_from_file() -> List[Dict[str, Any]]:
    """Charge les catégories depuis le fichier JSON."""
    if not _RISK_CATEGORIES_FILE.exists():
        logger.warning("risk_categories_file_not_found", path=str(_RISK_CATEGORIES_FILE))
        return _get_defaults()
    
    try:
        with open(_RISK_CATEGORIES_FILE, "r", encoding="utf-8") as f:
            categories = json.load(f)
        logger.debug("risk_categories_loaded", count=len(categories))
        return categories
    except (json.JSONDecodeError, IOError) as e:
        logger.error("risk_categories_load_error", error=str(e))
        return _get_defaults()


def _get_defaults() -> List[Dict[str, Any]]:
    """Retourne les catégories par défaut."""
    return [
        {
            "code": "regulatory", "name": "Réglementaire", "event_type": "reglementaire",
            "color": "#3B82F6", "bg_color": "#DBEAFE", "text_color": "#1D4ED8",
            "icon": "📜", "svg_icon": "scale", "tab_label": "Réglementations",
            "description": "Nouvelles réglementations", "is_active": True
        },
        {
            "code": "climate", "name": "Climatique", "event_type": "climatique",
            "color": "#10B981", "bg_color": "#D1FAE5", "text_color": "#047857",
            "icon": "🌡️", "svg_icon": "cloud", "tab_label": "Climat",
            "description": "Alertes météo et risques climatiques", "is_active": True
        },
        {
            "code": "geopolitical", "name": "Géopolitique", "event_type": "geopolitique",
            "color": "#F59E0B", "bg_color": "#FEF3C7", "text_color": "#B45309",
            "icon": "🌍", "svg_icon": "globe", "tab_label": "Géopolitique",
            "description": "Conflits, sanctions, instabilité politique", "is_active": True
        },
    ]


def _save_to_file(categories: List[Dict[str, Any]]) -> None:
    """Sauvegarde les catégories dans le fichier JSON."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(_RISK_CATEGORIES_FILE, "w", encoding="utf-8") as f:
            json.dump(categories, f, indent=2, ensure_ascii=False)
        logger.info("risk_categories_saved", count=len(categories))
    except IOError as e:
        logger.error("risk_categories_save_error", error=str(e))


def get_all_categories() -> List[Dict[str, Any]]:
    """Retourne toutes les catégories de risques (actives et inactives)."""
    global _categories_cache, _cache_mtime
    
    with _lock:
        # Recharger si le fichier a changé
        try:
            mtime = os.path.getmtime(_RISK_CATEGORIES_FILE) if _RISK_CATEGORIES_FILE.exists() else 0
        except OSError:
            mtime = 0
        
        if _categories_cache is None or mtime != _cache_mtime:
            _categories_cache = _load_from_file()
            _cache_mtime = mtime
        
        return list(_categories_cache)


def get_active_categories() -> List[Dict[str, Any]]:
    """Retourne uniquement les catégories actives."""
    return [c for c in get_all_categories() if c.get("is_active", True)]


def get_category_by_code(code: str) -> Optional[Dict[str, Any]]:
    """Trouve une catégorie par son code (regulatory, climate, etc.)."""
    return next((c for c in get_all_categories() if c["code"] == code), None)


def get_category_by_event_type(event_type: str) -> Optional[Dict[str, Any]]:
    """Trouve une catégorie par son event_type (reglementaire, climatique, etc.)."""
    et = event_type.lower().strip()
    # Chercher exact match d'abord
    cat = next((c for c in get_all_categories() if c["event_type"] == et), None)
    if cat:
        return cat
    # Chercher match partiel (ex: 'climat' dans 'climatique')
    for c in get_all_categories():
        if et in c["event_type"] or c["event_type"] in et:
            return c
    return None


def get_event_type_to_tab_label_map() -> Dict[str, str]:
    """Retourne un mapping event_type → tab_label pour le dashboard."""
    return {c["event_type"]: c["tab_label"] for c in get_active_categories()}


def get_event_type_to_display_name_map() -> Dict[str, str]:
    """Retourne un mapping event_type → display name pour les impacts."""
    return {c["event_type"]: c["tab_label"] for c in get_all_categories()}


def get_active_event_types() -> List[str]:
    """Retourne la liste des event_types actifs."""
    return [c["event_type"] for c in get_active_categories()]


def get_all_event_type_aliases() -> Dict[str, str]:
    """
    Retourne un mapping d'aliases → event_type normalisé.
    Permet de normaliser 'regulation' → 'reglementaire', 'climate' → 'climatique', etc.
    """
    aliases = {}
    # Mappings connus pour rétrocompatibilité
    known_aliases = {
        "regulation": "reglementaire",
        "regulatory": "reglementaire",
        "climate": "climatique",
        "weather": "climatique",
        "meteo": "climatique",
        "geopolitical": "geopolitique",
        "geopolitic": "geopolitique",
        "sanitary": "sanitaire",
        "health": "sanitaire",
        "pandemic": "sanitaire",
    }
    
    for c in get_all_categories():
        et = c["event_type"]
        aliases[et] = et  # identité
        aliases[c["code"]] = et  # code → event_type
    
    # Ajouter les aliases connus
    aliases.update(known_aliases)
    
    return aliases


def normalize_event_type(raw_event_type: str) -> str:
    """
    Normalise un type d'événement brut vers le event_type canonique.
    Retourne le type original (en lowercase) si aucun alias trouvé.
    """
    raw = raw_event_type.lower().strip()
    aliases = get_all_event_type_aliases()
    return aliases.get(raw, raw)


def map_event_type_to_category_label(event_type: str) -> str:
    """
    Mappe un event_type vers son label de catégorie pour le dashboard.
    Ex: 'climatique' → 'Climat', 'reglementaire' → 'Réglementations'
    Retourne le event_type capitalisé si non trouvé.
    """
    cat = get_category_by_event_type(event_type)
    if cat:
        return cat["tab_label"]
    # Fallback: capitaliser le type
    return event_type.capitalize()


def add_category(category_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ajoute une nouvelle catégorie et persiste dans le fichier JSON.
    Lève ValueError si le code existe déjà.
    """
    global _categories_cache, _cache_mtime
    
    with _lock:
        categories = _load_from_file()
        
        code = category_data.get("code", "")
        if any(c["code"] == code for c in categories):
            raise ValueError(f"Une catégorie avec le code '{code}' existe déjà")
        
        # S'assurer que tous les champs requis sont présents
        new_cat = {
            "code": code,
            "name": category_data.get("name", code.capitalize()),
            "event_type": category_data.get("event_type", code),
            "color": category_data.get("color", "#6B7280"),
            "bg_color": category_data.get("bg_color", "#F3F4F6"),
            "text_color": category_data.get("text_color", "#374151"),
            "icon": category_data.get("icon", "⚠️"),
            "svg_icon": category_data.get("svg_icon", "alert"),
            "tab_label": category_data.get("tab_label", category_data.get("name", code.capitalize())),
            "description": category_data.get("description", ""),
            "is_active": category_data.get("is_active", True),
        }
        
        categories.append(new_cat)
        _save_to_file(categories)
        
        # Invalider le cache
        _categories_cache = categories
        _cache_mtime = os.path.getmtime(_RISK_CATEGORIES_FILE) if _RISK_CATEGORIES_FILE.exists() else 0
        
        logger.info("risk_category_added", code=code, name=new_cat["name"])
        return new_cat


def toggle_category(code: str) -> Optional[Dict[str, Any]]:
    """Active ou désactive une catégorie. Retourne la catégorie modifiée."""
    global _categories_cache, _cache_mtime
    
    with _lock:
        categories = _load_from_file()
        
        cat = next((c for c in categories if c["code"] == code), None)
        if not cat:
            return None
        
        cat["is_active"] = not cat.get("is_active", True)
        _save_to_file(categories)
        
        _categories_cache = categories
        _cache_mtime = os.path.getmtime(_RISK_CATEGORIES_FILE) if _RISK_CATEGORIES_FILE.exists() else 0
        
        return cat


def update_category(code: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Met à jour une catégorie existante."""
    global _categories_cache, _cache_mtime
    
    with _lock:
        categories = _load_from_file()
        
        cat = next((c for c in categories if c["code"] == code), None)
        if not cat:
            return None
        
        for key, value in updates.items():
            if key != "code":  # Ne pas modifier le code
                cat[key] = value
        
        _save_to_file(categories)
        
        _categories_cache = categories
        _cache_mtime = os.path.getmtime(_RISK_CATEGORIES_FILE) if _RISK_CATEGORIES_FILE.exists() else 0
        
        return cat


def invalidate_cache():
    """Force la recharge du cache au prochain appel."""
    global _categories_cache, _cache_mtime
    with _lock:
        _categories_cache = None
        _cache_mtime = 0
