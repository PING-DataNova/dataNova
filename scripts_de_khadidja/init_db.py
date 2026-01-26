"""
Script d'initialisation de la base de données

Crée toutes les tables et peut charger des données de test
"""

import sys
import os

# Ajouter le dossier parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.database import init_db, get_session
from src.storage.repositories import CompanyProfileRepository
from src.storage.models import CompanyProfile
import json


def load_test_company_profiles():
    """Charger les profils entreprise de test depuis data/company_profiles/"""
    print("\n📦 Chargement des profils entreprise de test...")
    
    session = get_session()
    repo = CompanyProfileRepository(session)
    
    # Dossier des profils
    profiles_dir = os.path.join(
        os.path.dirname(__file__),
        "../data/company_profiles"
    )
    
    if not os.path.exists(profiles_dir):
        print("⚠️  Aucun dossier data/company_profiles trouvé")
        session.close()
        return
    
    # Charger les fichiers JSON
    for filename in os.listdir(profiles_dir):
        if not filename.endswith(".json"):
            continue
        
        filepath = os.path.join(profiles_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extraire le nom (soit "company_name" soit "name")
            company_name = data.get("company_name") or data.get("name", "Unknown")
            
            # Vérifier si le profil existe déjà
            existing = repo.find_by_name(company_name)
            if existing:
                print(f"⏩ {company_name} - déjà existant, ignoré")
                continue
            
            # Extraire les codes NC et mots-clés s'ils existent
            nc_codes = data.get("nc_codes", [])
            keywords = data.get("keywords", [])
            
            # Si pas de nc_codes/keywords dans le JSON, on met des valeurs par défaut
            if not nc_codes:
                nc_codes = []
            if not keywords:
                keywords = []
            
            # Créer le profil
            profile = CompanyProfile(
                company_name=company_name,
                nc_codes=nc_codes,
                keywords=keywords,
                regulations=data.get("regulations", ["CBAM"]),
                contact_emails=data.get("contact_emails", []),
                config=data.get("config", {}),
                active=True
            )
            
            repo.save(profile)
            session.commit()
            print(f"✅ {company_name} - profil créé")
        
        except Exception as e:
            print(f"❌ Erreur lors du chargement de {filename}: {e}")
            session.rollback()
    
    session.close()
    print("✅ Profils entreprise chargés\n")


def main():
    """Point d'entrée principal"""
    print("=" * 60)
    print("🚀 Initialisation de la base de données Agent 1")
    print("=" * 60)
    
    # Créer les tables
    init_db()
    
    # Charger les données de test (optionnel)
    load_test = input("\n📦 Charger les profils entreprise de test ? (o/n): ")
    if load_test.lower() in ['o', 'y', 'oui', 'yes']:
        load_test_company_profiles()
    
    print("=" * 60)
    print("✅ Initialisation terminée avec succès!")
    print("=" * 60)


if __name__ == "__main__":
    main()
