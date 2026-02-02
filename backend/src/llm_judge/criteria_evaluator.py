"""
Évaluateur de critères pour le LLM Judge (Anthropic Claude)
"""

import json
import time
from typing import Dict, List, Any
from anthropic import Anthropic, RateLimitError
from .prompts import (
    JUDGE_SYSTEM_PROMPT,
    EVALUATE_PERTINENCE_CHECKER_PROMPT,
    EVALUATE_RISK_ANALYZER_PROMPT
)


class CriteriaEvaluator:
    """
    Évalue les analyses selon les critères définis
    """
    
    def __init__(self, llm_model: str = "claude-sonnet-4-20250514"):
        """
        Initialise l'évaluateur
        
        Args:
            llm_model: Modèle Claude à utiliser
        """
        self.llm_model = llm_model
        self.client = Anthropic()  # API key depuis ANTHROPIC_API_KEY
    
    def _call_with_retry(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.1,
        max_retries: int = 3,
        base_delay: float = 30.0
    ) -> str:
        """
        Appelle l'API Claude avec retry et exponential backoff en cas de rate limit.
        
        Args:
            prompt: Le prompt utilisateur
            system_prompt: Le prompt système
            max_tokens: Nombre max de tokens en sortie
            temperature: Température du modèle
            max_retries: Nombre maximum de tentatives
            base_delay: Délai de base en secondes (doublé à chaque retry)
            
        Returns:
            Texte de la réponse
            
        Raises:
            Exception si tous les retries échouent
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.llm_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()
                
            except RateLimitError as e:
                last_error = e
                delay = base_delay * (2 ** attempt)  # 30s, 60s, 120s
                print(f"   ⚠️ Rate limit atteint. Tentative {attempt + 1}/{max_retries}. Attente de {delay}s...")
                time.sleep(delay)
                
            except Exception as e:
                # Autres erreurs : ne pas réessayer
                raise e
        
        # Tous les retries ont échoué
        raise last_error
    
    def evaluate_pertinence_checker(
        self,
        document: Dict[str, Any],
        pertinence_result: Dict[str, Any],
        sites_count: int,
        suppliers_count: int
    ) -> Dict[str, Any]:
        """
        Évalue la qualité de l'analyse de pertinence (Agent 1B)
        
        Args:
            document: Document source
            pertinence_result: Résultat de l'analyse de pertinence
            sites_count: Nombre de sites Hutchinson
            suppliers_count: Nombre de fournisseurs
            
        Returns:
            Dictionnaire avec les scores pour chaque critère
        """
        prompt = EVALUATE_PERTINENCE_CHECKER_PROMPT.format(
            document=json.dumps(document, indent=2, ensure_ascii=False),
            pertinence_result=json.dumps(pertinence_result, indent=2, ensure_ascii=False),
            sites_count=sites_count,
            suppliers_count=suppliers_count
        )
        
        result_text = self._call_with_retry(
            prompt=prompt,
            system_prompt=JUDGE_SYSTEM_PROMPT,
            max_tokens=4096,
            temperature=0.1
        )
        
        # Parser le JSON
        try:
            # Extraire le JSON si entouré de ```json
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            evaluation = json.loads(result_text)
            return evaluation
        except json.JSONDecodeError as e:
            print(f"Erreur de parsing JSON : {e}")
            print(f"Réponse brute : {result_text}")
            # Retourner une évaluation par défaut
            return self._default_evaluation(4)  # 4 critères pour Pertinence Checker
    
    def evaluate_risk_analyzer(
        self,
        document: Dict[str, Any],
        pertinence_result: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        sites_count: int,
        suppliers_count: int,
        relationships_count: int
    ) -> Dict[str, Any]:
        """
        Évalue la qualité de l'analyse de risque (Agent 2)
        
        Args:
            document: Document source
            pertinence_result: Résultat de l'analyse de pertinence
            risk_analysis: Résultat de l'analyse de risque
            sites_count: Nombre de sites Hutchinson
            suppliers_count: Nombre de fournisseurs
            relationships_count: Nombre de relations site-fournisseur
            
        Returns:
            Dictionnaire avec les scores pour chaque critère
        """
        prompt = EVALUATE_RISK_ANALYZER_PROMPT.format(
            document=json.dumps(document, indent=2, ensure_ascii=False),
            pertinence_result=json.dumps(pertinence_result, indent=2, ensure_ascii=False),
            risk_analysis=json.dumps(risk_analysis, indent=2, ensure_ascii=False),
            sites_count=sites_count,
            suppliers_count=suppliers_count,
            relationships_count=relationships_count
        )
        
        result_text = self._call_with_retry(
            prompt=prompt,
            system_prompt=JUDGE_SYSTEM_PROMPT,
            max_tokens=4096,
            temperature=0.1
        )
        
        # Parser le JSON
        try:
            # Extraire le JSON si entouré de ```json
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            evaluation = json.loads(result_text)
            return evaluation
        except json.JSONDecodeError as e:
            print(f"Erreur de parsing JSON : {e}")
            print(f"Réponse brute : {result_text}")
            # Retourner une évaluation par défaut
            return self._default_evaluation(8)  # 8 critères pour Risk Analyzer
    
    def _default_evaluation(self, num_criteria: int) -> Dict[str, Any]:
        """
        Génère une évaluation par défaut en cas d'erreur
        
        Args:
            num_criteria: Nombre de critères à générer
            
        Returns:
            Dictionnaire d'évaluation par défaut
        """
        criteria_names_4 = [
            "source_relevance",
            "company_data_alignment",
            "logical_coherence",
            "traceability"
        ]
        
        criteria_names_8 = criteria_names_4 + [
            "completeness",
            "recommendation_appropriateness",
            "strategic_alignment",
            "actionability_timeline"
        ]
        
        criteria = criteria_names_4 if num_criteria == 4 else criteria_names_8
        
        return {
            criterion: {
                "score": 5,
                "confidence": 0.5,
                "comment": "Évaluation par défaut (erreur de parsing)",
                "evidence": [],
                "weaknesses": ["Erreur lors de l'évaluation"]
            }
            for criterion in criteria
        }
    
    def extract_scores(self, evaluation: Dict[str, Any]) -> Dict[str, float]:
        """
        Extrait uniquement les scores de l'évaluation
        
        Args:
            evaluation: Dictionnaire d'évaluation complet
            
        Returns:
            Dictionnaire {criterion: score}
        """
        return {
            criterion: data["score"]
            for criterion, data in evaluation.items()
            if isinstance(data, dict) and "score" in data
        }
    
    def calculate_average_confidence(self, evaluation: Dict[str, Any]) -> float:
        """
        Calcule la confiance moyenne de l'évaluation
        
        Args:
            evaluation: Dictionnaire d'évaluation complet
            
        Returns:
            Confiance moyenne (0-1)
        """
        confidences = [
            data["confidence"]
            for data in evaluation.values()
            if isinstance(data, dict) and "confidence" in data
        ]
        
        return round(sum(confidences) / len(confidences), 2) if confidences else 0.5
