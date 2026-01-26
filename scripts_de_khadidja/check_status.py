"""
Script de vérification rapide du statut
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.database import get_session
from src.storage.models import Analysis
from sqlalchemy import func

session = get_session()

# ID de la régulation qu'on vient de tester
test_id = "85e11c52-cdb9-4523-8382-4dd7c74f922d"

analysis = session.query(Analysis).filter(Analysis.id == test_id).first()

if analysis:
    print(f"\n🔍 Régulation: {analysis.document.title}")
    print(f"   Status: {analysis.validation_status}")
    print(f"   Validé par: {analysis.validated_by or 'N/A'}")
    print(f"   Date: {analysis.validated_at or 'N/A'}")
else:
    print("❌ Régulation non trouvée")

# Stats globales
stats = session.query(
    Analysis.validation_status,
    func.count(Analysis.id)
).group_by(Analysis.validation_status).all()

print("\n📊 Compteurs:")
for status, count in stats:
    print(f"   {status}: {count}")

session.close()
