"""
Configuration des poids pour le scoring pondéré du Judge
selon le type de risque (climatique, réglementaire, géopolitique)
"""

from typing import Dict


# Poids pour les risques climatiques
WEIGHTS_CLIMATIQUE: Dict[str, float] = {
    "source_relevance": 1.0,
    "company_data_alignment": 1.5,      # Plus important (géolocalisation GPS)
    "logical_coherence": 1.0,
    "completeness": 1.0,
    "recommendation_appropriateness": 1.2,
    "traceability": 1.5,                # Critique (distance GPS, rayon)
    "strategic_alignment": 1.0,
    "actionability_timeline": 1.3       # Urgence temporelle importante
}

# Poids pour les risques réglementaires
WEIGHTS_REGLEMENTAIRE: Dict[str, float] = {
    "source_relevance": 2.0,            # CRITIQUE (source légale officielle)
    "company_data_alignment": 1.0,
    "logical_coherence": 1.2,
    "completeness": 1.3,                # Tous les aspects légaux doivent être couverts
    "recommendation_appropriateness": 1.0,
    "traceability": 1.8,                # CRITIQUE (références légales exactes)
    "strategic_alignment": 1.0,
    "actionability_timeline": 1.0
}

# Poids pour les risques géopolitiques
WEIGHTS_GEOPOLITIQUE: Dict[str, float] = {
    "source_relevance": 1.5,
    "company_data_alignment": 1.2,
    "logical_coherence": 1.3,           # Analyse complexe multi-niveaux
    "completeness": 1.4,                # Cascade d'impacts à analyser
    "recommendation_appropriateness": 1.5, # Actions stratégiques critiques
    "traceability": 1.2,
    "strategic_alignment": 1.6,         # CRITIQUE (impact stratégique majeur)
    "actionability_timeline": 1.4       # Urgence variable selon le conflit
}

# Mapping type de risque → poids
WEIGHTS_BY_EVENT_TYPE: Dict[str, Dict[str, float]] = {
    "climatique": WEIGHTS_CLIMATIQUE,
    "reglementaire": WEIGHTS_REGLEMENTAIRE,
    "geopolitique": WEIGHTS_GEOPOLITIQUE
}


def get_weights(event_type: str) -> Dict[str, float]:
    """
    Récupère les poids appropriés selon le type d'événement
    
    Args:
        event_type: Type d'événement (climatique, reglementaire, geopolitique)
        
    Returns:
        Dictionnaire des poids pour chaque critère
    """
    return WEIGHTS_BY_EVENT_TYPE.get(event_type, WEIGHTS_CLIMATIQUE)


def calculate_weighted_score(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    """
    Calcule le score global pondéré
    
    Args:
        scores: Dictionnaire {criterion: score (0-10)}
        weights: Dictionnaire {criterion: weight (0.5-2.0)}
        
    Returns:
        Score pondéré (0-10)
    """
    if not scores or not weights:
        return 0.0
    
    total_weighted = sum(scores.get(c, 0) * weights.get(c, 1.0) for c in scores)
    total_weight = sum(weights.get(c, 1.0) for c in scores)
    
    return round(total_weighted / total_weight, 2) if total_weight > 0 else 0.0
