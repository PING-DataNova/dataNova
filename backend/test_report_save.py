"""Test du rapport textuel complet sauvegardé par Agent 2"""
from src.storage.database import get_session
from src.storage.models import Document, PertinenceCheck, RiskAnalysis

session = get_session()

# Récupérer un document pertinent avec analyse de risque
docs_with_risk = session.query(Document, PertinenceCheck, RiskAnalysis).join(
    PertinenceCheck, Document.id == PertinenceCheck.document_id
).join(
    RiskAnalysis, Document.id == RiskAnalysis.document_id
).filter(PertinenceCheck.decision != 'NON').limit(1).all()

if docs_with_risk:
    doc, pc, risk = docs_with_risk[0]
    print(f"Document: {doc.title[:80]}...")
    print(f"Pertinence: {pc.decision}")
    print(f"\n" + "="*60)
    print("IMPACTS DESCRIPTION (le rapport):")
    print("="*60)
    print(risk.impacts_description[:2000] if risk.impacts_description else "N/A")
    print(f"\n" + "="*60)
    print("REASONING:")
    print("="*60)
    print(risk.reasoning[:1000] if risk.reasoning else "N/A")
else:
    print("Aucun document pertinent avec analyse de risque trouvé")
    
    # Forcer une nouvelle analyse pour un document pertinent
    print("\nLancement d'une analyse sur un document pertinent existant...")
    
    pc = session.query(PertinenceCheck).filter(PertinenceCheck.decision.in_(['OUI', 'PARTIELLEMENT'])).first()
    if pc:
        doc = session.query(Document).filter_by(id=pc.document_id).first()
        if doc:
            print(f"Document à analyser: {doc.title[:60]}...")
            
            # Charger les données company
            import json
            with open("data/company_profiles/Hutchinson_SA.json", "r") as f:
                company_data = json.load(f)
            
            # Lancer Agent 2
            from src.agent_2.agent import Agent2
            
            doc_dict = {
                "id": doc.id,
                "title": doc.title,
                "content": doc.content or doc.summary,
                "event_type": doc.event_type,
                "source": doc.source_url,
                "celex": doc.extra_metadata.get("celex_number") if doc.extra_metadata else None
            }
            
            pc_dict = {
                "check_id": pc.id,
                "decision": pc.decision,
                "confidence": pc.confidence
            }
            
            agent2 = Agent2(company_data)
            result = agent2.analyze(doc_dict)
            
            print(f"\nAgent 2 result keys: {result.keys()}")
            
            # Sauvegarder
            from src.orchestration.langgraph_workflow import save_risk_analysis
            risk_id = save_risk_analysis(doc_dict, pc_dict, result)
            print(f"\nRisk Analysis sauvegardé avec ID: {risk_id}")
            
            # Relire le rapport
            risk = session.query(RiskAnalysis).filter_by(id=risk_id).first()
            if risk:
                print(f"\n" + "="*60)
                print("IMPACTS DESCRIPTION (le rapport complet):")
                print("="*60)
                print(risk.impacts_description)
                print(f"\n" + "="*60)
                print("REASONING:")
                print("="*60)
                print(risk.reasoning)
    else:
        print("Aucun document pertinent en base")

session.close()
