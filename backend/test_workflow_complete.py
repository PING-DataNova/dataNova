#!/usr/bin/env python3
"""
Test du workflow complet PING avec limite à 1 document pour Agent 2.

Pipeline: Agent 1A → Agent 1B → Agent 2 (1 doc) → Notification
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

import asyncio
from datetime import datetime

from src.storage.database import SessionLocal
from src.storage.models import (
    Document, PertinenceCheck, RiskAnalysis, 
    HutchinsonSite, Supplier, SupplierRelationship
)
from src.agent_1a.agent import run_agent_1a_weather
from src.agent_1b.agent import Agent1B
from src.agent_2.agent import Agent2
from src.notifications.notification_service import NotificationService


async def run_full_workflow():
    """Workflow complet avec limite à 1 doc pour Agent 2."""
    
    print("\n" + "🚀" * 35)
    print("   WORKFLOW COMPLET PING - TEST")
    print("🚀" * 35 + "\n")
    
    db = SessionLocal()
    
    try:
        # ================================================================
        # ÉTAPE 1 : AGENT 1A - COLLECTE (Météo uniquement car EUR-Lex rate limited)
        # ================================================================
        print("=" * 70)
        print("📡 ÉTAPE 1 : AGENT 1A - Collecte des données")
        print("=" * 70)
        
        weather_result = await run_agent_1a_weather(forecast_days=7, save_to_db=True)
        print(f"   OpenMeteo: {weather_result.get('status')}")
        print(f"   Alertes: {weather_result.get('alerts', {}).get('total', 0)}")
        
        # ================================================================
        # ÉTAPE 2 : VÉRIFIER LES DOCUMENTS PERTINENTS
        # ================================================================
        print("\n" + "=" * 70)
        print("🔍 ÉTAPE 2 : Vérification documents pertinents")
        print("=" * 70)
        
        # Documents pertinents non analysés
        pertinent_checks = db.query(PertinenceCheck).filter(
            PertinenceCheck.decision.in_(['OUI', 'PARTIELLEMENT'])
        ).all()
        
        analyzed_ids = [r[0] for r in db.query(RiskAnalysis.document_id).all()]
        
        docs_to_analyze = []
        for pc in pertinent_checks:
            if pc.document_id not in analyzed_ids:
                doc = db.query(Document).filter(Document.id == pc.document_id).first()
                if doc:
                    docs_to_analyze.append((doc, pc))
        
        print(f"   Documents pertinents: {len(pertinent_checks)}")
        print(f"   Déjà analysés: {len(analyzed_ids)}")
        print(f"   À analyser: {len(docs_to_analyze)}")
        
        if not docs_to_analyze:
            print("   ⚠️ Aucun document à analyser!")
            return
        
        # ================================================================
        # ÉTAPE 3 : AGENT 2 - Analyse (1 SEUL DOCUMENT)
        # ================================================================
        print("\n" + "=" * 70)
        print("🤖 ÉTAPE 3 : AGENT 2 - Analyse de risque (1 document)")
        print("=" * 70)
        
        # Prendre seulement le premier document
        doc, pertinence = docs_to_analyze[0]
        
        print(f"   Document: {doc.title[:60]}...")
        print(f"   Pertinence: {pertinence.decision} ({pertinence.confidence})")
        
        # Charger données métier
        sites = db.query(HutchinsonSite).filter(HutchinsonSite.active == True).all()
        suppliers = db.query(Supplier).filter(Supplier.active == True).all()
        relationships = db.query(SupplierRelationship).filter(SupplierRelationship.active == True).all()
        
        sites_data = [
            {"id": s.id, "name": s.name, "code": s.code, "country": s.country,
             "region": s.region, "city": s.city, "latitude": s.latitude,
             "longitude": s.longitude, "sectors": s.sectors, "products": s.products,
             "strategic_importance": s.strategic_importance,
             "daily_revenue": s.daily_revenue, "safety_stock_days": s.safety_stock_days}
            for s in sites
        ]
        
        suppliers_data = [
            {"id": s.id, "name": s.name, "code": s.code, "country": s.country,
             "region": s.region, "city": s.city, "latitude": s.latitude,
             "longitude": s.longitude, "sector": s.sector,
             "products_supplied": s.products_supplied, "criticality_score": s.criticality_score}
            for s in suppliers
        ]
        
        relationships_data = [
            {"hutchinson_site_id": r.hutchinson_site_id, "supplier_id": r.supplier_id,
             "products_supplied": r.products_supplied, "criticality": r.criticality,
             "is_sole_supplier": r.is_sole_supplier, "has_backup_supplier": r.has_backup_supplier}
            for r in relationships
        ]
        
        doc_data = {
            "id": doc.id,
            "title": doc.title,
            "content": doc.content,
            "event_type": doc.event_type,
            "source_url": doc.source_url,
            "publication_date": str(doc.publication_date) if doc.publication_date else None,
            "metadata": doc.extra_metadata
        }
        
        pertinence_data = {
            "id": pertinence.id,
            "decision": pertinence.decision,
            "confidence": pertinence.confidence,
            "reasoning": pertinence.reasoning,
            "matched_elements": pertinence.matched_elements,
            "affected_sites": pertinence.affected_sites,
            "affected_suppliers": pertinence.affected_suppliers
        }
        
        agent2 = Agent2()
        start_time = datetime.now()
        
        analysis_result, projections = agent2.analyze(
            document=doc_data,
            pertinence_result=pertinence_data,
            sites=sites_data,
            suppliers=suppliers_data,
            supplier_relationships=relationships_data
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        print(f"\n   ✅ Analyse terminée en {execution_time:.1f}s")
        print(f"   Niveau: {analysis_result.get('overall_risk_level')}")
        print(f"   Score: {analysis_result.get('risk_score_360')}/100")
        print(f"   Sites affectés: {len(analysis_result.get('affected_sites', []))}")
        print(f"   Fournisseurs affectés: {len(analysis_result.get('affected_suppliers', []))}")
        
        # Sauvegarder en BDD
        reco_list = analysis_result.get('recommendations', [])
        reco_text = "\n".join([f"- {r.get('title', r) if isinstance(r, dict) else r}" for r in reco_list]) if isinstance(reco_list, list) else str(reco_list)
        
        risk_analysis = RiskAnalysis(
            document_id=doc.id,
            pertinence_check_id=pertinence.id,
            impacts_description=analysis_result.get('impacts_description', 'Analyse complète'),
            affected_sites=analysis_result.get('affected_sites', []),
            affected_suppliers=analysis_result.get('affected_suppliers', []),
            geographic_analysis=analysis_result.get('geographic_analysis', {}),
            criticality_analysis=analysis_result.get('criticality_analysis', {}),
            risk_level=analysis_result.get('overall_risk_level', 'Moyen'),
            risk_score=analysis_result.get('risk_score_360', 50) / 10,
            supply_chain_impact=analysis_result.get('overall_risk_level', 'moyen').lower(),
            recommendations=reco_text,
            reasoning=f"Score: {analysis_result.get('risk_score_360', 0)}/100",
            llm_model=analysis_result.get('ai_model_used', 'claude'),
            processing_time_ms=int(execution_time * 1000),
            analysis_metadata={
                "source": analysis_result.get('source', {}),
                "generated_by_ai": True,
                "weather_risk_summary": analysis_result.get('weather_risk_summary', {})
            }
        )
        db.add(risk_analysis)
        db.commit()
        print(f"   💾 Sauvegardé: {risk_analysis.id[:8]}...")
        
        # ================================================================
        # ÉTAPE 4 : NOTIFICATION
        # ================================================================
        print("\n" + "=" * 70)
        print("📧 ÉTAPE 4 : Envoi de notification")
        print("=" * 70)
        
        notification_service = NotificationService(dry_run=False)
        
        notif_result = notification_service.notify_risk_analysis(
            document=doc_data,
            risk_analysis=analysis_result,
            pertinence_result=pertinence_data
        )
        
        print(f"   Statut: {notif_result.get('status')}")
        print(f"   Niveau: {notif_result.get('risk_level')}")
        print(f"   Destinataires: {notif_result.get('recipients_count', 0)}")
        
        # ================================================================
        # RÉSUMÉ FINAL
        # ================================================================
        print("\n" + "=" * 70)
        print("📊 RÉSUMÉ DU WORKFLOW")
        print("=" * 70)
        print(f"✅ Agent 1A: {weather_result.get('alerts', {}).get('total', 0)} alertes météo")
        print(f"✅ Agent 2: {analysis_result.get('overall_risk_level')} ({analysis_result.get('risk_score_360')}/100)")
        print(f"✅ Notification: {notif_result.get('status')}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(run_full_workflow())
