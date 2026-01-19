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
            
            # Extraire le nom (support structure imbriquée et simple)
            company_name = (
                data.get("company_name") or 
                data.get("name") or
                (data.get("company", {}).get("company_name")) or
                (data.get("company", {}).get("legal_name")) or
                "Unknown"
            )
            
            # Vérifier si le profil existe déjà
            existing = repo.find_by_name(company_name)
            if existing:
                print(f"⏩ {company_name} - déjà existant, ignoré")
                continue
            
            # Extraire les codes NC (support structure imbriquée)
            nc_codes = data.get("nc_codes", {})
            if isinstance(nc_codes, dict):
                # Structure imbriquée avec imports/exports
                nc_codes_list = []
                for imp in nc_codes.get("imports", []):
                    if isinstance(imp, dict):
                        nc_codes_list.append(imp.get("code"))
                    else:
                        nc_codes_list.append(imp)
                for exp in nc_codes.get("exports", []):
                    if isinstance(exp, dict):
                        nc_codes_list.append(exp.get("code"))
                    else:
                        nc_codes_list.append(exp)
                nc_codes = nc_codes_list if nc_codes_list else []
            elif not isinstance(nc_codes, list):
                nc_codes = []
            
            # Extraire ou générer les mots-clés
            keywords = data.get("keywords", [])
            if not isinstance(keywords, list) or not keywords:
                # Générer automatiquement depuis les données
                keywords_set = set()
                
                # Depuis industry segments
                company = data.get("company", {})
                industry = company.get("industry", {})
                segments = industry.get("segments", [])
                for segment in segments:
                    if isinstance(segment, str):
                        # Extraire mots-clés du segment
                        words = segment.lower().replace("&", "").split()
                        keywords_set.update([w for w in words if len(w) > 3])
                
                # Depuis products
                products = data.get("products", [])
                for product in products:
                    if isinstance(product, str):
                        # Mots-clés des produits
                        if "caoutchouc" in product.lower() or "rubber" in product.lower():
                            keywords_set.add("caoutchouc")
                        if "étanchéité" in product.lower() or "seal" in product.lower():
                            keywords_set.add("étanchéité")
                        if "vibration" in product.lower():
                            keywords_set.add("vibration")
                        if "flexible" in product.lower() or "hose" in product.lower():
                            keywords_set.add("flexibles")
                        if "aéro" in product.lower() or "aerospace" in product.lower():
                            keywords_set.add("aéronautique")
                
                # Depuis supply_chain
                supply_chain = data.get("supply_chain", {})
                if "natural_rubber" in supply_chain:
                    keywords_set.add("caoutchouc_naturel")
                if "synthetic_rubber" in supply_chain:
                    keywords_set.add("caoutchouc_synthétique")
                if "metals_and_additives" in supply_chain:
                    keywords_set.add("métaux")
                    keywords_set.add("additifs")
                
                # Depuis sector
                sector = industry.get("sector", "")
                if sector:
                    keywords_set.add(sector.split()[0].lower() if sector else "")
                
                # Limiter à 15 mots-clés pertinents
                keywords = sorted([k for k in keywords_set if k and len(k) > 2])[:15]
            
            # Extraire les réglementations (support structure imbriquée)
            regulations = data.get("regulations", ["CBAM"])
            if isinstance(regulations, dict):
                # Structure imbriquée avec critical/high/medium
                reg_list = []
                for level in ["critical", "high", "medium"]:
                    for reg in regulations.get(level, []):
                        if isinstance(reg, dict):
                            name = reg.get("name") or reg.get("full_name", "")
                            if name and name not in reg_list:
                                reg_list.append(name)
                        elif reg and reg not in reg_list:
                            reg_list.append(reg)
                regulations = reg_list if reg_list else ["CBAM"]
            elif not isinstance(regulations, list):
                regulations = ["CBAM"]
            
            # Extraire les emails de contact
            contact_emails = data.get("contact_emails", [])
            if not isinstance(contact_emails, list) or not contact_emails:
                # Essayer d'extraire depuis internal_contacts
                internal_contacts = data.get("internal_contacts", {})
                if isinstance(internal_contacts, dict):
                    emails = []
                    # Parcourir toutes les sections de contacts
                    for key, contacts in internal_contacts.items():
                        if isinstance(contacts, list):
                            # Liste de contacts
                            for contact in contacts:
                                if isinstance(contact, dict) and "email" in contact:
                                    email = contact["email"]
                                    if email and email not in emails:
                                        emails.append(email)
                        elif isinstance(contacts, dict):
                            # Objet avec service_owner ou team
                            if "service_owner" in contacts and isinstance(contacts["service_owner"], dict):
                                email = contacts["service_owner"].get("email")
                                if email and email not in emails:
                                    emails.append(email)
                            if "team" in contacts and isinstance(contacts["team"], list):
                                for member in contacts["team"]:
                                    if isinstance(member, dict) and "email" in member:
                                        email = member["email"]
                                        if email and email not in emails:
                                            emails.append(email)
                    # Limiter à 5 emails principaux pour éviter surcharge
                    contact_emails = emails[:5] if emails else []
            
            # Créer le profil
            profile = CompanyProfile(
                company_name=company_name,
                nc_codes=nc_codes,
                keywords=keywords,
                regulations=regulations,  # Déjà une liste de strings
                contact_emails=contact_emails,  # ✅ Utiliser la variable extraite
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
