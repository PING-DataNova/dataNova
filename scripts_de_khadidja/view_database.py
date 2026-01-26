"""Script pour visualiser l'état de la base de données."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import SessionLocal
from src.storage.models import Document, Analysis, CompanyProfile

def view_database():
    """Afficher le contenu de la base de données."""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("📊 ÉTAT DE LA BASE DE DONNÉES")
        print("=" * 80)
        
        # Documents
        documents = db.query(Document).all()
        print(f"\n📄 DOCUMENTS ({len(documents)})")
        print("-" * 80)
        for doc in documents:
            print(f"  ID: {doc.id}")
            print(f"  Titre: {doc.title}")
            print(f"  Status: {doc.status}")
            print(f"  Codes NC: {', '.join(doc.nc_codes)}")
            print(f"  Créé le: {doc.created_at}")
            print()
        
        # Analyses par statut
        pending = db.query(Analysis).filter(Analysis.validation_status == "pending").all()
        approved = db.query(Analysis).filter(Analysis.validation_status == "approved").all()
        rejected = db.query(Analysis).filter(Analysis.validation_status == "rejected").all()
        
        print(f"\n📋 ANALYSES")
        print("-" * 80)
        print(f"  ⏳ En attente (pending): {len(pending)}")
        print(f"  ✅ Approuvées (approved): {len(approved)}")
        print(f"  ❌ Rejetées (rejected): {len(rejected)}")
        print(f"  📊 Total: {len(pending) + len(approved) + len(rejected)}")
        
        if pending:
            print(f"\n⏳ ANALYSES EN ATTENTE DE VALIDATION:")
            print("-" * 80)
            for analysis in pending:
                print(f"  ID: {analysis.id}")
                print(f"  Document ID: {analysis.document_id}")
                print(f"  Pertinent: {analysis.is_relevant}")
                print(f"  Confiance: {analysis.confidence:.2f}")
                print(f"  Raisonnement: {analysis.llm_reasoning[:100] if analysis.llm_reasoning else 'N/A'}...")
                print(f"  Codes NC: {', '.join(analysis.matched_nc_codes) if analysis.matched_nc_codes else 'N/A'}")
                print(f"  Mots-clés: {', '.join(analysis.matched_keywords) if analysis.matched_keywords else 'N/A'}")
                print(f"  Créé le: {analysis.created_at}")
                print()
        
        if approved:
            print(f"\n✅ ANALYSES APPROUVÉES:")
            print("-" * 80)
            for analysis in approved:
                print(f"  ID: {analysis.id} - Document: {analysis.document_id}")
                print(f"  Raisonnement: {analysis.llm_reasoning[:80] if analysis.llm_reasoning else 'N/A'}...")
                print()
        
        if rejected:
            print(f"\n❌ ANALYSES REJETÉES:")
            print("-" * 80)
            for analysis in rejected:
                print(f"  ID: {analysis.id} - Document: {analysis.document_id}")
                print(f"  Raisonnement: {analysis.llm_reasoning[:80] if analysis.llm_reasoning else 'N/A'}...")
                print()
        
        # Profils
        profiles = db.query(CompanyProfile).all()
        if profiles:
            print(f"\n🏢 PROFILS ENTREPRISE ({len(profiles)})")
            print("-" * 80)
            for profile in profiles:
                print(f"  ID: {profile.id}")
                print(f"  Nom: {profile.name}")
                print(f"  Secteur: {profile.industry_sector}")
                print(f"  Codes NC: {', '.join(profile.nc_codes)}")
                print()
        
        print("=" * 80)
        
    finally:
        db.close()

if __name__ == "__main__":
    view_database()
