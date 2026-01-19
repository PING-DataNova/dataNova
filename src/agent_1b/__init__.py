"""
Agent 1B - Analyse et scoring de pertinence

Responsable: Développeur 2 (Nora)

Modules:
- tools/: Outils modulaires pour l'analyse
    - keyword_filter: Filtrage par mots-clés (Niveau 1, 25%)
    - nc_code_verifier: Vérification codes NC (Niveau 2, 25%)
    - semantic_analyzer: Analyse LLM (Niveau 3, 50%)
    - score_calculator: Calcul score final + criticité
- agent_pipeline: Orchestration du workflow complet
"""

__version__ = "0.2.0"

# Exports principaux
from .agent_pipeline import Agent1BPipeline, run_agent_1b_pipeline
from .tools import (
    filter_by_keywords,
    verify_nc_codes,
    semantic_analysis,
    calculate_final_score,
    get_relevance_threshold,
    get_agent_1b_tools,
    DEFAULT_WEIGHTS,
    CRITICALITY_THRESHOLDS,
)

__all__ = [
    # Pipeline
    "Agent1BPipeline",
    "run_agent_1b_pipeline",
    # Tools
    "filter_by_keywords",
    "verify_nc_codes",
    "semantic_analysis",
    "calculate_final_score",
    "get_relevance_threshold",
    "get_agent_1b_tools",
    # Constants
    "DEFAULT_WEIGHTS",
    "CRITICALITY_THRESHOLDS",
]
