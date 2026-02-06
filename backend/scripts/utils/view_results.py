#!/usr/bin/env python3
"""Script pour visualiser les résultats du workflow."""

from src.storage.database import SessionLocal
from src.storage.models import RiskAnalysis, Document, PertinenceCheck, JudgeEvaluation
import json

def main():
    db = SessionLocal()
    
    # Analyse de risque
    analysis = db.query(RiskAnalysis).first()
    if analysis:
        print("=" * 70)
        print("ANALYSE DE RISQUE SAUVEGARDEE")
        print("=" * 70)
        print(f"ID: {analysis.id}")
        print(f"Document: {analysis.document_id}")
        print(f"Risk Score: {analysis.risk_score}/10")
        print(f"Risk Level: {analysis.risk_level}")
        print(f"Supply Chain Impact: {analysis.supply_chain_impact}")
        print()
        
        # Entites affectees
        affected_sites = analysis.affected_sites or []
        affected_suppliers = analysis.affected_suppliers or []
        print("Entites affectees:")
        print(f"   - Sites: {len(affected_sites)}")
        print(f"   - Fournisseurs: {len(affected_suppliers)}")
        
        # Recommendations stockees
        if analysis.recommendations:
            print()
            print("-" * 50)
            print("RECOMMANDATIONS (stockees):")
            print("-" * 50)
            print(analysis.recommendations[:2000])
        
        # Reasoning
        if analysis.reasoning:
            print()
            print("-" * 50)
            print("REASONING:")
            print("-" * 50)
            print(analysis.reasoning[:2000])
    
    # Judge evaluation
    judge = db.query(JudgeEvaluation).first()
    if judge:
        print()
        print("=" * 70)
        print("EVALUATION JUDGE")
        print("=" * 70)
        print(f"Score: {judge.weighted_score}/10")
        print(f"Action: {judge.action}")
        print(f"Confiance: {judge.confidence}")
    else:
        print()
        print("Pas d'evaluation Judge sauvegardee (erreur rate limit)")
    
    db.close()

if __name__ == "__main__":
    main()
