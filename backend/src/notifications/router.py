"""
Router de notifications - Détermine qui doit recevoir quoi
"""

from typing import List, Dict, Any, Set
from .contacts import get_contacts_for_level, get_contacts_for_event_type, get_contacts_for_site
import structlog

logger = structlog.get_logger()


class NotificationRouter:
    """
    Détermine les destinataires des notifications selon:
    - Niveau de risque
    - Type d'événement
    - Entités affectées
    """
    
    # Seuils de risque
    RISK_THRESHOLDS = {
        "CRITIQUE": 80,
        "ELEVE": 60,
        "MOYEN": 40,
        "FAIBLE": 0
    }
    
    def __init__(self):
        self.logger = logger.bind(component="notification_router")
    
    def determine_risk_level(self, risk_score: float) -> str:
        """
        Détermine le niveau de risque à partir du score
        
        Args:
            risk_score: Score de risque (0-100)
            
        Returns:
            Niveau: CRITIQUE, ELEVE, MOYEN, FAIBLE
        """
        if risk_score >= self.RISK_THRESHOLDS["CRITIQUE"]:
            return "CRITIQUE"
        elif risk_score >= self.RISK_THRESHOLDS["ELEVE"]:
            return "ELEVE"
        elif risk_score >= self.RISK_THRESHOLDS["MOYEN"]:
            return "MOYEN"
        else:
            return "FAIBLE"
    
    def get_recipients(
        self,
        risk_score: float,
        event_type: str,
        affected_sites: List[Dict] = None,
        affected_suppliers: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Détermine tous les destinataires pour une notification
        
        Args:
            risk_score: Score de risque (0-100)
            event_type: Type d'événement (reglementaire, climatique, geopolitique)
            affected_sites: Liste des sites affectés
            affected_suppliers: Liste des fournisseurs affectés
            
        Returns:
            Dict avec:
            - risk_level: Niveau de risque
            - recipients: Liste des emails uniques
            - recipients_details: Détails des destinataires
            - urgency: Délai d'action (IMMEDIAT, URGENT, PRIORITAIRE, NORMAL)
        """
        risk_level = self.determine_risk_level(risk_score)
        
        # Collecter tous les emails (avec déduplication)
        all_emails: Set[str] = set()
        recipients_details: List[Dict] = []
        
        # 1. Contacts par niveau de risque
        level_contacts = get_contacts_for_level(risk_level)
        for contact in level_contacts:
            all_emails.add(contact["email"])
            recipients_details.append({
                "email": contact["email"],
                "name": contact["name"],
                "role": contact["role"],
                "reason": f"Niveau de risque {risk_level}"
            })
        
        # 2. Contacts par type d'événement
        event_emails = get_contacts_for_event_type(event_type)
        for email in event_emails:
            if email not in all_emails:
                all_emails.add(email)
                recipients_details.append({
                    "email": email,
                    "name": "Contact spécialisé",
                    "role": f"Responsable {event_type}",
                    "reason": f"Type d'événement: {event_type}"
                })
        
        # 3. Contacts par site affecté (si CRITIQUE ou ELEVE)
        if risk_level in ["CRITIQUE", "ELEVE"] and affected_sites:
            for site in affected_sites[:5]:  # Limiter à 5 sites
                site_name = site.get("name", "").lower().replace(" ", "_")
                site_contacts = get_contacts_for_site(site_name)
                for role, email in site_contacts.items():
                    if email not in all_emails:
                        all_emails.add(email)
                        recipients_details.append({
                            "email": email,
                            "name": f"{role.capitalize()} - {site.get('name', site_name)}",
                            "role": role,
                            "reason": f"Site affecté: {site.get('name', site_name)}"
                        })
        
        # Déterminer l'urgence
        urgency_map = {
            "CRITIQUE": "IMMEDIAT",
            "ELEVE": "URGENT",
            "MOYEN": "PRIORITAIRE",
            "FAIBLE": "NORMAL"
        }
        
        # Déterminer le délai d'action
        delay_map = {
            "CRITIQUE": "48 heures",
            "ELEVE": "7 jours",
            "MOYEN": "14 jours",
            "FAIBLE": "30 jours"
        }
        
        result = {
            "risk_level": risk_level,
            "urgency": urgency_map.get(risk_level, "NORMAL"),
            "action_delay": delay_map.get(risk_level, "30 jours"),
            "recipients": list(all_emails),
            "recipients_count": len(all_emails),
            "recipients_details": recipients_details
        }
        
        self.logger.info(
            "notification_routing_complete",
            risk_level=risk_level,
            recipients_count=len(all_emails),
            event_type=event_type
        )
        
        return result
    
    def should_send_sms(self, risk_level: str) -> bool:
        """Détermine si un SMS doit être envoyé (uniquement CRITIQUE)"""
        return risk_level == "CRITIQUE"
    
    def should_generate_pdf(self, risk_level: str) -> bool:
        """Détermine si un PDF détaillé doit être généré"""
        return risk_level in ["CRITIQUE", "ELEVE", "MOYEN"]
    
    def get_email_priority(self, risk_level: str) -> str:
        """Retourne la priorité email (pour les headers)"""
        priority_map = {
            "CRITIQUE": "1",  # Highest
            "ELEVE": "2",     # High
            "MOYEN": "3",     # Normal
            "FAIBLE": "5"     # Low
        }
        return priority_map.get(risk_level, "3")
