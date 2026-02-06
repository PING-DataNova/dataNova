#!/usr/bin/env python
"""Test d'envoi de notification RÉELLE"""

import os
from pathlib import Path

# Charger les variables d'environnement
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

print(f"📧 BREVO_API_KEY: {'OK' if os.getenv('BREVO_API_KEY') else 'NON CONFIGURÉ'}")
print(f"📧 SENDER_EMAIL: {os.getenv('SENDER_EMAIL', 'non défini')}")

from src.notifications.notification_service import NotificationService

# Document simulé - risque réglementaire ÉLEVÉ
document = {
    'id': 'test-notification-real',
    'title': 'TEST ABONNEMENT - Nouvelle réglementation batteries UE 2026',
    'content': 'Ceci est un test pour vérifier le système d\'abonnement aux notifications',
    'event_type': 'reglementaire',
    'source': 'Test DataNova'
}

# Analyse de risque niveau ÉLEVÉ avec fournisseur en Chine
risk_analysis = {
    'risk_score': 78.0,
    'risk_level': 'Fort',  # ÉLEVÉ
    'impacts_description': 'Test: Impact sur la chaîne d\'approvisionnement batteries',
    'affected_sites': [
        {'id': 'site-montargis', 'name': 'Hutchinson Montargis', 'country': 'France'}
    ],
    'affected_suppliers': [
        {'id': 'sup-battery', 'name': 'China Battery Corp', 'country': 'China'}
    ],
    'recommendations': 'TEST: Vérification du système d\'abonnement'
}

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 ENVOI NOTIFICATION RÉELLE")
    print("=" * 60)
    print(f"\n📝 Document: {document['title']}")
    print(f"   Type: {document['event_type']}")
    print(f"   Niveau risque: {risk_analysis['risk_level']} (ÉLEVÉ)")
    print(f"   Fournisseur: China Battery Corp (China)")
    
    print("\n⚡ Envoi en cours...")
    
    # Mode RÉEL (dry_run=False)
    service = NotificationService(dry_run=False)
    result = service.notify_risk_analysis(document=document, risk_analysis=risk_analysis)
    
    print("\n" + "=" * 60)
    print("📧 RÉSULTAT ENVOI:")
    print(f"   Statut: {result.get('status')}")
    print(f"   Destinataires: {result.get('recipients', [])}")
    if result.get('email_result'):
        print(f"   Email: {result['email_result']}")
    print("=" * 60)
    print("\n✉️  Vérifiez votre boîte mail !")
