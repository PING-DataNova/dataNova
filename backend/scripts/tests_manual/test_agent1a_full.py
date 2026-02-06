#!/usr/bin/env python3
"""
Test Agent 1A - Collecte complète (EUR-Lex + OpenMeteo)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

import asyncio
from src.agent_1a.agent import run_agent_1a_by_domain, run_agent_1a_weather

async def main():
    print("=" * 70)
    print("🚀 AGENT 1A - COLLECTE COMPLÈTE")
    print("=" * 70)
    
    # 1. Collecte EUR-Lex
    print("\n" + "=" * 70)
    print("📜 COLLECTE EUR-LEX (Réglementaire)")
    print("=" * 70)
    
    try:
        eurlex_result = await run_agent_1a_by_domain(
            max_documents=5,  # Limiter pour éviter rate limit
            domains=["15", "13"]  # 15=Environnement, 13=Industrie
        )
        
        print(f"\nStatut EUR-Lex: {eurlex_result.get('status')}")
        if eurlex_result.get('status') == 'success':
            print(f"  Documents collectés: {eurlex_result.get('documents_collected', 0)}")
            print(f"  Nouveaux documents: {eurlex_result.get('documents_new', 0)}")
        elif eurlex_result.get('status') == 'skipped':
            print(f"  Source désactivée: {eurlex_result.get('message')}")
        else:
            print(f"  Erreur: {eurlex_result.get('error', 'Unknown')}")
    except Exception as e:
        print(f"  ❌ Erreur EUR-Lex: {e}")
        eurlex_result = {"status": "error", "error": str(e)}
    
    # 2. Collecte OpenMeteo
    print("\n" + "=" * 70)
    print("🌤️  COLLECTE OPENMETEO (Météo)")
    print("=" * 70)
    
    try:
        weather_result = await run_agent_1a_weather(
            forecast_days=7,
            save_to_db=True
        )
        
        print(f"\nStatut OpenMeteo: {weather_result.get('status')}")
        if weather_result.get('status') == 'success':
            alerts = weather_result.get('alerts', {})
            print(f"  Sites analysés: {weather_result.get('sites', {}).get('total', 0)}")
            print(f"  Alertes détectées: {alerts.get('total', 0)}")
            print(f"    - Critical: {alerts.get('by_severity', {}).get('critical', 0)}")
            print(f"    - High: {alerts.get('by_severity', {}).get('high', 0)}")
            print(f"    - Medium: {alerts.get('by_severity', {}).get('medium', 0)}")
            print(f"    - Low: {alerts.get('by_severity', {}).get('low', 0)}")
        elif weather_result.get('status') == 'skipped':
            print(f"  Source désactivée: {weather_result.get('message')}")
        else:
            print(f"  Erreur: {weather_result.get('error', 'Unknown')}")
    except Exception as e:
        print(f"  ❌ Erreur OpenMeteo: {e}")
        weather_result = {"status": "error", "error": str(e)}
    
    # 3. Résumé
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ COLLECTE AGENT 1A")
    print("=" * 70)
    print(f"EUR-Lex: {eurlex_result.get('status')}")
    print(f"OpenMeteo: {weather_result.get('status')}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
