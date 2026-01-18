"""
Agent 1B Tools - Outils disponibles pour l'Agent 1B

Intègre tous les outils nécessaires pour l'analyse de pertinence.

Responsable: Dev 1
Chemin final: src/agent_1b/tools.py
"""

from langchain.tools import tool
from src.agent_1b.tools.semantic_analyzer import analyze_document_relevance
from src.agent_1b.tools.company_loader import load_company_profile, extract_analysis_profile


@tool
async def semantic_analyzer_tool(
    document_content: str,
    document_title: str,
    company_id: str
) -> dict:
    """
    Outil d'analyse sémantique pour déterminer la pertinence d'un document.
    
    Analyse un document réglementaire par rapport au profil d'une entreprise.
    Détecte les mots-clés pertinents, codes NC, et génère un résumé.
    
    Args:
        document_content: Contenu textuel du document
        document_title: Titre du document
        company_id: ID de l'entreprise (ex: "GMG-001")
    
    Returns:
        dict avec:
        - is_relevant: bool
        - confidence: float (0.0-1.0)
        - matched_keywords: list
        - matched_nc_codes: list
        - summary: str
        - reasoning: str
    
    Example:
        >>> result = await semantic_analyzer_tool(
        ...     document_content="Le CBAM s'applique...",
        ...     document_title="Regulation (EU) 2023/956",
        ...     company_id="GMG-001"
        ... )
        >>> print(result["is_relevant"])
        True
    """
    
    try:
        # Charger le profil d'entreprise
        company_data = load_company_profile(company_id)
        company_profile = extract_analysis_profile(company_data)
        
        # Analyser la pertinence
        analysis_result = await analyze_document_relevance(
            content=document_content,
            title=document_title,
            company_profile=company_profile
        )
        
        return analysis_result.to_dict()
    
    except Exception as e:
        return {
            "is_relevant": False,
            "confidence": 0.0,
            "matched_keywords": [],
            "matched_nc_codes": [],
            "summary": f"Erreur lors de l'analyse: {str(e)}",
            "reasoning": f"Exception: {str(e)}"
        }


def get_agent_1b_tools():
    """
    Retourne la liste des outils disponibles pour l'Agent 1B.
    
    Returns:
        list: Liste des outils LangChain
    """
    
    tools = [
        semantic_analyzer_tool,
    ]
    
    return tools