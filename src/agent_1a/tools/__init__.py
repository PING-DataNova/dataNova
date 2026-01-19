"""
Outils LangChain pour Agent 1A - Version EUR-Lex

Dev 1 (Godson) - Responsable des outils de collecte
"""

from .scraper import search_eurlex_tool
from .document_fetcher import fetch_document_tool
from .pdf_extractor import extract_pdf_content_tool
from .summarizer import generate_summary_tool

def get_agent_1a_tools():
    """
    Retourne la liste des outils disponibles pour l'Agent 1A.
    
    Returns:
        List[Tool]: Liste des outils LangChain
    """
    return [
        search_eurlex_tool,
        fetch_document_tool,
        extract_pdf_content_tool,
        generate_summary_tool
    ]

__all__ = [
    "search_eurlex_tool",
    "fetch_document_tool",
    "extract_pdf_content_tool",
    "generate_summary_tool",
    "get_agent_1a_tools"
]
