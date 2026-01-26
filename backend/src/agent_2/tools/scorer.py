"""
Outil : Calcul du score et de la criticité

TODO (Dev 4): Implémenter le scoring

Formule du score (0-1) basée sur :
- Volume impacté (fournisseurs, produits)
- Impact financier estimé
- Délai d'application de la réglementation
- Complexité de mise en conformité

Criticité :
- CRITICAL: score >= 0.8
- HIGH: score >= 0.6
- MEDIUM: score >= 0.4
- LOW: score < 0.4
"""

from langchain.tools import tool


@tool
def calculate_score(
    affected_suppliers_count: int,
    affected_products_count: int,
    financial_impact: float,
    deadline_days: int
) -> dict:
    """
    TODO: Calculer le score d'impact et la criticité
    
    Args:
        affected_suppliers_count: Nombre de fournisseurs impactés
        affected_products_count: Nombre de produits impactés
        financial_impact: Impact financier estimé (€)
        deadline_days: Jours avant l'échéance réglementaire
    
    Returns:
        Dict avec:
        - total_score: float (0-1)
        - criticality: str (CRITICAL/HIGH/MEDIUM/LOW)
        - reasoning: str (explication du calcul)
    """
    # TODO: Implémenter la formule de scoring
    raise NotImplementedError("Dev 4: Implémenter calculate_score")
