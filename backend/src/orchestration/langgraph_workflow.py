"""
Orchestration LangGraph - Pipeline PING

Workflow conforme au diagramme :
START → Agent 1A → Agent 1B → [OUI/PARTIELLEMENT] → Agent 2 → LLM Judge → [Décision]
                            → [NON] → END

Décisions du Judge:
- Score >= 8.5 → APPROVE (Notification Immédiate)
- Score 7.0-8.4 → REVIEW (Validation Humaine requise)
- Score < 7.0 → REJECT (Archiver)
"""

# Charger les variables d'environnement en premier
from dotenv import load_dotenv
load_dotenv()

import asyncio
import structlog
from typing import Dict, List, TypedDict, Optional, Literal
from datetime import datetime

from langgraph.graph import StateGraph, END

# Imports des agents
from src.agent_1a.agent import run_agent_1a
from src.agent_1a.tools.weather import OpenMeteoClient, Location
from src.agent_1b.agent import Agent1B
from src.agent_2.agent import Agent2
from src.llm_judge.judge import Judge

# Import notifications
from src.notifications.notification_service import NotificationService

# Imports storage
from src.storage.database import get_session
from src.storage.models import (
    Document, 
    PertinenceCheck, 
    RiskAnalysis, 
    JudgeEvaluation,
    Alert,
    HutchinsonSite,
    Supplier,
    SupplierRelationship,
    CompanyProfile,
    ExecutionLog,
    RiskProjection,
    WeatherAlert
)

logger = structlog.get_logger()


# ============================================================================
# EXECUTION LOGGING HELPER
# ============================================================================

def log_execution(
    agent_name: str,
    status: str,
    document_id: str = None,
    execution_time_ms: int = None,
    error_message: str = None,
    extra_metadata: Dict = None
) -> str:
    """
    Sauvegarde un log d'exécution dans la table execution_logs
    
    Args:
        agent_name: Nom de l'agent (agent_1a, agent_1b, agent_2, judge)
        status: success, error, warning
        document_id: ID du document traité (optionnel)
        execution_time_ms: Temps d'exécution en ms
        error_message: Message d'erreur si échec
        extra_metadata: Données supplémentaires (JSON)
        
    Returns:
        ID du log créé
    """
    session = get_session()
    try:
        log_entry = ExecutionLog(
            agent_name=agent_name,
            document_id=document_id,
            status=status,
            execution_time_ms=execution_time_ms,
            error_message=error_message,
            extra_metadata=extra_metadata
        )
        session.add(log_entry)
        session.commit()
        log_id = log_entry.id
        logger.info("execution_log_saved", agent=agent_name, status=status, log_id=log_id)
        return log_id
    except Exception as e:
        session.rollback()
        logger.error("execution_log_save_error", error=str(e))
        return None
    finally:
        session.close()


# ============================================================================
# WEATHER COLLECTION HELPER
# ============================================================================

async def collect_weather_alerts(forecast_days: int = 16) -> Dict:
    """
    Collecte les alertes météo pour tous les sites (Hutchinson + Fournisseurs) depuis la BDD.
    
    Args:
        forecast_days: Nombre de jours de prévisions (max 16)
        
    Returns:
        dict: Statistiques de collecte (alerts_saved, sites_processed, etc.)
    """
    logger.info("collect_weather_alerts_started", forecast_days=forecast_days)
    
    session = get_session()
    weather_client = OpenMeteoClient(forecast_days=forecast_days)
    
    all_sites = []
    alerts_saved = 0
    sites_processed = 0
    errors = []
    
    try:
        # Charger les sites Hutchinson depuis la BDD
        hutchinson_sites = session.query(HutchinsonSite).filter(HutchinsonSite.active == True).all()
        for site in hutchinson_sites:
            if site.latitude and site.longitude:
                all_sites.append({
                    "site_id": site.id,
                    "name": site.name,
                    "city": site.city,
                    "country": site.country,
                    "latitude": site.latitude,
                    "longitude": site.longitude,
                    "site_type": "manufacturing",
                    "criticality": site.strategic_importance or "normal"
                })
        
        # Charger les fournisseurs depuis la BDD
        suppliers = session.query(Supplier).filter(Supplier.active == True).all()
        for supplier in suppliers:
            if supplier.latitude and supplier.longitude:
                all_sites.append({
                    "site_id": supplier.id,
                    "name": supplier.name,
                    "city": supplier.city,
                    "country": supplier.country,
                    "latitude": supplier.latitude,
                    "longitude": supplier.longitude,
                    "site_type": "supplier",
                    "criticality": "normal"
                })
        
        logger.info("weather_sites_loaded", 
                    hutchinson=len(hutchinson_sites), 
                    suppliers=len(suppliers),
                    total_with_coords=len(all_sites))
        
        # Collecter la météo pour chaque site
        for site in all_sites:
            try:
                location = Location(
                    site_id=site["site_id"],
                    name=site["name"],
                    city=site["city"],
                    country=site["country"],
                    latitude=site["latitude"],
                    longitude=site["longitude"],
                    site_type=site["site_type"],
                    criticality=site["criticality"]
                )
                
                # Récupérer les prévisions
                forecast = await weather_client.get_forecast(location)
                sites_processed += 1
                
                if forecast:
                    # Détecter les alertes
                    alerts = weather_client.detect_alerts(forecast)
                    
                    for alert in alerts:
                        try:
                            # Créer l'alerte en BDD
                            weather_alert = WeatherAlert(
                                site_id=alert.location.site_id,
                                site_name=alert.location.name,
                                city=alert.location.city,
                                country=alert.location.country,
                                latitude=alert.location.latitude,
                                longitude=alert.location.longitude,
                                site_type=alert.location.site_type,
                                site_criticality=alert.location.criticality,
                                alert_type=alert.alert_type,
                                severity=alert.severity,
                                alert_date=alert.date,
                                value=alert.value,
                                threshold=alert.threshold,
                                unit=alert.unit,
                                description=alert.description,
                                supply_chain_risk=alert.supply_chain_risk,
                                status="new"
                            )
                            session.add(weather_alert)
                            alerts_saved += 1
                        except Exception as e:
                            errors.append(f"Alert save error for {site['name']}: {str(e)}")
                            
            except Exception as e:
                errors.append(f"Weather fetch error for {site['name']}: {str(e)}")
                logger.warning("weather_fetch_error", site=site["name"], error=str(e))
        
        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error("collect_weather_alerts_failed", error=str(e))
        return {"status": "error", "error": str(e)}
    finally:
        session.close()
    
    result = {
        "status": "success",
        "sites_total": len(all_sites),
        "sites_processed": sites_processed,
        "alerts_saved": alerts_saved,
        "errors": len(errors)
    }
    
    logger.info("collect_weather_alerts_completed", **result)
    return result


# ============================================================================
# STATE DEFINITION
# ============================================================================

class PINGState(TypedDict):
    """État partagé du workflow PING"""
    # Configuration
    keyword: str
    max_documents: int
    company_name: str
    
    # Résultats Agent 1A
    agent_1a_result: Optional[Dict]
    documents_collected: List[Dict]
    
    # Résultats Agent 1B (par document)
    pertinence_results: List[Dict]
    documents_pertinent: List[Dict]  # OUI ou PARTIELLEMENT
    documents_non_pertinent: List[Dict]  # NON
    
    # Résultats Agent 2 (par document pertinent)
    risk_analyses: List[Dict]
    
    # Résultats LLM Judge
    judge_evaluations: List[Dict]
    
    # Décisions finales
    approved: List[Dict]  # Score >= 8.5
    needs_review: List[Dict]  # Score 7.0-8.4
    rejected: List[Dict]  # Score < 7.0
    
    # Notifications
    notifications_sent: List[Dict]  # Notifications envoyées
    notifications_skipped: List[Dict]  # Notifications ignorées (rejected)
    
    # Métadonnées
    company_profile: Optional[Dict]
    sites: List[Dict]
    suppliers: List[Dict]
    supplier_relationships: List[Dict]
    errors: List[str]
    current_step: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_company_data(company_name: str) -> Dict:
    """Charge le profil entreprise et les données associées depuis la BDD"""
    session = get_session()
    
    try:
        # Charger le profil entreprise
        profile = session.query(CompanyProfile).filter(
            CompanyProfile.company_name.ilike(f"%{company_name}%")
        ).first()
        
        if not profile:
            raise ValueError(f"Profil entreprise '{company_name}' non trouvé en BDD")
        
        # Charger les sites
        sites = session.query(HutchinsonSite).filter(
            HutchinsonSite.active == True
        ).all()
        
        # Charger les fournisseurs
        suppliers = session.query(Supplier).filter(
            Supplier.active == True
        ).all()
        
        # Charger les relations
        relationships = session.query(SupplierRelationship).all()
        
        return {
            "company_profile": {
                "id": profile.id,
                "company_name": profile.company_name,
                "headquarters_country": profile.headquarters_country,
                "risk_tolerance": profile.risk_tolerance,
                "notification_settings": profile.notification_settings or {},
                "data_sources_config": profile.data_sources_config or {},
                "llm_config": profile.llm_config or {}
            },
            "sites": [
                {
                    "id": s.id,
                    "site_id": s.code,
                    "name": s.name,  # L'Agent 2 attend 'name'
                    "site_name": s.name,
                    "city": s.city,
                    "country": s.country,
                    "latitude": s.latitude,
                    "longitude": s.longitude,
                    "site_type": s.sectors[0] if s.sectors else None,
                    "strategic_importance": s.strategic_importance,
                    # Business Interruption data
                    "daily_revenue": s.daily_revenue,
                    "daily_production_units": s.daily_production_units,
                    "safety_stock_days": s.safety_stock_days,
                    "recovery_time_days": s.ramp_up_time_days,  # ramp_up_time_days dans le modèle
                    "key_customers": s.key_customers or []
                }
                for s in sites
            ],
            "suppliers": [
                {
                    "id": s.id,
                    "supplier_id": s.code,
                    "name": s.name,  # L'Agent 2 attend 'name'
                    "company_name": s.name,
                    "country": s.country,
                    "city": s.city,
                    "latitude": s.latitude,
                    "longitude": s.longitude,
                    "criticality": s.financial_health,
                    # Business Interruption data
                    "annual_purchase_volume": s.annual_purchase_volume,
                    "average_stock_at_hutchinson_days": s.average_stock_at_hutchinson_days,
                    "switch_time_days": s.switch_time_days,
                    "criticality_score": s.criticality_score,
                    "alternative_supplier_id": s.alternative_supplier_id,
                    "ramp_up_time_days": s.qualification_time_days  # qualification_time_days dans le modèle
                }
                for s in suppliers
            ],
            "supplier_relationships": [
                {
                    "id": r.id,
                    "hutchinson_site_id": r.hutchinson_site_id,
                    "supplier_id": r.supplier_id,
                    "relationship_type": "supplier",
                    "criticality": r.criticality,
                    # Business Interruption data
                    "daily_consumption_value": r.daily_consumption_value,
                    "stock_coverage_days": r.stock_coverage_days,
                    "contract_penalties_per_day": r.contract_penalties_per_day,
                    "is_sole_supplier": r.is_sole_supplier
                }
                for r in relationships
            ]
        }
    finally:
        session.close()


def get_unanalyzed_documents() -> List[Dict]:
    """Récupère les documents non encore analysés par Agent 1B"""
    session = get_session()
    
    try:
        docs = session.query(Document).outerjoin(
            PertinenceCheck,
            Document.id == PertinenceCheck.document_id
        ).filter(
            PertinenceCheck.id.is_(None)
        ).all()
        
        return [
            {
                "id": d.id,
                "title": d.title,
                "source_url": d.source_url,
                "event_type": d.event_type,
                "event_subtype": d.event_subtype,
                "content": d.content,
                "extra_metadata": d.extra_metadata or {}
            }
            for d in docs
        ]
    finally:
        session.close()


def save_risk_analysis(document: Dict, pertinence_result: Dict, risk_analysis: Dict) -> str:
    """Sauvegarde l'analyse de risque (Agent 2) en BDD"""
    import json
    session = get_session()
    
    try:
        # ========================================
        # 1. GÉNÉRER LE RAPPORT D'IMPACTS (texte complet)
        # ========================================
        doc_title = document.get("title", "Document réglementaire")[:100]
        event_type = document.get("event_type", "reglementaire")
        
        affected_sites = risk_analysis.get("affected_sites", [])
        affected_suppliers = risk_analysis.get("affected_suppliers", [])
        weather_summary = risk_analysis.get("weather_risk_summary", {})
        
        # Construire le rapport d'impacts
        impacts_lines = []
        impacts_lines.append("=" * 60)
        impacts_lines.append("RAPPORT D'ANALYSE D'IMPACT - AGENT 2")
        impacts_lines.append("=" * 60)
        impacts_lines.append("")
        impacts_lines.append(f"Document analysé: {doc_title}")
        impacts_lines.append(f"Type d'événement: {event_type}")
        impacts_lines.append(f"Date d'analyse: {risk_analysis.get('analysis_timestamp', 'N/A')}")
        impacts_lines.append("")
        
        # Section Risque Global
        impacts_lines.append("-" * 40)
        impacts_lines.append("1. ÉVALUATION DU RISQUE GLOBAL")
        impacts_lines.append("-" * 40)
        impacts_lines.append(f"   Niveau de risque: {risk_analysis.get('overall_risk_level', 'N/A')}")
        impacts_lines.append(f"   Score de risque 360°: {risk_analysis.get('risk_score_360', 0)}/100")
        impacts_lines.append(f"   Score de sévérité: {risk_analysis.get('severity_score', 0)}/100")
        impacts_lines.append(f"   Score d'urgence: {risk_analysis.get('urgency_score', 0)}/100")
        impacts_lines.append(f"   Score d'interruption business: {risk_analysis.get('business_interruption_score', 0)}/100")
        impacts_lines.append(f"   Jours de perturbation estimés: {risk_analysis.get('estimated_disruption_days', 0)}")
        impacts_lines.append(f"   Impact sur le chiffre d'affaires: {risk_analysis.get('revenue_impact_percentage', 0)}%")
        impacts_lines.append("")
        
        # Section Sites Affectés
        impacts_lines.append("-" * 40)
        impacts_lines.append(f"2. SITES HUTCHINSON AFFECTÉS ({len(affected_sites)})")
        impacts_lines.append("-" * 40)
        if affected_sites:
            for site in affected_sites[:10]:  # Max 10 sites
                site_name = site.get('name', 'Site inconnu')
                site_score = site.get('risk_score', 0)
                site_bi = site.get('business_interruption_score', 0)
                site_reasoning = site.get('reasoning', '')[:200]
                impacts_lines.append(f"   • {site_name}")
                impacts_lines.append(f"     - Score de risque: {site_score}/100")
                impacts_lines.append(f"     - Score interruption: {site_bi}/100")
                impacts_lines.append(f"     - Analyse: {site_reasoning}...")
                impacts_lines.append("")
        else:
            impacts_lines.append("   Aucun site directement affecté.")
        impacts_lines.append("")
        
        # Section Fournisseurs Affectés
        impacts_lines.append("-" * 40)
        impacts_lines.append(f"3. FOURNISSEURS AFFECTÉS ({len(affected_suppliers)})")
        impacts_lines.append("-" * 40)
        if affected_suppliers:
            for supplier in affected_suppliers[:10]:  # Max 10 fournisseurs
                supplier_name = supplier.get('name', 'Fournisseur inconnu')
                supplier_score = supplier.get('risk_score', 0)
                supplier_bi = supplier.get('business_interruption_score', 0)
                supplier_reasoning = supplier.get('reasoning', '')[:200]
                impacts_lines.append(f"   • {supplier_name}")
                impacts_lines.append(f"     - Score de risque: {supplier_score}/100")
                impacts_lines.append(f"     - Score interruption: {supplier_bi}/100")
                impacts_lines.append(f"     - Analyse: {supplier_reasoning}...")
                impacts_lines.append("")
        else:
            impacts_lines.append("   Aucun fournisseur directement affecté.")
        impacts_lines.append("")
        
        # Section Risque Climatique
        impacts_lines.append("-" * 40)
        impacts_lines.append("4. ANALYSE DES RISQUES CLIMATIQUES (Open-Meteo)")
        impacts_lines.append("-" * 40)
        if weather_summary and weather_summary.get("total_alerts", 0) > 0:
            impacts_lines.append(f"   Total alertes météo actives: {weather_summary.get('total_alerts', 0)}")
            impacts_lines.append(f"   Entités avec alertes: {weather_summary.get('entities_with_alerts', 0)}")
            impacts_lines.append(f"   Sévérité maximale: {weather_summary.get('max_severity', 'N/A')}")
            impacts_lines.append(f"   Score de risque météo moyen: {weather_summary.get('average_weather_risk_score', 0)}/100")
            
            alerts_by_type = weather_summary.get("alerts_by_type", {})
            if alerts_by_type:
                impacts_lines.append("   Répartition des alertes:")
                for alert_type, count in alerts_by_type.items():
                    alert_label = {
                        'extreme_heat': 'Canicule',
                        'extreme_cold': 'Grand froid',
                        'strong_wind': 'Vents forts',
                        'heavy_rain': 'Fortes pluies',
                        'snow': 'Neige',
                        'storm': 'Tempête'
                    }.get(alert_type, alert_type)
                    impacts_lines.append(f"     - {alert_label}: {count} alerte(s)")
            
            # Entités à risque météo
            entities_at_risk = weather_summary.get("entities_at_risk", [])
            if entities_at_risk:
                impacts_lines.append("")
                impacts_lines.append("   Entités les plus exposées aux risques climatiques:")
                for entity in entities_at_risk[:5]:
                    impacts_lines.append(f"     - {entity.get('entity_name')}: {entity.get('alerts_count')} alerte(s), sévérité {entity.get('max_severity')}")
        else:
            impacts_lines.append("   Aucune alerte météo significative détectée.")
        impacts_lines.append("")
        
        # Section Criticité
        criticality = risk_analysis.get("criticality_analysis", {})
        impacts_lines.append("-" * 40)
        impacts_lines.append("5. ANALYSE DE CRITICITÉ")
        impacts_lines.append("-" * 40)
        if isinstance(criticality, dict):
            summary = criticality.get("summary", {})
            if isinstance(summary, dict):
                impacts_lines.append(f"   Entités critiques: {summary.get('total_critical', 0)}")
                impacts_lines.append(f"   Entités à risque élevé: {summary.get('total_high', 0)}")
                impacts_lines.append(f"   Entités à risque moyen: {summary.get('total_medium', 0)}")
        impacts_lines.append("")
        impacts_lines.append("=" * 60)
        impacts_lines.append("FIN DU RAPPORT D'ANALYSE D'IMPACT")
        impacts_lines.append("=" * 60)
        
        impacts_description = "\n".join(impacts_lines)
        
        # ========================================
        # 2. CONSTRUIRE LE REASONING (synthèse)
        # ========================================
        reasoning_lines = []
        reasoning_lines.append(f"Analyse d'impact pour le document '{doc_title}'.")
        reasoning_lines.append("")
        reasoning_lines.append(f"SYNTHÈSE: Ce document de type '{event_type}' présente un niveau de risque {risk_analysis.get('overall_risk_level', 'N/A')} avec un score global de {risk_analysis.get('risk_score_360', 0)}/100.")
        reasoning_lines.append("")
        reasoning_lines.append(f"IMPACT OPÉRATIONNEL: {len(affected_sites)} site(s) et {len(affected_suppliers)} fournisseur(s) sont potentiellement affectés.")
        
        if weather_summary and weather_summary.get("total_alerts", 0) > 0:
            reasoning_lines.append("")
            reasoning_lines.append(f"RISQUE CLIMATIQUE AGGRAVANT: {weather_summary.get('total_alerts', 0)} alerte(s) météo actives sur {weather_summary.get('entities_with_alerts', 0)} entité(s) augmentent le niveau de risque global.")
        
        reasoning_lines.append("")
        reasoning_lines.append(f"INTERRUPTION ESTIMÉE: {risk_analysis.get('estimated_disruption_days', 0)} jour(s) de perturbation potentielle avec un impact estimé de {risk_analysis.get('revenue_impact_percentage', 0)}% sur le chiffre d'affaires.")
        
        reasoning = "\n".join(reasoning_lines)
        
        # ========================================
        # 3. RECOMMANDATIONS (texte complet)
        # ========================================
        recommendations = risk_analysis.get("recommendations", "")
        if isinstance(recommendations, dict):
            reco_text = json.dumps(recommendations, ensure_ascii=False, indent=2)
        elif isinstance(recommendations, list):
            reco_text = "\n\n".join([str(r) for r in recommendations])
        else:
            reco_text = str(recommendations)
        
        # ========================================
        # 4. METADATA avec données complètes
        # ========================================
        extra_data = {
            "risk_score_360": risk_analysis.get("risk_score_360"),
            "severity_score": risk_analysis.get("severity_score"),
            "probability_score": risk_analysis.get("probability_score"),
            "exposure_score": risk_analysis.get("exposure_score"),
            "urgency_score": risk_analysis.get("urgency_score"),
            "business_interruption_score": risk_analysis.get("business_interruption_score"),
            "estimated_disruption_days": risk_analysis.get("estimated_disruption_days"),
            "revenue_impact_percentage": risk_analysis.get("revenue_impact_percentage"),
            "weather_risk_summary": risk_analysis.get("weather_risk_summary", {}),
            "analysis_metadata": risk_analysis.get("analysis_metadata", {})
        }
        
        # ========================================
        # 5. SAUVEGARDER EN BDD
        # ========================================
        risk_record = RiskAnalysis(
            document_id=document.get("id"),
            pertinence_check_id=pertinence_result.get("check_id", pertinence_result.get("id")),
            impacts_description=impacts_description,
            affected_sites=json.dumps(risk_analysis.get("affected_sites", []), ensure_ascii=False),
            affected_suppliers=json.dumps(risk_analysis.get("affected_suppliers", []), ensure_ascii=False),
            geographic_analysis=json.dumps(risk_analysis.get("geographic_analysis"), ensure_ascii=False) if risk_analysis.get("geographic_analysis") else None,
            criticality_analysis=json.dumps(risk_analysis.get("criticality_analysis"), ensure_ascii=False) if risk_analysis.get("criticality_analysis") else None,
            risk_level=risk_analysis.get("overall_risk_level", "Moyen"),
            risk_score=risk_analysis.get("risk_score", 0.0),
            supply_chain_impact=_map_risk_level_to_impact(risk_analysis.get("overall_risk_level", "Moyen")),
            recommendations=reco_text,
            reasoning=reasoning,
            llm_model=risk_analysis.get("analysis_metadata", {}).get("llm_model", "gpt-4o"),
            llm_tokens=risk_analysis.get("analysis_metadata", {}).get("llm_tokens"),
            processing_time_ms=risk_analysis.get("analysis_metadata", {}).get("processing_time_ms"),
            analysis_metadata=json.dumps(extra_data, ensure_ascii=False)
        )
        
        session.add(risk_record)
        session.commit()
        
        logger.info("risk_analysis_saved", risk_id=risk_record.id, document_id=document.get("id"))
        return risk_record.id
    finally:
        session.close()


def _map_risk_level_to_impact(risk_level: str) -> str:
    """Convertit le niveau de risque en niveau d'impact supply chain"""
    mapping = {
        "Critique": "critique",
        "Fort": "fort",
        "Moyen": "moyen",
        "Faible": "faible",
        "Minimal": "aucun"
    }
    return mapping.get(risk_level, "moyen")


def save_risk_projections(document_id: str, risk_projections: List[Dict]) -> int:
    """
    Sauvegarde les projections de risque par entité dans la table risk_projections.
    
    Args:
        document_id: ID du document (event_id)
        risk_projections: Liste des projections retournées par Agent 2
        
    Returns:
        Nombre de projections sauvegardées
    """
    import json
    session = get_session()
    saved_count = 0
    
    try:
        for proj in risk_projections:
            # Ne sauvegarder que les entités concernées (is_concerned=True)
            # ou avec un score de risque > 0
            if not proj.get("is_concerned") and proj.get("risk_score", 0) == 0:
                continue
            
            projection_record = RiskProjection(
                event_id=document_id,
                entity_id=proj.get("entity_id", ""),
                entity_type=proj.get("entity_type", "site"),  # "site" ou "supplier"
                
                # Scores
                risk_score=proj.get("risk_score", 0.0),
                impact_score=proj.get("impact_score"),
                business_interruption_score=proj.get("business_interruption_score"),
                
                # Détails
                is_concerned=proj.get("is_concerned", False),
                reasoning=proj.get("reasoning", ""),
                estimated_disruption_days=proj.get("estimated_disruption_days"),
                revenue_impact_percentage=proj.get("revenue_impact_percentage"),
                
                # Sous-scores 360°
                severity_score=proj.get("severity_score"),
                probability_score=proj.get("probability_score"),
                exposure_score=proj.get("exposure_score"),
                urgency_score=proj.get("urgency_score"),
                
                # Métadonnées
                extra_metadata=json.dumps({
                    "entity_name": proj.get("entity_name", ""),
                    "country": proj.get("country", ""),
                    "city": proj.get("city", ""),
                    "weather_alerts": proj.get("weather_alerts", []),
                    "weather_risk_score": proj.get("weather_risk_score", 0)
                }, ensure_ascii=False) if proj else None
            )
            
            session.add(projection_record)
            saved_count += 1
        
        session.commit()
        logger.info(
            "risk_projections_saved", 
            document_id=document_id, 
            projections_count=saved_count
        )
        
        return saved_count
        
    except Exception as e:
        session.rollback()
        logger.error("save_risk_projections_error", error=str(e), document_id=document_id)
        raise
    finally:
        session.close()


def save_judge_evaluation(risk_analysis_id: str, evaluation: Dict) -> str:
    """Sauvegarde l'évaluation du Judge en BDD"""
    session = get_session()
    
    try:
        judge_eval = JudgeEvaluation(
            risk_analysis_id=risk_analysis_id,
            score_completeness=evaluation.get("pertinence_evaluation", {}).get("completeness", {}).get("score", 0),
            score_accuracy=evaluation.get("risk_evaluation", {}).get("accuracy", {}).get("score", 0),
            score_relevance=evaluation.get("pertinence_evaluation", {}).get("relevance", {}).get("score", 0),
            score_clarity=evaluation.get("risk_evaluation", {}).get("clarity", {}).get("score", 0),
            score_actionability=evaluation.get("risk_evaluation", {}).get("actionability", {}).get("score", 0),
            score_traceability=evaluation.get("risk_evaluation", {}).get("traceability", {}).get("score", 0),
            overall_score=evaluation.get("overall_score", 0),
            action=evaluation.get("action", "REVIEW"),
            reasoning=evaluation.get("reasoning", ""),
            improvement_suggestions=evaluation.get("improvement_suggestions", []),
            llm_model=evaluation.get("llm_model", "claude-sonnet-4-20250514"),
            llm_tokens=evaluation.get("llm_tokens"),
            processing_time_ms=evaluation.get("processing_time_ms")
        )
        
        session.add(judge_eval)
        session.commit()
        
        return judge_eval.id
    finally:
        session.close()


def create_alert(document: Dict, risk_analysis: Dict, judge_evaluation: Dict) -> str:
    """Crée une alerte pour les documents approuvés"""
    session = get_session()
    
    try:
        # Déterminer la sévérité selon le niveau de risque
        risk_level = risk_analysis.get("risk_level", "Moyen")
        if risk_level == "Critique":
            severity = "critical"
        elif risk_level == "Fort":
            severity = "high"
        elif risk_level == "Moyen":
            severity = "medium"
        else:
            severity = "low"
        
        alert = Alert(
            title=f"Alerte: {document.get('title', 'Document')[:450]}",
            description=risk_analysis.get("reasoning", "Analyse de risque générée automatiquement"),
            severity=severity,
            status="new",
            document_id=document.get("id"),
            risk_analysis_id=risk_analysis.get("id"),
            judge_evaluation_id=judge_evaluation.get("id"),
            recommendations=risk_analysis.get("recommendations", "Consulter l'analyse détaillée"),
            affected_sites=risk_analysis.get("affected_sites"),
            affected_suppliers=risk_analysis.get("affected_suppliers")
        )
        
        session.add(alert)
        session.commit()
        
        return alert.id
    finally:
        session.close()


# ============================================================================
# NODE FUNCTIONS
# ============================================================================

def node_agent_1a(state: PINGState) -> PINGState:
    """
    Node Agent 1A : Collecte des documents ET des alertes météo
    """
    import time
    start_time = time.time()
    logger.info("node_agent_1a_started", keyword=state["keyword"])
    state["current_step"] = "agent_1a"
    
    weather_result = {"alerts_saved": 0}
    
    try:
        # Exécuter Agent 1A (recherche EUR-Lex par mot-clé)
        result = asyncio.run(run_agent_1a(
            keyword=state["keyword"],
            max_documents=state["max_documents"]
        ))
        
        state["agent_1a_result"] = result
        
        # Récupérer les documents non analysés
        documents = get_unanalyzed_documents()
        state["documents_collected"] = documents
        
        # ====================================================================
        # COLLECTE MÉTÉO POUR TOUS LES SITES
        # ====================================================================
        logger.info("node_agent_1a_collecting_weather")
        try:
            weather_result = asyncio.run(collect_weather_alerts(forecast_days=16))
            logger.info("node_agent_1a_weather_completed", 
                       alerts_saved=weather_result.get("alerts_saved", 0),
                       sites_processed=weather_result.get("sites_processed", 0))
        except Exception as weather_error:
            logger.warning("node_agent_1a_weather_error", error=str(weather_error))
            weather_result = {"alerts_saved": 0, "error": str(weather_error)}
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # LOG D'EXÉCUTION
        log_execution(
            agent_name="agent_1a",
            status="success",
            execution_time_ms=execution_time_ms,
            extra_metadata={
                "keyword": state["keyword"],
                "documents_collected": len(documents),
                "documents_found": result.get("documents_found", 0),
                "total_available": result.get("total_available_on_eurlex", 0),
                "weather_alerts_saved": weather_result.get("alerts_saved", 0),
                "weather_sites_processed": weather_result.get("sites_processed", 0)
            }
        )
        
        logger.info(
            "node_agent_1a_completed",
            documents_collected=len(documents),
            weather_alerts_saved=weather_result.get("alerts_saved", 0),
            status=result.get("status")
        )
        
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        log_execution(
            agent_name="agent_1a",
            status="error",
            execution_time_ms=execution_time_ms,
            error_message=str(e)
        )
        logger.error("node_agent_1a_error", error=str(e))
        state["errors"].append(f"Agent 1A: {str(e)}")
    
    return state


def node_load_company_data(state: PINGState) -> PINGState:
    """
    Node intermédiaire : Charge les données entreprise
    """
    logger.info("node_load_company_data_started", company=state["company_name"])
    
    try:
        company_data = load_company_data(state["company_name"])
        
        state["company_profile"] = company_data["company_profile"]
        state["sites"] = company_data["sites"]
        state["suppliers"] = company_data["suppliers"]
        state["supplier_relationships"] = company_data["supplier_relationships"]
        
        logger.info(
            "node_load_company_data_completed",
            sites=len(state["sites"]),
            suppliers=len(state["suppliers"])
        )
        
    except Exception as e:
        logger.error("node_load_company_data_error", error=str(e))
        state["errors"].append(f"Load Company Data: {str(e)}")
    
    return state


def node_agent_1b(state: PINGState) -> PINGState:
    """
    Node Agent 1B : Analyse de pertinence pour chaque document
    """
    import time
    start_time = time.time()
    logger.info("node_agent_1b_started", documents_count=len(state["documents_collected"]))
    state["current_step"] = "agent_1b"
    
    agent_1b = Agent1B()
    pertinence_results = []
    documents_pertinent = []
    documents_non_pertinent = []
    
    for doc in state["documents_collected"]:
        doc_start_time = time.time()
        try:
            result = agent_1b.check_pertinence(doc["id"], save_to_db=True)
            
            pertinence_results.append({
                "document_id": doc["id"],
                "document": doc,
                "pertinence_result": result
            })
            
            decision = result.get("decision", "NON")
            
            # LOG D'EXÉCUTION pour chaque document
            doc_exec_time = int((time.time() - doc_start_time) * 1000)
            log_execution(
                agent_name="agent_1b",
                status="success",
                document_id=doc["id"],
                execution_time_ms=doc_exec_time,
                extra_metadata={
                    "decision": decision,
                    "confidence": result.get("confidence"),
                    "affected_sites": len(result.get("affected_sites", [])),
                    "affected_suppliers": len(result.get("affected_suppliers", []))
                }
            )
            
            if decision in ["OUI", "PARTIELLEMENT"]:
                documents_pertinent.append({
                    "document": doc,
                    "pertinence_result": result
                })
                logger.info(
                    "document_pertinent",
                    doc_id=doc["id"],
                    decision=decision,
                    confidence=result.get("confidence")
                )
            else:
                documents_non_pertinent.append({
                    "document": doc,
                    "pertinence_result": result
                })
                logger.info(
                    "document_non_pertinent",
                    doc_id=doc["id"],
                    decision=decision
                )
                
        except Exception as e:
            doc_exec_time = int((time.time() - doc_start_time) * 1000)
            log_execution(
                agent_name="agent_1b",
                status="error",
                document_id=doc["id"],
                execution_time_ms=doc_exec_time,
                error_message=str(e)
            )
            logger.error("agent_1b_document_error", doc_id=doc["id"], error=str(e))
            state["errors"].append(f"Agent 1B (doc {doc['id']}): {str(e)}")
    
    state["pertinence_results"] = pertinence_results
    state["documents_pertinent"] = documents_pertinent
    state["documents_non_pertinent"] = documents_non_pertinent
    
    logger.info(
        "node_agent_1b_completed",
        pertinent=len(documents_pertinent),
        non_pertinent=len(documents_non_pertinent)
    )
    
    return state


def should_continue_to_agent_2(state: PINGState) -> Literal["agent_2", "end_no_pertinent"]:
    """
    Condition : Y a-t-il des documents pertinents à analyser ?
    
    OUI ou PARTIELLEMENT → Agent 2
    NON (tous) → END
    """
    if state["documents_pertinent"]:
        return "agent_2"
    else:
        logger.info("no_pertinent_documents", message="Aucun document pertinent, fin du workflow")
        return "end_no_pertinent"


def node_agent_2(state: PINGState) -> PINGState:
    """
    Node Agent 2 : Analyse de risque pour chaque document pertinent
    """
    import time
    start_time = time.time()
    logger.info("node_agent_2_started", documents_count=len(state["documents_pertinent"]))
    state["current_step"] = "agent_2"
    
    agent_2 = Agent2()
    risk_analyses = []
    
    for item in state["documents_pertinent"]:
        doc = item["document"]
        pertinence_result = item["pertinence_result"]
        doc_start_time = time.time()
        
        try:
            logger.info(
                "agent_2_analyzing_document",
                doc_id=doc["id"][:8],
                title=doc.get("title", "")[:60]
            )
            
            # Agent 2 analyse le document
            risk_analysis, risk_projections = agent_2.analyze(
                document=doc,
                pertinence_result=pertinence_result,
                sites=state["sites"],
                suppliers=state["suppliers"],
                supplier_relationships=state["supplier_relationships"]
            )
            
            # NOUVEAU : Sauvegarder le RiskAnalysis en BDD
            risk_analysis_id = save_risk_analysis(doc, pertinence_result, risk_analysis)
            risk_analysis["id"] = risk_analysis_id
            
            logger.info(
                "agent_2_risk_computed",
                doc_id=doc["id"][:8],
                risk_level=risk_analysis.get("overall_risk_level"),
                risk_score=risk_analysis.get("risk_score", 0),
                affected_sites=len(risk_analysis.get("affected_sites", [])),
                affected_suppliers=len(risk_analysis.get("affected_suppliers", []))
            )
            
            # ================================================================
            # AFFICHAGE DÉTAILLÉ DE L'ANALYSE AGENT 2
            # ================================================================
            print("\n" + "=" * 70)
            print(f"📊 ANALYSE DÉTAILLÉE - {doc.get('title', 'Document')[:50]}")
            print("=" * 70)
            
            # Score et niveau de risque
            print(f"\n🎯 SCORE DE RISQUE: {risk_analysis.get('risk_score', 0)}/100")
            print(f"   Niveau: {risk_analysis.get('overall_risk_level', 'N/A')}")
            
            # Section 1: Contexte et enjeux
            context = risk_analysis.get("context_and_stakes")
            if context:
                print(f"\n📋 1. CONTEXTE ET ENJEUX:")
                print(f"   {context[:500]}..." if len(str(context)) > 500 else f"   {context}")
            
            # Section 2: Entités affectées
            entities = risk_analysis.get("affected_entities_details")
            if entities:
                print(f"\n🏭 2. ENTITÉS AFFECTÉES:")
                print(f"   {entities[:400]}..." if len(str(entities)) > 400 else f"   {entities}")
            
            # Section 3: Analyse financière
            financial = risk_analysis.get("financial_analysis")
            if financial:
                print(f"\n💰 3. ANALYSE FINANCIÈRE:")
                print(f"   {financial[:500]}..." if len(str(financial)) > 500 else f"   {financial}")
            
            # Section 4: Recommandations
            recommendations = risk_analysis.get("recommendations", [])
            if recommendations:
                print(f"\n✅ 4. RECOMMANDATIONS ({len(recommendations)}):")
                for i, rec in enumerate(recommendations[:3], 1):
                    if isinstance(rec, dict):
                        print(f"   {i}. {rec.get('title', rec.get('action', 'N/A'))}")
                        print(f"      Priorité: {rec.get('priority', 'N/A')} | ROI: {rec.get('roi', 'N/A')}")
                    else:
                        print(f"   {i}. {str(rec)[:100]}")
                if len(recommendations) > 3:
                    print(f"   ... et {len(recommendations) - 3} autres recommandations")
            
            # Section 5: Timeline
            timeline = risk_analysis.get("timeline")
            if timeline:
                print(f"\n📅 5. TIMELINE:")
                print(f"   {timeline[:300]}..." if len(str(timeline)) > 300 else f"   {timeline}")
            
            # Section 6: Matrice de priorisation
            matrix = risk_analysis.get("prioritization_matrix")
            if matrix:
                print(f"\n📊 6. MATRICE DE PRIORISATION:")
                print(f"   {matrix[:300]}..." if len(str(matrix)) > 300 else f"   {matrix}")
            
            # Section 7: Scénario sans action
            do_nothing = risk_analysis.get("do_nothing_scenario")
            if do_nothing:
                print(f"\n⚠️ 7. SCÉNARIO SANS ACTION:")
                print(f"   {do_nothing[:400]}..." if len(str(do_nothing)) > 400 else f"   {do_nothing}")
            
            print("\n" + "=" * 70)
            
            # NOUVEAU : Sauvegarder les projections de risque par entité
            projections_count = save_risk_projections(doc["id"], risk_projections)
            
            risk_analyses.append({
                "document": doc,
                "pertinence_result": pertinence_result,
                "risk_analysis": risk_analysis,
                "risk_projections": risk_projections
            })
            
            # LOG D'EXÉCUTION
            doc_exec_time = int((time.time() - doc_start_time) * 1000)
            log_execution(
                agent_name="agent_2",
                status="success",
                document_id=doc["id"],
                execution_time_ms=doc_exec_time,
                extra_metadata={
                    "risk_analysis_id": risk_analysis_id,
                    "risk_level": risk_analysis.get("overall_risk_level"),
                    "risk_score_360": risk_analysis.get("risk_score_360"),
                    "affected_sites": len(risk_analysis.get("affected_sites", [])),
                    "affected_suppliers": len(risk_analysis.get("affected_suppliers", [])),
                    "weather_alerts": risk_analysis.get("weather_risk_summary", {}).get("total_alerts", 0),
                    "projections_saved": projections_count
                }
            )
            
            logger.info(
                "risk_analysis_completed",
                doc_id=doc["id"],
                risk_id=risk_analysis_id,
                risk_level=risk_analysis.get("risk_level"),
                risk_score=risk_analysis.get("risk_score")
            )
            
        except Exception as e:
            doc_exec_time = int((time.time() - doc_start_time) * 1000)
            log_execution(
                agent_name="agent_2",
                status="error",
                document_id=doc["id"],
                execution_time_ms=doc_exec_time,
                error_message=str(e)
            )
            logger.error("agent_2_document_error", doc_id=doc["id"], error=str(e))
            state["errors"].append(f"Agent 2 (doc {doc['id']}): {str(e)}")
    
    state["risk_analyses"] = risk_analyses
    
    logger.info("node_agent_2_completed", analyses_count=len(risk_analyses))
    
    return state


def node_llm_judge(state: PINGState) -> PINGState:
    """
    Node LLM Judge : Évaluation de qualité pour chaque analyse
    """
    import time
    start_time = time.time()
    logger.info("node_llm_judge_started", analyses_count=len(state["risk_analyses"]))
    state["current_step"] = "llm_judge"
    
    judge = Judge()
    judge_evaluations = []
    approved = []
    needs_review = []
    rejected = []
    
    for item in state["risk_analyses"]:
        doc = item["document"]
        pertinence_result = item["pertinence_result"]
        risk_analysis = item["risk_analysis"]
        doc_start_time = time.time()
        
        try:
            # Évaluation par le Judge
            evaluation = judge.evaluate(
                document=doc,
                pertinence_result=pertinence_result,
                risk_analysis=risk_analysis,
                sites=state["sites"],
                suppliers=state["suppliers"],
                supplier_relationships=state["supplier_relationships"]
            )
            
            # Sauvegarder l'évaluation
            risk_analysis_id = risk_analysis.get("id")
            if risk_analysis_id:
                eval_id = save_judge_evaluation(risk_analysis_id, evaluation)
                evaluation["id"] = eval_id
            
            judge_evaluations.append({
                "document": doc,
                "risk_analysis": risk_analysis,
                "evaluation": evaluation
            })
            
            # Catégoriser selon le score
            score = evaluation.get("overall_score", 0)
            action = evaluation.get("action", "REVIEW")
            
            result_item = {
                "document": doc,
                "pertinence_result": pertinence_result,
                "risk_analysis": risk_analysis,
                "judge_evaluation": evaluation
            }
            
            # LOG D'EXÉCUTION
            doc_exec_time = int((time.time() - doc_start_time) * 1000)
            log_execution(
                agent_name="judge",
                status="success",
                document_id=doc["id"],
                execution_time_ms=doc_exec_time,
                extra_metadata={
                    "overall_score": score,
                    "action": action,
                    "confidence": evaluation.get("overall_confidence"),
                    "pertinence_score": evaluation.get("pertinence_checker_score"),
                    "risk_analyzer_score": evaluation.get("risk_analyzer_score")
                }
            )
            
            if score >= 8.5 or action == "APPROVE":
                approved.append(result_item)
                # Créer une alerte pour les documents approuvés
                if risk_analysis_id:
                    create_alert(doc, risk_analysis, evaluation)
                logger.info(
                    "document_approved",
                    doc_id=doc["id"],
                    score=score
                )
                
            elif score >= 7.0 or action == "REVIEW":
                needs_review.append(result_item)
                logger.info(
                    "document_needs_review",
                    doc_id=doc["id"],
                    score=score
                )
                
            else:
                rejected.append(result_item)
                logger.info(
                    "document_rejected",
                    doc_id=doc["id"],
                    score=score
                )
                
        except Exception as e:
            doc_exec_time = int((time.time() - doc_start_time) * 1000)
            log_execution(
                agent_name="judge",
                status="error",
                document_id=doc["id"],
                execution_time_ms=doc_exec_time,
                error_message=str(e)[:500]  # Limiter la taille de l'erreur
            )
            logger.error("judge_document_error", doc_id=doc["id"], error=str(e))
            state["errors"].append(f"LLM Judge (doc {doc['id']}): {str(e)}")
    
    state["judge_evaluations"] = judge_evaluations
    state["approved"] = approved
    state["needs_review"] = needs_review
    state["rejected"] = rejected
    
    logger.info(
        "node_llm_judge_completed",
        approved=len(approved),
        needs_review=len(needs_review),
        rejected=len(rejected)
    )
    
    return state


def node_notification(state: PINGState) -> PINGState:
    """
    Node Notification : Envoie des alertes email selon le niveau de risque
    
    - CRITIQUE/ELEVE (APPROVE): Notification immédiate
    - MOYEN (REVIEW): Notification pour validation humaine
    - FAIBLE (REJECT): Archivage, pas de notification
    """
    import time
    start_time = time.time()
    logger.info("node_notification_started")
    state["current_step"] = "notification"
    
    # Initialiser le service (dry_run=True par défaut)
    notification_service = NotificationService(dry_run=True)
    
    notifications_sent = []
    notifications_skipped = []
    
    # Traiter les documents approuvés (notification immédiate)
    for item in state.get("approved", []):
        doc = item["document"]
        risk_analysis = item["risk_analysis"]
        pertinence_result = item.get("pertinence_result", {})
        judge_eval = item.get("judge_evaluation", {})
        
        try:
            result = notification_service.notify_risk_analysis(
                document=doc,
                risk_analysis=risk_analysis,
                pertinence_result=pertinence_result
            )
            
            notifications_sent.append({
                "document_id": doc.get("id"),
                "title": doc.get("title", "")[:50],
                "risk_level": result.get("risk_level"),
                "recipients_count": result.get("recipients_count"),
                "status": result.get("status"),
                "category": "APPROVE"
            })
            
            logger.info(
                "notification_sent_approve",
                doc_id=doc.get("id"),
                risk_level=result.get("risk_level"),
                recipients=result.get("recipients_count")
            )
            
        except Exception as e:
            logger.error("notification_error", doc_id=doc.get("id"), error=str(e))
            state["errors"].append(f"Notification (doc {doc.get('id')}): {str(e)}")
    
    # Traiter les documents en review (notification pour validation)
    for item in state.get("needs_review", []):
        doc = item["document"]
        risk_analysis = item["risk_analysis"]
        pertinence_result = item.get("pertinence_result", {})
        
        try:
            result = notification_service.notify_risk_analysis(
                document=doc,
                risk_analysis=risk_analysis,
                pertinence_result=pertinence_result
            )
            
            notifications_sent.append({
                "document_id": doc.get("id"),
                "title": doc.get("title", "")[:50],
                "risk_level": result.get("risk_level"),
                "recipients_count": result.get("recipients_count"),
                "status": result.get("status"),
                "category": "REVIEW"
            })
            
            logger.info(
                "notification_sent_review",
                doc_id=doc.get("id"),
                risk_level=result.get("risk_level"),
                recipients=result.get("recipients_count")
            )
            
        except Exception as e:
            logger.error("notification_error", doc_id=doc.get("id"), error=str(e))
            state["errors"].append(f"Notification (doc {doc.get('id')}): {str(e)}")
    
    # Les documents rejetés ne reçoivent pas de notification
    for item in state.get("rejected", []):
        doc = item["document"]
        notifications_skipped.append({
            "document_id": doc.get("id"),
            "title": doc.get("title", "")[:50],
            "reason": "Score trop faible - Archivé"
        })
    
    # Stocker les résultats dans le state
    state["notifications_sent"] = notifications_sent
    state["notifications_skipped"] = notifications_skipped
    
    exec_time = int((time.time() - start_time) * 1000)
    log_execution(
        agent_name="notification",
        status="success",
        execution_time_ms=exec_time,
        extra_metadata={
            "sent_count": len(notifications_sent),
            "skipped_count": len(notifications_skipped)
        }
    )
    
    # Afficher le résumé
    print("\n" + "=" * 70)
    print("📧 RÉSUMÉ DES NOTIFICATIONS")
    print("=" * 70)
    print(f"✅ Notifications envoyées: {len(notifications_sent)}")
    for notif in notifications_sent:
        print(f"   • {notif['category']} - {notif['risk_level']} - {notif['title']}")
        print(f"     Destinataires: {notif['recipients_count']} | Status: {notif['status']}")
    
    if notifications_skipped:
        print(f"\n⏭️  Notifications ignorées: {len(notifications_skipped)}")
        for skip in notifications_skipped:
            print(f"   • {skip['title']} - {skip['reason']}")
    print("=" * 70 + "\n")
    
    logger.info(
        "node_notification_completed",
        sent=len(notifications_sent),
        skipped=len(notifications_skipped)
    )
    
    return state


def node_end_no_pertinent(state: PINGState) -> PINGState:
    """Node de fin quand aucun document n'est pertinent"""
    state["current_step"] = "completed_no_pertinent"
    logger.info("workflow_ended_no_pertinent_documents")
    return state


def node_end_success(state: PINGState) -> PINGState:
    """Node de fin avec succès"""
    state["current_step"] = "completed"
    logger.info(
        "workflow_completed",
        total_collected=len(state["documents_collected"]),
        pertinent=len(state["documents_pertinent"]),
        approved=len(state["approved"]),
        needs_review=len(state["needs_review"]),
        rejected=len(state["rejected"]),
        errors=len(state["errors"])
    )
    return state


# ============================================================================
# WORKFLOW CONSTRUCTION
# ============================================================================

def create_ping_workflow() -> StateGraph:
    """
    Crée le workflow LangGraph PING
    
    Workflow:
    START → load_company → agent_1a → agent_1b → [condition] → agent_2 → judge → END
                                               → [no pertinent] → END
    """
    
    # Créer le graphe
    workflow = StateGraph(PINGState)
    
    # Ajouter les nodes
    workflow.add_node("load_company_data", node_load_company_data)
    workflow.add_node("agent_1a", node_agent_1a)
    workflow.add_node("agent_1b", node_agent_1b)
    workflow.add_node("agent_2", node_agent_2)
    workflow.add_node("llm_judge", node_llm_judge)
    workflow.add_node("notification", node_notification)
    workflow.add_node("end_no_pertinent", node_end_no_pertinent)
    workflow.add_node("end_success", node_end_success)
    
    # Définir le point d'entrée
    workflow.set_entry_point("load_company_data")
    
    # Définir les edges
    workflow.add_edge("load_company_data", "agent_1a")
    workflow.add_edge("agent_1a", "agent_1b")
    
    # Condition après Agent 1B
    workflow.add_conditional_edges(
        "agent_1b",
        should_continue_to_agent_2,
        {
            "agent_2": "agent_2",
            "end_no_pertinent": "end_no_pertinent"
        }
    )
    
    workflow.add_edge("agent_2", "llm_judge")
    workflow.add_edge("llm_judge", "notification")
    workflow.add_edge("notification", "end_success")
    workflow.add_edge("end_no_pertinent", END)
    workflow.add_edge("end_success", END)
    
    return workflow


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def run_ping_workflow(
    keyword: str = "CBAM",
    max_documents: int = 10,
    company_name: str = "HUTCHINSON"
) -> Dict:
    """
    Exécute le workflow PING complet
    
    Args:
        keyword: Mot-clé pour la recherche (CBAM, EUDR, CSRD)
        max_documents: Nombre maximum de documents à collecter
        company_name: Nom de l'entreprise
        
    Returns:
        Dict avec les résultats du workflow
    """
    print("\n" + "=" * 70)
    print("🚀 PING LangGraph Workflow")
    print("=" * 70)
    print(f"Keyword: {keyword}")
    print(f"Max Documents: {max_documents}")
    print(f"Company: {company_name}")
    print("=" * 70 + "\n")
    
    # Créer et compiler le workflow
    workflow = create_ping_workflow()
    app = workflow.compile()
    
    # État initial
    initial_state: PINGState = {
        "keyword": keyword,
        "max_documents": max_documents,
        "company_name": company_name,
        "agent_1a_result": None,
        "documents_collected": [],
        "pertinence_results": [],
        "documents_pertinent": [],
        "documents_non_pertinent": [],
        "risk_analyses": [],
        "judge_evaluations": [],
        "approved": [],
        "needs_review": [],
        "rejected": [],
        "notifications_sent": [],
        "notifications_skipped": [],
        "company_profile": None,
        "sites": [],
        "suppliers": [],
        "supplier_relationships": [],
        "errors": [],
        "current_step": "starting"
    }
    
    # Exécuter le workflow
    try:
        final_state = app.invoke(initial_state)
        
        # Résumé
        print("\n" + "=" * 70)
        print("📊 RÉSUMÉ DU WORKFLOW")
        print("=" * 70)
        print(f"✅ Documents collectés: {len(final_state['documents_collected'])}")
        print(f"✅ Documents pertinents: {len(final_state['documents_pertinent'])}")
        print(f"✅ Documents non pertinents: {len(final_state['documents_non_pertinent'])}")
        print(f"✅ Analyses de risque: {len(final_state['risk_analyses'])}")
        print(f"\n🎯 DÉCISIONS DU JUDGE:")
        print(f"   🟢 APPROUVÉS (Score ≥ 8.5): {len(final_state['approved'])}")
        print(f"   🟡 À REVOIR (Score 7.0-8.4): {len(final_state['needs_review'])}")
        print(f"   🔴 REJETÉS (Score < 7.0): {len(final_state['rejected'])}")
        
        if final_state["errors"]:
            print(f"\n⚠️ Erreurs: {len(final_state['errors'])}")
            for err in final_state["errors"][:5]:
                print(f"   - {err}")
        
        print("=" * 70 + "\n")
        
        return {
            "status": "success",
            "summary": {
                "documents_collected": len(final_state["documents_collected"]),
                "documents_pertinent": len(final_state["documents_pertinent"]),
                "documents_non_pertinent": len(final_state["documents_non_pertinent"]),
                "risk_analyses": len(final_state["risk_analyses"]),
                "approved": len(final_state["approved"]),
                "needs_review": len(final_state["needs_review"]),
                "rejected": len(final_state["rejected"]),
                "errors": len(final_state["errors"])
            },
            "state": final_state
        }
        
    except Exception as e:
        logger.error("workflow_failed", error=str(e))
        print(f"\n❌ ERREUR: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    result = run_ping_workflow(
        keyword="CBAM",
        max_documents=3,
        company_name="HUTCHINSON"
    )
    
    print("\n🏁 Workflow terminé!")
    print(f"Status: {result.get('status')}")
