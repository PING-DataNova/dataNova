"""
Système de feedback loop pour l'amélioration continue du Judge
"""

from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict


class JudgeFeedbackLoop:
    """
    Système d'amélioration continue du Judge basé sur les validations humaines
    """
    
    def __init__(self):
        """
        Initialise le feedback loop
        """
        self.disagreements: List[Dict[str, Any]] = []
        self.ground_truth_cases: List[Dict[str, Any]] = []
        self.adjustments_history: List[Dict[str, Any]] = []
    
    def log_disagreement(
        self,
        case_id: str,
        judge_decision: str,
        human_decision: str,
        human_reasoning: str,
        judge_score: float,
        human_score: float = None
    ):
        """
        Enregistre un désaccord entre le Judge et l'humain
        
        Args:
            case_id: Identifiant du cas
            judge_decision: Décision du Judge (APPROVE/REVIEW/REJECT)
            human_decision: Décision de l'humain
            human_reasoning: Raisonnement de l'humain
            judge_score: Score global du Judge
            human_score: Score global de l'humain (optionnel)
        """
        disagreement = {
            "case_id": case_id,
            "judge_decision": judge_decision,
            "human_decision": human_decision,
            "human_reasoning": human_reasoning,
            "judge_score": judge_score,
            "human_score": human_score,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        self.disagreements.append(disagreement)
        
        print(f"⚠️  Désaccord enregistré pour {case_id}:")
        print(f"   Judge: {judge_decision} (score: {judge_score})")
        print(f"   Humain: {human_decision}")
        
        # Tous les 10 désaccords, analyser et ajuster
        if len(self.disagreements) % 10 == 0:
            print(f"\n🔄 Analyse de {len(self.disagreements)} désaccords...")
            self.analyze_and_adjust()
    
    def log_agreement(
        self,
        case_id: str,
        decision: str,
        score: float
    ):
        """
        Enregistre un accord entre le Judge et l'humain
        
        Args:
            case_id: Identifiant du cas
            decision: Décision commune
            score: Score du Judge
        """
        self.ground_truth_cases.append({
            "case_id": case_id,
            "decision": decision,
            "score": score,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    
    def analyze_and_adjust(self):
        """
        Analyse les désaccords et propose des ajustements
        """
        if len(self.disagreements) < 10:
            print("   ⏳ Pas assez de désaccords pour analyser (minimum 10)")
            return
        
        # Analyser les 10 derniers désaccords
        recent_disagreements = self.disagreements[-10:]
        
        # Identifier les patterns
        patterns = self._identify_patterns(recent_disagreements)
        
        print(f"\n📊 Patterns identifiés:")
        for pattern in patterns:
            print(f"   - {pattern['type']}: {pattern['count']} cas")
            print(f"     Critère: {pattern.get('criterion', 'N/A')}")
            print(f"     Recommandation: {pattern['recommendation']}")
        
        # Enregistrer les ajustements
        adjustment = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "disagreements_analyzed": len(recent_disagreements),
            "patterns": patterns
        }
        
        self.adjustments_history.append(adjustment)
    
    def _identify_patterns(self, disagreements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identifie les patterns dans les désaccords
        
        Args:
            disagreements: Liste des désaccords récents
            
        Returns:
            Liste des patterns identifiés
        """
        patterns = []
        
        # Pattern 1 : Judge trop optimiste (APPROVE → REJECT/REVIEW)
        over_optimistic = [
            d for d in disagreements
            if d['judge_decision'] == 'APPROVE' and d['human_decision'] in ['REJECT', 'REVIEW']
        ]
        
        if len(over_optimistic) >= 3:
            patterns.append({
                "type": "over_optimistic",
                "count": len(over_optimistic),
                "recommendation": "Augmenter les seuils de décision (8.5 → 9.0 pour APPROVE)"
            })
        
        # Pattern 2 : Judge trop strict (REJECT → APPROVE/REVIEW)
        under_optimistic = [
            d for d in disagreements
            if d['judge_decision'] == 'REJECT' and d['human_decision'] in ['APPROVE', 'REVIEW']
        ]
        
        if len(under_optimistic) >= 3:
            patterns.append({
                "type": "under_optimistic",
                "count": len(under_optimistic),
                "recommendation": "Réduire les seuils de décision (7.0 → 6.5 pour REJECT)"
            })
        
        # Pattern 3 : Scores trop élevés
        score_diff = [
            d for d in disagreements
            if d.get('human_score') and d['judge_score'] - d['human_score'] > 1.5
        ]
        
        if len(score_diff) >= 3:
            patterns.append({
                "type": "score_inflation",
                "count": len(score_diff),
                "recommendation": "Ajuster les prompts pour être plus critique"
            })
        
        # Pattern 4 : Scores trop bas
        score_deflation = [
            d for d in disagreements
            if d.get('human_score') and d['human_score'] - d['judge_score'] > 1.5
        ]
        
        if len(score_deflation) >= 3:
            patterns.append({
                "type": "score_deflation",
                "count": len(score_deflation),
                "recommendation": "Ajuster les prompts pour être moins strict"
            })
        
        return patterns
    
    def calculate_judge_accuracy(self) -> float:
        """
        Calcule la précision du Judge par rapport aux validations humaines
        
        Returns:
            Précision (0-1)
        """
        total_cases = len(self.disagreements) + len(self.ground_truth_cases)
        
        if total_cases == 0:
            return 1.0
        
        correct_decisions = len(self.ground_truth_cases)
        
        return round(correct_decisions / total_cases, 3)
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Récupère les métriques de performance du Judge
        
        Returns:
            Dictionnaire des métriques
        """
        total_cases = len(self.disagreements) + len(self.ground_truth_cases)
        
        if total_cases == 0:
            return {
                "total_cases": 0,
                "judge_accuracy": 1.0,
                "false_approve_rate": 0.0,
                "false_reject_rate": 0.0,
                "total_adjustments": 0
            }
        
        # False Approve Rate : APPROVE → REJECT/REVIEW
        false_approves = len([
            d for d in self.disagreements
            if d['judge_decision'] == 'APPROVE' and d['human_decision'] in ['REJECT', 'REVIEW']
        ])
        
        # False Reject Rate : REJECT → APPROVE/REVIEW
        false_rejects = len([
            d for d in self.disagreements
            if d['judge_decision'] == 'REJECT' and d['human_decision'] in ['APPROVE', 'REVIEW']
        ])
        
        return {
            "total_cases": total_cases,
            "agreements": len(self.ground_truth_cases),
            "disagreements": len(self.disagreements),
            "judge_accuracy": self.calculate_judge_accuracy(),
            "false_approve_rate": round(false_approves / total_cases, 3),
            "false_reject_rate": round(false_rejects / total_cases, 3),
            "total_adjustments": len(self.adjustments_history)
        }
