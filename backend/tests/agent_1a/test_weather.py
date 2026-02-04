# Tests unitaires pour le module weather

import pytest
import sys
from pathlib import Path
from datetime import datetime, date

backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from src.agent_1a.tools.weather import (
    Location,
    DailyWeather,
    WeatherAlert,
    WeatherForecast,
    OpenMeteoClient,
    format_alert_summary,
)


class TestLocation:
    def test_location_creation(self):
        loc = Location(
            site_id="SITE001",
            name="Site Paris",
            city="Paris",
            country="France",
            latitude=48.8566,
            longitude=2.3522,
            site_type="warehouse",
            criticality="high"
        )
        assert loc.site_id == "SITE001"
        assert loc.city == "Paris"
        assert loc.latitude == 48.8566

    def test_location_coordinates(self):
        loc = Location(
            site_id="SITE002",
            name="Site Lyon",
            city="Lyon",
            country="France",
            latitude=45.75,
            longitude=4.85,
            site_type="factory",
            criticality="medium"
        )
        assert -90 <= loc.latitude <= 90
        assert -180 <= loc.longitude <= 180


class TestDailyWeather:
    def test_daily_weather_creation(self):
        weather = DailyWeather(
            date=date.today(),
            temperature_max=25.0,
            temperature_min=15.0,
            precipitation_sum=5.0,
            rain_sum=4.0,
            snowfall_sum=0.0,
            wind_speed_max=30.0,
            wind_gusts_max=45.0,
            weather_code=3,
            weather_description="Nuageux"
        )
        assert weather.temperature_max == 25.0
        assert weather.precipitation_sum == 5.0


class TestWeatherAlert:
    def test_weather_alert_creation(self):
        loc = Location(
            site_id="SITE001",
            name="Site Paris",
            city="Paris",
            country="France",
            latitude=48.8566,
            longitude=2.3522,
            site_type="warehouse",
            criticality="high"
        )
        alert = WeatherAlert(
            location=loc,
            alert_type="heat_wave",
            severity="high",
            date=date.today(),
            value=42.0,
            threshold=35.0,
            unit="C",
            description="Canicule detectee",
            supply_chain_risk="Risque de rupture"
        )
        assert alert.alert_type == "heat_wave"
        assert alert.severity == "high"
        assert alert.value > alert.threshold


class TestWeatherForecast:
    def test_weather_forecast_creation(self):
        loc = Location(
            site_id="SITE001",
            name="Site Paris",
            city="Paris",
            country="France",
            latitude=48.8566,
            longitude=2.3522,
            site_type="warehouse",
            criticality="high"
        )
        forecast = WeatherForecast(
            location=loc,
            forecast_days=[
                DailyWeather(
                    date=date.today(),
                    temperature_max=20.0,
                    temperature_min=10.0,
                    precipitation_sum=0.0,
                    rain_sum=0.0,
                    snowfall_sum=0.0,
                    wind_speed_max=15.0,
                    wind_gusts_max=25.0,
                    weather_code=0,
                    weather_description="Ensoleille"
                )
            ],
            fetched_at=datetime.now(),
            timezone="Europe/Paris"
        )
        assert forecast.location.city == "Paris"
        assert len(forecast.forecast_days) == 1


class TestOpenMeteoClient:
    def test_client_initialization(self):
        client = OpenMeteoClient()
        assert client is not None


class TestFormatAlertSummary:
    def test_format_empty_alerts(self):
        result = format_alert_summary([])
        assert isinstance(result, str)

    def test_format_single_alert(self):
        loc = Location(
            site_id="SITE001",
            name="Site Paris",
            city="Paris",
            country="France",
            latitude=48.8566,
            longitude=2.3522,
            site_type="warehouse",
            criticality="high"
        )
        alerts = [
            WeatherAlert(
                location=loc,
                alert_type="heat_wave",
                severity="high",
                date=date.today(),
                value=40.0,
                threshold=35.0,
                unit="C",
                description="Canicule",
                supply_chain_risk="Risque logistique"
            )
        ]
        result = format_alert_summary(alerts)
        assert isinstance(result, str)
        assert len(result) > 0


class TestAlertThresholds:
    def test_temperature_thresholds(self):
        heat_threshold = 35.0
        cold_threshold = -10.0
        assert heat_threshold > cold_threshold

    def test_wind_thresholds(self):
        strong_wind = 60.0
        storm_wind = 100.0
        assert storm_wind > strong_wind


class TestSeverityLevels:
    def test_severity_ordering(self):
        severities = ["low", "medium", "high", "critical"]
        assert severities.index("low") < severities.index("medium")
        assert severities.index("high") < severities.index("critical")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
