"""
Repositories (Data Access Layer)

Pattern Repository pour abstraire l'accès aux données
Documentation: docs/DATABASE_SCHEMA.md
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from src.storage.models import (
    Document,
    Analysis,
    Alert,
    ExecutionLog,
    CompanyProfile,
    CompanyProcess,
    ImpactAssessment,
)


class DocumentRepository:
    """Repository pour gérer les documents réglementaires"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, document: Document) -> Document:
        """
        Sauvegarder un document
        
        Args:
            document: Instance de Document
        
        Returns:
            Document sauvegardé avec ID
        """
        self.session.add(document)
        self.session.flush()  # Pour obtenir l'ID sans commit
        return document
    
    def find_by_id(self, document_id: str) -> Optional[Document]:
        """Trouver un document par ID"""
        return self.session.query(Document).filter(Document.id == document_id).first()
    
    def find_by_hash(self, hash_sha256: str) -> Optional[Document]:
        """
        Trouver un document par son hash SHA-256
        
        Usage: Détection de documents déjà connus ou modifiés
        
        Args:
            hash_sha256: Hash SHA-256 du contenu
        
        Returns:
            Document ou None
        """
        return self.session.query(Document)\
            .filter(Document.hash_sha256 == hash_sha256)\
            .first()
    
    def list_new_documents(self, limit: int = 50) -> List[Document]:
        """
        Lister les documents avec status='new'
        
        Args:
            limit: Nombre maximum de résultats
        
        Returns:
            Liste de documents nouveaux
        """
        return self.session.query(Document)\
            .filter(Document.status == "new")\
            .order_by(Document.first_seen.desc())\
            .limit(limit)\
            .all()
    
    def list_by_regulation_type(self, regulation_type: str) -> List[Document]:
        """
        Lister les documents par type de réglementation
        
        Args:
            regulation_type: CBAM, EUDR, CSRD, etc.
        
        Returns:
            Liste de documents
        """
        return self.session.query(Document)\
            .filter(Document.regulation_type == regulation_type)\
            .order_by(Document.publication_date.desc())\
            .all()
    
    def update_status(self, document_id: str, status: str) -> None:
        """
        Mettre à jour le statut d'un document
        
        Args:
            document_id: ID du document
            status: Nouveau statut (new, modified, unchanged)
        """
        document = self.find_by_id(document_id)
        if document:
            document.status = status
            document.last_checked = datetime.utcnow()
            self.session.flush()
    
    def count_by_status(self) -> dict:
        """
        Compter les documents par statut
        
        Returns:
            Dict {'new': 5, 'modified': 2, 'unchanged': 30}
        """
        from sqlalchemy import func
        
        results = self.session.query(
            Document.status,
            func.count(Document.id)
        ).group_by(Document.status).all()
        
        return {status: count for status, count in results}
    
    def find_by_workflow_status(self, workflow_status: str) -> List[Document]:
        """
        Trouver les documents par workflow_status
        
        Args:
            workflow_status: raw, analyzed, rejected_analysis, validated, rejected_validation
        
        Returns:
            Liste de documents
        """
        return self.session.query(Document)\
            .filter(Document.workflow_status == workflow_status)\
            .order_by(Document.created_at.desc())\
            .all()
    
    def update_workflow_status(
        self,
        document_id: str,
        workflow_status: str,
        analyzed_at: Optional[datetime] = None,
        validated_at: Optional[datetime] = None,
        validated_by: Optional[str] = None
    ) -> None:
        """
        Mettre à jour le workflow_status d'un document
        
        Args:
            document_id: ID du document
            workflow_status: Nouveau statut workflow
            analyzed_at: Date d'analyse (optionnel)
            validated_at: Date de validation (optionnel)
            validated_by: Email du validateur (optionnel)
        """
        document = self.find_by_id(document_id)
        if document:
            document.workflow_status = workflow_status
            if analyzed_at:
                document.analyzed_at = analyzed_at
            if validated_at:
                document.validated_at = validated_at
            if validated_by:
                document.validated_by = validated_by
            self.session.flush()


class AnalysisRepository:
    """Repository pour gérer les analyses de pertinence"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, analysis: Analysis) -> Analysis:
        """Sauvegarder une analyse"""
        self.session.add(analysis)
        self.session.flush()
        return analysis
    
    def find_by_id(self, analysis_id: str) -> Optional[Analysis]:
        """Trouver une analyse par ID"""
        return self.session.query(Analysis).filter(Analysis.id == analysis_id).first()
    
    def find_by_document_id(self, document_id: str) -> Optional[Analysis]:
        """
        Trouver l'analyse d'un document spécifique
        
        Args:
            document_id: ID du document
        
        Returns:
            Analyse ou None
        """
        return self.session.query(Analysis)\
            .filter(Analysis.document_id == document_id)\
            .order_by(Analysis.created_at.desc())\
            .first()
    
    def list_relevant_analyses(self, validation_status: str = "approved") -> List[Analysis]:
        """
        Lister les analyses par validation_status
        
        Args:
            validation_status: pending, approved, rejected (défaut: approved)
        
        Returns:
            Liste d'analyses
        """
        return self.session.query(Analysis)\
            .filter(Analysis.validation_status == validation_status)\
            .order_by(Analysis.created_at.desc())\
            .all()
    
    def find_by_validation_status(self, validation_status: str) -> List[Analysis]:
        """
        Trouver les analyses par validation_status
        
        Args:
            validation_status: pending, approved, rejected
        
        Returns:
            Liste d'analyses
        """
        return self.session.query(Analysis)\
            .filter(Analysis.validation_status == validation_status)\
            .order_by(Analysis.created_at.desc())\
            .all()
    
    def update_validation(
        self,
        analysis_id: str,
        approved: bool,
        comment: str,
        validated_by: str
    ) -> None:
        """
        Mettre à jour la validation d'une analyse
        
        Args:
            analysis_id: ID de l'analyse
            approved: True si approuvé, False si rejeté
            comment: Commentaire du juriste
            validated_by: Email du validateur
        """
        analysis = self.find_by_id(analysis_id)
        if analysis:
            analysis.validation_status = "approved" if approved else "rejected"
            analysis.validation_comment = comment
            analysis.validated_by = validated_by
            analysis.validated_at = datetime.utcnow()
            
            # Mettre à jour le document aussi
            if analysis.document:
                analysis.document.workflow_status = "validated" if approved else "rejected_validation"
                analysis.document.validated_at = datetime.utcnow()
                analysis.document.validated_by = validated_by
            
            self.session.flush()


class ImpactAssessmentRepository:
    """Repository pour gérer les analyses d'impact (Agent 2)"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, impact: ImpactAssessment) -> ImpactAssessment:
        """Sauvegarder une analyse d'impact"""
        self.session.add(impact)
        self.session.flush()
        return impact
    
    def find_by_id(self, impact_id: str) -> Optional[ImpactAssessment]:
        """Trouver une analyse d'impact par ID"""
        return self.session.query(ImpactAssessment)\
            .filter(ImpactAssessment.id == impact_id)\
            .first()
    
    def find_by_analysis_id(self, analysis_id: str) -> Optional[ImpactAssessment]:
        """
        Trouver l'analyse d'impact pour une analyse donnée
        
        Args:
            analysis_id: ID de l'analyse
        
        Returns:
            ImpactAssessment ou None
        """
        return self.session.query(ImpactAssessment)\
            .filter(ImpactAssessment.analysis_id == analysis_id)\
            .first()
    
    def list_by_impact_level(self, impact_level: str) -> List[ImpactAssessment]:
        """
        Lister les analyses d'impact par niveau d'impact

        Args:
            impact_level: faible, moyen, eleve

        Returns:
            Liste d'analyses d'impact
        """
        return self.session.query(ImpactAssessment)\
            .filter(ImpactAssessment.impact_level == impact_level)\
            .order_by(ImpactAssessment.created_at.desc())\
            .all()

    def list_by_risk_main(self, risk_main: str) -> List[ImpactAssessment]:
        """
        Lister les analyses d'impact par risque principal

        Args:
            risk_main: Valeur du risque principal

        Returns:
            Liste d'analyses d'impact
        """
        return self.session.query(ImpactAssessment)\
            .filter(ImpactAssessment.risk_main == risk_main)\
            .order_by(ImpactAssessment.created_at.desc())\
            .all()


class AlertRepository:
    """Repository pour gérer les alertes"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, alert: Alert) -> Alert:
        """Sauvegarder une alerte"""
        self.session.add(alert)
        self.session.flush()
        return alert
    
    def find_by_id(self, alert_id: str) -> Optional[Alert]:
        """Trouver une alerte par ID"""
        return self.session.query(Alert).filter(Alert.id == alert_id).first()
    
    def find_by_impact_assessment_id(self, impact_assessment_id: str) -> List[Alert]:
        """
        Trouver les alertes pour un impact assessment donné
        
        Args:
            impact_assessment_id: ID de l'impact assessment
        
        Returns:
            Liste d'alertes
        """
        return self.session.query(Alert)\
            .filter(Alert.impact_assessment_id == impact_assessment_id)\
            .order_by(Alert.created_at.desc())\
            .all()
    
    def list_unsent_alerts(self) -> List[Alert]:
        """
        Lister les alertes en attente d'envoi (status='pending')
        
        Returns:
            Liste d'alertes non envoyées
        """
        return self.session.query(Alert)\
            .filter(Alert.status == "pending")\
            .order_by(Alert.created_at.asc())\
            .all()
    
    def mark_as_sent(self, alert_id: str) -> None:
        """
        Marquer une alerte comme envoyée
        
        Args:
            alert_id: ID de l'alerte
        """
        alert = self.find_by_id(alert_id)
        if alert:
            alert.status = "sent"
            alert.sent_at = datetime.utcnow()
            self.session.flush()
    
    def mark_as_failed(self, alert_id: str, error_message: str) -> None:
        """
        Marquer une alerte comme échouée
        
        Args:
            alert_id: ID de l'alerte
            error_message: Message d'erreur
        """
        alert = self.find_by_id(alert_id)
        if alert:
            alert.status = "failed"
            alert.error_message = error_message
            self.session.flush()


class ExecutionLogRepository:
    """Repository pour gérer les logs d'exécution"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, log: ExecutionLog) -> ExecutionLog:
        """Sauvegarder un log d'exécution"""
        self.session.add(log)
        self.session.flush()
        return log
    
    def find_by_id(self, log_id: str) -> Optional[ExecutionLog]:
        """Trouver un log par ID"""
        return self.session.query(ExecutionLog).filter(ExecutionLog.id == log_id).first()
    
    def get_last_execution(self, agent_type: str) -> Optional[ExecutionLog]:
        """
        Récupérer la dernière exécution d'un agent
        
        Args:
            agent_type: agent_1a ou agent_1b
        
        Returns:
            Dernier log d'exécution ou None
        """
        return self.session.query(ExecutionLog)\
            .filter(ExecutionLog.agent_type == agent_type)\
            .order_by(ExecutionLog.start_time.desc())\
            .first()
    
    def list_failed_executions(self, agent_type: Optional[str] = None) -> List[ExecutionLog]:
        """
        Lister les exécutions échouées
        
        Args:
            agent_type: Filtrer par type d'agent (optionnel)
        
        Returns:
            Liste des logs d'échec
        """
        query = self.session.query(ExecutionLog)\
            .filter(ExecutionLog.status == "error")
        
        if agent_type:
            query = query.filter(ExecutionLog.agent_type == agent_type)
        
        return query.order_by(ExecutionLog.start_time.desc()).all()
    
    def complete_execution(
        self,
        log_id: str,
        status: str = "success",
        documents_processed: int = 0,
        documents_new: int = 0,
        documents_modified: int = 0,
        errors: Optional[List[str]] = None
    ) -> None:
        """
        Finaliser une exécution
        
        Args:
            log_id: ID du log
            status: success ou error
            documents_processed: Nombre total traité
            documents_new: Nombre de nouveaux
            documents_modified: Nombre de modifiés
            errors: Liste d'erreurs (optionnel)
        """
        log = self.find_by_id(log_id)
        if log:
            log.status = status
            log.end_time = datetime.utcnow()
            log.duration_seconds = (log.end_time - log.start_time).total_seconds()
            log.documents_processed = documents_processed
            log.documents_new = documents_new
            log.documents_modified = documents_modified
            log.errors = errors or []
            self.session.flush()


class CompanyProfileRepository:
    """Repository pour gérer les profils entreprise"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, profile: CompanyProfile) -> CompanyProfile:
        """Sauvegarder un profil entreprise"""
        self.session.add(profile)
        self.session.flush()
        return profile
    
    def find_by_id(self, profile_id: str) -> Optional[CompanyProfile]:
        """Trouver un profil par ID"""
        return self.session.query(CompanyProfile)\
            .filter(CompanyProfile.id == profile_id)\
            .first()
    
    def find_by_name(self, company_name: str) -> Optional[CompanyProfile]:
        """
        Trouver un profil par nom d'entreprise
        
        Args:
            company_name: Nom de l'entreprise
        
        Returns:
            Profil ou None
        """
        return self.session.query(CompanyProfile)\
            .filter(CompanyProfile.company_name == company_name)\
            .first()
    
    def list_active_profiles(self) -> List[CompanyProfile]:
        """
        Lister tous les profils actifs
        
        Returns:
            Liste de profils actifs
        """
        return self.session.query(CompanyProfile)\
            .filter(CompanyProfile.active == True)\
            .all()
    
    def update(self, profile_id: str, **kwargs) -> None:
        """
        Mettre à jour un profil
        
        Args:
            profile_id: ID du profil
            **kwargs: Champs à mettre à jour
        """
        profile = self.find_by_id(profile_id)
        if profile:
            for key, value in kwargs.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            profile.updated_at = datetime.utcnow()
            self.session.flush()

class CompanyProcessRepository:
    """Repository pour gerer les donnees entreprise (company_processes)"""

    def __init__(self, session: Session):
        self.session = session

    def save(self, process: CompanyProcess) -> CompanyProcess:
        """Sauvegarder un profil entreprise"""
        self.session.add(process)
        self.session.flush()
        return process

    def find_by_id(self, process_id: str) -> Optional[CompanyProcess]:
        """Trouver un profil par ID"""
        return self.session.query(CompanyProcess)\
            .filter(CompanyProcess.id == process_id)\
            .first()

    def find_by_name(self, company_name: str) -> Optional[CompanyProcess]:
        """Trouver un profil par nom d'entreprise"""
        return self.session.query(CompanyProcess)\
            .filter(CompanyProcess.company_name == company_name)\
            .first()

    def list_all(self) -> List[CompanyProcess]:
        """Lister tous les profils"""
        return self.session.query(CompanyProcess)\
            .order_by(CompanyProcess.created_at.desc())\
            .all()

    def update(self, process_id: str, **kwargs) -> None:
        """Mettre a jour un profil"""
        process = self.find_by_id(process_id)
        if process:
            for key, value in kwargs.items():
                if hasattr(process, key):
                    setattr(process, key, value)
            process.updated_at = datetime.utcnow()
            self.session.flush()

