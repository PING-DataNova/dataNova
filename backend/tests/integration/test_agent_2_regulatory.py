#!/usr/bin/env python3
"""
Test Agent 2 avec scénario RÉGLEMENTAIRE
Vérifie que le LLM utilise les données BI pour les analyses réglementaires
"""

import asyncio
import os
import sys
from datetime import datetime

# Ajouter le chemin src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agent_2.agent import Agent2
from agent_2.llm_reasoning import LLMReasoning

# Document réglementaire de test - CBAM (Carbon Border Adjustment Mechanism)
REGULATORY_DOCUMENT = {
    "id": "test_cbam_2024",
    "title": "CBAM : Nouvelles taxes carbone sur les importations d'acier et aluminium",
    "summary": """Le mécanisme d'ajustement carbone aux frontières (CBAM) de l'UE entre en vigueur. 
    À partir de 2026, toutes les importations d'acier, aluminium et produits à haute empreinte carbone 
    seront taxées selon leur contenu CO2. Les fournisseurs hors-UE devront fournir des certificats 
    d'émissions. Non-conformité = interdiction d'importation. Impact estimé: +15-25% sur les coûts 
    de matières premières importées de pays à forte empreinte carbone.""",
    "event_type": "reglementaire",
    "event_subtype": "taxe_carbone",
    "publication_date": datetime.now().isoformat(),
    "geographic_scope": {
        "countries": ["EU"],
        "regions": ["Europe"],
        "coordinates": None
    },
    "extra_metadata": {
        "effective_date": "2026-01-01",
        "transition_period_days": 365,
        "penalty_per_violation_eur": 100000
    }
}

# Données de test enrichies avec BI
TEST_SUPPLIERS = [
    {
        "id": "sup_china_steel",
        "name": "Shanghai Steel Corp",
        "country": "China",
        "region": "Asie",
        "sector": "Métallurgie",
        "products_supplied": ["Acier haute résistance", "Acier galvanisé"],
        "company_size": "Grande",
        "financial_health": "Bonne",
        "latitude": 31.2304,
        "longitude": 121.4737,
        # Données BI
        "criticality_score": 85,
        "switch_time_days": 180,
        "ramp_up_time_days": 90
    },
    {
        "id": "sup_india_alu",
        "name": "Mumbai Aluminium Works",
        "country": "India",
        "region": "Asie",
        "sector": "Métallurgie",
        "products_supplied": ["Aluminium", "Alliages légers"],
        "company_size": "Moyenne",
        "financial_health": "Correcte",
        "latitude": 19.0760,
        "longitude": 72.8777,
        # Données BI
        "criticality_score": 70,
        "switch_time_days": 120,
        "ramp_up_time_days": 60
    }
]

TEST_SITES = [
    {
        "id": "site_montargis",
        "name": "Hutchinson Montargis",
        "country": "France",
        "region": "Centre-Val de Loire",
        "sectors": ["Automobile"],
        "main_products": ["Joints anti-vibration", "Silent-blocs"],
        "raw_materials": ["Acier", "Caoutchouc"],
        "employee_count": 800,
        "annual_production_value": 120000000,
        "strategic_importance": "Haute",
        "latitude": 47.9969,
        "longitude": 2.7337,
        # Données BI
        "daily_revenue": 480000,
        "daily_production_units": 15000,
        "safety_stock_days": 12,
        "production_line_cost_per_hour": 8500,
        "customer_penalty_per_day": 45000,
        "key_customers": "Stellantis, Renault, Volkswagen"
    }
]

TEST_RELATIONSHIPS = [
    {
        "supplier_id": "sup_china_steel",
        "site_id": "site_montargis",
        "supplier_name": "Shanghai Steel Corp",
        "site_name": "Hutchinson Montargis",
        "criticality": "Critique",
        "is_unique_supplier": True,
        "backup_supplier_id": None,
        "annual_volume_eur": 8500000,
        "lead_time_days": 45,
        "products_supplied": ["Acier haute résistance"]
    },
    {
        "supplier_id": "sup_india_alu",
        "site_id": "site_montargis",
        "supplier_name": "Mumbai Aluminium Works",
        "site_name": "Hutchinson Montargis",
        "criticality": "Important",
        "is_unique_supplier": False,
        "backup_supplier_id": "sup_eu_alu",
        "annual_volume_eur": 3200000,
        "lead_time_days": 30,
        "products_supplied": ["Aluminium", "Alliages légers"]
    }
]


def test_regulatory_analysis():
    """Test Agent 2 avec scénario réglementaire CBAM"""
    
    print("=" * 80)
    print("🏛️  TEST AGENT 2 - SCÉNARIO RÉGLEMENTAIRE (CBAM)")
    print("=" * 80)
    
    # Vérifier si clé API présente
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        print(f"✅ Clé Anthropic détectée ({api_key[:10]}...)")
    else:
        print("⚠️  Pas de clé Anthropic - mode fallback")
    
    # Initialiser l'agent
    agent = Agent2()
    
    # Simuler le résultat de pertinence (Agent 1B)
    pertinence_result = {
        "is_pertinent": True,
        "pertinence_score": 0.85,
        "affected_countries": ["China", "India"],
        "affected_sectors": ["Métallurgie", "Automobile"]
    }
    
    print(f"\n📋 Document analysé: {REGULATORY_DOCUMENT['title']}")
    print(f"   Type: {REGULATORY_DOCUMENT['event_type']}")
    print(f"   Sous-type: {REGULATORY_DOCUMENT['event_subtype']}")
    
    # Analyser avec la bonne signature
    print("\n⏳ Analyse en cours (appel LLM si disponible)...\n")
    result, projections = agent.analyze(
        document=REGULATORY_DOCUMENT,
        pertinence_result=pertinence_result,
        sites=TEST_SITES,
        suppliers=TEST_SUPPLIERS,
        supplier_relationships=TEST_RELATIONSHIPS
    )
    
    # Afficher les résultats
    print("\n" + "=" * 80)
    print("📊 RÉSULTATS DE L'ANALYSE")
    print("=" * 80)
    
    print(f"\n🎯 Score de risque global: {result.get('risk_score', 'N/A')}/100")
    print(f"📊 Score BI: {result.get('business_interruption_score', 'N/A')}/100")
    print(f"🏷️  Niveau: {result.get('overall_risk_level', 'N/A')}")
    
    # Entités impactées via projections
    print("\n" + "-" * 40)
    print("📍 ENTITÉS IMPACTÉES (projections):")
    
    concerned = [p for p in projections if p.get('is_concerned', False)]
    print(f"   {len(concerned)} entités concernées sur {len(projections)}")
    
    for entity in concerned:
        print(f"\n  {'='*70}")
        print(f"  • {entity.get('entity_name')} ({entity.get('entity_type')})")
        print(f"  {'='*70}")
        print(f"    - Score risque: {entity.get('risk_score', 'N/A')}/100")
        print(f"    - Score BI: {entity.get('business_interruption_score', 'N/A')}/100")
        
        # ============================================================
        # TRAÇABILITÉ COMPLÈTE - Section ajoutée
        # ============================================================
        print(f"\n    📋 TRAÇABILITÉ DES DONNÉES:")
        print(f"    {'-'*50}")
        
        # 1. Données sources (from DB or test)
        bi = entity.get("business_impact_details", {})
        print(f"    📁 DONNÉES SOURCES:")
        print(f"       - CA quotidien (daily_revenue): {bi.get('daily_revenue_loss_eur', 0):,.0f} EUR")
        print(f"       - Pénalités clients/jour: {bi.get('customer_penalties_per_day_eur', 0):,.0f} EUR")
        print(f"       - Stock de sécurité: {bi.get('stock_coverage_days', 0)} jours")
        print(f"       - Switch time fournisseur: {bi.get('switch_time_days', 'N/A')} jours")
        print(f"       - Fournisseur unique: {'OUI' if bi.get('is_sole_supplier') else 'NON'}")
        
        # 2. Formule de calcul
        print(f"\n    🔢 FORMULE DE CALCUL:")
        print(f"       Impact total/jour = CA quotidien + Pénalités clients")
        print(f"       = {bi.get('daily_revenue_loss_eur', 0):,.0f}€ + {bi.get('customer_penalties_per_day_eur', 0):,.0f}€")
        print(f"       = {bi.get('total_daily_impact_eur', 0):,.0f}€/jour")
        
        # 3. Détail score_calculation si disponible
        reasoning_details = entity.get("reasoning_details", {})
        score_calc = reasoning_details.get("score_calculation", {})
        if score_calc:
            print(f"\n    📊 CALCUL DU SCORE 360°:")
            formula = score_calc.get("formula", "N/A")
            calculation = score_calc.get("calculation", "N/A")
            print(f"       Formule: {formula}")
            print(f"       Calcul: {calculation}")
            
            # Détail des composantes
            for key in ["severity", "probability", "exposure", "urgency"]:
                comp = score_calc.get(key, {})
                if comp:
                    print(f"       - {key.upper()}: {comp.get('value', 'N/A')} → {comp.get('explanation', 'N/A')[:80]}")
        
        # 4. Business Impact breakdown
        bi_details = score_calc.get("business_interruption", {})
        if bi_details:
            print(f"\n    💰 CALCUL BUSINESS INTERRUPTION:")
            print(f"       - Impact quotidien: {bi_details.get('daily_impact_eur', 0):,.0f}€")
            print(f"       - Stock couvre: {bi_details.get('stock_coverage_days', 0)} jours")
            print(f"       - Jours de disruption effectifs: {bi_details.get('effective_disruption_days', 0)}")
            print(f"       - Clients impactés: {bi_details.get('affected_customers_count', 0)}")
            
            breakdown = bi_details.get('calculation_breakdown', '')
            if breakdown:
                print(f"\n    📄 DÉTAIL COMPLET DU CALCUL:")
                for line in breakdown.split('\n')[:15]:  # Premiers 15 lignes
                    print(f"       {line}")
        
        print(f"    {'-'*50}")
        
        # Reasoning (condensé)
        reasoning = entity.get("reasoning", "")
        if reasoning:
            print(f"\n    📝 ANALYSE LLM (extrait):")
            if len(reasoning) > 600:
                print(f"    {reasoning[:600]}...")
            else:
                print(f"    {reasoning}")
    
    # Recommandations
    print("\n" + "-" * 40)
    print("💡 RECOMMANDATIONS:")
    
    for i, rec in enumerate(result.get("recommendations", []), 1):
        print(f"\n  {i}. [{rec.get('urgency', 'N/A')}] {rec.get('action', 'N/A')}")
        if rec.get('timeline'):
            print(f"     📅 Délai: {rec['timeline']}")
        if rec.get('estimated_cost_eur'):
            print(f"     💰 Coût estimé: {rec['estimated_cost_eur']:,.0f} EUR")
        if rec.get('rationale'):
            print(f"     📋 Justification: {rec['rationale']}")
    
    # Vérifier si LLM a été utilisé
    print("\n" + "-" * 40)
    llm_used = result.get("analysis_metadata", {}).get("llm_reasoning_used", False)
    print(f"🤖 LLM utilisé: {'OUI ✅' if llm_used else 'NON (fallback) ⚠️'}")
    
    print("\n" + "=" * 80)
    print("✅ Test terminé")
    print("=" * 80)
    
    return result, projections


if __name__ == "__main__":
    test_regulatory_analysis()
