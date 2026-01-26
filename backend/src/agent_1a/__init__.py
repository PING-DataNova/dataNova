"""
Agent 1A - Collecte et extraction de données réglementaires

Responsable: Développeur 1

Modules:
- scraper/: Scraping des sources web
- downloader/: Téléchargement des documents
- extractors/: Extraction de contenu (PDF, HTML)
- tools/: Outils LangChain pour l'agent
"""

__version__ = "0.1.0"

# Importer la fonction principale
from .agent import run_agent_1a_combined

__all__ = ["run_agent_1a_combined"]
