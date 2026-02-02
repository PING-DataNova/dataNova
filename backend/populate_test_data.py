"""
Script pour populer la base de données SQLite avec des données de test réalistes.
Inspiré de Prewave et du document "donnees_minimales.pdf".

Usage:
    python populate_test_data.py

Ce script va:
1. Créer la base de données SQLite si elle n'existe pas
2. Créer toutes les tables selon le schéma SQLAlchemy
3. Insérer les données de test (sites, fournisseurs, relations, documents, pertinence checks)
"""

import json
import sys
from pathlib import Path
from datetime import datetime
# Ajouter le répertoire src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from storage.models import (
    Base,
    HutchinsonSite,
    Supplier,
    SupplierRelationship,
    Document,
    PertinenceCheck,
)


def load_test_data(json_path: str) -> dict:
    """Charge les données de test depuis le fichier JSON."""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_database(db_path: str = "ping_test.db"):
    """Crée la base de données et toutes les tables."""
    engine = create_engine(f"sqlite:///{db_path}", echo=True)
    Base.metadata.create_all(engine)
    return engine


def populate_sites(session, sites_data: list):
    """Insère les sites Hutchinson."""
    print("\n🏭 Insertion des sites Hutchinson...")
    for site_data in sites_data:
        # Mapper strategic_importance (int) vers string
        importance_map = {1: "faible", 2: "faible", 3: "moyen", 4: "fort", 5: "critique"}
        strategic_importance = importance_map.get(site_data["strategic_importance"], "moyen")
        
        site = HutchinsonSite(
            id=site_data["id"],
            name=site_data["name"],
            code=site_data["code"],
            country=site_data["country"],
            region=site_data["region"],
            latitude=site_data["latitude"],
            longitude=site_data["longitude"],
            products=site_data["products"],
            sectors=site_data["sectors"],
            raw_materials=site_data.get("raw_materials", []),
            strategic_importance=strategic_importance,
            active=site_data["active"],
        )
        session.add(site)
        print(f"  ✓ {site.name} ({site.country})")
    
    session.commit()
    print(f"✅ {len(sites_data)} sites insérés avec succès")


def populate_suppliers(session, suppliers_data: list):
    """Insère les fournisseurs."""
    print("\n🏢 Insertion des fournisseurs...")
    for supplier_data in suppliers_data:
        # Mapper financial_health_score (float) vers string
        score = supplier_data["financial_health_score"]
        if score >= 0.8:
            financial_health = "excellent"
        elif score >= 0.7:
            financial_health = "bon"
        elif score >= 0.6:
            financial_health = "moyen"
        else:
            financial_health = "faible"
        
        supplier = Supplier(
            id=supplier_data["id"],
            name=supplier_data["name"],
            code=supplier_data["code"],
            country=supplier_data["country"],
            region=supplier_data["region"],
            latitude=supplier_data["latitude"],
            longitude=supplier_data["longitude"],
            products_supplied=supplier_data["products_supplied"],
            sector=supplier_data["sector"],
            company_size=supplier_data["company_size"],
            financial_health=financial_health,
            certifications=supplier_data["certifications"],
            active=supplier_data["active"],
        )
        session.add(supplier)
        print(f"  ✓ {supplier.name} ({supplier.country})")
    
    session.commit()
    print(f"✅ {len(suppliers_data)} fournisseurs insérés avec succès")


def populate_relationships(session, relationships_data: list):
    """Insère les relations site-fournisseur."""
    print("\n🔗 Insertion des relations site-fournisseur...")
    for rel_data in relationships_data:
        relationship = SupplierRelationship(
            hutchinson_site_id=rel_data["hutchinson_site_id"],
            supplier_id=rel_data["supplier_id"],
            products_supplied=rel_data["products_supplied"],
            criticality=rel_data["criticality"],
            is_sole_supplier=rel_data["is_sole_supplier"],
            has_backup_supplier=rel_data["has_backup_supplier"],
            backup_supplier_id=rel_data.get("backup_supplier_id"),
            lead_time_days=rel_data["lead_time_days"],
            annual_volume=rel_data["annual_volume_eur"],
            contract_end_date=datetime.strptime(rel_data["contract_end_date"], "%Y-%m-%d").date(),
        )
        session.add(relationship)
        print(f"  ✓ {rel_data['hutchinson_site_id']} ← {rel_data['supplier_id']} ({rel_data['criticality']})")
    
    session.commit()
    print(f"✅ {len(relationships_data)} relations insérées avec succès")


def populate_documents(session, documents_data: list):
    """Insère les documents (événements)."""
    print("\n📄 Insertion des documents (événements)...")
    for doc_data in documents_data:
        # Générer un hash SHA256 simple basé sur le titre + source
        import hashlib
        hash_content = f"{doc_data['title']}{doc_data['source_url']}"
        hash_sha256 = hashlib.sha256(hash_content.encode()).hexdigest()
        
        document = Document(
            id=doc_data["id"],
            event_type=doc_data["event_type"],
            event_subtype=doc_data["event_subtype"],
            title=doc_data["title"],
            summary=doc_data["summary"],
            source_url=doc_data["source_url"],
            publication_date=datetime.fromisoformat(doc_data.get("publication_date", doc_data.get("published_date", "2026-01-01T00:00:00")).replace("Z", "+00:00")) if doc_data.get("publication_date") or doc_data.get("published_date") else None,
            hash_sha256=hash_sha256,
            geographic_scope=doc_data["geographic_scope"],
            extra_metadata=doc_data["extra_metadata"],
        )
        session.add(document)
        print(f"  ✓ {document.title[:60]}... ({document.event_type})")
    
    session.commit()
    print(f"✅ {len(documents_data)} documents insérés avec succès")


def populate_pertinence_checks(session, checks_data: list):
    """Insère les checks de pertinence."""
    print("\n✅ Insertion des checks de pertinence...")
    for check_data in checks_data:
        check = PertinenceCheck(
            id=check_data["id"],
            document_id=check_data["document_id"],
            decision=check_data["decision"],
            confidence=check_data["confidence"],
            reasoning=check_data["reasoning"],
            matched_elements=check_data.get("affected_entities_preview"),
            llm_model="claude-3-5-sonnet-20241022",
        )
        session.add(check)
        print(f"  ✓ {check.document_id} → {check.decision} (confiance: {check.confidence})")
    
    session.commit()
    print(f"✅ {len(checks_data)} checks de pertinence insérés avec succès")


def main():
    """Fonction principale."""
    print("=" * 80)
    print("🚀 PING - Population de la base de données avec des données de test")
    print("=" * 80)
    
    # Chemins
    script_dir = Path(__file__).parent
    json_path = script_dir / "data" / "test_data.json"
    db_path = script_dir / "ping_test.db"
    
    # Vérifier que le fichier JSON existe
    if not Path(json_path).exists():
        print(f"❌ Erreur: Le fichier {json_path} n'existe pas")
        sys.exit(1)
    
    # Charger les données de test
    print(f"\nChargement des données depuis {json_path}...")
    test_data = load_test_data(json_path)
    print(f"✅ Données chargées:")
    print(f"  - {len(test_data['hutchinson_sites'])} sites")
    print(f"  - {len(test_data['suppliers'])} fournisseurs")
    print(f"  - {len(test_data['supplier_relationships'])} relations")
    print(f"  - {len(test_data['documents'])} documents")
    print(f"  - {len(test_data['pertinence_checks'])} checks de pertinence")
    
    # Créer la base de données
    print(f"\n Création de la base de données: {db_path}")
    engine = create_database(str(db_path))
    
    # Créer une session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Populer les tables
        populate_sites(session, test_data["hutchinson_sites"])
        populate_suppliers(session, test_data["suppliers"])
        populate_relationships(session, test_data["supplier_relationships"])
        populate_documents(session, test_data["documents"])
        populate_pertinence_checks(session, test_data["pertinence_checks"])
        
        print("\n" + "=" * 80)
        print("🎉 Base de données populée avec succès!")
        print("=" * 80)
        print(f"\n📍 Base de données: {db_path}")
        print("\n🧪 Vous pouvez maintenant tester Agent 2 avec ces données:")
        print("   cd backend/src/agents/agent_2")
        print("   python test_agent_2.py")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'insertion des données: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
