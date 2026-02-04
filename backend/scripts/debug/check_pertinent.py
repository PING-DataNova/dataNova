"""Script pour vérifier les documents pertinents."""
from src.storage.database import SessionLocal
from src.storage.models import Document, PertinenceCheck, RiskAnalysis

db = SessionLocal()

# decision = OUI, NON, PARTIELLEMENT
pertinent = db.query(Document).join(PertinenceCheck).filter(
    PertinenceCheck.decision.in_(['OUI', 'PARTIELLEMENT'])
).all()
print(f'Documents pertinents: {len(pertinent)}')

analyzed_ids = [a[0] for a in db.query(RiskAnalysis.document_id).distinct().all()]
not_analyzed = [d for d in pertinent if d.id not in analyzed_ids]
print(f'Non analysés: {len(not_analyzed)}')

for d in not_analyzed[:5]:
    print(f'  ID {d.id}: {d.title[:60]}')

# Tous les documents en BDD
all_docs = db.query(Document).count()
print(f'\nTotal documents en BDD: {all_docs}')

db.close()
