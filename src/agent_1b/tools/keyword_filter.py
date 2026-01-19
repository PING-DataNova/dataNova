"""
Keyword Filter - Agent 1B Tool (Niveau 1)

Filtrage des documents par mots-clés de l'entreprise.
Score = ratio mots-clés trouvés / total mots-clés entreprise.

Responsable: Dev 2 (Nora)
"""

import re
from typing import Dict, List, Any
import structlog

logger = structlog.get_logger()


def filter_by_keywords(
    text: str,
    company_keywords: List[str]
) -> Dict[str, Any]:
    """
    Niveau 1 : Filtrage par mots-clés
    
    Recherche les mots-clés de l'entreprise dans le texte du document.
    Score basé sur le ratio de mots-clés trouvés.
    
    Args:
        text: Contenu textuel du document
        company_keywords: Liste des mots-clés de surveillance de l'entreprise
    
    Returns:
        dict: {
            "score": float (0-1),
            "matched": list (mots-clés trouvés),
            "total_keywords": int
        }
    
    Example:
        >>> result = filter_by_keywords("CBAM carbon border...", ["cbam", "carbon", "rubber"])
        >>> result["score"]
        0.67
    """
    text_lower = text.lower()
    matched_keywords = []
    
    for keyword in company_keywords:
        if keyword and keyword in text_lower:
            matched_keywords.append(keyword)
    
    # Score = ratio mots-clés trouvés
    score = len(matched_keywords) / max(len(company_keywords), 1)
    
    logger.debug(
        "keyword_filter_completed",
        matched=len(matched_keywords),
        total=len(company_keywords),
        score=round(score, 3)
    )
    
    return {
        "score": min(score, 1.0),  # Cap à 1.0
        "matched": matched_keywords[:20],  # Top 20
        "total_keywords": len(company_keywords)
    }
