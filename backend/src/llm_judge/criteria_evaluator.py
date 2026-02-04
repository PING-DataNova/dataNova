"""
Évaluateur de critères pour le LLM Judge (Anthropic Claude)
"""

import json
import time
import os
from typing import Dict, List, Any
from .prompts import (
    JUDGE_SYSTEM_PROMPT,
    EVALUATE_PERTINENCE_CHECKER_PROMPT,
    EVALUATE_RISK_ANALYZER_PROMPT
)


class CriteriaEvaluator:
    """
    Évalue les analyses selon les critères définis
    """
    
    def __init__(self, llm_model: str = None):
        """
        Initialise l'évaluateur
        
        Args:
            llm_model: Modèle à utiliser (optionnel)
        """
        # Le Judge utilise OpenAI par défaut pour éviter les rate limits Anthropic
        self.llm_provider = os.getenv("JUDGE_LLM_PROVIDER", "openai").lower()
        
        if self.llm_provider == "openai":
            from openai import OpenAI
            self.llm_model = llm_model or os.getenv("JUDGE_MODEL", "gpt-4o-mini")
            self.client = OpenAI()
        else:
            from anthropic import Anthropic
            self.llm_model = llm_model or "claude-sonnet-4-20250514"
            self.client = Anthropic()
    
    def _condense_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un résumé condensé du document pour réduire les tokens
        """
        content = document.get('content', '')
        summary = document.get('summary', '')
        
        return {
            "id": document.get('id', 'unknown'),
            "title": document.get('title', '')[:200],
            "event_type": document.get('event_type', ''),
            "event_subtype": document.get('event_subtype', ''),
            "source_url": document.get('source_url', ''),
            "publication_date": document.get('publication_date', ''),
            "summary": (summary or content)[:1000] + "..." if len(summary or content) > 1000 else (summary or content)
        }
    
    def _condense_pertinence_result(self, pertinence_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un résumé condensé du résultat de pertinence
        """
        reasoning = pertinence_result.get('reasoning', '')
        
        return {
            "decision": pertinence_result.get('decision', ''),
            "confidence": pertinence_result.get('confidence', 0),
            "reasoning": reasoning[:500] + "..." if len(reasoning) > 500 else reasoning,
            "affected_sites_count": len(pertinence_result.get('affected_sites', [])),
            "affected_suppliers_count": len(pertinence_result.get('affected_suppliers', [])),
            "matched_elements_count": len(pertinence_result.get('matched_elements', []))
        }
    
    def _condense_risk_analysis(self, risk_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un résumé condensé de l'analyse de risque pour réduire les tokens.
        N'inclut que les métriques clés, pas le texte des 7 sections.
        """
        # Résumer les recommandations (juste titres et urgences)
        recommendations = risk_analysis.get('recommendations', [])
        if isinstance(recommendations, dict):
            recommendations = recommendations.get('recommendations', [])
        
        condensed_recommendations = []
        for rec in recommendations[:5]:  # Max 5 recommandations
            if isinstance(rec, dict):
                condensed_recommendations.append({
                    "title": rec.get('title', rec.get('action', ''))[:100],
                    "urgency": rec.get('urgency', 'N/A'),
                    "timeline": rec.get('timeline', 'N/A'),
                    "budget_eur": rec.get('budget_eur', 0)
                })
        
        return {
            "overall_risk_level": risk_analysis.get('overall_risk_level', 'N/A'),
            "risk_score": risk_analysis.get('risk_score', 0),
            "risk_score_360": risk_analysis.get('risk_score_360', 0),
            "business_interruption_score": risk_analysis.get('business_interruption_score', 0),
            "affected_sites_count": risk_analysis.get('affected_sites_count', 0),
            "affected_suppliers_count": risk_analysis.get('affected_suppliers_count', 0),
            "recommendations_count": len(recommendations),
            "recommendations_summary": condensed_recommendations,
            "has_context_and_stakes": bool(risk_analysis.get('context_and_stakes')),
            "has_financial_analysis": bool(risk_analysis.get('financial_analysis')),
            "has_timeline": bool(risk_analysis.get('timeline')),
            "has_do_nothing_scenario": bool(risk_analysis.get('do_nothing_scenario')),
            "weather_risk_summary": {
                "total_alerts": risk_analysis.get('weather_risk_summary', {}).get('total_alerts', 0),
                "entities_with_alerts": risk_analysis.get('weather_risk_summary', {}).get('entities_with_alerts', 0)
            }
        }
    
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
                if self.llm_provider == "openai":
                    response = self.client.chat.completions.create(
                        model=self.llm_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    return response.choices[0].message.content.strip()
                else:
                    from anthropic import RateLimitError
                    response = self.client.messages.create(
                        model=self.llm_model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system=system_prompt,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return response.content[0].text.strip()
                
            except Exception as e:
                # Gérer les rate limits
                if "rate" in str(e).lower() or "429" in str(e):
                    last_error = e
                    delay = base_delay * (2 ** attempt)
                    print(f"   ⚠️ Rate limit atteint. Tentative {attempt + 1}/{max_retries}. Attente de {delay}s...")
                    time.sleep(delay)
                else:
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
