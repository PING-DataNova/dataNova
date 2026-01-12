"""
Outils LangChain pour l'Agent 1A

Chaque outil est une fonction décorée avec @tool qui peut être utilisée par l'agent.
"""

import asyncio
import json
from pathlib import Path

from langchain_core.tools import tool

from src.agent_1a.tools.scraper import scrape_cbam_page, ScrapeResult
from src.agent_1a.tools.document_fetcher import download_document, DownloadResult
from src.agent_1a.tools.pdf_extractor import extract_pdf_content, PDFContent
from src.agent_1a.tools.change_detector import check_document_exists, ChangeStatus


@tool
def scrape_source(source_url: str, source_id: str = "cbam-legislation") -> dict:
    """
    Scrape une source réglementaire pour détecter les documents disponibles.
    
    Args:
        source_url: URL de la source à scraper
        source_id: Identifiant de la source (ex: "cbam-legislation")
    
    Returns:
        dict: Liste des documents trouvés avec leurs métadonnées
    """
    result: ScrapeResult = asyncio.run(scrape_cbam_page(source_url, source_id))
    
    # Convertir en dict pour LangChain
    return {
        "source_id": result.source_id,
        "source_url": str(result.source_url),
        "scraped_at": result.scraped_at.isoformat(),
        "total_found": result.total_found,
        "status": result.status,
        "error": result.error,
        "documents": [
            {
                "title": doc.title,
                "url": str(doc.url),
                "celex_id": doc.celex_id,
                "document_type": doc.document_type,
                "publication_date": doc.publication_date,
                "metadata": doc.metadata
            }
            for doc in result.documents
        ]
    }


@tool
def download_document_tool(document_url: str, celex_id: str = None) -> dict:
    """
    Télécharge un document depuis une URL.
    
    Args:
        document_url: URL du document à télécharger
        celex_id: Identifiant CELEX du document (optionnel)
    
    Returns:
        dict: Chemin du fichier téléchargé et métadonnées
    """
    result: DownloadResult = asyncio.run(download_document(document_url, celex_id))
    
    return {
        "celex_id": result.celex_id,
        "file_path": str(result.file_path) if result.file_path else None,
        "file_hash": result.file_hash,
        "file_size_bytes": result.file_size_bytes,
        "downloaded_at": result.downloaded_at.isoformat(),
        "format": result.format,
        "status": result.status,
        "error": result.error,
        "url": str(result.url)
    }


@tool
def extract_pdf_content_tool(file_path: str) -> dict:
    """
    Extrait le contenu textuel et les métadonnées d'un PDF.
    
    Args:
        file_path: Chemin vers le fichier PDF
    
    Returns:
        dict: Contenu extrait, codes NC détectés, métadonnées
    """
    result: PDFContent = extract_pdf_content(Path(file_path))
    
    return {
        "file_path": str(result.file_path),
        "total_pages": result.total_pages,
        "text_content": result.text_content[:1000] + "..." if len(result.text_content) > 1000 else result.text_content,
        "text_length": len(result.text_content),
        "nc_codes": [
            {
                "code": nc.code,
                "context": nc.context,
                "page_number": nc.page_number
            }
            for nc in result.nc_codes
        ],
        "tables_count": len(result.tables),
        "metadata": result.metadata,
        "extraction_status": result.extraction_status,
        "error": result.error
    }


@tool
def check_document_exists_tool(document_hash: str, celex_id: str = None) -> dict:
    """
    Vérifie si un document existe déjà dans la base de données.
    
    Args:
        document_hash: Hash SHA-256 du document
        celex_id: Identifiant CELEX (optionnel)
    
    Returns:
        dict: Statut du document (nouveau, modifié, inchangé)
    """
    result: ChangeStatus = check_document_exists(document_hash, celex_id)
    
    return {
        "document_hash": result.document_hash,
        "celex_id": result.celex_id,
        "status": result.status,
        "existing_document_id": result.existing_document_id,
        "previous_hash": result.previous_hash,
        "checked_at": result.checked_at.isoformat()
    }


@tool
def save_document_data(document_data: str) -> dict:
    """
    Sauvegarde les données d'un document dans la base de données.
    
    Args:
        document_data: JSON string contenant les données du document
    
    Returns:
        dict: Confirmation de la sauvegarde
    """
    # Parse le JSON
    data = json.loads(document_data)
    
    # TODO: Implémenter la sauvegarde dans la base de données
    # Cette partie sera complétée par Dev 3 (Storage)
    
    return {
        "saved": False,
        "status": "not_implemented",
        "message": "À implémenter par Dev 3 - Storage"
    }


def get_agent_1a_tools() -> list:
    """Retourne la liste des outils disponibles pour l'Agent 1A."""
    return [
        scrape_source,
        download_document_tool,
        extract_pdf_content_tool,
        check_document_exists_tool,
        save_document_data,
    ]