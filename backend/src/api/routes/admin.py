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
    from src.orchestration.langgraph_workflow import run_ping_workflow
    import asyncio
    
    try:
        # Lancer le workflow en mode synchrone dans un thread séparé
        # pour ne pas bloquer l'event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            lambda: run_ping_workflow(keyword="CBAM", max_documents=8, company_name="HUTCHINSON")
        )
        
        SCHEDULER_CONFIG["last_run"] = datetime.utcnow().isoformat()
        
        return {
            "message": "Analyse lancée avec succès",
            "status": "completed",
            "triggered_at": SCHEDULER_CONFIG["last_run"],
            "result": {
                "documents_collected": len(result.get("documents_collected", [])),
                "pertinent": len(result.get("documents_pertinent", [])),
                "risk_analyses": len(result.get("risk_analyses", [])),
                "notifications_sent": len(result.get("notifications_sent", []))
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
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


# ============================================================================
# ENDPOINTS GESTION DES FOURNISSEURS
# ============================================================================

class SupplierCreate(BaseModel):
    """Schéma pour créer un fournisseur"""
    name: str = Field(..., min_length=2, max_length=200, description="Nom du fournisseur")
    code: str = Field(..., min_length=2, max_length=50, description="Code unique")
    country: str = Field(..., description="Pays")
    region: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sector: str = Field(..., description="Secteur d'activité")
    products_supplied: List[str] = Field(..., description="Produits fournis")
    company_size: Optional[str] = Field(None, description="PME, ETI, Grand groupe")
    certifications: Optional[List[str]] = None
    financial_health: Optional[str] = Field(None, description="excellent, bon, moyen, faible")
    criticality_score: Optional[int] = Field(None, ge=1, le=10, description="Score de criticité 1-10")
    active: bool = True


class SupplierUpdate(BaseModel):
    """Schéma pour mettre à jour un fournisseur"""
    name: Optional[str] = None
    code: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sector: Optional[str] = None
    products_supplied: Optional[List[str]] = None
    company_size: Optional[str] = None
    certifications: Optional[List[str]] = None
    financial_health: Optional[str] = None
    criticality_score: Optional[int] = None
    active: Optional[bool] = None


class SupplierResponse(BaseModel):
    """Schéma de réponse pour un fournisseur"""
    id: str
    name: str
    code: str
    country: str
    region: Optional[str]
    city: Optional[str]
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    sector: str
    products_supplied: List[str]
    company_size: Optional[str]
    certifications: Optional[List[str]]
    financial_health: Optional[str]
    criticality_score: Optional[int]
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/suppliers", response_model=List[SupplierResponse])
async def list_suppliers(active_only: bool = False):
    """Liste tous les fournisseurs"""
    from src.storage.models import Supplier
    
    session = get_session()
    try:
        query = session.query(Supplier)
        if active_only:
            query = query.filter(Supplier.active == True)
        suppliers = query.order_by(Supplier.name).all()
        return suppliers
    finally:
        session.close()


@router.post("/suppliers", response_model=SupplierResponse, status_code=201)
async def create_supplier(supplier: SupplierCreate):
    """Crée un nouveau fournisseur"""
    from src.storage.models import Supplier
    
    session = get_session()
    try:
        # Vérifier si le code existe déjà
        existing = session.query(Supplier).filter(Supplier.code == supplier.code).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Un fournisseur avec le code '{supplier.code}' existe déjà"
            )
        
        new_supplier = Supplier(
            name=supplier.name,
            code=supplier.code,
            country=supplier.country,
            region=supplier.region,
            city=supplier.city,
            address=supplier.address,
            latitude=supplier.latitude,
            longitude=supplier.longitude,
            sector=supplier.sector,
            products_supplied=supplier.products_supplied,
            company_size=supplier.company_size,
            certifications=supplier.certifications,
            financial_health=supplier.financial_health,
            criticality_score=supplier.criticality_score,
            active=supplier.active
        )
        
        session.add(new_supplier)
        session.commit()
        session.refresh(new_supplier)
        
        return new_supplier
    finally:
        session.close()


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: str):
    """Récupère les détails d'un fournisseur"""
    from src.storage.models import Supplier
    
    session = get_session()
    try:
        supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
        return supplier
    finally:
        session.close()


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(supplier_id: str, update: SupplierUpdate):
    """Met à jour un fournisseur"""
    from src.storage.models import Supplier
    
    session = get_session()
    try:
        supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
        
        # Vérifier l'unicité du code si modifié
        if update.code and update.code != supplier.code:
            existing = session.query(Supplier).filter(Supplier.code == update.code).first()
            if existing:
                raise HTTPException(status_code=400, detail=f"Le code '{update.code}' est déjà utilisé")
        
        update_data = update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(supplier, key):
                setattr(supplier, key, value)
        
        supplier.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(supplier)
        
        return supplier
    finally:
        session.close()


@router.delete("/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str):
    """Supprime un fournisseur"""
    from src.storage.models import Supplier
    
    session = get_session()
    try:
        supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
        
        session.delete(supplier)
        session.commit()
        
        return {"message": "Fournisseur supprimé avec succès", "id": supplier_id}
    finally:
        session.close()


@router.post("/suppliers/{supplier_id}/toggle", response_model=SupplierResponse)
async def toggle_supplier(supplier_id: str):
    """Active ou désactive un fournisseur"""
    from src.storage.models import Supplier
    
    session = get_session()
    try:
        supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
        
        supplier.active = not supplier.active
        supplier.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(supplier)
        
        return supplier
    finally:
        session.close()


# ============================================================================
# ENDPOINTS GESTION DES SITES HUTCHINSON
# ============================================================================

class SiteCreate(BaseModel):
    """Schéma pour créer un site Hutchinson"""
    name: str = Field(..., min_length=2, max_length=200, description="Nom du site")
    code: str = Field(..., min_length=2, max_length=50, description="Code unique")
    country: str = Field(..., description="Pays")
    region: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sectors: Optional[List[str]] = Field(None, description="Secteurs: automotive, aerospace...")
    products: Optional[List[str]] = Field(None, description="Produits fabriqués")
    raw_materials: Optional[List[str]] = Field(None, description="Matières premières utilisées")
    certifications: Optional[List[str]] = None
    employee_count: Optional[int] = None
    annual_production_value: Optional[float] = Field(None, description="CA annuel en euros")
    strategic_importance: Optional[str] = Field(None, description="faible, moyen, fort, critique")
    daily_revenue: Optional[float] = Field(None, description="CA journalier en euros")
    active: bool = True


class SiteUpdate(BaseModel):
    """Schéma pour mettre à jour un site"""
    name: Optional[str] = None
    code: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sectors: Optional[List[str]] = None
    products: Optional[List[str]] = None
    raw_materials: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    employee_count: Optional[int] = None
    annual_production_value: Optional[float] = None
    strategic_importance: Optional[str] = None
    daily_revenue: Optional[float] = None
    active: Optional[bool] = None


class SiteResponse(BaseModel):
    """Schéma de réponse pour un site"""
    id: str
    name: str
    code: str
    country: str
    region: Optional[str]
    city: Optional[str]
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    sectors: Optional[List[str]]
    products: Optional[List[str]]
    raw_materials: Optional[List[str]]
    certifications: Optional[List[str]]
    employee_count: Optional[int]
    annual_production_value: Optional[float]
    strategic_importance: Optional[str]
    daily_revenue: Optional[float]
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/sites", response_model=List[SiteResponse])
async def list_sites(active_only: bool = False):
    """Liste tous les sites Hutchinson"""
    from src.storage.models import HutchinsonSite
    
    session = get_session()
    try:
        query = session.query(HutchinsonSite)
        if active_only:
            query = query.filter(HutchinsonSite.active == True)
        sites = query.order_by(HutchinsonSite.name).all()
        return sites
    finally:
        session.close()


@router.post("/sites", response_model=SiteResponse, status_code=201)
async def create_site(site: SiteCreate):
    """Crée un nouveau site Hutchinson"""
    from src.storage.models import HutchinsonSite
    
    session = get_session()
    try:
        # Vérifier si le code existe déjà
        existing = session.query(HutchinsonSite).filter(HutchinsonSite.code == site.code).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Un site avec le code '{site.code}' existe déjà"
            )
        
        new_site = HutchinsonSite(
            name=site.name,
            code=site.code,
            country=site.country,
            region=site.region,
            city=site.city,
            address=site.address,
            latitude=site.latitude,
            longitude=site.longitude,
            sectors=site.sectors,
            products=site.products,
            raw_materials=site.raw_materials,
            certifications=site.certifications,
            employee_count=site.employee_count,
            annual_production_value=site.annual_production_value,
            strategic_importance=site.strategic_importance,
            daily_revenue=site.daily_revenue,
            active=site.active
        )
        
        session.add(new_site)
        session.commit()
        session.refresh(new_site)
        
        return new_site
    finally:
        session.close()


@router.get("/sites/{site_id}", response_model=SiteResponse)
async def get_site(site_id: str):
    """Récupère les détails d'un site"""
    from src.storage.models import HutchinsonSite
    
    session = get_session()
    try:
        site = session.query(HutchinsonSite).filter(HutchinsonSite.id == site_id).first()
        if not site:
            raise HTTPException(status_code=404, detail="Site non trouvé")
        return site
    finally:
        session.close()


@router.put("/sites/{site_id}", response_model=SiteResponse)
async def update_site(site_id: str, update: SiteUpdate):
    """Met à jour un site Hutchinson"""
    from src.storage.models import HutchinsonSite
    
    session = get_session()
    try:
        site = session.query(HutchinsonSite).filter(HutchinsonSite.id == site_id).first()
        if not site:
            raise HTTPException(status_code=404, detail="Site non trouvé")
        
        # Vérifier l'unicité du code si modifié
        if update.code and update.code != site.code:
            existing = session.query(HutchinsonSite).filter(HutchinsonSite.code == update.code).first()
            if existing:
                raise HTTPException(status_code=400, detail=f"Le code '{update.code}' est déjà utilisé")
        
        update_data = update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(site, key):
                setattr(site, key, value)
        
        site.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(site)
        
        return site
    finally:
        session.close()


@router.delete("/sites/{site_id}")
async def delete_site(site_id: str):
    """Supprime un site Hutchinson"""
    from src.storage.models import HutchinsonSite
    
    session = get_session()
    try:
        site = session.query(HutchinsonSite).filter(HutchinsonSite.id == site_id).first()
        if not site:
            raise HTTPException(status_code=404, detail="Site non trouvé")
        
        session.delete(site)
        session.commit()
        
        return {"message": "Site supprimé avec succès", "id": site_id}
    finally:
        session.close()


@router.post("/sites/{site_id}/toggle", response_model=SiteResponse)
async def toggle_site(site_id: str):
    """Active ou désactive un site"""
    from src.storage.models import HutchinsonSite
    
    session = get_session()
    try:
        site = session.query(HutchinsonSite).filter(HutchinsonSite.id == site_id).first()
        if not site:
            raise HTTPException(status_code=404, detail="Site non trouvé")
        
        site.active = not site.active
        site.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(site)
        
        return site
    finally:
        session.close()


# ============================================================================
# ENDPOINTS GESTION DES UTILISATEURS
# ============================================================================

class UserResponse(BaseModel):
    """Schéma de réponse pour un utilisateur"""
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    department: Optional[str] = None
    active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schéma pour mettre à jour un utilisateur"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    active: Optional[bool] = None


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    status: Optional[str] = None,
    active_only: bool = False
):
    """
    Liste tous les utilisateurs.
    
    - **status**: Filtrer par statut (pending, approved, rejected) - basé sur active
    - **active_only**: Si True, retourne uniquement les utilisateurs actifs
    """
    from src.storage.models import User
    
    session = get_session()
    try:
        query = session.query(User)
        
        if active_only:
            query = query.filter(User.active == True)
        elif status == 'pending':
            # Les utilisateurs "pending" sont ceux qui n'ont jamais été connectés
            query = query.filter(User.last_login == None, User.active == True)
        elif status == 'approved':
            # Les utilisateurs "approved" sont actifs et se sont déjà connectés
            query = query.filter(User.last_login != None, User.active == True)
        elif status == 'rejected':
            # Les utilisateurs "rejected" sont inactifs
            query = query.filter(User.active == False)
        
        users = query.order_by(User.created_at.desc()).all()
        return users
    finally:
        session.close()


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Récupère les détails d'un utilisateur"""
    from src.storage.models import User
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        return user
    finally:
        session.close()


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, update: UserUpdate):
    """Met à jour un utilisateur"""
    from src.storage.models import User
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        update_data = update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(user)
        
        return user
    finally:
        session.close()


@router.post("/users/{user_id}/approve", response_model=UserResponse)
async def approve_user(user_id: str):
    """Approuve un utilisateur (active son compte)"""
    from src.storage.models import User
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        user.active = True
        user.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(user)
        
        return user
    finally:
        session.close()


@router.post("/users/{user_id}/reject", response_model=UserResponse)
async def reject_user(user_id: str):
    """Rejette un utilisateur (désactive son compte)"""
    from src.storage.models import User
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        user.active = False
        user.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(user)
        
        return user
    finally:
        session.close()


@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """Supprime un utilisateur"""
    from src.storage.models import User
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        session.delete(user)
        session.commit()
        
        return {"message": "Utilisateur supprimé avec succès", "id": user_id}
    finally:
        session.close()
