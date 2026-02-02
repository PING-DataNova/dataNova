"""
SQLAlchemy Models pour PING - Version Finale Complète

Ce fichier contient tous les modèles de données pour le système PING.
Architecture: 3 types de risques + projection géographique + validation qualité
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column, String, DateTime, Text, JSON, Boolean, Float, Integer, ForeignKey, Date
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_uuid():
    """Génère un UUID v4 comme string"""
    return str(uuid4())


# ============================================================================
# CONSTANTS (Valeurs acceptées pour les champs String)
# ============================================================================

# Types d'événements surveillés
EVENT_TYPES = ["reglementaire", "climatique", "geopolitique"]

# Sous-types d'événements
EVENT_SUBTYPES_REG = ["CBAM", "EUDR", "CRCD", "REACH", "autre"]
EVENT_SUBTYPES_CLI = ["inondation", "tempete", "secheresse", "incendie", "autre"]
EVENT_SUBTYPES_GEO = ["conflit", "sanction", "instabilite", "greve", "autre"]

# Résultats possibles de l'analyse de pertinence (Agent 1B)
PERTINENCE_RESULTS = ["OUI", "NON", "PARTIELLEMENT"]

# Niveaux de risque
RISK_LEVELS = ["Faible", "Moyen", "Fort", "Critique"]

# Niveaux d'impact supply chain
SUPPLY_CHAIN_IMPACTS = ["aucun", "faible", "moyen", "fort", "critique"]

# Actions recommandées par le LLM Judge
JUDGE_ACTIONS = ["APPROVE", "REVIEW", "REJECT"]

# Taille de l'entreprise/fournisseur
COMPANY_SIZES = ["PME", "ETI", "Grand groupe"]

# Criticité de la relation fournisseur
CRITICALITY_LEVELS = ["Critique", "Important", "Standard"]

# Importance stratégique des sites
STRATEGIC_IMPORTANCE = ["faible", "moyen", "fort", "critique"]

# Santé financière
FINANCIAL_HEALTH = ["excellent", "bon", "moyen", "faible"]

# Sévérité des alertes
ALERT_SEVERITIES = ["info", "low", "medium", "high", "critical"]

# Statuts des alertes
ALERT_STATUSES = ["new", "acknowledged", "in_progress", "resolved", "dismissed"]

# Canaux de notification
NOTIFICATION_CHANNELS = ["email", "sms", "push", "in_app"]

# Statuts des notifications
NOTIFICATION_STATUSES = ["pending", "sent", "delivered", "failed"]

# Rôles utilisateurs
USER_ROLES = ["admin", "analyst", "viewer"]

# Tolérance au risque
RISK_TOLERANCES = ["low", "medium", "high"]


# ============================================================================
# DOCUMENTS & COLLECTE (Agent 1A)
# ============================================================================

class Document(Base):
    """
    Documents collectés par Agent 1A (réglementaires, climatiques, géopolitiques)
    """
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String(500), nullable=False)
    source_url = Column(String(1000), nullable=False)
    event_type = Column(String(50), nullable=False)  # reglementaire, climatique, geopolitique
    event_subtype = Column(String(100), nullable=True)  # CBAM, inondation, conflit, etc.
    publication_date = Column(DateTime, nullable=True)
    collection_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    hash_sha256 = Column(String(64), unique=True, nullable=False)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    geographic_scope = Column(JSON, nullable=True)  # {countries: [], regions: [], coordinates: {}}
    extra_metadata = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, default="new")  # new, modified, unchanged
    first_seen = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_checked = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    pertinence_check = relationship("PertinenceCheck", back_populates="document", uselist=False)
    risk_analysis = relationship("RiskAnalysis", back_populates="document", uselist=False)
    alerts = relationship("Alert", back_populates="document")
    ground_truth_case = relationship("GroundTruthCase", back_populates="document", uselist=False)


# ============================================================================
# DONNÉES MÉTIER HUTCHINSON
# ============================================================================

class HutchinsonSite(Base):
    """
    Sites de production Hutchinson (80-90 sites)
    """
    __tablename__ = "hutchinson_sites"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    country = Column(String(100), nullable=False)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    sectors = Column(JSON, nullable=True)  # ["automotive", "aerospace", ...]
    products = Column(JSON, nullable=True)  # ["joints", "tuyaux", ...]
    raw_materials = Column(JSON, nullable=True)  # ["caoutchouc", "plastique", ...]
    certifications = Column(JSON, nullable=True)  # ["ISO 9001", "ISO 14001", ...]
    employee_count = Column(Integer, nullable=True)
    annual_production_value = Column(Float, nullable=True)  # en euros
    strategic_importance = Column(String(20), nullable=True)  # faible, moyen, fort, critique
    extra_metadata = Column(JSON, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    supplier_relationships = relationship("SupplierRelationship", back_populates="hutchinson_site")


class Supplier(Base):
    """
    Fournisseurs d'Hutchinson
    """
    __tablename__ = "suppliers"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    country = Column(String(100), nullable=False)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    sector = Column(String(100), nullable=False)
    products_supplied = Column(JSON, nullable=False)  # ["composants", "matières premières", ...]
    company_size = Column(String(20), nullable=True)  # PME, ETI, Grand groupe
    certifications = Column(JSON, nullable=True)
    financial_health = Column(String(20), nullable=True)  # excellent, bon, moyen, faible
    extra_metadata = Column(JSON, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    supplier_relationships = relationship(
        "SupplierRelationship",
        foreign_keys="SupplierRelationship.supplier_id",
        back_populates="supplier"
    )

class SupplierRelationship(Base):
    """
    Relations entre sites Hutchinson et fournisseurs
    """
    __tablename__ = "supplier_relationships"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    hutchinson_site_id = Column(String, ForeignKey("hutchinson_sites.id"), nullable=False)
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=False)
    products_supplied = Column(JSON, nullable=False)  # Produits fournis à ce site
    annual_volume = Column(Float, nullable=True)  # Volume annuel en euros
    criticality = Column(String(20), nullable=False)  # Critique, Important, Standard
    is_sole_supplier = Column(Boolean, default=False)  # Fournisseur unique pour ce produit
    has_backup_supplier = Column(Boolean, default=False)  # Existe-t-il un fournisseur de secours
    backup_supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=True)
    lead_time_days = Column(Integer, nullable=True)  # Délai de livraison en jours
    contract_end_date = Column(Date, nullable=True)
    risk_mitigation_plan = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    hutchinson_site = relationship("HutchinsonSite", back_populates="supplier_relationships")
    supplier = relationship("Supplier", back_populates="supplier_relationships", foreign_keys=[supplier_id])


# ============================================================================
# PIPELINE D'ANALYSE
# ============================================================================

class PertinenceCheck(Base):
    """
    Résultats de l'Agent 1B (Pertinence Checker)
    """
    __tablename__ = "pertinence_checks"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, unique=True)
    
    decision = Column(String(20), nullable=False)  # OUI, NON, PARTIELLEMENT
    confidence = Column(Float, nullable=False)  # 0-1
    reasoning = Column(Text, nullable=False)
    matched_elements = Column(JSON, nullable=True)  # Éléments pertinents identifiés
    affected_sites = Column(JSON, nullable=True)  # Sites Hutchinson concernés
    affected_suppliers = Column(JSON, nullable=True)  # Fournisseurs concernés
    llm_model = Column(String(50), nullable=False)  # ex: "claude-3-5-sonnet-20241022"
    llm_tokens = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    analysis_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relations
    document = relationship("Document", back_populates="pertinence_check")
    risk_analysis = relationship("RiskAnalysis", back_populates="pertinence_check", uselist=False)
    ground_truth_results = relationship("GroundTruthResult", back_populates="pertinence_check")


class RiskAnalysis(Base):
    """
    Résultats de l'Agent 2 (Risk Analyzer)
    Inclut la projection géographique et l'analyse de criticité
    """
    __tablename__ = "risk_analyses"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, unique=True)
    pertinence_check_id = Column(String, ForeignKey("pertinence_checks.id"), nullable=False, unique=True)
    
    impacts_description = Column(Text, nullable=False)
    affected_sites = Column(JSON, nullable=True)  # [{site_id, distance_km, impact_level, ...}, ...]
    affected_suppliers = Column(JSON, nullable=True)  # [{supplier_id, distance_km, impact_level, ...}, ...]
    geographic_analysis = Column(JSON, nullable=True)  # Détails de l'analyse géographique
    criticality_analysis = Column(JSON, nullable=True)  # Détails de l'analyse de criticité
    risk_level = Column(String(20), nullable=False)  # Faible, Moyen, Fort, Critique
    risk_score = Column(Float, nullable=False)  # 0-10
    supply_chain_impact = Column(String(20), nullable=False)  # aucun, faible, moyen, fort, critique
    recommendations = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=False)
    llm_model = Column(String(50), nullable=False)
    llm_tokens = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    analysis_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relations
    document = relationship("Document", back_populates="risk_analysis")
    pertinence_check = relationship("PertinenceCheck", back_populates="risk_analysis")
    judge_evaluation = relationship("JudgeEvaluation", back_populates="risk_analysis", uselist=False)
    alerts = relationship("Alert", back_populates="risk_analysis")
    ground_truth_results = relationship("GroundTruthResult", back_populates="risk_analysis")


class JudgeEvaluation(Base):
    """
    Résultats du LLM Judge (validation qualité)
    """
    __tablename__ = "judge_evaluations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    risk_analysis_id = Column(String, ForeignKey("risk_analyses.id"), nullable=False, unique=True)
    
    score_completeness = Column(Float, nullable=False)  # 0-10
    score_accuracy = Column(Float, nullable=False)  # 0-10
    score_relevance = Column(Float, nullable=False)  # 0-10
    score_clarity = Column(Float, nullable=False)  # 0-10
    score_actionability = Column(Float, nullable=False)  # 0-10
    score_traceability = Column(Float, nullable=False)  # 0-10
    
    overall_score = Column(Float, nullable=False)  # 0-10
    action = Column(String(20), nullable=False)  # APPROVE, REVIEW, REJECT
    reasoning = Column(Text, nullable=False)
    improvement_suggestions = Column(JSON, nullable=True)
    llm_model = Column(String(50), nullable=False)
    llm_tokens = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relations
    risk_analysis = relationship("RiskAnalysis", back_populates="judge_evaluation")
    alerts = relationship("Alert", back_populates="judge_evaluation")


# ============================================================================
# ALERTES MÉTÉO (Agent 1A - Collecte Climatique)
# ============================================================================

class WeatherAlert(Base):
    """
    Alertes météorologiques collectées par Agent 1A.
    Source: Open-Meteo API
    Objectif: Anticiper les risques supply chain liés à la météo
    """
    __tablename__ = "weather_alerts"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    
    # Localisation
    site_id = Column(String(50), nullable=False)  # ID du site (ex: FR-LEH-MFG1)
    site_name = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(10), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    site_type = Column(String(50), nullable=True)  # manufacturing, supplier, port, hq
    site_criticality = Column(String(20), nullable=True)  # critical, high, normal, low
    
    # Alerte
    alert_type = Column(String(50), nullable=False)  # snow, heavy_rain, extreme_heat, extreme_cold, strong_wind, storm
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    alert_date = Column(Date, nullable=False)  # Date de l'événement météo
    
    # Données météo
    value = Column(Float, nullable=False)  # Valeur mesurée
    threshold = Column(Float, nullable=False)  # Seuil dépassé
    unit = Column(String(20), nullable=False)  # mm, cm, °C, km/h
    
    # Description
    description = Column(Text, nullable=False)
    supply_chain_risk = Column(Text, nullable=False)  # Risque supply chain associé
    
    # Prévisions complètes (optionnel)
    forecast_data = Column(JSON, nullable=True)  # Données météo brutes sur 16 jours
    
    # Métadonnées
    status = Column(String(20), nullable=False, default="new")  # new, acknowledged, resolved
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# PROJECTIONS DE RISQUE PAR ENTITÉ (Agent 2)
# ============================================================================

class RiskProjection(Base):
    """
    Projection de l'impact d'un événement (document) sur une entité spécifique.
    Chaque document pertinent génère N projections (1 par site/fournisseur concerné).
    
    Objectif: Permettre l'analyse granulaire de l'impact par entité.
    """
    __tablename__ = "risk_projections"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    event_id = Column(String, ForeignKey("documents.id"), nullable=False)
    entity_id = Column(String, nullable=False)  # ID du site ou fournisseur
    entity_type = Column(String(20), nullable=False)  # "site" ou "supplier"
    
    # Scores de risque
    risk_score = Column(Float, nullable=False)  # Score de risque 0-100
    impact_score = Column(Float, nullable=True)  # Score d'impact opérationnel
    business_interruption_score = Column(Float, nullable=True)  # Score d'interruption d'activité
    
    # Détails
    is_concerned = Column(Boolean, nullable=False, default=False)  # L'entité est-elle concernée ?
    reasoning = Column(Text, nullable=True)  # Explication textuelle de l'impact
    estimated_disruption_days = Column(Integer, nullable=True)  # Jours d'interruption estimés
    revenue_impact_percentage = Column(Float, nullable=True)  # % d'impact sur le CA
    
    # Sous-scores pour 360° Risk Score
    severity_score = Column(Float, nullable=True)
    probability_score = Column(Float, nullable=True)
    exposure_score = Column(Float, nullable=True)
    urgency_score = Column(Float, nullable=True)
    
    # Métadonnées
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relations
    document = relationship("Document", backref="risk_projections")


# ============================================================================
# ALERTES & NOTIFICATIONS
# ============================================================================

class Alert(Base):
    """
    Alertes générées par le système
    """
    __tablename__ = "alerts"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    risk_analysis_id = Column(String, ForeignKey("risk_analyses.id"), nullable=False)
    judge_evaluation_id = Column(String, ForeignKey("judge_evaluations.id"), nullable=True)
    
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)  # info, low, medium, high, critical
    affected_sites = Column(JSON, nullable=True)
    affected_suppliers = Column(JSON, nullable=True)
    recommendations = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="new")  # new, acknowledged, in_progress, resolved, dismissed
    assigned_to = Column(String, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    document = relationship("Document", back_populates="alerts")
    risk_analysis = relationship("RiskAnalysis", back_populates="alerts")
    judge_evaluation = relationship("JudgeEvaluation", back_populates="alerts")
    assigned_user = relationship("User", back_populates="assigned_alerts", foreign_keys=[assigned_to])
    notifications = relationship("Notification", back_populates="alert")


class Notification(Base):
    """
    Notifications envoyées aux utilisateurs
    """
    __tablename__ = "notifications"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    alert_id = Column(String, ForeignKey("alerts.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    channel = Column(String(20), nullable=False)  # email, sms, push, in_app
    status = Column(String(20), nullable=False, default="pending")  # pending, sent, delivered, failed
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relations
    alert = relationship("Alert", back_populates="notifications")
    user = relationship("User", back_populates="notifications")


# ============================================================================
# GROUND TRUTH (Amélioration Continue)
# ============================================================================

class GroundTruthCase(Base):
    """
    Cas de référence validés par des experts
    """
    __tablename__ = "ground_truth_cases"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, unique=True)
    
    expert_pertinence_decision = Column(String(20), nullable=False)  # OUI, NON, PARTIELLEMENT
    expert_pertinence_reasoning = Column(Text, nullable=False)
    expert_risk_level = Column(String(20), nullable=False)  # Faible, Moyen, Fort, Critique
    expert_affected_sites = Column(JSON, nullable=True)
    expert_affected_suppliers = Column(JSON, nullable=True)
    expert_recommendations = Column(Text, nullable=False)
    expert_name = Column(String(200), nullable=False)
    validated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    extra_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relations
    document = relationship("Document", back_populates="ground_truth_case")
    ground_truth_results = relationship("GroundTruthResult", back_populates="ground_truth_case")


class GroundTruthResult(Base):
    """
    Comparaison des résultats LLM avec les résultats experts
    """
    __tablename__ = "ground_truth_results"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    ground_truth_case_id = Column(String, ForeignKey("ground_truth_cases.id"), nullable=False)
    pertinence_check_id = Column(String, ForeignKey("pertinence_checks.id"), nullable=False)
    risk_analysis_id = Column(String, ForeignKey("risk_analyses.id"), nullable=False)
    
    pertinence_match = Column(Boolean, nullable=False)  # Décision pertinence correspond
    risk_level_match = Column(Boolean, nullable=False)  # Niveau de risque correspond
    sites_match_score = Column(Float, nullable=False)  # Score de correspondance sites (0-1)
    suppliers_match_score = Column(Float, nullable=False)  # Score de correspondance fournisseurs (0-1)
    overall_match_score = Column(Float, nullable=False)  # Score global de correspondance (0-1)
    discrepancies = Column(JSON, nullable=True)  # Écarts détaillés
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relations
    ground_truth_case = relationship("GroundTruthCase", back_populates="ground_truth_results")
    pertinence_check = relationship("PertinenceCheck", back_populates="ground_truth_results")
    risk_analysis = relationship("RiskAnalysis", back_populates="ground_truth_results")


# ============================================================================
# UTILISATEURS & CONFIGURATION
# ============================================================================

class User(Base):
    """
    Utilisateurs du système
    """
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, default="viewer")  # admin, analyst, viewer
    department = Column(String(100), nullable=True)
    notification_preferences = Column(JSON, nullable=True)
    active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    assigned_alerts = relationship("Alert", back_populates="assigned_user", foreign_keys="Alert.assigned_to")
    notifications = relationship("Notification", back_populates="user")


class CompanyProfile(Base):
    """
    Configuration globale d'Hutchinson
    """
    __tablename__ = "company_profile"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    company_name = Column(String(200), nullable=False)
    headquarters_country = Column(String(100), nullable=False)
    total_sites = Column(Integer, nullable=True)
    total_suppliers = Column(Integer, nullable=True)
    risk_tolerance = Column(String(20), nullable=False, default="medium")  # low, medium, high
    notification_settings = Column(JSON, nullable=True)
    data_sources_config = Column(JSON, nullable=True)  # Configuration des sources de données
    llm_config = Column(JSON, nullable=True)  # Configuration des LLM
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# LOGS D'EXÉCUTION (pour monitoring)
# ============================================================================

class ExecutionLog(Base):
    """
    Logs d'exécution des agents (pour monitoring et debugging)
    """
    __tablename__ = "execution_logs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    agent_name = Column(String(50), nullable=False)  # agent_1a, agent_1b, agent_2, judge
    document_id = Column(String, nullable=True)
    status = Column(String(20), nullable=False)  # success, error, warning
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ============================================================================
# ANALYSES PONCTUELLES FOURNISSEURS (Agent 1A - Mode Supplier)
# ============================================================================

class SupplierAnalysis(Base):
    """
    Analyses ponctuelles de risques fournisseurs.
    Stocke les résultats des analyses déclenchées manuellement par l'utilisateur
    via l'interface "Analyse de risques fournisseur".
    """
    __tablename__ = "supplier_analyses"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    
    # Informations fournisseur (saisies par l'utilisateur)
    supplier_name = Column(String(200), nullable=False)
    country = Column(String(100), nullable=False)
    city = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    nc_codes = Column(JSON, nullable=True)  # ["4001", "400121", "400122"]
    materials = Column(JSON, nullable=True)  # ["Caoutchouc naturel", "Latex"]
    criticality = Column(String(20), nullable=False)  # Critique, Important, Standard
    annual_volume = Column(Float, nullable=True)  # Volume annuel en euros
    
    # Résultats de l'analyse réglementaire
    regulatory_risks_count = Column(Integer, default=0)
    regulatory_risks = Column(JSON, nullable=True)  # Liste des documents EUR-Lex pertinents
    
    # Résultats de l'analyse météorologique
    weather_risks_count = Column(Integer, default=0)
    weather_risks = Column(JSON, nullable=True)  # Alertes météo sur 16 jours
    
    # Score et niveau de risque global
    risk_score = Column(Float, nullable=True)  # Score global 0-10
    risk_level = Column(String(20), nullable=True)  # Faible, Moyen, Fort, Critique
    
    # Recommandations générées
    recommendations = Column(JSON, nullable=True)  # Liste de recommandations
    
    # Métadonnées
    requested_by = Column(String, ForeignKey("users.id"), nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending, completed, error
    error_message = Column(Text, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    extra_metadata = Column(JSON, nullable=True)  # Données additionnelles (ex: document_ids)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    requested_by_user = relationship("User", foreign_keys=[requested_by])


# ============================================================================
# ALIAS POUR COMPATIBILITÉ AVEC ANCIEN CODE
# ============================================================================

# Alias pour compatibilité avec les routes API existantes
Analysis = PertinenceCheck
ImpactAssessment = RiskAnalysis
