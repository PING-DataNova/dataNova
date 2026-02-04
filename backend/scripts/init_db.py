"""
Script d'initialisation de la base de donnees

Cree toutes les tables et peut charger des donnees de test
"""

import sys
import os
import json

# Ajouter le dossier parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.database import init_db, get_session
from src.storage.repositories import CompanyProfileRepository
from src.storage.models import CompanyProfile

# CompanyProcess model/repository may have been removed in some branches. Import defensively.
try:
    from src.storage.repositories import CompanyProcessRepository
    from src.storage.models import CompanyProcess
except Exception:
    CompanyProcessRepository = None
    CompanyProcess = None


def load_test_company_profiles():
    """Charger les profils entreprise de test depuis data/company_profiles/"""
    print("\nChargement des profils entreprise de test...")

    session = get_session()
    repo = CompanyProfileRepository(session)

    profiles_dir = os.path.join(
        os.path.dirname(__file__),
        "../data/company_profiles"
    )

    if not os.path.exists(profiles_dir):
        print("Aucun dossier data/company_profiles trouve")
        session.close()
        return

    for filename in os.listdir(profiles_dir):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(profiles_dir, filename)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extraire company_name depuis différentes structures possibles
            company_name = None
            if "company" in data:
                company_name = data["company"].get("company_name")
            if not company_name:
                company_name = data.get("company_name") or data.get("name", "Unknown")

            existing = repo.find_by_name(company_name)
            if existing:
                print(f"{company_name} - deja existant, ignore")
                continue

            # Map incoming test profile data to the current CompanyProfile model
            headquarters_country = data.get("headquarters_country") or data.get("country") or "Unknown"
            total_sites = len(data.get("sites", [])) if isinstance(data.get("sites", []), list) else None

            profile = CompanyProfile(
                company_name=company_name,
                headquarters_country=headquarters_country,
                total_sites=total_sites,
                total_suppliers=data.get("total_suppliers"),
                risk_tolerance=data.get("risk_tolerance", "medium"),
                notification_settings={"contact_emails": data.get("contact_emails", [])},
                data_sources_config=data.get("config", {}),
                llm_config=data.get("llm_config", {})
            )

            repo.save(profile)
            session.commit()
            print(f"{company_name} - profil cree")

        except Exception as e:
            print(f"Erreur lors du chargement de {filename}: {e}")
            session.rollback()

    session.close()
    print("Profils entreprise charges\n")


def load_test_company_processes():
    """Charger les donnees entreprise de test depuis data/company_processes/"""
    print("\nChargement des donnees entreprise de test...")

    if CompanyProcessRepository is None or CompanyProcess is None:
        print("CompanyProcess model/repository not available; skipping company_processes load.")
        return

    session = get_session()
    repo = CompanyProcessRepository(session)

    processes_dir = os.path.join(
        os.path.dirname(__file__),
        "../data/company_processes"
    )

    if not os.path.exists(processes_dir):
        print("Aucun dossier data/company_processes trouve")
        session.close()
        return

    for filename in os.listdir(processes_dir):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(processes_dir, filename)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            company_name = data.get("company_name") or data.get("name", "Unknown")

            existing = repo.find_by_name(company_name)
            if existing:
                print(f"{company_name} - deja existant, ignore")
                continue

            process = CompanyProcess(
                company_name=company_name,
                processes=data.get("processes", {}),
                transport_modes=data.get("transport_modes", {}),
                suppliers=data.get("suppliers", []),
                products=data.get("products", []),
                import_export_flows=data.get("import_export_flows", []),
                notes=data.get("notes", None),
            )

            repo.save(process)
            session.commit()
            print(f"{company_name} - donnees chargees")

        except Exception as e:
            print(f"Erreur lors du chargement de {filename}: {e}")
            session.rollback()

    session.close()
    print("Donnees entreprise chargees\n")


def main():
    """Point d'entree principal"""
    import sys
    auto_mode = "--auto" in sys.argv
    
    print("=" * 60)
    print("Initialisation de la base de donnees")
    print("=" * 60)

    init_db()

    if auto_mode:
        # Mode automatique (conteneur Docker)
        load_test_company_profiles()
        load_test_company_processes()
    else:
        # Mode interactif (dev local)
        load_test = input("\nCharger les profils entreprise de test ? (o/n): ")
        if load_test.lower() in ['o', 'y', 'oui', 'yes']:
            load_test_company_profiles()

        load_processes = input("\nCharger les donnees entreprise (company_processes) ? (o/n): ")
        if load_processes.lower() in ['o', 'y', 'oui', 'yes']:
            load_test_company_processes()

    print("=" * 60)
    print("Initialisation terminee avec succes!")
    print("=" * 60)


if __name__ == "__main__":
    main()
