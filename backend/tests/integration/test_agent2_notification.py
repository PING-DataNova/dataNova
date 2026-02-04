#!/usr/bin/env python3
"""
Test du workflow Agent 2 + Notification sur un document pertinent existant.
Skip Agent 1A et 1B car les documents sont déjà collectés et évalués.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from datetime import datetime
import structlog

from src.storage.database import SessionLocal
from src.storage.models import Document, PertinenceCheck, RiskAnalysis, HutchinsonSite, Supplier, SupplierRelationship
from src.agent_2.agent import Agent2
from src.notifications.notification_service import NotificationService

logger = structlog.get_logger()

async def test_agent2_and_notification():
    """Test Agent 2 sur un document pertinent puis envoie notification."""
    
    db = SessionLocal()
    
    try:
        # 1. Trouver un document pertinent non analysé
        print("=" * 70)
        print("🔍 RECHERCHE D'UN DOCUMENT PERTINENT NON ANALYSÉ")
        print("=" * 70)
        
        # Documents pertinents (OUI ou PARTIELLEMENT)
        pertinent_checks = db.query(PertinenceCheck).filter(
            PertinenceCheck.decision.in_(['OUI', 'PARTIELLEMENT'])
        ).all()
        
        print(f"Documents pertinents trouvés: {len(pertinent_checks)}")
        
        # Trouver ceux sans analyse
        analyzed_ids = [r[0] for r in db.query(RiskAnalysis.document_id).all()]
        
        doc_to_analyze = None
        pertinence_check = None
        
        for pc in pertinent_checks:
            if pc.document_id not in analyzed_ids:
                doc_to_analyze = db.query(Document).filter(Document.id == pc.document_id).first()
                pertinence_check = pc
                break
        
        if not doc_to_analyze:
            print("❌ Aucun document pertinent non analysé trouvé!")
            return
        
        print(f"\n📄 Document sélectionné:")
        print(f"   ID: {doc_to_analyze.id}")
        print(f"   Titre: {doc_to_analyze.title[:80]}...")
        print(f"   Type: {doc_to_analyze.event_type}")
        print(f"   Pertinence: {pertinence_check.decision} (confiance: {pertinence_check.confidence})")
        
        # 2. Lancer Agent 2
        print("\n" + "=" * 70)
        print("🤖 LANCEMENT DE L'AGENT 2 (Risk Analyzer)")
        print("=" * 70)
        
        agent2 = Agent2()
        
        # Charger les données métier
        sites = db.query(HutchinsonSite).filter(HutchinsonSite.active == True).all()
        suppliers = db.query(Supplier).filter(Supplier.active == True).all()
        relationships = db.query(SupplierRelationship).filter(SupplierRelationship.active == True).all()
        
        print(f"   Sites chargés: {len(sites)}")
        print(f"   Fournisseurs chargés: {len(suppliers)}")
        print(f"   Relations chargées: {len(relationships)}")
        
        # Convertir en dicts
        sites_data = [
            {
                "id": s.id, "name": s.name, "code": s.code, "country": s.country,
                "region": s.region, "city": s.city, "latitude": s.latitude,
                "longitude": s.longitude, "sectors": s.sectors, "products": s.products,
                "strategic_importance": s.strategic_importance,
                "daily_revenue": s.daily_revenue, "safety_stock_days": s.safety_stock_days
            } for s in sites
        ]
        
        suppliers_data = [
            {
                "id": s.id, "name": s.name, "code": s.code, "country": s.country,
                "region": s.region, "city": s.city, "latitude": s.latitude,
                "longitude": s.longitude, "sector": s.sector,
                "products_supplied": s.products_supplied, "criticality_score": s.criticality_score
            } for s in suppliers
        ]
        
        relationships_data = [
            {
                "hutchinson_site_id": r.hutchinson_site_id, "supplier_id": r.supplier_id,
                "products_supplied": r.products_supplied, "criticality": r.criticality,
                "is_sole_supplier": r.is_sole_supplier, "has_backup_supplier": r.has_backup_supplier
            } for r in relationships
        ]
        
        # Préparer les données pour Agent 2
        doc_data = {
            "id": doc_to_analyze.id,
            "title": doc_to_analyze.title,
            "content": doc_to_analyze.content,
            "event_type": doc_to_analyze.event_type,
            "source_url": doc_to_analyze.source_url,
            "celex_id": doc_to_analyze.extra_metadata.get("celex_id") if doc_to_analyze.extra_metadata else None,
            "publication_date": str(doc_to_analyze.publication_date) if doc_to_analyze.publication_date else None,
            "metadata": doc_to_analyze.extra_metadata
        }
        
        pertinence_data = {
            "id": pertinence_check.id,
            "decision": pertinence_check.decision,
            "confidence": pertinence_check.confidence,
            "reasoning": pertinence_check.reasoning,
            "matched_elements": pertinence_check.matched_elements,
            "affected_sites": pertinence_check.affected_sites,
            "affected_suppliers": pertinence_check.affected_suppliers
        }
        
        start_time = datetime.now()
        
        # Appel Agent 2 (synchrone, pas async)
        analysis_result, projections = agent2.analyze(
            document=doc_data,
            pertinence_result=pertinence_data,
            sites=sites_data,
            suppliers=suppliers_data,
            supplier_relationships=relationships_data
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ Analyse terminée en {execution_time:.2f}s")
        print(f"   Niveau de risque: {analysis_result.get('overall_risk_level', 'N/A')}")
        print(f"   Score risque 360°: {analysis_result.get('risk_score_360', 0)}/100")
        print(f"   Sites affectés: {len(analysis_result.get('affected_sites', []))}")
        print(f"   Fournisseurs affectés: {len(analysis_result.get('affected_suppliers', []))}")
        print(f"   Projections générées: {len(projections)}")
        
        # Vérifier les nouveaux champs (source, generated_by_ai)
        if 'source' in analysis_result:
            print(f"\n📚 Source:")
            source = analysis_result['source']
            print(f"   URL: {source.get('url', 'N/A')}")
            print(f"   Extrait: {source.get('excerpt', 'N/A')[:100]}...")
        
        if analysis_result.get('generated_by_ai'):
            print(f"\n🤖 Généré par IA: {analysis_result.get('ai_model_used', 'N/A')}")
        
        # 3. Sauvegarder en BDD
        print("\n" + "=" * 70)
        print("💾 SAUVEGARDE EN BASE DE DONNÉES")
        print("=" * 70)
        
        import json
        
        # Convertir les recommandations en texte
        reco_list = analysis_result.get('recommendations', [])
        if isinstance(reco_list, list):
            reco_text = "\n".join([f"- {r.get('title', r) if isinstance(r, dict) else r}" for r in reco_list])
        else:
            reco_text = str(reco_list)
        
        risk_analysis = RiskAnalysis(
            document_id=doc_to_analyze.id,
            pertinence_check_id=pertinence_check.id,
            impacts_description=analysis_result.get('impacts_description', 'Analyse de risque complète'),
            affected_sites=analysis_result.get('affected_sites', []),
            affected_suppliers=analysis_result.get('affected_suppliers', []),
            geographic_analysis=analysis_result.get('geographic_analysis', {}),
            criticality_analysis=analysis_result.get('criticality_analysis', {}),
            risk_level=analysis_result.get('overall_risk_level', 'Moyen'),
            risk_score=analysis_result.get('risk_score_360', 50) / 10,  # Convertir en 0-10
            supply_chain_impact=analysis_result.get('overall_risk_level', 'moyen').lower(),
            recommendations=reco_text,
            reasoning=f"Analyse générée par Agent 2. Score: {analysis_result.get('risk_score_360', 0)}/100",
            llm_model=analysis_result.get('ai_model_used', 'claude-3-5-sonnet'),
            llm_tokens=analysis_result.get('llm_tokens'),
            processing_time_ms=int(execution_time * 1000),
            analysis_metadata={
                "source": analysis_result.get('source', {}),
                "generated_by_ai": analysis_result.get('generated_by_ai', True),
                "weather_risk_summary": analysis_result.get('weather_risk_summary', {}),
                "business_interruption": {
                    "score": analysis_result.get('business_interruption_score', 0),
                    "disruption_days": analysis_result.get('estimated_disruption_days', 0),
                    "revenue_impact": analysis_result.get('revenue_impact_percentage', 0)
                }
            }
        )
        
        db.add(risk_analysis)
        db.commit()
        
        print(f"✅ Analyse sauvegardée avec ID: {risk_analysis.id}")
        
        # 4. Envoyer notification
        print("\n" + "=" * 70)
        print("📧 ENVOI DE LA NOTIFICATION")
        print("=" * 70)
        
        notification_service = NotificationService(dry_run=False)  # Envoi réel
        
        try:
            notification_result = notification_service.notify_risk_analysis(
                document=doc_data,
                risk_analysis=analysis_result,
                pertinence_result=pertinence_data
            )
            print(f"✅ Notification: {notification_result.get('status', 'unknown')}")
            print(f"   Niveau de risque: {notification_result.get('risk_level', 'N/A')}")
            print(f"   Destinataires: {notification_result.get('recipients_count', 0)}")
            if notification_result.get('emails_sent'):
                print(f"   Emails envoyés: {notification_result.get('emails_sent')}")
        except Exception as e:
            print(f"⚠️  Notification erreur: {e}")
            import traceback
            traceback.print_exc()
        
        # 5. Résumé final
        print("\n" + "=" * 70)
        print("📊 RÉSUMÉ DU TEST")
        print("=" * 70)
        print(f"✅ Document analysé: {doc_to_analyze.title[:50]}...")
        print(f"✅ Niveau de risque: {analysis_result.get('overall_risk_level')}")
        print(f"✅ Score: {analysis_result.get('risk_score_360')}/100")
        print(f"✅ Analyse sauvegardée en BDD")
        print(f"✅ Temps total: {execution_time:.2f}s")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "🚀" * 35)
    print("   TEST AGENT 2 + NOTIFICATION")
    print("🚀" * 35 + "\n")
    
    asyncio.run(test_agent2_and_notification())
