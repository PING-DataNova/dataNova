"""
Agent 1A - Collecte et analyse de documents réglementaires via EUR-Lex

Version EUR-Lex : Recherche directement sur EUR-Lex au lieu de la page Commission

Agent ReAct utilisant Claude 3.5 Sonnet avec 4 outils :
- EUR-Lex Searcher : Recherche de documents sur EUR-Lex par mot-clé
- Document Fetcher : Téléchargement de documents
- PDF Extractor : Extraction de contenu (texte, tableaux, codes NC)
- Summarizer : Génération de résumés via LLM

Responsable: Dev 1
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
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
    Crée l'Agent 1A avec Claude 3.5 Haiku et ses outils.

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
        timeout=60,
        max_retries=1
    )
    
    # 2. Récupérer les outils
    tools = get_agent_1a_tools()
    logger.info("agent_1a_tools_loaded", tool_count=len(tools))
    
    # 3. Créer le prompt système
    system_prompt = """Tu es l'Agent 1A, spécialisé dans la collecte automatisée de documents réglementaires via EUR-Lex.

WORKFLOW COMPLET :
1. Rechercher sur EUR-Lex avec search_eurlex_tool (mot-clé fourni par l'utilisateur)
2. Pour CHAQUE document trouvé :
   a. Télécharger le PDF avec fetch_document_tool (utiliser pdf_url si disponible, sinon url)
   b. Extraire le contenu avec extract_pdf_content_tool
   c. Générer un résumé avec generate_summary_tool
3. Retourner le JSON final avec TOUS les documents enrichis

RÈGLES IMPORTANTES :
- Traiter TOUS les documents trouvés (ou jusqu'à la limite spécifiée)
- Le résumé doit être concis (2-4 phrases) et mentionner les points clés
- Format de sortie : JSON avec la structure exacte demandée
- Ne pas arrêter tant que tous les documents n'ont pas été traités
- Utiliser pdf_url en priorité pour le téléchargement

FORMAT DE SORTIE ATTENDU :
{
  "documents": [
    {
      "title": "...",
      "celex_number": "32023R0956",
      "document_type": "REGULATION|DIRECTIVE|DECISION|PROPOSAL",
      "publication_date": "YYYY-MM-DDTHH:MM:SS",
      "url": "...",
      "pdf_url": "...",
      "summary": "Résumé généré par LLM (2-4 phrases)",
      "status": "ACTIVE_LAW|PROPOSAL|DECISION"
    }
  ]
}"""
    
    # 4. Créer l'agent avec LangGraph
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt
    )
    
    logger.info("agent_1a_initialization_completed")
    return agent


async def run_agent_1a_eurlex(
    keyword: str = "CBAM",
    max_documents: int = 10
) -> dict:
    """
    Exécute l'Agent 1A avec une recherche EUR-Lex.
    
    Args:
        keyword: Mot-clé de recherche (CBAM, EUDR, CSRD, etc.)
        max_documents: Nombre maximum de documents à traiter
    
    Returns:
        dict: Résultat de l'exécution avec documents enrichis
    """
    logger.info("agent_1a_eurlex_execution_started", keyword=keyword, max_documents=max_documents)
    
    try:
        agent = create_agent_1a()
        
        # Construire la requête
        query = f"Recherche sur EUR-Lex le mot-clé '{keyword}', limite à {max_documents} documents. Pour chaque document, télécharge le PDF, extrait le contenu et génère un résumé. Retourne le JSON au format demandé."
        
        # LangGraph utilise ainvoke avec un dict contenant "messages"
        result = await agent.ainvoke(
            {"messages": [("user", query)]},
            config={"recursion_limit": 100}  # Augmenté pour traiter plusieurs documents
        )
        
        # Extraire la réponse finale
        final_message = result["messages"][-1]
        output = final_message.content if hasattr(final_message, 'content') else str(final_message)
        
        # Essayer de parser le JSON de sortie
        try:
            output_json = json.loads(output)
        except json.JSONDecodeError:
            # Si ce n'est pas du JSON valide, essayer d'extraire le JSON du texte
            import re
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                output_json = json.loads(json_match.group(0))
            else:
                output_json = {"error": "Could not parse JSON output", "raw_output": output}
        
        logger.info("agent_1a_eurlex_execution_completed", status="success", documents_count=len(output_json.get("documents", [])))
        
        return {
            "status": "success",
            "keyword": keyword,
            "output": output_json,
            "intermediate_steps": result.get("messages", [])
        }
        
    except Exception as e:
        logger.error("agent_1a_eurlex_execution_error", error=str(e), exc_info=True)
        return {
            "status": "error",
            "keyword": keyword,
            "error": str(e)
        }


async def run_agent_1a_simple(keyword: str = "CBAM", max_documents: int = 5) -> Dict[str, Any]:
    """
    Version simplifiée pour exécuter l'agent et obtenir directement les documents enrichis.
    
    Args:
        keyword: Mot-clé de recherche EUR-Lex (CBAM, EUDR, CSRD, etc.)
        max_documents: Nombre maximum de documents à traiter
    
    Returns:
        dict: {"documents": [...]}
    """
    result = await run_agent_1a_eurlex(keyword, max_documents)
    
    if result["status"] == "success":
        return result["output"]
    else:
        return {"error": result.get("error"), "documents": []}


# Pour tester l'agent directement
if __name__ == "__main__":
    import asyncio
    
    async def test_agent():
        print("=" * 80)
        print("🤖 TEST AGENT 1A EUR-LEX - Recherche CBAM")
        print("=" * 80)
        
        # Test : Rechercher 3 documents CBAM sur EUR-Lex
        result = await run_agent_1a_simple(keyword="CBAM", max_documents=3)
        
        if "error" in result:
            print(f"\n❌ Erreur: {result['error']}")
        else:
            print(f"\n✅ {len(result.get('documents', []))} documents collectés depuis EUR-Lex\n")
            
            # Afficher les documents
            for i, doc in enumerate(result.get("documents", []), 1):
                print(f"\n{'='*60}")
                print(f"Titre : {doc.get('title', 'Sans titre')}")
                print(f"CELEX: {doc.get('celex_number', 'N/A')}")
                print(f"Type: {doc.get('document_type', 'N/A')}")
                print(f"Status: {doc.get('status', 'N/A')}")
                # Formater la date pour afficher seulement YYYY-MM-DD
                pub_date = doc.get('publication_date', 'N/A')
                if pub_date != 'N/A' and 'T' in str(pub_date):
                    pub_date = pub_date.split('T')[0]  # Garder seulement la partie avant 'T'
                print(f"Date: {pub_date}")
                print(f"URL: {doc.get('url', 'N/A')}")
                print(f"PDF: {doc.get('pdf_url', 'N/A')}")
                print(f"\nRésumé:")
                print(f"{doc.get('summary', 'Pas de résumé disponible')}")
        
        print("\n" + "=" * 80)
        print("✅ Test terminé !")
        print("=" * 80)
    
    asyncio.run(test_agent())