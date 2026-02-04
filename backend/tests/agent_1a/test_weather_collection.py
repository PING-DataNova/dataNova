"""
Test de collecte météo Agent 1A
Date: 04/02/2026
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le dossier backend au path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from src.agent_1a.agent import run_agent_1a_weather


async def main():
    print("\n" + "="*70)
    print("🌦️  COLLECTE MÉTÉO - AGENT 1A")
    print("="*70)
    print("\nLancement de la collecte des alertes météo...")
    print("  - Source: OpenMeteo API")
    print("  - Prévisions: 16 jours")
    print("  - Sites: depuis BDD (sites + fournisseurs)")
    print("\n" + "-"*70)
    
    try:
        result = await run_agent_1a_weather(
            forecast_days=16,
            save_to_db=True
        )
        
        print("\n" + "="*70)
        print("📊 RÉSULTAT DE LA COLLECTE")
        print("="*70)
        
        status = result.get("status", "unknown")
        print(f"\nStatut: {status}")
        
        if status == "skipped":
            print(f"  Message: {result.get('message')}")
            print("\n⚠️ La source OpenMeteo est désactivée dans l'admin.")
            return
        
        if status == "error":
            print(f"  Erreur: {result.get('error')}")
            return
        
        # Statistiques
        print(f"\n📍 Sites analysés:")
        print(f"  - Hutchinson: {result.get('sites_count', 0)}")
        print(f"  - Fournisseurs: {result.get('suppliers_count', 0)}")
        
        print(f"\n🌤️ Alertes météo:")
        print(f"  - Total alertes: {result.get('total_alerts', 0)}")
        print(f"  - Alertes sauvegardées: {result.get('alerts_saved', 0)}")
        
        # Détail par type d'alerte
        alerts_by_type = result.get("alerts_by_type", {})
        if alerts_by_type:
            print(f"\n📋 Alertes par type:")
            for alert_type, count in alerts_by_type.items():
                print(f"    - {alert_type}: {count}")
        
        # Alertes critiques
        critical_alerts = result.get("critical_alerts", [])
        if critical_alerts:
            print(f"\n🚨 ALERTES CRITIQUES ({len(critical_alerts)}):")
            for alert in critical_alerts[:5]:  # Max 5
                print(f"    - {alert.get('site_name')}: {alert.get('alert_type')} - {alert.get('description')}")
        
        print("\n" + "="*70)
        print("✅ Collecte météo terminée avec succès !")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
