#!/usr/bin/env python3
"""Script pour vérifier les données en base"""

from src.storage.database import SessionLocal
from src.storage.models import RiskAnalysis, Document, Alert, Notification

session = SessionLocal()

# Compter les RiskAnalysis par niveau
analyses = session.query(RiskAnalysis).all()
print('=== RISK ANALYSES EN BASE ===')
print(f'Total analyses: {len(analyses)}')

critique = len([a for a in analyses if a.risk_level and a.risk_level.lower() == 'critique'])
fort = len([a for a in analyses if a.risk_level and a.risk_level.lower() == 'fort'])
moyen = len([a for a in analyses if a.risk_level and a.risk_level.lower() == 'moyen'])
faible = len([a for a in analyses if a.risk_level and a.risk_level.lower() == 'faible'])

print(f'Critique: {critique}')
print(f'Fort: {fort}')
print(f'Moyen: {moyen}')
print(f'Faible: {faible}')

# Analyser les scores
print('')
print('=== SCORES ===')
scores = [a.risk_score for a in analyses if a.risk_score]
if scores:
    print(f'Score moyen: {sum(scores)/len(scores):.1f}')
    print(f'Score max: {max(scores)}')
    print(f'Score min: {min(scores)}')

# Documents
docs = session.query(Document).all()
print('')
print(f'=== DOCUMENTS: {len(docs)} ===')

# Alerts
alerts = session.query(Alert).all()
print(f'=== ALERTS: {len(alerts)} ===')

# Notifications
notifs = session.query(Notification).all()
print(f'=== NOTIFICATIONS: {len(notifs)} ===')

# Afficher les analyses
print('')
print('=== TOUTES LES RISK ANALYSES ===')
for a in analyses:
    doc = session.query(Document).filter_by(id=a.document_id).first()
    title = doc.title[:60] if doc and doc.title else 'N/A'
    print(f'- {title}')
    print(f'  Niveau: {a.risk_level} | Score: {a.risk_score} | Supply Chain: {a.supply_chain_impact}')

session.close()
