"""
Outils pour Agent 1A - Version EUR-Lex
"""

from langchain_core.tools import Tool

# Importer les fonctions
from .scraper import search_eurlex
from .cbam_guidance_scraper import search_cbam_guidance, search_cbam_guidance_sync
from .document_fetcher import fetch_document
from .pdf_extractor import extract_pdf_content

# Créer les LangChain Tools pour l'agent ReAct
search_eurlex_tool = Tool(
    name="search_eurlex_tool",
    description="Recherche des documents sur EUR-Lex par mot-clé (CBAM, EUDR, CSRD)",
    func=lambda keyword, max_results=10: search_eurlex(keyword, max_results),
    coroutine=search_eurlex  # Pour async
)

fetch_document_tool = Tool(
    name="fetch_document_tool",
    description="Télécharge un document PDF depuis une URL",
    func=lambda url, output_dir="data/documents": fetch_document(url, output_dir),
    coroutine=fetch_document  # Pour async
)

extract_pdf_content_tool = Tool(
    name="extract_pdf_content_tool",
    description="Extrait le contenu d'un PDF (texte + codes NC)",
    func=lambda file_path: extract_pdf_content(file_path),
    coroutine=extract_pdf_content  # Pour async
)

search_cbam_guidance_tool = Tool(
    name="search_cbam_guidance_tool",
    description="Recherche des documents Guidance, FAQs, Templates sur le site CBAM officiel. Categories: all, guidance, faq, template, default_values, tool",
    func=search_cbam_guidance_sync,
    coroutine=search_cbam_guidance  # Pour async
)

def get_agent_1a_tools():
    """Retourne la liste des outils LangChain pour l'agent ReAct"""
    return [
        search_eurlex_tool,
        search_cbam_guidance_tool,
        fetch_document_tool,
        extract_pdf_content_tool
    ]

# Exporter les fonctions ET les tools
__all__ = [
    # Fonctions (pour appel direct)
    "search_eurlex",
    "search_cbam_guidance",
    "fetch_document",
    "extract_pdf_content",
    # Tools (pour agent ReAct)
    "search_eurlex_tool",
    "search_cbam_guidance_tool",
    "fetch_document_tool",
    "extract_pdf_content_tool",
    "get_agent_1a_tools"
]
