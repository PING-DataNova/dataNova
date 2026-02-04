"""
Service de notification principal
Orchestre le routage et l'envoi des notifications
"""

from typing import Dict, Any, List
from datetime import datetime
import structlog

from .router import NotificationRouter
from .email_sender import EmailSender

logger = structlog.get_logger()


class NotificationService:
    """
    Service principal de notification
    Utilisé par le workflow après l'Agent 2 ou le Judge
    """
    
    def __init__(self, dry_run: bool = None):
        """
        Initialise le service de notification
        
        Args:
            dry_run: Si True, affiche les emails sans les envoyer
        """
        self.router = NotificationRouter()
        self.email_sender = EmailSender(dry_run=dry_run)
        self.logger = logger.bind(component="notification_service")
    
    def notify_risk_analysis(
        self,
        document: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        pertinence_result: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Envoie une notification pour une analyse de risque
        
        Args:
            document: Document source
            risk_analysis: Résultat de l'analyse Agent 2
            pertinence_result: Résultat de pertinence Agent 1B (optionnel)
            
        Returns:
            Dict avec le statut de la notification
        """
        self.logger.info(
            "notification_started",
            document_id=document.get("id", "unknown")[:8],
            document_title=document.get("title", "")[:50]
        )
        
        # Extraire les données de l'analyse
        risk_score = risk_analysis.get("risk_score", 0)
        event_type = document.get("event_type", "reglementaire")
        event_title = document.get("title", "Événement non titré")
        
        affected_sites = risk_analysis.get("affected_sites", [])
        affected_suppliers = risk_analysis.get("affected_suppliers", [])
        
        # 1. Router les destinataires
        routing = self.router.get_recipients(
            risk_score=risk_score,
            event_type=event_type,
            affected_sites=affected_sites,
            affected_suppliers=affected_suppliers
        )
        
        risk_level = routing["risk_level"]
        recipients = routing["recipients"]
        
        if not recipients:
            self.logger.warning("no_recipients_found", risk_level=risk_level)
            return {
                "status": "no_recipients",
                "risk_level": risk_level,
                "message": "Aucun destinataire trouvé pour ce niveau de risque"
            }
        
        # 2. Préparer le résumé des entités affectées
        affected_entities = {
            "sites": len(affected_sites),
            "suppliers": len(affected_suppliers),
            "unique_suppliers": len([s for s in affected_suppliers if s.get("is_unique_supplier", False)])
        }
        
        # 3. Préparer l'impact financier
        total_daily_impact = sum(
            s.get("daily_impact_eur", 0) for s in affected_sites
        ) + sum(
            s.get("daily_impact_eur", 0) for s in affected_suppliers
        )
        
        impact_summary = f"Impact quotidien estimé: {total_daily_impact:,.0f}€/jour ({total_daily_impact * 365:,.0f}€/an)"
        
        # 4. Extraire les recommandations
        recommendations = risk_analysis.get("recommendations", [])
        
        # 5. Extraire les sections détaillées
        context_and_stakes = risk_analysis.get("context_and_stakes")
        financial_analysis = risk_analysis.get("financial_analysis")
        do_nothing_scenario = risk_analysis.get("do_nothing_scenario")
        
        # 6. Envoyer l'email
        email_result = self.email_sender.send_notification(
            recipients=recipients,
            risk_level=risk_level,
            event_title=event_title,
            event_type=event_type,
            risk_score=risk_score,
            impact_summary=impact_summary,
            affected_entities=affected_entities,
            recommendations=recommendations,
            context_and_stakes=context_and_stakes,
            financial_analysis=financial_analysis,
            do_nothing_scenario=do_nothing_scenario,
            action_delay=routing["action_delay"]
        )
        
        # 7. Construire le résultat final
        result = {
            "status": email_result.get("status", "unknown"),
            "risk_level": risk_level,
            "urgency": routing["urgency"],
            "action_delay": routing["action_delay"],
            "recipients_count": len(recipients),
            "recipients": recipients,
            "document_id": document.get("id"),
            "document_title": event_title,
            "risk_score": risk_score,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "email_result": email_result
        }
        
        self.logger.info(
            "notification_completed",
            status=result["status"],
            risk_level=risk_level,
            recipients_count=len(recipients)
        )
        
        return result
    
    def notify_batch(
        self,
        analyses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Envoie des notifications pour plusieurs analyses
        
        Args:
            analyses: Liste de dicts avec 'document' et 'risk_analysis'
            
        Returns:
            Liste des résultats de notification
        """
        results = []
        
        for item in analyses:
            document = item.get("document", {})
            risk_analysis = item.get("risk_analysis", {})
            pertinence_result = item.get("pertinence_result", {})
            
            result = self.notify_risk_analysis(
                document=document,
                risk_analysis=risk_analysis,
                pertinence_result=pertinence_result
            )
            results.append(result)
        
        return results


# Fonction utilitaire pour utilisation directe
def send_risk_notification(
    document: Dict[str, Any],
    risk_analysis: Dict[str, Any],
    dry_run: bool = None
) -> Dict[str, Any]:
    """
    Fonction utilitaire pour envoyer une notification rapidement
    
    Args:
        document: Document source
        risk_analysis: Résultat de l'analyse Agent 2
        dry_run: Mode dry-run (par défaut: True)
    """
    service = NotificationService(dry_run=dry_run)
    return service.notify_risk_analysis(document, risk_analysis)
