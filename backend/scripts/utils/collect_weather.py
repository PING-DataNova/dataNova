"""Script pour collecter les alertes météo Open-Meteo"""

import asyncio
from src.agent_1a.tools.weather import OpenMeteoClient, Location, fetch_weather_for_sites
from src.storage.database import get_session
from src.storage.models import HutchinsonSite, Supplier, WeatherAlert

def collect_weather_alerts():
    session = get_session()
    
    # Récupérer les sites et fournisseurs
    sites = session.query(HutchinsonSite).all()
    suppliers = session.query(Supplier).all()
    
    # Créer les locations
    locations = []
    for s in sites:
        if s.latitude and s.longitude:
            locations.append(Location(
                site_id=s.code,
                name=s.name,
                city=s.city or 'Unknown',
                country=s.country,
                latitude=s.latitude,
                longitude=s.longitude,
                site_type='manufacturing',
                criticality='high'
            ))
            
    for s in suppliers:
        if s.latitude and s.longitude:
            locations.append(Location(
                site_id=s.code,
                name=s.name,
                city=s.city or 'Unknown',
                country=s.country,
                latitude=s.latitude,
                longitude=s.longitude,
                site_type='supplier',
                criticality='normal'
            ))
    
    print(f"📍 Locations à analyser: {len(locations)}")
    
    # Collecter les alertes via Open-Meteo
    alerts = asyncio.run(fetch_weather_for_sites(locations))
    print(f"⚠️  Alertes météo trouvées: {len(alerts)}")
    
    # Sauvegarder en BDD
    saved = 0
    for alert in alerts:
        wa = WeatherAlert(
            site_id=alert.site_id,
            site_name=alert.site_name,
            city=alert.city,
            country=alert.country,
            latitude=alert.latitude,
            longitude=alert.longitude,
            site_type=alert.site_type,
            site_criticality=alert.site_criticality,
            alert_type=alert.alert_type,
            severity=alert.severity,
            alert_date=alert.alert_date,
            value=alert.value,
            threshold=alert.threshold,
            unit=alert.unit,
            description=alert.description,
            supply_chain_risk=alert.supply_chain_risk
        )
        session.add(wa)
        saved += 1
    
    session.commit()
    print(f"✅ Alertes sauvegardées en BDD: {saved}")
    
    # Résumé par type
    if alerts:
        types = {}
        for a in alerts:
            types[a.alert_type] = types.get(a.alert_type, 0) + 1
        print("\n📊 Répartition par type:")
        for t, c in types.items():
            print(f"   - {t}: {c}")
    
    session.close()
    return saved

if __name__ == "__main__":
    print("=" * 50)
    print("🌤️  COLLECTE ALERTES MÉTÉO OPEN-METEO")
    print("=" * 50)
    collect_weather_alerts()
