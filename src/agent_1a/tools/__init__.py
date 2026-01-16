"""
Implémentations des outils Agent 1A

Ce fichier exporte les implémentations brutes (fonctions et classes).
Pour l'interface LangChain avec décorateurs @tool, voir ../tools.py

Architecture:
- scraper.py          → search_eurlex() + search_eurlex_tool
- document_fetcher.py → fetch_document() + fetch_document_tool
- pdf_extractor.py    → class PDFExtractor
- change_detector.py  → class ChangeDetector

Note: get_agent_1a_tools() est maintenant dans ../tools.py (Dev 3)
"""

# ✅ CORRECTION: Ne plus exporter get_agent_1a_tools() ici
# Cette fonction est maintenant dans ../tools.py pour centraliser l'interface

# Export des implémentations brutes
from .scraper import search_eurlex, search_eurlex_tool, EURLexSearchResult, EURLexDocument
from .document_fetcher import fetch_document, fetch_document_tool, FetchResult, FetchedDocument
from .pdf_extractor import PDFExtractor
from .change_detector import ChangeDetector

__all__ = [
    # Fonctions de scraping
    "search_eurlex",
    "search_eurlex_tool",
    "EURLexSearchResult",
    "EURLexDocument",
    
    # Fonctions de téléchargement
    "fetch_document",
    "fetch_document_tool",
    "FetchResult",
    "FetchedDocument",
    
    # Classes d'extraction et détection
    "PDFExtractor",
    "ChangeDetector",
]