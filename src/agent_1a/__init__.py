"""
Agent 1A - Collecte et extraction de données réglementaires EUR-Lex

Responsable: Développeur 1

Pipeline d'orchestration manuelle:
- Plus rapide (3-5x vs ReAct)
- Aucun risque de rate limit
- Contrôle total du workflow
"""

__version__ = "0.2.0"

# Pipeline (orchestration manuelle)
from .agent_pipeline import (
    run_agent_1a_pipeline,
    run_agent_1a_simple_pipeline,
    Agent1APipeline
)

from .tools import get_agent_1a_tools

__all__ = [
    # Pipeline
    "run_agent_1a_pipeline",
    "run_agent_1a_simple_pipeline",
    "Agent1APipeline",
    # Outils
    "get_agent_1a_tools"
]
