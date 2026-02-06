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
    
    def __init__(self, llm_model: str = None):
        """
        Initialise Agent 2 Extended
        
        Args:
            llm_model: Modèle LLM à utiliser pour le raisonnement (optionnel)
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
        # Génération de recommandations et sections détaillées (LLM avec données BI)
        # ========================================
        detailed_report = self._generate_recommendations(
            document,
            affected_sites,
            affected_suppliers,
            criticality_results,
            weather_risk_summary,
            risk_projections  # NOUVEAU: passer les projections avec données BI
        )
        
        # Extraire les différentes sections du rapport
        recommendations = detailed_report.get("recommendations", [])
        context_and_stakes = detailed_report.get("context_and_stakes")
        affected_entities_details = detailed_report.get("affected_entities_details")
        financial_analysis = detailed_report.get("financial_analysis")
        timeline = detailed_report.get("timeline")
        prioritization_matrix = detailed_report.get("prioritization_matrix")
        do_nothing_scenario = detailed_report.get("do_nothing_scenario")
        recommendations_model = detailed_report.get("_model_used", "unknown")
        
        # ========================================
        # NOUVEAU: Extraire les informations de source (demande client)
        # ========================================
        source_info = self._extract_source_info(document)
        
        # ========================================
        # Construire le résultat final
        # ========================================
        risk_analysis = {
            "document_id": event_id,
            "event_type": event_type,
            "event_subtype": document.get('event_subtype'),
            "analysis_timestamp": datetime.utcnow().isoformat(),
            
            # ========================================
            # NOUVEAU: SOURCE CITÉE (demande client obligatoire)
            # "À chaque fois, vous mettez la source. L'utilisateur peut cliquer sur la source."
            # ========================================
            "source": source_info,
            
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
            
            # Recommandations (Section 4)
            "recommendations": recommendations,
            
            # NOUVEAU : Sections détaillées du rapport (7 sections)
            "context_and_stakes": context_and_stakes,  # Section 1
            "affected_entities_details": affected_entities_details,  # Section 2
            "financial_analysis": financial_analysis,  # Section 3
            "timeline": timeline,  # Section 5
            "prioritization_matrix": prioritization_matrix,  # Section 6
            "do_nothing_scenario": do_nothing_scenario,  # Section 7
            "recommendations_model": recommendations_model,  # Modèle utilisé
            
            # NOUVEAU: Mention "Généré par IA" (demande client)
            "generated_by_ai": True,
            "ai_model_used": recommendations_model,
            "ai_confidence_score": None,  # Sera rempli par LLM Judge
            
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
        - business_impact_details (NOUVEAU: calcul BI détaillé avec vraies données)
        
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
                weather_risks.get(site.get('id'), {}),
                sites  # NOUVEAU: passer les sites pour les calculs BI
            )
            projections.append(projection)
        
        # Boucler sur les fournisseurs
        for supplier in suppliers:
            projection = self._project_on_entity(
                document,
                supplier,
                'supplier',
                supplier_relationships,
                weather_risks.get(supplier.get('id'), {}),
                sites  # NOUVEAU: passer les sites pour les calculs BI
            )
            projections.append(projection)
        
        return projections
    
    def _project_on_entity(
        self,
        document: Dict,
        entity: Dict,
        entity_type: str,  # 'site' ou 'supplier'
        supplier_relationships: List[Dict],
        weather_risk: Dict = None,  # NOUVEAU: données météo Open-Meteo
        sites: List[Dict] = None  # NOUVEAU: liste des sites pour calcul BI fournisseurs
    ) -> Dict:
        """
        Calcule la projection pour UNE entité (site ou fournisseur)
        
        AMÉLIORÉ: Utilise les vraies données Business Interruption de la base de données
        pour calculer des impacts financiers réels (daily_revenue, contract_penalties, etc.)
        
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
                "weather_risk_score": 45.0,
                "weather_risk": {...},
                "reasoning": "...",
                "estimated_disruption_days": 14,
                "revenue_impact_percentage": 3.5,
                "business_impact_details": {...}  # NOUVEAU: calcul BI détaillé
            }
        """
        event_type = document.get('event_type')
        event_id = document.get('id')
        entity_id = entity.get('id')
        entity_name = entity.get('name')
        weather_risk = weather_risk or {}
        sites = sites or []
        
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
                "revenue_impact_percentage": 0.0,
                "business_impact_details": None
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
        
        # ========================================
        # NOUVEAU: Business Interruption avec vraies données
        # ========================================
        
        # Estimer les jours de disruption
        disruption_days = self._estimate_entity_disruption_days(document, entity, entity_type)
        
        # Ajouter des jours de disruption si risque météo
        if weather_risk.get("has_weather_risk", False):
            weather_disruption = self._estimate_weather_disruption_days(weather_risk)
            disruption_days += weather_disruption
        
        # NOUVEAU: Obtenir le calcul BI détaillé avec les vraies données
        business_impact = self._estimate_entity_revenue_impact(
            entity, entity_type, supplier_relationships, sites
        )
        
        # Extraire le % d'impact (pour compatibilité)
        revenue_impact = business_impact.get("revenue_impact_percentage", 1.0)
        
        # NOUVEAU: Calculer le BI score basé sur les vraies données
        # Formule améliorée: prend en compte l'impact financier réel
        total_daily_impact = business_impact.get("total_daily_impact_eur", 0)
        stock_coverage = business_impact.get("stock_coverage_days", 30)
        is_sole_supplier = business_impact.get("is_sole_supplier", False)
        
        # Si le fournisseur ferme, quand l'impact commence-t-il ?
        # Impact réel = après épuisement du stock
        effective_disruption_days = max(0, disruption_days - stock_coverage)
        
        # Score BI amélioré (0-100)
        # Base: exposure * impact financier relatif
        # Multiplicateur si fournisseur unique
        if total_daily_impact > 0:
            # Normaliser l'impact sur 100
            # 100k€/jour = score max
            financial_impact_normalized = min(100, (total_daily_impact / 100000) * 100)
            
            # Combiner avec l'exposition et les jours effectifs
            business_interruption = (
                financial_impact_normalized * 0.4 +  # Impact financier (40%)
                exposure * 0.3 +                     # Exposition (30%)
                (effective_disruption_days / 30) * 100 * 0.2 +  # Durée effective (20%)
                (100 if is_sole_supplier else 0) * 0.1  # Risque mono-fournisseur (10%)
            )
        else:
            # Fallback si pas de données financières
            business_interruption = exposure * (disruption_days / 30) * revenue_impact
        
        business_interruption = min(100.0, business_interruption)
        
        # Raisonnement avec LLM (analyse en cascade) - passer les données BI enrichies
        reasoning = self._generate_entity_reasoning(
            document, entity, entity_type, risk_score_360,
            business_impact=business_impact,
            supplier_relationships=supplier_relationships,
            sites=sites
        )
        
        # Ajouter le contexte météo au raisonnement si pertinent
        if weather_risk.get("has_weather_risk", False):
            reasoning += f"\n\n⚠️ RISQUE MÉTÉO: {weather_risk.get('weather_summary', '')}"
        
        # Construire reasoning_details (transparence complète) avec données BI
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
                "business_interruption": {
                    "daily_impact_eur": total_daily_impact,
                    "stock_coverage_days": stock_coverage,
                    "effective_disruption_days": effective_disruption_days,
                    "is_sole_supplier": is_sole_supplier,
                    "affected_customers_count": len(business_impact.get("affected_customers", [])),
                    "calculation_breakdown": business_impact.get("calculation_breakdown", "")
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
            "revenue_impact_percentage": round(revenue_impact, 2),
            "business_impact_details": business_impact  # NOUVEAU: détails BI complets
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
        supplier_relationships: List[Dict],
        sites: List[Dict] = None
    ) -> Dict:
        """
        Estime l'impact Business Interruption avec les vraies données
        
        NOUVEAU: Retourne un dict complet avec les calculs détaillés :
        {
            "revenue_impact_percentage": float,  # Impact % (ancien comportement, pour compatibilité)
            "daily_revenue_loss_eur": float,     # Perte de CA par jour
            "customer_penalties_per_day_eur": float,  # Pénalités contractuelles par jour
            "total_daily_impact_eur": float,     # Impact total par jour
            "switch_time_days": int,             # Jours pour changer de fournisseur
            "stock_coverage_days": int,          # Jours de stock disponible
            "is_sole_supplier": bool,            # Fournisseur unique ?
            "affected_customers": list,          # Clients affectés (avec détails)
            "calculation_breakdown": str         # Explication du calcul
        }
        """
        sites = sites or []
        
        if entity_type == "supplier":
            return self._calculate_supplier_business_impact(entity, supplier_relationships, sites)
        
        elif entity_type == "site":
            return self._calculate_site_business_impact(entity, supplier_relationships)
        
        return {
            "revenue_impact_percentage": 1.0,
            "daily_revenue_loss_eur": 0,
            "customer_penalties_per_day_eur": 0,
            "total_daily_impact_eur": 0,
            "switch_time_days": 0,
            "stock_coverage_days": 0,
            "is_sole_supplier": False,
            "affected_customers": [],
            "calculation_breakdown": "Type d'entité inconnu"
        }
    
    def _calculate_supplier_business_impact(
        self,
        supplier: Dict,
        supplier_relationships: List[Dict],
        sites: List[Dict]
    ) -> Dict:
        """
        Calcule l'impact Business Interruption pour un fournisseur
        
        Utilise les vraies données :
        - daily_consumption_value de chaque relation
        - contract_penalties_per_day des clients
        - stock_coverage_days
        - is_sole_supplier
        - switch_time_days du fournisseur
        """
        supplier_id = supplier.get('id')
        
        # Récupérer les relations de ce fournisseur
        relationships = [r for r in supplier_relationships if r.get('supplier_id') == supplier_id]
        
        if not relationships:
            return {
                "revenue_impact_percentage": 0.5,
                "daily_revenue_loss_eur": 0,
                "customer_penalties_per_day_eur": 0,
                "total_daily_impact_eur": 0,
                "switch_time_days": 0,
                "stock_coverage_days": 0,
                "is_sole_supplier": False,
                "affected_customers": [],
                "calculation_breakdown": "Aucune relation site-fournisseur trouvée"
            }
        
        # Calculer l'impact cumulé sur tous les sites clients
        total_daily_consumption = 0
        total_penalties_per_day = 0
        min_stock_coverage = float('inf')
        has_sole_supplier = False
        affected_sites = []
        affected_customers = []
        
        for rel in relationships:
            site_id = rel.get('hutchinson_site_id')
            site = next((s for s in sites if s.get('id') == site_id), None)
            
            daily_consumption = rel.get('daily_consumption_value') or 0
            penalties = rel.get('contract_penalties_per_day') or 0
            stock_days = rel.get('stock_coverage_days') or 0
            is_sole = rel.get('is_sole_supplier', False)
            
            total_daily_consumption += daily_consumption
            total_penalties_per_day += penalties
            
            if stock_days > 0:
                min_stock_coverage = min(min_stock_coverage, stock_days)
            
            if is_sole:
                has_sole_supplier = True
            
            if site:
                site_name = site.get('name', 'Site inconnu')
                site_daily_revenue = site.get('daily_revenue') or 0
                key_customers = site.get('key_customers') or []
                
                affected_sites.append({
                    "site_id": site_id,
                    "site_name": site_name,
                    "daily_consumption": daily_consumption,
                    "stock_coverage_days": stock_days,
                    "is_sole_supplier": is_sole
                })
                
                # Récupérer les pénalités clients du site (données key_customers)
                for customer in key_customers:
                    customer_penalty = customer.get('penalty_per_day_eur') or 0
                    if customer_penalty > 0:
                        affected_customers.append({
                            "customer_name": customer.get('name', 'Client inconnu'),
                            "site_impacted": site_name,
                            "revenue_share_pct": customer.get('revenue_share_pct', 0),
                            "penalty_per_day_eur": customer_penalty,
                            "contract_type": customer.get('contract_type', 'unknown')
                        })
                        total_penalties_per_day += customer_penalty
        
        # Si stock coverage est infini (pas de données), utiliser valeur par défaut
        if min_stock_coverage == float('inf'):
            min_stock_coverage = 30  # Par défaut 30 jours
        
        # Données fournisseur
        switch_time = supplier.get('switch_time_days') or 30
        criticality_score = supplier.get('criticality_score') or 5
        
        # Calculer l'impact total par jour
        # Impact = consommation journalière + pénalités clients
        total_daily_impact = total_daily_consumption + total_penalties_per_day
        
        # Estimer le % d'impact sur le CA global Hutchinson
        # (Approximation basée sur la consommation)
        hutchinson_daily_revenue = sum([s.get('daily_revenue') or 0 for s in sites])
        if hutchinson_daily_revenue > 0:
            revenue_impact_pct = (total_daily_impact / hutchinson_daily_revenue) * 100
        else:
            # Fallback si pas de données revenue
            revenue_impact_pct = criticality_score * 1.0  # 1% par point de criticité
        
        # Construire l'explication du calcul
        breakdown = f"""
📊 CALCUL D'IMPACT BUSINESS INTERRUPTION - {supplier.get('name', 'Fournisseur')}
{'='*60}

🔗 Sites approvisionnés: {len(affected_sites)}
   - Consommation quotidienne totale: {total_daily_consumption:,.0f}€

📦 Couverture stock minimum: {min_stock_coverage} jours
   → Délai avant impact réel sur production

🔄 Temps de substitution: {switch_time} jours
   → Temps pour trouver un fournisseur alternatif

⚠️  Fournisseur unique pour au moins un site: {'OUI' if has_sole_supplier else 'NON'}

💰 IMPACT FINANCIER PAR JOUR D'ARRÊT:
   - Approvisionnement manquant: {total_daily_consumption:,.0f}€
   - Pénalités contractuelles clients: {total_penalties_per_day:,.0f}€
   - TOTAL: {total_daily_impact:,.0f}€/jour

📈 Impact estimé sur CA Hutchinson: {revenue_impact_pct:.2f}%
"""
        
        return {
            "revenue_impact_percentage": min(revenue_impact_pct, 100.0),
            "daily_revenue_loss_eur": total_daily_consumption,
            "customer_penalties_per_day_eur": total_penalties_per_day,
            "total_daily_impact_eur": total_daily_impact,
            "switch_time_days": switch_time,
            "stock_coverage_days": min_stock_coverage,
            "is_sole_supplier": has_sole_supplier,
            "affected_customers": affected_customers,
            "affected_sites": affected_sites,
            "calculation_breakdown": breakdown
        }
    
    def _calculate_site_business_impact(
        self,
        site: Dict,
        supplier_relationships: List[Dict]
    ) -> Dict:
        """
        Calcule l'impact Business Interruption pour un site Hutchinson
        
        Utilise les vraies données :
        - daily_revenue du site
        - key_customers (avec pénalités)
        - safety_stock_days
        - recovery_time_days
        """
        site_id = site.get('id')
        site_name = site.get('name', 'Site')
        
        daily_revenue = site.get('daily_revenue') or 0
        daily_production = site.get('daily_production_units') or 0
        safety_stock = site.get('safety_stock_days') or 0
        recovery_time = site.get('recovery_time_days') or 7
        key_customers_raw = site.get('key_customers') or []
        customer_penalty_per_day = site.get('customer_penalty_per_day') or 0
        
        # Gérer key_customers qui peut être string ou liste
        if isinstance(key_customers_raw, str):
            # Format string "Stellantis, Renault, VW" → utiliser customer_penalty_per_day global
            customer_names = [c.strip() for c in key_customers_raw.split(',') if c.strip()]
            affected_customers = [{"customer_name": name} for name in customer_names]
            total_penalties_per_day = customer_penalty_per_day
        elif isinstance(key_customers_raw, list):
            # Format liste de dicts
            total_penalties_per_day = 0
            affected_customers = []
            for customer in key_customers_raw:
                if isinstance(customer, dict):
                    penalty = customer.get('penalty_per_day_eur') or 0
                    total_penalties_per_day += penalty
                    if penalty > 0:
                        affected_customers.append({
                            "customer_name": customer.get('name', 'Client inconnu'),
                            "revenue_share_pct": customer.get('revenue_share_pct', 0),
                            "penalty_per_day_eur": penalty,
                            "contract_type": customer.get('contract_type', 'unknown')
                        })
                else:
                    # String dans la liste
                    affected_customers.append({"customer_name": str(customer)})
        else:
            affected_customers = []
            total_penalties_per_day = customer_penalty_per_day
        
        # Impact total par jour = perte de CA + pénalités
        total_daily_impact = daily_revenue + total_penalties_per_day
        
        # Trouver les fournisseurs critiques de ce site
        relationships = [r for r in supplier_relationships if r.get('hutchinson_site_id') == site_id]
        sole_suppliers_count = sum(1 for r in relationships if r.get('is_sole_supplier'))
        
        breakdown = f"""
📊 CALCUL D'IMPACT BUSINESS INTERRUPTION - Site {site_name}
{'='*60}

💰 Chiffre d'affaires quotidien: {daily_revenue:,.0f}€
🏭 Production quotidienne: {daily_production:,} unités
📦 Stock de sécurité: {safety_stock} jours
⏱️  Temps de reprise estimé: {recovery_time} jours

👥 CLIENTS IMPACTÉS ({len(affected_customers)}):
"""
        for c in affected_customers:
            if isinstance(c, dict):
                name = c.get('customer_name', 'Inconnu')
                share = c.get('revenue_share_pct', 0)
                penalty = c.get('penalty_per_day_eur', 0)
                breakdown += f"   - {name}: {share}% du CA, {penalty:,.0f}€/jour de pénalité\n"
            else:
                breakdown += f"   - {c}\n"
        
        # Message adapté selon le nombre de fournisseurs uniques
        if sole_suppliers_count > 0:
            sole_supplier_msg = f"⚠️ {sole_suppliers_count} fournisseur(s) unique(s) - RISQUE ÉLEVÉ de rupture supply chain"
        else:
            sole_supplier_msg = f"✅ Aucun fournisseur unique - Risque supply chain maîtrisé"
        
        breakdown += f"""
🔗 {sole_supplier_msg}

💸 IMPACT FINANCIER PAR JOUR D'ARRÊT:
   - Perte de CA: {daily_revenue:,.0f}€
   - Pénalités clients: {total_penalties_per_day:,.0f}€
   - TOTAL: {total_daily_impact:,.0f}€/jour
"""
        
        # Revenue impact % (par rapport au CA total estimé Hutchinson)
        # Approximation : on considère que ce site représente une partie du CA total
        strategic_importance = site.get('strategic_importance', 'MEDIUM')
        if strategic_importance == 'HIGH':
            revenue_impact_pct = 15.0
        elif strategic_importance == 'MEDIUM':
            revenue_impact_pct = 8.0
        else:
            revenue_impact_pct = 3.0
        
        return {
            "revenue_impact_percentage": revenue_impact_pct,
            "daily_revenue_loss_eur": daily_revenue,
            "customer_penalties_per_day_eur": total_penalties_per_day,
            "total_daily_impact_eur": total_daily_impact,
            "switch_time_days": 0,  # N/A pour un site
            "stock_coverage_days": safety_stock,
            "is_sole_supplier": False,  # N/A pour un site
            "affected_customers": affected_customers,
            "recovery_time_days": recovery_time,
            "calculation_breakdown": breakdown
        }
    
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
    
    # ========================================
    # NOUVEAU: Extraction des infos source (demande client)
    # ========================================
    
    def _extract_source_info(self, document: Dict) -> Dict:
        """
        Extrait les informations de source pour le rapport.
        
        Demande client obligatoire:
        > "À chaque fois, vous mettez la source. L'utilisateur peut cliquer 
        > sur la source pour aller voir effectivement."
        
        Returns:
            {
                "title": "Règlement (UE) 2023/956 - CBAM",
                "url": "https://eur-lex.europa.eu/...",
                "publication_date": "2023-05-10",
                "application_date": "2026-01-01",
                "celex_id": "32023R0956",
                "document_type": "Règlement",
                "excerpt": "Les importateurs d'aluminium, acier, ciment..."
            }
        """
        # Extraire l'URL source
        source_url = document.get('source_url', '')
        
        # Si pas d'URL directe, essayer de construire depuis les métadonnées
        if not source_url:
            extra_meta = document.get('extra_metadata', {}) or {}
            celex_id = extra_meta.get('celex_id', '')
            if celex_id:
                # Construire l'URL EUR-Lex depuis le CELEX
                source_url = f"https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:{celex_id}"
        
        # Extraire le CELEX ID
        extra_meta = document.get('extra_metadata', {}) or {}
        celex_id = extra_meta.get('celex_id', '')
        
        # Extraire les dates (depuis le document ou les métadonnées)
        publication_date = document.get('publication_date')
        if not publication_date:
            # Essayer d'extraire depuis created_at
            created_at = document.get('created_at')
            if created_at:
                publication_date = str(created_at)[:10] if created_at else None
        
        # Date d'application (à extraire du contenu ou des métadonnées)
        application_date = document.get('application_date')
        if not application_date:
            # Essayer d'extraire depuis le contenu via regex
            application_date = self._extract_application_date(document.get('content', ''))
        
        # Extraire un extrait pertinent du texte (premiers 500 caractères significatifs)
        content = document.get('content', '') or document.get('summary', '') or ''
        excerpt = self._extract_relevant_excerpt(content)
        
        return {
            "title": document.get('title', 'Document sans titre'),
            "url": source_url,
            "publication_date": publication_date,
            "application_date": application_date,
            "celex_id": celex_id,
            "document_type": document.get('event_subtype', 'Réglementation'),
            "excerpt": excerpt,
            "can_click": bool(source_url)  # Indique si l'utilisateur peut cliquer
        }
    
    def _extract_application_date(self, content: str) -> Optional[str]:
        """
        Essaie d'extraire la date d'application depuis le contenu.
        
        Recherche des patterns comme:
        - "s'applique à partir du 1er janvier 2026"
        - "entre en vigueur le 01/01/2026"
        - "applicable from 1 January 2026"
        """
        import re
        
        if not content:
            return None
        
        # Patterns français
        patterns = [
            r"s'applique\s+(?:à partir\s+)?du\s+(\d{1,2}(?:er)?\s+\w+\s+\d{4})",
            r"entre en vigueur\s+(?:le\s+)?(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})",
            r"applicable\s+(?:à compter\s+)?du\s+(\d{1,2}(?:er)?\s+\w+\s+\d{4})",
            r"date d'application\s*:\s*(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})",
            # Patterns anglais
            r"applies from\s+(\d{1,2}\s+\w+\s+\d{4})",
            r"entry into force\s*:\s*(\d{1,2}\s+\w+\s+\d{4})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_relevant_excerpt(self, content: str, max_length: int = 500) -> str:
        """
        Extrait un extrait pertinent du document.
        
        Cherche les passages les plus significatifs (articles, définitions, etc.)
        """
        if not content:
            return ""
        
        # Nettoyer le contenu
        content = content.strip()
        
        # Chercher des sections importantes
        important_markers = [
            "Article 1",
            "Objet et champ d'application",
            "Définitions",
            "Le présent règlement",
            "La présente directive",
            "Les États membres",
            "Les importateurs",
        ]
        
        for marker in important_markers:
            idx = content.find(marker)
            if idx != -1:
                # Extraire à partir de ce point
                excerpt = content[idx:idx + max_length]
                # Couper proprement à la fin d'une phrase
                last_period = excerpt.rfind('.')
                if last_period > max_length // 2:
                    excerpt = excerpt[:last_period + 1]
                return excerpt.strip()
        
        # Fallback: premiers caractères
        excerpt = content[:max_length]
        last_period = excerpt.rfind('.')
        if last_period > max_length // 2:
            excerpt = excerpt[:last_period + 1]
        
        return excerpt.strip() + "..." if len(content) > max_length else excerpt.strip()
    
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
                "entities_at_risk": [{"name": "...", "alerts_count": 3}],
                "logistics_recommendations": [...]  # NOUVEAU
            }
        """
        entities_with_alerts = []
        total_alerts = 0
        max_severity_weight = 0
        max_severity = None
        all_weather_scores = []
        alerts_by_type = {}
        all_logistics_recommendations = []  # NOUVEAU
        
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
                
                # NOUVEAU: Collecter les recommandations logistiques
                logistics_recs = weather_risk.get("logistics_recommendations", [])
                all_logistics_recommendations.extend(logistics_recs)
                
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
        
        # NOUVEAU: Trier les recommandations par priorité
        priority_order = {"critique": 0, "haute": 1, "moyenne": 2, "basse": 3}
        all_logistics_recommendations.sort(
            key=lambda x: priority_order.get(x.get("priority", "moyenne"), 2)
        )
        
        return {
            "entities_with_alerts": len(entities_with_alerts),
            "total_alerts": total_alerts,
            "max_severity": max_severity,
            "average_weather_risk_score": round(sum(all_weather_scores) / len(all_weather_scores), 2) if all_weather_scores else 0,
            "alerts_by_type": alerts_by_type,
            "entities_at_risk": entities_with_alerts[:10],  # Top 10
            "logistics_recommendations": all_logistics_recommendations[:15]  # NOUVEAU: Top 15 recommandations
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
        weather_risk_summary: Dict = None,
        risk_projections: List[Dict] = None
    ) -> Dict:
        """
        Génère un rapport complet détaillé avec 7 sections via LLM
        
        NOUVEAU: Retourne un dict avec les 7 sections + recommendations
        
        Returns:
            Dict avec: {
                "recommendations": [...],
                "context_and_stakes": "...",
                "affected_entities_details": "...",
                "financial_analysis": "...",
                "timeline": "...",
                "prioritization_matrix": "...",
                "do_nothing_scenario": "...",
                "model_used": "gpt-4o-mini"
            }
        """
        event_type = document.get('event_type')
        event_title = document.get('title', 'Événement')
        
        # Essayer le LLM d'abord
        if self.llm_reasoning.llm_available:
            try:
                llm_result = self._generate_llm_recommendations(
                    document, affected_sites, affected_suppliers, 
                    criticality_results, weather_risk_summary, risk_projections
                )
                if llm_result:
                    return llm_result  # Retourne TOUT (7 sections + recommendations)
            except Exception as e:
                print(f"⚠️ LLM detailed report failed, using fallback: {e}")
        
        # Fallback: templates (seulement recommendations)
        fallback_recommendations = self._generate_fallback_recommendations(
            document, affected_sites, affected_suppliers, 
            criticality_results, weather_risk_summary
        )
        
        return {
            "recommendations": fallback_recommendations,
            "context_and_stakes": None,
            "affected_entities_details": None,
            "financial_analysis": None,
            "timeline": None,
            "prioritization_matrix": None,
            "do_nothing_scenario": None,
            "model_used": "fallback"
        }
    
    def _generate_llm_recommendations(
        self,
        document: Dict,
        affected_sites: List[Dict],
        affected_suppliers: List[Dict],
        criticality_results: Dict,
        weather_risk_summary: Dict,
        risk_projections: List[Dict]
    ) -> Dict:
        """
        Génère un rapport complet détaillé via le LLM (7 sections)
        
        NOUVEAU: Retourne un dict avec toutes les sections, pas juste recommendations
        NOUVEAU: Utilise gpt-4o-mini pour économiser les coûts
        """
        # Construire le prompt avec toutes les données BI
        prompt = self._build_recommendations_prompt(
            document, affected_sites, affected_suppliers,
            criticality_results, weather_risk_summary, risk_projections
        )
        
        try:
            # Utiliser gpt-4o-mini pour les rapports détaillés (économies de coûts)
            recommendations_model = "gpt-4o-mini" if self.llm_reasoning.llm_provider == "openai" else self.llm_reasoning.model
            
            if self.llm_reasoning.llm_provider == "openai":
                response = self.llm_reasoning.client.chat.completions.create(
                    model=recommendations_model,  # gpt-4o-mini au lieu de gpt-4o
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=8192  # Augmenté pour les 7 sections
                )
                content = response.choices[0].message.content.strip()
            else:
                response = self.llm_reasoning.client.messages.create(
                    model=recommendations_model,
                    max_tokens=8192,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.content[0].text.strip()
            
            # Nettoyer le JSON
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            result = json.loads(content.strip())
            
            # Ajouter le modèle utilisé dans le résultat
            result["_model_used"] = recommendations_model
            
            return result  # Retourner TOUT le résultat (7 sections)
            
        except Exception as e:
            print(f"⚠️ LLM detailed report generation failed: {e}")
            return None
    
    def _build_recommendations_prompt(
        self,
        document: Dict,
        affected_sites: List[Dict],
        affected_suppliers: List[Dict],
        criticality_results: Dict,
        weather_risk_summary: Dict,
        risk_projections: List[Dict]
    ) -> str:
        """
        Construit un prompt AMÉLIORÉ pour générer un rapport d'analyse complet et détaillé
        avec 7 sections obligatoires
        """
        event_type = document.get('event_type', 'inconnu')
        event_subtype = document.get('event_subtype', '')
        event_title = document.get('title', 'Événement')
        event_content = document.get('content', 'N/A')[:3000]  # Augmenté de 500 à 3000 chars
        
        # Résumer les impacts BI des projections
        bi_summary = []
        if risk_projections:
            for proj in risk_projections:
                if proj.get('is_concerned') and proj.get('business_impact_details'):
                    bi = proj['business_impact_details']
                    bi_summary.append({
                        "entity": proj.get('entity_name'),
                        "type": proj.get('entity_type'),
                        "risk_score": proj.get('risk_score', 0),
                        "business_interruption_score": proj.get('business_interruption_score', 0),
                        "daily_impact_eur": bi.get('total_daily_impact_eur', 0),
                        "is_sole_supplier": bi.get('is_sole_supplier', False),
                        "stock_coverage_days": bi.get('stock_coverage_days', 0),
                        "switch_time_days": bi.get('switch_time_days', 0),
                        "affected_customers": [c.get('customer_name') for c in bi.get('affected_customers', [])][:3]
                    })
        
        # Calculer les métriques globales
        total_daily_impact = sum(item.get('daily_impact_eur', 0) for item in bi_summary)
        total_annual_impact = total_daily_impact * 365 if total_daily_impact > 0 else 0
        sole_suppliers_count = sum(1 for item in bi_summary if item.get('is_sole_supplier'))
        critical_entities = [item for item in bi_summary if item.get('risk_score', 0) >= 70]
        
        # Identifier les entités les plus critiques (top 5)
        top_entities = sorted(bi_summary, key=lambda x: x.get('daily_impact_eur', 0), reverse=True)[:5]
        
        prompt = f"""Tu es un expert senior en gestion des risques supply chain pour Hutchinson (équipementier automobile/aéronautique).

Tu dois produire un RAPPORT D'ANALYSE COMPLET ET DÉTAILLÉ pour aider les décideurs à comprendre l'impact d'un événement.

═══════════════════════════════════════════════════════════════════════════════
📋 ÉVÉNEMENT ANALYSÉ
═══════════════════════════════════════════════════════════════════════════════

TYPE: {event_type.upper()}
SOUS-TYPE: {event_subtype or 'N/A'}
TITRE: {event_title}

DESCRIPTION:
{event_content}

═══════════════════════════════════════════════════════════════════════════════
📊 IMPACT MESURÉ SUR HUTCHINSON
═══════════════════════════════════════════════════════════════════════════════

ENTITÉS AFFECTÉES:
- Sites Hutchinson: {len(affected_sites)}
- Fournisseurs: {len(affected_suppliers)}
- Fournisseurs UNIQUES (sole suppliers): {sole_suppliers_count}
- Entités CRITIQUES (score ≥ 70): {len(critical_entities)}

IMPACT FINANCIER ESTIMÉ:
- Impact quotidien: {total_daily_impact:,.0f}€/jour
- Impact annuel projeté: {total_annual_impact:,.0f}€/an

TOP 5 ENTITÉS LES PLUS IMPACTÉES:
{json.dumps(top_entities, indent=2, ensure_ascii=False)}

RISQUES MÉTÉO (si applicable):
- Entités avec alertes: {weather_risk_summary.get('entities_with_alerts', 0) if weather_risk_summary else 0}
- Alertes totales: {weather_risk_summary.get('total_alerts', 0) if weather_risk_summary else 0}

═══════════════════════════════════════════════════════════════════════════════
🎯 TON OBJECTIF - 7 SECTIONS OBLIGATOIRES
═══════════════════════════════════════════════════════════════════════════════

GÉNÈRE un rapport structuré en 7 sections :

1. CONTEXTE ET ENJEUX : Explique l'événement en langage clair et ses implications pour Hutchinson
2. ENTITÉS AFFECTÉES (liste complète, pas de troncature)
3. ANALYSE FINANCIÈRE DÉTAILLÉE (impacts directs + coûts de mitigation + ROI)
4. RECOMMANDATIONS PRIORITAIRES (actionnables avec budget et ROI)
5. TIMELINE DES ACTIONS (vue chronologique)
6. MATRICE DE PRIORISATION (impact × urgence)
7. SCÉNARIO "NE RIEN FAIRE" (conséquences de l'inaction)

CONSIGNES CRITIQUES:
- LISTER TOUTES les entités (pas de "... et X autres")
- CHIFFRER tous les impacts en euros
- DÉTAILLER chaque recommandation (actions concrètes étape par étape)
- CALCULER le ROI de chaque action
- NOMMER des responsables suggérés
- DÉCRIRE le scénario d'inaction sur 3 horizons temporels

RÉPONDS UNIQUEMENT EN JSON:
{{
  "context_and_stakes": "Contexte et enjeux en langage clair (3-5 paragraphes)",
  "affected_entities_details": "Liste COMPLÈTE de toutes les entités avec détails (aucune troncature)",
  "financial_analysis": "Analyse financière détaillée (impacts + mitigation + ROI)",
  "recommendations": [
    {{
      "id": 1,
      "title": "Titre de l'action",
      "urgency": "IMMEDIATE|HIGH|MEDIUM|LOW",
      "timeline": "30 jours",
      "owner": "Directeur Achats",
      "budget_eur": 590000,
      "context": "Contexte et justification",
      "risk_if_no_action": "Risque si on ne fait rien",
      "concrete_actions": "Actions étape par étape",
      "expected_impact": "Impact attendu",
      "roi": "6.9x",
      "priority_score": 95
    }}
  ],
  "timeline": "Timeline visuelle des actions (semaine 1-2, mois 1, etc.)",
  "prioritization_matrix": "Matrice de priorisation impact×urgence",
  "do_nothing_scenario": "Scénario inaction (court/moyen/long terme)"
}}
"""
        return prompt
    
    def _generate_fallback_recommendations(
        self,
        document: Dict,
        affected_sites: List[Dict],
        affected_suppliers: List[Dict],
        criticality_results: Dict,
        weather_risk_summary: Dict = None
    ) -> List[Dict]:
        """
        Génère des recommandations templates (fallback si LLM non disponible)
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
        risk_score: float,
        business_impact: Dict = None,
        supplier_relationships: List[Dict] = None,
        sites: List[Dict] = None
    ) -> str:
        """
        Génère un raisonnement pour expliquer le score de risque d'une entité
        
        AMÉLIORÉ: Utilise le LLM pour analyse en cascade si disponible
        
        Returns:
            Texte explicatif
        """
        event_type = document.get('event_type')
        entity_name = entity.get('name')
        
        # Si LLM disponible et données BI présentes, faire analyse en cascade
        if self.llm_reasoning.llm_available and business_impact:
            try:
                # Préparer le contexte enrichi pour le LLM
                context = self._prepare_llm_context(
                    entity, entity_type, business_impact, 
                    supplier_relationships or [], sites or []
                )
                
                # Appeler le LLM pour analyse en cascade
                llm_result = self.llm_reasoning.analyze_cascade_impact(
                    event=document,
                    affected_entity=entity,
                    entity_type=entity_type,
                    relationships=supplier_relationships or [],
                    context=context
                )
                
                # Construire le raisonnement à partir de la réponse LLM
                return self._format_llm_reasoning(llm_result, entity_name, risk_score)
                
            except Exception as e:
                print(f"⚠️ LLM reasoning failed, using fallback: {e}")
        
        # Fallback : raisonnement template
        return self._generate_fallback_reasoning(document, entity, entity_type, risk_score, business_impact)
    
    def _prepare_llm_context(
        self,
        entity: Dict,
        entity_type: str,
        business_impact: Dict,
        supplier_relationships: List[Dict],
        sites: List[Dict]
    ) -> Dict:
        """
        Prépare le contexte enrichi avec les données BI pour le LLM
        """
        context = {
            # Données Business Interruption
            "total_daily_impact_eur": business_impact.get("total_daily_impact_eur", 0),
            "daily_revenue_loss_eur": business_impact.get("daily_revenue_loss_eur", 0),
            "customer_penalties_per_day_eur": business_impact.get("customer_penalties_per_day_eur", 0),
            "stock_coverage_days": business_impact.get("stock_coverage_days", 0),
            "switch_time_days": business_impact.get("switch_time_days", 0),
            "is_sole_supplier": business_impact.get("is_sole_supplier", False),
            "affected_customers": business_impact.get("affected_customers", []),
        }
        
        if entity_type == "supplier":
            # Ajouter les sites impactés en aval
            context["affected_sites"] = business_impact.get("affected_sites", [])
            context["criticality_score"] = entity.get("criticality_score", 5)
        else:
            # Pour un site, ajouter le recovery time
            context["recovery_time_days"] = business_impact.get("recovery_time_days", 7)
            context["daily_production_units"] = entity.get("daily_production_units", 0)
        
        return context
    
    def _format_llm_reasoning(self, llm_result: Dict, entity_name: str, risk_score: float) -> str:
        """
        Formate la réponse du LLM en texte de raisonnement
        """
        if not llm_result:
            return f"Score de risque: {risk_score:.1f}/100"
        
        reasoning_parts = []
        
        # Niveau de risque global
        risk_level = llm_result.get("overall_risk_level", "MOYEN")
        reasoning_parts.append(f"🎯 NIVEAU DE RISQUE: {risk_level} (Score: {risk_score:.1f}/100)")
        
        # Analyse d'impact
        impact = llm_result.get("impact_assessment") or {}
        if impact:
            prob = impact.get("impact_probability", 0) or 0
            duration = impact.get("estimated_impact_duration_days", 0) or 0
            reasoning_parts.append(f"\n📊 PROBABILITÉ D'IMPACT: {prob*100:.0f}%")
            reasoning_parts.append(f"⏱️ DURÉE ESTIMÉE: {duration} jours")
        
        # Analyse en cascade
        cascade = impact.get("cascade_analysis") or {}
        if cascade:
            days_until = cascade.get("days_until_disruption", 0)
            downstream = cascade.get("affected_downstream_entities", [])
            financial = cascade.get("financial_impact_estimate_eur", 0)
            
            reasoning_parts.append(f"\n🔗 ANALYSE EN CASCADE:")
            reasoning_parts.append(f"   - Délai avant disruption: {days_until} jours")
            if downstream:
                reasoning_parts.append(f"   - Entités impactées en aval: {', '.join(downstream[:5])}")
            if financial:
                reasoning_parts.append(f"   - Impact financier estimé: {financial:,.0f}€")
            
            prod_impact = cascade.get("production_impact", "")
            if prod_impact:
                reasoning_parts.append(f"   - Impact production: {prod_impact}")
            
            customer_impact = cascade.get("customer_impact", "")
            if customer_impact:
                reasoning_parts.append(f"   - Impact clients: {customer_impact}")
        
        # Raisonnement LLM
        llm_reasoning = llm_result.get("risk_reasoning", "")
        if llm_reasoning:
            reasoning_parts.append(f"\n💡 ANALYSE: {llm_reasoning}")
        
        return "\n".join(reasoning_parts)
    
    def _generate_fallback_reasoning(
        self,
        document: Dict,
        entity: Dict,
        entity_type: str,
        risk_score: float,
        business_impact: Dict = None
    ) -> str:
        """
        Génère un raisonnement template (fallback si LLM non disponible)
        """
        event_type = document.get('event_type')
        entity_name = entity.get('name')
        
        reasoning = ""
        
        if event_type == "climatique":
            reasoning = f"{entity_name} est concerné par l'événement climatique en raison de sa proximité géographique."
        elif event_type == "reglementaire":
            reasoning = f"{entity_name} est concerné par la réglementation en raison de son secteur d'activité et/ou produits."
        elif event_type == "geopolitique":
            reasoning = f"{entity_name} est concerné par l'événement géopolitique en raison de sa localisation dans un pays affecté."
        else:
            reasoning = f"{entity_name} est potentiellement concerné par l'événement."
        
        reasoning += f" Score de risque : {risk_score:.1f}/100."
        
        # Ajouter les données BI si disponibles
        if business_impact:
            total_impact = business_impact.get("total_daily_impact_eur", 0)
            if total_impact > 0:
                reasoning += f"\n💰 Impact financier estimé: {total_impact:,.0f}€/jour"
            
            if business_impact.get("is_sole_supplier"):
                reasoning += "\n⚠️ ATTENTION: Fournisseur unique - risque critique de rupture supply chain"
        
        return reasoning
    
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
    
    def run(self, validation_status: str = "approved", limit: int = 10) -> Dict:
        """
        Méthode principale pour exécuter l'Agent 2 sur les documents pertinents.
        
        Cette méthode est appelée par l'API pour traiter les documents ayant passé
        le filtre de pertinence (Agent 1B).
        
        Args:
            validation_status: Statut de validation requis (par défaut "approved")
            limit: Nombre maximum de documents à traiter
            
        Returns:
            Dict avec les résultats de l'analyse
        """
        from src.storage.database import get_session
        from src.storage.models import (
            Document, PertinenceCheck, HutchinsonSite, Supplier, 
            SupplierRelationship, RiskAnalysis
        )
        import structlog
        
        logger = structlog.get_logger()
        session = get_session()
        
        try:
            # Charger les sites et fournisseurs
            sites_db = session.query(HutchinsonSite).filter_by(active=True).all()
            suppliers_db = session.query(Supplier).filter_by(active=True).all()
            relationships_db = session.query(SupplierRelationship).all()
            
            sites = [
                {
                    "id": s.id,
                    "name": s.name,
                    "country": s.country,
                    "city": s.city,
                    "latitude": s.latitude,
                    "longitude": s.longitude,
                    "strategic_importance": s.strategic_importance,
                    "revenue_percentage": getattr(s, 'revenue_percentage', 5.0),
                    "employees_count": getattr(s, 'employees_count', 100),
                }
                for s in sites_db
            ]
            
            suppliers = [
                {
                    "id": s.id,
                    "name": s.name,
                    "country": s.country,
                    "city": getattr(s, 'city', None),
                    "latitude": s.latitude,
                    "longitude": s.longitude,
                    "is_sole_supplier": getattr(s, 'is_sole_supplier', False),
                    "strategic_importance": getattr(s, 'strategic_importance', 'moyen'),
                }
                for s in suppliers_db
            ]
            
            supplier_relationships = [
                {
                    "id": r.id,
                    "site_id": r.hutchinson_site_id,
                    "supplier_id": r.supplier_id,
                    "dependency_score": r.criticality,
                }
                for r in relationships_db
            ]
            
            # Récupérer les documents pertinents (OUI ou PARTIELLEMENT)
            pertinent_checks = (
                session.query(PertinenceCheck, Document)
                .join(Document, PertinenceCheck.document_id == Document.id)
                .filter(PertinenceCheck.decision.in_(['OUI', 'PARTIELLEMENT']))
                .limit(limit)
                .all()
            )
            
            logger.info(
                "agent2_run_started",
                pertinent_count=len(pertinent_checks),
                sites_count=len(sites),
                suppliers_count=len(suppliers)
            )
            
            results = []
            
            for check, doc in pertinent_checks:
                # Vérifier si déjà analysé
                existing_analysis = session.query(RiskAnalysis).filter_by(
                    document_id=doc.id
                ).first()
                
                if existing_analysis:
                    logger.info("document_already_analyzed", doc_id=doc.id[:8])
                    continue
                
                # Préparer le document
                document_dict = {
                    "id": doc.id,
                    "title": doc.title,
                    "content": doc.content,
                    "summary": doc.summary,
                    "event_type": doc.event_type,
                    "source_url": doc.source_url,
                    "geographic_scope": doc.geographic_scope,
                    "extra_metadata": doc.extra_metadata,
                }
                
                # Préparer le résultat de pertinence
                pertinence_result = {
                    "decision": check.decision,
                    "confidence": check.confidence,
                    "reasoning": check.reasoning,
                    "affected_sites": check.affected_sites or [],
                    "affected_suppliers": check.affected_suppliers or [],
                }
                
                logger.info(
                    "agent2_analyzing",
                    doc_id=doc.id[:8],
                    title=doc.title[:50] if doc.title else "N/A"
                )
                
                # Analyser avec Agent 2
                try:
                    risk_analysis, risk_projections = self.analyze(
                        document=document_dict,
                        pertinence_result=pertinence_result,
                        sites=sites,
                        suppliers=suppliers,
                        supplier_relationships=supplier_relationships
                    )
                    
                    # Sauvegarder en BDD
                    new_analysis = RiskAnalysis(
                        id=str(uuid.uuid4()),
                        document_id=doc.id,
                        pertinence_check_id=check.id,
                        impacts_description=risk_analysis.get("impacts_description", ""),
                        affected_sites=risk_analysis.get("affected_sites", []),
                        affected_suppliers=risk_analysis.get("affected_suppliers", []),
                        geographic_analysis=risk_analysis.get("geographic_analysis"),
                        criticality_analysis=risk_analysis.get("criticality_analysis"),
                        risk_level=risk_analysis.get("overall_risk_level", "Moyen"),
                        risk_score=risk_analysis.get("risk_score", 50.0),
                        supply_chain_impact=risk_analysis.get("supply_chain_impact", "moyen"),
                        recommendations=json.dumps(risk_analysis.get("recommendations", [])),
                        reasoning=risk_analysis.get("reasoning", ""),
                        llm_model=risk_analysis.get("llm_model", "unknown"),
                        llm_tokens=risk_analysis.get("llm_tokens", 0),
                        processing_time_ms=risk_analysis.get("processing_time_ms", 0),
                        # Note: severity_score, probability_score, exposure_score, urgency_score, 
                        # risk_score_360, business_interruption_score stockés dans analysis_metadata
                        analysis_metadata={
                            "severity_score": risk_analysis.get("severity_score"),
                            "probability_score": risk_analysis.get("probability_score"),
                            "exposure_score": risk_analysis.get("exposure_score"),
                            "urgency_score": risk_analysis.get("urgency_score"),
                            "risk_score_360": risk_analysis.get("risk_score_360"),
                            "business_interruption_score": risk_analysis.get("business_interruption_score"),
                            "weather_risk_summary": risk_analysis.get("weather_risk_summary"),
                        },
                        context_and_stakes=risk_analysis.get("context_and_stakes"),
                        affected_entities_details=risk_analysis.get("affected_entities_details"),
                        financial_analysis=risk_analysis.get("financial_analysis"),
                        timeline=risk_analysis.get("timeline"),
                        prioritization_matrix=risk_analysis.get("prioritization_matrix"),
                        do_nothing_scenario=risk_analysis.get("do_nothing_scenario"),
                        recommendations_model=risk_analysis.get("recommendations_model"),
                    )
                    
                    session.add(new_analysis)
                    session.commit()
                    
                    results.append({
                        "document_id": doc.id,
                        "risk_level": risk_analysis.get("overall_risk_level"),
                        "risk_score": risk_analysis.get("risk_score"),
                    })
                    
                    logger.info(
                        "agent2_analysis_saved",
                        doc_id=doc.id[:8],
                        risk_level=risk_analysis.get("overall_risk_level"),
                        risk_score=risk_analysis.get("risk_score")
                    )
                    
                except Exception as e:
                    logger.error(
                        "agent2_analysis_failed",
                        doc_id=doc.id[:8],
                        error=str(e)
                    )
                    continue
            
            return {
                "status": "completed",
                "documents_analyzed": len(results),
                "results": results,
                "messages": [{"content": f"Agent 2 a analysé {len(results)} documents"}]
            }
            
        finally:
            session.close()
