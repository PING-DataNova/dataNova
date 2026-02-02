"""
from dotenv import load_dotenv
load_dotenv()  # Charge automatiquement le fichier .env
"""
"""
Agent 2 - Risk Analyzer (EXTENDED)

Agent principal qui orchestre l'analyse d'impact complète :
1. Projection sur CHAQUE entité (sites + fournisseurs) - NOUVEAU
2. Calcul 360° Risk Score pour chaque entité - NOUVEAU
3. Calcul Business Interruption Score - NOUVEAU
4. Analyse de criticité globale
5. Génération de recommandations avec LLM
"""

import json
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
from dataclasses import asdict

# Import des moteurs de projection (existants)
from .geographic_engine import GeographicEngine
from .regulatory_geopolitical_engine import RegulatoryEngine, GeopoliticalEngine
from .criticality_analyzer import CriticalityAnalyzer
from .llm_reasoning import LLMReasoning
from .weather_risk_engine import WeatherRiskEngine


class Agent2:
    """
    Agent 2 - Risk Analyzer (Extended)
    
    Analyse l'impact d'un événement sur CHAQUE site et fournisseur individuellement,
    calcule des scores de risque sophistiqués (360°, Business Interruption),
    et génère des recommandations.
    """
    
    def __init__(self, llm_model: str = "claude-sonnet-4-5-20250929"):
        """
        Initialise Agent 2 Extended
        
        Args:
            llm_model: Modèle LLM à utiliser pour le raisonnement
        """
        self.geographic_engine = GeographicEngine()
        self.regulatory_engine = RegulatoryEngine()
        self.geopolitical_engine = GeopoliticalEngine()
        self.criticality_analyzer = CriticalityAnalyzer()
        self.llm_reasoning = LLMReasoning(model=llm_model)
        self.weather_risk_engine = WeatherRiskEngine()
    
    def analyze(
        self,
        document: Dict,
        pertinence_result: Dict,
        sites: List[Dict],
        suppliers: List[Dict],
        supplier_relationships: List[Dict]
    ) -> Tuple[Dict, List[Dict]]:
        """
        Analyse complète de l'impact d'un événement.
        
        NOUVEAU : Retourne 2 objets :
        1. risk_analysis : Analyse globale (pour table RISK_ANALYSES)
        2. risk_projections : Liste de projections par entité (pour table RISK_PROJECTIONS)
        
        Args:
            document: Document analysé par Agent 1A
            pertinence_result: Résultat de l'analyse de pertinence (Agent 1B)
            sites: Liste des sites Hutchinson
            suppliers: Liste des fournisseurs
            supplier_relationships: Relations site-fournisseur
            
        Returns:
            Tuple (risk_analysis, risk_projections)
        """
        event_type = document.get('event_type')
        event_id = document.get('id')
        
        # ========================================
        # NOUVEAU : Projection sur CHAQUE entité
        # ========================================
        risk_projections = self._project_on_all_entities(
            document,
            sites,
            suppliers,
            supplier_relationships
        )
        
        # Filtrer les entités concernées
        concerned_projections = [p for p in risk_projections if p['is_concerned']]
        
        # Extraire les sites et fournisseurs affectés
        affected_sites = [
            {
                "id": p['entity_id'],
                "name": p['entity_name'],
                "risk_score": p['risk_score'],
                "business_interruption_score": p['business_interruption_score'],
                "reasoning": p['reasoning']
            }
            for p in concerned_projections if p['entity_type'] == 'site'
        ]
        
        affected_suppliers = [
            {
                "id": p['entity_id'],
                "name": p['entity_name'],
                "risk_score": p['risk_score'],
                "business_interruption_score": p['business_interruption_score'],
                "reasoning": p['reasoning']
            }
            for p in concerned_projections if p['entity_type'] == 'supplier'
        ]
        
        # ========================================
        # Analyse de criticité globale (existante)
        # ========================================
        criticality_results = self._analyze_criticality_from_projections(
            concerned_projections,
            sites,
            suppliers,
            supplier_relationships
        )
        
        # ========================================
        # Calcul du niveau de risque global
        # ========================================
        overall_risk_level, overall_risk_score_360 = self._calculate_overall_risk(
            risk_projections
        )
        
        # ========================================
        # NOUVEAU: Agrégation des risques météo
        # ========================================
        weather_risk_summary = self._aggregate_weather_risks(risk_projections)
        
        # ========================================
        # Génération de recommandations (LLM)
        # ========================================
        recommendations = self._generate_recommendations(
            document,
            affected_sites,
            affected_suppliers,
            criticality_results,
            weather_risk_summary  # NOUVEAU: inclure météo
        )
        
        # ========================================
        # Construire le résultat final
        # ========================================
        risk_analysis = {
            "document_id": event_id,
            "event_type": event_type,
            "event_subtype": document.get('event_subtype'),
            "analysis_timestamp": datetime.utcnow().isoformat(),
            
            # Résultats de projection
            "affected_sites": affected_sites,
            "affected_suppliers": affected_suppliers,
            "affected_sites_count": len(affected_sites),
            "affected_suppliers_count": len(affected_suppliers),
            
            # Analyse de criticité
            "criticality_analysis": criticality_results,
            "overall_risk_level": overall_risk_level,
            
            # NOUVEAU : Scores 360°
            "risk_score": overall_risk_score_360,  # Score simple (existant)
            "risk_score_360": overall_risk_score_360,  # Score composite (nouveau)
            "severity_score": self._calculate_severity_score(document),
            "probability_score": self._calculate_global_probability(concerned_projections),
            "exposure_score": self._calculate_global_exposure(concerned_projections),
            "urgency_score": self._calculate_urgency_score(document),
            
            # NOUVEAU : Business Interruption
            "business_interruption_score": self._calculate_global_business_interruption(concerned_projections),
            "estimated_disruption_days": self._estimate_disruption_days(document, event_type),
            "revenue_impact_percentage": self._estimate_revenue_impact(concerned_projections, supplier_relationships),
            
            # NOUVEAU : Risques météo agrégés
            "weather_risk_summary": weather_risk_summary,
            
            # Recommandations
            "recommendations": recommendations,
            
            # Métadonnées
            "analysis_metadata": {
                "sites_analyzed": len(sites),
                "suppliers_analyzed": len(suppliers),
                "entities_concerned": len(concerned_projections),
                "entities_with_weather_alerts": weather_risk_summary.get("entities_with_alerts", 0),
                "projection_method": "entity_level",  # Nouveau : projection par entité
                "llm_reasoning_used": self.llm_reasoning.llm_available,
                "weather_data_integrated": True  # NOUVEAU
            }
        }
        
        return risk_analysis, risk_projections
    
    # ========================================
    # NOUVEAU : Projection sur chaque entité
    # ========================================
    
    def _project_on_all_entities(
        self,
        document: Dict,
        sites: List[Dict],
        suppliers: List[Dict],
        supplier_relationships: List[Dict]
    ) -> List[Dict]:
        """
        Boucle sur CHAQUE site et fournisseur pour calculer :
        - is_concerned (boolean)
        - risk_score (0-100)
        - business_interruption_score (0-100)
        - Sous-scores (severity, probability, exposure, urgency)
        - weather_risk (NOUVEAU: risque météo depuis Open-Meteo)
        
        Returns:
            Liste de projections (une par entité)
        """
        event_type = document.get('event_type')
        event_id = document.get('id')
        projections = []
        
        # NOUVEAU: Charger les risques météo pour toutes les entités
        weather_risks = self.weather_risk_engine.get_all_weather_risks(sites, suppliers)
        
        # Boucler sur les sites
        for site in sites:
            projection = self._project_on_entity(
                document,
                site,
                'site',
                supplier_relationships,
                weather_risks.get(site.get('id'), {})
            )
            projections.append(projection)
        
        # Boucler sur les fournisseurs
        for supplier in suppliers:
            projection = self._project_on_entity(
                document,
                supplier,
                'supplier',
                supplier_relationships,
                weather_risks.get(supplier.get('id'), {})
            )
            projections.append(projection)
        
        return projections
    
    def _project_on_entity(
        self,
        document: Dict,
        entity: Dict,
        entity_type: str,  # 'site' ou 'supplier'
        supplier_relationships: List[Dict],
        weather_risk: Dict = None  # NOUVEAU: données météo Open-Meteo
    ) -> Dict:
        """
        Calcule la projection pour UNE entité (site ou fournisseur)
        
        Returns:
            {
                "id": "uuid",
                "event_id": "doc_id",
                "entity_id": "site_id",
                "entity_type": "site",
                "entity_name": "Hutchinson Le Havre",
                "is_concerned": True,
                "risk_score": 85.0,
                "impact_score": 70.0,
                "business_interruption_score": 60.0,
                "severity_score": 90.0,
                "probability_score": 80.0,
                "exposure_score": 75.0,
                "urgency_score": 95.0,
                "weather_risk_score": 45.0,  # NOUVEAU
                "weather_risk": {...},  # NOUVEAU
                "reasoning": "...",
                "estimated_disruption_days": 14,
                "revenue_impact_percentage": 3.5
            }
        """
        event_type = document.get('event_type')
        event_id = document.get('id')
        entity_id = entity.get('id')
        entity_name = entity.get('name')
        weather_risk = weather_risk or {}
        
        # Déterminer si l'entité est concernée
        is_concerned = self._is_entity_concerned(document, entity, entity_type)
        
        if not is_concerned:
            # Entité non concernée : scores à 0 (mais on garde les données météo)
            return {
                "id": str(uuid.uuid4()),
                "event_id": event_id,
                "entity_id": entity_id,
                "entity_type": entity_type,
                "entity_name": entity_name,
                "is_concerned": False,
                "risk_score": 0.0,
                "impact_score": 0.0,
                "business_interruption_score": 0.0,
                "severity_score": 0.0,
                "probability_score": 0.0,
                "exposure_score": 0.0,
                "urgency_score": 0.0,
                "weather_risk_score": weather_risk.get("weather_risk_score", 0.0),
                "weather_risk": weather_risk,
                "reasoning": "Entité non concernée par l'événement",
                "estimated_disruption_days": 0,
                "revenue_impact_percentage": 0.0
            }
        
        # Entité concernée : calculer les scores
        severity = self._calculate_severity_score(document)
        probability = self._calculate_entity_probability(document, entity, entity_type)
        exposure = self._calculate_entity_exposure(entity, entity_type, supplier_relationships)
        urgency = self._calculate_urgency_score(document)
        
        # 360° Risk Score (formule composite) - AVANT ajustement météo
        base_risk_score_360 = (
            0.30 * severity +
            0.25 * probability +
            0.25 * exposure +
            0.20 * urgency
        )
        
        # NOUVEAU: Ajuster le score avec le risque météo
        weather_risk_score = weather_risk.get("weather_risk_score", 0.0)
        weather_adjustment_reason = ""
        
        if weather_risk.get("has_weather_risk", False):
            # Ajustement: le risque météo peut augmenter le score jusqu'à +15%
            risk_score_360, weather_adjustment_reason = self.weather_risk_engine.calculate_weather_impact_on_risk(
                base_risk_score_360,
                weather_risk
            )
        else:
            risk_score_360 = base_risk_score_360
        
        # Business Interruption Score (intègre aussi le risque météo)
        disruption_days = self._estimate_entity_disruption_days(document, entity, entity_type)
        
        # NOUVEAU: Ajouter des jours de disruption si risque météo
        if weather_risk.get("has_weather_risk", False):
            weather_disruption = self._estimate_weather_disruption_days(weather_risk)
            disruption_days += weather_disruption
        
        revenue_impact = self._estimate_entity_revenue_impact(entity, entity_type, supplier_relationships)
        business_interruption = exposure * (disruption_days / 30) * revenue_impact  # Normalisé sur 100
        business_interruption = min(100.0, business_interruption)  # Cap à 100
        
        # Raisonnement (optionnel : utiliser LLM)
        reasoning = self._generate_entity_reasoning(document, entity, entity_type, risk_score_360)
        
        # Ajouter le contexte météo au raisonnement si pertinent
        if weather_risk.get("has_weather_risk", False):
            reasoning += f"\n\n⚠️ RISQUE MÉTÉO: {weather_risk.get('weather_summary', '')}"
        
        # Construire reasoning_details (transparence complète)
        reasoning_details = {
            "why_concerned": self._explain_why_concerned(document, entity, entity_type),
            "risks_identified": self._identify_risks(document, entity, entity_type),
            "impacts_calculated": self._explain_impacts(document, entity, entity_type, disruption_days, revenue_impact),
            "score_calculation": {
                "severity": {
                    "value": round(severity, 2),
                    "explanation": self._explain_severity(document)
                },
                "probability": {
                    "value": round(probability, 2),
                    "explanation": self._explain_probability(document, entity, entity_type)
                },
                "exposure": {
                    "value": round(exposure, 2),
                    "explanation": self._explain_exposure(entity, entity_type, supplier_relationships)
                },
                "urgency": {
                    "value": round(urgency, 2),
                    "explanation": self._explain_urgency(document)
                },
                "weather_risk": {
                    "value": round(weather_risk_score, 2),
                    "has_alerts": weather_risk.get("has_weather_risk", False),
                    "alerts_count": weather_risk.get("alerts_count", 0),
                    "max_severity": weather_risk.get("max_severity"),
                    "summary": weather_risk.get("weather_summary", ""),
                    "adjustment": weather_adjustment_reason
                },
                "formula": "Risk Score 360° = (0.30×Severity + 0.25×Probability + 0.25×Exposure + 0.20×Urgency) + Weather Adjustment",
                "calculation": f"Base: ({0.30}×{severity:.1f} + {0.25}×{probability:.1f} + {0.25}×{exposure:.1f} + {0.20}×{urgency:.1f}) = {base_risk_score_360:.1f}, Ajusté: {risk_score_360:.1f}"
            }
        }
        
        return {
            "id": str(uuid.uuid4()),
            "event_id": event_id,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "entity_name": entity_name,
            "is_concerned": True,
            "risk_score": round(risk_score_360, 2),
            "impact_score": round((severity + exposure) / 2, 2),  # Impact = moyenne severity + exposure
            "business_interruption_score": round(business_interruption, 2),
            "severity_score": round(severity, 2),
            "probability_score": round(probability, 2),
            "exposure_score": round(exposure, 2),
            "urgency_score": round(urgency, 2),
            "weather_risk_score": round(weather_risk_score, 2),
            "weather_risk": weather_risk,
            "reasoning": reasoning,
            "reasoning_details": reasoning_details,
            "estimated_disruption_days": disruption_days,
            "revenue_impact_percentage": round(revenue_impact, 2)
        }
    
    def _estimate_weather_disruption_days(self, weather_risk: Dict) -> int:
        """
        Estime le nombre de jours de disruption dus aux conditions météo.
        
        Args:
            weather_risk: Données de risque météo
            
        Returns:
            Nombre de jours estimés
        """
        if not weather_risk.get("has_weather_risk", False):
            return 0
        
        max_severity = weather_risk.get("max_severity", "low")
        alerts_count = weather_risk.get("alerts_count", 0)
        
        # Jours de base selon la sévérité
        severity_days = {
            "critical": 5,
            "high": 3,
            "medium": 1,
            "low": 0
        }
        
        base_days = severity_days.get(max_severity, 0)
        
        # Ajouter selon le nombre d'alertes (max +3 jours)
        additional_days = min(3, alerts_count // 2)
        
        return base_days + additional_days
    
    # ========================================
    # Déterminer si une entité est concernée
    # ========================================
    
    def _is_entity_concerned(
        self,
        document: Dict,
        entity: Dict,
        entity_type: str
    ) -> bool:
        """
        Détermine si une entité (site ou fournisseur) est concernée par l'événement
        
        Returns:
            True si concerné, False sinon
        """
        event_type = document.get('event_type')
        
        if event_type == "climatique":
            return self._is_concerned_climatic(document, entity)
        elif event_type == "reglementaire":
            return self._is_concerned_regulatory(document, entity)
        elif event_type == "geopolitique":
            return self._is_concerned_geopolitical(document, entity)
        else:
            return False
    
    def _is_concerned_climatic(self, document: Dict, entity: Dict) -> bool:
        """Vérifie si l'entité est concernée par un événement climatique (distance géographique)"""
        geographic_scope = document.get('geographic_scope') or {}
        coordinates = geographic_scope.get('coordinates', {})
        
        if not coordinates or 'latitude' not in coordinates:
            return False
        
        event_lat = coordinates['latitude']
        event_lon = coordinates['longitude']
        entity_lat = entity.get('latitude')
        entity_lon = entity.get('longitude')
        
        if not entity_lat or not entity_lon:
            return False
        
        # Calculer la distance (haversine)
        distance_km = self._haversine_distance(event_lat, event_lon, entity_lat, entity_lon)
        
        # Seuil : 200 km
        return distance_km <= 200
    
    def _is_concerned_regulatory(self, document: Dict, entity: Dict) -> bool:
        """Vérifie si l'entité est concernée par un événement réglementaire (pays, secteur, produits)"""
        geographic_scope = document.get('geographic_scope') or {}
        
        # Critères réglementaires
        affected_countries = geographic_scope.get('affected_countries', []) or []
        affected_sectors = geographic_scope.get('affected_sectors', []) or []
        affected_products = geographic_scope.get('affected_products', []) or []
        
        entity_country = entity.get('country')
        entity_sectors = entity.get('sectors', [])
        entity_products = entity.get('products', []) or entity.get('products_supplied', [])
        
        # Vérifier pays
        if affected_countries and entity_country not in affected_countries:
            return False
        
        # Vérifier secteur (si spécifié)
        if affected_sectors:
            if not any(sector in affected_sectors for sector in entity_sectors):
                return False
        
        # Vérifier produits (si spécifié)
        if affected_products:
            if not any(product in affected_products for product in entity_products):
                return False
        
        return True
    
    def _is_concerned_geopolitical(self, document: Dict, entity: Dict) -> bool:
        """Vérifie si l'entité est concernée par un événement géopolitique (pays affectés)"""
        geographic_scope = document.get('geographic_scope') or {}
        
        directly_affected = geographic_scope.get('directly_affected_countries', [])
        indirectly_affected = geographic_scope.get('indirectly_affected_countries', [])
        
        entity_country = entity.get('country')
        
        # Concerné si dans les pays directement ou indirectement affectés
        return entity_country in directly_affected or entity_country in indirectly_affected
    
    # ========================================
    # Calcul des sous-scores (360° Risk Score)
    # ========================================
    
    def _calculate_severity_score(self, document: Dict) -> float:
        """
        Calcule le score de gravité de l'événement (0-100)
        
        Basé sur :
        - Type d'événement
        - Sous-type
        - Intensité (si disponible)
        """
        event_type = document.get('event_type')
        event_subtype = document.get('event_subtype', '')
        
        # Scores de base par type
        base_scores = {
            "climatique": 70,
            "reglementaire": 50,
            "geopolitique": 80
        }
        
        severity = base_scores.get(event_type, 50)
        
        # Ajuster selon le sous-type
        high_severity_keywords = ["guerre", "conflit", "ouragan", "inondation", "tremblement", "tsunami", "catastrophe"]
        if any(keyword in event_subtype.lower() for keyword in high_severity_keywords):
            severity = min(100, severity + 20)
        
        return float(severity)
    
    def _calculate_entity_probability(
        self,
        document: Dict,
        entity: Dict,
        entity_type: str
    ) -> float:
        """
        Calcule la probabilité que l'événement impacte l'entité (0-100)
        
        Basé sur :
        - Distance géographique (pour climatique)
        - Correspondance secteur/produit (pour réglementaire)
        - Proximité pays (pour géopolitique)
        """
        event_type = document.get('event_type')
        
        if event_type == "climatique":
            # Plus l'entité est proche, plus la probabilité est élevée
            geographic_scope = document.get('geographic_scope') or {}
            coordinates = geographic_scope.get('coordinates', {})
            
            if not coordinates or 'latitude' not in coordinates:
                return 50.0
            
            event_lat = coordinates['latitude']
            event_lon = coordinates['longitude']
            entity_lat = entity.get('latitude')
            entity_lon = entity.get('longitude')
            
            if not entity_lat or not entity_lon:
                return 50.0
            
            distance_km = self._haversine_distance(event_lat, event_lon, entity_lat, entity_lon)
            
            # Probabilité décroissante avec la distance
            if distance_km <= 50:
                return 100.0
            elif distance_km <= 100:
                return 80.0
            elif distance_km <= 150:
                return 60.0
            elif distance_km <= 200:
                return 40.0
            else:
                return 20.0
        
        elif event_type == "reglementaire":
            # Probabilité basée sur la correspondance secteur/produit
            geographic_scope = document.get('geographic_scope') or {}
            affected_sectors = geographic_scope.get('affected_sectors', []) or []
            affected_products = geographic_scope.get('affected_products', []) or []
            
            entity_sectors = entity.get('sectors', [])
            entity_products = entity.get('products', []) or entity.get('products_supplied', [])
            
            match_score = 0
            
            # Correspondance secteur
            if affected_sectors and any(sector in affected_sectors for sector in entity_sectors):
                match_score += 50
            
            # Correspondance produit
            if affected_products and any(product in affected_products for product in entity_products):
                match_score += 50
            
            return float(match_score) if match_score > 0 else 30.0
        
        elif event_type == "geopolitique":
            # Probabilité basée sur le niveau d'affectation du pays
            geographic_scope = document.get('geographic_scope') or {}
            directly_affected = geographic_scope.get('directly_affected_countries', []) or []
            indirectly_affected = geographic_scope.get('indirectly_affected_countries', []) or []
            
            entity_country = entity.get('country')
            
            if entity_country in directly_affected:
                return 90.0
            elif entity_country in indirectly_affected:
                return 50.0
            else:
                return 10.0
        
        return 50.0
    
    def _calculate_entity_exposure(
        self,
        entity: Dict,
        entity_type: str,
        supplier_relationships: List[Dict]
    ) -> float:
        """
        Calcule l'exposition de l'entité (0-100)
        
        Basé sur :
        - Criticité (fournisseur unique = 100)
        - Taille du site/fournisseur
        - Volume d'affaires
        """
        exposure = 50.0  # Base
        
        if entity_type == "supplier":
            # Vérifier si c'est un fournisseur unique
            entity_id = entity.get('id')
            relationships = [r for r in supplier_relationships if r.get('supplier_id') == entity_id]
            
            for rel in relationships:
                if rel.get('is_sole_supplier'):
                    exposure = 100.0
                    break
                elif rel.get('criticality') == 'HIGH':
                    exposure = max(exposure, 80.0)
                elif rel.get('criticality') == 'MEDIUM':
                    exposure = max(exposure, 60.0)
        
        elif entity_type == "site":
            # Exposition basée sur l'importance stratégique
            strategic_importance = entity.get('strategic_importance', 'MEDIUM')
            
            if strategic_importance == 'HIGH':
                exposure = 80.0
            elif strategic_importance == 'MEDIUM':
                exposure = 60.0
            else:
                exposure = 40.0
        
        return float(exposure)
    
    def _calculate_urgency_score(self, document: Dict) -> float:
        """
        Calcule l'urgence de réaction (0-100)
        
        Basé sur :
        - Date d'application (réglementaire)
        - Vitesse de l'événement (climatique)
        - Niveau de tension (géopolitique)
        """
        event_type = document.get('event_type')
        
        if event_type == "climatique":
            # Événements climatiques : urgence élevée (en cours)
            return 90.0
        
        elif event_type == "reglementaire":
            # Urgence basée sur la date d'application
            # TODO : Extraire la date d'application du document
            # Pour l'instant : urgence moyenne
            return 60.0
        
        elif event_type == "geopolitique":
            # Urgence basée sur le niveau de tension
            event_subtype = document.get('event_subtype', '')
            
            high_urgency_keywords = ["guerre", "conflit", "coup d'état", "crise"]
            if any(keyword in event_subtype.lower() for keyword in high_urgency_keywords):
                return 95.0
            else:
                return 70.0
        
        return 50.0
    
    # ========================================
    # Calcul Business Interruption Score
    # ========================================
    
    def _estimate_entity_disruption_days(
        self,
        document: Dict,
        entity: Dict,
        entity_type: str
    ) -> int:
        """
        Estime la durée de l'interruption (en jours)
        
        Basé sur :
        - Type d'événement
        - Gravité
        """
        event_type = document.get('event_type')
        
        if event_type == "climatique":
            # Inondation, tempête : 7-14 jours
            return 10
        elif event_type == "reglementaire":
            # Réglementation : 0 jours (mais coût de conformité)
            return 0
        elif event_type == "geopolitique":
            # Conflit : 30-90 jours
            return 60
        
        return 7
    
    def _estimate_entity_revenue_impact(
        self,
        entity: Dict,
        entity_type: str,
        supplier_relationships: List[Dict]
    ) -> float:
        """
        Estime l'impact sur le CA (en %)
        
        Basé sur :
        - Volume d'affaires de l'entité
        - Criticité
        """
        if entity_type == "supplier":
            # Vérifier le volume d'affaires
            entity_id = entity.get('id')
            relationships = [r for r in supplier_relationships if r.get('supplier_id') == entity_id]
            
            if not relationships:
                return 1.0
            
            # Estimer l'impact basé sur la criticité
            max_criticality = max([
                3 if r.get('criticality') == 'HIGH' else 
                2 if r.get('criticality') == 'MEDIUM' else 1
                for r in relationships
            ])
            
            if max_criticality == 3:
                return 5.0  # 5% du CA
            elif max_criticality == 2:
                return 2.0  # 2% du CA
            else:
                return 0.5  # 0.5% du CA
        
        elif entity_type == "site":
            # Impact basé sur l'importance stratégique
            strategic_importance = entity.get('strategic_importance', 'MEDIUM')
            
            if strategic_importance == 'HIGH':
                return 10.0  # 10% du CA
            elif strategic_importance == 'MEDIUM':
                return 5.0  # 5% du CA
            else:
                return 2.0  # 2% du CA
        
        return 1.0
    
    # ========================================
    # Calcul des scores globaux
    # ========================================
    
    def _calculate_overall_risk(
        self,
        risk_projections: List[Dict]
    ) -> Tuple[str, float]:
        """
        Calcule le niveau de risque global et le score 360° global
        
        Returns:
            Tuple (risk_level, risk_score_360)
        """
        if not risk_projections:
            return "FAIBLE", 0.0
        
        # Score global = max des scores des entités concernées
        concerned_projections = [p for p in risk_projections if p['is_concerned']]
        
        if not concerned_projections:
            return "FAIBLE", 0.0
        
        max_risk_score = max([p['risk_score'] for p in concerned_projections])
        
        # Déterminer le niveau de risque
        if max_risk_score >= 80:
            risk_level = "CRITIQUE"
        elif max_risk_score >= 60:
            risk_level = "ÉLEVÉ"
        elif max_risk_score >= 40:
            risk_level = "MOYEN"
        else:
            risk_level = "FAIBLE"
        
        return risk_level, max_risk_score
    
    def _calculate_global_business_interruption(
        self,
        concerned_projections: List[Dict]
    ) -> float:
        """
        Calcule le Business Interruption Score global
        
        Returns:
            Score global (0-100)
        """
        if not concerned_projections:
            return 0.0
        
        # Score global = max des scores des entités concernées
        max_bi_score = max([p['business_interruption_score'] for p in concerned_projections])
        
        return max_bi_score
    
    def _estimate_disruption_days(self, document: Dict, event_type: str) -> int:
        """Estime la durée globale de l'interruption"""
        if event_type == "climatique":
            return 10
        elif event_type == "reglementaire":
            return 0
        elif event_type == "geopolitique":
            return 60
        return 7
    
    def _estimate_revenue_impact(
        self,
        concerned_projections: List[Dict],
        supplier_relationships: List[Dict]
    ) -> float:
        """Estime l'impact global sur le CA"""
        if not concerned_projections:
            return 0.0
        
        # Impact global = somme des impacts des entités concernées
        total_impact = sum([p['revenue_impact_percentage'] for p in concerned_projections])
        
        return min(100.0, total_impact)  # Cap à 100%
    
    def _calculate_global_probability(self, concerned_projections: List[Dict]) -> float:
        """Calcule le score de probabilité global"""
        if not concerned_projections:
            return 0.0
        
        # Probabilité globale = max des probabilités des entités concernées
        max_prob = max([p['probability_score'] for p in concerned_projections])
        return max_prob
    
    def _calculate_global_exposure(self, concerned_projections: List[Dict]) -> float:
        """Calcule le score d'exposition global"""
        if not concerned_projections:
            return 0.0
        
        # Exposition globale = max des expositions des entités concernées
        max_exposure = max([p['exposure_score'] for p in concerned_projections])
        return max_exposure
    
    # ========================================
    # Analyse de criticité (adaptée)
    # ========================================
    
    def _analyze_criticality_from_projections(
        self,
        concerned_projections: List[Dict],
        sites: List[Dict],
        suppliers: List[Dict],
        supplier_relationships: List[Dict]
    ) -> Dict:
        """
        Analyse de criticité basée sur les projections
        
        (Réutilise la logique existante de CriticalityAnalyzer)
        """
        # Extraire les entités concernées
        affected_sites_proj = [p for p in concerned_projections if p['entity_type'] == 'site']
        affected_suppliers_proj = [p for p in concerned_projections if p['entity_type'] == 'supplier']
        
        # Analyser chaque site
        site_criticalities = []
        for proj in affected_sites_proj:
            site = next((s for s in sites if s['id'] == proj['entity_id']), None)
            if site:
                # Mapper le score de risque vers un niveau d'impact
                if proj['risk_score'] >= 80:
                    impact_level = "Critique"
                elif proj['risk_score'] >= 60:
                    impact_level = "Important"
                else:
                    impact_level = "Standard"
                
                crit = self.criticality_analyzer.analyze_site_criticality(
                    site,
                    impact_level,
                    sites
                )
                site_criticalities.append(crit)
        
        # Analyser chaque fournisseur
        supplier_criticalities = []
        for proj in affected_suppliers_proj:
            supplier = next((s for s in suppliers if s['id'] == proj['entity_id']), None)
            if supplier:
                # Mapper le score de risque vers un niveau d'impact
                if proj['risk_score'] >= 80:
                    impact_level = "Critique"
                elif proj['risk_score'] >= 60:
                    impact_level = "Important"
                else:
                    impact_level = "Standard"
                
                crit = self.criticality_analyzer.analyze_supplier_criticality(
                    supplier,
                    impact_level,
                    supplier_relationships
                )
                supplier_criticalities.append(crit)
        
        # Construire le résultat (convertir les dataclass en dict pour la sérialisation JSON)
        all_criticalities = site_criticalities + supplier_criticalities
        return {
            "sites": [asdict(c) for c in site_criticalities],
            "suppliers": [asdict(c) for c in supplier_criticalities],
            "summary": {
                "total_critical": sum(1 for c in all_criticalities if c.overall_criticality == "critique"),
                "total_high": sum(1 for c in all_criticalities if c.overall_criticality == "fort"),
                "total_medium": sum(1 for c in all_criticalities if c.overall_criticality == "moyen")
            }
        }
    
    # ========================================
    # NOUVEAU: Agrégation des risques météo
    # ========================================
    
    def _aggregate_weather_risks(self, risk_projections: List[Dict]) -> Dict:
        """
        Agrège les risques météo de toutes les projections.
        
        Returns:
            {
                "entities_with_alerts": 3,
                "total_alerts": 8,
                "max_severity": "high",
                "average_weather_risk_score": 45.2,
                "alerts_by_type": {"snow": 2, "heavy_rain": 6},
                "entities_at_risk": [{"name": "...", "alerts_count": 3}]
            }
        """
        entities_with_alerts = []
        total_alerts = 0
        max_severity_weight = 0
        max_severity = None
        all_weather_scores = []
        alerts_by_type = {}
        
        severity_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        
        for projection in risk_projections:
            weather_risk = projection.get("weather_risk", {})
            
            if weather_risk.get("has_weather_risk", False):
                entity_alerts = weather_risk.get("alerts_count", 0)
                total_alerts += entity_alerts
                all_weather_scores.append(weather_risk.get("weather_risk_score", 0))
                
                entities_with_alerts.append({
                    "entity_id": projection["entity_id"],
                    "entity_name": projection["entity_name"],
                    "entity_type": projection["entity_type"],
                    "alerts_count": entity_alerts,
                    "max_severity": weather_risk.get("max_severity"),
                    "weather_summary": weather_risk.get("weather_summary", "")
                })
                
                # Trouver la sévérité max
                entity_severity = weather_risk.get("max_severity", "low")
                weight = severity_weights.get(entity_severity, 0)
                if weight > max_severity_weight:
                    max_severity_weight = weight
                    max_severity = entity_severity
                
                # Agréger les types d'alertes
                for alert_type, count in weather_risk.get("alerts_by_type", {}).items():
                    if alert_type not in alerts_by_type:
                        alerts_by_type[alert_type] = 0
                    alerts_by_type[alert_type] += count
        
        return {
            "entities_with_alerts": len(entities_with_alerts),
            "total_alerts": total_alerts,
            "max_severity": max_severity,
            "average_weather_risk_score": round(sum(all_weather_scores) / len(all_weather_scores), 2) if all_weather_scores else 0,
            "alerts_by_type": alerts_by_type,
            "entities_at_risk": entities_with_alerts[:10]  # Top 10
        }
    
    # ========================================
    # Génération de recommandations (LLM)
    # ========================================
    
    def _generate_recommendations(
        self,
        document: Dict,
        affected_sites: List[Dict],
        affected_suppliers: List[Dict],
        criticality_results: Dict,
        weather_risk_summary: Dict = None  # NOUVEAU: données météo
    ) -> List[str]:
        """
        Génère des recommandations détaillées et actionnables
        
        Recommandations structurées par :
        - Urgence (court terme vs moyen/long terme)
        - Type d'action (surveillance, mitigation, contingence)
        - Entités concernées (sites, fournisseurs)
        """
        recommendations = []
        event_type = document.get('event_type')
        event_title = document.get('title', 'Événement')
        
        # ========================================
        # 1. RECOMMANDATIONS IMMÉDIATES (0-7 jours)
        # ========================================
        
        if affected_sites:
            site_names = [s['name'] for s in affected_sites[:3]]
            site_count = len(affected_sites)
            
            # Surveillance des sites
            if site_count == 1:
                recommendations.append(
                    f"🚨 URGENT (0-24h) : Contacter le site {site_names[0]} pour évaluer l'impact réel de l'événement et confirmer la capacité de production. "
                    f"Mettre en place une cellule de crise si nécessaire."
                )
            else:
                recommendations.append(
                    f"🚨 URGENT (0-24h) : Contacter les {site_count} sites affectés ({', '.join(site_names)}) pour évaluer l'impact réel et la capacité de production. "
                    f"Prioriser les sites à forte criticité."
                )
            
            # Activation PCA
            recommendations.append(
                f"⚡ COURT TERME (1-7 jours) : Activer les Plans de Continuité d'Activité (PCA) pour les sites concernés. "
                f"Vérifier la disponibilité des équipes, des équipements de secours et des procédures d'urgence."
            )
        
        if affected_suppliers:
            supplier_names = [s['name'] for s in affected_suppliers[:3]]
            supplier_count = len(affected_suppliers)
            
            # Évaluation fournisseurs
            if supplier_count == 1:
                recommendations.append(
                    f"🚨 URGENT (0-48h) : Contacter le fournisseur {supplier_names[0]} pour évaluer sa capacité de livraison et les délais prévisionnels. "
                    f"Demander un plan d'action détaillé avec échéances."
                )
            else:
                recommendations.append(
                    f"🚨 URGENT (0-48h) : Contacter les {supplier_count} fournisseurs affectés ({', '.join(supplier_names)}) pour évaluer leur capacité de livraison. "
                    f"Prioriser les fournisseurs uniques (sole suppliers)."
                )
        
        # ========================================
        # 2. RECOMMANDATIONS TACTIQUES (1-4 semaines)
        # ========================================
        
        # Gestion des stocks
        if affected_suppliers:
            # Identifier les fournisseurs critiques
            critical_suppliers = [s for s in affected_suppliers if s.get('business_interruption_score', 0) > 70]
            
            if critical_suppliers:
                recommendations.append(
                    f"📦 STOCKS (1-2 semaines) : Augmenter les stocks de sécurité pour les produits fournis par {len(critical_suppliers)} fournisseur(s) critique(s). "
                    f"Objectif : couvrir 30-60 jours de production en cas d'interruption prolongée."
                )
            else:
                recommendations.append(
                    f"📦 STOCKS (1-2 semaines) : Évaluer les niveaux de stocks actuels pour les produits fournis par les fournisseurs affectés. "
                    f"Anticiper les ruptures potentielles et ajuster les commandes en conséquence."
                )
        
        # Double-sourcing / Fournisseurs alternatifs
        if affected_suppliers:
            sole_suppliers = [s for s in affected_suppliers if s.get('is_sole_supplier', False)]
            
            if sole_suppliers:
                recommendations.append(
                    f"🔄 SOURCING (2-4 semaines) : PRIORITÉ HAUTE - Identifier des fournisseurs alternatifs pour les {len(sole_suppliers)} fournisseur(s) unique(s) affecté(s). "
                    f"Lancer des appels d'offres d'urgence et négocier des contrats de secours. Risque de dépendance critique."
                )
            else:
                recommendations.append(
                    f"🔄 SOURCING (2-4 semaines) : Évaluer les options de double-sourcing pour les fournisseurs affectés. "
                    f"Contacter les fournisseurs alternatifs existants pour augmenter les volumes si nécessaire."
                )
        
        # ========================================
        # 3. RECOMMANDATIONS STRATÉGIQUES (1-6 mois)
        # ========================================
        
        # Recommandations spécifiques par type d'événement
        if event_type == "climatique":
            recommendations.append(
                f"🌍 STRATÉGIE (1-3 mois) : Réaliser une analyse de vulnérabilité climatique pour tous les sites et fournisseurs dans les zones à risque. "
                f"Intégrer les critères climatiques dans la sélection des futurs fournisseurs (cartographie des risques d'inondation, tempêtes, sécheresse)."
            )
            
            recommendations.append(
                f"💡 DIVERSIFICATION (3-6 mois) : Diversifier géographiquement la supply chain pour réduire l'exposition aux risques climatiques localisés. "
                f"Privilégier des fournisseurs dans des zones géographiques moins exposées aux événements météorologiques extrêmes."
            )
        
        elif event_type == "reglementaire":
            recommendations.append(
                f"📋 CONFORMITÉ (1-3 mois) : Évaluer les coûts de mise en conformité réglementaire pour les sites et fournisseurs concernés. "
                f"Planifier les investissements nécessaires (certifications, audits, modifications de processus) et les intégrer au budget."
            )
            
            recommendations.append(
                f"⚖️ VEILLE (3-6 mois) : Mettre en place une veille réglementaire proactive pour anticiper les futures évolutions législatives. "
                f"Former les équipes achats et qualité aux nouvelles exigences réglementaires (CBAM, LkSG, etc.)."
            )
        
        elif event_type == "geopolitique":
            recommendations.append(
                f"🌐 DIVERSIFICATION (1-3 mois) : Diversifier les sources d'approvisionnement vers des zones géographiques plus stables politiquement. "
                f"Réduire la dépendance aux fournisseurs situés dans des pays à risque géopolitique élevé."
            )
            
            recommendations.append(
                f"🛡️ STRATÉGIE ACHATS (3-6 mois) : Intégrer une analyse de risque géopolitique dans la stratégie achats. "
                f"Privilégier des fournisseurs dans des pays membres de l'UE ou ayant des accords commerciaux stables avec l'Europe."
            )
        
        # ========================================
        # 4. RECOMMANDATIONS TRANSVERSES
        # ========================================
        
        # Communication interne
        recommendations.append(
            f"📢 TRANSVERSE : Communiquer régulièrement (hebdomadaire) avec les équipes opérationnelles, achats et direction sur l'évolution de la situation. "
            f"Mettre en place un tableau de bord de suivi des indicateurs clés (délais de livraison, taux de service, stocks)."
        )
        
        # ========================================
        # 5. NOUVEAU: RECOMMANDATIONS MÉTÉO (Open-Meteo)
        # ========================================
        
        weather_risk_summary = weather_risk_summary or {}
        if weather_risk_summary.get("entities_with_alerts", 0) > 0:
            total_alerts = weather_risk_summary.get("total_alerts", 0)
            entities_count = weather_risk_summary.get("entities_with_alerts", 0)
            max_severity = weather_risk_summary.get("max_severity", "medium")
            alerts_by_type = weather_risk_summary.get("alerts_by_type", {})
            
            # Traduire les types d'alertes
            type_names = {
                "snow": "neige",
                "heavy_rain": "fortes pluies",
                "extreme_cold": "grand froid",
                "extreme_heat": "canicule",
                "strong_wind": "vents forts",
                "storm": "tempête"
            }
            
            alert_types_str = ", ".join([
                f"{count} {type_names.get(t, t)}"
                for t, count in alerts_by_type.items()
            ])
            
            # Recommandation urgente si sévérité critique ou haute
            if max_severity in ["critical", "high"]:
                recommendations.insert(0,  # En premier !
                    f"⛈️ ALERTE MÉTÉO CRITIQUE : {total_alerts} alerte(s) météo active(s) sur {entities_count} site(s)/fournisseur(s) "
                    f"({alert_types_str}). ACTIONS IMMÉDIATES REQUISES : "
                    f"1) Vérifier l'état des routes d'accès aux sites concernés. "
                    f"2) Anticiper les retards de livraison (2-5 jours). "
                    f"3) Prévenir les équipes logistiques et production."
                )
            else:
                recommendations.append(
                    f"🌤️ VIGILANCE MÉTÉO : {total_alerts} alerte(s) météo détectée(s) sur {entities_count} site(s)/fournisseur(s) "
                    f"({alert_types_str}). Surveiller l'évolution des conditions météorologiques et anticiper d'éventuels retards de livraison."
                )
            
            # Recommandation de transport si neige ou vent fort
            if "snow" in alerts_by_type or "strong_wind" in alerts_by_type:
                recommendations.append(
                    f"🚛 TRANSPORT : Risque élevé de perturbation des transports routiers (neige/vents). "
                    f"Contacter les transporteurs pour confirmer les livraisons. "
                    f"Envisager des modes de transport alternatifs si les délais sont critiques."
                )
            
            # Recommandation de production si températures extrêmes
            if "extreme_heat" in alerts_by_type or "extreme_cold" in alerts_by_type:
                recommendations.append(
                    f"🏭 PRODUCTION : Conditions de températures extrêmes prévues. "
                    f"Vérifier le bon fonctionnement des systèmes de climatisation/chauffage. "
                    f"Adapter les horaires de travail si nécessaire pour protéger les équipes."
                )
        
        # Analyse post-crise
        recommendations.append(
            f"📊 POST-ÉVÉNEMENT : Réaliser un retour d'expérience (REX) une fois la crise passée pour identifier les points d'amélioration dans la gestion de crise. "
            f"Mettre à jour les PCA et les procédures de gestion des risques supply chain en conséquence."
        )
        
        return recommendations

    def _generate_entity_reasoning(
        self,
        document: Dict,
        entity: Dict,
        entity_type: str,
        risk_score: float
    ) -> str:
        """
        Génère un raisonnement pour expliquer le score de risque d'une entité
        
        Returns:
            Texte explicatif
        """
        event_type = document.get('event_type')
        entity_name = entity.get('name')
        
        if event_type == "climatique":
            return f"{entity_name} est concerné par l'événement climatique en raison de sa proximité géographique. Score de risque : {risk_score:.1f}/100."
        elif event_type == "reglementaire":
            return f"{entity_name} est concerné par la réglementation en raison de son secteur d'activité et/ou produits. Score de risque : {risk_score:.1f}/100."
        elif event_type == "geopolitique":
            return f"{entity_name} est concerné par l'événement géopolitique en raison de sa localisation dans un pays affecté. Score de risque : {risk_score:.1f}/100."
        
        return f"Score de risque : {risk_score:.1f}/100."
    
    # ========================================
    # Utilitaires
    # ========================================
    
    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calcule la distance entre deux points GPS (formule de Haversine)
        
        Returns:
            Distance en kilomètres
        """
        # Convertir en radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Formule de Haversine
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Rayon de la Terre en km
        r = 6371
        
        return c * r
    # ========================================
    # Méthodes d'Explication (Transparence)
    # ========================================
    
    def _explain_why_concerned(self, document: Dict, entity: Dict, entity_type: str) -> str:
        """Explique pourquoi l'entité est concernée par l'événement"""
        event_type = document.get('event_type')
        entity_name = entity.get('name')
        
        if event_type == "climatique":
            geographic_scope = document.get('geographic_scope') or {}
            coordinates = geographic_scope.get('coordinates', {})
            event_lat = coordinates.get('latitude')
            event_lon = coordinates.get('longitude')
            entity_lat = entity.get('latitude')
            entity_lon = entity.get('longitude')
            
            if event_lat and entity_lat:
                distance_km = self._haversine_distance(event_lat, event_lon, entity_lat, entity_lon)
                return f"{entity_name} est situé à {distance_km:.1f} km de l'événement climatique (seuil: 200 km). Zone d'impact direct."
            else:
                return f"{entity_name} est dans la zone géographique affectée."
        
        elif event_type == "reglementaire":
            geographic_scope = document.get('geographic_scope') or {}
            affected_countries = geographic_scope.get('affected_countries', [])
            affected_sectors = geographic_scope.get('affected_sectors', [])
            affected_products = geographic_scope.get('affected_products', [])
            
            entity_country = entity.get('country')
            entity_sectors = entity.get('sectors', [])
            entity_products = entity.get('products', []) or entity.get('products_supplied', [])
            
            reasons = []
            if entity_country in affected_countries:
                reasons.append(f"Pays concerné: {entity_country}")
            if any(s in affected_sectors for s in entity_sectors):
                matching_sectors = [s for s in entity_sectors if s in affected_sectors]
                reasons.append(f"Secteur(s) concerné(s): {', '.join(matching_sectors)}")
            if any(p in affected_products for p in entity_products):
                matching_products = [p for p in entity_products if p in affected_products]
                reasons.append(f"Produit(s) concerné(s): {', '.join(matching_products)}")
            
            return f"{entity_name} est concerné par la réglementation. " + " | ".join(reasons)
        
        elif event_type == "geopolitique":
            geographic_scope = document.get('geographic_scope') or {}
            directly_affected = geographic_scope.get('directly_affected_countries', [])
            indirectly_affected = geographic_scope.get('indirectly_affected_countries', [])
            
            entity_country = entity.get('country')
            
            if entity_country in directly_affected:
                return f"{entity_name} est situé dans un pays directement affecté: {entity_country}"
            elif entity_country in indirectly_affected:
                return f"{entity_name} est situé dans un pays indirectement affecté: {entity_country}"
            else:
                return f"{entity_name} est dans la zone géopolitique affectée."
        
        return f"{entity_name} est concerné par l'événement."
    
    def _identify_risks(self, document: Dict, entity: Dict, entity_type: str) -> List[Dict]:
        """Identifie les risques concrets pour l'entité"""
        event_type = document.get('event_type')
        event_subtype = document.get('event_subtype', '')
        risks = []
        
        if event_type == "climatique":
            if "inondation" in event_subtype.lower():
                risks.append({
                    "type": "Interruption de production",
                    "probability": "100%",
                    "reason": "Site dans zone inondable, accès routier coupé"
                })
                risks.append({
                    "type": "Coupure électrique",
                    "probability": "60%",
                    "reason": "Transformateur électrique en zone à risque"
                })
                risks.append({
                    "type": "Dommages matériels",
                    "probability": "40%",
                    "reason": "Équipements au rez-de-chaussée exposés"
                })
            elif "tempête" in event_subtype.lower():
                risks.append({
                    "type": "Interruption de production",
                    "probability": "80%",
                    "reason": "Vents violents, risque de coupure électrique"
                })
                risks.append({
                    "type": "Dommages toiture",
                    "probability": "50%",
                    "reason": "Bâtiments industriels exposés"
                })
        
        elif event_type == "reglementaire":
            risks.append({
                "type": "Non-conformité réglementaire",
                "probability": "100%",
                "reason": "Nouvelle réglementation applicable immédiatement"
            })
            risks.append({
                "type": "Coûts de mise en conformité",
                "probability": "100%",
                "reason": "Investissements nécessaires (certifications, audits, processus)"
            })
            risks.append({
                "type": "Retard de livraison",
                "probability": "60%",
                "reason": "Temps d'adaptation aux nouvelles exigences"
            })
        
        elif event_type == "geopolitique":
            if "conflit" in event_subtype.lower() or "guerre" in event_subtype.lower():
                risks.append({
                    "type": "Interruption totale",
                    "probability": "90%",
                    "reason": "Zone de conflit, impossibilité d'opérer"
                })
                risks.append({
                    "type": "Rupture supply chain",
                    "probability": "100%",
                    "reason": "Frontières fermées, transport impossible"
                })
            elif "sanction" in event_subtype.lower():
                risks.append({
                    "type": "Impossibilité de paiement",
                    "probability": "100%",
                    "reason": "Sanctions financières, banques bloquées"
                })
                risks.append({
                    "type": "Rupture contrats",
                    "probability": "80%",
                    "reason": "Interdiction de commercer avec le pays"
                })
        
        return risks
    
    def _explain_impacts(self, document: Dict, entity: Dict, entity_type: str, disruption_days: int, revenue_impact: float) -> Dict:
        """Explique les impacts calculés"""
        event_type = document.get('event_type')
        entity_name = entity.get('name')
        
        impacts = {
            "production_loss": {
                "description": f"Perte de production estimée à {disruption_days} jours",
                "calculation": f"Basé sur historique d'événements similaires et capacité de récupération",
                "unit": "jours"
            },
            "revenue_impact": {
                "description": f"Impact sur le chiffre d'affaires: {revenue_impact:.1f}%",
                "calculation": self._explain_revenue_calculation(entity, entity_type, revenue_impact),
                "unit": "%"
            }
        }
        
        if event_type == "climatique":
            impacts["recovery_time"] = {
                "description": f"Temps de récupération estimé: {disruption_days + 5} jours",
                "calculation": f"{disruption_days} jours d'arrêt + 5 jours de remise en route",
                "unit": "jours"
            }
        
        return impacts
    
    def _explain_revenue_calculation(self, entity: Dict, entity_type: str, revenue_impact: float) -> str:
        """Explique le calcul de l'impact CA"""
        if entity_type == "site":
            strategic_importance = entity.get('strategic_importance', 'moyen')
            if strategic_importance == "critique":
                return f"Site stratégique critique (15% du CA global Hutchinson)"
            elif strategic_importance == "élevé":
                return f"Site à importance élevée (10% du CA global)"
            else:
                return f"Site à importance moyenne (5% du CA global)"
        else:  # supplier
            is_sole = entity.get('is_sole_supplier', False)
            if is_sole:
                return f"Fournisseur unique (sole supplier), impact critique sur la supply chain"
            else:
                return f"Fournisseur avec alternatives disponibles, impact limité"
    
    def _explain_severity(self, document: Dict) -> str:
        """Explique le score de sévérité"""
        event_type = document.get('event_type')
        event_subtype = document.get('event_subtype', '')
        
        if event_type == "climatique":
            if "majeur" in event_subtype.lower() or "catastrophique" in event_subtype.lower():
                return "Événement climatique majeur (score: 90/100). Impact étendu, durée prolongée."
            else:
                return "Événement climatique modéré (score: 60/100). Impact localisé, durée limitée."
        elif event_type == "reglementaire":
            return "Nouvelle réglementation (score: 70/100). Impact sur conformité et processus."
        elif event_type == "geopolitique":
            if "conflit" in event_subtype.lower():
                return "Conflit armé (score: 95/100). Impact critique, durée indéterminée."
            else:
                return "Instabilité géopolitique (score: 75/100). Impact significatif."
        
        return "Événement standard (score: 50/100)"
    
    def _explain_probability(self, document: Dict, entity: Dict, entity_type: str) -> str:
        """Explique le score de probabilité"""
        event_type = document.get('event_type')
        
        if event_type == "climatique":
            geographic_scope = document.get('geographic_scope') or {}
            coordinates = geographic_scope.get('coordinates', {})
            event_lat = coordinates.get('latitude')
            event_lon = coordinates.get('longitude')
            entity_lat = entity.get('latitude')
            entity_lon = entity.get('longitude')
            
            if event_lat and entity_lat:
                distance_km = self._haversine_distance(event_lat, event_lon, entity_lat, entity_lon)
                if distance_km < 50:
                    return f"Probabilité 100%: Entité dans zone d'impact direct ({distance_km:.1f} km)"
                elif distance_km < 100:
                    return f"Probabilité 80%: Entité dans zone d'impact proche ({distance_km:.1f} km)"
                else:
                    return f"Probabilité 60%: Entité dans zone d'impact étendu ({distance_km:.1f} km)"
        
        elif event_type == "reglementaire":
            return "Probabilité 100%: Réglementation applicable à l'entité (pays/secteur/produits concernés)"
        
        elif event_type == "geopolitique":
            return "Probabilité 90%: Entité dans pays affecté par l'événement géopolitique"
        
        return "Probabilité 50%: Impact possible mais incertain"
    
    def _explain_exposure(self, entity: Dict, entity_type: str, supplier_relationships: List[Dict]) -> str:
        """Explique le score d'exposition"""
        if entity_type == "site":
            strategic_importance = entity.get('strategic_importance', 'moyen')
            if strategic_importance == "critique":
                return "Exposition 100%: Site stratégique critique (15% du CA, produits clés)"
            elif strategic_importance == "élevé":
                return "Exposition 80%: Site à importance élevée (10% du CA)"
            else:
                return "Exposition 60%: Site à importance moyenne (5% du CA)"
        else:  # supplier
            is_sole = entity.get('is_sole_supplier', False)
            if is_sole:
                return "Exposition 100%: Fournisseur unique (sole supplier), aucune alternative immédiate"
            else:
                # Compter le nombre de sites clients
                entity_id = entity.get('id')
                client_sites = [r for r in supplier_relationships if r.get('supplier_id') == entity_id]
                if len(client_sites) > 3:
                    return f"Exposition 80%: Fournisseur de {len(client_sites)} sites Hutchinson"
                else:
                    return f"Exposition 60%: Fournisseur de {len(client_sites)} site(s), alternatives disponibles"
    
    def _explain_urgency(self, document: Dict) -> str:
        """Explique le score d'urgence"""
        # Simuler la date de l'événement (en production, utiliser document.get('publication_date'))
        return "Urgence 90%: Événement en cours, action immédiate requise (0-48h)"
