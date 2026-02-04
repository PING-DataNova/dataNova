"""
Script de Test pour l'Agent 1B
================================

Ce script teste les trois types d'analyse de l'Agent 1B :
- Réglementaire (triangulée)
- Climatique (distance géographique)
- Géopolitique (correspondance pays)

Auteur: DataNova PING
Date: 2026-02-01
"""

import sys
import json
from datetime import datetime

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, '/Users/noradossou-gbete/Documents/Projet_PING/Datanova_perso/dataNova/backend')

from src.agent_1b.agent import Agent1B
from src.storage.database import get_session
from src.storage.models import Document, HutchinsonSite, Supplier, PertinenceCheck


def create_test_document_regulatory(session):
    """
    Crée un document de test pour événement réglementaire
    """
    doc = Document(
        id="test-doc-regulatory-001",
        title="Nouveau règlement CBAM sur les importations d'aluminium",
        source_url="https://eur-lex.europa.eu/test",
        event_type="reglementaire",
        event_subtype="CBAM",
        publication_date=datetime.utcnow(),
        hash_sha256="test-hash-regulatory-001",
        content="""
        Le règlement CBAM (Carbon Border Adjustment Mechanism) impose de nouvelles obligations 
        aux importateurs d'aluminium (code NC 7601) et de caoutchouc (code NC 4001) dans l'UE.
        Les entreprises du secteur automobile devront déclarer leurs émissions de carbone 
        pour tous les produits importés depuis la Chine, l'Inde et les États-Unis.
        """,
        summary="Nouvelles obligations CBAM pour l'aluminium et le caoutchouc",
        geographic_scope={
            "countries": ["France", "Germany", "Spain", "Poland"],
            "regions": ["EU"]
        },
        status="new"
    )
    
    session.add(doc)
    session.commit()
    return doc.id


def create_test_document_climatic(session):
    """
    Crée un document de test pour événement climatique
    """
    doc = Document(
        id="test-doc-climatic-001",
        title="Inondations majeures à Toulouse",
        source_url="https://meteofrance.com/test",
        event_type="climatique",
        event_subtype="inondation",
        publication_date=datetime.utcnow(),
        hash_sha256="test-hash-climatic-001",
        content="""
        Des inondations majeures ont touché la région de Toulouse suite à des pluies torrentielles.
        Plusieurs zones industrielles sont affectées, notamment le secteur de Blagnac.
        Les autorités recommandent l'évacuation préventive des sites à risque.
        """,
        summary="Inondations majeures à Toulouse",
        geographic_scope={
            "countries": ["France"],
            "regions": ["Occitanie"],
            "coordinates": {
                "latitude": 43.6047,
                "longitude": 1.4442
            }
        },
        status="new"
    )
    
    session.add(doc)
    session.commit()
    return doc.id


def create_test_document_geopolitical(session):
    """
    Crée un document de test pour événement géopolitique
    """
    doc = Document(
        id="test-doc-geopolitical-001",
        title="Nouvelles sanctions économiques contre la Russie",
        source_url="https://europa.eu/test",
        event_type="geopolitique",
        event_subtype="sanction",
        publication_date=datetime.utcnow(),
        hash_sha256="test-hash-geopolitical-001",
        content="""
        L'Union Européenne a annoncé de nouvelles sanctions économiques contre la Russie,
        incluant un embargo sur certains matériaux industriels et composants automobiles.
        Les entreprises ayant des fournisseurs en Russie ou dans les pays limitrophes
        (Biélorussie, Kazakhstan) doivent revoir leurs chaînes d'approvisionnement.
        """,
        summary="Nouvelles sanctions UE contre la Russie",
        geographic_scope={
            "countries": ["Russia", "Belarus", "Kazakhstan"],
            "regions": ["Eastern Europe", "Central Asia"]
        },
        status="new"
    )
    
    session.add(doc)
    session.commit()
    return doc.id


def create_test_site(session):
    """
    Crée un site de test à Toulouse
    """
    site = HutchinsonSite(
        id="test-site-toulouse-001",
        name="Hutchinson Toulouse",
        code="HUT-TLS-001",
        country="France",
        region="Occitanie",
        city="Toulouse",
        latitude=43.5850,
        longitude=1.4330,
        sectors=["Automotive", "Aerospace"],
        products=["Joints d'étanchéité", "Tuyaux"],
        raw_materials=["Caoutchouc", "Plastique"],
        strategic_importance="fort",
        active=True
    )
    
    session.add(site)
    session.commit()
    return site.id


def create_test_supplier(session):
    """
    Crée un fournisseur de test en Pologne
    """
    supplier = Supplier(
        id="test-supplier-poland-001",
        name="Polish Rubber Components",
        code="SUP-POL-001",
        country="Poland",
        region="Mazovia",
        city="Warsaw",
        latitude=52.2297,
        longitude=21.0122,
        sector="Automotive",
        products_supplied=["Composants en caoutchouc"],
        company_size="ETI",
        active=True
    )
    
    session.add(supplier)
    session.commit()
    return supplier.id


def test_regulatory_analysis():
    """
    Test de l'analyse réglementaire
    """
    print("\n" + "="*80)
    print("TEST 1: ANALYSE RÉGLEMENTAIRE")
    print("="*80)
    
    session = get_session()
    
    try:
        # Créer un document de test
        doc_id = create_test_document_regulatory(session)
        print(f"✅ Document de test créé: {doc_id}")
        
        # Exécuter l'analyse
        agent = Agent1B()
        result = agent.check_pertinence(doc_id, save_to_db=True)
        
        # Afficher les résultats
        print(f"\n📊 Résultats de l'analyse:")
        print(f"  - Décision: {result['decision']}")
        print(f"  - Confiance: {result['confidence']:.2f}")
        print(f"  - Sites affectés: {len(result['affected_sites'])}")
        print(f"  - Fournisseurs affectés: {len(result['affected_suppliers'])}")
        print(f"\n📝 Raisonnement:")
        print(result['reasoning'])
        
        # Nettoyer (désactivé pour vérifier la sauvegarde)
        # session.query(PertinenceCheck).filter_by(document_id=doc_id).delete()
        # session.query(Document).filter_by(id=doc_id).delete()
        # session.commit()
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        session.close()


def test_climatic_analysis():
    """
    Test de l'analyse climatique
    """
    print("\n" + "="*80)
    print("TEST 2: ANALYSE CLIMATIQUE")
    print("="*80)
    
    session = get_session()
    
    try:
        # Créer un site de test
        site_id = create_test_site(session)
        print(f"✅ Site de test créé: {site_id}")
        
        # Créer un document de test
        doc_id = create_test_document_climatic(session)
        print(f"✅ Document de test créé: {doc_id}")
        
        # Exécuter l'analyse
        agent = Agent1B()
        result = agent.check_pertinence(doc_id, save_to_db=True)
        
        # Afficher les résultats
        print(f"\n📊 Résultats de l'analyse:")
        print(f"  - Décision: {result['decision']}")
        print(f"  - Confiance: {result['confidence']:.2f}")
        print(f"  - Sites affectés: {len(result['affected_sites'])}")
        print(f"  - Fournisseurs affectés: {len(result['affected_suppliers'])}")
        print(f"\n📝 Raisonnement:")
        print(result['reasoning'])
        
        # Nettoyer (désactivé pour vérifier la sauvegarde)
        # session.query(PertinenceCheck).filter_by(document_id=doc_id).delete()
        # session.query(Document).filter_by(id=doc_id).delete()
        # session.query(HutchinsonSite).filter_by(id=site_id).delete()
        # session.commit()
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        session.close()


def test_geopolitical_analysis():
    """
    Test de l'analyse géopolitique
    """
    print("\n" + "="*80)
    print("TEST 3: ANALYSE GÉOPOLITIQUE")
    print("="*80)
    
    session = get_session()
    
    try:
        # Créer un fournisseur de test
        supplier_id = create_test_supplier(session)
        print(f"✅ Fournisseur de test créé: {supplier_id}")
        
        # Créer un document de test
        doc_id = create_test_document_geopolitical(session)
        print(f"✅ Document de test créé: {doc_id}")
        
        # Exécuter l'analyse
        agent = Agent1B()
        result = agent.check_pertinence(doc_id, save_to_db=True)
        
        # Afficher les résultats
        print(f"\n📊 Résultats de l'analyse:")
        print(f"  - Décision: {result['decision']}")
        print(f"  - Confiance: {result['confidence']:.2f}")
        print(f"  - Sites affectés: {len(result['affected_sites'])}")
        print(f"  - Fournisseurs affectés: {len(result['affected_suppliers'])}")
        print(f"\n📝 Raisonnement:")
        print(result['reasoning'])
        
        # Nettoyer (désactivé pour vérifier la sauvegarde)
        # session.query(PertinenceCheck).filter_by(document_id=doc_id).delete()
        # session.query(Document).filter_by(id=doc_id).delete()
        # session.query(Supplier).filter_by(id=supplier_id).delete()
        # session.commit()
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        session.close()


def main():
    """
    Fonction principale pour exécuter tous les tests
    """
    print("\n" + "="*80)
    print("🧪 SUITE DE TESTS AGENT 1B")
    print("="*80)
    
    results = []
    
    # Test 1: Réglementaire
    result1 = test_regulatory_analysis()
    if result1:
        results.append(("Réglementaire", result1))
    
    # Test 2: Climatique
    result2 = test_climatic_analysis()
    if result2:
        results.append(("Climatique", result2))
    
    # Test 3: Géopolitique
    result3 = test_geopolitical_analysis()
    if result3:
        results.append(("Géopolitique", result3))
    
    # Résumé
    print("\n" + "="*80)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*80)
    
    for test_name, result in results:
        print(f"\n{test_name}:")
        print(f"  ✅ Décision: {result['decision']}")
        print(f"  ✅ Confiance: {result['confidence']:.2f}")
        print(f"  ✅ Entités affectées: {len(result['affected_sites']) + len(result['affected_suppliers'])}")
    
    print("\n" + "="*80)
    print(f"✅ {len(results)}/{3} tests réussis")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
