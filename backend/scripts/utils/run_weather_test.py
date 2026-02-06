#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script pour lancer le workflow et verifier l'integration meteo"""
import sys
import asyncio

# Forcer UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def main():
    from src.orchestration.langgraph_workflow import run_ping_workflow
    from src.storage.database import get_session
    from src.storage.models import RiskAnalysis, WeatherAlert
    import json
    
    # 1. Verifier les alertes meteo disponibles
    session = get_session()
    alerts_count = session.query(WeatherAlert).count()
    print(f"Alertes meteo en base: {alerts_count}")
    session.close()
    
    # 2. Lancer le workflow
    print("LANCEMENT DU WORKFLOW PING AVEC INTEGRATION METEO")
    
    result = run_ping_workflow(keyword="CBAM", company_name="HUTCHINSON")
    
    print("RESULTAT DU WORKFLOW")
    print(f"Documents collectes: {result.get('documents_collected', 0)}")
    print(f"Documents pertinents: {result.get('documents_pertinent', 0)}")
    print(f"Risk score: {result.get('risk_score', 'N/A')}")
    print(f"Risk level: {result.get('risk_level', 'N/A')}")
    print(f"Decision Judge: {result.get('judge_decision', 'N/A')}")
    
    # 3. Verifier l'analyse de risque
    session = get_session()
    analysis = session.query(RiskAnalysis).order_by(RiskAnalysis.created_at.desc()).first()
    
    if analysis and analysis.extra_data:
        data = analysis.extra_data if isinstance(analysis.extra_data, dict) else json.loads(analysis.extra_data)
        weather = data.get("weather_risk_summary", {})
        
        print("DONNEES METEO INTEGREES:")
        print(f"  Total alertes: {weather.get('total_alerts', 0)}")
        print(f"  Entites avec alertes: {weather.get('entities_with_alerts', 0)}")
        avg = weather.get('average_weather_risk_score', 0)
        print(f"  Score meteo moyen: {avg}")
        print(f"  Severite max: {weather.get('max_severity', 'N/A')}")
        
        if weather.get("alerts_by_type"):
            print(f"  Types: {weather.get('alerts_by_type')}")
    else:
        print("Pas de donnees meteo dans l'analyse")
    
    session.close()
    print("Verification terminee")


if __name__ == "__main__":
    main()
