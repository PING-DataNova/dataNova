"""
Routes API Administration
=========================

Endpoints pour la gestion des sources de données, types de risques,
et configuration du système par l'administrateur.

Conforme CDC:
- L'admin peut ajouter/supprimer des sources sans toucher au code
- L'admin peut activer/désactiver des sources
- L'admin peut paramétrer la fréquence d'analyse
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.storage.database import get_session
from src.storage.datasource_repository import DataSourceRepository
from src.storage.models import DataSource

router = APIRouter(prefix="/admin", tags=["Administration"])


# ============================================================================
# SCHEMAS PYDANTIC
# ============================================================================

class DataSourceCreate(BaseModel):
    """Schéma pour créer une source de données"""
    name: str = Field(..., min_length=2, max_length=100, description="Nom unique de la source")
    description: Optional[str] = Field(None, description="Description de la source")
    source_type: str = Field(..., description="Type: api, scraper, file")
    risk_type: str = Field(..., description="Type de risque: regulatory, climate, geopolitical, sanitary")
    base_url: Optional[str] = Field(None, description="URL de base de l'API/source")
    api_key_env_var: Optional[str] = Field(None, description="Nom de la variable d'env pour l'API key")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Configuration spécifique")
    is_active: bool = Field(True, description="Source activée par défaut")
    priority: int = Field(0, description="Priorité (0 = basse, 10 = haute)")


class DataSourceUpdate(BaseModel):
    """Schéma pour mettre à jour une source de données"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    source_type: Optional[str] = None
    risk_type: Optional[str] = None
    base_url: Optional[str] = None
    api_key_env_var: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None


class DataSourceResponse(BaseModel):
    """Schéma de réponse pour une source de données"""
    id: str
    name: str
    description: Optional[str]
    source_type: str
    risk_type: Optional[str]
    base_url: Optional[str]
    api_key_env_var: Optional[str]
    config: Optional[Dict[str, Any]]
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SchedulerConfig(BaseModel):
    """Configuration du scheduler"""
    frequency: str = Field(..., description="Fréquence: hourly, daily, weekly, manual")
    time: Optional[str] = Field(None, description="Heure d'exécution (HH:MM)")
    day_of_week: Optional[str] = Field(None, description="Jour de la semaine pour weekly")
    enabled: bool = Field(True, description="Scheduler activé")


class RiskCategoryCreate(BaseModel):
    """Schéma pour créer une catégorie de risque"""
    name: str = Field(..., description="Nom de la catégorie")
    code: str = Field(..., description="Code interne (regulatory, climate, etc.)")
    description: Optional[str] = None
    color: Optional[str] = Field("#3B82F6", description="Couleur pour l'UI")
    icon: Optional[str] = Field("⚠️", description="Icône emoji")
    is_active: bool = True


# ============================================================================
# ENDPOINTS SOURCES DE DONNÉES
# ============================================================================

@router.get("/sources", response_model=List[DataSourceResponse])
async def list_data_sources(
    risk_type: Optional[str] = None,
    active_only: bool = False
):
    """
    Liste toutes les sources de données.
    
    - **risk_type**: Filtrer par type de risque (regulatory, climate, geopolitical, sanitary)
    - **active_only**: Si True, retourne uniquement les sources activées
    """
    session = get_session()
    try:
        repo = DataSourceRepository(session)
        
        if active_only:
            sources = repo.get_active()
        elif risk_type:
            sources = repo.get_by_risk_type(risk_type)
        else:
            sources = repo.get_all()
        
        return sources
    finally:
        session.close()


@router.post("/sources", response_model=DataSourceResponse, status_code=201)
async def create_data_source(source: DataSourceCreate):
    """
    Crée une nouvelle source de données.
    
    L'administrateur peut ajouter une nouvelle source sans toucher au code.
    L'Agent 1A utilisera automatiquement cette source si elle est activée.
    """
    session = get_session()
    try:
        repo = DataSourceRepository(session)
        
        # Vérifier si le nom existe déjà
        existing = repo.get_by_name(source.name)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Une source avec le nom '{source.name}' existe déjà"
            )
        
        # Créer la source
        new_source = DataSource(
            name=source.name,
            description=source.description,
            source_type=source.source_type,
            risk_type=source.risk_type,
            base_url=source.base_url,
            api_key_env_var=source.api_key_env_var,
            config=source.config or {},
            is_active=source.is_active,
            priority=source.priority
        )
        
        session.add(new_source)
        session.commit()
        session.refresh(new_source)
        
        return new_source
    finally:
        session.close()


@router.get("/sources/{source_id}", response_model=DataSourceResponse)
async def get_data_source(source_id: str):
    """Récupère les détails d'une source de données."""
    session = get_session()
    try:
        repo = DataSourceRepository(session)
        source = repo.get_by_id(source_id)
        
        if not source:
            raise HTTPException(status_code=404, detail="Source non trouvée")
        
        return source
    finally:
        session.close()


@router.put("/sources/{source_id}", response_model=DataSourceResponse)
async def update_data_source(source_id: str, update: DataSourceUpdate):
    """
    Met à jour une source de données.
    
    Seuls les champs fournis seront mis à jour.
    """
    session = get_session()
    try:
        repo = DataSourceRepository(session)
        source = repo.get_by_id(source_id)
        
        if not source:
            raise HTTPException(status_code=404, detail="Source non trouvée")
        
        # Mettre à jour les champs fournis
        update_data = update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(source, key):
                setattr(source, key, value)
        
        source.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(source)
        
        return source
    finally:
        session.close()


@router.delete("/sources/{source_id}")
async def delete_data_source(source_id: str):
    """Supprime une source de données."""
    session = get_session()
    try:
        repo = DataSourceRepository(session)
        success = repo.delete(source_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Source non trouvée")
        
        return {"message": "Source supprimée avec succès", "id": source_id}
    finally:
        session.close()


@router.post("/sources/{source_id}/toggle", response_model=DataSourceResponse)
async def toggle_data_source(source_id: str):
    """
    Active ou désactive une source de données.
    
    Si la source est active, elle sera désactivée et vice-versa.
    L'Agent 1A ne collectera plus de données depuis les sources désactivées.
    """
    session = get_session()
    try:
        repo = DataSourceRepository(session)
        source = repo.toggle_active(source_id)
        
        if not source:
            raise HTTPException(status_code=404, detail="Source non trouvée")
        
        status = "activée" if source.is_active else "désactivée"
        return source
    finally:
        session.close()


# ============================================================================
# ENDPOINTS CATÉGORIES DE RISQUES
# ============================================================================

# Les catégories sont stockées dans la config ou dans une table dédiée
# Pour l'instant, on utilise une liste en mémoire (à persister en BDD si besoin)

RISK_CATEGORIES = [
    {"code": "regulatory", "name": "Réglementaire", "color": "#3B82F6", "icon": "📜", "is_active": True},
    {"code": "climate", "name": "Climatique", "color": "#10B981", "icon": "🌡️", "is_active": True},
    {"code": "geopolitical", "name": "Géopolitique", "color": "#F59E0B", "icon": "🌍", "is_active": True},
    {"code": "sanitary", "name": "Sanitaire", "color": "#EF4444", "icon": "🏥", "is_active": False},
]


@router.get("/risk-categories")
async def list_risk_categories():
    """
    Liste toutes les catégories de risques.
    
    Le client peut ainsi ajouter de nouvelles catégories (ex: risque sanitaire COVID).
    """
    return {
        "categories": RISK_CATEGORIES,
        "total": len(RISK_CATEGORIES),
        "active": sum(1 for c in RISK_CATEGORIES if c["is_active"])
    }


@router.post("/risk-categories")
async def create_risk_category(category: RiskCategoryCreate):
    """
    Ajoute une nouvelle catégorie de risque.
    
    Conforme demande client:
    > "Si on voit que les risques sanitaires deviennent récurrents, 
    > est-ce qu'on peut rajouter ces risques-là comme catégorie?"
    """
    # Vérifier si le code existe déjà
    existing = next((c for c in RISK_CATEGORIES if c["code"] == category.code), None)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Une catégorie avec le code '{category.code}' existe déjà"
        )
    
    new_category = {
        "code": category.code,
        "name": category.name,
        "description": category.description,
        "color": category.color,
        "icon": category.icon,
        "is_active": category.is_active
    }
    
    RISK_CATEGORIES.append(new_category)
    
    return {
        "message": "Catégorie créée avec succès",
        "category": new_category
    }


@router.post("/risk-categories/{code}/toggle")
async def toggle_risk_category(code: str):
    """Active ou désactive une catégorie de risque."""
    category = next((c for c in RISK_CATEGORIES if c["code"] == code), None)
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    
    category["is_active"] = not category["is_active"]
    status = "activée" if category["is_active"] else "désactivée"
    
    return {
        "message": f"Catégorie {status}",
        "category": category
    }


# ============================================================================
# ENDPOINTS SCHEDULER
# ============================================================================

# Configuration du scheduler (en mémoire, à persister en BDD)
SCHEDULER_CONFIG = {
    "frequency": "daily",
    "time": "06:00",
    "day_of_week": None,
    "enabled": True,
    "last_run": None,
    "next_run": None
}


@router.get("/scheduler/config")
async def get_scheduler_config():
    """
    Récupère la configuration du scheduler.
    
    Conforme demande client:
    > "Au moins qu'il y ait la mécanique d'orchestration qui permet, 
    > de manière paramétrée, de dire combien de fois l'administrateur souhaite lancer l'analyse."
    """
    return SCHEDULER_CONFIG


@router.put("/scheduler/config")
async def update_scheduler_config(config: SchedulerConfig):
    """
    Met à jour la configuration du scheduler.
    
    Fréquences disponibles:
    - hourly: Toutes les heures
    - daily: Une fois par jour (défaut: 06:00)
    - weekly: Une fois par semaine
    - manual: Uniquement sur déclenchement manuel
    """
    global SCHEDULER_CONFIG
    
    SCHEDULER_CONFIG["frequency"] = config.frequency
    SCHEDULER_CONFIG["time"] = config.time
    SCHEDULER_CONFIG["day_of_week"] = config.day_of_week
    SCHEDULER_CONFIG["enabled"] = config.enabled
    
    return {
        "message": "Configuration mise à jour",
        "config": SCHEDULER_CONFIG
    }


@router.post("/scheduler/run-now")
async def run_scheduler_now():
    """
    Déclenche une analyse immédiate.
    
    Lance le pipeline complet: Agent 1A → Agent 1B → Agent 2 → LLM Judge → Notifications
    """
    from src.orchestration.langgraph_workflow import run_workflow
    
    try:
        # Lancer le workflow en mode asynchrone
        # Note: Pour une vraie implémentation, utiliser une task queue (Celery, etc.)
        result = await run_workflow()
        
        SCHEDULER_CONFIG["last_run"] = datetime.utcnow().isoformat()
        
        return {
            "message": "Analyse lancée avec succès",
            "status": "running",
            "triggered_at": SCHEDULER_CONFIG["last_run"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du lancement de l'analyse: {str(e)}"
        )


# ============================================================================
# ENDPOINTS STATISTIQUES ADMIN
# ============================================================================

@router.get("/stats")
async def get_admin_stats():
    """
    Récupère les statistiques globales pour l'administration.
    """
    from src.storage.models import Document, RiskAnalysis, HutchinsonSite, Supplier
    
    session = get_session()
    try:
        # Compter les entités
        documents_count = session.query(Document).count()
        analyses_count = session.query(RiskAnalysis).count()
        sites_count = session.query(HutchinsonSite).filter_by(active=True).count()
        suppliers_count = session.query(Supplier).filter_by(active=True).count()
        
        # Sources actives
        repo = DataSourceRepository(session)
        sources = repo.get_all()
        sources_active = sum(1 for s in sources if s.is_active)
        
        return {
            "documents": {
                "total": documents_count,
            },
            "analyses": {
                "total": analyses_count,
            },
            "entities": {
                "sites": sites_count,
                "suppliers": suppliers_count
            },
            "sources": {
                "total": len(sources),
                "active": sources_active,
                "inactive": len(sources) - sources_active
            },
            "scheduler": SCHEDULER_CONFIG
        }
    finally:
        session.close()
