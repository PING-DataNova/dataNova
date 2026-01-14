"""
Agent 1A - Collecte et analyse de documents réglementaires CBAM

Agent ReAct utilisant Claude 3.5 Sonnet avec 4 outils :
- Scraper : Extraction de documents depuis la page CBAM
- Document Fetcher : Téléchargement de documents
- PDF Extractor : Extraction de contenu (texte, tableaux, codes NC)
- Change Detector : Détection de modifications

Responsable: Dev 1
"""

import os
from pathlib import Path
import structlog
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from .tools import get_agent_1a_tools

logger = structlog.get_logger()


def create_agent_1a(
    model_name: str = "claude-3-haiku-20240307",
    temperature: float = 0.1,
    max_tokens: int = 4096
):
    """
    Crée l'Agent 1A avec Claude 3.5 Haiku et ses 4 outils.

    Args:
        model_name: Modèle Anthropic à utiliser
        temperature: Température de génération (0.0 = déterministe)
        max_tokens: Nombre maximum de tokens
    
    Returns:
        Agent LangGraph prêt à l'emploi
    """
    logger.info("agent_1a_initialization_started", model=model_name)
      # 1. Initialiser le modèle Claude
    llm = ChatAnthropic(
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=60,  # Réduit de 120 à 60 secondes
        max_retries=1  # Réduit de 2 à 1 retry
    )
    
    # 2. Récupérer les outils
    tools = get_agent_1a_tools()
    logger.info("agent_1a_tools_loaded", tool_count=len(tools))
      # 3. Créer le prompt système
    system_prompt = """Tu es l'Agent 1A, spécialisé dans la collecte automatisée de documents réglementaires CBAM.

RÈGLES IMPORTANTES :
1. Toujours utiliser scrape_cbam_page_tool EN PREMIER pour trouver les documents
2. Utiliser fetch_document_tool pour télécharger UN document à la fois
3. Utiliser extract_pdf_content_tool APRÈS avoir téléchargé un PDF
4. Utiliser detect_changes_tool pour comparer avec la base de données
5. TOUJOURS fournir le résultat en JSON structuré dans la réponse finale"""
    
    # 4. Créer l'agent avec LangGraph (nouvelle API)
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt
    )
    
    logger.info("agent_1a_initialization_completed")
    return agent


async def run_agent_1a(query: str) -> dict:
    """
    Exécute l'Agent 1A avec une requête.
    
    Args:
        query: Question ou instruction pour l'agent
    
    Returns:
        dict: Résultat de l'exécution avec output et étapes intermédiaires
    """
    logger.info("agent_1a_execution_started", query=query)
    
    try:
        agent = create_agent_1a()
          # LangGraph utilise ainvoke avec un dict contenant "messages"
        result = await agent.ainvoke(
            {"messages": [("user", query)]},
            config={"recursion_limit": 5}  # Réduit de 10 à 5 pour éviter les boucles longues
        )
        
        # Extraire la réponse finale
        final_message = result["messages"][-1]
        output = final_message.content if hasattr(final_message, 'content') else str(final_message)
        
        logger.info("agent_1a_execution_completed", status="success")
        return {
            "status": "success",
            "output": output,
            "intermediate_steps": result.get("messages", [])
        }
        
    except Exception as e:
        logger.error("agent_1a_execution_error", error=str(e), exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


# Pour tester l'agent directement
if __name__ == "__main__":
    import asyncio
    
    async def test_agent():
        print("=" * 80)
        print("🤖 TEST AGENT 1A - Collecte de documents CBAM")
        print("=" * 80)
        
        # Test 1 : Scraping simple
        query1 = "Scrape la page CBAM et donne-moi le nombre total de documents trouvés"
        print(f"\n📝 Query 1: {query1}")
        result1 = await run_agent_1a(query1)
        print(f"✅ Résultat: {result1['output']}")
        
        # Test 2 : Télécharger et extraire
        query2 = """Scrape la page CBAM, télécharge le premier document PDF trouvé, 
        puis extrait son contenu et compte les codes NC"""
        print(f"\n📝 Query 2: {query2}")
        result2 = await run_agent_1a(query2)
        print(f"✅ Résultat: {result2['output']}")
        
        print("\n" + "=" * 80)
        print("✅ Tests terminés !")
        print("=" * 80)
    
    asyncio.run(test_agent())