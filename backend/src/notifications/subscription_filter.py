"""
Filtrage des notifications par abonnements
Vérifie si une notification correspond aux critères d'un abonnement
"""

from typing import List, Dict, Any, Set
from datetime import datetime
import structlog

from src.storage.database import get_session
from src.storage.models import AlertSubscription

logger = structlog.get_logger()


# Mapping des niveaux de criticité pour la comparaison
CRITICALITY_ORDER = {
    "FAIBLE": 1,
    "MOYEN": 2,
    "ELEVE": 3,
    "CRITIQUE": 4
}


def risk_level_to_criticality(risk_level: str) -> str:
    """Convertit le niveau de risque en criticité"""
    mapping = {
        "Faible": "FAIBLE",
        "Moyen": "MOYEN",
        "Fort": "ELEVE",
        "Critique": "CRITIQUE",
        # Variantes possibles
        "faible": "FAIBLE",
        "moyen": "MOYEN",
        "fort": "ELEVE",
        "critique": "CRITIQUE",
        "eleve": "ELEVE",
        "ELEVE": "ELEVE",
    }
    return mapping.get(risk_level, "MOYEN")


def is_criticality_sufficient(notification_criticality: str, min_criticality: str) -> bool:
    """
    Vérifie si la criticité de la notification est >= à la criticité minimum de l'abonnement
    
    Ex: Si l'abonnement veut MOYEN+, et la notification est ELEVE → True
        Si l'abonnement veut ELEVE+, et la notification est MOYEN → False
    """
    notif_order = CRITICALITY_ORDER.get(notification_criticality.upper(), 2)
    min_order = CRITICALITY_ORDER.get(min_criticality.upper(), 2)
    return notif_order >= min_order


def event_type_matches(subscription_event_types: List[str], notification_event_type: str) -> bool:
    """Vérifie si le type d'événement correspond"""
    if not subscription_event_types or "all" in subscription_event_types:
        return True
    
    # Normaliser le type d'événement
    notif_type = notification_event_type.lower()
    sub_types = [t.lower() for t in subscription_event_types]
    
    return notif_type in sub_types


def entities_match_filters(
    affected_sites: List[Dict],
    affected_suppliers: List[Dict],
    sub_site_ids: List[str],
    sub_supplier_ids: List[str],
    sub_countries: List[str]
) -> bool:
    """
    Vérifie si les entités affectées correspondent aux filtres de l'abonnement
    
    Logique:
    - Si aucun filtre (site_ids, supplier_ids, countries vides) → True
    - Si filtres définis, au moins un doit matcher
    """
    has_site_filter = sub_site_ids and len(sub_site_ids) > 0
    has_supplier_filter = sub_supplier_ids and len(sub_supplier_ids) > 0
    has_country_filter = sub_countries and len(sub_countries) > 0
    
    # Si aucun filtre d'entité, la notification passe
    if not has_site_filter and not has_supplier_filter and not has_country_filter:
        return True
    
    # Extraire les IDs et pays des entités affectées
    affected_site_ids = set()
    affected_supplier_ids = set()
    affected_countries = set()
    
    for site in (affected_sites or []):
        if site.get("id"):
            affected_site_ids.add(site["id"])
        if site.get("site_id"):
            affected_site_ids.add(site["site_id"])
        if site.get("country"):
            affected_countries.add(site["country"])
    
    for supplier in (affected_suppliers or []):
        if supplier.get("id"):
            affected_supplier_ids.add(supplier["id"])
        if supplier.get("supplier_id"):
            affected_supplier_ids.add(supplier["supplier_id"])
        if supplier.get("country"):
            affected_countries.add(supplier["country"])
    
    # Vérifier les correspondances
    site_match = False
    supplier_match = False
    country_match = False
    
    if has_site_filter:
        site_match = bool(affected_site_ids & set(sub_site_ids))
    
    if has_supplier_filter:
        supplier_match = bool(affected_supplier_ids & set(sub_supplier_ids))
    
    if has_country_filter:
        country_match = bool(affected_countries & set(sub_countries))
    
    # Au moins un filtre doit matcher
    if has_site_filter and not site_match:
        return False
    if has_supplier_filter and not supplier_match:
        return False
    if has_country_filter and not country_match:
        return False
    
    return True


def notification_type_enabled(subscription: AlertSubscription, event_type: str) -> bool:
    """Vérifie si le type de notification est activé dans l'abonnement"""
    event_type_lower = event_type.lower()
    
    if event_type_lower in ["reglementaire", "regulatory"]:
        return subscription.include_regulatory
    elif event_type_lower in ["climatique", "climate", "meteo", "weather"]:
        return subscription.include_weather_alerts
    elif event_type_lower in ["geopolitique", "geopolitical"]:
        return subscription.include_geopolitical
    
    return True  # Par défaut, accepter


def get_matching_subscriptions(
    event_type: str,
    risk_level: str,
    affected_sites: List[Dict] = None,
    affected_suppliers: List[Dict] = None
) -> List[Dict[str, Any]]:
    """
    Récupère tous les abonnements qui correspondent à la notification
    
    Args:
        event_type: Type d'événement (reglementaire, climatique, geopolitique)
        risk_level: Niveau de risque (Faible, Moyen, Fort, Critique)
        affected_sites: Liste des sites affectés
        affected_suppliers: Liste des fournisseurs affectés
        
    Returns:
        Liste des abonnements correspondants avec leurs emails
    """
    log = logger.bind(
        event_type=event_type,
        risk_level=risk_level,
        affected_sites_count=len(affected_sites or []),
        affected_suppliers_count=len(affected_suppliers or [])
    )
    
    matching_subscriptions = []
    notification_criticality = risk_level_to_criticality(risk_level)
    
    with get_session() as session:
        # Récupérer tous les abonnements actifs et vérifiés
        active_subscriptions = session.query(AlertSubscription).filter(
            AlertSubscription.is_active == True,
            AlertSubscription.verified == True
        ).all()
        
        log.info(f"Checking {len(active_subscriptions)} active subscriptions")
        
        for sub in active_subscriptions:
            # Vérifier chaque critère
            
            # 1. Type d'événement
            if not event_type_matches(sub.event_types or ["all"], event_type):
                continue
            
            # 2. Criticité minimum
            if not is_criticality_sufficient(notification_criticality, sub.min_criticality):
                continue
            
            # 3. Type de notification activé
            if not notification_type_enabled(sub, event_type):
                continue
            
            # 4. Filtres d'entités (sites, fournisseurs, pays)
            if not entities_match_filters(
                affected_sites,
                affected_suppliers,
                sub.site_ids,
                sub.supplier_ids,
                sub.countries
            ):
                continue
            
            # L'abonnement correspond !
            matching_subscriptions.append({
                "subscription_id": sub.id,
                "email": sub.email,
                "name": sub.name,
                "subscription_name": sub.subscription_name,
                "notify_immediately": sub.notify_immediately
            })
            
            log.debug(
                "subscription_matched",
                subscription_id=sub.id[:8],
                email=sub.email
            )
    
    log.info(
        "subscription_matching_complete",
        total_checked=len(active_subscriptions) if 'active_subscriptions' in dir() else 0,
        matching_count=len(matching_subscriptions)
    )
    
    return matching_subscriptions


def update_subscription_stats(subscription_id: str):
    """Met à jour les statistiques de l'abonnement après notification"""
    with get_session() as session:
        sub = session.query(AlertSubscription).filter(
            AlertSubscription.id == subscription_id
        ).first()
        
        if sub:
            sub.notification_count = (sub.notification_count or 0) + 1
            sub.last_notified_at = datetime.utcnow()
            session.commit()
