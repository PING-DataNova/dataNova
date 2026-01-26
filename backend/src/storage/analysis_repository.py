"""
Repository pour les analyses - Gestion de la table "analyses"
"""

import json
import structlog
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy.orm import Session

from src.storage.models import Analysis, Document

logger = structlog.get_logger()


class AnalysisRepository:
    """Repository pour les opérations CRUD sur les analyses"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(
        self,
        document_id: str,
        is_relevant: bool,
        confidence: float,
        matched_keywords: List[str] = None,
        matched_nc_codes: List[str] = None,
        llm_reasoning: str = None,
        metadata: Dict = None
    ) -> Analysis:
        """
        Crée une nouvelle analyse
        
        Args:
            document_id: ID du document analysé
            is_relevant: Le document est-il pertinent ?
            confidence: Niveau de confiance (0-1)
            matched_keywords: Mots-clés trouvés
            matched_nc_codes: Codes NC trouvés
            llm_reasoning: Explication du LLM
            metadata: Métadonnées additionnelles
            
        Returns:
            Analysis créée
        """
        analysis = Analysis(
            document_id=document_id,
            is_relevant=is_relevant,
            confidence=confidence,
            matched_keywords=matched_keywords or [],
            matched_nc_codes=matched_nc_codes or [],
            llm_reasoning=llm_reasoning,
            validation_status="pending"
        )
        
        self.session.add(analysis)
        self.session.commit()
        
        logger.info(
            "analysis_created",
            analysis_id=analysis.id[:8],
            document_id=document_id[:8],
            is_relevant=is_relevant,
            confidence=confidence
        )
        
        return analysis
    
    def save_from_document_analysis(
        self,
        document_analysis,  # DocumentAnalysis Pydantic
        document_id: str
    ) -> Analysis:
        """
        Sauvegarde une analyse depuis une DocumentAnalysis Pydantic
        
        Args:
            document_analysis: Objet DocumentAnalysis (Pydantic)
            document_id: ID du document
            
        Returns:
            Analysis sauvegardée
        """
        # Déterminer la pertinence basée sur le score final
        is_relevant = document_analysis.is_relevant
        
        # Confiance = combinaison du score final et de la confiance sémantique
        confidence = (
            document_analysis.relevance_score.final_score * 0.6 +
            document_analysis.semantic_analysis.confidence_level * 0.4
        )
        
        # Mots-clés trouvés
        matched_keywords = document_analysis.keyword_analysis.keywords_found
        
        # Codes NC trouvés
        matched_nc_codes = (
            document_analysis.nc_code_analysis.exact_matches +
            document_analysis.nc_code_analysis.partial_matches
        )
        
        # Construire le reasoning LLM
        llm_reasoning = self._build_llm_reasoning(document_analysis)
        
        # Créer l'analyse
        analysis = self.create(
            document_id=document_id,
            is_relevant=is_relevant,
            confidence=min(1.0, max(0.0, confidence)),  # Clamp 0-1
            matched_keywords=matched_keywords,
            matched_nc_codes=matched_nc_codes,
            llm_reasoning=llm_reasoning
        )
        
        # Mettre à jour le statut du document
        document = self.session.query(Document).filter_by(id=document_id).first()
        if document:
            document.workflow_status = "analyzed"
            document.analyzed_at = datetime.utcnow()
            self.session.commit()
        
        return analysis
    
    def find_by_id(self, analysis_id: str) -> Optional[Analysis]:
        """Récupère une analyse par son ID"""
        return self.session.query(Analysis).filter_by(id=analysis_id).first()
    
    def find_by_document(self, document_id: str) -> Optional[Analysis]:
        """Récupère l'analyse associée à un document"""
        return self.session.query(Analysis).filter_by(
            document_id=document_id
        ).order_by(Analysis.created_at.desc()).first()
    
    def find_all_relevant(self, limit: int = 100) -> List[Analysis]:
        """Récupère toutes les analyses pertinentes"""
        return self.session.query(Analysis).filter_by(
            is_relevant=True
        ).order_by(Analysis.created_at.desc()).limit(limit).all()
    
    def find_by_status(self, validation_status: str, limit: int = 100) -> List[Analysis]:
        """Récupère les analyses par statut de validation"""
        return self.session.query(Analysis).filter_by(
            validation_status=validation_status
        ).order_by(Analysis.created_at.desc()).limit(limit).all()
    
    def approve(self, analysis_id: str, validated_by: str = "system", comment: str = "") -> Analysis:
        """Approuve une analyse"""
        analysis = self.find_by_id(analysis_id)
        if analysis:
            analysis.validation_status = "approved"
            analysis.validated_by = validated_by
            analysis.validated_at = datetime.utcnow()
            analysis.validation_comment = comment
            self.session.commit()
            
            logger.info("analysis_approved", analysis_id=analysis_id[:8])
        
        return analysis
    
    def reject(self, analysis_id: str, validated_by: str = "system", comment: str = "") -> Analysis:
        """Rejette une analyse"""
        analysis = self.find_by_id(analysis_id)
        if analysis:
            analysis.validation_status = "rejected"
            analysis.validated_by = validated_by
            analysis.validated_at = datetime.utcnow()
            analysis.validation_comment = comment
            self.session.commit()
            
            logger.info("analysis_rejected", analysis_id=analysis_id[:8], reason=comment)
        
        return analysis
    
    def _build_llm_reasoning(self, document_analysis) -> str:
        """Construit le texte de reasoning à partir de l'analyse"""
        sections = []
        
        # Résumé de la loi
        sections.append(f"📜 Règlement:\n{document_analysis.law_explanation}\n")
        
        # Analyse sémantique
        sections.append(f"🧠 Analyse Sémantique:\n{document_analysis.semantic_analysis.explanation}\n")
        
        # Impact
        if document_analysis.impact_justification:
            sections.append(f"⚠️  Impact:\n{document_analysis.impact_justification}\n")
        
        # Processus impactés
        if document_analysis.impacted_processes:
            processes = ", ".join([p.value for p in document_analysis.impacted_processes])
            sections.append(f"🎯 Processus Impactés: {processes}\n")
        
        # Recommandations
        if document_analysis.recommended_actions:
            actions = "\n".join([f"• {a}" for a in document_analysis.recommended_actions])
            sections.append(f"💡 Actions Recommandées:\n{actions}\n")
        
        # Scores détaillés
        sections.append(
            f"📊 Scores:\n"
            f"• Mots-clés (30%): {document_analysis.relevance_score.keyword_score:.1%}\n"
            f"• Codes NC (30%): {document_analysis.relevance_score.nc_code_score:.1%}\n"
            f"• Sémantique (40%): {document_analysis.relevance_score.semantic_score:.1%}\n"
            f"• Final: {document_analysis.relevance_score.final_score:.1%}\n"
            f"• Criticité: {document_analysis.relevance_score.criticality.value}"
        )
        
        return "\n".join(sections)
