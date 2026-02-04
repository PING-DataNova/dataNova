"""
Email Sender - Envoi des notifications par email via Brevo (Sendinblue)
"""

import os
from typing import List, Dict, Any
from datetime import datetime
import structlog

logger = structlog.get_logger()

# Import Brevo SDK
try:
    import sib_api_v3_sdk
    from sib_api_v3_sdk.rest import ApiException
    BREVO_AVAILABLE = True
except ImportError:
    BREVO_AVAILABLE = False


class EmailSender:
    """
    Gère l'envoi d'emails de notification via Brevo
    300 emails/jour gratuits, envoi à n'importe quel destinataire
    """
    
    def __init__(self, dry_run: bool = None):
        """
        Initialise l'email sender
        
        Args:
            dry_run: Si True, affiche l'email au lieu de l'envoyer
        """
        self.logger = logger.bind(component="email_sender")
        
        # Configuration Brevo
        self.brevo_api_key = os.getenv("BREVO_API_KEY", "")
        self.sender_email = os.getenv("SENDER_EMAIL", "ping@hutchinson.com")
        self.sender_name = os.getenv("SENDER_NAME", "Système PING - Hutchinson")
        
        # Mode dry-run
        if dry_run is None:
            if self.brevo_api_key:
                dry_run = os.getenv("EMAIL_DRY_RUN", "false").lower() == "true"
            else:
                dry_run = True
        self.dry_run = dry_run
        
        # Initialiser Brevo si disponible
        if self.brevo_api_key and BREVO_AVAILABLE:
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = self.brevo_api_key
            self.brevo_api = sib_api_v3_sdk.TransactionalEmailsApi(
                sib_api_v3_sdk.ApiClient(configuration)
            )
            self.logger.info("brevo_initialized", api_key_set=True)
        else:
            self.brevo_api = None
    
    def send_notification(
        self,
        recipients: List[str],
        risk_level: str,
        event_title: str,
        event_type: str,
        risk_score: float,
        impact_summary: str,
        affected_entities: Dict[str, int],
        recommendations: List[Dict],
        context_and_stakes: str = None,
        financial_analysis: str = None,
        do_nothing_scenario: str = None,
        action_delay: str = "48 heures",
        pdf_attachment: bytes = None
    ) -> Dict[str, Any]:
        """Envoie une notification par email"""
        
        # Générer le sujet
        subject = self._generate_subject(risk_level, event_type, event_title, risk_score)
        
        # Générer le corps HTML
        html_body = self._generate_html_body(
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
            action_delay=action_delay
        )
        
        if self.dry_run:
            return self._dry_run_send(recipients, subject, html_body)
        elif self.brevo_api:
            return self._brevo_send(recipients, subject, html_body)
        else:
            return {
                "status": "error",
                "error": "Aucun service email configuré. Ajoutez BREVO_API_KEY dans .env"
            }
    
    def _generate_subject(
        self,
        risk_level: str,
        event_type: str,
        event_title: str,
        risk_score: float
    ) -> str:
        """Génère le sujet de l'email selon le niveau de risque"""
        emoji_map = {
            "CRITIQUE": "🚨",
            "ELEVE": "⚠️",
            "MOYEN": "ℹ️",
            "FAIBLE": "📊"
        }
        emoji = emoji_map.get(risk_level, "📊")
        
        title_short = event_title[:50] + "..." if len(event_title) > 50 else event_title
        
        if risk_level == "CRITIQUE":
            return f"{emoji} ALERTE CRITIQUE - {event_type.capitalize()} - {title_short} - Action Immédiate Requise"
        elif risk_level == "ELEVE":
            return f"{emoji} ALERTE ÉLEVÉE - {event_type.capitalize()} - {title_short} - Action Urgente"
        elif risk_level == "MOYEN":
            return f"{emoji} ALERTE MOYENNE - {event_type.capitalize()} - {title_short}"
        else:
            return f"{emoji} Nouvelle Alerte - {event_type.capitalize()} - {title_short}"
    
    def _generate_html_body(
        self,
        risk_level: str,
        event_title: str,
        event_type: str,
        risk_score: float,
        impact_summary: str,
        affected_entities: Dict[str, int],
        recommendations: List[Dict],
        context_and_stakes: str = None,
        financial_analysis: str = None,
        do_nothing_scenario: str = None,
        action_delay: str = "48 heures"
    ) -> str:
        """Génère le corps HTML de l'email"""
        
        color_map = {
            "CRITIQUE": "#dc3545",
            "ELEVE": "#fd7e14",
            "MOYEN": "#ffc107",
            "FAIBLE": "#28a745"
        }
        color = color_map.get(risk_level, "#6c757d")
        
        # Générer la liste des recommandations
        recommendations_html = ""
        for i, rec in enumerate(recommendations[:5], 1):
            if isinstance(rec, dict):
                title = rec.get("title", rec.get("action", "Recommandation"))
                priority = rec.get("priority", "N/A")
                roi = rec.get("roi", "N/A")
                budget = rec.get("budget", "N/A")
                recommendations_html += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">
                        <strong>{i}. {title}</strong><br>
                        <span style="color: #666; font-size: 0.9em;">
                            Priorité: {priority} | ROI: {roi} | Budget: {budget}
                        </span>
                    </td>
                </tr>
                """
            else:
                recommendations_html += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">
                        <strong>{i}. {str(rec)[:200]}</strong>
                    </td>
                </tr>
                """
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
        .header {{ background: {color}; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .section {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid {color}; }}
        .section-title {{ font-weight: bold; color: {color}; margin-bottom: 10px; font-size: 1.1em; }}
        .metric {{ display: inline-block; padding: 10px 20px; margin: 5px; background: white; border-radius: 5px; text-align: center; }}
        .metric-value {{ font-size: 1.5em; font-weight: bold; color: {color}; }}
        .metric-label {{ font-size: 0.85em; color: #666; }}
        .footer {{ background: #333; color: white; padding: 15px; text-align: center; border-radius: 0 0 8px 8px; font-size: 0.9em; }}
        .btn {{ display: inline-block; padding: 12px 25px; background: {color}; color: white; text-decoration: none; border-radius: 5px; margin: 5px; }}
        table {{ width: 100%; border-collapse: collapse; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">🚨 ALERTE {risk_level}</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">{event_title}</p>
        </div>
        
        <div class="content">
            <div style="text-align: center; padding: 15px 0;">
                <div class="metric">
                    <div class="metric-value">{risk_score}/100</div>
                    <div class="metric-label">Score de Risque</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{affected_entities.get('sites', 0)}</div>
                    <div class="metric-label">Sites Affectés</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{affected_entities.get('suppliers', 0)}</div>
                    <div class="metric-label">Fournisseurs</div>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">📋 RÉSUMÉ EXÉCUTIF</div>
                <p><strong>Événement :</strong> {event_title}</p>
                <p><strong>Type :</strong> {event_type.capitalize()}</p>
                <p><strong>Niveau de risque :</strong> <span style="color: {color}; font-weight: bold;">{risk_level}</span> (Score {risk_score}/100)</p>
                <p><strong>Urgence :</strong> Action requise sous <strong>{action_delay}</strong></p>
            </div>
            
            {"" if not context_and_stakes else f'''
            <div class="section">
                <div class="section-title">🎯 CONTEXTE ET ENJEUX</div>
                <p>{context_and_stakes[:800]}{"..." if len(str(context_and_stakes)) > 800 else ""}</p>
            </div>
            '''}
            
            {"" if not financial_analysis else f'''
            <div class="section">
                <div class="section-title">💰 ANALYSE FINANCIÈRE</div>
                <p>{financial_analysis[:600]}{"..." if len(str(financial_analysis)) > 600 else ""}</p>
            </div>
            '''}
            
            <div class="section">
                <div class="section-title">✅ ACTIONS PRIORITAIRES</div>
                <table>
                    {recommendations_html}
                </table>
            </div>
            
            {"" if not do_nothing_scenario else f'''
            <div class="section" style="border-left-color: #dc3545;">
                <div class="section-title" style="color: #dc3545;">⚠️ RISQUE EN CAS D'INACTION</div>
                <p>{do_nothing_scenario[:500]}{"..." if len(str(do_nothing_scenario)) > 500 else ""}</p>
            </div>
            '''}
            
            <div style="text-align: center; padding: 20px 0;">
                <a href="#" class="btn">📊 Voir le Rapport Complet</a>
                <a href="#" class="btn" style="background: #28a745;">✓ Approuver les Recommandations</a>
            </div>
        </div>
        
        <div class="footer">
            <p style="margin: 0;">Système PING - Hutchinson Risk Management</p>
            <p style="margin: 5px 0 0 0; opacity: 0.7;">
                Généré le {datetime.now().strftime("%d/%m/%Y à %H:%M")}
            </p>
        </div>
    </div>
</body>
</html>
        """
        return html
    
    def _dry_run_send(
        self,
        recipients: List[str],
        subject: str,
        html_body: str
    ) -> Dict[str, Any]:
        """Mode dry-run : affiche l'email dans la console"""
        import re
        
        print("\n" + "=" * 70)
        print("📧 EMAIL NOTIFICATION (DRY-RUN MODE)")
        print("=" * 70)
        print(f"📬 Destinataires: {', '.join(recipients)}")
        print(f"📌 Sujet: {subject}")
        print("-" * 70)
        
        text_content = re.sub(r'<[^>]+>', ' ', html_body)
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        print(f"📝 Contenu (résumé):")
        print(text_content[:1000] + "..." if len(text_content) > 1000 else text_content)
        print("=" * 70)
        print("✅ Email prêt à envoyer (mode dry-run actif)")
        print("   Pour envoyer réellement, ajoutez BREVO_API_KEY dans .env")
        print("=" * 70 + "\n")
        
        self.logger.info("email_dry_run", recipients=recipients, subject=subject)
        
        return {
            "status": "dry_run",
            "recipients": recipients,
            "recipients_count": len(recipients),
            "subject": subject,
            "message": "Email affiché en mode dry-run"
        }
    
    def _brevo_send(
        self,
        recipients: List[str],
        subject: str,
        html_body: str
    ) -> Dict[str, Any]:
        """Envoi via Brevo API"""
        try:
            # Préparer les destinataires
            to_list = [{"email": email} for email in recipients]
            
            # Créer l'email
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=to_list,
                sender={"name": self.sender_name, "email": self.sender_email},
                subject=subject,
                html_content=html_body
            )
            
            # Envoyer
            response = self.brevo_api.send_transac_email(send_smtp_email)
            
            print("\n" + "=" * 70)
            print("📧 EMAIL ENVOYÉ VIA BREVO")
            print("=" * 70)
            print(f"📬 Destinataires: {', '.join(recipients)}")
            print(f"📌 Sujet: {subject}")
            print(f"✅ Message ID: {response.message_id}")
            print("=" * 70 + "\n")
            
            self.logger.info(
                "email_sent_brevo",
                recipients=recipients,
                subject=subject,
                message_id=response.message_id
            )
            
            return {
                "status": "sent",
                "provider": "brevo",
                "recipients": recipients,
                "recipients_count": len(recipients),
                "subject": subject,
                "message_id": response.message_id,
                "message": "Email envoyé avec succès via Brevo"
            }
            
        except ApiException as e:
            self.logger.error("brevo_send_error", error=str(e))
            print(f"\n❌ Erreur Brevo: {e.body}")
            return {
                "status": "error",
                "provider": "brevo",
                "recipients": recipients,
                "error": str(e.body)
            }
        except Exception as e:
            self.logger.error("brevo_send_error", error=str(e))
            return {
                "status": "error",
                "provider": "brevo",
                "recipients": recipients,
                "error": str(e)
            }
