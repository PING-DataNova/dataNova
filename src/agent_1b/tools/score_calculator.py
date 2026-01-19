"""
Score Calculator - Agent 1B Tool

Calcule le score final pondéré et détermine la criticité.

Pondération par défaut:
- Keywords (Niveau 1): 25%
- NC Codes (Niveau 2): 25%
- Sémantique (Niveau 3): 50%

Responsable: Dev 2 (Nora)
"""

from typing import Tuple
import structlog

logger = structlog.get_logger()

# Pondérations par défaut
DEFAULT_WEIGHTS = {
    "keywords": 0.25,
    "nc_codes": 0.25,
    "semantic": 0.50
}

# Seuils de criticité
CRITICALITY_THRESHOLDS = {
    "CRITICAL": 0.8,
    "HIGH": 0.6,
    "MEDIUM": 0.4,
    "LOW": 0.0
}


def calculate_final_score(
    keyword_score: float,
    nc_code_score: float,
    semantic_score: float,
    weights: dict = None
) -> Tuple[float, str]:
    """
    Calcule le score final pondéré et la criticité.
    
    Args:
        keyword_score: Score du filtrage mots-clés (0-1)
        nc_code_score: Score des codes NC (0-1)
        semantic_score: Score de l'analyse sémantique (0-1)
        weights: Pondérations personnalisées (optionnel)
    
    Returns:
        tuple: (final_score, criticality)
            - final_score: float arrondi à 3 décimales
            - criticality: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
    
    Example:
        >>> score, crit = calculate_final_score(0.34, 0.0, 0.95)
        >>> print(f"{score} → {crit}")
        0.561 → MEDIUM
    """
    # Utiliser les poids par défaut si non fournis
    w = weights or DEFAULT_WEIGHTS
    
    # Calcul pondéré
    final_score = (
        w.get("keywords", 0.25) * keyword_score +
        w.get("nc_codes", 0.25) * nc_code_score +
        w.get("semantic", 0.50) * semantic_score
    )
    
    # Déterminer la criticité
    if final_score >= CRITICALITY_THRESHOLDS["CRITICAL"]:
        criticality = "CRITICAL"
    elif final_score >= CRITICALITY_THRESHOLDS["HIGH"]:
        criticality = "HIGH"
    elif final_score >= CRITICALITY_THRESHOLDS["MEDIUM"]:
        criticality = "MEDIUM"
    else:
        criticality = "LOW"
    
    final_score = round(final_score, 3)
    
    logger.debug(
        "score_calculated",
        keyword=keyword_score,
        nc_code=nc_code_score,
        semantic=semantic_score,
        final=final_score,
        criticality=criticality
    )
    
    return final_score, criticality


def get_relevance_threshold() -> float:
    """Retourne le seuil de pertinence (document considéré pertinent si score >= seuil)."""
    return 0.3  # Ajusté selon les tests (initialement 0.5)
