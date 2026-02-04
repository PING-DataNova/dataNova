#!/usr/bin/env python3
"""
Script pour tester uniquement l'Agent 2 et afficher son rapport
"""

import sys
import json
from pathlib import Path

# Ajouter le répertoire backend au path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent_2.agent import Agent2
from src.storage.database import get_session
from src.storage.models import Document, HutchinsonSite, Supplier, SupplierRelationship, PertinenceCheck

def main():
    print("=" * 80)
    print("🧪 TEST AGENT 2 - RAPPORT D'ANALYSE DE RISQUE")
    print("=" * 80)
    print()
    
    session = get_session()
    
    try:
        # Récupérer un document pertinent
        pertinence_check = session.query(PertinenceCheck).filter(
            PertinenceCheck.decision.in_(["OUI", "PARTIELLEMENT"])
        ).first()
        
        if not pertinence_check:
            print("❌ Aucun document pertinent trouvé en BDD")
            print("   Lancez d'abord le workflow complet pour avoir des données")
            return
        
        document = session.query(Document).filter_by(id=pertinence_check.document_id).first()
        
        # Charger les sites et fournisseurs
        sites = session.query(HutchinsonSite).all()
        suppliers = session.query(Supplier).all()
        relationships = session.query(SupplierRelationship).all()
        
        print(f"📄 Document: {document.title}")
        print(f"   Type: {document.event_type}")
        print(f"   Décision pertinence: {pertinence_check.decision} (confiance: {pertinence_check.confidence:.1%})")
        print()
        print(f"🏭 Contexte:")
        print(f"   - {len(sites)} sites Hutchinson")
        print(f"   - {len(suppliers)} fournisseurs")
        print(f"   - {len(relationships)} relations")
        print()
        print("🔄 Analyse en cours avec Agent 2...")
        print()
        
        # Préparer les données pour Agent 2
        doc_dict = {
            "id": str(document.id),
            "title": document.title,
            "event_type": document.event_type,
            "event_subtype": document.event_subtype,
            "summary": document.summary,
            "content": document.content,
            "source_url": document.source_url,
            "publication_date": str(document.publication_date) if document.publication_date else None,
            "geographic_scope": document.geographic_scope if document.geographic_scope else {},
            "extra_metadata": document.extra_metadata if document.extra_metadata else {}
        }
        
        pertinence_dict = {
            "decision": pertinence_check.decision,
            "confidence": pertinence_check.confidence,
            "reasoning": pertinence_check.reasoning,
            "affected_sites": pertinence_check.affected_sites if pertinence_check.affected_sites else [],
            "affected_suppliers": pertinence_check.affected_suppliers if pertinence_check.affected_suppliers else []
        }
        
        sites_list = [{
            "id": s.id,
            "name": s.name,
            "country": s.country,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "products": s.products if s.products else [],
            "employee_count": s.employee_count,
            "daily_revenue": s.daily_revenue
        } for s in sites]
        
        suppliers_list = [{
            "id": sup.id,
            "name": sup.name,
            "country": sup.country,
            "latitude": sup.latitude,
            "longitude": sup.longitude,
            "products_supplied": sup.products_supplied if sup.products_supplied else []
        } for sup in suppliers]
        
        relationships_list = [{
            "hutchinson_site_id": r.hutchinson_site_id,
            "supplier_id": r.supplier_id,
            "products_supplied": r.products_supplied if r.products_supplied else [],
            "criticality": r.criticality,
            "is_sole_supplier": r.is_sole_supplier,
            "lead_time_days": r.lead_time_days
        } for r in relationships]
        
        # Lancer Agent 2
        agent2 = Agent2()
        risk_analysis, risk_projections = agent2.analyze(
            document=doc_dict,
            pertinence_result=pertinence_dict,
            sites=sites_list,
            suppliers=suppliers_list,
            supplier_relationships=relationships_list
        )
        
        # AFFICHER LE RAPPORT COMPLET (avec les 7 sections)
        print("=" * 100)
        print("📊 RAPPORT D'ANALYSE DÉTAILLÉ - AGENT 2")
        print("=" * 100)
        print()
        print("⚠️  Ce rapport a été généré automatiquement par une IA")
        print(f"    Modèle utilisé: {risk_analysis.get('recommendations_model', 'N/A')}")
        print(f"    Date de génération: {risk_analysis.get('analysis_timestamp', 'N/A')}")
        print()
        
        # SECTION 1: CONTEXTE ET ENJEUX
        if risk_analysis.get('context_and_stakes'):
            print("=" * 100)
            print("SECTION 1 : CONTEXTE ET ENJEUX")
            print("=" * 100)
            print()
            print(risk_analysis['context_and_stakes'])
            print()
        
        # SECTION 2: ENTITÉS AFFECTÉES (DÉTAILS)
        if risk_analysis.get('affected_entities_details'):
            print("=" * 100)
            print("SECTION 2 : ENTITÉS AFFECTÉES (LISTE COMPLÈTE)")
            print("=" * 100)
            print()
            print(risk_analysis['affected_entities_details'])
            print()
        
        # SECTION 3: ANALYSE FINANCIÈRE
        if risk_analysis.get('financial_analysis'):
            print("=" * 100)
            print("SECTION 3 : ANALYSE FINANCIÈRE DÉTAILLÉE")
            print("=" * 100)
            print()
            print(risk_analysis['financial_analysis'])
            print()
        
        # SECTION 4: RECOMMANDATIONS (existant)
        print("=" * 100)
        print("SECTION 4 : RECOMMANDATIONS PRIORITAIRES")
        print("=" * 100)
        print()
        recommendations = risk_analysis.get("recommendations", [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. [{rec.get('urgency', 'N/A')}] {rec.get('title', rec.get('action', 'Action non spécifiée'))}")
                if rec.get('timeline'):
                    print(f"   Délai: {rec.get('timeline')}")
                if rec.get('owner'):
                    print(f"   Responsable: {rec.get('owner')}")
                if rec.get('budget_eur'):
                    print(f"   Budget: {rec.get('budget_eur'):,.0f}€")
                if rec.get('roi'):
                    print(f"   ROI: {rec.get('roi')}")
                if rec.get('expected_impact'):
                    print(f"   Impact attendu: {rec.get('expected_impact')}")
        else:
            print("⚠️  Aucune recommandation générée")
        print()
        
        # SECTION 5: TIMELINE
        if risk_analysis.get('timeline'):
            print("=" * 100)
            print("SECTION 5 : TIMELINE DES ACTIONS")
            print("=" * 100)
            print()
            print(risk_analysis['timeline'])
            print()
        
        # SECTION 6: MATRICE DE PRIORISATION
        if risk_analysis.get('prioritization_matrix'):
            print("=" * 100)
            print("SECTION 6 : MATRICE DE PRIORISATION")
            print("=" * 100)
            print()
            print(risk_analysis['prioritization_matrix'])
            print()
        
        # SECTION 7: SCÉNARIO "NE RIEN FAIRE"
        if risk_analysis.get('do_nothing_scenario'):
            print("=" * 100)
            print('SECTION 7 : SCÉNARIO "NE RIEN FAIRE"')
            print("=" * 100)
            print()
            print(risk_analysis['do_nothing_scenario'])
            print()
        
        # SYNTHÈSE FINALE
        print("=" * 100)
        print("📊 SYNTHÈSE")
        print("=" * 100)
        print()
        print(f"📋 DOCUMENT: {doc_dict['title'][:100]}...")
        print(f"   Type: {doc_dict['event_type'].upper()} / {doc_dict.get('event_subtype', 'N/A')}")
        print()
        print("🎯 SCORES:")
        print(f"   • Niveau de risque: {risk_analysis.get('overall_risk_level', 'N/A')}")
        print(f"   • Score de risque 360°: {risk_analysis.get('risk_score_360', 0):.2f}/100")
        print(f"   • Score business interruption: {risk_analysis.get('business_interruption_score', 0):.2f}/100")
        print()
        print(f"🏭 ENTITÉS AFFECTÉES:")
        print(f"   • Sites: {len(risk_analysis.get('affected_sites', []))}")
        print(f"   • Fournisseurs: {len(risk_analysis.get('affected_suppliers', []))}")
        print()
        print(f"📈 PROJECTIONS:")
        print(f"   • Total: {len(risk_projections)} entités analysées")
        high_risk = [p for p in risk_projections if p.get("risk_score", 0) >= 70]
        print(f"   • Entités à haut risque (≥70): {len(high_risk)}")
        print()
        print("=" * 100)
        print(f"✅ Rapport généré par PING v1.0 | Modèle: {risk_analysis.get('recommendations_model', 'N/A')} | ID: {risk_analysis.get('document_id', 'N/A')}")
        print("=" * 100)
        
    finally:
        session.close()


if __name__ == "__main__":
    main()
