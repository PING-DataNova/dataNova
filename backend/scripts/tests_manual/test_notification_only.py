#!/usr/bin/env python3
"""
Test rapide de l'envoi de notification sur une analyse existante.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Charger les variables d'environnement AVANT tout import
from dotenv import load_dotenv
load_dotenv()

from src.storage.database import SessionLocal
from src.storage.models import Document, PertinenceCheck, RiskAnalysis
from src.notifications.notification_service import NotificationService

def test_notification():
    """Envoie une notification pour la dernière analyse en BDD."""
    
    db = SessionLocal()
    
    try:
        # Récupérer la dernière analyse
        analysis = db.query(RiskAnalysis).order_by(RiskAnalysis.created_at.desc()).first()
        
        if not analysis:
            print("❌ Aucune analyse en BDD")
            return
        
        doc = db.query(Document).filter(Document.id == analysis.document_id).first()
        pertinence = db.query(PertinenceCheck).filter(PertinenceCheck.id == analysis.pertinence_check_id).first()
        
        print("=" * 70)
        print("📧 TEST D'ENVOI DE NOTIFICATION")
        print("=" * 70)
        print(f"Document: {doc.title[:60]}...")
        print(f"Niveau de risque: {analysis.risk_level}")
        print(f"Score: {analysis.risk_score * 10}/100")
        
        # Debug: afficher le contenu de l'analyse
        print(f"\nDébug - affected_sites: {len(analysis.affected_sites or [])} sites")
        print(f"Débug - affected_suppliers: {len(analysis.affected_suppliers or [])} suppliers")
        
        # Préparer les données
        doc_data = {
            "id": doc.id,
            "title": doc.title,
            "event_type": doc.event_type,
            "source_url": doc.source_url
        }
        
        risk_data = {
            "risk_score": analysis.risk_score * 10,  # Reconvertir en 0-100
            "overall_risk_level": analysis.risk_level,
            "affected_sites": analysis.affected_sites or [],
            "affected_suppliers": analysis.affected_suppliers or [],
            "recommendations": analysis.recommendations,
            "analysis_metadata": analysis.analysis_metadata
        }
        
        # Envoyer notification (RÉELLEMENT)
        from src.notifications.email_sender import EmailSender
        
        # Tester d'abord l'email sender directement
        email_sender = EmailSender(dry_run=False)
        print(f"\nDébug - dry_run: {email_sender.dry_run}")
        print(f"Débug - brevo_api: {email_sender.brevo_api is not None}")
        
        notification_service = NotificationService(dry_run=False)
        
        result = notification_service.notify_risk_analysis(
            document=doc_data,
            risk_analysis=risk_data
        )
        
        print("\n" + "=" * 70)
        print(f"✅ Résultat: {result.get('status')}")
        print(f"   Niveau: {result.get('risk_level')}")
        print(f"   Destinataires: {result.get('recipients_count', 0)}")
        if result.get('emails_sent'):
            print(f"   Emails envoyés: {result.get('emails_sent')}")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_notification()
