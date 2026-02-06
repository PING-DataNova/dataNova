#!/usr/bin/env python
"""Test Agent 1B avec 100% LLM scoring"""
import sys
sys.path.insert(0, '/Users/noradossou-gbete/Documents/Projet_PING/dataNova/backend')

from src.storage.database import SessionLocal
from src.storage.models import Document, PertinenceCheck

def show_stats():
    session = SessionLocal()
    total_docs = session.query(Document).count()
    total_checks = session.query(PertinenceCheck).count()
    oui = session.query(PertinenceCheck).filter(PertinenceCheck.decision=='OUI').count()
    part = session.query(PertinenceCheck).filter(PertinenceCheck.decision=='PARTIELLEMENT').count()
    non = session.query(PertinenceCheck).filter(PertinenceCheck.decision=='NON').count()
    
    print(f'\n=== STATISTIQUES ACTUELLES ===')
    print(f'Documents: {total_docs} | Analyses: {total_checks}')
    print(f'OUI: {oui} | PARTIELLEMENT: {part} | NON: {non}')
    
    # Docs sans analyse
    unanalyzed = session.query(Document).outerjoin(
        PertinenceCheck, Document.id == PertinenceCheck.document_id
    ).filter(PertinenceCheck.id.is_(None)).count()
    print(f'Documents sans analyse: {unanalyzed}')
    session.close()
    return unanalyzed

def run_agent1b_test(limit=5):
    """Teste Agent 1B sur quelques documents"""
    from src.agent_1b.agent import Agent1B
    
    session = SessionLocal()
    agent = Agent1B()
    
    # Prendre quelques documents non analysés
    unanalyzed_docs = session.query(Document).outerjoin(
        PertinenceCheck, Document.id == PertinenceCheck.document_id
    ).filter(PertinenceCheck.id.is_(None)).limit(limit).all()
    
    print(f'\n=== TEST AGENT 1B (100% LLM) sur {len(unanalyzed_docs)} docs ===\n')
    
    results = {"OUI": 0, "PARTIELLEMENT": 0, "NON": 0}
    
    for doc in unanalyzed_docs:
        print(f'Analysing: {doc.title[:60]}...')
        try:
            result = agent.check_pertinence(doc.id, save_to_db=True)
            decision = result['decision']
            score = result['confidence']
            results[decision] += 1
            status = '✅' if decision == 'OUI' else ('⚠️' if decision == 'PARTIELLEMENT' else '❌')
            print(f'  {status} {decision} (score: {score:.2f})')
        except Exception as e:
            print(f'  ❌ Erreur: {e}')
    
    print(f'\n=== RÉSULTATS TEST ===')
    print(f'OUI: {results["OUI"]} | PARTIELLEMENT: {results["PARTIELLEMENT"]} | NON: {results["NON"]}')
    
    session.close()

def reanalyze_documents(limit=10):
    """Ré-analyse des documents avec le nouveau scoring 100% LLM"""
    from src.agent_1b.agent import Agent1B
    
    session = SessionLocal()
    agent = Agent1B()
    
    # Prendre des documents déjà analysés (NON ou PARTIELLEMENT)
    old_checks = session.query(PertinenceCheck).filter(
        PertinenceCheck.decision.in_(['NON', 'PARTIELLEMENT'])
    ).limit(limit).all()
    
    print(f'\n=== RE-ANALYSE avec 100% LLM ({len(old_checks)} docs) ===\n')
    
    changes = {"upgraded": 0, "same": 0, "downgraded": 0}
    
    for check in old_checks:
        doc = check.document
        old_decision = check.decision
        old_conf = check.confidence
        
        print(f'Doc: {doc.title[:50]}...')
        print(f'  Avant: {old_decision} ({old_conf:.2f})')
        
        try:
            # Supprimer l'ancienne analyse pour forcer re-calcul
            session.delete(check)
            session.commit()
            
            # Re-analyser
            result = agent.check_pertinence(doc.id, save_to_db=True)
            new_decision = result['decision']
            new_conf = result['confidence']
            
            status = '✅' if new_decision == 'OUI' else ('⚠️' if new_decision == 'PARTIELLEMENT' else '❌')
            print(f'  Après: {status} {new_decision} ({new_conf:.2f})')
            
            # Comparer
            rankings = {'NON': 0, 'PARTIELLEMENT': 1, 'OUI': 2}
            if rankings[new_decision] > rankings[old_decision]:
                changes['upgraded'] += 1
                print(f'  ⬆️ UPGRADED!')
            elif rankings[new_decision] < rankings[old_decision]:
                changes['downgraded'] += 1
            else:
                changes['same'] += 1
            print()
                
        except Exception as e:
            print(f'  ❌ Erreur: {e}')
            session.rollback()
    
    print(f'\n=== RÉSUMÉ CHANGEMENTS ===')
    print(f'Upgraded: {changes["upgraded"]} | Same: {changes["same"]} | Downgraded: {changes["downgraded"]}')
    
    session.close()

if __name__ == "__main__":
    show_stats()
    reanalyze_documents(100)  # Tous les documents NON
    print('\n=== APRÈS RE-ANALYSE ===')
    show_stats()
