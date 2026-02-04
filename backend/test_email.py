#!/usr/bin/env python3
"""
Test d'envoi d'email via Brevo
"""
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

from src.notifications.email_sender import EmailSender

print("=" * 60)
print("📧 TEST D'ENVOI EMAIL VIA BREVO")
print("=" * 60)

# Vérifier la configuration
api_key = os.getenv("BREVO_API_KEY", "")
print(f"API Key configurée: {'✅ Oui' if api_key else '❌ Non'}")

# Créer le sender
sender = EmailSender(dry_run=False)

# Envoyer un email de test aux destinataires configurés
result = sender.send_notification(
    recipients=[
        "marc.houndji@groupe-esigelec.org",
        "nora.dossou-gbete@groupe-esigelec.org"
    ],
    risk_level="CRITIQUE",
    event_title="Test CBAM - Système PING",
    event_type="reglementaire",
    risk_score=82.75,
    impact_summary="Impact quotidien estimé: 4,614,000€/jour (1.68Md€/an)",
    affected_entities={"sites": 8, "suppliers": 10, "unique_suppliers": 3},
    recommendations=[
        {
            "title": "Déploiement système traçabilité carbone",
            "priority": "HAUTE",
            "roi": "16.8x",
            "budget": "8M€"
        },
        {
            "title": "Diversification fournisseurs critiques",
            "priority": "HAUTE",
            "roi": "12.4x",
            "budget": "25M€"
        },
        {
            "title": "Constitution stocks stratégiques",
            "priority": "MOYENNE",
            "roi": "4.2x",
            "budget": "85M€"
        }
    ],
    context_and_stakes="Le Mécanisme d'Ajustement Carbone aux Frontières (CBAM) de l'UE impose une taxe carbone sur les importations de produits à forte intensité carbone. Pour Hutchinson, équipementier automobile et aéronautique, l'impact est majeur sur les achats d'acier, aluminium et composants importés.",
    financial_analysis="Impact quotidien total: 4,614,000€/jour. Impact annuel projeté: 1,684,110,000€/an. Répartition: Europe 45%, Asie 30%, Amériques 25%.",
    do_nothing_scenario="Sans action: absorption complète du surcoût CBAM (1.68Md€/an), érosion marge opérationnelle de 8.5% à 2.1%, perte de compétitivité face aux concurrents préparés.",
    action_delay="48 heures"
)

print("\n📊 RÉSULTAT:")
print(f"   Status: {result.get('status')}")
print(f"   Destinataires: {result.get('recipients_count')}")
if result.get('resend_id'):
    print(f"   Resend ID: {result.get('resend_id')}")
if result.get('error'):
    print(f"   Erreur: {result.get('error')}")
print("=" * 60)
