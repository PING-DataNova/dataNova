"""
Agent 1A - Collecte et analyse de documents réglementaires via EUR-Lex

Version EUR-Lex : Recherche directement sur EUR-Lex au lieu de la page Commission

Agent ReAct utilisant Claude 3 Haiku avec 5 outils :
- EUR-Lex Searcher : Recherche de documents sur EUR-Lex par mot-clé
- Document Fetcher : Téléchargement de documents
- PDF Extractor : Extraction de contenu (texte, tableaux, codes NC)
- Change Detector : Détection de changements (hash)
- DB Saver : Sauvegarde en base de données

Responsable: Dev 1 (Godson) + Dev 2 (Nora) + Dev 3 (Marc)
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

# Importer depuis tools.py centralisé (Dev 3)
from src.agent_1a.tools import get_agent_1a_tools

logger = structlog.get_logger()


def create_agent_1a(
    model_name: str = "claude-3-haiku-20240307",
    temperature: float = 0.1,
    max_tokens: int = 4096
):
    """
    Crée l'Agent 1A avec Claude 3 Haiku et ses outils.

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
    
    # ✅ CORRECTION: Prompt système mis à jour pour refléter les outils réels
    # 3. Créer le prompt système
    system_prompt = """Tu es l'Agent 1A, spécialisé dans la collecte automatisée de documents réglementaires via EUR-Lex.

OUTILS DISPONIBLES :
1. search_eurlex_tool : Recherche de documents sur EUR-Lex par mot-clé
2. fetch_document_tool : Téléchargement de PDFs depuis EUR-Lex
3. extract_pdf_content : Extraction de contenu (texte, tableaux, codes NC)
4. check_document_changes : Détection de changements via hash SHA-256
5. save_document_to_db : Sauvegarde en base de données

WORKFLOW COMPLET :
1. Rechercher sur EUR-Lex avec search_eurlex_tool (mot-clé fourni par l'utilisateur)
2. Pour CHAQUE document trouvé :
   a. Télécharger le PDF avec fetch_document_tool (utiliser pdf_url si disponible)
   b. Extraire le contenu avec extract_pdf_content (obtenir texte, tableaux, codes NC)
   c. Vérifier les changements avec check_document_changes (comparer hash)
   d. Si nouveau ou modifié : sauvegarder avec save_document_to_db
3. Retourner un rapport de traitement avec statistiques

RÈGLES IMPORTANTES :
- Traiter TOUS les documents trouvés (ou jusqu'à la limite spécifiée)
- Utiliser pdf_url en priorité pour le téléchargement
- Toujours extraire les codes NC des documents
- Sauvegarder uniquement les documents nouveaux ou modifiés
- En cas d'erreur sur un document, continuer avec les suivants
- Fournir un rapport final avec : nombre total, nouveaux, modifiés, inchangés, erreurs

FORMAT DE SORTIE ATTENDU :
{
  "summary": {
    "total_found": int,
    "total_processed": int,
    "new": int,
    "modified": int,
    "unchanged": int,
    "errors": int
  },
  "documents": [
    {
      "title": "...",
      "celex_number": "32023R0956",
      "document_type": "REGULATION|DIRECTIVE|DECISION",
      "publication_date": "YYYY-MM-DD",
      "url": "...",
      "pdf_url": "...",
      "status": "new|modified|unchanged|error",
      "nc_codes": ["4002.19", "7606"],
      "document_id": "uuid" (si sauvegardé)
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
        query = f"""Recherche sur EUR-Lex le mot-clé '{keyword}', limite à {max_documents} documents. 

Pour chaque document :
1. Télécharge le PDF
2. Extrait le contenu (texte, codes NC)
3. Vérifie les changements
4. Sauvegarde en base si nouveau ou modifié

Retourne le JSON au format demandé avec le résumé et la liste des documents."""
        
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
        dict: {"summary": {...}, "documents": [...]}
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
            # Afficher le résumé
            summary = result.get('summary', {})
            print(f"\n📊 RÉSUMÉ:")
            print(f"   Total trouvés: {summary.get('total_found', 0)}")
            print(f"   Total traités: {summary.get('total_processed', 0)}")
            print(f"   Nouveaux: {summary.get('new', 0)}")
            print(f"   Modifiés: {summary.get('modified', 0)}")
            print(f"   Inchangés: {summary.get('unchanged', 0)}")
            print(f"   Erreurs: {summary.get('errors', 0)}")
            
            # Afficher les documents
            documents = result.get("documents", [])
            print(f"\n📄 {len(documents)} DOCUMENTS DÉTAILLÉS:\n")
            
            for i, doc in enumerate(documents, 1):
                print(f"\n{'='*60}")
                print(f"[{i}] Titre : {doc.get('title', 'Sans titre')}")
                print(f"{'='*60}")
                print(f"CELEX: {doc.get('celex_number', 'N/A')}")
                print(f"Type: {doc.get('document_type', 'N/A')}")
                print(f"Statut: {doc.get('status', 'N/A')}")
                
                # Formater la date pour afficher seulement YYYY-MM-DD
                pub_date = doc.get('publication_date', 'N/A')
                if pub_date != 'N/A' and 'T' in str(pub_date):
                    pub_date = pub_date.split('T')[0]
                print(f"Date: {pub_date}")
                
                print(f"URL: {doc.get('url', 'N/A')}")
                print(f"PDF: {doc.get('pdf_url', 'N/A')}")
                
                # Codes NC
                nc_codes = doc.get('nc_codes', [])
                if nc_codes:
                    print(f"Codes NC: {', '.join(nc_codes)}")
                
                # ID document si sauvegardé
                doc_id = doc.get('document_id')
                if doc_id:
                    print(f"ID BDD: {doc_id}")
        
        print("\n" + "=" * 80)
        print("✅ Test terminé !")
        print("=" * 80)
    
    asyncio.run(test_agent())