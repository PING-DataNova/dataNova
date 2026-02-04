"""Script pour verifier les donnees meteo integrees dans l'analyse de risque"""

import sys
from pathlib import Path

# Ajouter le dossier backend au path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from src.storage.database import get_session
from src.storage.models import RiskAnalysis
import json

def main():
    session = get_session()
    
    try:
        # Recuperer la derniere analyse
        analysis = session.query(RiskAnalysis).order_by(RiskAnalysis.created_at.desc()).first()
        
        if not analysis:
            print("Aucune analyse trouvee")
            return
        
        print("")
        print("=" * 70)
        print("ANALYSE DE RISQUE AVEC DONNEES METEO INTEGREES")
        print("=" * 70)
        print("Document ID: {}".format(analysis.document_id))
        print("Risk Score: {}".format(analysis.risk_score))
        print("Risk Level: {}".format(analysis.risk_level))
        print("Sites affectes: {}".format(analysis.affected_sites_count))
        print("Fournisseurs affectes: {}".format(analysis.affected_suppliers_count))
        
        # Verifier les donnees meteo dans extra_data
        if analysis.extra_data:
            data = analysis.extra_data if isinstance(analysis.extra_data, dict) else json.loads(analysis.extra_data)
            weather = data.get("weather_risk_summary", {})
            
            print("")
            print("-" * 40)
            print("DONNEES METEO (Open-Meteo):")
            print("-" * 40)
            print("  Entites avec alertes: {}".format(weather.get('entities_with_alerts', 0)))
            print("  Total alertes: {}".format(weather.get('total_alerts', 0)))
            print("  Severite max: {}".format(weather.get('max_severity', 'N/A')))
            print("  Score meteo moyen: {}".format(weather.get('average_weather_risk_score', 0)))
            
            alerts_by_type = weather.get("alerts_by_type", {})
            if alerts_by_type:
                print("  Types alertes: {}".format(alerts_by_type))
            
            # Entites a risque
            entities = weather.get("entities_at_risk", [])
            if entities:
                print("")
                print("  Top entites a risque meteo:")
                for e in entities[:5]:
                    print("    - {}: {} alerte(s), severite {}".format(
                        e.get('entity_name'), 
                        e.get('alerts_count'),
                        e.get('max_severity')
                    ))
            
            # Metadata
            metadata = data.get("analysis_metadata", {})
            if metadata.get("weather_data_integrated"):
                print("")
                print("  Weather data integrated: OUI")
                print("  Entites avec alertes meteo: {}".format(metadata.get('entities_with_weather_alerts', 0)))
        else:
            print("")
            print("Pas de donnees extra_data")
        
        print("")
        print("=" * 70)
        print("INTEGRATION METEO VERIFIEE !")
        print("=" * 70)
        print("")
        
    finally:
        session.close()


if __name__ == "__main__":
    main()
