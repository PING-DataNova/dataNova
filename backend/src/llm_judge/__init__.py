"""
Agent 3 : LLM Judge - Évaluation de la qualité des analyses
"""

from .judge import Judge
from .criteria_evaluator import CriteriaEvaluator
from .weights_config import (
    get_weights,
    calculate_weighted_score,
    WEIGHTS_CLIMATIQUE,
    WEIGHTS_REGLEMENTAIRE,
    WEIGHTS_GEOPOLITIQUE
)
from .feedback_loop import JudgeFeedbackLoop

__all__ = [
    "Judge",
    "CriteriaEvaluator",
    "get_weights",
    "calculate_weighted_score",
    "WEIGHTS_CLIMATIQUE",
    "WEIGHTS_REGLEMENTAIRE",
    "WEIGHTS_GEOPOLITIQUE",
    "JudgeFeedbackLoop"
]
