#!/usr/bin/env python
"""Test d'envoi de notification réelle basée sur les abonnements"""

from src.notifications.notification_service import NotificationService
from src.notifications.subscription_filter import get_matching_subscriptions

if __name__ == "__main__":
    print("=" * 60)
    print("TEST D'ENVOI DE NOTIFICATION RÉELLE")
    print("=" * 60)
    
    # Document simulé - risque réglementaire ÉLEVÉ
    document = {
        "id": "test-doc-001",
        "title": "Nouvelle réglementation européenne sur les batteries",
        "content": "Test de notification pour vérifier les abonnements",
        "event_type": "reglementaire",
        "source": "EUR-Lex"
    }
    
    # Analyse de risque simulée - niveau ÉLEVÉ
    risk_analysis = {
        "risk_score": 75.0,
        "risk_level": "Fort",  # Correspond à ÉLEVÉ
        "impacts_description": "Impact important sur la chaîne d'approvisionnement",
        "affected_sites": [
            {"id": "site-1", "name": "Hutchinson Montargis", "country": "France"}
        ],
        "affected_suppliers": [
            {"id": "sup-1", "name": "Battery Corp", "country": "China"}  # Chine pour test@example.com
        ],
        "recommendations": "Audit des fournisseurs de batteries recommandé"
    }
    
    print("\n📝 Document de test:")
    print(f"   Titre: {document['title']}")
    print(f"   Type: {document['event_type']}")
    print(f"   Fournisseurs affectés: {risk_analysis['affected_suppliers']}")
    
    print("\n📊 Analyse de risque:")
    print(f"   Score: {risk_analysis['risk_score']}")
    print(f"   Niveau: {risk_analysis['risk_level']} (ÉLEVÉ)")
    
    # Vérifier les abonnements correspondants
    print("\n🔍 Recherche des abonnements correspondants...")
    matches = get_matching_subscriptions(
        event_type=document['event_type'],
        risk_level=risk_analysis['risk_level'],
        affected_sites=risk_analysis['affected_sites'],
        affected_suppliers=risk_analysis['affected_suppliers']
    )
    
    print(f"\n✉️  {len(matches)} abonné(s) seront notifié(s):")
    for m in matches:
        print(f"   - {m['email']} ({m['subscription_name']})")
    
    if len(matches) == 0:
        print("\n⚠️  Aucun abonné correspondant aux critères")
        exit(0)
    
    # Demander confirmation avant envoi
    response = input("\n🚀 Envoyer les emails de test ? (o/n): ")
    if response.lower() != 'o':
        print("❌ Envoi annulé")
        exit(0)
    
    # Envoyer la notification
    print("\n📤 Envoi des notifications...")
    service = NotificationService(dry_run=False)  # Mode réel
    
    result = service.notify_risk_analysis(
        document=document,
        risk_analysis=risk_analysis
    )
    
    print("\n" + "=" * 60)
    print("RÉSULTAT:")
    print(f"   Status: {result.get('status')}")
    print(f"   Destinataires: {result.get('recipients', [])}")
    print(f"   Message: {result.get('message', 'N/A')}")
    print("=" * 60)
