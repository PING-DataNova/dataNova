"""
Outils LangChain pour l'Agent 1A

Chaque outil est une fonction décorée avec @tool qui peut être utilisée par l'agent.
"""

from langchain_core.tools import tool

# TODO: Implémenter les outils suivants (DEV 1)


@tool
def scrape_source(source_id: str) -> dict:
    """
    Scrape une source réglementaire pour détecter les documents disponibles.
    
    Args:
        source_id: Identifiant de la source (ex: "cbam-legislation")
    
    Returns:
        dict: Liste des documents trouvés avec leurs métadonnées
    """
    # TODO: Implémenter le scraping
    return {"documents": [], "status": "not_implemented"}


@tool
def download_document(document_url: str, document_id: str) -> dict:
    """
    Télécharge un document depuis une URL.
    
    Args:
        document_url: URL du document à télécharger
        document_id: Identifiant unique du document
    
    Returns:
        dict: Chemin du fichier téléchargé et métadonnées
    """
    # TODO: Implémenter le téléchargement
    return {"file_path": None, "status": "not_implemented"}


@tool
def extract_pdf_content(file_path: str) -> dict:
    """
    Extrait le contenu textuel et les métadonnées d'un PDF.
    
    Args:
        file_path: Chemin vers le fichier PDF
    
    Returns:
        dict: Contenu extrait, codes NC détectés, métadonnées
    """
    # TODO: Implémenter l'extraction PDF
    return {"content": "", "nc_codes": [], "status": "not_implemented"}


@tool
def save_document_data(document_data: dict) -> dict:
    """
    Sauvegarde les données d'un document dans la base de données.
    
    Args:
        document_data: Dictionnaire contenant les données du document
    
    Returns:
        dict: Confirmation de la sauvegarde
    """
    # TODO: Implémenter la sauvegarde
    return {"saved": False, "status": "not_implemented"}


@tool
def check_document_exists(document_hash: str) -> bool:
    """
    Vérifie si un document existe déjà dans la base de données.
    
    Args:
        document_hash: Hash SHA-256 du document
    
    Returns:
        bool: True si le document existe, False sinon
    """
    # TODO: Implémenter la vérification
    return False


def get_agent_1a_tools() -> list:
    """Retourne la liste des outils disponibles pour l'Agent 1A."""
    return [
        scrape_source,
        download_document,
        extract_pdf_content,
        save_document_data,
        check_document_exists,
    ]
