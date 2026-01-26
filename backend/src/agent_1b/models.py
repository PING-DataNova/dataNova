"""
Modèles Pydantic pour l'Agent 1B - Analyse de pertinence

Ces modèles garantissent la structure et la validité des résultats d'analyse.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime


class Criticality(str, Enum):
    """Niveaux de criticité pour une réglementation"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NOT_RELEVANT = "NOT_RELEVANT"


class ImpactedProcess(str, Enum):
    """Processus internes potentiellement impactés"""
    PROCUREMENT = "Procurement"
    CUSTOMS_TRADE = "Customs & Trade"
    ESG_COMPLIANCE = "ESG & Compliance"
    QUALITY = "Quality"
    SUPPLY_CHAIN = "Supply Chain"
    LEGAL = "Legal"
    FINANCE = "Finance"
    PRODUCTION = "Production"
    HSE = "HSE (Health, Safety, Environment)"
    IT_DATA = "IT & Data"
    UNKNOWN = "Unknown"


class KeywordAnalysisResult(BaseModel):
    """Résultat de l'analyse par mots-clés (Niveau 1)"""
    
    score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Score de densité des mots-clés (0-1)"
    )
    
    keywords_found: List[str] = Field(
        default_factory=list,
        description="Liste des mots-clés trouvés dans le document"
    )
    
    total_keywords_searched: int = Field(
        ...,
        ge=0,
        description="Nombre total de mots-clés recherchés"
    )
    
    keyword_density: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Ratio mots-clés trouvés / mots-clés totaux"
    )
    
    context_snippets: Dict[str, str] = Field(
        default_factory=dict,
        description="Contexte autour de chaque mot-clé trouvé"
    )


class NCCodeAnalysisResult(BaseModel):
    """Résultat de l'analyse par codes NC (Niveau 2)"""
    
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score basé sur les codes NC trouvés"
    )
    
    nc_codes_found: List[str] = Field(
        default_factory=list,
        description="Codes NC/SH trouvés dans le document"
    )
    
    exact_matches: List[str] = Field(
        default_factory=list,
        description="Codes avec correspondance exacte"
    )
    
    partial_matches: List[str] = Field(
        default_factory=list,
        description="Codes avec correspondance partielle (ex: 4001 vs 4001.22)"
    )
    
    critical_codes: List[str] = Field(
        default_factory=list,
        description="Codes critiques pour l'entreprise"
    )
    
    context_snippets: Dict[str, str] = Field(
        default_factory=dict,
        description="Contexte autour de chaque code NC trouvé"
    )


class SemanticAnalysisResult(BaseModel):
    """Résultat de l'analyse sémantique LLM (Niveau 3)"""
    
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score de pertinence sémantique (0-1)"
    )
    
    is_applicable: bool = Field(
        ...,
        description="Le document est-il applicable à l'entreprise ?"
    )
    
    explanation: str = Field(
        ...,
        min_length=50,
        description="Explication détaillée de l'analyse LLM"
    )
    
    regulation_summary: str = Field(
        ...,
        min_length=20,
        description="Résumé de ce que dit la loi/réglementation"
    )
    
    impact_explanation: str = Field(
        default="",
        description="Pourquoi et comment cela impacte l'entreprise"
    )
    
    obligations_identified: List[str] = Field(
        default_factory=list,
        description="Obligations ou actions requises identifiées"
    )
    
    products_inferred: List[str] = Field(
        default_factory=list,
        description="Produits/matériaux identifiés même sans code NC explicite"
    )
    
    geographical_scope: List[str] = Field(
        default_factory=list,
        description="Pays/régions concernés mentionnés"
    )
    
    confidence_level: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Niveau de confiance de l'analyse LLM"
    )


class RelevanceScore(BaseModel):
    """Score de pertinence final agrégé"""
    
    final_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score final pondéré (0-1)"
    )
    
    keyword_score: float = Field(..., ge=0.0, le=1.0)
    nc_code_score: float = Field(..., ge=0.0, le=1.0)
    semantic_score: float = Field(..., ge=0.0, le=1.0)
    
    keyword_weight: float = Field(default=0.30, description="Poids mots-clés")
    nc_code_weight: float = Field(default=0.30, description="Poids codes NC")
    semantic_weight: float = Field(default=0.40, description="Poids sémantique")
    
    criticality: Criticality = Field(
        ...,
        description="Niveau de criticité déterminé"
    )
    
    @field_validator('final_score', mode='before')
    @classmethod
    def validate_final_score(cls, v, info):
        """Valider que le score final est cohérent"""
        if v < 0.0 or v > 1.0:
            raise ValueError("Le score final doit être entre 0 et 1")
        return round(v, 3)


class DocumentAnalysis(BaseModel):
    """Analyse complète d'un document par l'Agent 1B"""
    
    # Métadonnées
    document_id: str = Field(..., description="ID du document analysé")
    company_profile_id: str = Field(..., description="ID du profil entreprise")
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Date/heure de l'analyse"
    )
    
    # Résultats des 3 niveaux d'analyse
    keyword_analysis: KeywordAnalysisResult
    nc_code_analysis: NCCodeAnalysisResult
    semantic_analysis: SemanticAnalysisResult
    
    # Score et criticité finaux
    relevance_score: RelevanceScore
    
    # Impact et recommandations
    impacted_processes: List[ImpactedProcess] = Field(
        default_factory=list,
        description="Processus/départements impactés"
    )
    
    primary_impact_process: Optional[ImpactedProcess] = Field(
        None,
        description="Processus principal impacté"
    )
    
    # Explication globale
    executive_summary: str = Field(
        ...,
        min_length=100,
        description="Résumé exécutif de l'analyse"
    )
    
    law_explanation: str = Field(
        ...,
        min_length=50,
        description="Explication de ce que dit la loi"
    )
    
    impact_justification: str = Field(
        ...,
        min_length=50,
        description="Justification de l'impact sur l'entreprise"
    )
    
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="Actions recommandées"
    )
    
    # Métadonnées techniques
    is_relevant: bool = Field(
        ...,
        description="Le document est-il pertinent ? (score > seuil)"
    )
    
    workflow_status: str = Field(
        default="analyzed",
        description="Statut dans le workflow"
    )
    
    @field_validator('is_relevant', mode='before')
    @classmethod
    def determine_relevance(cls, v, info):
        """Déterminer si le document est pertinent basé sur le score"""
        # La pertinence sera déterminée par le scorer
        return v


class AnalysisAlert(BaseModel):
    """Alerte générée pour un document pertinent"""
    
    alert_id: str = Field(..., description="ID unique de l'alerte")
    document_id: str = Field(..., description="ID du document source")
    company_profile_id: str = Field(..., description="ID du profil entreprise")
    
    criticality: Criticality
    title: str = Field(..., min_length=10, description="Titre de l'alerte")
    summary: str = Field(..., min_length=50, description="Résumé de l'alerte")
    
    impacted_processes: List[ImpactedProcess]
    recommended_actions: List[str] = Field(default_factory=list)
    
    score: float = Field(..., ge=0.0, le=1.0)
    
    created_at: datetime = Field(default_factory=datetime.now)
    sent_to: List[str] = Field(default_factory=list, description="Emails destinataires")
    
    metadata: Dict = Field(default_factory=dict, description="Métadonnées additionnelles")
