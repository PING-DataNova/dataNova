"""
Agent autonome 1A - Collecte de données

Utilise LangChain pour créer un agent ReAct qui décide quelles actions entreprendre.
"""

from langchain.agents import AgentExecutor, create_react_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate

from src.agent_1a.tools import get_agent_1a_tools
from src.config import settings

# Prompt pour l'agent ReAct
AGENT_1A_PROMPT = PromptTemplate.from_template(
    """Tu es l'Agent 1A, spécialisé dans la collecte et l'extraction de documents réglementaires.

Ta mission:
1. Scraper les sources configurées pour détecter de nouveaux documents
2. Télécharger les documents pertinents
3. Extraire le contenu et les métadonnées
4. Sauvegarder les données structurées

Outils disponibles:
{tools}

Utilise ce format:
Question: la tâche à accomplir
Thought: ce que tu penses faire
Action: l'outil à utiliser
Action Input: l'entrée de l'outil
Observation: le résultat de l'action
... (ce cycle Thought/Action/Action Input/Observation peut se répéter)
Thought: Je sais maintenant la réponse finale
Final Answer: la réponse finale

Question: {input}

{agent_scratchpad}
"""
)


def create_agent_1a() -> AgentExecutor:
    """Crée l'agent 1A avec ses outils."""
    
    # LLM
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        api_key=settings.anthropic_api_key,
        temperature=0,
    )
    
    # Outils
    tools = get_agent_1a_tools()
    
    # Agent
    agent = create_react_agent(llm, tools, AGENT_1A_PROMPT)
    
    # Executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10,
    )
    
    return agent_executor


def run_agent_1a(task: str) -> dict:
    """Exécute l'agent 1A avec une tâche donnée."""
    agent = create_agent_1a()
    result = agent.invoke({"input": task})
    return result


# À IMPLÉMENTER PAR DEV 1
# TODO: Compléter l'implémentation de l'agent
