"""
Repositories (Data Access Layer)

Pattern Repository pour abstraire l'accès aux données
Documentation: docs/DATABASE_SCHEMA.md
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from src.storage.models import Document, Analysis, Alert, ExecutionLog, CompanyProfile, ImpactAssessment


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

    def find_by_url(self, source_url: str) -> Optional[Document]:
        """
        Trouver un document par son URL source
        
        Usage: Vérifier si un document existe déjà (utilisé par change_detector)
        
        Args:
            source_url: URL source du document (EUR-Lex)
        
        Returns:
            Document ou None
        """
        return self.session.query(Document)\
            .filter(Document.source_url == source_url)\
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
    
    def upsert_document(
        self,
        source_url: str,
        hash_sha256: str,
        title: str,
        content: str,
        nc_codes: List[str],
        regulation_type: str,
        publication_date: Optional[datetime] = None,
        document_metadata: Optional[dict] = None
    ) -> tuple[Document, str]:
        """
        Insert ou Update un document (détection automatique nouveau/modifié/inchangé)
        
        Logique:
        1. Chercher par hash → Si trouvé = contenu inchangé
        2. Chercher par URL → Si trouvé = contenu modifié
        3. Sinon → Nouveau document
        
        Args:
            source_url: URL source du document
            hash_sha256: Hash SHA-256 du contenu
            title: Titre du document
            content: Contenu extrait
            nc_codes: Liste des codes NC trouvés
            regulation_type: Type de réglementation (CBAM, EUDR, etc.)
            publication_date: Date de publication (optionnel)
            document_metadata: Métadonnées diverses (optionnel)
        
        Returns:
            Tuple (Document, status) où status = "new" | "modified" | "unchanged"
        
        Usage Agent 1A:
            doc, status = repo.upsert_document(
                source_url=url,
                hash_sha256=hash,
                title=title,
                content=text,
                nc_codes=codes,
                regulation_type="CBAM"
            )
            print(f"Document {status}: {doc.title}")
        """
        # Étape 1: Chercher par hash (contenu identique ?)
        existing = self.find_by_hash(hash_sha256)
        
        if existing:
            # Document existe avec même contenu = inchangé
            existing.last_checked = datetime.utcnow()
            existing.status = "unchanged"
            self.session.flush()
            return (existing, "unchanged")
        
        # Étape 2: Chercher par URL (même document, contenu différent ?)
        existing_url = self.find_by_url(source_url)
        
        if existing_url:
            # Document modifié (nouveau contenu)
            existing_url.hash_sha256 = hash_sha256
            existing_url.content = content
            existing_url.nc_codes = nc_codes
            existing_url.title = title
            existing_url.publication_date = publication_date
            existing_url.document_metadata = document_metadata or {}
            existing_url.status = "modified"
            existing_url.workflow_status = "raw"  # À réanalyser
            existing_url.last_checked = datetime.utcnow()
            self.session.flush()
            return (existing_url, "modified")
        
        # Étape 3: Nouveau document
        from src.storage.models import Document as DocumentModel
        
        doc = DocumentModel(
            title=title,
            source_url=source_url,
            hash_sha256=hash_sha256,
            content=content,
            nc_codes=nc_codes,
            regulation_type=regulation_type,
            publication_date=publication_date,
            document_metadata=document_metadata or {},
            status="new",
            workflow_status="raw"
        )
        self.session.add(doc)
        self.session.flush()
        return (doc, "new")
    
    def commit(self) -> None:
        """
        Helper pour commit la transaction
        
        Usage:
            doc, status = repo.upsert_document(...)
            repo.commit()
        """
        self.session.commit()
    
    def rollback(self) -> None:
        """
        Helper pour rollback la transaction en cas d'erreur
        
        Usage:
            try:
                doc = repo.upsert_document(...)
                repo.commit()
            except Exception:
                repo.rollback()
                raise
        """
        self.session.rollback()


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
    
    def find_by_document_id(self, document_id: str) -> List[Analysis]:
        """Trouver les analyses pour un document"""
        return self.session.query(Analysis)\
            .filter(Analysis.document_id == document_id)\
            .order_by(Analysis.created_at.desc())\
            .all()
    
    def find_by_validation_status(self, validation_status: str) -> List[Analysis]:
        """
        Trouver les analyses par statut de validation
        
        Args:
            validation_status: pending, approved, rejected
        
        Returns:
            Liste d'analyses
        """
        return self.session.query(Analysis)\
            .filter(Analysis.validation_status == validation_status)\
            .order_by(Analysis.created_at.desc())\
            .all()
    
    def update_validation_status(
        self,
        analysis_id: str,
        validation_status: str,
        validation_comment: Optional[str] = None,
        validated_by: Optional[str] = None
    ) -> None:
        """
        Mettre à jour le statut de validation
        
        Args:
            analysis_id: ID de l'analyse
            validation_status: pending, approved, rejected
            validation_comment: Commentaire du validateur
            validated_by: Email du validateur
        """
        analysis = self.find_by_id(analysis_id)
        if analysis:
            analysis.validation_status = validation_status
            if validation_comment:
                analysis.validation_comment = validation_comment
            if validated_by:
                analysis.validated_by = validated_by
            analysis.validated_at = datetime.utcnow()
            self.session.flush()
    
    def commit(self) -> None:
        """Commit la transaction"""
        self.session.commit()
    
    def rollback(self) -> None:
        """Rollback la transaction"""
        self.session.rollback()


class ImpactAssessmentRepository:
    """Repository pour gérer les analyses d'impact"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, impact_assessment: ImpactAssessment) -> ImpactAssessment:
        """Sauvegarder une analyse d'impact"""
        self.session.add(impact_assessment)
        self.session.flush()
        return impact_assessment
    
    def find_by_id(self, impact_assessment_id: str) -> Optional[ImpactAssessment]:
        """Trouver une analyse d'impact par ID"""
        return self.session.query(ImpactAssessment)\
            .filter(ImpactAssessment.id == impact_assessment_id)\
            .first()
    
    def find_by_analysis_id(self, analysis_id: str) -> List[ImpactAssessment]:
        """Trouver les analyses d'impact pour une analyse"""
        return self.session.query(ImpactAssessment)\
            .filter(ImpactAssessment.analysis_id == analysis_id)\
            .all()
    
    def find_by_criticality(self, criticality: str) -> List[ImpactAssessment]:
        """
        Trouver les analyses d'impact par criticité
        
        Args:
            criticality: CRITICAL, HIGH, MEDIUM, LOW
        
        Returns:
            Liste d'analyses d'impact
        """
        return self.session.query(ImpactAssessment)\
            .filter(ImpactAssessment.criticality == criticality)\
            .order_by(ImpactAssessment.total_score.desc())\
            .all()
    
    def commit(self) -> None:
        """Commit la transaction"""
        self.session.commit()
    
    def rollback(self) -> None:
        """Rollback la transaction"""
        self.session.rollback()


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
    
    def find_pending_alerts(self) -> List[Alert]:
        """Trouver les alertes en attente d'envoi"""
        return self.session.query(Alert)\
            .filter(Alert.status == "pending")\
            .order_by(Alert.created_at.asc())\
            .all()
    
    def update_status(self, alert_id: str, status: str, error_message: Optional[str] = None) -> None:
        """
        Mettre à jour le statut d'une alerte
        
        Args:
            alert_id: ID de l'alerte
            status: pending, sent, failed
            error_message: Message d'erreur si applicable
        """
        alert = self.find_by_id(alert_id)
        if alert:
            alert.status = status
            if status == "sent":
                alert.sent_at = datetime.utcnow()
            if error_message:
                alert.error_message = error_message
            self.session.flush()
    
    def commit(self) -> None:
        """Commit la transaction"""
        self.session.commit()
    
    def rollback(self) -> None:
        """Rollback la transaction"""
        self.session.rollback()


class ExecutionLogRepository:
    """Repository pour gérer les logs d'exécution"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, execution_log: ExecutionLog) -> ExecutionLog:
        """Sauvegarder un log d'exécution"""
        self.session.add(execution_log)
        self.session.flush()
        return execution_log
    
    def find_by_id(self, execution_log_id: str) -> Optional[ExecutionLog]:
        """Trouver un log par ID"""
        return self.session.query(ExecutionLog).filter(ExecutionLog.id == execution_log_id).first()
    
    def find_by_agent_type(self, agent_type: str) -> List[ExecutionLog]:
        """
        Trouver les logs pour un type d'agent
        
        Args:
            agent_type: agent_1a, agent_1b, agent_2
        
        Returns:
            Liste de logs
        """
        return self.session.query(ExecutionLog)\
            .filter(ExecutionLog.agent_type == agent_type)\
            .order_by(ExecutionLog.start_time.desc())\
            .all()
    
    def commit(self) -> None:
        """Commit la transaction"""
        self.session.commit()
    
    def rollback(self) -> None:
        """Rollback la transaction"""
        self.session.rollback()


class CompanyProfileRepository:
    """Repository pour gérer les profils entreprise"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, company_profile: CompanyProfile) -> CompanyProfile:
        """Sauvegarder un profil entreprise"""
        self.session.add(company_profile)
        self.session.flush()
        return company_profile
    
    def find_by_id(self, profile_id: str) -> Optional[CompanyProfile]:
        """Trouver un profil par ID"""
        return self.session.query(CompanyProfile).filter(CompanyProfile.id == profile_id).first()
    
    def find_by_name(self, company_name: str) -> Optional[CompanyProfile]:
        """Trouver un profil par nom d'entreprise"""
        return self.session.query(CompanyProfile)\
            .filter(CompanyProfile.company_name == company_name)\
            .first()
    
    def find_active_profiles(self) -> List[CompanyProfile]:
        """Trouver tous les profils actifs"""
        return self.session.query(CompanyProfile)\
            .filter(CompanyProfile.active == True)\
            .all()
    
    def commit(self) -> None:
        """Commit la transaction"""
        self.session.commit()
    
    def rollback(self) -> None:
        """Rollback la transaction"""
        self.session.rollback()