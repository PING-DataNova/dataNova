"""
NC Code Verifier - Agent 1B Tool (Niveau 2)

Vérification de la présence de codes NC (Nomenclature Combinée) 
dans les documents réglementaires.

Responsable: Dev 2 (Nora)
"""

import re
from typing import Dict, List, Any, Set
import structlog

logger = structlog.get_logger()


def verify_nc_codes(
    text: str,
    extracted_nc_codes: List[str],
    company_nc_codes: List[str]
) -> Dict[str, Any]:
    """
    Niveau 2 : Vérification codes NC
    
    Compare les codes NC extraits du document avec ceux de l'entreprise.
    Cherche également les codes NC directement dans le texte.
    
    Args:
        text: Texte du document
        extracted_nc_codes: Codes NC extraits par Agent 1A
        company_nc_codes: Codes NC de l'entreprise (imports/exports)
    
    Returns:
        dict: {
            "score": float (0-1),
            "found": list (codes matchés),
            "company_codes": list (codes entreprise, max 10)
        }
    
    Example:
        >>> result = verify_nc_codes("CN code 4002.19...", ["4002.19"], ["4002.19", "7208"])
        >>> result["score"]
        0.5
    """
    # Intersection codes Agent 1A et codes entreprise
    doc_codes_set: Set[str] = set(extracted_nc_codes)
    company_codes_set: Set[str] = set(company_nc_codes)
    
    # Chercher aussi dans le texte directement
    # Pattern: NC/CN/TARIC suivi de 4 chiffres, optionnellement .XX.XX
    nc_pattern = r'\b(?:NC|CN|TARIC)\s*[:\-]?\s*(\d{4}(?:\.\d{2})?(?:\.\d{2})?)'
    found_in_text = re.findall(nc_pattern, text, re.IGNORECASE)
    
    # Union de tous les codes trouvés
    all_found = doc_codes_set.union(set(found_in_text))
    
    # Intersection avec codes entreprise
    matched_codes = all_found.intersection(company_codes_set)
    
    # Score basé sur le nombre de codes matchés
    if len(company_codes_set) > 0:
        score = len(matched_codes) / len(company_codes_set)
    else:
        score = 0.0
    
    logger.debug(
        "nc_code_verification_completed",
        matched=len(matched_codes),
        company_total=len(company_codes_set),
        score=round(score, 3)
    )
    
    return {
        "score": min(score, 1.0),
        "found": list(matched_codes),
        "company_codes": list(company_codes_set)[:10]
    }
