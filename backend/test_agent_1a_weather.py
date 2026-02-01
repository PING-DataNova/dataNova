"""Test de la fonction run_agent_1a_weather avec sauvegarde en BDD."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.agent_1a.agent import run_agent_1a_weather


async def main():
    print("=" * 70)
    print("TEST COLLECTE METEOROLOGIQUE - AGENT 1A")
    print("=" * 70)
    
    result = await run_agent_1a_weather(
        forecast_days=16,
        save_to_db=True
    )
    
    print("\n" + "=" * 70)
    print("RESULTAT")
    print("=" * 70)
    print(f"Status: {result['status']}")
    print(f"Sites surveilles: {result['sites_count']}")
    print(f"Previsions collectees: {result['forecasts_fetched']}")
    print(f"Alertes detectees: {result['alerts_detected']}")
    print(f"Alertes sauvegardees: {result['alerts_saved']}")
    
    if result.get('alerts_by_type'):
        print("\nAlertes par type:")
        for alert_type, count in result['alerts_by_type'].items():
            print(f"  - {alert_type}: {count}")
    
    if result.get('alerts_by_severity'):
        print("\nAlertes par severite:")
        for severity, count in result['alerts_by_severity'].items():
            print(f"  - {severity}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
