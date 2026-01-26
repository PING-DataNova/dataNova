"""
Script pour approuver les analyses en attente
"""
from src.storage.database import get_session
from src.storage.models import Analysis

def approve_pending_analyses():
    """Approuve toutes les analyses en attente"""
    with get_session() as session:
        pending_analyses = session.query(Analysis).filter(
            Analysis.validation_status == "pending"
        ).all()
        
        if not pending_analyses:
            print("Aucune analyse en attente.")
            return
        
        print(f"📋 {len(pending_analyses)} analyses en attente trouvées")
        
        for analysis in pending_analyses:
            analysis.validation_status = "approved"
            analysis.validated_at = analysis.created_at
            analysis.validated_by = "admin"
            print(f"✅ Analyse {analysis.id[:8]} approuvée")
        
        session.commit()
        print(f"\n✅ {len(pending_analyses)} analyses approuvées avec succès!")

if __name__ == "__main__":
    approve_pending_analyses()
