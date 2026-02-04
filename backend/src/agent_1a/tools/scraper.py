# src/agent_1a/tools/scraper.py

import requests
from lxml import etree
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel
import os
from pathlib import Path
from dotenv import load_dotenv
import structlog
import re

logger = structlog.get_logger()

# Charger le .env depuis le dossier backend (racine du projet)
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

EURLEX_API_USERNAME = os.getenv("EURLEX_API_USERNAME")
EURLEX_API_PASSWORD = os.getenv("EURLEX_API_PASSWORD")
EURLEX_SOAP_URL = os.getenv("EURLEX_SOAP_URL", "https://eur-lex.europa.eu/EURLexWebService")
EURLEX_API_RATE_LIMIT = int(os.getenv("EURLEX_API_RATE_LIMIT", "500"))

# ========================================
# LISTE DES RÉGLEMENTATIONS EUROPÉENNES
# Chaque réglementation a son mot-clé de recherche EUR-Lex
# ========================================

REGULATIONS_CONFIG = {
    # === Environnement & Climat ===
    "CBAM": {
        "name": "Carbon Border Adjustment Mechanism",
        "search_keywords": ["CBAM", "carbon border adjustment"],
        "description": "Taxe carbone aux frontières sur imports (acier, aluminium, ciment, électricité, engrais, hydrogène)"
    },
    "EU_ETS": {
        "name": "EU Emissions Trading System",
        "search_keywords": ["emission trading", "ETS", "allowances trading"],
        "description": "Système d'échange de quotas d'émission de CO2"
    },
    "F_GAS": {
        "name": "F-Gas Regulation",
        "search_keywords": ["fluorinated greenhouse gases", "F-gas"],
        "description": "Réduction des gaz fluorés à effet de serre"
    },
    "RED": {
        "name": "Renewable Energy Directive",
        "search_keywords": ["renewable energy directive"],
        "description": "Directive sur les énergies renouvelables"
    },
    "IED": {
        "name": "Industrial Emissions Directive",
        "search_keywords": ["industrial emissions directive"],
        "description": "Directive sur les émissions industrielles"
    },
    
    # === Économie circulaire & Déchets ===
    "PACKAGING": {
        "name": "Packaging and Packaging Waste Regulation",
        "search_keywords": ["packaging waste"],
        "description": "Emballages et déchets d'emballages"
    },
    "BATTERY": {
        "name": "EU Battery Regulation",
        "search_keywords": ["batteries and waste batteries"],
        "description": "Batteries et déchets de batteries"
    },
    "WEEE": {
        "name": "Waste Electrical and Electronic Equipment",
        "search_keywords": ["waste electrical electronic equipment", "WEEE"],
        "description": "Déchets d'équipements électriques et électroniques"
    },
    "ELV": {
        "name": "End-of-Life Vehicles",
        "search_keywords": ["end-of-life vehicles"],
        "description": "Véhicules hors d'usage"
    },
    "ECODESIGN": {
        "name": "Ecodesign for Sustainable Products",
        "search_keywords": ["ecodesign sustainable products", "ecodesign requirements"],
        "description": "Écoconception des produits durables"
    },
    "WASTE_FRAMEWORK": {
        "name": "Waste Framework Directive",
        "search_keywords": ["waste framework directive"],
        "description": "Directive cadre sur les déchets"
    },
    
    # === Substances chimiques ===
    "REACH": {
        "name": "Registration, Evaluation, Authorisation of Chemicals",
        "search_keywords": ["REACH", "registration evaluation authorisation chemicals"],
        "description": "Enregistrement et autorisation des substances chimiques"
    },
    "CLP": {
        "name": "Classification, Labelling and Packaging",
        "search_keywords": ["classification labelling packaging substances"],
        "description": "Classification et étiquetage des substances dangereuses"
    },
    "ROHS": {
        "name": "Restriction of Hazardous Substances",
        "search_keywords": ["restriction hazardous substances electrical", "RoHS"],
        "description": "Restriction des substances dangereuses dans équipements électroniques"
    },
    "POP": {
        "name": "Persistent Organic Pollutants",
        "search_keywords": ["persistent organic pollutants"],
        "description": "Polluants organiques persistants"
    },
    "SEVESO": {
        "name": "Seveso III Directive",
        "search_keywords": ["major-accident hazards", "Seveso"],
        "description": "Prévention des accidents majeurs"
    },
    
    # === Reporting & Finance durable ===
    "CSRD": {
        "name": "Corporate Sustainability Reporting Directive",
        "search_keywords": ["corporate sustainability reporting"],
        "description": "Reporting extra-financier des entreprises"
    },
    "SFDR": {
        "name": "Sustainable Finance Disclosure Regulation",
        "search_keywords": ["sustainability-related disclosures financial"],
        "description": "Transparence des produits financiers durables"
    },
    "TAXONOMY": {
        "name": "EU Taxonomy Regulation",
        "search_keywords": ["taxonomy sustainable investment", "environmentally sustainable economic"],
        "description": "Classification des activités économiques durables"
    },
    "CSDDD": {
        "name": "Corporate Sustainability Due Diligence Directive",
        "search_keywords": ["corporate sustainability due diligence"],
        "description": "Devoir de vigilance des entreprises"
    },
    
    # === Biodiversité & Ressources naturelles ===
    "EUDR": {
        "name": "EU Deforestation Regulation",
        "search_keywords": ["deforestation-free", "deforestation regulation"],
        "description": "Lutte contre la déforestation importée"
    },
    "WATER_FRAMEWORK": {
        "name": "Water Framework Directive",
        "search_keywords": ["water policy framework"],
        "description": "Protection des eaux"
    },
    "NATURE_RESTORATION": {
        "name": "Nature Restoration Law",
        "search_keywords": ["nature restoration"],
        "description": "Restauration de la nature"
    },
    
    # === Transport & Mobilité ===
    "CO2_VEHICLES": {
        "name": "CO2 Emission Standards for Vehicles",
        "search_keywords": ["CO2 emission standards passenger cars", "CO2 emission performance"],
        "description": "Normes d'émissions CO2 véhicules"
    },
    "EURO_EMISSIONS": {
        "name": "Euro Emission Standards",
        "search_keywords": ["Euro 6", "Euro 7", "type-approval motor vehicles emissions"],
        "description": "Normes Euro polluants véhicules"
    },
    "AFIR": {
        "name": "Alternative Fuels Infrastructure Regulation",
        "search_keywords": ["alternative fuels infrastructure"],
        "description": "Infrastructure de recharge/ravitaillement"
    },
}

# Liste des codes de réglementation (pour compatibilité)
KNOWN_REGULATIONS = list(REGULATIONS_CONFIG.keys()) + ["OTHER"]


def get_all_regulations() -> List[str]:
    """Retourne la liste de toutes les réglementations disponibles."""
    return list(REGULATIONS_CONFIG.keys())


def get_regulation_info(regulation_code: str) -> Optional[Dict]:
    """Retourne les informations d'une réglementation."""
    return REGULATIONS_CONFIG.get(regulation_code)


def get_search_keywords_for_regulation(regulation_code: str) -> List[str]:
    """Retourne les mots-clés de recherche pour une réglementation."""
    config = REGULATIONS_CONFIG.get(regulation_code)
    if config:
        return config["search_keywords"]
    return []


# ========================================
# MODÈLES PYDANTIC
# ========================================

class EurlexDocument(BaseModel):
    """Modèle pour un document EUR-Lex"""
    celex_number: Optional[str]
    title: str
    url: str
    pdf_url: Optional[str]
    document_type: str
    source: str = "eurlex"
    keyword: str
    publication_date: Optional[datetime] = None
    status: str = "ACTIVE_LAW"
    metadata: Dict = {}

class SearchResult(BaseModel):
    """Modèle pour le résultat de recherche"""
    status: str
    total_found: int  # Nombre de documents retournés
    total_available: int = 0  # Nombre total de documents disponibles sur EUR-Lex
    documents: List[EurlexDocument]
    error: Optional[str] = None

# ========================================
# CLIENT API EUR-LEX
# ========================================

def _build_soap_request(expert_query: str, page: int = 1, page_size: int = 10) -> str:
    """
    Construit une requête SOAP pour l'API EUR-Lex
    
    Args:
        expert_query: Requête en syntaxe expert (ex: "TI~CBAM", "DN=32023R0956")
        page: Numéro de page (commence à 1)
        page_size: Nombre de résultats par page
        
    Returns:
        str: Requête SOAP au format XML
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:sear="http://eur-lex.europa.eu/search">
   <soap:Header>
      <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
         <wsse:UsernameToken>
            <wsse:Username>{EURLEX_API_USERNAME}</wsse:Username>
            <wsse:Password>{EURLEX_API_PASSWORD}</wsse:Password>
         </wsse:UsernameToken>
      </wsse:Security>
   </soap:Header>
   <soap:Body>
      <sear:searchRequest>
         <sear:expertQuery>{expert_query}</sear:expertQuery>
         <sear:page>{page}</sear:page>
         <sear:pageSize>{page_size}</sear:pageSize>
         <sear:searchLanguage>en</sear:searchLanguage>
      </sear:searchRequest>
   </soap:Body>
</soap:Envelope>"""


def _extract_celex_from_reference(reference: str) -> Optional[str]:
    """
    Extrait le numéro CELEX depuis une référence EUR-Lex.
    
    Les références peuvent être sous forme:
    - eng_cellar:xxx -> pas de CELEX direct
    - CELEX:32023R0956 -> CELEX = 32023R0956
    - cellar:xxx -> pas de CELEX direct
    
    Args:
        reference: Référence du document
        
    Returns:
        str ou None: Numéro CELEX si trouvé
    """
    import re
    
    if not reference:
        return None
    
    # Chercher un pattern CELEX dans la référence
    # Format: année (4 chiffres) + lettre type + numéro
    celex_pattern = r'(3\d{4}[RLDEACB]\d{4})'
    match = re.search(celex_pattern, reference)
    if match:
        return match.group(1)
    
    return None


def _extract_date_from_celex(celex: str) -> Optional[datetime]:
    """
    Extrait une date approximative depuis le numéro CELEX.
    
    Le CELEX contient l'année : 32023R0956 -> année 2023
    
    Args:
        celex: Numéro CELEX (ex: 32023R0956)
        
    Returns:
        datetime ou None: Date approximative (1er janvier de l'année)
    """
    if not celex or len(celex) < 5:
        return None
    
    try:
        # Le format CELEX est: 3YYYYTNNNN où YYYY est l'année
        year_str = celex[1:5]  # Extraire les 4 chiffres après le "3"
        year = int(year_str)
        
        if 1950 <= year <= 2100:  # Validation de l'année
            return datetime(year, 1, 1)
    except (ValueError, IndexError):
        pass
    
    return None


def _extract_date_from_content(content: str) -> Optional[datetime]:
    """
    Tente d'extraire une date depuis le contenu/titre du document.
    
    Cherche des patterns comme:
    - "of 10 May 2023"
    - "2023/956"
    - "(EU) 2023/956"
    
    Args:
        content: Contenu ou titre du document
        
    Returns:
        datetime ou None
    """
    import re
    
    if not content:
        return None
    
    # Pattern 1: "of DD Month YYYY" ou "DD Month YYYY"
    months = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    
    pattern1 = r'(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})'
    match = re.search(pattern1, content.lower())
    if match:
        try:
            day = int(match.group(1))
            month = months[match.group(2)]
            year = int(match.group(3))
            return datetime(year, month, day)
        except (ValueError, KeyError):
            pass
    
    # Pattern 2: Numéro de règlement "YYYY/NNNN" -> extraire l'année
    pattern2 = r'\b(20\d{2})/\d+'
    match = re.search(pattern2, content)
    if match:
        try:
            year = int(match.group(1))
            return datetime(year, 1, 1)
        except ValueError:
            pass
    
    return None


def _build_pdf_url_from_cellar(cellar_id: str) -> str:
    """
    Construit l'URL PDF à partir d'un identifiant cellar.
    
    Args:
        cellar_id: Identifiant cellar (ex: 062f76c4-5e06-11ea-b735-01aa75ed71a1)
        
    Returns:
        str: URL PDF valide
    """
    # Nettoyer l'ID cellar
    clean_id = cellar_id.replace('eng_cellar:', '').replace('_en', '').replace('cellar:', '')
    
    # L'URL correcte utilise juste l'UUID sans préfixe
    return f"https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELLAR:{clean_id}"


def _parse_soap_response(response_xml: str, keyword: str) -> tuple[List[Dict], int]:
    """
    Parse la réponse SOAP et extrait les documents
    
    Args:
        response_xml: Réponse XML de l'API
        keyword: Mot-clé de recherche (pour les métadonnées)
        
    Returns:
        tuple: (Liste des documents extraits, Nombre total disponible sur EUR-Lex)
    """
    try:
        # Parser le XML
        root = etree.fromstring(response_xml.encode('utf-8'))
        
        # Namespaces - le contenu est dans le namespace par défaut de EUR-Lex
        namespaces = {
            'soap': 'http://www.w3.org/2003/05/soap-envelope',
            'sear': 'http://eur-lex.europa.eu/search'
        }
        
        # Extraire le nombre total de résultats disponibles
        total_available = 0
        for field_name in ['numHits', 'totalHits', 'totalhits', 'total', 'count']:
            elem = root.find(f'.//sear:{field_name}', namespaces)
            if elem is not None and elem.text:
                total_available = int(elem.text)
                logger.info("total_hits_found", field=field_name, value=total_available)
                break
        
        # Si toujours 0, essayer de chercher sans namespace
        if total_available == 0:
            match = re.search(r'<[^>]*(?:numHits|totalhits)[^>]*>(\d+)<', response_xml, re.IGNORECASE)
            if match:
                total_available = int(match.group(1))
                logger.info("total_hits_found_regex", value=total_available)
        
        # Extraire les documents
        documents = []
        result_elements = root.findall('.//sear:result', namespaces)
        
        for result in result_elements:
            # Convertir l'élément result en string pour le parsing regex
            result_xml = etree.tostring(result, encoding='unicode')
            
            # Extraire les champs de base
            reference = result.findtext('sear:reference', default='', namespaces=namespaces)
            rank = result.findtext('sear:rank', default='0', namespaces=namespaces)
            
            # Extraire le titre depuis EXPRESSION_TITLE/VALUE dans ce résultat spécifique
            title = None
            title_match = re.search(r'<EXPRESSION_TITLE>\s*<LANG>en</LANG>\s*<VALUE>([^<]+)</VALUE>', result_xml)
            if title_match:
                title = title_match.group(1).strip()
            
            # Si pas trouvé avec LANG=en, chercher n'importe quel VALUE
            if not title:
                title_match = re.search(r'<EXPRESSION_TITLE>.*?<VALUE>([^<]+)</VALUE>', result_xml, re.DOTALL)
                if title_match:
                    title = title_match.group(1).strip()
            
            if not title:
                title = f"Document {reference}"
            
            # Extraire le CELEX depuis ID_CELEX/VALUE dans ce résultat
            celex = None
            celex_match = re.search(r'<ID_CELEX>\s*<VALUE>([^<]+)</VALUE>', result_xml)
            if celex_match:
                celex = celex_match.group(1).strip()
                # Nettoyer le CELEX (enlever la date de consolidation si présente)
                if '-' in celex:
                    celex = celex.split('-')[0]
            
            # Extraire la date depuis le titre (ex: "of 10 May 2023")
            publication_date = None
            if title:
                publication_date = _extract_date_from_content(title)
            
            # Si pas trouvé, extraire depuis WORK_DATE_DOCUMENT
            if not publication_date:
                date_match = re.search(r'<WORK_DATE_DOCUMENT>.*?<VALUE>([^<]+)</VALUE>', result_xml, re.DOTALL)
                if date_match:
                    try:
                        publication_date = datetime.strptime(date_match.group(1).strip(), '%Y-%m-%d')
                    except ValueError:
                        pass
            
            # Si toujours pas de date, extraire depuis le CELEX
            if not publication_date and celex:
                publication_date = _extract_date_from_celex(celex)
            
            # Extraire les liens PDF et HTML
            html_url = None
            pdf_url = None
            
            # Chercher les liens avec regex dans ce résultat
            pdf_match = re.search(r'<document_link[^>]*type="pdf"[^>]*>([^<]+)</document_link>', result_xml)
            if pdf_match:
                pdf_url = pdf_match.group(1)
            
            html_match = re.search(r'<document_link[^>]*type="html"[^>]*>([^<]+)</document_link>', result_xml)
            if html_match:
                html_url = html_match.group(1)
            
            # Si pas de PDF trouvé, construire l'URL depuis cellar
            if not pdf_url and 'cellar' in reference.lower():
                pdf_url = _build_pdf_url_from_cellar(reference)
            
            if not html_url:
                if celex:
                    html_url = f"https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{celex}"
                else:
                    html_url = f"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=cellar:{reference}"
            
            # Skip les documents sans PDF
            if not pdf_url:
                logger.warning("document_without_pdf", reference=reference)
                continue
            
            # Déterminer le type de document
            document_type = _extract_type_from_celex(celex) if celex else 'OTHER'
            
            # Construire le document
            doc = {
                'celex_number': celex,
                'title': title,
                'url': html_url,
                'pdf_url': pdf_url,
                'document_type': document_type,
                'source': 'eurlex',
                'keyword': keyword,
                'publication_date': publication_date,
                'status': 'ACTIVE_LAW',
                'metadata': {
                    'reference': reference,
                    'rank': int(rank),
                    'scraped_at': datetime.now().isoformat(),
                    'api_version': 'soap_v2'
                }
            }
            
            documents.append(doc)
        
        return documents, total_available
        
    except Exception as e:
        logger.error("soap_parsing_failed", error=str(e))
        return [], 0


def _extract_celex_from_link(link: str) -> Optional[str]:
    """Extrait le numéro CELEX depuis un lien EUR-Lex"""
    if not link:
        return None
    
    if 'CELEX:' in link:
        import re
        match = re.search(r'CELEX:([A-Z0-9]+)', link)
        if match:
            return match.group(1)
    
    return None


def _extract_type_from_celex(celex: Optional[str]) -> str:
    """Extrait le type de document depuis le numéro CELEX"""
    if not celex or len(celex) < 6:
        return 'OTHER'
    
    type_char = celex[5] if len(celex) > 5 else ''
    
    type_mapping = {
        'R': 'REGULATION',
        'L': 'DIRECTIVE',
        'D': 'DECISION',
        'E': 'DECISION',
        'A': 'AGREEMENT',
        'B': 'BUDGET',
        'C': 'CONSOLIDATED',
    }
    
    return type_mapping.get(type_char, 'OTHER')


# ========================================
# FONCTION PRINCIPALE (API publique)
# ========================================

# Documents CBAM connus avec leur numéro CELEX (fallback si recherche dynamique échoue)
CBAM_KNOWN_DOCUMENTS = {
    "CBAM": [
        "32023R0956",   # Règlement CBAM principal
        "32023R1773",   # Règlement d'implémentation CBAM
        "32023R2318",   # Règlement délégué CBAM
    ],
    "EUDR": [
        "32023R1115",   # Règlement déforestation
    ],
    "CSRD": [
        "32022L2464",   # Directive CSRD
    ]
}

# Sous-domaines EUR-Lex par défaut pour la recherche
DEFAULT_SUBDOMAINS = ["LEGISLATION", "CONSLEG", "PREP_ACT"]

async def search_eurlex(
    keyword: str, 
    max_results: int = 10, 
    subdomains: list = None,
    use_known_celex: bool = False,
    consolidated_only: bool = False
) -> SearchResult:
    """
    Rechercher des documents EUR-Lex via l'API officielle
    
    Args:
        keyword: Mot-clé de recherche (ex: "CBAM", "EUDR", "CSRD")
        max_results: Nombre maximum de résultats à retourner
        subdomains: Liste des sous-domaines à rechercher (LEGISLATION, CONSLEG, PREP_ACT, etc.)
                   Par défaut: ["LEGISLATION", "CONSLEG", "PREP_ACT"]
        use_known_celex: Si True, utilise les CELEX connus au lieu de la recherche dynamique
        consolidated_only: Si True, récupère uniquement les textes consolidés (Collection = CONSLEG)
                          Les textes consolidés regroupent le texte original + toutes ses modifications
        
    Returns:
        SearchResult: Objet contenant le statut et la liste des documents
    """
    # Utiliser les sous-domaines par défaut si non spécifiés
    if subdomains is None:
        subdomains = DEFAULT_SUBDOMAINS
    
    logger.info("eurlex_api_search_started", keyword=keyword, max_results=max_results, subdomains=subdomains, consolidated_only=consolidated_only)
    
    # Vérifier les credentials
    if not EURLEX_API_USERNAME or not EURLEX_API_PASSWORD:
        error_msg = "EUR-Lex API credentials not found. Please set EURLEX_API_USERNAME and EURLEX_API_PASSWORD in .env"
        logger.error("credentials_missing")
        return SearchResult(
            status="error",
            total_found=0,
            documents=[],
            error=error_msg
        )
    
    try:
        # Construire la requête expert
        if use_known_celex:
            # Utiliser les documents CELEX connus (fallback)
            known_celex = CBAM_KNOWN_DOCUMENTS.get(keyword.upper(), [])
            if known_celex:
                celex_queries = " OR ".join([f"DN={celex}" for celex in known_celex[:max_results]])
                expert_query = celex_queries
            else:
                # Construire le filtre de sous-domaines
                subdom_filter = " OR ".join([f"DTS_SUBDOM={s}" for s in subdomains])
                # Recherche plein texte (selon doc EUR-Lex: Text~keyword)
                # Fallback sur TI~ si Text~ ne fonctionne pas
                expert_query = f"Text~{keyword} AND ({subdom_filter})"
        elif consolidated_only:
            # Recherche uniquement les textes consolidés (Collection = CONSLEG)
            # Les textes consolidés regroupent le texte original + toutes ses modifications
            expert_query = f"Text~{keyword} AND Collection = CONSLEG"
            logger.info("consolidated_search", query=expert_query)
        else:
            # Recherche dynamique : texte complet + filtre sous-domaines
            subdom_filter = " OR ".join([f"DTS_SUBDOM={s}" for s in subdomains])
            expert_query = f"Text~{keyword} AND ({subdom_filter})"
        
        logger.info("building_soap_request", expert_query=expert_query)
        
        # Construire la requête SOAP
        soap_request = _build_soap_request(expert_query, page=1, page_size=max_results)
        
        # Envoyer la requête
        logger.info("sending_soap_request", url=EURLEX_SOAP_URL)
        
        response = requests.post(
            EURLEX_SOAP_URL,
            data=soap_request,
            headers={
                'Content-Type': 'application/soap+xml; charset=utf-8',
                'User-Agent': 'DataNova-Agent1A/1.0'
            },
            timeout=30
        )
        
        response.raise_for_status()
        
        logger.info("soap_response_received", status_code=response.status_code)
        
        # Parser la réponse (retourne documents + nombre total disponible)
        documents_data, total_available = _parse_soap_response(response.text, keyword)
        
        # Convertir en objets Pydantic
        documents = [EurlexDocument(**doc) for doc in documents_data]
        
        logger.info(
            "eurlex_api_search_completed", 
            count=len(documents),
            total_available=total_available
        )
        
        return SearchResult(
            status="success",
            total_found=len(documents),
            total_available=total_available,
            documents=documents
        )
        
    except requests.exceptions.Timeout:
        error_msg = f"EUR-Lex API timeout after 30 seconds"
        logger.error("api_timeout", error=error_msg)
        return SearchResult(
            status="error",
            total_found=0,
            total_available=0,
            documents=[],
            error=error_msg
        )
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"EUR-Lex API HTTP error: {e.response.status_code}"
        logger.error("api_http_error", status_code=e.response.status_code, error=str(e))
        return SearchResult(
            status="error",
            total_found=0,
            total_available=0,
            documents=[],
            error=error_msg
        )
        
    except Exception as e:
        error_msg = f"EUR-Lex API error: {str(e)}"
        logger.error("eurlex_api_search_failed", error=str(e))
        return SearchResult(
            status="error",
            total_found=0,
            total_available=0,
            documents=[],
            error=error_msg
        )


# ========================================
# NOUVELLE API : COLLECTE PAR DOMAINES (Option 3)
# ========================================

def load_eurlex_domains_config() -> Dict:
    """
    Charge la configuration des domaines EUR-Lex depuis le fichier JSON.
    
    Returns:
        Dict: Configuration des domaines
    """
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "eurlex_domains.json"
    
    try:
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("eurlex_domains_config_not_found", path=str(config_path))
        return {}
    except json.JSONDecodeError as e:
        logger.error("eurlex_domains_config_invalid", error=str(e))
        return {}


def get_enabled_domains() -> List[str]:
    """
    Retourne la liste des codes de domaines activés.
    
    Returns:
        List[str]: Liste des codes de domaines (ex: ["15", "13", "11"])
    """
    config = load_eurlex_domains_config()
    domains = config.get("domains", {})
    
    enabled = []
    for domain_key, domain_info in domains.items():
        if domain_info.get("enabled", False):
            enabled.append(domain_info.get("code"))
    
    return enabled


def get_enabled_document_types() -> List[str]:
    """
    Retourne la liste des types de documents activés.
    
    Returns:
        List[str]: Liste des codes de types (ex: ["R", "L", "D"])
    """
    config = load_eurlex_domains_config()
    doc_types = config.get("document_types", {})
    
    enabled = set()
    for type_key, type_info in doc_types.items():
        if type_info.get("enabled", False):
            enabled.add(type_info.get("code"))
    
    return list(enabled)


def _build_domain_query(
    domains: List[str] = None,
    document_types: List[str] = None,
    max_age_days: int = None,
    collections: List[str] = None
) -> str:
    """
    Construit une requête expert EUR-Lex basée sur les domaines.
    
    IMPORTANT: L'API SOAP EUR-Lex a des limitations sur les champs utilisables.
    Les champs qui fonctionnent: Text~, DTS_SUBDOM, DN (CELEX)
    
    Stratégie: On utilise une recherche par collection (LEGISLATION/CONSLEG)
    et on filtre côté application par date et type si nécessaire.
    
    Args:
        domains: Liste des codes de domaines (non utilisé - filtrage côté app)
        document_types: Liste des types de documents (non utilisé - filtrage côté app)
        max_age_days: Âge maximum des documents en jours (non utilisé - filtrage côté app)
        collections: Collections EUR-Lex (LEGISLATION, CONSLEG)
        
    Returns:
        str: Requête expert EUR-Lex
    """
    # L'API EUR-Lex SOAP est limitée dans ses capacités de filtrage
    # On utilise uniquement les filtres qui fonctionnent de manière fiable
    
    # Filtre par collection (seul filtre fiable sans mot-clé)
    if collections:
        coll_filter = " OR ".join([f"DTS_SUBDOM={c}" for c in collections])
        return f"({coll_filter})"
    else:
        return "DTS_SUBDOM=LEGISLATION"


async def search_eurlex_by_domain(
    domains: List[str] = None,
    document_types: List[str] = None,
    max_age_days: int = 365,
    max_results: int = 50,
    collections: List[str] = None
) -> SearchResult:
    """
    Recherche des documents EUR-Lex par domaines (sans filtre par mot-clé réglementation).
    
    Cette fonction implémente l'Option 3 du CDC :
    - Filtrage par domaines pertinents pour l'industrie
    - Filtrage par type de document (Règlements, Directives)
    - Filtrage par date (documents récents)
    
    L'Agent 1A collecte TOUT ce qui correspond aux critères.
    L'Agent 1B filtrera ensuite ce qui est pertinent pour Hutchinson.
    
    Args:
        domains: Liste des codes de domaines EUR-Lex (ex: ["15", "13", "11"])
                 Si None, utilise les domaines activés dans la config
        document_types: Types de documents (ex: ["R", "L", "D"])
                       Si None, utilise les types activés dans la config
        max_age_days: Âge maximum des documents en jours (défaut: 365)
        max_results: Nombre maximum de résultats (défaut: 50)
        collections: Collections EUR-Lex (défaut: ["LEGISLATION", "CONSLEG"])
        
    Returns:
        SearchResult: Résultats de la recherche
    """
    # Charger la config si paramètres non fournis
    config = load_eurlex_domains_config()
    
    if domains is None:
        domains = get_enabled_domains()
    
    if document_types is None:
        document_types = get_enabled_document_types()
    
    if collections is None:
        collections = config.get("collection_settings", {}).get("collections", ["LEGISLATION", "CONSLEG"])
    
    logger.info(
        "eurlex_domain_search_started",
        domains=domains,
        document_types=document_types,
        max_age_days=max_age_days,
        max_results=max_results,
        collections=collections
    )
    
    # Vérifier les credentials
    if not EURLEX_API_USERNAME or not EURLEX_API_PASSWORD:
        error_msg = "EUR-Lex API credentials not found"
        logger.error("credentials_missing")
        return SearchResult(
            status="error",
            total_found=0,
            documents=[],
            error=error_msg
        )
    
    try:
        # Construire la requête par domaines
        expert_query = _build_domain_query(
            domains=domains,
            document_types=document_types,
            max_age_days=max_age_days,
            collections=collections
        )
        
        logger.info("domain_query_built", expert_query=expert_query)
        
        # Construire et envoyer la requête SOAP
        soap_request = _build_soap_request(expert_query, page=1, page_size=max_results)
        
        response = requests.post(
            EURLEX_SOAP_URL,
            data=soap_request,
            headers={
                'Content-Type': 'application/soap+xml; charset=utf-8',
                'User-Agent': 'DataNova-Agent1A/2.0'
            },
            timeout=60  # Timeout plus long pour les grandes recherches
        )
        
        response.raise_for_status()
        
        # Parser la réponse (keyword="DOMAIN_SEARCH" pour identifier la source)
        documents_data, total_available = _parse_soap_response(response.text, "DOMAIN_SEARCH")
        
        # Convertir en objets Pydantic
        documents = [EurlexDocument(**doc) for doc in documents_data]
        
        logger.info(
            "eurlex_domain_search_completed",
            count=len(documents),
            total_available=total_available
        )
        
        return SearchResult(
            status="success",
            total_found=len(documents),
            total_available=total_available,
            documents=documents
        )
        
    except requests.exceptions.Timeout:
        error_msg = "EUR-Lex API timeout"
        logger.error("api_timeout")
        return SearchResult(
            status="error",
            total_found=0,
            total_available=0,
            documents=[],
            error=error_msg
        )
        
    except Exception as e:
        error_msg = f"EUR-Lex API error: {str(e)}"
        logger.error("eurlex_domain_search_failed", error=str(e))
        return SearchResult(
            status="error",
            total_found=0,
            total_available=0,
            documents=[],
            error=error_msg
        )
