"""
Module Open-Meteo pour la collecte des données météorologiques.

Objectif: Anticiper les risques supply chain liés à la météo
- Neige → routes bloquées, retards livraisons
- Précipitations fortes → inondations, routes coupées
- Températures extrêmes → canicule, gel, conditions travail
- Vent fort → fermeture ports, ponts, transport aérien
- Alertes météo → tempêtes, orages violents

API: Open-Meteo (gratuit, sans clé, données ECMWF)
Documentation: https://open-meteo.com/en/docs
"""

import httpx
import asyncio
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)

# =============================================================================
# MODÈLES DE DONNÉES
# =============================================================================

class Location(BaseModel):
    """Localisation d'un site ou fournisseur."""
    site_id: str
    name: str
    city: str
    country: str
    latitude: float
    longitude: float
    site_type: str = "manufacturing"  # manufacturing, supplier, warehouse, hq
    criticality: str = "normal"  # critical, high, normal, low


class DailyWeather(BaseModel):
    """Prévisions météo journalières."""
    date: date
    temperature_max: float  # °C
    temperature_min: float  # °C
    precipitation_sum: float  # mm
    rain_sum: float  # mm
    snowfall_sum: float  # cm
    wind_speed_max: float  # km/h
    wind_gusts_max: float  # km/h
    weather_code: int  # WMO Weather code
    weather_description: str


class WeatherForecast(BaseModel):
    """Prévisions météo complètes pour une localisation."""
    location: Location
    forecast_days: list[DailyWeather]
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    timezone: str = "UTC"


class WeatherAlert(BaseModel):
    """Alerte météo détectée."""
    location: Location
    alert_type: str  # snow, heavy_rain, extreme_heat, extreme_cold, strong_wind, storm
    severity: str  # low, medium, high, critical
    date: date
    value: float  # Valeur mesurée (mm, cm, °C, km/h)
    threshold: float  # Seuil dépassé
    unit: str  # mm, cm, °C, km/h
    description: str
    supply_chain_risk: str  # Description du risque supply chain


# =============================================================================
# CODES MÉTÉO WMO
# =============================================================================

WMO_WEATHER_CODES = {
    0: "Ciel dégagé",
    1: "Principalement dégagé",
    2: "Partiellement nuageux",
    3: "Couvert",
    45: "Brouillard",
    48: "Brouillard givrant",
    51: "Bruine légère",
    53: "Bruine modérée",
    55: "Bruine dense",
    56: "Bruine verglaçante légère",
    57: "Bruine verglaçante dense",
    61: "Pluie légère",
    63: "Pluie modérée",
    65: "Pluie forte",
    66: "Pluie verglaçante légère",
    67: "Pluie verglaçante forte",
    71: "Neige légère",
    73: "Neige modérée",
    75: "Neige forte",
    77: "Grains de neige",
    80: "Averses légères",
    81: "Averses modérées",
    82: "Averses violentes",
    85: "Averses de neige légères",
    86: "Averses de neige fortes",
    95: "Orage",
    96: "Orage avec grêle légère",
    99: "Orage avec grêle forte",
}


# =============================================================================
# SEUILS D'ALERTE
# =============================================================================

ALERT_THRESHOLDS = {
    "snowfall": {  # cm
        "low": 5,
        "medium": 10,
        "high": 20,
        "critical": 30,
    },
    "rain": {  # mm
        "low": 20,
        "medium": 40,
        "high": 60,
        "critical": 100,
    },
    "wind_speed": {  # km/h
        "low": 50,
        "medium": 70,
        "high": 90,
        "critical": 120,
    },
    "temperature_max": {  # °C (canicule)
        "low": 32,
        "medium": 35,
        "high": 38,
        "critical": 42,
    },
    "temperature_min": {  # °C (gel)
        "low": 0,
        "medium": -5,
        "high": -10,
        "critical": -20,
    },
}

SUPPLY_CHAIN_RISKS = {
    "snow": "Routes bloquées, retards de livraison, fermeture possible du site",
    "heavy_rain": "Inondations possibles, routes coupées, risque entrepôts",
    "extreme_heat": "Conditions de travail dégradées, transport frigorifique impacté",
    "extreme_cold": "Gel des équipements, routes verglacées, chauffage renforcé",
    "strong_wind": "Fermeture ports/ponts, transport aérien annulé, risque structures",
    "storm": "Tempête majeure - tous transports impactés, risque personnel",
}


# =============================================================================
# CLIENT API OPEN-METEO
# =============================================================================

class OpenMeteoClient:
    """Client pour l'API Open-Meteo (gratuit, sans clé)."""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    # Paramètres météo à récupérer
    DAILY_PARAMS = [
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "rain_sum",
        "snowfall_sum",
        "wind_speed_10m_max",
        "wind_gusts_10m_max",
        "weather_code",
    ]
    
    def __init__(self, forecast_days: int = 16):
        """
        Initialise le client Open-Meteo.
        
        Args:
            forecast_days: Nombre de jours de prévisions (max 16)
        """
        self.forecast_days = min(forecast_days, 16)
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Ferme le client HTTP."""
        await self.client.aclose()
    
    async def get_forecast(self, location: Location) -> Optional[WeatherForecast]:
        """
        Récupère les prévisions météo pour une localisation.
        
        Args:
            location: Localisation avec coordonnées GPS
            
        Returns:
            WeatherForecast ou None si erreur
        """
        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "daily": ",".join(self.DAILY_PARAMS),
            "forecast_days": self.forecast_days,
            "timezone": "auto",
        }
        
        try:
            logger.info(
                "openmeteo_fetch_started",
                site_id=location.site_id,
                city=location.city,
                lat=location.latitude,
                lon=location.longitude,
            )
            
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Parser les données
            daily_data = data.get("daily", {})
            dates = daily_data.get("time", [])
            
            forecast_days = []
            for i, date_str in enumerate(dates):
                weather_code = daily_data.get("weather_code", [0] * len(dates))[i] or 0
                
                day_weather = DailyWeather(
                    date=datetime.strptime(date_str, "%Y-%m-%d").date(),
                    temperature_max=daily_data.get("temperature_2m_max", [0] * len(dates))[i] or 0,
                    temperature_min=daily_data.get("temperature_2m_min", [0] * len(dates))[i] or 0,
                    precipitation_sum=daily_data.get("precipitation_sum", [0] * len(dates))[i] or 0,
                    rain_sum=daily_data.get("rain_sum", [0] * len(dates))[i] or 0,
                    snowfall_sum=daily_data.get("snowfall_sum", [0] * len(dates))[i] or 0,
                    wind_speed_max=daily_data.get("wind_speed_10m_max", [0] * len(dates))[i] or 0,
                    wind_gusts_max=daily_data.get("wind_gusts_10m_max", [0] * len(dates))[i] or 0,
                    weather_code=weather_code,
                    weather_description=WMO_WEATHER_CODES.get(weather_code, "Inconnu"),
                )
                forecast_days.append(day_weather)
            
            logger.info(
                "openmeteo_fetch_completed",
                site_id=location.site_id,
                days=len(forecast_days),
            )
            
            return WeatherForecast(
                location=location,
                forecast_days=forecast_days,
                timezone=data.get("timezone", "UTC"),
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "openmeteo_http_error",
                site_id=location.site_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            return None
        except Exception as e:
            logger.error(
                "openmeteo_error",
                site_id=location.site_id,
                error=str(e),
            )
            return None
    
    def detect_alerts(self, forecast: WeatherForecast) -> list[WeatherAlert]:
        """
        Détecte les alertes météo à partir des prévisions.
        
        Args:
            forecast: Prévisions météo
            
        Returns:
            Liste des alertes détectées
        """
        alerts = []
        location = forecast.location
        
        for day in forecast.forecast_days:
            # Alerte neige
            if day.snowfall_sum > 0:
                severity = self._get_severity(day.snowfall_sum, "snowfall")
                if severity:
                    alerts.append(WeatherAlert(
                        location=location,
                        alert_type="snow",
                        severity=severity,
                        date=day.date,
                        value=day.snowfall_sum,
                        threshold=ALERT_THRESHOLDS["snowfall"][severity],
                        unit="cm",
                        description=f"Neige prévue: {day.snowfall_sum} cm",
                        supply_chain_risk=SUPPLY_CHAIN_RISKS["snow"],
                    ))
            
            # Alerte pluie forte
            if day.rain_sum > 0:
                severity = self._get_severity(day.rain_sum, "rain")
                if severity:
                    alerts.append(WeatherAlert(
                        location=location,
                        alert_type="heavy_rain",
                        severity=severity,
                        date=day.date,
                        value=day.rain_sum,
                        threshold=ALERT_THRESHOLDS["rain"][severity],
                        unit="mm",
                        description=f"Fortes pluies prévues: {day.rain_sum} mm",
                        supply_chain_risk=SUPPLY_CHAIN_RISKS["heavy_rain"],
                    ))
            
            # Alerte vent fort
            wind_max = max(day.wind_speed_max, day.wind_gusts_max)
            severity = self._get_severity(wind_max, "wind_speed")
            if severity:
                alerts.append(WeatherAlert(
                    location=location,
                    alert_type="strong_wind",
                    severity=severity,
                    date=day.date,
                    value=wind_max,
                    threshold=ALERT_THRESHOLDS["wind_speed"][severity],
                    unit="km/h",
                    description=f"Vent fort prévu: {wind_max} km/h",
                    supply_chain_risk=SUPPLY_CHAIN_RISKS["strong_wind"],
                ))
            
            # Alerte canicule
            severity = self._get_severity(day.temperature_max, "temperature_max")
            if severity:
                alerts.append(WeatherAlert(
                    location=location,
                    alert_type="extreme_heat",
                    severity=severity,
                    date=day.date,
                    value=day.temperature_max,
                    threshold=ALERT_THRESHOLDS["temperature_max"][severity],
                    unit="°C",
                    description=f"Canicule prévue: {day.temperature_max}°C",
                    supply_chain_risk=SUPPLY_CHAIN_RISKS["extreme_heat"],
                ))
            
            # Alerte gel
            severity = self._get_severity_cold(day.temperature_min)
            if severity:
                alerts.append(WeatherAlert(
                    location=location,
                    alert_type="extreme_cold",
                    severity=severity,
                    date=day.date,
                    value=day.temperature_min,
                    threshold=ALERT_THRESHOLDS["temperature_min"][severity],
                    unit="°C",
                    description=f"Gel prévu: {day.temperature_min}°C",
                    supply_chain_risk=SUPPLY_CHAIN_RISKS["extreme_cold"],
                ))
            
            # Alerte orage
            if day.weather_code >= 95:
                alerts.append(WeatherAlert(
                    location=location,
                    alert_type="storm",
                    severity="high" if day.weather_code >= 96 else "medium",
                    date=day.date,
                    value=day.weather_code,
                    threshold=95,
                    unit="code",
                    description=f"Orage prévu: {day.weather_description}",
                    supply_chain_risk=SUPPLY_CHAIN_RISKS["storm"],
                ))
        
        return alerts
    
    def _get_severity(self, value: float, metric: str) -> Optional[str]:
        """Détermine la sévérité basée sur les seuils."""
        thresholds = ALERT_THRESHOLDS.get(metric, {})
        
        if value >= thresholds.get("critical", float("inf")):
            return "critical"
        elif value >= thresholds.get("high", float("inf")):
            return "high"
        elif value >= thresholds.get("medium", float("inf")):
            return "medium"
        elif value >= thresholds.get("low", float("inf")):
            return "low"
        return None
    
    def _get_severity_cold(self, temp: float) -> Optional[str]:
        """Détermine la sévérité pour le froid (logique inversée)."""
        thresholds = ALERT_THRESHOLDS["temperature_min"]
        
        if temp <= thresholds.get("critical", float("-inf")):
            return "critical"
        elif temp <= thresholds.get("high", float("-inf")):
            return "high"
        elif temp <= thresholds.get("medium", float("-inf")):
            return "medium"
        elif temp <= thresholds.get("low", float("-inf")):
            return "low"
        return None


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

async def fetch_weather_for_sites(
    locations: list[Location],
    forecast_days: int = 16,
) -> tuple[list[WeatherForecast], list[WeatherAlert]]:
    """
    Récupère les prévisions météo pour plusieurs sites.
    
    Args:
        locations: Liste des localisations
        forecast_days: Nombre de jours de prévisions
        
    Returns:
        Tuple (forecasts, alerts)
    """
    client = OpenMeteoClient(forecast_days=forecast_days)
    
    try:
        forecasts = []
        all_alerts = []
        
        for location in locations:
            forecast = await client.get_forecast(location)
            if forecast:
                forecasts.append(forecast)
                alerts = client.detect_alerts(forecast)
                all_alerts.extend(alerts)
            
            # Petit délai pour ne pas surcharger l'API
            await asyncio.sleep(0.2)
        
        return forecasts, all_alerts
        
    finally:
        await client.close()


def format_alert_summary(alerts: list[WeatherAlert]) -> str:
    """
    Formate un résumé des alertes pour affichage.
    
    Args:
        alerts: Liste des alertes
        
    Returns:
        Résumé formaté
    """
    if not alerts:
        return "✅ Aucune alerte météo détectée"
    
    # Grouper par sévérité
    by_severity = {"critical": [], "high": [], "medium": [], "low": []}
    for alert in alerts:
        by_severity[alert.severity].append(alert)
    
    lines = [f"⚠️ {len(alerts)} alertes météo détectées:\n"]
    
    severity_icons = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
    }
    
    for severity in ["critical", "high", "medium", "low"]:
        severity_alerts = by_severity[severity]
        if severity_alerts:
            icon = severity_icons[severity]
            lines.append(f"\n{icon} {severity.upper()} ({len(severity_alerts)}):")
            for alert in severity_alerts[:5]:  # Max 5 par sévérité
                lines.append(
                    f"  • {alert.location.city} ({alert.date}): "
                    f"{alert.description}"
                )
            if len(severity_alerts) > 5:
                lines.append(f"  ... et {len(severity_alerts) - 5} autres")
    
    return "\n".join(lines)
