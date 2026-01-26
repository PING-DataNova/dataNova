"""
Script de vérification rapide du statut des régulations
À exécuter PENDANT que le backend tourne pour vérifier les changements
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.database import get_session
from src.storage.models import Analysis, Document
from sqlalchemy import func
from datetime import datetime

def show_status():
    session = get_session()
    
    # Statistiques globales
    stats = session.query(
        Analysis.validation_status,
        func.count(Analysis.id)
    ).group_by(Analysis.validation_status).all()
    
    print("\n" + "="*70)
    print("📊 ÉTAT ACTUEL DE LA BASE DE DONNÉES")
    print("="*70)
    print(f"\n⏰ Vérification à : {datetime.now().strftime('%H:%M:%S')}\n")
    
    status_labels = {
        'pending': '⏳ En attente',
        'approved': '✅ Validées',
        'rejected': '❌ Rejetées'
    }
    
    total = 0
    for status, count in stats:
        label = status_labels.get(status, status)
        print(f"   {label:20} : {count}")
        total += count
    
    print(f"   {'─' * 25}")
    print(f"   {'TOTAL':20} : {total}\n")
    
    # Détails des régulations en attente
    pending = session.query(Analysis).join(Document).filter(
        Analysis.validation_status == 'pending'
    ).all()
    
    if pending:
        print("🔍 RÉGULATIONS EN ATTENTE DE VALIDATION:")
        print("─" * 70)
        for analysis in pending:
            print(f"\n   • {analysis.document.title[:60]}")
            print(f"     ID: {analysis.id}")
            print(f"     Type: {analysis.document.regulation_type}")
    else:
        print("✨ Aucune régulation en attente - Tout est validé!")
    
    # Dernières validations
    recent = session.query(Analysis).filter(
        Analysis.validation_status == 'approved',
        Analysis.validated_at.isnot(None)
    ).order_by(Analysis.validated_at.desc()).limit(3).all()
    
    if recent:
        print("\n\n📝 DERNIÈRES VALIDATIONS:")
        print("─" * 70)
        for analysis in recent:
            print(f"\n   • {analysis.document.title[:60]}")
            print(f"     Validé par: {analysis.validated_by or 'N/A'}")
            print(f"     Date: {analysis.validated_at.strftime('%Y-%m-%d %H:%M:%S') if analysis.validated_at else 'N/A'}")
            if analysis.validation_comment:
                print(f"     Commentaire: {analysis.validation_comment[:50]}...")
    
    print("\n" + "="*70 + "\n")
    
    session.close()

if __name__ == "__main__":
    try:
        show_status()
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        print("\n💡 Assurez-vous que le backend est démarré sur la branche backend_khadidja")
