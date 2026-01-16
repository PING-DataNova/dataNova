tools.py
"""
Outils LangChain pour l'Agent 1A
 
Chaque outil est une fonction décorée avec @tool qui peut être utilisée par l'agent.
Les implémentations détaillées sont dans le dossier tools/
 
Architecture:
- tools/scraper.py          → Dev 1 (Godson)
- tools/document_fetcher.py → Dev 1 (Godson)  
- tools/pdf_extractor.py    → Dev 2 (Nora)
- tools/change_detector.py  → Dev 2 (Nora)
- Ce fichier (tools.py)     → Dev 3 (Marc) - Centralise et expose les @tool
"""
 
from langchain_core.tools import tool
 
# Import des classes d'implémentation
from src.agent_1a.tools.pdf_extractor import PDFExtractor
from src.agent_1a.tools.change_detector import ChangeDetector
 
# TODO: Importer quand Dev 1 aura implémenté
# from src.agent_1a.tools.scraper import CBAMScraper
# from src.agent_1a.tools.document_fetcher import DocumentFetcher
 
 
# ═══════════════════════════════════════════════════════════
# DEV 1 - SCRAPING & TÉLÉCHARGEMENT (TODO)
# ═══════════════════════════════════════════════════════════
 
@tool
def scrape_source(source_id: str) -> dict:
    """
    Scrape une source réglementaire pour détecter les documents disponibles.
    
    Args:
        source_id: Identifiant de la source (ex: "cbam-legislation")
    
    Returns:
        dict: Liste des documents trouvés avec leurs métadonnées
    """
    # TODO: Dev 1 - Implémenter avec CBAMScraper
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
    # TODO: Dev 1 - Implémenter avec DocumentFetcher
    return {"file_path": None, "status": "not_implemented"}
 
 
# ═══════════════════════════════════════════════════════════
# DEV 2 - EXTRACTION & DÉTECTION
# ═══════════════════════════════════════════════════════════
 
# Instance globale pour éviter réinitialisation à chaque appel
_pdf_extractor = None
 
def _get_pdf_extractor() -> PDFExtractor:
    """Lazy initialization du PDFExtractor"""
    global _pdf_extractor
    if _pdf_extractor is None:
        _pdf_extractor = PDFExtractor()
    return _pdf_extractor
 
 
@tool
def extract_pdf_content(file_path: str) -> dict:
    """
    Extrait le contenu structuré d'un PDF réglementaire avec Docling.
    
    Utilise Docling (meilleur que pdfplumber) pour extraire :
    - Texte complet avec structure (sections, articles)
    - Tableaux (taux CBAM, listes NC codes)
    - Codes NC automatiquement détectés
    - Montants (EUR, %, tonnes)
    
    Args:
        file_path: Chemin vers le fichier PDF local ou URL
    
    Returns:
        dict: {
            "text": str (contenu complet),
            "nc_codes": List[str] (codes NC trouvés),
            "tables": List[dict] (tableaux structurés),
            "metadata": dict (titre, auteur, nb pages),
            "sections": List[dict] (chapitres/articles),
            "amounts": List[dict] (montants EUR, %)
        }
    
    Example:
        >>> result = extract_pdf_content("data/documents/cbam_regulation_2024.pdf")
        >>> result["nc_codes"]
        ['4002.19', '7606', '2707']
    """
    extractor = _get_pdf_extractor()
    
    # Détecter si c'est une URL ou un fichier local
    if file_path.startswith('http'):
        return extractor.extract_from_url(file_path)
    else:
        return extractor.extract_from_file(file_path)
 
 
@tool
def check_document_changes(document_hash: str, source_url: str) -> dict:
    """
    Vérifie si un document existe déjà et détecte les changements.
    
    Compare le hash SHA-256 du nouveau contenu avec celui stocké en DB.
    Permet d'éviter de ré-extraire des documents inchangés.
    
    Args:
        document_hash: Hash SHA-256 du nouveau contenu téléchargé
        source_url: URL source du document (EUR-Lex)
    
    Returns:
        dict: {
            "status": "new" | "modified" | "unchanged",
            "existing_id": str | None,
            "old_hash": str | None (si modified)
        }
    
    Example:
        >>> check_document_changes("abc123...", "https://eur-lex.europa.eu/...")
        {"status": "new", "existing_id": None}
        
        >>> check_document_changes("abc123...", "https://eur-lex.europa.eu/...")
        {"status": "unchanged", "existing_id": "550e8400-..."}
    """
    from src.storage.database import get_session
    
    session = get_session()
    try:
        detector = ChangeDetector(session)
        return detector.detect(document_hash, source_url)
    finally:
        session.close()
 
 
# ═══════════════════════════════════════════════════════════
# DEV 3 - SAUVEGARDE EN BASE DE DONNÉES
# ═══════════════════════════════════════════════════════════
 
@tool
def save_document_to_db(
    title: str,
    source_url: str,
    regulation_type: str,
    hash_sha256: str,
    content: str,
    nc_codes: list,
    status: str = "new"
) -> dict:
    """
    Sauvegarde un document extrait dans la base de données.
    
    Crée une entrée dans table `documents` avec workflow_status="raw".
    Si document existe déjà (même hash), retourne l'existant sans dupliquer.
    
    Args:
        title: Titre du document
        source_url: URL d'origine EUR-Lex
        regulation_type: Type (CBAM, EUDR, CSRD, etc.)
        hash_sha256: Hash SHA-256 du contenu
        content: Texte complet extrait
        nc_codes: Liste des codes NC trouvés
        status: "new", "modified", "unchanged"
    
    Returns:
        dict: {"status": "created|existing", "document_id": str}
    """
    from datetime import datetime
    from src.storage.database import get_session
    from src.storage.repositories import DocumentRepository
    from src.storage.models import Document
    
    session = get_session()
    try:
        repo = DocumentRepository(session)
        
        # Vérifier si existe déjà
        existing = repo.find_by_hash(hash_sha256)
        if existing:
            existing.last_checked = datetime.utcnow()
            session.commit()
            return {
                "status": "existing",
                "document_id": existing.id,
                "workflow_status": existing.workflow_status
            }
        
        # Créer nouveau document
        document = Document(
            title=title,
            source_url=source_url,
            regulation_type=regulation_type,
            hash_sha256=hash_sha256,
            content=content,
            nc_codes=nc_codes,
            status=status,
            workflow_status="raw",
            first_seen=datetime.utcnow(),
            last_checked=datetime.utcnow()
        )
        
        saved = repo.save(document)
        session.commit()
        
        return {
            "status": "created",
            "document_id": saved.id,
            "workflow_status": "raw"
        }
    
    except Exception as e:
        session.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        session.close()
 
 
# ═══════════════════════════════════════════════════════════
# EXPORT DES OUTILS POUR AGENT 1A
# ═══════════════════════════════════════════════════════════
 
def get_agent_1a_tools() -> list:
    """Retourne la liste des outils disponibles pour l'Agent 1A."""
    return [
        # Dev 1 - Scraping
        scrape_source,
        download_document,
        # Dev 2 - Extraction
        extract_pdf_content,
        check_document_changes,
        # Dev 3 - Sauvegarde
        save_document_to_db,
    ]