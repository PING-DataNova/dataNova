"""
Tests pour Agent 3 (Judge) avec les résultats d'Agent 2
"""

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path
import json

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))
from storage.models import HutchinsonSite, Supplier, SupplierRelationship, Document
from agent_2.agent import Agent2
from llm_judge.judge import Judge


def test_judge_with_real_data():
    """
    Teste le Judge avec les données réelles de la base de données
    """
    # Connexion à la base
    db_path = Path(__file__).parent.parent.parent / "ping_test.db"
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Charger les données
    sites = session.query(HutchinsonSite).all()
    suppliers = session.query(Supplier).all()
    relationships = session.query(SupplierRelationship).all()
    documents = session.query(Document).all()
    
    print("=" * 80)
    print("🧪 TESTS AGENT 3 (JUDGE) - Évaluation de Qualité")
    print("=" * 80)
    print(f"\n📊 Données chargées:")
    print(f"  - {len(sites)} sites")
    print(f"  - {len(suppliers)} fournisseurs")
    print(f"  - {len(relationships)} relations")
    print(f"  - {len(documents)} documents")
    
    # Convertir en dictionnaires
    sites_dict = [
        {
            "id": s.id,
            "name": s.name,
            "country": s.country,
            "region": s.region,
            "city": s.city,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "sectors": s.sectors or [],
            "main_products": s.products or [],  # Renommé pour cohérence
            "products": s.products or [],
            "raw_materials": s.raw_materials or [],
            "employee_count": s.employee_count or 0,
            "annual_production_value": s.annual_production_value or 0,
            "strategic_importance": s.strategic_importance or "moyen",
            "certifications": s.certifications or [],
            "sectors_served": s.sectors or []  # Pour compatibilité Risk Analyzer
        }
        for s in sites
    ]
    
    suppliers_dict = [
        {
            "id": sup.id,
            "name": sup.name,
            "code": sup.code,
            "country": sup.country,
            "region": sup.region,
            "city": sup.city,
            "latitude": sup.latitude,
            "longitude": sup.longitude,
            "products_supplied": sup.products_supplied or [],
            "sector": sup.sector or "Inconnu",
            "company_size": sup.company_size or "PME",
            "financial_health": sup.financial_health or "moyen",
            "certifications": sup.certifications or []
        }
        for sup in suppliers
    ]
    
    relationships_dict = [
        {
            "site_id": r.hutchinson_site_id,
            "supplier_id": r.supplier_id,
            "products_supplied": r.products_supplied or [],
            "criticality": r.criticality or "Standard",
            "is_sole_supplier": r.is_sole_supplier or False,
            "is_unique_supplier": r.is_sole_supplier or False,  # Alias pour Agent 2
            "has_backup_supplier": r.has_backup_supplier or False,
            "backup_supplier_id": r.backup_supplier_id,
            "lead_time_days": r.lead_time_days or 30,
            "annual_volume_eur": r.annual_volume or 0
        }
        for r in relationships
    ]
    
    # Initialiser Agent 2 et Judge
    agent2 = Agent2(llm_model="claude-sonnet-4-5-20250929")
    judge = Judge(llm_model="claude-sonnet-4-5-20250929")
    
    # Tester sur le premier document (Bangkok flood)
    doc = documents[0]
    
    print(f"\n{'=' * 80}")
    print(f"🧪 TEST : {doc.title}")
    print(f"   Type: {doc.event_type}")
    print(f"{'=' * 80}")
    
    # Simuler le résultat de pertinence
    pertinence_mock = {
        "decision": "OUI",
        "confidence": 0.95,
        "reasoning": "Événement climatique majeur affectant directement le site de Bangkok et son fournisseur principal Thai Rubber Industries. La zone industrielle de Lat Krabang où se situe le site est dans la zone d'inondation prévue selon les bulletins météorologiques du Thai Meteorological Department.",
        "affected_entities_preview": {
            "sites": ["site_bangkok"],
            "suppliers": ["supplier_thai_rubber"]
        },
        "matched_keywords": ["inondation", "Bangkok", "caoutchouc", "production"],
        "source_verification": {
            "source_type": "Thai Meteorological Department",
            "source_url": "https://www.tmd.go.th/en/weather/warning/flood",
            "publication_date": "2026-01-28T14:30:00+07:00",
            "verified": True
        }
    }
    
    # Enrichir le document avec un contenu réaliste si manquant
    enriched_content = doc.content or """
BULLETIN D'ALERTE MÉTÉOROLOGIQUE - INONDATIONS BANGKOK
Source: Thai Meteorological Department (TMD)
Date: 28 janvier 2026, 14h30 ICT

ALERTE INONDATION MAJEURE - BANGKOK METROPOLITAN REGION

Les pluies torrentielles des 3 derniers jours (accumulation de 280mm) ont saturé les capacités de drainage de Bangkok. 
Le niveau du fleuve Chao Phraya atteint des niveaux critiques (3.2m au-dessus de la normale).

ZONES À RISQUE ÉLEVÉ:
- District de Lat Krabang (ZONE INDUSTRIELLE) ⚠️
- District de Bang Kapi
- District de Min Buri
- Périphérie Est de Bangkok

PRÉVISIONS:
- Poursuite des pluies intenses pendant 5-7 jours
- Débordement probable du Chao Phraya dans les 24-48h
- Routes principales vers les zones industrielles susceptibles d'être coupées
- Durée estimée de la perturbation: 14-21 jours minimum

RECOMMANDATIONS:
- Évacuation préventive des zones industrielles basses
- Protection des équipements et stocks critiques
- Mise en place de plans de continuité d'activité

RÉFÉRENCE HISTORIQUE:
Les inondations de 2011 ont duré 3 mois et ont causé l'arrêt de 60% des usines de la région de Bangkok.

Contact: Thai Meteorological Department - +66 2 398 9874
    """
    
    doc_dict = {
        "id": doc.id,
        "title": doc.title,
        "event_type": doc.event_type,
        "event_subtype": doc.event_subtype or "inondation",
        "publication_date": "2026-01-28T14:30:00+07:00",
        "source_url": "https://www.tmd.go.th/en/weather/warning/flood",
        "geographic_scope": doc.geographic_scope,
        "content": enriched_content.strip()
    }
    
    # Étape 1 : Analyse d'Agent 2
    print("\n🔄 Étape 1 : Analyse d'Agent 2...")
    risk_analysis = agent2.analyze(
        document=doc_dict,
        pertinence_result=pertinence_mock,
        sites=sites_dict,
        suppliers=suppliers_dict,
        supplier_relationships=relationships_dict
    )
    
    print(f"\n📊 Résultat Agent 2:")
    print(f"   - Sites impactés: {len(risk_analysis.get('affected_sites', []))}")
    print(f"   - Fournisseurs impactés: {len(risk_analysis.get('affected_suppliers', []))}")
    print(f"   - Niveau de risque: {risk_analysis.get('overall_risk_level', 'N/A')}")
    print(f"   - Recommandations: {len(risk_analysis.get('recommendations', []))}")
    
    # Étape 2 : Évaluation du Judge
    print("\n🔄 Étape 2 : Évaluation du Judge...")
    judge_result = judge.evaluate(
        document=doc_dict,
        pertinence_result=pertinence_mock,
        risk_analysis=risk_analysis,
        sites=sites_dict,
        suppliers=suppliers_dict,
        supplier_relationships=relationships_dict
    )
    
    # Afficher le résultat
    print(f"\n{'=' * 80}")
    print("✅ RÉSULTAT DE L'ÉVALUATION JUDGE")
    print(f"{'=' * 80}")
    
    judge_eval = judge_result['judge_evaluation']
    
    print(f"\n📋 Pertinence Checker:")
    print(f"   Score pondéré: {judge_eval['pertinence_checker_evaluation']['weighted_score']}/10")
    print(f"   Confiance: {judge_eval['pertinence_checker_evaluation']['confidence_overall']}")
    
    print(f"\n📊 Risk Analyzer:")
    print(f"   Score pondéré: {judge_eval['risk_analyzer_evaluation']['weighted_score']}/10")
    print(f"   Confiance: {judge_eval['risk_analyzer_evaluation']['confidence_overall']}")
    
    print(f"\n🎯 Score Global: {judge_eval['overall_quality_score']}/10")
    print(f"🎯 Confiance Globale: {judge_eval['overall_confidence']}")
    
    print(f"\n🚦 Décision: {judge_eval['action_recommended']}")
    print(f"📝 Raisonnement: {judge_eval['reasoning']}")
    
    # Sauvegarder le résultat complet
    output_path = Path(__file__).parent / "judge_result.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(judge_result, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultat complet sauvegardé dans: {output_path}")
    
    print(f"\n{'=' * 80}")
    print("✅ TEST TERMINÉ")
    print(f"{'=' * 80}")
    
    session.close()


if __name__ == "__main__":
    test_judge_with_real_data()
