"""
Outil : Calcul du score (deprecie)

Ce projet ne conserve plus de score chiffre pour Agent 2.
Le fichier est conserve pour compatibilite et pourra etre supprime plus tard.
"""

from langchain.tools import tool


@tool
def calculate_score(*_args, **_kwargs) -> dict:
    """Outil deprecie. Retourne un message d'indisponibilite."""
    return {
        "status": "deprecated",
        "message": "Scoring retire: utiliser les metriques d'impact sans score chiffre."
    }
