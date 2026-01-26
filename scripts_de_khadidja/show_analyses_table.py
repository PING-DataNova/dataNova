"""Script pour voir la table analyses avec SQLAlchemy."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import SessionLocal
from src.storage.models import Analysis, Document

def show_analyses_table():
    """Afficher la table analyses avec tous les détails."""
    db = SessionLocal()
    
    try:
        print("\n" + "=" * 130)
        print("TABLE ANALYSES - Vue détaillée de la base de données")
        print("=" * 130)
        
        # Récupérer toutes les analyses
        analyses = db.query(Analysis).order_by(Analysis.validation_status, Analysis.created_at).all()
        
        print(f"\n{'ID (8 car.)':<12} {'Doc ID (8 car.)':<14} {'Status':<12} {'Pertinent':<10} {'Conf.':<6} {'Titre du document'}")
        print("-" * 130)
        
        for analysis in analyses:
            # Récupérer le document associé
            document = db.query(Document).filter(Document.id == analysis.document_id).first()
            
            # Formater les données
            id_short = analysis.id[:8]
            doc_id_short = analysis.document_id[:8]
            status = analysis.validation_status
            relevant = "Oui" if analysis.is_relevant else "Non"
            confidence = f"{analysis.confidence:.2f}"
            title = (document.title[:70] + "...") if document and len(document.title) > 70 else (document.title if document else "N/A")
            
            print(f"{id_short:<12} {doc_id_short:<14} {status:<12} {relevant:<10} {confidence:<6} {title}")
        
        # Statistiques
        print("\n" + "=" * 130)
        print("STATISTIQUES PAR STATUT DE VALIDATION")
        print("=" * 130)
        
        from sqlalchemy import func
        stats = db.query(
            Analysis.validation_status,
            func.count(Analysis.id)
        ).group_by(Analysis.validation_status).all()
        
        total = sum(count for _, count in stats)
        
        for status, count in sorted(stats, key=lambda x: x[0]):
            percentage = (count / total * 100) if total > 0 else 0
            bar = "#" * int(percentage / 5)  # Barre de progression
            print(f"{status.upper():<12} : {count:>2} analyses ({percentage:>5.1f}%) {bar}")
        
        print(f"\nTOTAL: {total} analyses dans la base de données")
        
        # Détails de la dernière analyse modifiée
        print("\n" + "=" * 130)
        print("DÉTAILS DE LA DERNIÈRE ANALYSE APPROUVÉE")
        print("=" * 130)
        
        last_approved = db.query(Analysis).filter(
            Analysis.validation_status == 'approved'
        ).order_by(Analysis.created_at.desc()).first()
        
        if last_approved:
            doc = db.query(Document).filter(Document.id == last_approved.document_id).first()
            print(f"\nID complet: {last_approved.id}")
            print(f"Document: {doc.title if doc else 'N/A'}")
            print(f"Pertinence: {'Oui' if last_approved.is_relevant else 'Non'}")
            print(f"Confiance: {last_approved.confidence:.2f}")
            print(f"Codes NC: {', '.join(last_approved.matched_nc_codes) if last_approved.matched_nc_codes else 'Aucun'}")
            print(f"Mots-clés: {', '.join(last_approved.matched_keywords) if last_approved.matched_keywords else 'Aucun'}")
            print(f"\nRaisonnement LLM:")
            reasoning = last_approved.llm_reasoning if last_approved.llm_reasoning else "N/A"
            print(f"  {reasoning[:300]}{'...' if len(reasoning) > 300 else ''}")
        
        print("\n" + "=" * 130 + "\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    show_analyses_table()
