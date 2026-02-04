#!/usr/bin/env python3
"""Test direct d'envoi email via Brevo."""

import os
from dotenv import load_dotenv
load_dotenv()

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

api_key = os.getenv('BREVO_API_KEY')
sender_email = os.getenv('SENDER_EMAIL')

print(f"Sender: {sender_email}")
print(f"API Key: {api_key[:20]}...")

config = sib_api_v3_sdk.Configuration()
config.api_key['api-key'] = api_key

api = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(config))

email = sib_api_v3_sdk.SendSmtpEmail(
    to=[{'email': 'nora.dossou-gbete@groupe-esigelec.org'}],
    sender={'name': 'PING Test', 'email': sender_email},
    subject='Test PING - Notification fonctionnelle',
    html_content='<h1>Test reussi</h1><p>La notification PING fonctionne correctement.</p>'
)

try:
    response = api.send_transac_email(email)
    print(f'Email envoye! Message ID: {response.message_id}')
except ApiException as e:
    print(f'Erreur: {e.body}')
except Exception as e:
    print(f'Erreur generale: {e}')
