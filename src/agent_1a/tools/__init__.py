"""
Outils LangChain pour Agent 1A - Version EUR-Lex

Dev 1 (Godson) - Responsable des outils de collecte
"""

from .scraper import search_eurlex_tool
from .document_fetcher import fetch_document_tool
# from .pdf_extractor import extract_pdf_content_tool  # Dev 2
# from .summarizer import generate_summary_tool  # Bonus Dev 1

def get_agent_1a_tools():
    """
    Retourne la liste des outils disponibles pour l'Agent 1A.
    
    Returns:
        List[Tool]: Liste des outils LangChain
    """
    return [
        search_eurlex_tool,
        fetch_document_tool,
        # extract_pdf_content_tool,  # Dev 2 - À ajouter
        # generate_summary_tool  # Bonus - À réactiver si besoin
    ]

__all__ = [
    "search_eurlex_tool",
    "fetch_document_tool",
    # "extract_pdf_content_tool",  # Dev 2
    # "generate_summary_tool",  # Bonus
    "get_agent_1a_tools"
]
