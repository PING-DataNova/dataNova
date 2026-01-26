"""Script pour ajouter des données de test pour la validation juridique."""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from src.storage.database import SessionLocal
from src.storage.models import Document, Analysis

def create_test_data():
    """Créer des documents et analyses de test."""
    db = SessionLocal()
    
    try:
        # Créer quelques documents
        doc1 = Document(
            title="Règlement CBAM 2026 - Secteur Acier",
            source_url="https://example.com/cbam-steel-2026",
            hash_sha256="abc123def456",
            content="Le nouveau règlement CBAM impose des restrictions sur les importations d'acier...",
            nc_codes=["7208", "7209", "7210"],
            regulation_type="CBAM",
            status="new",
            workflow_status="analyzed"
        )
        
        doc2 = Document(
            title="Directive Européenne - Aluminium",
            source_url="https://example.com/eu-aluminium-directive",
            hash_sha256="xyz789ghi012",
            content="Cette directive concerne les importations d'aluminium en provenance de Chine...",
            nc_codes=["7601", "7602"],
            regulation_type="EU_DIRECTIVE",
            status="new",
            workflow_status="analyzed"
        )
        
        doc3 = Document(
            title="Mise à jour CBAM - Ciment",
            source_url="https://example.com/cbam-cement-update",
            hash_sha256="cement456update",
            content="Nouvelles règles pour l'importation de ciment et produits dérivés...",
            nc_codes=["2523"],
            regulation_type="CBAM",
            status="modified",
            workflow_status="analyzed"
        )
        
        db.add_all([doc1, doc2, doc3])
        db.flush()
        
        # Créer des analyses en attente de validation
        analysis1 = Analysis(
            document_id=doc1.id,
            is_relevant=True,
            confidence=0.95,
            matched_keywords=["CBAM", "acier", "importation", "taxe carbone"],
            matched_nc_codes=["7208", "7209", "7210"],
            llm_reasoning="Impact majeur sur les importations d'acier. Les entreprises du secteur sidérurgique devront adapter leurs processus d'importation. Coûts supplémentaires estimés à 15% des transactions.",
            validation_status="pending"
        )
        
        analysis2 = Analysis(
            document_id=doc2.id,
            is_relevant=True,
            confidence=0.85,
            matched_keywords=["aluminium", "Chine", "directive", "importation"],
            matched_nc_codes=["7601", "7602"],
            llm_reasoning="Impact modéré sur le secteur de l'aluminium. Principalement pour les importations chinoises. Nécessite une révision des contrats fournisseurs.",
            validation_status="pending"
        )
        
        analysis3 = Analysis(
            document_id=doc3.id,
            is_relevant=True,
            confidence=0.70,
            matched_keywords=["CBAM", "ciment", "construction"],
            matched_nc_codes=["2523"],
            llm_reasoning="Faible impact sur le secteur du ciment. Concerne principalement les grandes quantités. Les PME sont peu affectées.",
            validation_status="pending"
        )
        
        # Ajouter une analyse déjà approuvée (pour test)
        analysis4 = Analysis(
            document_id=doc1.id,
            is_relevant=True,
            confidence=0.90,
            matched_keywords=["test"],
            matched_nc_codes=["7208"],
            llm_reasoning="Analyse précédente déjà validée.",
            validation_status="approved"
        )
        
        # Ajouter une analyse rejetée (pour test)
        analysis5 = Analysis(
            document_id=doc2.id,
            is_relevant=False,
            confidence=0.30,
            matched_keywords=["test"],
            matched_nc_codes=["7601"],
            llm_reasoning="Analyse rejetée car non pertinente.",
            validation_status="rejected"
        )
        
        db.add_all([analysis1, analysis2, analysis3, analysis4, analysis5])
        db.commit()
        
        print("✅ Données de test créées avec succès!")
        print(f"\n📊 Résumé:")
        print(f"  - 3 documents créés")
        print(f"  - 3 analyses en attente (pending)")
        print(f"  - 1 analyse approuvée (approved)")
        print(f"  - 1 analyse rejetée (rejected)")
        print(f"\n🔍 IDs des analyses en attente:")
        print(f"  - Analyse #{analysis1.id} - Acier (priorité: urgent)")
        print(f"  - Analyse #{analysis2.id} - Aluminium (priorité: normal)")
        print(f"  - Analyse #{analysis3.id} - Ciment (priorité: low)")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Création des données de test pour la validation juridique...")
    create_test_data()
