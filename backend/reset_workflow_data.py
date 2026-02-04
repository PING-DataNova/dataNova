#!/usr/bin/env python3
"""
Script pour réinitialiser les données du workflow PING
Supprime les documents et analyses pour permettre un re-scraping complet
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.storage.database import get_session
from src.storage.models import Document, PertinenceCheck, RiskAnalysis, JudgeEvaluation, RiskProjection

def reset_workflow_data():
    session = get_session()
    
    try:
        # Compter avant suppression
        docs_count = session.query(Document).count()
        pertinence_count = session.query(PertinenceCheck).count()
        risk_count = session.query(RiskAnalysis).count()
        judge_count = session.query(JudgeEvaluation).count()
        proj_count = session.query(RiskProjection).count()
        
        print("=" * 60)
        print("📊 ÉTAT ACTUEL DE LA BASE:")
        print("=" * 60)
        print(f"   - Documents: {docs_count}")
        print(f"   - PertinenceCheck: {pertinence_count}")
        print(f"   - RiskAnalysis: {risk_count}")
        print(f"   - JudgeEvaluation: {judge_count}")
        print(f"   - RiskProjection: {proj_count}")
        
        if docs_count == 0:
            print("\n✅ La base est déjà vide, rien à supprimer.")
            return
        
        # Supprimer dans l'ordre (contraintes FK)
        print("\n🗑️  SUPPRESSION EN COURS...")
        
        deleted_judge = session.query(JudgeEvaluation).delete()
        print(f"   - JudgeEvaluation supprimés: {deleted_judge}")
        
        deleted_proj = session.query(RiskProjection).delete()
        print(f"   - RiskProjection supprimés: {deleted_proj}")
        
        deleted_risk = session.query(RiskAnalysis).delete()
        print(f"   - RiskAnalysis supprimés: {deleted_risk}")
        
        deleted_pertinence = session.query(PertinenceCheck).delete()
        print(f"   - PertinenceCheck supprimés: {deleted_pertinence}")
        
        deleted_docs = session.query(Document).delete()
        print(f"   - Documents supprimés: {deleted_docs}")
        
        session.commit()
        
        print("\n" + "=" * 60)
        print("✅ TABLES VIDÉES AVEC SUCCÈS!")
        print("=" * 60)
        print("   Le workflow va maintenant re-collecter les documents depuis EUR-Lex")
        print("   Lancez: python -m src.orchestration.langgraph_workflow")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ ERREUR: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    reset_workflow_data()
