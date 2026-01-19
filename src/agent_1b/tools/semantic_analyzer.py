"""
Semantic Analyzer - Agent 1B Tool (Niveau 3)

Analyse sémantique approfondie par LLM (Claude).
Évalue la pertinence du document pour l'entreprise.

Pondération: 50% du score final

Responsable: Dev 2 (Nora)
"""

import os
import re
import json
from typing import Dict, List, Any, Optional
import structlog
from anthropic import Anthropic

logger = structlog.get_logger()

# Instance LLM globale (lazy init)
_llm_instance: Optional[Anthropic] = None


def _get_llm() -> Anthropic:
    """Lazy initialization du client Anthropic."""
    global _llm_instance
    if _llm_instance is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        _llm_instance = Anthropic(api_key=api_key)
        logger.info("semantic_analyzer_llm_initialized", model="claude-sonnet-4-5-20250929")
    return _llm_instance


async def semantic_analysis(
    text: str,
    title: str,
    matched_keywords: List[str],
    matched_nc_codes: List[str],
    company_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Niveau 3 : Analyse sémantique par LLM
    
    Utilise Claude pour évaluer la pertinence du document
    pour l'entreprise en fonction de son contexte métier.
    
    Args:
        text: Extrait du document (limité à 5000 chars)
        title: Titre du document
        matched_keywords: Mots-clés trouvés (niveau 1)
        matched_nc_codes: Codes NC matchés (niveau 2)
        company_context: Contexte entreprise {
            "name": str,
            "sector": str,
            "products": list,
            "countries": list,
            "nc_codes": list
        }
    
    Returns:
        dict: {
            "score": float (0-1),
            "reasoning": str (explication 2-3 phrases),
            "impacts": list (impacts potentiels)
        }
    """
    llm = _get_llm()
    
    # Construire le contexte entreprise
    context = f"""Entreprise : {company_context.get('name', 'N/A')}
Secteur : {company_context.get('sector', 'N/A')}
Produits : {', '.join(company_context.get('products', [])[:3])}
Pays fournisseurs : {', '.join(company_context.get('countries', [])[:5])}
Codes NC : {', '.join(company_context.get('nc_codes', [])[:5])}
"""
    
    prompt = f"""Analyse ce document réglementaire pour déterminer sa pertinence pour l'entreprise.

{context}

DOCUMENT:
Titre: {title}
Keywords trouvés: {', '.join(matched_keywords[:10])}
Codes NC matchés: {', '.join(matched_nc_codes)}

Extrait:
{text[:5000]}

TÂCHE:
1. Score de pertinence (0.0 à 1.0) - 1.0 = très pertinent, 0.0 = pas pertinent
2. Raison en 2-3 phrases expliquant pourquoi
3. Impacts potentiels pour l'entreprise (liste de 1-3 items)

IMPORTANT: Réponds UNIQUEMENT avec du JSON valide, sans texte avant ou après.
Format JSON attendu:
{{
  "score": 0.8,
  "reasoning": "Ce règlement concerne...",
  "impacts": ["Impact 1", "Impact 2"]
}}
"""
    
    try:
        response = llm.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=500,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Extraire le JSON de la réponse
        content = response.content[0].text
        
        # Chercher le JSON dans la réponse (Claude peut ajouter du texte autour)
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
            result = json.loads(json_str)
        else:
            # Fallback: essayer de parser directement
            result = json.loads(content)
        
        logger.debug(
            "semantic_analysis_completed",
            score=result.get("score", 0.0),
            reasoning_length=len(result.get("reasoning", ""))
        )
        
        return {
            "score": float(result.get("score", 0.0)),
            "reasoning": result.get("reasoning", ""),
            "impacts": result.get("impacts", [])
        }
    
    except json.JSONDecodeError as e:
        logger.error("semantic_analysis_json_error", error=str(e), content_preview=content[:200] if 'content' in locals() else 'N/A')
        return {
            "score": 0.0,
            "reasoning": f"Erreur parsing JSON: {str(e)}",
            "impacts": []
        }
    except Exception as e:
        logger.error("semantic_analysis_failed", error=str(e))
        return {
            "score": 0.0,
            "reasoning": f"Erreur analyse: {str(e)}",
            "impacts": []
        }
