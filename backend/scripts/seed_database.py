"""
Script de seed pour charger les données de test dans la base de données.

Ce script charge les données depuis test_data.json dans les tables :
- hutchinson_sites
- suppliers
- supplier_relationships
- data_sources (EUR-Lex, OpenMeteo, ACLED, WHO)

Usage:
    cd backend
    python scripts/seed_database.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import SessionLocal
from src.storage.models import HutchinsonSite, Supplier, SupplierRelationship, DataSource, CompanyProfile


def load_json_data(filepath: str) -> dict:
    """Charge les données depuis un fichier JSON."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def clear_tables(db):
    """Vide les tables avant de les remplir (ordre important pour les FK)."""
    print("🗑️  Suppression des données existantes...")
    db.query(SupplierRelationship).delete()
    db.query(Supplier).delete()
    db.query(HutchinsonSite).delete()
    db.query(DataSource).delete()
    db.query(CompanyProfile).delete()
    db.commit()
    print("   ✅ Tables vidées")


def seed_hutchinson_sites(db, sites_data: list) -> dict:
    """
    Insère les sites Hutchinson dans la BDD.
    Retourne un mapping id_json -> id_bdd pour les relations.
    """
    print(f"\n📍 Insertion de {len(sites_data)} sites Hutchinson...")
    id_mapping = {}
    
    for site in sites_data:
        # Mapper les champs du JSON vers le modèle
        db_site = HutchinsonSite(
            id=site.get('id'),
            name=site.get('name'),
            code=site.get('code'),
            country=site.get('country'),
            region=site.get('region'),
            city=site.get('city'),
            address=site.get('address'),
            latitude=site.get('latitude'),
            longitude=site.get('longitude'),
            sectors=site.get('sectors'),
            products=site.get('products'),
            raw_materials=site.get('raw_materials'),
            certifications=site.get('certifications'),
            employee_count=site.get('employee_count'),
            annual_production_value=site.get('annual_production_value'),
            strategic_importance=site.get('strategic_importance'),
            # Nouvelles colonnes Business Interruption
            daily_revenue=site.get('daily_revenue'),
            daily_production_units=site.get('daily_production_units'),
            safety_stock_days=site.get('safety_stock_days'),
            ramp_up_time_days=site.get('recovery_time_days'),  # recovery_time -> ramp_up_time
            key_customers=site.get('key_customers'),  # JSON directement
            extra_metadata=site.get('extra_metadata'),
            active=site.get('active', True)
        )
        db.add(db_site)
        id_mapping[site['id']] = site['id']
        print(f"   ✅ {site['name']} ({site['country']})")
    
    db.commit()
    return id_mapping


def seed_suppliers(db, suppliers_data: list) -> dict:
    """
    Insère les fournisseurs dans la BDD.
    Retourne un mapping id_json -> id_bdd pour les relations.
    """
    print(f"\n🏭 Insertion de {len(suppliers_data)} fournisseurs...")
    id_mapping = {}
    
    for supplier in suppliers_data:
        # Mapper financial_health_score vers financial_health (string)
        financial_score = supplier.get('financial_health_score', 0)
        if financial_score >= 0.85:
            financial_health = 'excellent'
        elif financial_score >= 0.70:
            financial_health = 'bon'
        elif financial_score >= 0.50:
            financial_health = 'moyen'
        else:
            financial_health = 'faible'
        
        db_supplier = Supplier(
            id=supplier.get('id'),
            name=supplier.get('name'),
            code=supplier.get('code'),
            country=supplier.get('country'),
            region=supplier.get('region'),
            city=supplier.get('city'),
            address=supplier.get('address'),
            latitude=supplier.get('latitude'),
            longitude=supplier.get('longitude'),
            sector=supplier.get('sector'),
            products_supplied=supplier.get('products_supplied'),
            company_size=supplier.get('company_size'),
            certifications=supplier.get('certifications'),
            financial_health=financial_health,
            # Nouvelles colonnes Business Interruption
            annual_purchase_volume=supplier.get('annual_purchase_volume_eur'),
            average_stock_at_hutchinson_days=supplier.get('average_stock_at_hutchinson_days'),
            switch_time_days=supplier.get('switch_time_days'),
            criticality_score=supplier.get('criticality_score'),
            extra_metadata=supplier.get('extra_metadata'),
            active=supplier.get('active', True)
        )
        db.add(db_supplier)
        id_mapping[supplier['id']] = supplier['id']
        print(f"   ✅ {supplier['name']} ({supplier['country']})")
    
    db.commit()
    return id_mapping


def seed_supplier_relationships(db, relationships_data: list, site_mapping: dict, supplier_mapping: dict):
    """Insère les relations site-fournisseur dans la BDD."""
    print(f"\n🔗 Insertion de {len(relationships_data)} relations fournisseur...")
    
    for rel in relationships_data:
        # Convertir annual_volume_eur en annual_volume
        annual_volume = rel.get('annual_volume_eur') or rel.get('annual_volume')
        
        # Convertir contract_end_date string en date
        contract_end = None
        if rel.get('contract_end_date'):
            try:
                contract_end = datetime.strptime(rel['contract_end_date'], '%Y-%m-%d').date()
            except:
                pass
        
        db_rel = SupplierRelationship(
            hutchinson_site_id=rel.get('hutchinson_site_id'),
            supplier_id=rel.get('supplier_id'),
            products_supplied=rel.get('products_supplied'),
            annual_volume=annual_volume,
            criticality=rel.get('criticality'),
            is_sole_supplier=rel.get('is_sole_supplier', False),
            has_backup_supplier=rel.get('has_backup_supplier', False),
            backup_supplier_id=rel.get('backup_supplier_id'),
            lead_time_days=rel.get('lead_time_days'),
            contract_end_date=contract_end,
            risk_mitigation_plan=rel.get('risk_mitigation_plan'),
            # Nouvelles colonnes Business Interruption
            daily_consumption_value=rel.get('daily_consumption_value_eur'),
            stock_coverage_days=rel.get('stock_coverage_days'),
            contract_penalties_per_day=rel.get('contract_penalties_per_day_eur'),
            extra_metadata=rel.get('extra_metadata'),
            active=True
        )
        db.add(db_rel)
        
        site_id = rel.get('hutchinson_site_id')
        supplier_id = rel.get('supplier_id')
        print(f"   ✅ {site_id} ↔ {supplier_id}")
    
    db.commit()


def seed_company_profiles(db):
    """
    Charge les profils entreprise depuis data/company_profiles/*.json
    Utilise le nouveau modèle CompanyProfile (company_name, headquarters_country, etc.)
    """
    print("\n🏢 Insertion des profils entreprise...")
    
    profiles_dir = Path(__file__).parent.parent / "data" / "company_profiles"
    
    if not profiles_dir.exists():
        print("   ⚠️  Dossier data/company_profiles/ non trouvé, ignoré")
        return
    
    count = 0
    for filepath in sorted(profiles_dir.glob("*.json")):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extraire company_name depuis différentes structures
            company_data = data.get("company", {})
            company_name = (
                company_data.get("company_name") 
                or company_data.get("legal_name")
                or data.get("company_name") 
                or data.get("name", filepath.stem)
            )
            
            headquarters_country = (
                company_data.get("registration", {}).get("country")
                or data.get("headquarters_country", "FR")
            )
            
            # Compter sites et fournisseurs si disponibles
            total_sites = len(data.get("sites", []))
            total_suppliers = len(data.get("suppliers", []))
            
            profile = CompanyProfile(
                company_name=company_name,
                headquarters_country=headquarters_country,
                total_sites=total_sites or None,
                total_suppliers=total_suppliers or None,
                risk_tolerance=data.get("risk_tolerance", "medium"),
                notification_settings=data.get("notification_settings"),
                data_sources_config=data.get("data_sources_config"),
                llm_config=data.get("llm_config"),
            )
            db.add(profile)
            count += 1
            print(f"   ✅ {company_name} ({headquarters_country})")
            
        except Exception as e:
            print(f"   ❌ Erreur {filepath.name}: {e}")
    
    db.commit()
    print(f"   → {count} profil(s) chargé(s)")


def seed_data_sources(db):
    """
    Insère les sources de données par défaut pour l'Agent 1A.
    Ces sources permettent à l'admin de les activer/désactiver via l'API.
    """
    print("\n📡 Insertion des sources de données...")
    
    default_sources = [
        {
            "name": "EUR-Lex",
            "description": "Base de données officielle du droit de l'Union européenne. Contient les règlements, directives et décisions.",
            "source_type": "api",
            "risk_type": "regulatory",
            "base_url": "https://eur-lex.europa.eu/eurlex-ws/search",
            "api_key_env_var": None,
            "config": {
                "domains": ["ENVI", "AGRI", "EMPL", "REGIO"],
                "max_results": 100,
                "language": "FRA"
            },
            "is_active": True,
            "priority": 1
        },
        {
            "name": "OpenMeteo",
            "description": "API météorologique open-source pour les prévisions et données historiques climatiques.",
            "source_type": "api",
            "risk_type": "climate",
            "base_url": "https://api.open-meteo.com/v1",
            "api_key_env_var": None,
            "config": {
                "forecast_days": 7,
                "models": ["best_match"],
                "variables": ["temperature_2m", "precipitation", "wind_speed_10m"]
            },
            "is_active": True,
            "priority": 2
        },
        {
            "name": "ACLED",
            "description": "Armed Conflict Location & Event Data - Base de données sur les conflits et événements géopolitiques.",
            "source_type": "api",
            "risk_type": "geopolitical",
            "base_url": "https://api.acleddata.com/acled/read",
            "api_key_env_var": "ACLED_API_KEY",
            "config": {
                "event_types": ["battles", "protests", "riots", "strategic_developments"],
                "limit": 500
            },
            "is_active": False,  # Nécessite une clé API
            "priority": 3
        },
        {
            "name": "WHO Disease Outbreak News",
            "description": "Actualités sur les épidémies et urgences sanitaires de l'OMS.",
            "source_type": "rss",
            "risk_type": "sanitary",
            "base_url": "https://www.who.int/feeds/entity/don/en/rss.xml",
            "api_key_env_var": None,
            "config": {
                "refresh_interval_hours": 6,
                "keywords": ["outbreak", "epidemic", "pandemic", "health emergency"]
            },
            "is_active": False,  # À activer selon besoin
            "priority": 4
        }
    ]
    
    for source_data in default_sources:
        source = DataSource(
            name=source_data["name"],
            description=source_data["description"],
            source_type=source_data["source_type"],
            risk_type=source_data["risk_type"],
            base_url=source_data["base_url"],
            api_key_env_var=source_data["api_key_env_var"],
            config=source_data["config"],
            is_active=source_data["is_active"],
            priority=source_data["priority"]
        )
        db.add(source)
        status = "✅ Active" if source_data["is_active"] else "⏸️  Inactive"
        print(f"   {status} {source_data['name']} ({source_data['risk_type']})")
    
    db.commit()


def print_summary(db):
    """Affiche un résumé des données insérées."""
    profiles_count = db.query(CompanyProfile).count()
    sites_count = db.query(HutchinsonSite).count()
    suppliers_count = db.query(Supplier).count()
    relationships_count = db.query(SupplierRelationship).count()
    sources_count = db.query(DataSource).count()
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DU SEED")
    print("=" * 60)
    print(f"   Profils entreprise:    {profiles_count}")
    print(f"   Sites Hutchinson:      {sites_count}")
    print(f"   Fournisseurs:          {suppliers_count}")
    print(f"   Relations:             {relationships_count}")
    print(f"   Sources de données:    {sources_count}")
    print("=" * 60)


def main():
    """Point d'entrée principal."""
    print("=" * 60)
    print("🌱 SEED DATABASE - DataNova")
    print("=" * 60)
    
    # Chemin vers le fichier de données
    data_file = Path(__file__).parent.parent / "data" / "test_data.json"
    
    if not data_file.exists():
        print(f"❌ Fichier non trouvé: {data_file}")
        sys.exit(1)
    
    print(f"📁 Chargement depuis: {data_file}")
    
    # Charger les données JSON
    data = load_json_data(data_file)
    
    # Note: les tables sont créées par Alembic (start.sh), pas par init_db()
    
    # Créer une session
    db = SessionLocal()
    
    try:
        # Vérifier si les données existent déjà
        existing_sites = db.query(HutchinsonSite).count()
        if existing_sites > 0:
            print(f"\n✅ Base déjà peuplée ({existing_sites} sites). Seed ignoré.")
            print("   (Pour re-seeder, utilisez FORCE_SEED=true ou videz les tables)")
            
            import os
            if os.environ.get("FORCE_SEED") != "true":
                print_summary(db)
                return
            else:
                print("   ⚠️  FORCE_SEED=true → Re-seed forcé")
        
        # Vider les tables existantes
        clear_tables(db)
        
        # Insérer les données
        site_mapping = seed_hutchinson_sites(db, data.get('hutchinson_sites', []))
        supplier_mapping = seed_suppliers(db, data.get('suppliers', []))
        seed_supplier_relationships(
            db, 
            data.get('supplier_relationships', []),
            site_mapping,
            supplier_mapping
        )
        
        # Insérer les profils entreprise depuis data/company_profiles/
        seed_company_profiles(db)
        
        # Insérer les sources de données par défaut
        seed_data_sources(db)
        
        # Afficher le résumé
        print_summary(db)
        
        print("\n✅ Seed terminé avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du seed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
