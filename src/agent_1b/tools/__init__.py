"""
Outils pour Agent 1B - Évaluation de pertinence

Ce module expose les 4 niveaux de scoring :
- Niveau 1: Filtrage par mots-clés (keyword_filter)
- Niveau 2: Vérification codes NC (nc_code_verifier)
- Niveau 3: Analyse sémantique LLM (semantic_analyzer)
- Calcul: Score final pondéré (score_calculator)

Pondération par défaut: 25% keywords + 25% NC + 50% semantic
"""

from .keyword_filter import filter_by_keywords
from .nc_code_verifier import verify_nc_codes
from .semantic_analyzer import semantic_analysis
from .score_calculator import (
    calculate_final_score,
    get_relevance_threshold,
    DEFAULT_WEIGHTS,
    CRITICALITY_THRESHOLDS,
)


def get_agent_1b_tools():
    """
    Retourne la liste des outils Agent 1B.
    
    Returns:
        dict: {
            "filter_by_keywords": function,
            "verify_nc_codes": function,
            "semantic_analysis": async function,
            "calculate_final_score": function
        }
    """
    return {
        "filter_by_keywords": filter_by_keywords,
        "verify_nc_codes": verify_nc_codes,
        "semantic_analysis": semantic_analysis,
        "calculate_final_score": calculate_final_score,
    }


__all__ = [
    "filter_by_keywords",
    "verify_nc_codes",
    "semantic_analysis",
    "calculate_final_score",
    "get_relevance_threshold",
    "get_agent_1b_tools",
    "DEFAULT_WEIGHTS",
    "CRITICALITY_THRESHOLDS",
]
