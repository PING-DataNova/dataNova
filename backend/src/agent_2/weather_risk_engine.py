"""
Weather Risk Engine pour Agent 2

Ce module récupère les alertes météo de la table weather_alerts
et calcule un score de risque climatique pour chaque site/fournisseur.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
import structlog

logger = structlog.get_logger(__name__)


# Coefficients de sévérité par type d'alerte météo
WEATHER_SEVERITY_WEIGHTS = {
    "extreme_cold": {
        "critical": 1.0,
        "high": 0.8,
        "medium": 0.5,
        "low": 0.2
    },
    "extreme_heat": {
        "critical": 1.0,
        "high": 0.8,
        "medium": 0.5,
        "low": 0.2
    },
    "heavy_rain": {
        "critical": 1.0,
        "high": 0.8,
        "medium": 0.5,
        "low": 0.2
    },
    "snow": {
        "critical": 1.0,
        "high": 0.8,
        "medium": 0.5,
        "low": 0.2
    },
    "strong_wind": {
        "critical": 1.0,
        "high": 0.8,
        "medium": 0.5,
        "low": 0.2
    },
    "storm": {
        "critical": 1.0,
        "high": 0.9,
        "medium": 0.6,
        "low": 0.3
    }
}

# Impact supply chain par type d'alerte
SUPPLY_CHAIN_IMPACT = {
    "snow": {
        "transport_disruption": 0.9,
        "production_impact": 0.6,
        "description": "Risque de routes bloquées, retards livraisons"
    },
    "heavy_rain": {
        "transport_disruption": 0.8,
        "production_impact": 0.5,
        "description": "Risque d'inondations, routes coupées"
    },
    "extreme_cold": {
        "transport_disruption": 0.6,
        "production_impact": 0.7,
        "description": "Gel des équipements, conditions de travail difficiles"
    },
    "extreme_heat": {
        "transport_disruption": 0.3,
        "production_impact": 0.8,
        "description": "Canicule, réduction capacité de travail"
    },
    "strong_wind": {
        "transport_disruption": 0.85,
        "production_impact": 0.4,
        "description": "Fermeture ports et ponts, transport perturbé"
    },
    "storm": {
        "transport_disruption": 0.95,
        "production_impact": 0.8,
        "description": "Tempête majeure, arrêt potentiel des opérations"
    }
}


class WeatherRiskEngine:
    """
    Moteur de risque météorologique pour l'Agent 2.
    
    Récupère les alertes météo depuis la BDD et calcule un score
    de risque climatique pour chaque entité (site/fournisseur).
    """
    
    def __init__(self, session=None):
        """
        Initialise le moteur de risque météo.
        
        Args:
            session: Session SQLAlchemy (optionnel, sera créée si non fournie)
        """
        self._session = session
        self._weather_cache: Dict[str, List[Dict]] = {}  # Cache par site_id
    
    def _get_session(self):
        """Obtient une session BDD"""
        if self._session:
            return self._session
        
        from src.storage.database import get_session
        return get_session()
    
    def load_weather_alerts(
        self,
        site_ids: List[str] = None,
        days_ahead: int = 16
    ) -> Dict[str, List[Dict]]:
        """
        Charge les alertes météo depuis la BDD pour les sites spécifiés.
        
        Args:
            site_ids: Liste des IDs de sites (None = tous)
            days_ahead: Nombre de jours à regarder (défaut: 16)
            
        Returns:
            Dict {site_id: [alerts]}
        """
        from src.storage.models import WeatherAlert
        
        session = self._get_session()
        
        try:
            today = date.today()
            end_date = today + timedelta(days=days_ahead)
            
            query = session.query(WeatherAlert).filter(
                WeatherAlert.alert_date >= today,
                WeatherAlert.alert_date <= end_date,
                WeatherAlert.status.in_(["new", "acknowledged"])
            )
            
            if site_ids:
                query = query.filter(WeatherAlert.site_id.in_(site_ids))
            
            alerts = query.order_by(
                WeatherAlert.site_id,
                WeatherAlert.alert_date,
                WeatherAlert.severity.desc()
            ).all()
            
            # Grouper par site_id
            alerts_by_site: Dict[str, List[Dict]] = {}
            
            for alert in alerts:
                site_id = alert.site_id
                if site_id not in alerts_by_site:
                    alerts_by_site[site_id] = []
                
                alerts_by_site[site_id].append({
                    "id": alert.id,
                    "site_id": alert.site_id,
                    "site_name": alert.site_name,
                    "city": alert.city,
                    "country": alert.country,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "alert_date": alert.alert_date,
                    "value": alert.value,
                    "threshold": alert.threshold,
                    "unit": alert.unit,
                    "description": alert.description,
                    "supply_chain_risk": alert.supply_chain_risk
                })
            
            self._weather_cache = alerts_by_site
            
            logger.info(
                "weather_alerts_loaded",
                sites_with_alerts=len(alerts_by_site),
                total_alerts=sum(len(a) for a in alerts_by_site.values())
            )
            
            return alerts_by_site
            
        finally:
            if not self._session:
                session.close()
    
    def get_site_weather_risk(
        self,
        site_id: str,
        site_code: str = None
    ) -> Dict:
        """
        Calcule le score de risque météo pour un site donné.
        
        Args:
            site_id: UUID du site
            site_code: Code du site (ex: FR-LEH-MFG1)
            
        Returns:
            {
                "has_weather_risk": True/False,
                "weather_risk_score": 0-100,
                "alerts_count": 3,
                "alerts_by_type": {"snow": 1, "heavy_rain": 2},
                "max_severity": "high",
                "transport_disruption_risk": 0.8,
                "production_impact_risk": 0.6,
                "weather_summary": "...",
                "alerts": [...]
            }
        """
        # Chercher les alertes pour ce site
        alerts = []
        
        # D'abord par site_id UUID
        if site_id in self._weather_cache:
            alerts = self._weather_cache[site_id]
        # Ensuite par site_code
        elif site_code and site_code in self._weather_cache:
            alerts = self._weather_cache[site_code]
        
        if not alerts:
            return {
                "has_weather_risk": False,
                "weather_risk_score": 0.0,
                "alerts_count": 0,
                "alerts_by_type": {},
                "max_severity": None,
                "transport_disruption_risk": 0.0,
                "production_impact_risk": 0.0,
                "weather_summary": "Aucune alerte météo active",
                "alerts": []
            }
        
        # Calculer les scores
        alerts_by_type = {}
        max_severity_weight = 0.0
        max_severity = "low"
        total_transport_risk = 0.0
        total_production_risk = 0.0
        
        for alert in alerts:
            alert_type = alert["alert_type"]
            severity = alert["severity"]
            
            # Compter par type
            if alert_type not in alerts_by_type:
                alerts_by_type[alert_type] = 0
            alerts_by_type[alert_type] += 1
            
            # Poids de sévérité
            severity_weight = WEATHER_SEVERITY_WEIGHTS.get(
                alert_type, {}
            ).get(severity, 0.3)
            
            if severity_weight > max_severity_weight:
                max_severity_weight = severity_weight
                max_severity = severity
            
            # Impact supply chain
            impact = SUPPLY_CHAIN_IMPACT.get(alert_type, {})
            transport_risk = impact.get("transport_disruption", 0.5) * severity_weight
            production_risk = impact.get("production_impact", 0.5) * severity_weight
            
            total_transport_risk = max(total_transport_risk, transport_risk)
            total_production_risk = max(total_production_risk, production_risk)
        
        # Score de risque météo (0-100)
        # Formule: (nombre d'alertes * poids) + (sévérité max * 50)
        base_score = min(len(alerts) * 10, 30)  # Max 30 points pour le nombre
        severity_score = max_severity_weight * 50  # Max 50 points pour la sévérité
        impact_score = (total_transport_risk + total_production_risk) * 10  # Max 20 points
        
        weather_risk_score = min(100.0, base_score + severity_score + impact_score)
        
        # Générer un résumé
        weather_summary = self._generate_weather_summary(alerts, alerts_by_type, max_severity)
        
        return {
            "has_weather_risk": True,
            "weather_risk_score": round(weather_risk_score, 2),
            "alerts_count": len(alerts),
            "alerts_by_type": alerts_by_type,
            "max_severity": max_severity,
            "transport_disruption_risk": round(total_transport_risk, 2),
            "production_impact_risk": round(total_production_risk, 2),
            "weather_summary": weather_summary,
            "alerts": alerts[:5]  # Limiter à 5 alertes les plus récentes
        }
    
    def _generate_weather_summary(
        self,
        alerts: List[Dict],
        alerts_by_type: Dict[str, int],
        max_severity: str
    ) -> str:
        """Génère un résumé textuel des alertes météo."""
        if not alerts:
            return "Aucune alerte météo active"
        
        # Traduire les types
        type_names = {
            "snow": "neige",
            "heavy_rain": "fortes pluies",
            "extreme_cold": "grand froid",
            "extreme_heat": "canicule",
            "strong_wind": "vents forts",
            "storm": "tempête"
        }
        
        severity_names = {
            "critical": "critique",
            "high": "élevé",
            "medium": "modéré",
            "low": "faible"
        }
        
        # Lister les types d'alertes
        alert_types_str = ", ".join([
            f"{count} alerte(s) {type_names.get(t, t)}"
            for t, count in alerts_by_type.items()
        ])
        
        severity_str = severity_names.get(max_severity, max_severity)
        
        # Dates concernées
        dates = sorted(set(a["alert_date"] for a in alerts))
        if len(dates) == 1:
            date_str = f"le {dates[0].strftime('%d/%m/%Y')}"
        else:
            date_str = f"du {dates[0].strftime('%d/%m')} au {dates[-1].strftime('%d/%m/%Y')}"
        
        return f"⚠️ {len(alerts)} alerte(s) météo (niveau {severity_str}) {date_str}: {alert_types_str}"
    
    def calculate_weather_impact_on_risk(
        self,
        base_risk_score: float,
        site_weather_risk: Dict
    ) -> Tuple[float, str]:
        """
        Ajuste le score de risque en fonction du risque météo.
        
        Args:
            base_risk_score: Score de risque de base (0-100)
            site_weather_risk: Résultat de get_site_weather_risk()
            
        Returns:
            (adjusted_score, adjustment_reason)
        """
        if not site_weather_risk["has_weather_risk"]:
            return base_risk_score, "Pas d'ajustement météo"
        
        weather_score = site_weather_risk["weather_risk_score"]
        max_severity = site_weather_risk["max_severity"]
        
        # Coefficient d'ajustement selon la sévérité
        adjustment_coefficients = {
            "critical": 0.25,  # +25% max
            "high": 0.15,      # +15% max
            "medium": 0.08,    # +8% max
            "low": 0.03        # +3% max
        }
        
        coef = adjustment_coefficients.get(max_severity, 0.05)
        
        # Ajustement proportionnel au score météo
        adjustment = (weather_score / 100) * coef * 100
        adjusted_score = min(100.0, base_risk_score + adjustment)
        
        reason = (
            f"Score ajusté de +{adjustment:.1f} points "
            f"(risque météo: {weather_score:.0f}/100, sévérité: {max_severity})"
        )
        
        return round(adjusted_score, 2), reason
    
    def get_all_weather_risks(
        self,
        sites: List[Dict],
        suppliers: List[Dict]
    ) -> Dict[str, Dict]:
        """
        Calcule le risque météo pour toutes les entités.
        
        Args:
            sites: Liste des sites
            suppliers: Liste des fournisseurs
            
        Returns:
            Dict {entity_id: weather_risk_data}
        """
        # Collecter tous les site_ids et codes
        site_ids = []
        site_codes = []
        
        for site in sites:
            site_ids.append(site.get("id"))
            if site.get("site_id"):
                site_codes.append(site["site_id"])
        
        for supplier in suppliers:
            site_ids.append(supplier.get("id"))
            if supplier.get("supplier_id"):
                site_codes.append(supplier["supplier_id"])
        
        # Charger les alertes
        self.load_weather_alerts(site_ids=site_ids + site_codes)
        
        # Calculer pour chaque entité
        results = {}
        
        for site in sites:
            site_id = site.get("id")
            site_code = site.get("site_id")
            results[site_id] = self.get_site_weather_risk(site_id, site_code)
        
        for supplier in suppliers:
            supplier_id = supplier.get("id")
            supplier_code = supplier.get("supplier_id")
            results[supplier_id] = self.get_site_weather_risk(supplier_id, supplier_code)
        
        return results
