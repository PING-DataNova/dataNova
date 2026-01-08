"""
Agent autonome 1B - Analyse et scoring

Utilise LangChain pour créer un agent ReAct qui analyse la pertinence des documents.
"""

from langchain.agents import AgentExecutor, create_react_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate

from src.agent_1b.tools import get_agent_1b_tools
from src.config import settings

# Prompt pour l'agent ReAct
AGENT_1B_PROMPT = PromptTemplate.from_template(
    """Tu es l'Agent 1B, spécialisé dans l'analyse de pertinence de documents réglementaires.

Ta mission:
1. Analyser chaque nouveau document collecté par l'Agent 1A
2. Appliquer un triple filtrage:
   - Niveau 1: Filtrage par mots-clés
   - Niveau 2: Vérification des codes NC (douaniers)
   - Niveau 3: Analyse sémantique approfondie
3. Calculer un score de pertinence (0-1)
4. Déterminer le niveau de criticité (CRITICAL/HIGH/MEDIUM/LOW)
5. Générer des alertes structurées si pertinent

Contexte entreprise:
{company_profile}

Outils disponibles:
{tools}

Utilise ce format:
Question: le document à analyser
Thought: ce que tu penses faire
Action: l'outil à utiliser
Action Input: l'entrée de l'outil
Observation: le résultat de l'action
... (ce cycle peut se répéter)
Thought: Je connais maintenant la pertinence du document
Final Answer: le résultat de l'analyse avec le score et la criticité

Question: {input}

{agent_scratchpad}
"""
)


def create_agent_1b(company_profile: dict) -> AgentExecutor:
    """Crée l'agent 1B avec ses outils."""
    
    # LLM
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        api_key=settings.anthropic_api_key,
        temperature=0,
    )
    
    # Outils
    tools = get_agent_1b_tools()
    
    # Agent avec contexte entreprise
    agent = create_react_agent(llm, tools, AGENT_1B_PROMPT)
    
    # Executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=15,
    )
    
    return agent_executor


def run_agent_1b(document_id: str, company_profile: dict) -> dict:
    """Exécute l'agent 1B pour analyser un document."""
    agent = create_agent_1b(company_profile)
    
    task = f"Analyser le document {document_id} pour déterminer sa pertinence"
    result = agent.invoke({
        "input": task,
        "company_profile": company_profile
    })
    
    return result


# À IMPLÉMENTER PAR DEV 2
# TODO: Compléter l'implémentation de l'agent
