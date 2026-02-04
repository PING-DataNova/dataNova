#!/usr/bin/env python3
"""Script pour créer les alertes manquantes"""

from src.storage.database import SessionLocal
from src.storage.models import Alert, RiskAnalysis, Document
from datetime import datetime
import uuid

session = SessionLocal()

# Récupérer la RiskAnalysis critique
analysis = session.query(RiskAnalysis).filter(RiskAnalysis.risk_level == 'CRITIQUE').first()

if analysis:
    # Vérifier si une alerte existe déjà pour cette analyse
    existing_alert = session.query(Alert).filter(Alert.risk_analysis_id == analysis.id).first()
    
    if existing_alert:
        print(f"Alerte existe deja: {existing_alert.id}")
    else:
        # Récupérer le document associé
        doc = session.query(Document).filter(Document.id == analysis.document_id).first()
        
        # Créer l'alerte
        alert = Alert(
            id=str(uuid.uuid4()),
            document_id=analysis.document_id,
            risk_analysis_id=analysis.id,
            title=f"Risque Critique - {doc.title if doc else 'Document'}",
            description=analysis.impacts_description[:500] if analysis.impacts_description else "Analyse de risque critique detectee",
            severity="critical",
            affected_sites=analysis.affected_sites,
            affected_suppliers=analysis.affected_suppliers,
            recommendations=analysis.recommendations[:500] if analysis.recommendations else "Voir analyse complete",
            status="new",
            created_at=datetime.utcnow()
        )
        session.add(alert)
        session.commit()
        print(f"Alerte creee: {alert.id}")
        print(f"   Titre: {alert.title}")
        print(f"   Severite: {alert.severity}")
        print(f"   Status: {alert.status}")
else:
    print("Aucune RiskAnalysis critique trouvee")

# Vérifier le total
total_alerts = session.query(Alert).count()
print(f"Total alertes en base: {total_alerts}")

session.close()
