import json
import structlog
import re
from typing import Dict, List, Any, Optional
from langchain_anthropic import ChatAnthropic
from src.config import settings

logger = structlog.get_logger()

class SemanticAnalyzerResult:
    def __init__(self, is_relevant: bool, confidence: float, matched_keywords: List[str], matched_nc_codes: List[str], summary: str, reasoning: str):
        self.is_relevant = is_relevant
        self.confidence = confidence
        self.matched_keywords = matched_keywords
        self.matched_nc_codes = matched_nc_codes
        self.summary = summary
        self.reasoning = reasoning
    
    def to_dict(self) -> dict:
        return {
            "is_relevant": self.is_relevant,
            "confidence": self.confidence,
            "matched_keywords": self.matched_keywords,
            "matched_nc_codes": self.matched_nc_codes,
            "summary": self.summary,
            "reasoning": self.reasoning
        }

async def analyze_document_relevance(content: str, title: str, company_profile: Dict[str, Any], nc_codes: Optional[List[str]] = None) -> SemanticAnalyzerResult:
    if not content or not content.strip():
        return SemanticAnalyzerResult(False, 0.0, [], [], "Contenu vide", "Impossible d'analyser")
    
    try:
        llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            temperature=0.3,
            max_tokens=1500,
            api_key=settings.anthropic_api_key,
            timeout=60,
            max_retries=2
        )
        
        prompt = f"""Analyse ce document pour {company_profile.get('name', 'Unknown')}:

Titre: {title}
Contenu: {content[:4000]}

Codes NC de l'entreprise: {', '.join(company_profile.get('nc_codes', []))}
Mots-clés: {', '.join(company_profile.get('keywords', []))}

Retourne UNIQUEMENT du JSON:
{{"is_relevant": true/false, "confidence": 0.0-1.0, "matched_keywords": [], "matched_nc_codes": [], "summary": "...", "reasoning": "..."}}
"""
        
        response = await llm.ainvoke([{"role": "user", "content": prompt}])
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        try:
            result_dict = json.loads(response_text)
        except:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            result_dict = json.loads(json_match.group(0)) if json_match else {}
        
        return SemanticAnalyzerResult(
            is_relevant=result_dict.get("is_relevant", False),
            confidence=float(result_dict.get("confidence", 0.0)),
            matched_keywords=result_dict.get("matched_keywords", []),
            matched_nc_codes=result_dict.get("matched_nc_codes", []),
            summary=result_dict.get("summary", ""),
            reasoning=result_dict.get("reasoning", "")
        )
    except Exception as e:
        logger.error("semantic_analysis_error", error=str(e))
        return SemanticAnalyzerResult(False, 0.0, [], [], f"Erreur: {str(e)[:100]}", "Impossible d'analyser")
