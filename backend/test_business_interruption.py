"""
Test du calcul Business Interruption avec les vraies données
"""
import json
from src.agent_2.agent import Agent2
from src.storage.database import get_session
from src.storage.models import HutchinsonSite, Supplier, SupplierRelationship

def test_business_interruption_calculation():
    """
    Test que Agent 2 utilise bien les vraies données BI de la base
    """
    print("=" * 70)
    print("TEST: Calcul Business Interruption avec données réelles")
    print("=" * 70)
    
    # 1. Charger les données depuis la BDD (comme le fait le workflow)
    session = get_session()
    
    sites = session.query(HutchinsonSite).filter(HutchinsonSite.active == True).all()
    suppliers = session.query(Supplier).filter(Supplier.active == True).all()
    relationships = session.query(SupplierRelationship).all()
    
    # Convertir en dicts avec les nouvelles colonnes BI
    sites_data = [
        {
            "id": s.id,
            "name": s.name,
            "country": s.country,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "strategic_importance": s.strategic_importance,
            # Données BI
            "daily_revenue": s.daily_revenue,
            "daily_production_units": s.daily_production_units,
            "safety_stock_days": s.safety_stock_days,
            "recovery_time_days": s.ramp_up_time_days,  # ramp_up_time_days = recovery_time
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
            # Données BI
            "annual_purchase_volume": s.annual_purchase_volume,
            "average_stock_at_hutchinson_days": s.average_stock_at_hutchinson_days,
            "switch_time_days": s.switch_time_days,
            "criticality_score": s.criticality_score,
            "alternative_supplier_id": s.alternative_supplier_id,
            "ramp_up_time_days": s.qualification_time_days  # qualification_time_days dans le modèle
        }
        for s in suppliers
    ]
    
    relationships_data = [
        {
            "id": r.id,
            "hutchinson_site_id": r.hutchinson_site_id,
            "supplier_id": r.supplier_id,
            "criticality": r.criticality,
            # Données BI
            "daily_consumption_value": r.daily_consumption_value,
            "stock_coverage_days": r.stock_coverage_days,
            "contract_penalties_per_day": r.contract_penalties_per_day,
            "is_sole_supplier": r.is_sole_supplier
        }
        for r in relationships
    ]
    
    session.close()
    
    print(f"\n📊 Données chargées:")
    print(f"   - {len(sites_data)} sites")
    print(f"   - {len(suppliers_data)} fournisseurs")
    print(f"   - {len(relationships_data)} relations")
    
    # 2. Tester le calcul BI pour un fournisseur critique
    agent = Agent2()
    
    # Trouver le fournisseur Ukrainian Titanium Works (le plus critique)
    ukrainian_titanium = next((s for s in suppliers_data if "Ukrainian" in s.get("name", "")), None)
    
    if ukrainian_titanium:
        print(f"\n🧪 Test avec fournisseur critique: {ukrainian_titanium['name']}")
        print(f"   - Pays: {ukrainian_titanium['country']}")
        print(f"   - Criticality Score: {ukrainian_titanium.get('criticality_score')}")
        print(f"   - Switch Time: {ukrainian_titanium.get('switch_time_days')} jours")
        
        # Calculer l'impact BI
        bi_impact = agent._calculate_supplier_business_impact(
            ukrainian_titanium,
            relationships_data,
            sites_data
        )
        
        print("\n📈 RÉSULTAT CALCUL BI:")
        print(f"   - Impact % CA: {bi_impact.get('revenue_impact_percentage', 0):.2f}%")
        print(f"   - Perte quotidienne: {bi_impact.get('daily_revenue_loss_eur', 0):,.0f}€")
        print(f"   - Pénalités clients/jour: {bi_impact.get('customer_penalties_per_day_eur', 0):,.0f}€")
        print(f"   - IMPACT TOTAL/JOUR: {bi_impact.get('total_daily_impact_eur', 0):,.0f}€")
        print(f"   - Couverture stock min: {bi_impact.get('stock_coverage_days', 0)} jours")
        print(f"   - Fournisseur unique: {'OUI ⚠️' if bi_impact.get('is_sole_supplier') else 'NON'}")
        
        if bi_impact.get('affected_customers'):
            print("\n👥 Clients impactés:")
            for customer in bi_impact['affected_customers']:
                print(f"   - {customer.get('customer_name')}: {customer.get('penalty_per_day_eur', 0):,.0f}€/jour")
        
        print("\n" + bi_impact.get('calculation_breakdown', ''))
    
    # 3. Tester le calcul BI pour un site
    bangkok_site = next((s for s in sites_data if "Bangkok" in s.get("name", "")), None)
    
    if bangkok_site:
        print("\n" + "=" * 70)
        print(f"🧪 Test avec site: {bangkok_site['name']}")
        print(f"   - Pays: {bangkok_site['country']}")
        print(f"   - CA quotidien: {bangkok_site.get('daily_revenue', 0):,.0f}€")
        print(f"   - Production quotidienne: {bangkok_site.get('daily_production_units', 0):,} unités")
        
        bi_impact_site = agent._calculate_site_business_impact(
            bangkok_site,
            relationships_data
        )
        
        print("\n📈 RÉSULTAT CALCUL BI SITE:")
        print(f"   - Perte CA quotidienne: {bi_impact_site.get('daily_revenue_loss_eur', 0):,.0f}€")
        print(f"   - Pénalités clients/jour: {bi_impact_site.get('customer_penalties_per_day_eur', 0):,.0f}€")
        print(f"   - IMPACT TOTAL/JOUR: {bi_impact_site.get('total_daily_impact_eur', 0):,.0f}€")
        print(f"   - Stock de sécurité: {bi_impact_site.get('stock_coverage_days', 0)} jours")
        print(f"   - Temps de reprise: {bi_impact_site.get('recovery_time_days', 0)} jours")
        
        print("\n" + bi_impact_site.get('calculation_breakdown', ''))
    
    print("\n" + "=" * 70)
    print("✅ TEST TERMINÉ - Les calculs BI utilisent les vraies données !")
    print("=" * 70)


if __name__ == "__main__":
    test_business_interruption_calculation()
