#!/usr/bin/env python
"""Test d'envoi de notification - dry run"""

from src.notifications.notification_service import NotificationService

# Document simulé - risque réglementaire ÉLEVÉ
document = {
    'id': 'test-doc-001',
    'title': 'Nouvelle réglementation européenne sur les batteries',
    'content': 'Test de notification',
    'event_type': 'reglementaire',
    'source': 'EUR-Lex'
}

# Analyse de risque niveau ÉLEVÉ avec fournisseur en Chine
risk_analysis = {
    'risk_score': 75.0,
    'risk_level': 'Fort',
    'impacts_description': 'Impact sur la chaîne approvisionnement',
    'affected_sites': [{'id': 'site-1', 'name': 'Montargis', 'country': 'France'}],
    'affected_suppliers': [{'id': 'sup-1', 'name': 'Battery Corp', 'country': 'China'}],
    'recommendations': 'Audit fournisseurs batteries'
}

if __name__ == "__main__":
    print("=" * 60)
    print("TEST ENVOI NOTIFICATION (DRY RUN)")
    print("=" * 60)
    print(f"\nDocument: {document['title']}")
    print(f"Type: {document['event_type']}")
    print(f"Niveau risque: {risk_analysis['risk_level']} (ÉLEVÉ)")
    print(f"Fournisseur affecté: Battery Corp (China)")
    print("\n" + "=" * 60)
    
    service = NotificationService(dry_run=True)
    result = service.notify_risk_analysis(document=document, risk_analysis=risk_analysis)
    
    print("\n" + "=" * 60)
    print("RÉSULTAT:")
    print(f"  Statut: {result.get('status')}")
    print(f"  Destinataires: {result.get('recipients', [])}")
    print("=" * 60)
