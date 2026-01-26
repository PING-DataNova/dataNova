"""
Script de test du workflow de validation
Vérifie que le changement de statut fonctionne end-to-end
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.database import get_session
from src.storage.models import Analysis, Document
from sqlalchemy import func

def print_separator():
    print("\n" + "="*80 + "\n")

def show_all_regulations():
    """Affiche toutes les régulations avec leur statut"""
    session = get_session()
    
    analyses = session.query(Analysis).join(Document).all()
    
    print("📋 ÉTAT ACTUEL DES RÉGULATIONS")
    print(f"Total: {len(analyses)} analyses")
    print_separator()
    
    for i, analysis in enumerate(analyses, 1):
        doc = analysis.document
        print(f"{i}. {doc.title[:60]}")
        print(f"   ID: {analysis.id}")
        print(f"   Status: {analysis.validation_status.upper()}")
        print(f"   Document: {doc.regulation_type}")
        if analysis.validated_by:
            print(f"   Validé par: {analysis.validated_by} le {analysis.validated_at}")
        print()
    
    # Compteurs par statut
    print("📊 STATISTIQUES:")
    statuses = session.query(
        Analysis.validation_status, 
        func.count(Analysis.id)
    ).group_by(Analysis.validation_status).all()
    
    for status, count in statuses:
        print(f"   {status}: {count}")
    
    session.close()

def find_pending_regulation():
    """Trouve une régulation en attente pour test"""
    session = get_session()
    
    pending = session.query(Analysis).join(Document).filter(
        Analysis.validation_status == "pending"
    ).first()
    
    if pending:
        print(f"🔍 RÉGULATION EN ATTENTE TROUVÉE:")
        print(f"   ID: {pending.id}")
        print(f"   Titre: {pending.document.title}")
        print(f"   Status actuel: {pending.validation_status}")
        result = pending.id
    else:
        print("⚠️  Aucune régulation en attente trouvée")
        result = None
    
    session.close()
    return result

def test_status_update(analysis_id: str, new_status: str = "approved"):
    """Simule une mise à jour de statut via l'API"""
    session = get_session()
    
    analysis = session.query(Analysis).filter(Analysis.id == analysis_id).first()
    
    if not analysis:
        print(f"❌ Analyse {analysis_id} non trouvée")
        session.close()
        return False
    
    print_separator()
    print(f"🔄 TEST DE MISE À JOUR:")
    print(f"   ID: {analysis_id}")
    print(f"   Status AVANT: {analysis.validation_status}")
    
    # Simuler la mise à jour (comme le fait l'API)
    old_status = analysis.validation_status
    analysis.validation_status = new_status
    analysis.validated_by = "test@example.com"
    from datetime import datetime
    analysis.validated_at = datetime.utcnow()
    analysis.validation_comment = "Test de validation automatique"
    
    session.commit()
    
    print(f"   Status APRÈS: {analysis.validation_status}")
    print(f"   ✅ Mise à jour réussie!")
    
    session.close()
    return True

def verify_update(analysis_id: str):
    """Vérifie que la mise à jour a été persistée"""
    session = get_session()
    
    analysis = session.query(Analysis).filter(Analysis.id == analysis_id).first()
    
    print_separator()
    print(f"🔍 VÉRIFICATION:")
    print(f"   ID: {analysis_id}")
    print(f"   Status dans DB: {analysis.validation_status}")
    print(f"   Validé par: {analysis.validated_by}")
    print(f"   Date: {analysis.validated_at}")
    print(f"   Commentaire: {analysis.validation_comment}")
    
    session.close()

if __name__ == "__main__":
    print_separator()
    print("🧪 TEST DU WORKFLOW DE VALIDATION")
    print_separator()
    
    # 1. Afficher l'état initial
    show_all_regulations()
    print_separator()
    
    # 2. Trouver une régulation en attente
    pending_id = find_pending_regulation()
    
    if pending_id:
        input("\n⏸️  Appuyez sur Entrée pour tester la validation...")
        
        # 3. Mettre à jour le statut
        test_status_update(pending_id, "approved")
        
        # 4. Vérifier la persistance
        verify_update(pending_id)
        
        # 5. Afficher l'état final
        print_separator()
        show_all_regulations()
        
        print_separator()
        print("✅ TEST TERMINÉ!")
        print("\n💡 Maintenant, testez via l'UI:")
        print("   1. Ouvrez http://localhost:3001")
        print("   2. Cliquez sur 'Valider' sur une régulation")
        print("   3. Rechargez cette page")
        print("   4. Vérifiez que le statut a changé")
    else:
        print("\n⚠️  Impossible de tester: aucune régulation en attente")
