"""
Script de seed pour charger les données de test dans la base de données.

Ce script charge les données depuis test_data.json dans les tables :
- hutchinson_sites
- suppliers
- supplier_relationships

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

from src.storage.database import SessionLocal, init_db
from src.storage.models import HutchinsonSite, Supplier, SupplierRelationship


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
            extra_metadata=rel.get('extra_metadata'),
            active=True
        )
        db.add(db_rel)
        
        site_id = rel.get('hutchinson_site_id')
        supplier_id = rel.get('supplier_id')
        print(f"   ✅ {site_id} ↔ {supplier_id}")
    
    db.commit()


def print_summary(db):
    """Affiche un résumé des données insérées."""
    sites_count = db.query(HutchinsonSite).count()
    suppliers_count = db.query(Supplier).count()
    relationships_count = db.query(SupplierRelationship).count()
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DU SEED")
    print("=" * 60)
    print(f"   Sites Hutchinson:      {sites_count}")
    print(f"   Fournisseurs:          {suppliers_count}")
    print(f"   Relations:             {relationships_count}")
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
    
    # Initialiser la BDD
    init_db()
    
    # Créer une session
    db = SessionLocal()
    
    try:
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
