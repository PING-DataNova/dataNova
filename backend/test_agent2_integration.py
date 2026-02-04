"""
Test d'intégration complet : Agent 2 avec données BI réelles
Simule l'analyse d'un événement géopolitique en Ukraine
"""
import json
from src.agent_2.agent import Agent2
from src.storage.database import get_session
from src.storage.models import HutchinsonSite, Supplier, SupplierRelationship


def test_agent2_ukraine_crisis():
    """
    Test complet : Analyse d'une crise géopolitique en Ukraine
    avec calcul d'impact Business Interruption réel
    """
    print("=" * 70)
    print("TEST INTÉGRATION: Agent 2 - Crise géopolitique Ukraine")
    print("=" * 70)
    
    # 1. Préparer le document simulant une crise Ukraine
    document = {
        "id": "test-ukraine-crisis-001",
        "title": "Escalade du conflit en Ukraine - Fermeture des usines",
        "event_type": "geopolitique",
        "event_subtype": "conflit_arme",
        "content": """
        La situation en Ukraine s'est brutalement dégradée. Les combats 
        s'intensifient dans les zones industrielles, forçant la fermeture 
        temporaire de nombreuses usines, dont Ukrainian Titanium Works, 
        principal fournisseur de titane pour l'industrie aéronautique européenne.
        Les experts estiment une durée de perturbation de 60 à 90 jours minimum.
        """,
        "geographic_scope": {
            "directly_affected_countries": ["Ukraine"],
            "indirectly_affected_countries": ["Poland", "Romania", "Germany", "France"],
            "coordinates": {"latitude": 48.3794, "longitude": 31.1656}  # Ukraine centre
        },
        "extra_metadata": {
            "severity": "critical",
            "source": "test_scenario"
        }
    }
    
    pertinence_result = {
        "pertinence": "OUI",
        "confidence": 0.95,
        "justification": "Impact direct sur fournisseur stratégique en Ukraine"
    }
    
    # 2. Charger les données depuis la BDD
    session = get_session()
    
    sites = session.query(HutchinsonSite).filter(HutchinsonSite.active == True).all()
    suppliers = session.query(Supplier).filter(Supplier.active == True).all()
    relationships = session.query(SupplierRelationship).all()
    
    # Convertir en dicts
    sites_data = [
        {
            "id": s.id,
            "name": s.name,
            "country": s.country,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "strategic_importance": s.strategic_importance,
            "daily_revenue": s.daily_revenue,
            "daily_production_units": s.daily_production_units,
            "safety_stock_days": s.safety_stock_days,
            "recovery_time_days": s.ramp_up_time_days,
            "key_customers": s.key_customers or []
        }
        for s in sites
    ]
    
    suppliers_data = [
        {
            "id": s.id,
            "name": s.name,
            "country": s.country,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "annual_purchase_volume": s.annual_purchase_volume,
            "average_stock_at_hutchinson_days": s.average_stock_at_hutchinson_days,
            "switch_time_days": s.switch_time_days,
            "criticality_score": s.criticality_score,
            "alternative_supplier_id": s.alternative_supplier_id,
            "ramp_up_time_days": s.qualification_time_days
        }
        for s in suppliers
    ]
    
    relationships_data = [
        {
            "id": r.id,
            "hutchinson_site_id": r.hutchinson_site_id,
            "supplier_id": r.supplier_id,
            "criticality": r.criticality,
            "daily_consumption_value": r.daily_consumption_value,
            "stock_coverage_days": r.stock_coverage_days,
            "contract_penalties_per_day": r.contract_penalties_per_day,
            "is_sole_supplier": r.is_sole_supplier
        }
        for r in relationships
    ]
    
    session.close()
    
    # 3. Lancer Agent 2
    print("\n🤖 Lancement de l'analyse Agent 2...")
    agent = Agent2()
    
    risk_analysis, risk_projections = agent.analyze(
        document=document,
        pertinence_result=pertinence_result,
        sites=sites_data,
        suppliers=suppliers_data,
        supplier_relationships=relationships_data
    )
    
    # 4. Afficher les résultats
    print("\n" + "=" * 70)
    print("📊 RÉSULTATS ANALYSE AGENT 2")
    print("=" * 70)
    
    print(f"\n📈 SCORES GLOBAUX:")
    print(f"   - Niveau de risque: {risk_analysis.get('overall_risk_level')}")
    print(f"   - Risk Score 360°: {risk_analysis.get('risk_score_360', 0):.1f}/100")
    print(f"   - BI Score: {risk_analysis.get('business_interruption_score', 0):.1f}/100")
    print(f"   - Jours de disruption estimés: {risk_analysis.get('estimated_disruption_days', 0)}")
    print(f"   - Impact CA global: {risk_analysis.get('revenue_impact_percentage', 0):.1f}%")
    
    print(f"\n🏭 SITES AFFECTÉS: {risk_analysis.get('affected_sites_count', 0)}")
    for site in risk_analysis.get('affected_sites', []):
        print(f"   - {site.get('name')}: Risk={site.get('risk_score', 0):.1f}, BI={site.get('business_interruption_score', 0):.1f}")
    
    print(f"\n📦 FOURNISSEURS AFFECTÉS: {risk_analysis.get('affected_suppliers_count', 0)}")
    for supplier in risk_analysis.get('affected_suppliers', []):
        print(f"   - {supplier.get('name')}: Risk={supplier.get('risk_score', 0):.1f}, BI={supplier.get('business_interruption_score', 0):.1f}")
    
    # 5. Afficher les détails des projections concernées
    print("\n" + "=" * 70)
    print("📋 DÉTAILS DES PROJECTIONS (entités concernées)")
    print("=" * 70)
    
    concerned = [p for p in risk_projections if p.get('is_concerned')]
    for proj in concerned:
        print(f"\n🔍 {proj.get('entity_type').upper()}: {proj.get('entity_name')}")
        print(f"   - Risk Score: {proj.get('risk_score', 0):.1f}")
        print(f"   - BI Score: {proj.get('business_interruption_score', 0):.1f}")
        print(f"   - Disruption Days: {proj.get('estimated_disruption_days', 0)}")
        print(f"   - Revenue Impact: {proj.get('revenue_impact_percentage', 0):.1f}%")
        
        # Afficher les détails BI si disponibles
        bi_details = proj.get('business_impact_details')
        if bi_details:
            print(f"   📊 IMPACT FINANCIER:")
            print(f"      - Impact total/jour: {bi_details.get('total_daily_impact_eur', 0):,.0f}€")
            print(f"      - Couverture stock: {bi_details.get('stock_coverage_days', 0)} jours")
            if bi_details.get('is_sole_supplier'):
                print(f"      ⚠️  FOURNISSEUR UNIQUE - RISQUE CRITIQUE")
            if bi_details.get('switch_time_days'):
                print(f"      - Temps substitution: {bi_details.get('switch_time_days')} jours")
    
    # 6. Afficher les recommandations
    print("\n" + "=" * 70)
    print("💡 RECOMMANDATIONS")
    print("=" * 70)
    recommendations = risk_analysis.get('recommendations', [])
    if isinstance(recommendations, list):
        for i, rec in enumerate(recommendations, 1):
            if isinstance(rec, dict):
                print(f"\n{i}. [{rec.get('priority', 'N/A')}] {rec.get('action', rec)}")
            else:
                print(f"\n{i}. {rec}")
    else:
        print(recommendations)
    
    print("\n" + "=" * 70)
    print("✅ TEST INTÉGRATION TERMINÉ")
    print("=" * 70)
    
    return risk_analysis, risk_projections


if __name__ == "__main__":
    test_agent2_ukraine_crisis()
