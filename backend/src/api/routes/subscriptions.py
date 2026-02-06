"""
Routes API pour la gestion des abonnements aux alertes
"""

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import uuid4
import secrets
from datetime import datetime

from src.storage.database import get_session
from src.storage.models import AlertSubscription, HutchinsonSite, Supplier
from src.api.schemas import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    SubscriptionListResponse
)

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


def subscription_to_response(sub: AlertSubscription) -> SubscriptionResponse:
    """Convertit un modèle SQLAlchemy en réponse Pydantic"""
    return SubscriptionResponse(
        id=sub.id,
        email=sub.email,
        name=sub.name,
        subscription_name=sub.subscription_name,
        event_types=sub.event_types or ["all"],
        supplier_ids=sub.supplier_ids,
        supplier_names=sub.supplier_names,
        site_ids=sub.site_ids,
        site_names=sub.site_names,
        countries=sub.countries,
        min_criticality=sub.min_criticality,
        notify_immediately=sub.notify_immediately,
        digest_frequency=sub.digest_frequency,
        include_weather_alerts=sub.include_weather_alerts,
        include_regulatory=sub.include_regulatory,
        include_geopolitical=sub.include_geopolitical,
        is_active=sub.is_active,
        verified=sub.verified,
        notification_count=sub.notification_count,
        last_notified_at=sub.last_notified_at,
        created_at=sub.created_at
    )


@router.post("", response_model=SubscriptionResponse)
async def create_subscription(data: SubscriptionCreate):
    """
    Créer un nouvel abonnement aux alertes.
    
    Un email de vérification sera envoyé (à implémenter).
    """
    with get_session() as session:
        # Récupérer les noms des fournisseurs si des IDs sont fournis
        supplier_names = None
        if data.supplier_ids:
            suppliers = session.query(Supplier).filter(
                Supplier.id.in_(data.supplier_ids)
            ).all()
            supplier_names = [s.name for s in suppliers]
        
        # Récupérer les noms des sites si des IDs sont fournis
        site_names = None
        if data.site_ids:
            sites = session.query(HutchinsonSite).filter(
                HutchinsonSite.id.in_(data.site_ids)
            ).all()
            site_names = [s.name for s in sites]
        
        subscription = AlertSubscription(
            id=str(uuid4()),
            email=data.email,
            name=data.name,
            subscription_name=data.subscription_name,
            event_types=data.event_types,
            supplier_ids=data.supplier_ids,
            supplier_names=supplier_names,
            site_ids=data.site_ids,
            site_names=site_names,
            countries=data.countries,
            min_criticality=data.min_criticality,
            notify_immediately=data.notify_immediately,
            digest_frequency=data.digest_frequency,
            include_weather_alerts=data.include_weather_alerts,
            include_regulatory=data.include_regulatory,
            include_geopolitical=data.include_geopolitical,
            verification_token=secrets.token_urlsafe(32),
            verified=True,  # Pour l'instant, valider automatiquement
            is_active=True
        )
        
        session.add(subscription)
        session.commit()
        session.refresh(subscription)
        
        return subscription_to_response(subscription)


@router.get("", response_model=SubscriptionListResponse)
async def list_subscriptions(
    email: Optional[str] = Query(None, description="Filtrer par email"),
    active_only: bool = Query(True, description="Uniquement les abonnements actifs")
):
    """
    Lister les abonnements.
    
    Si un email est fourni, retourne uniquement les abonnements de cet email.
    """
    with get_session() as session:
        query = session.query(AlertSubscription)
        
        if email:
            query = query.filter(AlertSubscription.email == email)
        
        if active_only:
            query = query.filter(AlertSubscription.is_active == True)
        
        subscriptions = query.order_by(AlertSubscription.created_at.desc()).all()
        
        return SubscriptionListResponse(
            subscriptions=[subscription_to_response(s) for s in subscriptions],
            total=len(subscriptions)
        )


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(subscription_id: str):
    """Récupérer les détails d'un abonnement"""
    with get_session() as session:
        subscription = session.query(AlertSubscription).filter(
            AlertSubscription.id == subscription_id
        ).first()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Abonnement non trouvé")
        
        return subscription_to_response(subscription)


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(subscription_id: str, data: SubscriptionUpdate):
    """Mettre à jour un abonnement"""
    with get_session() as session:
        subscription = session.query(AlertSubscription).filter(
            AlertSubscription.id == subscription_id
        ).first()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Abonnement non trouvé")
        
        # Mettre à jour les champs fournis
        if data.subscription_name is not None:
            subscription.subscription_name = data.subscription_name
        if data.event_types is not None:
            subscription.event_types = data.event_types
        if data.supplier_ids is not None:
            subscription.supplier_ids = data.supplier_ids
            # Récupérer les noms
            if data.supplier_ids:
                suppliers = session.query(Supplier).filter(
                    Supplier.id.in_(data.supplier_ids)
                ).all()
                subscription.supplier_names = [s.name for s in suppliers]
            else:
                subscription.supplier_names = None
        if data.site_ids is not None:
            subscription.site_ids = data.site_ids
            # Récupérer les noms
            if data.site_ids:
                sites = session.query(HutchinsonSite).filter(
                    HutchinsonSite.id.in_(data.site_ids)
                ).all()
                subscription.site_names = [s.name for s in sites]
            else:
                subscription.site_names = None
        if data.countries is not None:
            subscription.countries = data.countries
        if data.min_criticality is not None:
            subscription.min_criticality = data.min_criticality
        if data.notify_immediately is not None:
            subscription.notify_immediately = data.notify_immediately
        if data.digest_frequency is not None:
            subscription.digest_frequency = data.digest_frequency
        if data.include_weather_alerts is not None:
            subscription.include_weather_alerts = data.include_weather_alerts
        if data.include_regulatory is not None:
            subscription.include_regulatory = data.include_regulatory
        if data.include_geopolitical is not None:
            subscription.include_geopolitical = data.include_geopolitical
        if data.is_active is not None:
            subscription.is_active = data.is_active
        
        subscription.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(subscription)
        
        return subscription_to_response(subscription)


@router.delete("/{subscription_id}")
async def delete_subscription(subscription_id: str):
    """Supprimer un abonnement"""
    with get_session() as session:
        subscription = session.query(AlertSubscription).filter(
            AlertSubscription.id == subscription_id
        ).first()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Abonnement non trouvé")
        
        session.delete(subscription)
        session.commit()
        
        return {"message": "Abonnement supprimé", "id": subscription_id}


@router.post("/{subscription_id}/toggle")
async def toggle_subscription(subscription_id: str):
    """Activer/désactiver un abonnement"""
    with get_session() as session:
        subscription = session.query(AlertSubscription).filter(
            AlertSubscription.id == subscription_id
        ).first()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Abonnement non trouvé")
        
        subscription.is_active = not subscription.is_active
        subscription.updated_at = datetime.utcnow()
        session.commit()
        
        return {
            "id": subscription_id,
            "is_active": subscription.is_active,
            "message": "Abonnement activé" if subscription.is_active else "Abonnement désactivé"
        }


# ========================================
# Routes pour obtenir les options de filtrage
# ========================================

@router.get("/options/suppliers")
async def get_supplier_options():
    """Retourne la liste des fournisseurs pour les filtres"""
    with get_session() as session:
        suppliers = session.query(Supplier).filter(
            Supplier.active == True
        ).order_by(Supplier.name).all()
        
        return [
            {
                "id": s.id,
                "name": s.name,
                "country": s.country,
                "sector": s.sector
            }
            for s in suppliers
        ]


@router.get("/options/sites")
async def get_site_options():
    """Retourne la liste des sites Hutchinson pour les filtres"""
    with get_session() as session:
        sites = session.query(HutchinsonSite).filter(
            HutchinsonSite.active == True
        ).order_by(HutchinsonSite.name).all()
        
        return [
            {
                "id": s.id,
                "name": s.name,
                "code": s.code,
                "country": s.country,
                "city": s.city
            }
            for s in sites
        ]


@router.get("/options/countries")
async def get_country_options():
    """Retourne la liste des pays disponibles"""
    with get_session() as session:
        # Pays des fournisseurs
        supplier_countries = session.query(Supplier.country).distinct().all()
        # Pays des sites
        site_countries = session.query(HutchinsonSite.country).distinct().all()
        
        # Combiner et dédupliquer
        all_countries = set()
        for (country,) in supplier_countries:
            if country:
                all_countries.add(country)
        for (country,) in site_countries:
            if country:
                all_countries.add(country)
        
        return sorted(list(all_countries))


@router.get("/options/event-types")
async def get_event_type_options():
    """Retourne les types d'événements disponibles"""
    return [
        {"value": "all", "label": "Tous les types", "description": "Recevoir toutes les alertes"},
        {"value": "reglementaire", "label": "Réglementaire", "description": "Nouvelles réglementations (CBAM, CRCD, etc.)"},
        {"value": "climatique", "label": "Climatique", "description": "Alertes météo et risques climatiques"},
        {"value": "geopolitique", "label": "Géopolitique", "description": "Conflits, sanctions, instabilité"}
    ]


@router.get("/options/criticality-levels")
async def get_criticality_options():
    """Retourne les niveaux de criticité disponibles"""
    return [
        {"value": "FAIBLE", "label": "Faible et +", "description": "Recevoir toutes les alertes"},
        {"value": "MOYEN", "label": "Moyen et +", "description": "Alertes moyennes, élevées et critiques"},
        {"value": "ELEVE", "label": "Élevé et +", "description": "Alertes élevées et critiques uniquement"},
        {"value": "CRITIQUE", "label": "Critique uniquement", "description": "Uniquement les alertes critiques"}
    ]
