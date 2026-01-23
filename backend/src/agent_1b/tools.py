"""
Outils LangChain pour l'Agent 1B

Chaque outil implémente une partie de l'analyse de pertinence.
"""

from langchain_core.tools import tool

# TODO: Implémenter les outils suivants (DEV 2)


@tool
def filter_by_keywords(document_content: str, keywords: list[str]) -> dict:
    """
    Filtre un document par mots-clés (Niveau 1).
    
    Args:
        document_content: Contenu textuel du document
        keywords: Liste des mots-clés à rechercher
    
    Returns:
        dict: Score de correspondance (0-1) et mots-clés trouvés
    """
    # TODO: Implémenter le filtrage par mots-clés
    return {"keyword_score": 0.0, "matched_keywords": [], "status": "not_implemented"}


@tool
def verify_nc_codes(document_content: str, target_nc_codes: list[str]) -> dict:
    """
    Vérifie la présence de codes NC dans le document (Niveau 2).
    
    Args:
        document_content: Contenu textuel du document
        target_nc_codes: Codes NC de l'entreprise (ex: ["4002.19"])
    
    Returns:
        dict: Score de correspondance (0-1) et codes trouvés
    """
    # TODO: Implémenter la vérification des codes NC
    return {"nc_code_score": 0.0, "found_codes": [], "status": "not_implemented"}


@tool
def semantic_analysis(document_content: str, company_context: str) -> dict:
    """
    Analyse sémantique approfondie par LLM (Niveau 3).
    
    Args:
        document_content: Contenu du document
        company_context: Contexte de l'entreprise (secteur, produits, supply chain)
    
    Returns:
        dict: Score sémantique (0-1), raison, et impacts potentiels
    """
    # TODO: Implémenter l'analyse sémantique avec Claude
    return {
        "semantic_score": 0.0,
        "reasoning": "",
        "potential_impacts": [],
        "status": "not_implemented"
    }


@tool
def calculate_relevance_score(
    keyword_score: float,
    nc_code_score: float,
    semantic_score: float
) -> dict:
    """
    Calcule le score de pertinence global pondéré.
    
    Args:
        keyword_score: Score du filtrage mots-clés (0-1)
        nc_code_score: Score des codes NC (0-1)
        semantic_score: Score de l'analyse sémantique (0-1)
    
    Returns:
        dict: Score final et niveau de criticité
    """
    # TODO: Implémenter le calcul du score avec les poids configurés
    return {
        "final_score": 0.0,
        "criticality": "LOW",
        "status": "not_implemented"
    }


@tool
def generate_alert(analysis_result: dict, document_metadata: dict) -> dict:
    """
    Génère une alerte structurée en JSON.
    
    Args:
        analysis_result: Résultat de l'analyse (scores, criticité)
        document_metadata: Métadonnées du document
    
    Returns:
        dict: Alerte structurée prête à être envoyée
    """
    # TODO: Implémenter la génération d'alertes
    return {"alert": {}, "status": "not_implemented"}


@tool
def save_analysis(document_id: str, analysis_result: dict) -> dict:
    """
    Sauvegarde le résultat de l'analyse dans la base de données.
    
    Args:
        document_id: Identifiant du document
        analysis_result: Résultat complet de l'analyse
    
    Returns:
        dict: Confirmation de la sauvegarde
    """
    # TODO: Implémenter la sauvegarde
    return {"saved": False, "status": "not_implemented"}


def get_agent_1b_tools() -> list:
    """Retourne la liste des outils disponibles pour l'Agent 1B."""
    return [
        filter_by_keywords,
        verify_nc_codes,
        semantic_analysis,
        calculate_relevance_score,
        generate_alert,
        save_analysis,
    ]
