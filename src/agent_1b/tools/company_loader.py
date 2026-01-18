"""
Company Loader Tool - Agent 1B

Charge les profils d'entreprise depuis data/company_profiles/
et extrait les données pertinentes pour l'analyse de documents.

Responsable: Dev 1
"""

import json
import structlog
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = structlog.get_logger()


def load_company_profile(company_id: str) -> Dict[str, Any]:
    """
    Charge le profil d'une entreprise depuis data/company_profiles/
    
    Args:
        company_id: ID de l'entreprise (ex: "GMG-001")
    
    Returns:
        Dictionnaire avec le profil complet de l'entreprise
    
    Raises:
        FileNotFoundError: Si le profil n'existe pas
        json.JSONDecodeError: Si le JSON est invalide
    """
    
    logger.info("loading_company_profile", company_id=company_id)
    
    profile_path = Path("data/company_profiles")
    
    if not profile_path.exists():
        logger.error("company_profiles_directory_not_found", path=str(profile_path))
        raise FileNotFoundError(f"Répertoire {profile_path} non trouvé")
    
    # Chercher le fichier JSON correspondant
    for file in profile_path.glob("*.json"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get("company_id") == company_id:
                    logger.info("company_profile_loaded", company_id=company_id, file=str(file))
                    return data
        except json.JSONDecodeError as e:
            logger.warning("invalid_json_in_profile", file=str(file), error=str(e))
            continue
    
    logger.error("company_profile_not_found", company_id=company_id)
    raise FileNotFoundError(f"Profil d'entreprise {company_id} non trouvé dans {profile_path}")


def extract_analysis_profile(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrait les données pertinentes pour l'analyse de documents
    
    Args:
        company_data: Données complètes de l'entreprise
    
    Returns:
        Profil simplifié pour l'Agent 1B avec:
        - company_id
        - name
        - sector
        - zones_operation
        - keywords (mots-clés de conformité)
        - nc_codes (codes NC pertinents)
        - regulations (réglementations suivies)
        - activities (activités métier)
    """
    
    logger.info("extracting_analysis_profile", company_id=company_data.get("company_id"))
    
    company_id = company_data.get("company_id")
    
    # Extraire les codes NC des activités
    nc_codes = _extract_nc_codes_from_activities(
        company_data.get("business_model", {}).get("activities", [])
    )
    
    # Extraire les mots-clés des fonctions de conformité
    keywords = _extract_keywords_from_compliance(
        company_data.get("compliance_functions", [])
    )
    
    # Extraire les réglementations
    regulations = _extract_regulations(company_data)
    
    profile = {
        "company_id": company_id,
        "name": company_data.get("name", "Unknown"),
        "sector": company_data.get("sector", "Unknown"),
        "zones_operation": company_data.get("zones_operation", []),
        "keywords": keywords,
        "nc_codes": nc_codes,
        "regulations": regulations,
        "activities": company_data.get("business_model", {}).get("activities", []),
        "countries": _extract_countries(company_data)
    }
    
    logger.info(
        "analysis_profile_extracted",
        company_id=company_id,
        keywords_count=len(keywords),
        nc_codes_count=len(nc_codes),
        regulations_count=len(regulations)
    )
    
    return profile


def _extract_nc_codes_from_activities(activities: List[str]) -> List[str]:
    """
    Extrait les codes NC pertinents des activités métier
    
    Args:
        activities: Liste des activités de l'entreprise
    
    Returns:
        Liste des codes NC pertinents
    """
    
    # Mapping des mots-clés vers codes NC
    nc_mapping = {
        "matière première": ["2606", "2804", "2701"],
        "métaux": ["7606", "7210", "7225", "7326"],
        "acier": ["7210", "7225", "7226"],
        "aluminium": ["7606", "7607", "7608"],
        "composants électroniques": ["8542", "8541", "8517"],
        "équipements": ["8704", "8705", "8706"],
        "électromécanique": ["8501", "8502", "8503"],
        "bois": ["4401", "4402", "4403"],
        "import": ["all"],  # Tous les codes peuvent être importés
        "export": ["all"],
        "fabrication": ["all"],
        "assemblage": ["all"]
    }
    
    codes = set()
    
    for activity in activities:
        activity_lower = activity.lower()
        
        for keyword, nc_codes in nc_mapping.items():
            if keyword in activity_lower:
                if "all" not in nc_codes:
                    codes.update(nc_codes)
    
    logger.info("nc_codes_extracted", count=len(codes), codes=list(codes))
    
    return sorted(list(codes))


def _extract_keywords_from_compliance(compliance_functions: List[str]) -> List[str]:
    """
    Extrait les mots-clés pertinents des fonctions de conformité
    
    Args:
        compliance_functions: Liste des fonctions de conformité
    
    Returns:
        Liste des mots-clés pertinents
    """
    
    keywords = set()
    
    for func in compliance_functions:
        func_lower = func.lower()
        
        # CBAM (Carbon Border Adjustment Mechanism)
        if "cbam" in func_lower or "carbon border" in func_lower:
            keywords.update([
                "CBAM",
                "carbon",
                "border",
                "adjustment",
                "mechanism",
                "emissions",
                "tariff",
                "import",
                "export"
            ])
        
        # EUDR (EU Deforestation Regulation)
        if "eudr" in func_lower or "deforestation" in func_lower:
            keywords.update([
                "EUDR",
                "deforestation",
                "forest",
                "timber",
                "wood",
                "supply chain",
                "due diligence"
            ])
        
        # CSRD (Corporate Sustainability Reporting Directive)
        if "csrd" in func_lower or "sustainability reporting" in func_lower:
            keywords.update([
                "CSRD",
                "sustainability",
                "reporting",
                "ESG",
                "environment",
                "social",
                "governance"
            ])
        
        # ESG / Environnemental
        if "esg" in func_lower or "environnemental" in func_lower or "environmental" in func_lower:
            keywords.update([
                "ESG",
                "environment",
                "emissions",
                "CO2",
                "carbon",
                "sustainability",
                "green"
            ])
        
        # Douanes / Commerce
        if "douane" in func_lower or "customs" in func_lower or "tariff" in func_lower:
            keywords.update([
                "douane",
                "customs",
                "tariff",
                "import",
                "export",
                "HS code",
                "origin",
                "preference"
            ])
        
        # Due Diligence / Supply Chain
        if "due diligence" in func_lower or "supply chain" in func_lower or "fournisseur" in func_lower:
            keywords.update([
                "due diligence",
                "supply chain",
                "fournisseur",
                "supplier",
                "traçabilité",
                "traceability",
                "audit"
            ])
        
        # Sanctions / Compliance
        if "sanction" in func_lower or "embargo" in func_lower or "screening" in func_lower:
            keywords.update([
                "sanctions",
                "embargo",
                "screening",
                "compliance",
                "risk"
            ])
    
    logger.info("keywords_extracted", count=len(keywords), keywords=sorted(list(keywords)))
    
    return sorted(list(keywords))


def _extract_regulations(company_data: Dict[str, Any]) -> List[str]:
    """
    Extrait les réglementations pertinentes pour l'entreprise
    
    Args:
        company_data: Données complètes de l'entreprise
    
    Returns:
        Liste des réglementations pertinentes
    """
    
    regulations = set()
    
    # Analyser les fonctions de conformité
    compliance = " ".join(company_data.get("compliance_functions", [])).lower()
    
    if "cbam" in compliance or "carbon border" in compliance:
        regulations.add("CBAM")
    
    if "eudr" in compliance or "deforestation" in compliance:
        regulations.add("EUDR")
    
    if "csrd" in compliance or "sustainability reporting" in compliance:
        regulations.add("CSRD")
    
    if "esg" in compliance or "environnemental" in compliance:
        regulations.add("ESG")
    
    if "douane" in compliance or "customs" in compliance:
        regulations.add("Customs")
    
    if "due diligence" in compliance or "supply chain" in compliance:
        regulations.add("Due Diligence")
    
    # Analyser le secteur
    sector = company_data.get("sector", "").lower()
    
    if "manufacture" in sector or "production" in sector:
        regulations.add("Manufacturing")
    
    if "import" in sector or "export" in sector or "trade" in sector:
        regulations.add("Trade")
    
    logger.info("regulations_extracted", count=len(regulations), regulations=sorted(list(regulations)))
    
    return sorted(list(regulations))


def _extract_countries(company_data: Dict[str, Any]) -> List[str]:
    """
    Extrait les pays d'opération de l'entreprise
    
    Args:
        company_data: Données complètes de l'entreprise
    
    Returns:
        Liste des pays d'opération
    """
    
    countries = set()
    
    # Ajouter le pays du siège
    if company_data.get("headquarters", {}).get("country"):
        countries.add(company_data["headquarters"]["country"])
    
    # Ajouter les pays des entités
    for entity in company_data.get("entities", []):
        if entity.get("country"):
            countries.add(entity["country"])
    
    # Ajouter les pays des sites
    for site in company_data.get("sites", {}).get("factories", []):
        if "location" in site:
            # Extraire le pays de la location (ex: "Lyon, France" → "France")
            location_parts = site["location"].split(",")
            if len(location_parts) > 1:
                countries.add(location_parts[-1].strip())
    
    for site in company_data.get("sites", {}).get("warehouses", []):
        if "location" in site:
            location_parts = site["location"].split(",")
            if len(location_parts) > 1:
                countries.add(location_parts[-1].strip())
    
    logger.info("countries_extracted", count=len(countries), countries=sorted(list(countries)))
    
    return sorted(list(countries))