#!/usr/bin/env python3
"""Affiche le contenu de la table risk_analyses"""
import json
from src.storage.database import get_session
from src.storage.models import RiskAnalysis

def main():
    session = get_session()
    analyses = session.query(RiskAnalysis).all()
    
    print("=" * 70)
    print("CONTENU DE LA TABLE risk_analyses")
    print("=" * 70)
    print("Nombre d'analyses: {}".format(len(analyses)))
    
    for a in analyses:
        print("")
        print("-" * 50)
        print("ID: {}".format(a.id))
        print("Document ID: {}".format(a.document_id))
        print("Risk Score: {}".format(a.risk_score))
        print("Risk Level: {}".format(a.risk_level))
        print("Supply Chain Impact: {}".format(a.supply_chain_impact))
        
        # Sites et fournisseurs affectes
        if a.affected_sites:
            sites = json.loads(a.affected_sites) if isinstance(a.affected_sites, str) else a.affected_sites
            print("Sites affectes: {}".format(len(sites) if isinstance(sites, list) else "N/A"))
        
        if a.affected_suppliers:
            suppliers = json.loads(a.affected_suppliers) if isinstance(a.affected_suppliers, str) else a.affected_suppliers
            print("Fournisseurs affectes: {}".format(len(suppliers) if isinstance(suppliers, list) else "N/A"))
        
        # Donnees meteo dans analysis_metadata
        if a.analysis_metadata:
            meta = json.loads(a.analysis_metadata) if isinstance(a.analysis_metadata, str) else a.analysis_metadata
            
            print("")
            print("  RISQUE REGLEMENTAIRE:")
            print("    Risk Score 360: {}".format(meta.get("risk_score_360", "N/A")))
            print("    Severity Score: {}".format(meta.get("severity_score", "N/A")))
            print("    Urgency Score: {}".format(meta.get("urgency_score", "N/A")))
            print("    Business Interruption: {}".format(meta.get("business_interruption_score", "N/A")))
            
            weather = meta.get("weather_risk_summary", {})
            if weather:
                print("")
                print("  RISQUE CLIMATIQUE (Open-Meteo):")
                print("    Total alertes: {}".format(weather.get("total_alerts", 0)))
                print("    Entites avec alertes: {}".format(weather.get("entities_with_alerts", 0)))
                print("    Score meteo moyen: {}".format(weather.get("average_weather_risk_score", 0)))
                print("    Severite max: {}".format(weather.get("max_severity", "N/A")))
                print("    Types d'alertes: {}".format(weather.get("alerts_by_type", {})))
            else:
                print("")
                print("  RISQUE CLIMATIQUE: Pas de donnees meteo")
        
        # Recommandations (apercu)
        if a.recommendations:
            reco = a.recommendations[:200] + "..." if len(a.recommendations) > 200 else a.recommendations
            print("")
            print("  RECOMMANDATIONS (apercu):")
            print("    {}".format(reco))
    
    session.close()
    print("")
    print("=" * 70)


if __name__ == "__main__":
    main()
