"""
Agent 1A - Collecte et extraction de données réglementaires EUR-Lex

Responsable: Développeur 1

Version recommandée: Pipeline (orchestration Python manuelle)
- Plus rapide (3-5x vs ReAct)
- Aucun risque de rate limit
- Contrôle total du workflow

Version alternative: ReAct (LangGraph) - pour workflows non-déterministes
"""

__version__ = "0.2.0"

# VERSION RECOMMANDÉE : Pipeline (Option B)
from .agent_pipeline import (
    run_agent_1a_pipeline,
    run_agent_1a_simple_pipeline,
    Agent1APipeline
)

# VERSION ALTERNATIVE : ReAct (Option A optimisée)
from .agent import (
    create_agent_1a,
    run_agent_1a_eurlex,
    run_agent_1a_simple
)

from .tools import get_agent_1a_tools

# Export version pipeline comme défaut
__all__ = [
    # Pipeline (recommandé)
    "run_agent_1a_pipeline",
    "run_agent_1a_simple_pipeline",
    "Agent1APipeline",
    # ReAct (alternatif)
    "create_agent_1a",
    "run_agent_1a_eurlex",
    "run_agent_1a_simple",
    # Outils
    "get_agent_1a_tools"
]
