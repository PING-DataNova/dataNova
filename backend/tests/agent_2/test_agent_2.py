"""
Test Agent 2 avec affichage de la transparence complète
"""

import sys
from pathlib import Path

# Ajouter le chemin backend au PYTHONPATH
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from src.agent_2.agent import Agent2
import json

print("=" * 80)
print("🧪 TEST AGENT 2 - TRANSPARENCE COMPLÈTE")
print("=" * 80)
print()

# Données de test
document = {
    "id": "doc_test_001",
    "title": "Inondations majeures dans le sud de la France",
    "event_type": "climatique",
    "event_subtype": "inondation majeure",
    "geographic_scope": {
        "coordinates": {
            "latitude": 43.6047,
            "longitude": 1.4442
        }
    }
}

sites = [
    {
        "id": "site_001",
        "name": "Hutchinson Toulouse",
        "country": "France",
        "latitude": 43.6047,
        "longitude": 1.4442,
        "strategic_importance": "critique",
        "sectors": ["automotive"],
        "products": ["joints", "tuyaux"]
    },
    {
        "id": "site_002",
        "name": "Hutchinson Paris",
        "country": "France",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "strategic_importance": "élevé",
        "sectors": ["automotive"],
        "products": ["joints"]
    }
]

suppliers = [
    {
        "id": "supplier_001",
        "name": "Fournisseur Sud France",
        "country": "France",
        "latitude": 43.2965,
        "longitude": 5.3698,
        "is_sole_supplier": False,
        "sectors": ["automotive"],
        "products_supplied": ["caoutchouc"]
    },
    {
        "id": "supplier_002",
        "name": "Fournisseur Nord",
        "country": "France",
        "latitude": 50.6292,
        "longitude": 3.0573,
        "is_sole_supplier": False,
        "sectors": ["automotive"],
        "products_supplied": ["plastique"]
    }
]

supplier_relationships = [
    {
        "hutchinson_site_id": "site_001",
        "supplier_id": "supplier_001",
        "products_supplied": ["caoutchouc"],
        "criticality": "Critique"
    }
]

pertinence_result = {
    "is_pertinent": "OUI",
    "confidence": 0.95
}

print("📊 Données de test :")
print(f"  - Événement : {document['title']}")
print(f"  - Type : {document['event_type']}")
print(f"  - Sites : {len(sites)}")
print(f"  - Fournisseurs : {len(suppliers)}")
print()

# Initialiser Agent 2
agent2 = Agent2(llm_model="claude-sonnet-4-5-20250929")

print("🔄 Analyse en cours...")
print()

# Analyser
risk_analysis, risk_projections = agent2.analyze(
    document=document,
    pertinence_result=pertinence_result,
    sites=sites,
    suppliers=suppliers,
    supplier_relationships=supplier_relationships
)

print("=" * 80)
print("✅ RÉSULTATS AVEC TRANSPARENCE COMPLÈTE")
print("=" * 80)
print()

# Afficher les projections avec transparence
concerned_projections = [p for p in risk_projections if p['is_concerned']]

for proj in concerned_projections:
    entity_type = proj['entity_type'].upper()
    entity_name = proj['entity_name']
    
    print(f"{'=' * 80}")
    print(f"🎯 {entity_type} : {entity_name}")
    print(f"{'=' * 80}")
    print()
    
    # Scores
    print("📊 SCORES :")
    print(f"  - Risk Score 360° : {proj['risk_score']}/100")
    print(f"  - Business Interruption : {proj['business_interruption_score']}/100")
    print()
    
    # Reasoning Details
    if 'reasoning_details' in proj:
        details = proj['reasoning_details']
        
        # Pourquoi concerné
        print("📍 POURQUOI CONCERNÉ :")
        print(f"  {details['why_concerned']}")
        print()
        
        # Risques identifiés
        print("⚠️  RISQUES IDENTIFIÉS :")
        for risk in details['risks_identified']:
            print(f"  • {risk['type']}")
            print(f"    - Probabilité : {risk['probability']}")
            print(f"    - Raison : {risk['reason']}")
        print()
        
        # Impacts calculés
        print("💥 IMPACTS CALCULÉS :")
        impacts = details['impacts_calculated']
        for impact_key, impact_data in impacts.items():
            print(f"  • {impact_data['description']}")
            print(f"    - Calcul : {impact_data['calculation']}")
        print()
        
        # Calcul des scores
        print("🧮 CALCUL DES SCORES :")
        score_calc = details['score_calculation']
        
        print(f"  • Severity : {score_calc['severity']['value']}/100")
        print(f"    → {score_calc['severity']['explanation']}")
        print()
        
        print(f"  • Probability : {score_calc['probability']['value']}/100")
        print(f"    → {score_calc['probability']['explanation']}")
        print()
        
        print(f"  • Exposure : {score_calc['exposure']['value']}/100")
        print(f"    → {score_calc['exposure']['explanation']}")
        print()
        
        print(f"  • Urgency : {score_calc['urgency']['value']}/100")
        print(f"    → {score_calc['urgency']['explanation']}")
        print()
        
        print(f"  📐 Formule : {score_calc['formula']}")
        print(f"  📊 Calcul : {score_calc['calculation']}")
        print()

print("=" * 80)
print("✅ TEST TERMINÉ")
print("=" * 80)
print()
print("💡 Tous les scores sont maintenant expliqués et traçables !")
