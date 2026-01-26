"""
Scorer de pertinence - Agrège les 3 scores et détermine la criticité

Combine les résultats des 3 filtres pour produire un score final.
"""

import structlog
import uuid
from typing import Dict, List
from datetime import datetime

from src.agent_1b.models import (
    KeywordAnalysisResult,
    NCCodeAnalysisResult,
    SemanticAnalysisResult,
    RelevanceScore,
    Criticality,
    ImpactedProcess,
    DocumentAnalysis,
    AnalysisAlert
)

logger = structlog.get_logger()


class RelevanceScorer:
    """Calcule le score de pertinence final et détermine la criticité"""
    
    def __init__(
        self,
        keyword_weight: float = 0.30,
        nc_code_weight: float = 0.30,
        semantic_weight: float = 0.40,
        thresholds: Dict[str, float] = None
    ):
        """
        Args:
            keyword_weight: Poids du score mots-clés (défaut: 30%)
            nc_code_weight: Poids du score codes NC (défaut: 30%)
            semantic_weight: Poids du score sémantique (défaut: 40%)
            thresholds: Seuils de criticité personnalisés
        """
        self.keyword_weight = keyword_weight
        self.nc_code_weight = nc_code_weight
        self.semantic_weight = semantic_weight
        
        # Seuils par défaut pour la criticité
        self.thresholds = thresholds or {
            "critical": 0.80,
            "high": 0.60,
            "medium": 0.40,
            "low": 0.20
        }
    
    def calculate_score(
        self,
        keyword_result: KeywordAnalysisResult,
        nc_code_result: NCCodeAnalysisResult,
        semantic_result: SemanticAnalysisResult
    ) -> RelevanceScore:
        """
        Calcule le score final pondéré
        
        Args:
            keyword_result: Résultat de l'analyse mots-clés
            nc_code_result: Résultat de l'analyse codes NC
            semantic_result: Résultat de l'analyse sémantique
            
        Returns:
            RelevanceScore avec score final et criticité
        """
        logger.info("calculating_relevance_score")
        
        # Calcul du score pondéré
        final_score = (
            keyword_result.score * self.keyword_weight +
            nc_code_result.score * self.nc_code_weight +
            semantic_result.score * self.semantic_weight
        )
        
        # Arrondir à 3 décimales
        final_score = round(final_score, 3)
        
        # Déterminer la criticité basée sur le score
        criticality = self._determine_criticality(final_score, nc_code_result, semantic_result)
        
        logger.info(
            "relevance_score_calculated",
            final_score=final_score,
            criticality=criticality.value,
            keyword_score=keyword_result.score,
            nc_code_score=nc_code_result.score,
            semantic_score=semantic_result.score
        )
        
        return RelevanceScore(
            final_score=final_score,
            keyword_score=keyword_result.score,
            nc_code_score=nc_code_result.score,
            semantic_score=semantic_result.score,
            keyword_weight=self.keyword_weight,
            nc_code_weight=self.nc_code_weight,
            semantic_weight=self.semantic_weight,
            criticality=criticality
        )
    
    def _determine_criticality(
        self,
        score: float,
        nc_code_result: NCCodeAnalysisResult,
        semantic_result: SemanticAnalysisResult
    ) -> Criticality:
        """
        Détermine la criticité basée sur le score et d'autres facteurs
        
        Facteurs considérés:
        - Score global
        - Présence de codes NC critiques
        - Niveau d'applicabilité sémantique
        """
        # Boost si codes critiques trouvés
        has_critical_codes = len(nc_code_result.critical_codes) > 0
        
        # Boost si très applicable selon LLM
        high_applicability = semantic_result.is_applicable and semantic_result.score > 0.7
        
        # Déterminer criticité de base
        if score >= self.thresholds["critical"]:
            base_criticality = Criticality.CRITICAL
        elif score >= self.thresholds["high"]:
            base_criticality = Criticality.HIGH
        elif score >= self.thresholds["medium"]:
            base_criticality = Criticality.MEDIUM
        elif score >= self.thresholds["low"]:
            base_criticality = Criticality.LOW
        else:
            base_criticality = Criticality.NOT_RELEVANT
        
        # Upgrade criticité si conditions spéciales
        if has_critical_codes and base_criticality == Criticality.HIGH:
            return Criticality.CRITICAL
        
        if high_applicability and base_criticality == Criticality.MEDIUM:
            return Criticality.HIGH
        
        return base_criticality
    
    def identify_impacted_processes(
        self,
        semantic_result: SemanticAnalysisResult,
        regulation_type: str
    ) -> List[ImpactedProcess]:
        """
        Identifie les processus impactés basés sur l'analyse
        
        Args:
            semantic_result: Résultat de l'analyse sémantique
            regulation_type: Type de réglementation (CBAM, EUDR, etc.)
            
        Returns:
            Liste des processus impactés
        """
        processes = []
        
        # Logique basée sur le type de réglementation
        if regulation_type == "CBAM":
            processes.extend([
                ImpactedProcess.CUSTOMS_TRADE,
                ImpactedProcess.ESG_COMPLIANCE,
                ImpactedProcess.PROCUREMENT
            ])
        
        elif regulation_type == "EUDR":
            processes.extend([
                ImpactedProcess.SUPPLY_CHAIN,
                ImpactedProcess.ESG_COMPLIANCE,
                ImpactedProcess.PROCUREMENT
            ])
        
        elif regulation_type == "CSRD":
            processes.extend([
                ImpactedProcess.ESG_COMPLIANCE,
                ImpactedProcess.FINANCE
            ])
        
        # Analyser les obligations identifiées pour affiner
        obligations_text = " ".join(semantic_result.obligations_identified).lower()
        
        if "douane" in obligations_text or "customs" in obligations_text:
            if ImpactedProcess.CUSTOMS_TRADE not in processes:
                processes.append(ImpactedProcess.CUSTOMS_TRADE)
        
        if "qualité" in obligations_text or "quality" in obligations_text:
            if ImpactedProcess.QUALITY not in processes:
                processes.append(ImpactedProcess.QUALITY)
        
        if "déclaration" in obligations_text or "reporting" in obligations_text:
            if ImpactedProcess.ESG_COMPLIANCE not in processes:
                processes.append(ImpactedProcess.ESG_COMPLIANCE)
        
        if "fournisseur" in obligations_text or "supplier" in obligations_text:
            if ImpactedProcess.SUPPLY_CHAIN not in processes:
                processes.append(ImpactedProcess.SUPPLY_CHAIN)
        
        if "production" in obligations_text or "manufacturing" in obligations_text:
            if ImpactedProcess.PRODUCTION not in processes:
                processes.append(ImpactedProcess.PRODUCTION)
        
        if "juridique" in obligations_text or "legal" in obligations_text:
            if ImpactedProcess.LEGAL not in processes:
                processes.append(ImpactedProcess.LEGAL)
        
        return processes if processes else [ImpactedProcess.UNKNOWN]


def create_document_analysis(
    document_id: str,
    company_profile_id: str,
    document_title: str,
    regulation_type: str,
    keyword_result: KeywordAnalysisResult,
    nc_code_result: NCCodeAnalysisResult,
    semantic_result: SemanticAnalysisResult,
    scorer: RelevanceScorer = None
) -> DocumentAnalysis:
    """
    Crée une analyse complète du document
    
    Args:
        document_id: ID du document
        company_profile_id: ID du profil entreprise
        document_title: Titre du document
        regulation_type: Type de réglementation
        keyword_result: Résultat analyse mots-clés
        nc_code_result: Résultat analyse codes NC
        semantic_result: Résultat analyse sémantique
        scorer: Scorer personnalisé (optionnel)
        
    Returns:
        DocumentAnalysis complète
    """
    if scorer is None:
        scorer = RelevanceScorer()
    
    # Calculer le score final
    relevance_score = scorer.calculate_score(keyword_result, nc_code_result, semantic_result)
    
    # Identifier les processus impactés
    impacted_processes = scorer.identify_impacted_processes(semantic_result, regulation_type)
    primary_process = impacted_processes[0] if impacted_processes else ImpactedProcess.UNKNOWN
    
    # Déterminer si pertinent
    is_relevant = relevance_score.final_score >= scorer.thresholds["low"]
    
    # Générer résumé exécutif
    executive_summary = _generate_executive_summary(
        document_title,
        relevance_score,
        semantic_result,
        impacted_processes
    )
    
    # Actions recommandées désactivées
    recommended_actions = []
    
    return DocumentAnalysis(
        document_id=document_id,
        company_profile_id=company_profile_id,
        keyword_analysis=keyword_result,
        nc_code_analysis=nc_code_result,
        semantic_analysis=semantic_result,
        relevance_score=relevance_score,
        impacted_processes=impacted_processes,
        primary_impact_process=primary_process,
        executive_summary=executive_summary,
        law_explanation=semantic_result.regulation_summary,
        impact_justification=semantic_result.impact_explanation,
        recommended_actions=recommended_actions,
        is_relevant=is_relevant,
        workflow_status="analyzed"
    )


def _generate_executive_summary(
    document_title: str,
    relevance_score: RelevanceScore,
    semantic_result: SemanticAnalysisResult,
    impacted_processes: List[ImpactedProcess]
) -> str:
    """Génère un résumé exécutif de l'analyse"""
    
    criticality_text = {
        Criticality.CRITICAL: "CRITIQUE - Action immédiate requise",
        Criticality.HIGH: "ÉLEVÉE - Attention prioritaire",
        Criticality.MEDIUM: "MOYENNE - Suivi recommandé",
        Criticality.LOW: "FAIBLE - Information",
        Criticality.NOT_RELEVANT: "NON PERTINENT"
    }
    
    processes_text = ", ".join([p.value for p in impacted_processes[:3]])
    
    summary = f"""Analyse du document: {document_title}

CRITICITÉ: {criticality_text[relevance_score.criticality]}
SCORE DE PERTINENCE: {relevance_score.final_score * 100:.1f}%

PROCESSUS IMPACTÉS: {processes_text}

{semantic_result.regulation_summary}

{semantic_result.impact_explanation if semantic_result.impact_explanation else "Impact à évaluer en détail."}
"""
    
    return summary.strip()


def _extract_recommendations(
    semantic_result: SemanticAnalysisResult,
    criticality: Criticality,
    regulation_type: str
) -> List[str]:
    """Extrait les recommandations d'action"""
    
    recommendations = []
    
    # Recommandations basées sur les obligations identifiées
    if semantic_result.obligations_identified:
        recommendations.extend(semantic_result.obligations_identified[:3])
    
    # Recommandations génériques basées sur la criticité
    if criticality == Criticality.CRITICAL:
        recommendations.append("Convoquer une réunion d'urgence avec les parties prenantes")
        recommendations.append("Évaluer l'impact financier et opérationnel immédiat")
    
    elif criticality == Criticality.HIGH:
        recommendations.append("Planifier une analyse d'impact détaillée")
        recommendations.append("Informer la direction et les départements concernés")
    
    elif criticality == Criticality.MEDIUM:
        recommendations.append("Suivre l'évolution de la réglementation")
        recommendations.append("Documenter les impacts potentiels")
    
    # Recommandations spécifiques par type
    if regulation_type == "CBAM":
        recommendations.append("Vérifier les émissions carbone des fournisseurs concernés")
    elif regulation_type == "EUDR":
        recommendations.append("Audit de traçabilité de la chaîne d'approvisionnement")
    
    return recommendations[:5]  # Limiter à 5 recommandations


def create_alert(
    analysis: DocumentAnalysis,
    contact_emails: List[str] = None
) -> AnalysisAlert:
    """
    Crée une alerte à partir d'une analyse
    
    Args:
        analysis: Analyse du document
        contact_emails: Emails destinataires (optionnel)
        
    Returns:
        AnalysisAlert
    """
    alert_id = str(uuid.uuid4())
    
    # Titre de l'alerte
    title = f"[{analysis.relevance_score.criticality.value}] Nouvelle réglementation pertinente"
    
    # Résumé court
    summary = f"""Score: {analysis.relevance_score.final_score * 100:.1f}%
Processus: {analysis.primary_impact_process.value if analysis.primary_impact_process else 'Unknown'}

{analysis.law_explanation[:200]}...
"""
    
    return AnalysisAlert(
        alert_id=alert_id,
        document_id=analysis.document_id,
        company_profile_id=analysis.company_profile_id,
        criticality=analysis.relevance_score.criticality,
        title=title,
        summary=summary.strip(),
        impacted_processes=analysis.impacted_processes,
        recommended_actions=analysis.recommended_actions,
        score=analysis.relevance_score.final_score,
        sent_to=contact_emails or [],
        metadata={
            "keyword_score": analysis.relevance_score.keyword_score,
            "nc_code_score": analysis.relevance_score.nc_code_score,
            "semantic_score": analysis.relevance_score.semantic_score
        }
    )
