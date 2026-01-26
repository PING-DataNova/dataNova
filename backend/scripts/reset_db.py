"""
Script de réinitialisation complète de la base de données

Supprime toutes les données et recrée les tables
"""

import sys
import os

# Ajouter le dossier parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.database import engine, Base
from src.storage.models import (
    Document, Analysis, ImpactAssessment, Alert, 
    ExecutionLog, CompanyProfile
)

def reset_database():
    """Supprime toutes les tables et les recrée"""
    print("=" * 60)
    print("⚠️  RÉINITIALISATION DE LA BASE DE DONNÉES")
    print("=" * 60)
    
    confirm = input("\n⚠️  ATTENTION : Toutes les données seront SUPPRIMÉES !\nContinuer ? (oui/non): ")
    
    if confirm.lower() not in ['oui', 'yes', 'o', 'y']:
        print("\n❌ Opération annulée")
        return
    
    print("\n🗑️  Suppression de toutes les tables...")
    
    try:
        # Supprimer toutes les tables
        Base.metadata.drop_all(bind=engine)
        print("✅ Tables supprimées")
        
        # Recréer toutes les tables
        print("\n🔨 Recréation des tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables créées")
        
        print("\n" + "=" * 60)
        print("✅ Base de données réinitialisée avec succès !")
        print("=" * 60)
        
        print("\n💡 Prochaine étape :")
        print("   python scripts/init_db.py")
        print("   (pour charger les profils entreprise)")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la réinitialisation : {e}")
        sys.exit(1)


if __name__ == "__main__":
    reset_database()
