"""
Tools pour l'Agent 1A - Version EUR-Lex
"""

from typing import List
from langchain.tools import BaseTool

# Import des outils
from .tools.eurlex_scraper import search_eurlex_tool      # NOUVEAU
from .tools.document_fetcher import fetch_document_tool
from .tools.pdf_extractor import extract_pdf_content_tool



def get_agent_1a_tools() -> List[BaseTool]:
    """
    Retourne la liste des outils disponibles pour l'Agent 1A.
    """
    tools = [
        search_eurlex_tool,          # 1. Rechercher sur EUR-Lex
        fetch_document_tool,         # 2. Télécharger les documents
        extract_pdf_content_tool,    # 3. Extraire le contenu des PDFs
        generate_summary_tool,       # 4. Générer les résumés avec LLM
    ]
    
    return tools
