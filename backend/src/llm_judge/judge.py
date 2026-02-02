"""
Agent 3 : LLM Judge - Évaluation de la qualité des analyses (Anthropic Claude)
"""

import json
import time
from typing import Dict, List, Any
from datetime import datetime
from anthropic import Anthropic

from .criteria_evaluator import CriteriaEvaluator
from .weights_config import get_weights, calculate_weighted_score
from .prompts import JUDGE_SYSTEM_PROMPT, FINAL_DECISION_PROMPT


class Judge:
    """
    Agent Judge qui évalue la qualité des analyses de pertinence et de risque
    """
    
    def __init__(self, llm_model: str = "claude-sonnet-4-20250514"):
        """
        Initialise le Judge
        
        Args:
            llm_model: Modèle Claude à utiliser
        """
        self.llm_model = llm_model
        self.client = Anthropic()
        self.evaluator = CriteriaEvaluator(llm_model)
    
    def evaluate(
        self,
        document: Dict[str, Any],
        pertinence_result: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        sites: List[Dict],
        suppliers: List[Dict],
        supplier_relationships: List[Dict]
    ) -> Dict[str, Any]:
        """
        Évalue la qualité complète de l'analyse (Pertinence + Risque)
        
        Args:
            document: Document source
            pertinence_result: Résultat de l'analyse de pertinence (Agent 1B)
            risk_analysis: Résultat de l'analyse de risque (Agent 2)
            sites: Liste des sites Hutchinson
            suppliers: Liste des fournisseurs
            supplier_relationships: Liste des relations site-fournisseur
            
        Returns:
            Évaluation complète avec scores, décision et métadonnées
        """
        print(f"\n🎯 Évaluation Judge pour document: {document.get('id', 'unknown')}")
        print(f"   Type d'événement: {document.get('event_type', 'unknown')}")
        
        # 1. Évaluer le Pertinence Checker (Agent 1B)
        print("\n📋 Évaluation du Pertinence Checker...")
        pertinence_eval = self.evaluator.evaluate_pertinence_checker(
            document=document,
            pertinence_result=pertinence_result,
            sites_count=len(sites),
            suppliers_count=len(suppliers)
        )
        
        # Calculer le score pondéré pour Pertinence Checker
        event_type = document.get('event_type', 'climatique')
        weights = get_weights(event_type)
        
        pertinence_scores = self.evaluator.extract_scores(pertinence_eval)
        # Filtrer uniquement les critères applicables au Pertinence Checker
        pertinence_weights = {k: v for k, v in weights.items() if k in pertinence_scores}
        pertinence_weighted_score = calculate_weighted_score(pertinence_scores, pertinence_weights)
        pertinence_confidence = self.evaluator.calculate_average_confidence(pertinence_eval)
        
        pertinence_eval['weighted_score'] = pertinence_weighted_score
        pertinence_eval['confidence_overall'] = pertinence_confidence
        
        print(f"   ✅ Score pondéré: {pertinence_weighted_score}/10")
        print(f"   ✅ Confiance: {pertinence_confidence}")
        
        # Délai entre les appels API pour éviter le rate limit
        print("   ⏳ Pause de 5s avant l'évaluation du Risk Analyzer...")
        time.sleep(5)
        
        # 2. Évaluer le Risk Analyzer (Agent 2)
        print("\n📊 Évaluation du Risk Analyzer...")
        risk_eval = self.evaluator.evaluate_risk_analyzer(
            document=document,
            pertinence_result=pertinence_result,
            risk_analysis=risk_analysis,
            sites_count=len(sites),
            suppliers_count=len(suppliers),
            relationships_count=len(supplier_relationships)
        )
        
        # Calculer le score pondéré pour Risk Analyzer
        risk_scores = self.evaluator.extract_scores(risk_eval)
        risk_weighted_score = calculate_weighted_score(risk_scores, weights)
        risk_confidence = self.evaluator.calculate_average_confidence(risk_eval)
        
        risk_eval['weighted_score'] = risk_weighted_score
        risk_eval['confidence_overall'] = risk_confidence
        
        print(f"   ✅ Score pondéré: {risk_weighted_score}/10")
        print(f"   ✅ Confiance: {risk_confidence}")
        
        # 3. Calculer le score global
        overall_score = round((pertinence_weighted_score + risk_weighted_score) / 2, 2)
        overall_confidence = round((pertinence_confidence + risk_confidence) / 2, 2)
        
        print(f"\n🎯 Score global: {overall_score}/10")
        print(f"🎯 Confiance globale: {overall_confidence}")
        
        # 4. Déterminer l'action recommandée
        print("\n🤔 Détermination de l'action...")
        decision = self._determine_action(
            pertinence_weighted_score,
            pertinence_confidence,
            risk_weighted_score,
            risk_confidence,
            overall_score,
            overall_confidence
        )
        
        print(f"   ✅ Action: {decision['action_recommended']}")
        print(f"   📝 Raisonnement: {decision['reasoning']}")
        
        # 5. Construire le résultat final
        result = {
            "event_id": document.get('id', 'unknown'),
            "event_type": event_type,
            "judge_evaluation": {
                "pertinence_checker_evaluation": pertinence_eval,
                "risk_analyzer_evaluation": risk_eval,
                "overall_quality_score": overall_score,
                "overall_confidence": overall_confidence,
                "action_recommended": decision['action_recommended'],
                "reasoning": decision['reasoning'],
                "metadata": {
                    "judge_model": self.llm_model,
                    "evaluation_timestamp": datetime.utcnow().isoformat() + "Z",
                    "weights_used": event_type,
                    "total_criteria_evaluated": len(pertinence_scores) + len(risk_scores)
                }
            }
        }
        
        return result
    
    def _determine_action(
        self,
        pertinence_score: float,
        pertinence_confidence: float,
        risk_score: float,
        risk_confidence: float,
        overall_score: float,
        overall_confidence: float
    ) -> Dict[str, str]:
        """
        Détermine l'action recommandée basée sur les scores et la confiance
        
        Args:
            pertinence_score: Score pondéré du Pertinence Checker
            pertinence_confidence: Confiance du Pertinence Checker
            risk_score: Score pondéré du Risk Analyzer
            risk_confidence: Confiance du Risk Analyzer
            overall_score: Score global
            overall_confidence: Confiance globale
            
        Returns:
            Dictionnaire avec action_recommended et reasoning
        """
        prompt = FINAL_DECISION_PROMPT.format(
            pertinence_score=pertinence_score,
            pertinence_confidence=pertinence_confidence,
            risk_score=risk_score,
            risk_confidence=risk_confidence,
            overall_score=overall_score,
            overall_confidence=overall_confidence
        )
        
        response = self.client.messages.create(
            model=self.llm_model,
            max_tokens=1024,
            temperature=0.0,  # Déterministe pour la décision
            system=JUDGE_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        result_text = response.content[0].text.strip()
        
        # Parser le JSON
        try:
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            decision = json.loads(result_text)
            return decision
        except json.JSONDecodeError:
            # Décision par défaut basée sur les règles
            if overall_score >= 8.5 and overall_confidence >= 0.85:
                action = "APPROVE"
                reasoning = f"Score global de {overall_score} (≥ 8.5) avec confiance élevée ({overall_confidence} ≥ 0.85)."
            elif overall_score >= 8.5 and overall_confidence < 0.85:
                action = "REVIEW"
                reasoning = f"Score global élevé ({overall_score}) mais confiance faible ({overall_confidence} < 0.85)."
            elif 7.0 <= overall_score < 8.5 and overall_confidence >= 0.80:
                action = "REVIEW"
                reasoning = f"Score global acceptable ({overall_score}) avec confiance correcte ({overall_confidence})."
            elif 7.0 <= overall_score < 8.5 and overall_confidence < 0.80:
                action = "REVIEW_PRIORITY"
                reasoning = f"Score global acceptable ({overall_score}) mais confiance faible ({overall_confidence})."
            else:
                action = "REJECT"
                reasoning = f"Score global insuffisant ({overall_score} < 7.0)."
            
            return {
                "action_recommended": action,
                "reasoning": reasoning
            }
