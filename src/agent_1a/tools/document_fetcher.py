"""
TODO: Outil de téléchargement de documents (LangChain @tool)

Tâches:
1. Décorer avec @tool
2. Télécharger PDF/HTML depuis EUR-Lex
3. Gérer les redirections
4. Sauvegarder localement avec hash
5. Détecter les changements (compare hash)

Formats:
- PDF
- HTML
- XML (optionnel)
"""

"""
Document Fetcher - Téléchargement de documents réglementaires

Responsable: Dev 1
"""
from langchain.tools import tool
import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

import httpx
import structlog
from pydantic import BaseModel, HttpUrl

logger = structlog.get_logger()


class FetchedDocument(BaseModel):
    """Modèle pour un document téléchargé"""
    url: HttpUrl
    file_path: str
    hash_sha256: str
    file_size: int
    content_type: Optional[str] = None
    status: str
    downloaded_at: datetime
    metadata: Dict[str, Any] = {}


class FetchResult(BaseModel):
    """Résultat du téléchargement"""
    url: HttpUrl
    success: bool
    document: Optional[FetchedDocument] = None
    error: Optional[str] = None


async def fetch_document(
    url: str,
    output_dir: str = "data/documents",
    filename: Optional[str] = None,
    timeout: int = 60
) -> FetchResult:
    """
    Télécharge un document depuis une URL et le sauvegarde localement.
    
    Args:
        url: URL du document à télécharger
        output_dir: Dossier de destination
        filename: Nom du fichier (optionnel, sinon généré depuis l'URL)
        timeout: Timeout en secondes
    
    Returns:
        FetchResult: Résultat du téléchargement avec métadonnées
    """
    logger.info("fetch_started", url=url, output_dir=output_dir)
    
    try:
        # Créer le dossier de destination s'il n'existe pas
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Télécharger le document
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            limits=httpx.Limits(max_connections=5)
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            content = response.content
            content_type = response.headers.get("content-type", "")
            
        # Générer le nom du fichier si non fourni
        if not filename:
            filename = _generate_filename(url, content_type)
        
        # Nettoyer le nom du fichier
        filename = _sanitize_filename(filename)
        
        # Chemin complet du fichier
        file_path = output_path / filename
        
        # Calculer le hash SHA-256
        hash_sha256 = hashlib.sha256(content).hexdigest()
        
        # Sauvegarder le fichier
        with open(file_path, "wb") as f:
            f.write(content)
        
        file_size = len(content)
        
        logger.info(
            "fetch_completed",
            url=url,
            file_path=str(file_path),
            file_size=file_size,
            hash=hash_sha256[:16] + "..."
        )        # Créer le résultat
        document = FetchedDocument(
            url=url,
            file_path=str(file_path),
            hash_sha256=hash_sha256,
            file_size=file_size,
            content_type=content_type,
            status="success",
            downloaded_at=datetime.now(timezone.utc),
            metadata={
                "filename": filename,
                "extension": file_path.suffix
            }
        )
        
        return FetchResult(
            url=url,
            success=True,
            document=document
        )
        
    except httpx.HTTPError as e:
        logger.error("fetch_http_error", url=url, error=str(e))
        return FetchResult(
            url=url,
            success=False,
            error=f"HTTP Error: {str(e)}"
        )
    
    except Exception as e:
        logger.error("fetch_unexpected_error", url=url, error=str(e), exc_info=True)
        return FetchResult(
            url=url,
            success=False,
            error=f"Unexpected error: {str(e)}"
        )


def _generate_filename(url: str, content_type: str) -> str:
    """
    Génère un nom de fichier depuis l'URL ou le content-type.
    
    Args:
        url: URL du document
        content_type: Type MIME du contenu
    
    Returns:
        str: Nom de fichier généré
    """
    # Essayer d'extraire le nom du fichier depuis l'URL
    url_parts = url.split("/")
    filename = url_parts[-1].split("?")[0]  # Retirer les query params
    
    # Si le nom contient une extension, l'utiliser
    if "." in filename and len(filename.split(".")[-1]) <= 5:
        return filename
    
    # Sinon, générer un nom basé sur le hash de l'URL + extension depuis content-type
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    
    # Déterminer l'extension depuis le content-type
    extension = _get_extension_from_content_type(content_type)
    
    return f"document_{url_hash}{extension}"


def _get_extension_from_content_type(content_type: str) -> str:
    """
    Détermine l'extension de fichier depuis le Content-Type.
    
    Args:
        content_type: Type MIME du contenu
    
    Returns:
        str: Extension (ex: .pdf, .html, .xml)
    """
    content_type_map = {
        "application/pdf": ".pdf",
        "text/html": ".html",
        "application/xml": ".xml",
        "text/xml": ".xml",
        "application/json": ".json",
        "text/plain": ".txt",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    }
    
    # Extraire le type principal (avant le ;)
    main_type = content_type.split(";")[0].strip().lower()
    
    return content_type_map.get(main_type, ".bin")


def _sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier en retirant les caractères non valides.
    
    Args:
        filename: Nom de fichier à nettoyer
    
    Returns:
        str: Nom de fichier nettoyé
    """
    # Remplacer les caractères non valides par des underscores
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    
    # Limiter la longueur à 200 caractères
    if len(filename) > 200:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[:190] + (f".{ext}" if ext else "")
    
    return filename


def fetch_document_sync(
    url: str,
    output_dir: str = "data/documents",
    filename: Optional[str] = None,
    timeout: int = 60
) -> FetchResult:
    """Version synchrone du fetcher (pour compatibilité)."""
    import asyncio
    return asyncio.run(fetch_document(url, output_dir, filename, timeout))


# Pour tester le module directement
if __name__ == "__main__":
    import asyncio
    
    # URL de test (un document CBAM)
    test_url = "https://taxation-customs.ec.europa.eu/document/download/74a278ac-6212-4a3d-bd3b-060a32dab8d6_en?filename=IA%20on%20Methodology_0.pdf"
    
    # Tester le téléchargement
    result = asyncio.run(fetch_document(test_url))
    
    if result.success:
        print(f"\n✅ Téléchargement réussi !")
        print(f"Fichier: {result.document.file_path}")
        print(f"Taille: {result.document.file_size} bytes")
        print(f"Hash: {result.document.hash_sha256}")
        print(f"Type: {result.document.content_type}")
    else:
        print(f"\n❌ Erreur: {result.error}")

@tool
async def fetch_document_tool(url: str, output_dir: str = "data/documents") -> str:
    """Télécharge document. Retourne JSON: {file_path,hash_sha256,file_size}"""
    result = await fetch_document(url, output_dir)
    
    if result.success and result.document:
        return json.dumps({
            "success": True,
            "url": str(result.url),
            "file_path": result.document.file_path,
            "hash_sha256": result.document.hash_sha256,
            "file_size": result.document.file_size,
            "content_type": result.document.content_type,
            "error": None
        }, ensure_ascii=False, indent=2)
    else:
        return json.dumps({
            "success": False,
            "url": str(result.url),
            "file_path": None,
            "hash_sha256": None,
            "file_size": None,
            "content_type": None,
            "error": result.error
        }, ensure_ascii=False, indent=2)