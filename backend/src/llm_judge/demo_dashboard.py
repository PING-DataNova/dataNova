"""
Démonstration du dashboard avec tests multiples

Génère plusieurs évaluations pour visualiser les métriques
"""

import sys
from pathlib import Path
import json

# Ajouter le chemin backend au PYTHONPATH (niveau au-dessus de src)
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from src.storage.database import SessionLocal
from src.storage import models
from src.agent_2.agent import Agent2
from src.llm_judge.judge import Judge
from src.llm_judge.metrics_dashboard import JudgeMetricsDashboard


def run_multiple_evaluations():
    """
    Exécute plusieurs évaluations et affiche le dashboard
    """
    print("🔄 Génération d'évaluations de test pour le dashboard...")
    print()
    
    db = SessionLocal()
    
    try:
        # Récupérer tous les documents disponibles
        documents = db.query(models.Document).all()
        
        if not documents:
            print("⚠️  Aucun document trouvé dans la base de données")
            print("   Exécutez d'abord: python populate_test_data.py")
            return
        
        print(f"📄 Trouvé {len(documents)} documents")
        
        # Évaluer chaque document
        agent2 = Agent2()
        judge = Judge()
        
        evaluations_count = 0
        
        for i, doc in enumerate(documents[:5], 1):  # Limiter à 5 pour le démo
            print(f"\n{'='*80}")
            print(f"🔍 Document {i}/{min(len(documents), 5)}: {doc.title[:50]}...")
            print(f"   Type: {doc.event_type}")
            print(f"{'='*80}")
            
            try:
                # Convertir le document en dictionnaire
                doc_dict = {
                    'id': doc.id,
                    'title': doc.title,
                    'event_type': doc.event_type,
                    'content': doc.content,
                    'source_url': doc.source_url,
                    'event_date': doc.event_date.isoformat() if doc.event_date else None,
                    'countries_mentioned': doc.countries_mentioned or [],
                    'sectors_mentioned': doc.sectors_mentioned or [],
                    'is_pertinent': doc.is_pertinent
                }
                
                # Récupérer les entités liées pour Agent 2
                sites = []
                suppliers = []
                
                # Sites proches de l'événement (simulation basique)
                all_sites = db.query(models.Site).all()
                for site in all_sites:
                    site_dict = {
                        'id': site.id,
                        'name': site.name,
                        'country': site.country,
                        'latitude': site.latitude,
                        'longitude': site.longitude,
                        'employee_count': site.employee_count or 0,
                        'annual_production_value': site.annual_production_value or 0,
                        'sectors': site.sectors or [],
                        'raw_materials': site.raw_materials or []
                    }
                    sites.append(site_dict)
                
                # Fournisseurs
                all_suppliers = db.query(models.Supplier).all()
                for supplier in all_suppliers:
                    supplier_dict = {
                        'id': supplier.id,
                        'name': supplier.name,
                        'country': supplier.country,
                        'sector': supplier.sector,
                        'company_size': supplier.company_size,
                        'financial_health': supplier.financial_health
                    }
                    suppliers.append(supplier_dict)
                
                print(f"   Sites: {len(sites)}, Fournisseurs: {len(suppliers)}")
                
                # Exécuter Agent 2
                print(f"\n   🤖 Agent 2 en cours...")
                agent2_result = agent2.analyze(
                    document=doc_dict,
                    impacted_sites=sites[:2],  # Limiter pour performance
                    impacted_suppliers=suppliers[:2]
                )
                
                print(f"   ✓ Agent 2 terminé - Niveau de risque: {agent2_result.get('risk_level', 'N/A')}")
                
                # Exécuter le Judge
                print(f"   ⚖️  Judge en cours...")
                judge_result = judge.evaluate(
                    document=doc_dict,
                    pertinence_analysis={'is_pertinent': doc.is_pertinent, 'reasoning': 'Test'},
                    agent2_analysis=agent2_result
                )
                
                print(f"   ✓ Judge terminé - Score: {judge_result['overall_quality_score']:.2f}/10")
                print(f"              - Décision: {judge_result['action_recommended']}")
                
                # Sauvegarder le résultat
                result_file = Path(__file__).parent / f"judge_result_{doc.id}.json"
                full_result = {
                    'event_id': f"doc_{doc.id}",
                    'event_type': doc.event_type,
                    'document': doc_dict,
                    'agent2_result': agent2_result,
                    'judge_evaluation': judge_result
                }
                
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(full_result, f, indent=2, ensure_ascii=False)
                
                evaluations_count += 1
                
            except Exception as e:
                print(f"   ❌ Erreur lors de l'évaluation: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n{'='*80}")
        print(f"✅ {evaluations_count} évaluations complétées")
        print(f"{'='*80}\n")
        
        # Afficher le dashboard
        print("📊 Génération du dashboard de métriques...\n")
        dashboard = JudgeMetricsDashboard()
        dashboard.display_full_dashboard()
    
    finally:
        db.close()


if __name__ == "__main__":
    run_multiple_evaluations()
