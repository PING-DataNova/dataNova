"""
Agent autonome 1B - Analyse et scoring

Analyse la pertinence des documents collectés par l'Agent 1A avec une approche triangulée :
- 30% Analyse par mots-clés
- 30% Analyse par codes NC
- 40% Analyse sémantique LLM

Utilise Pydantic pour garantir la fiabilité des données.
Sauvegarde les résultats en BDD + affichage Rich.
"""

import structlog
import json
from typing import Dict, List, Optional
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax

from src.agent_1b.models import (
    DocumentAnalysis,
    AnalysisAlert,
    Criticality
)
from src.agent_1b.tools.keyword_filter import analyze_keywords
from src.agent_1b.tools.nc_code_filter import analyze_nc_codes
from src.agent_1b.tools.semantic_analyzer import analyze_semantically
from src.agent_1b.tools.relevance_scorer import (
    RelevanceScorer,
    create_document_analysis,
    create_alert
)
from src.storage.database import get_session
from src.storage.analysis_repository import AnalysisRepository
from src.storage.models import Document, CompanyProfile
from src.storage.repositories import DocumentRepository

logger = structlog.get_logger()


class Agent1B:
    """
    Agent 1B - Analyseur de pertinence réglementaire
    
    Reçoit un document brut de l'Agent 1A et détermine :
    1. Est-ce pertinent pour l'entreprise ?
    2. Quelle est l'urgence (criticité) ?
    3. Quels départements sont impactés ?
    """
    
    def __init__(self, company_profile: Dict):
        """
        Args:
            company_profile: Profil entreprise (dict depuis JSON)
        """
        self.company_profile = company_profile
        self.company_name = company_profile.get("company_name", "Unknown")
        self.scorer = RelevanceScorer()
        
        logger.info("agent_1b_initialized", company=self.company_name)
    
    def analyze_document(
        self,
        document_id: str,
        document_content: str,
        document_title: str,
        regulation_type: str = "CBAM"
    ) -> DocumentAnalysis:
        """
        Analyse complète d'un document
        
        Args:
            document_id: ID du document à analyser
            document_content: Contenu textuel du document
            document_title: Titre du document
            regulation_type: Type de réglementation (CBAM, EUDR, etc.)
            
        Returns:
            DocumentAnalysis avec scores, criticité et recommandations
        """
        logger.info(
            "agent_1b_analysis_started",
            document_id=document_id[:8],
            title=document_title[:60],
            regulation_type=regulation_type
        )
        
        # ====================================================================
        # NIVEAU 1 : ANALYSE MOTS-CLÉS (30%)
        # ====================================================================
        logger.info("level_1_keyword_analysis")
        
        company_keywords = self.company_profile.get("keywords", [])
        keyword_result = analyze_keywords(document_content, company_keywords)
        
        logger.info(
            "level_1_completed",
            score=keyword_result.score,
            keywords_found=len(keyword_result.keywords_found)
        )
        
        # ====================================================================
        # NIVEAU 2 : ANALYSE CODES NC (30%)
        # ====================================================================
        logger.info("level_2_nc_code_analysis")
        
        company_nc_codes = self._extract_nc_codes_from_profile()
        nc_code_result = analyze_nc_codes(
            document_content,
            company_nc_codes,
            critical_codes=self._get_critical_nc_codes()
        )
        
        logger.info(
            "level_2_completed",
            score=nc_code_result.score,
            nc_codes_found=len(nc_code_result.nc_codes_found),
            critical_codes=len(nc_code_result.critical_codes)
        )
        
        # ====================================================================
        # NIVEAU 3 : ANALYSE SÉMANTIQUE LLM (40%)
        # ====================================================================
        logger.info("level_3_semantic_analysis")
        
        semantic_result = analyze_semantically(
            document_content,
            document_title,
            regulation_type,
            self.company_profile
        )
        
        logger.info(
            "level_3_completed",
            score=semantic_result.score,
            is_applicable=semantic_result.is_applicable,
            confidence=semantic_result.confidence_level
        )
        
        # ====================================================================
        # AGRÉGATION ET SCORING FINAL
        # ====================================================================
        logger.info("aggregating_scores")
        
        analysis = create_document_analysis(
            document_id=document_id,
            company_profile_id=self.company_profile.get("company_id", "unknown"),
            document_title=document_title,
            regulation_type=regulation_type,
            keyword_result=keyword_result,
            nc_code_result=nc_code_result,
            semantic_result=semantic_result,
            scorer=self.scorer
        )
        
        logger.info(
            "agent_1b_analysis_completed",
            document_id=document_id[:8],
            final_score=analysis.relevance_score.final_score,
            criticality=analysis.relevance_score.criticality.value,
            is_relevant=analysis.is_relevant
        )
        
        return analysis
    
    def _extract_nc_codes_from_profile(self) -> List[str]:
        """Extrait tous les codes NC du profil entreprise"""
        nc_codes = []
        
        # Format simple : liste directe
        if isinstance(self.company_profile.get("nc_codes"), list):
            nc_codes = self.company_profile["nc_codes"]
        
        # Format structuré : imports + exports
        elif isinstance(self.company_profile.get("nc_codes"), dict):
            nc_dict = self.company_profile["nc_codes"]
            
            for imp in nc_dict.get("imports", []):
                if isinstance(imp, dict):
                    nc_codes.append(imp.get("code", ""))
                else:
                    nc_codes.append(str(imp))
            
            for exp in nc_dict.get("exports", []):
                if isinstance(exp, dict):
                    nc_codes.append(exp.get("code", ""))
                else:
                    nc_codes.append(str(exp))
        
        # Nettoyer et dédupliquer
        nc_codes = list(set(filter(None, nc_codes)))
        
        return nc_codes
    
    def _get_critical_nc_codes(self) -> List[str]:
        """Identifie les codes NC critiques pour l'entreprise"""
        # Pour l'instant, retourne une liste vide
        # À améliorer avec une logique métier
        return []


def run_agent_1b_on_document(
    document_id: str,
    company_profile_path: str = "data/company_profiles/Hutchinson_SA.json"
) -> DocumentAnalysis:
    """
    Exécute l'Agent 1B sur un document depuis la base de données
    
    Args:
        document_id: ID du document à analyser
        company_profile_path: Chemin vers le profil entreprise JSON
        
    Returns:
        DocumentAnalysis
    """
    logger.info("loading_company_profile", path=company_profile_path)
    
    # Charger le profil entreprise
    with open(company_profile_path, 'r', encoding='utf-8') as f:
        company_profile_data = json.load(f)
    
    # Extraire le nom de l'entreprise
    company_name = (
        company_profile_data.get("company", {}).get("company_name") or
        company_profile_data.get("company_name") or
        "HUTCHINSON"
    )
    
    # Préparer le profil pour l'agent
    profile = {
        "company_id": company_profile_data.get("company", {}).get("company_id", "HUT-001"),
        "company_name": company_name,
        "industry": company_profile_data.get("company", {}).get("industry", {}).get("sector", ""),
        "products": company_profile_data.get("products", []),
        "nc_codes": company_profile_data.get("nc_codes", {}),
        "keywords": _extract_keywords_from_profile(company_profile_data),
        "regulations": _extract_regulations_from_profile(company_profile_data),
        "countries": _extract_countries_from_profile(company_profile_data)
    }
    
    # Récupérer le document depuis la base
    session = get_session()
    repo = DocumentRepository(session)
    
    try:
        document = repo.find_by_id(document_id)
        
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Créer l'agent
        agent = Agent1B(profile)
        
        # Analyser le document
        analysis = agent.analyze_document(
            document_id=document.id,
            document_content=document.content or "",
            document_title=document.title,
            regulation_type=document.regulation_type or "CBAM"
        )
        
        return analysis
        
    finally:
        session.close()


def _extract_keywords_from_profile(profile_data: Dict) -> List[str]:
    """Extrait ou génère les mots-clés depuis le profil"""
    keywords = profile_data.get("keywords", [])
    
    if keywords and isinstance(keywords, list):
        return keywords
    
    # Générer depuis les produits et l'industrie
    keywords_set = set()
    
    # Depuis produits
    for product in profile_data.get("products", []):
        if "caoutchouc" in product.lower() or "rubber" in product.lower():
            keywords_set.add("caoutchouc")
        if "aluminium" in product.lower():
            keywords_set.add("aluminium")
        if "joint" in product.lower() or "seal" in product.lower():
            keywords_set.add("étanchéité")
    
    # Depuis industry
    industry = profile_data.get("company", {}).get("industry", {})
    for segment in industry.get("segments", []):
        if isinstance(segment, str):
            words = segment.lower().split()
            keywords_set.update([w for w in words if len(w) > 4])
    
    return list(keywords_set)[:15]


def _extract_regulations_from_profile(profile_data: Dict) -> List[str]:
    """Extrait la liste des réglementations suivies"""
    regulations = []
    
    regs_data = profile_data.get("regulations", {})
    
    if isinstance(regs_data, dict):
        for level in ["critical", "high", "medium"]:
            for reg in regs_data.get(level, []):
                if isinstance(reg, dict):
                    name = reg.get("name") or reg.get("full_name", "")
                    if name:
                        regulations.append(name)
                elif reg:
                    regulations.append(reg)
    elif isinstance(regs_data, list):
        regulations = regs_data
    
    return regulations or ["CBAM", "EUDR", "CSRD"]


def _extract_countries_from_profile(profile_data: Dict) -> str:
    """Extrait les pays d'opération"""
    countries = set()
    
    # Depuis sites
    for site in profile_data.get("sites", []):
        country = site.get("country")
        if country:
            countries.add(country)
    
    # Depuis locations
    for location in profile_data.get("locations", {}).get("production_sites", []):
        country = location.get("country")
        if country:
            countries.add(country)
    
    return ", ".join(sorted(countries)) if countries else "EU, US, IN"
