"""
Agent 1B - Analyse et scoring de pertinence

Triple filtrage:
- Niveau 1 (30%): Mots-clés métier
- Niveau 2 (30%): Codes NC/SH douaniers
- Niveau 3 (40%): Analyse sémantique LLM

Output validé avec Pydantic.
"""

__version__ = "0.1.0"

from .agent import Agent1B, run_agent_1b_on_document
from .models import (
    DocumentAnalysis,
    AnalysisAlert,
    Criticality,
    ImpactedProcess,
    KeywordAnalysisResult,
    NCCodeAnalysisResult,
    SemanticAnalysisResult,
    RelevanceScore
)

__all__ = [
    "Agent1B",
    "run_agent_1b_on_document",
    "DocumentAnalysis",
    "AnalysisAlert",
    "Criticality",
    "ImpactedProcess",
    "KeywordAnalysisResult",
    "NCCodeAnalysisResult",
    "SemanticAnalysisResult",
    "RelevanceScore"
]
