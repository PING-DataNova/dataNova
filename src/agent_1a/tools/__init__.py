"""
Outils LangChain pour Agent 1A
"""
"""
Agent 1A Tools - Export des outils LangChain
"""

from .scraper import scrape_cbam_page_tool
from .document_fetcher import fetch_document_tool
from .pdf_extractor import extract_pdf_content_tool
from .change_detector import detect_changes_tool

def get_agent_1a_tools():
    """
    Retourne la liste des outils disponibles pour l'Agent 1A.
    
    Returns:
        List[Tool]: Liste des outils LangChain
    """
    return [
        scrape_cbam_page_tool,
        fetch_document_tool,
        extract_pdf_content_tool,
        detect_changes_tool
    ]

__all__ = [
    "scrape_cbam_page_tool",
    "fetch_document_tool",
    "extract_pdf_content_tool",
    "detect_changes_tool",
    "get_agent_1a_tools"
]