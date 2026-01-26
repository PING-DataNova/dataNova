"""
TODO: Outil de détection de changements (LangChain @tool)

Tâches:
1. Décorer avec @tool
2. Calculer hash SHA-256 des documents
3. Comparer avec base de données
4. Identifier: nouveau / modifié / inchangé
5. Retourner liste des changements
"""
"""
Change Detector - Détection de modifications de documents

Compare les hash SHA-256 pour identifier les changements.
Responsable: Dev 1
"""
from langchain.tools import tool
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import structlog
from pydantic import BaseModel

logger = structlog.get_logger()


class DocumentChange(BaseModel):
    """Modèle pour un changement de document détecté"""
    url: str
    current_hash: str
    previous_hash: Optional[str] = None
    status: str  # "new", "modified", "unchanged"
    detected_at: datetime


class ChangeDetectionResult(BaseModel):
    """Résultat de la détection de changements"""
    url: str
    changes: List[DocumentChange]
    new_count: int
    modified_count: int
    unchanged_count: int
    status: str
    error: Optional[str] = None


async def detect_changes(
    documents: List[dict],
    existing_hashes: dict = None
) -> ChangeDetectionResult:
    """
    Détecte les changements dans une liste de documents.
    
    Args:
        documents: Liste de documents avec URL et hash
        existing_hashes: Dict {url: hash_sha256} des documents existants
    
    Returns:
        ChangeDetectionResult: Résultat de la détection avec statistiques
    """
    logger.info("change_detection_started", total_documents=len(documents))
    
    if existing_hashes is None:
        existing_hashes = {}
    
    changes = []
    new_count = 0
    modified_count = 0
    unchanged_count = 0
    
    try:
        for doc in documents:
            url = doc.get("url")
            current_hash = doc.get("hash_sha256")
            
            if not url or not current_hash:
                continue
            
            previous_hash = existing_hashes.get(url)
            
            # Déterminer le statut
            if previous_hash is None:
                status = "new"
                new_count += 1
            elif previous_hash != current_hash:
                status = "modified"
                modified_count += 1
            else:
                status = "unchanged"
                unchanged_count += 1
            
            change = DocumentChange(
                url=url,
                current_hash=current_hash,
                previous_hash=previous_hash,
                status=status,
                detected_at=datetime.utcnow()
            )
            changes.append(change)
        
        logger.info(
            "change_detection_completed",
            total=len(documents),
            new=new_count,
            modified=modified_count,
            unchanged=unchanged_count
        )
        
        return ChangeDetectionResult(
            url="batch",
            changes=changes,
            new_count=new_count,
            modified_count=modified_count,
            unchanged_count=unchanged_count,
            status="success"
        )
        
    except Exception as e:
        logger.error("change_detection_error", error=str(e), exc_info=True)
        return ChangeDetectionResult(
            url="batch",
            changes=[],
            new_count=0,
            modified_count=0,
            unchanged_count=0,
            status="error",
            error=f"Detection error: {str(e)}"
        )


def calculate_file_hash(file_path: str) -> str:
    """
    Calcule le hash SHA-256 d'un fichier.
    
    Args:
        file_path: Chemin vers le fichier
    
    Returns:
        str: Hash SHA-256 en hexadécimal
    """
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        # Lire par blocs de 8KB pour économiser la mémoire
        for byte_block in iter(lambda: f.read(8192), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()


async def compare_with_database(
    document_url: str,
    current_hash: str,
    db_hash: Optional[str] = None
) -> DocumentChange:
    """
    Compare un document avec sa version en base de données.
    
    Args:
        document_url: URL du document
        current_hash: Hash actuel du document
        db_hash: Hash stocké en base de données (None si nouveau)
    
    Returns:
        DocumentChange: Résultat de la comparaison
    """
    if db_hash is None:
        status = "new"
    elif db_hash != current_hash:
        status = "modified"
    else:
        status = "unchanged"
    
    return DocumentChange(
        url=document_url,
        current_hash=current_hash,
        previous_hash=db_hash,
        status=status,
        detected_at=datetime.utcnow()
    )


def detect_changes_sync(
    documents: List[dict],
    existing_hashes: dict = None
) -> ChangeDetectionResult:
    """Version synchrone du détecteur (pour compatibilité)."""
    import asyncio
    return asyncio.run(detect_changes(documents, existing_hashes))


# Pour tester le module directement
if __name__ == "__main__":
    import asyncio
    
    print("=" * 80)
    print("🔍 TEST CHANGE DETECTOR")
    print("=" * 80)
    
    # Simulation : Base de données avec des hash existants
    existing_hashes = {
        "https://example.com/doc1.pdf": "abc123hash",
        "https://example.com/doc2.pdf": "def456hash",
        "https://example.com/doc3.pdf": "ghi789hash",
    }
    
    # Simulation : Nouveaux documents scrapés
    new_documents = [
        # Document inchangé (même hash)
        {
            "url": "https://example.com/doc1.pdf",
            "hash_sha256": "abc123hash",
            "title": "Document 1 (inchangé)"
        },
        # Document modifié (hash différent)
        {
            "url": "https://example.com/doc2.pdf",
            "hash_sha256": "def456NEW",
            "title": "Document 2 (modifié)"
        },
        # Document nouveau (pas dans la BDD)
        {
            "url": "https://example.com/doc4.pdf",
            "hash_sha256": "jkl012hash",
            "title": "Document 4 (nouveau)"
        },
    ]
    
    # Tester la détection
    result = asyncio.run(detect_changes(new_documents, existing_hashes))
    
    print(f"\n📊 RÉSULTATS")
    print("-" * 80)
    print(f"Total analysé: {len(new_documents)}")
    print(f"🆕 Nouveaux: {result.new_count}")
    print(f"✏️  Modifiés: {result.modified_count}")
    print(f"✅ Inchangés: {result.unchanged_count}")
    
    print(f"\n📋 DÉTAILS")
    print("-" * 80)
    for change in result.changes:
        icon = {"new": "🆕", "modified": "✏️", "unchanged": "✅"}[change.status]
        print(f"{icon} {change.status.upper()}: {change.url}")
        print(f"   Hash actuel: {change.current_hash[:16]}...")
        if change.previous_hash:
            print(f"   Hash précédent: {change.previous_hash[:16]}...")
    
    print("\n" + "=" * 80)
    print("✅ Test terminé !")
    print("=" * 80)
    
    # Test du calcul de hash sur un fichier réel
    test_file = "data/documents/document_332f671132b3.pdf"
    if Path(test_file).exists():
        print(f"\n🔐 Test calcul hash sur fichier réel:")
        file_hash = calculate_file_hash(test_file)
        print(f"Fichier: {test_file}")
        print(f"Hash: {file_hash}")

@tool
async def detect_changes_tool(documents_json: str, existing_hashes_json: str = "{}") -> str:
    """
    Détecte les changements dans une liste de documents (nouveaux, modifiés, inchangés).
    
    Args:
        documents_json: JSON string avec liste de documents [{"url": "...", "hash_sha256": "..."}]
        existing_hashes_json: JSON string avec hash existants {"url": "hash"}
    
    Returns:
        JSON string avec les statistiques de changements détectés
    """
    documents = json.loads(documents_json)
    existing_hashes = json.loads(existing_hashes_json)
    
    result = await detect_changes(documents, existing_hashes)
    
    return json.dumps({
        "status": result.status,
        "new_count": result.new_count,
        "modified_count": result.modified_count,
        "unchanged_count": result.unchanged_count,
        "changes": [
            {
                "url": change.url,
                "status": change.status,
                "current_hash": change.current_hash,
                "previous_hash": change.previous_hash
            }
            for change in result.changes
        ],
        "error": result.error
    }, ensure_ascii=False, indent=2)