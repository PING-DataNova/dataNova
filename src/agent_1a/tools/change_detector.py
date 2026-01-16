"""
Change Detector - Agent 1A Tool
Détecte si un document est nouveau, modifié ou inchangé

Compare le hash SHA-256 du contenu téléchargé avec celui stocké en DB.
Permet d'éviter de ré-extraire des documents inchangés.
"""

import hashlib
import logging
from typing import Dict, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ChangeDetector:
    """
    Détecte les changements dans les documents réglementaires.
    
    Compare le hash SHA-256 du nouveau contenu avec celui en base de données
    pour déterminer si un document est nouveau, modifié ou inchangé.
    
    Usage:
        detector = ChangeDetector(session)
        result = detector.detect(hash_sha256, source_url)
        # result = {"status": "new|modified|unchanged", "existing_id": ...}
    """
    
    def __init__(self, session: Session):
        """
        Initialise le détecteur avec une session DB.
        
        Args:
            session: Session SQLAlchemy active
        """
        self.session = session
        # Import ici pour éviter circular imports
        from src.storage.repositories import DocumentRepository
        self.repo = DocumentRepository(session)
        logger.info("✅ ChangeDetector initialized")
    
    def detect(self, document_hash: str, source_url: str) -> Dict[str, any]:
        """
        Détecte si un document est nouveau, modifié ou inchangé.
        
        Args:
            document_hash: Hash SHA-256 du nouveau contenu téléchargé
            source_url: URL source du document (EUR-Lex)
        
        Returns:
            dict: {
                "status": "new" | "modified" | "unchanged",
                "existing_id": str | None,
                "old_hash": str | None
            }
        """
        logger.info(f"🔍 Checking changes for: {source_url[:60]}...")
        
        try:
            # 1. Chercher document existant par URL
            existing = self.repo.find_by_url(source_url)
            
            if existing is None:
                # Document jamais vu → NOUVEAU
                logger.info(f"   └─ Status: NEW (first time seen)")
                return {
                    "status": "new",
                    "existing_id": None,
                    "old_hash": None
                }
            
            if existing.hash_sha256 == document_hash:
                # Même hash → INCHANGÉ
                logger.info(f"   └─ Status: UNCHANGED (hash match)")
                return {
                    "status": "unchanged",
                    "existing_id": existing.id,
                    "old_hash": existing.hash_sha256
                }
            
            else:
                # Hash différent → MODIFIÉ
                logger.info(f"   └─ Status: MODIFIED (hash changed)")
                logger.debug(f"      Old hash: {existing.hash_sha256[:16]}...")
                logger.debug(f"      New hash: {document_hash[:16]}...")
                return {
                    "status": "modified",
                    "existing_id": existing.id,
                    "old_hash": existing.hash_sha256
                }
        
        except Exception as e:
            logger.error(f"❌ Change detection error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "existing_id": None,
                "old_hash": None
            }
    
    def detect_by_hash_only(self, document_hash: str) -> Dict[str, any]:
        """
        Détecte si un document existe déjà en cherchant uniquement par hash.
        
        Utile quand on n'a pas encore l'URL (ex: contenu uploadé manuellement).
        
        Args:
            document_hash: Hash SHA-256 du contenu
        
        Returns:
            dict: {"exists": bool, "existing_id": str | None}
        """
        existing = self.repo.find_by_hash(document_hash)
        
        if existing:
            return {
                "exists": True,
                "existing_id": existing.id,
                "source_url": existing.source_url
            }
        
        return {
            "exists": False,
            "existing_id": None,
            "source_url": None
        }
    
    @staticmethod
    def calculate_hash(content: str) -> str:
        """
        Calcule le hash SHA-256 d'un contenu texte.
        
        Args:
            content: Texte du document
        
        Returns:
            str: Hash SHA-256 (64 caractères hexadécimaux)
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def calculate_hash_from_bytes(content_bytes: bytes) -> str:
        """
        Calcule le hash SHA-256 d'un contenu binaire (PDF).
        
        Args:
            content_bytes: Contenu binaire du fichier
        
        Returns:
            str: Hash SHA-256 (64 caractères hexadécimaux)
        """
        return hashlib.sha256(content_bytes).hexdigest()
