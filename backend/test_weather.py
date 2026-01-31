"""
Test du module Open-Meteo pour la veille météo supply chain.

Ce script:
1. Charge les localisations des sites Hutchinson + fournisseurs
2. Récupère les prévisions météo (16 jours) via Open-Meteo API
3. Détecte les alertes météo (neige, pluie, vent, températures extrêmes)
4. Affiche un résumé des risques supply chain
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Ajouter le chemin du backend au path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.agent_1a.tools.weather import (
    OpenMeteoClient,
    Location,
    fetch_weather_for_sites,
    format_alert_summary,
)

console = Console()


def load_locations() -> list[Location]:
    """Charge les localisations depuis le fichier de config."""
    config_path = Path(__file__).parent / "config" / "sites_locations.json"
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    locations = []
    
    # Sites Hutchinson
    for site in data.get("hutchinson_sites", []):
        locations.append(Location(
            site_id=site["site_id"],
            name=site["name"],
            city=site["city"],
            country=site["country"],
            latitude=site["latitude"],
            longitude=site["longitude"],
            site_type=site.get("site_type", "manufacturing"),
            criticality=site.get("criticality", "normal"),
        ))
    
    # Fournisseurs
    for supplier in data.get("suppliers", []):
        locations.append(Location(
            site_id=supplier["site_id"],
            name=supplier["name"],
            city=supplier["city"],
            country=supplier["country"],
            latitude=supplier["latitude"],
            longitude=supplier["longitude"],
            site_type="supplier",
            criticality=supplier.get("criticality", "normal"),
        ))
    
    # Ports
    for port in data.get("ports", []):
        locations.append(Location(
            site_id=port["site_id"],
            name=port["name"],
            city=port["city"],
            country=port["country"],
            latitude=port["latitude"],
            longitude=port["longitude"],
            site_type="port",
            criticality=port.get("criticality", "high"),
        ))
    
    return locations


async def main():
    """Point d'entrée principal."""
    console.print(Panel.fit(
        "🌦️ TEST MODULE OPEN-METEO - VEILLE MÉTÉO SUPPLY CHAIN",
        style="bold cyan"
    ))
    
    # === ÉTAPE 1 : Charger les localisations ===
    console.print("\n[bold cyan]📍 ÉTAPE 1 : Chargement des localisations[/bold cyan]")
    
    locations = load_locations()
    console.print(f"✅ {len(locations)} localisations chargées")
    
    # Afficher le résumé
    sites_table = Table(title="Sites à surveiller")
    sites_table.add_column("Type", style="cyan")
    sites_table.add_column("Nombre", justify="right")
    
    by_type = {}
    for loc in locations:
        by_type[loc.site_type] = by_type.get(loc.site_type, 0) + 1
    
    for site_type, count in sorted(by_type.items()):
        sites_table.add_row(site_type.capitalize(), str(count))
    
    console.print(sites_table)
    
    # === ÉTAPE 2 : Récupérer les prévisions météo ===
    console.print("\n[bold cyan]🌤️ ÉTAPE 2 : Récupération des prévisions météo (16 jours)[/bold cyan]")
    
    forecasts, alerts = await fetch_weather_for_sites(locations, forecast_days=16)
    
    console.print(f"✅ {len(forecasts)} prévisions récupérées")
    
    # Afficher quelques prévisions
    preview_table = Table(title="Aperçu des prévisions (aujourd'hui)")
    preview_table.add_column("Site", style="cyan")
    preview_table.add_column("Ville")
    preview_table.add_column("Temp Max", justify="right")
    preview_table.add_column("Temp Min", justify="right")
    preview_table.add_column("Pluie", justify="right")
    preview_table.add_column("Neige", justify="right")
    preview_table.add_column("Vent", justify="right")
    preview_table.add_column("Météo")
    
    for forecast in forecasts[:10]:  # Max 10
        if forecast.forecast_days:
            today = forecast.forecast_days[0]
            preview_table.add_row(
                forecast.location.site_id[:15],
                forecast.location.city,
                f"{today.temperature_max:.1f}°C",
                f"{today.temperature_min:.1f}°C",
                f"{today.rain_sum:.1f}mm",
                f"{today.snowfall_sum:.1f}cm",
                f"{today.wind_speed_max:.0f}km/h",
                today.weather_description[:20],
            )
    
    console.print(preview_table)
    
    # === ÉTAPE 3 : Analyser les alertes ===
    console.print("\n[bold cyan]⚠️ ÉTAPE 3 : Analyse des alertes météo[/bold cyan]")
    
    console.print(format_alert_summary(alerts))
    
    if alerts:
        # Tableau détaillé des alertes critiques/high
        critical_alerts = [a for a in alerts if a.severity in ("critical", "high")]
        
        if critical_alerts:
            alerts_table = Table(title="Alertes critiques et hautes priorité")
            alerts_table.add_column("Sévérité", style="bold")
            alerts_table.add_column("Site")
            alerts_table.add_column("Ville")
            alerts_table.add_column("Date")
            alerts_table.add_column("Type")
            alerts_table.add_column("Valeur", justify="right")
            alerts_table.add_column("Risque supply chain")
            
            for alert in critical_alerts[:20]:  # Max 20
                severity_style = "red" if alert.severity == "critical" else "yellow"
                alerts_table.add_row(
                    f"[{severity_style}]{alert.severity.upper()}[/{severity_style}]",
                    alert.location.site_id[:15],
                    alert.location.city,
                    str(alert.date),
                    alert.alert_type,
                    f"{alert.value:.1f} {alert.unit}",
                    alert.supply_chain_risk[:40] + "...",
                )
            
            console.print(alerts_table)
    
    # === RÉSUMÉ FINAL ===
    console.print("\n" + "=" * 80)
    
    # Stats des alertes par type
    alert_types = {}
    for alert in alerts:
        alert_types[alert.alert_type] = alert_types.get(alert.alert_type, 0) + 1
    
    console.print(Panel.fit(
        f"🎉 VEILLE MÉTÉO TERMINÉE\n\n"
        f"Sites surveillés : {len(locations)}\n"
        f"Prévisions récupérées : {len(forecasts)}\n"
        f"Alertes détectées : {len(alerts)}\n"
        f"  - Critiques : {len([a for a in alerts if a.severity == 'critical'])}\n"
        f"  - Hautes : {len([a for a in alerts if a.severity == 'high'])}\n"
        f"  - Moyennes : {len([a for a in alerts if a.severity == 'medium'])}\n"
        f"  - Basses : {len([a for a in alerts if a.severity == 'low'])}\n"
        f"\nTypes d'alertes : {alert_types}",
        style="green"
    ))


if __name__ == "__main__":
    asyncio.run(main())
