#!/usr/bin/env python3
"""Reset complet de la BDD et relance du workflow"""
import sys

def main():
    from src.storage.database import get_session
    from src.storage.models import (
        Document, PertinenceCheck, RiskAnalysis, 
        JudgeEvaluation, Alert
    )
    
    session = get_session()
    
    print("Nettoyage des tables...")
    session.query(JudgeEvaluation).delete()
    session.query(Alert).delete()
    session.query(RiskAnalysis).delete()
    session.query(PertinenceCheck).delete()
    session.query(Document).delete()
    session.commit()
    print("Tables nettoyees: documents, pertinence_checks, risk_analyses, judge_evaluations, alerts")
    
    session.close()
    
    # Lancer le workflow
    print("")
    print("Lancement du workflow...")
    from src.orchestration.langgraph_workflow import run_ping_workflow
    result = run_ping_workflow(keyword="CBAM", company_name="HUTCHINSON")
    
    print("")
    print("WORKFLOW TERMINE")
    print("Documents collectes: {}".format(result.get('documents_collected', 0)))
    print("Documents pertinents: {}".format(result.get('documents_pertinent', 0)))
    
    # Verifier les analyses
    session = get_session()
    from src.storage.models import RiskAnalysis
    import json
    
    analysis = session.query(RiskAnalysis).order_by(RiskAnalysis.created_at.desc()).first()
    
    if analysis:
        print("")
        print("ANALYSE SAUVEGARDEE EN BDD:")
        print("  ID: {}".format(analysis.id))
        print("  Document ID: {}".format(analysis.document_id))
        print("  Risk Score: {}".format(analysis.risk_score))
        print("  Risk Level: {}".format(analysis.risk_level))
        
        if analysis.analysis_metadata:
            data = analysis.analysis_metadata if isinstance(analysis.analysis_metadata, dict) else json.loads(analysis.analysis_metadata)
            weather = data.get("weather_risk_summary", {})
            print("")
            print("DONNEES METEO:")
            print("  Entites avec alertes: {}".format(weather.get('entities_with_alerts', 0)))
            print("  Total alertes: {}".format(weather.get('total_alerts', 0)))
            print("  Severite max: {}".format(weather.get('max_severity', 'N/A')))
            print("  Score meteo moyen: {}".format(weather.get('average_weather_risk_score', 0)))
            if weather.get("alerts_by_type"):
                print("  Types: {}".format(weather.get('alerts_by_type')))
    else:
        print("Aucune analyse trouvee en BDD")
    
    session.close()


if __name__ == "__main__":
    main()
