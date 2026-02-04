# src/agent_1a/tools/keyword_extractor.py
"""
Module d'extraction de mots-clés depuis le profil entreprise.

Ce module lit le profil JSON de l'entreprise et génère automatiquement
des mots-clés pertinents pour la recherche EUR-Lex, SANS utiliser
les noms de réglementations (CBAM, REACH, etc.).

L'objectif est que l'Agent 1A collecte des documents de manière "neutre",
et que l'Agent 1B détermine ensuite quelles réglementations s'appliquent.

Catégories de mots-clés extraits:
- Codes NC/HS (nomenclature douanière)
- Matières premières
- Secteurs d'activité (codes NACE)
- Pays fournisseurs
- Types de produits
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger()


@dataclass
class CompanyKeywords:
    """Structure contenant les mots-clés extraits du profil entreprise."""
    
    company_name: str
    company_id: str
    
    # Codes douaniers (très précis pour EUR-Lex)
    nc_codes: List[str] = field(default_factory=list)
    hs_codes: List[str] = field(default_factory=list)
    
    # Matières premières
    materials: List[str] = field(default_factory=list)
    
    # Secteurs d'activité
    sectors: List[str] = field(default_factory=list)
    nace_codes: List[str] = field(default_factory=list)
    
    # Pays (fournisseurs, sites de production)
    countries: List[str] = field(default_factory=list)
    
    # Produits fabriqués
    products: List[str] = field(default_factory=list)
    
    # Mots-clés commerciaux génériques
    trade_terms: List[str] = field(default_factory=list)
    
    def get_all_keywords(self) -> List[str]:
        """Retourne tous les mots-clés uniques."""
        all_kw = set()
        all_kw.update(self.nc_codes)
        all_kw.update(self.hs_codes)
        all_kw.update(self.materials)
        all_kw.update(self.sectors)
        all_kw.update(self.countries)
        all_kw.update(self.products)
        all_kw.update(self.trade_terms)
        return list(all_kw)
    
    def get_prioritized_keywords(self) -> List[tuple]:
        """
        Retourne les mots-clés avec leur priorité.
        Priorité 1 = plus précis (codes NC), Priorité 3 = plus général.
        
        Returns:
            Liste de tuples (keyword, priority, category)
        """
        keywords = []
        
        # Priorité 1: Codes NC/HS (très précis, ~200-600 docs chacun)
        for code in self.nc_codes:
            keywords.append((code, 1, 'nc_code'))
        for code in self.hs_codes:
            keywords.append((code, 1, 'hs_code'))
        
        # Priorité 2: Matières spécifiques et produits
        for mat in self.materials:
            keywords.append((mat, 2, 'material'))
        for prod in self.products:
            keywords.append((prod, 2, 'product'))
        
        # Priorité 3: Secteurs et pays
        for sector in self.sectors:
            keywords.append((sector, 3, 'sector'))
        for country in self.countries:
            keywords.append((country, 3, 'country'))
        
        # Priorité 4: Termes commerciaux (très génériques)
        for term in self.trade_terms:
            keywords.append((term, 4, 'trade'))
        
        return keywords
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire."""
        return {
            'company_name': self.company_name,
            'company_id': self.company_id,
            'nc_codes': self.nc_codes,
            'hs_codes': self.hs_codes,
            'materials': self.materials,
            'sectors': self.sectors,
            'nace_codes': self.nace_codes,
            'countries': self.countries,
            'products': self.products,
            'trade_terms': self.trade_terms,
            'total_keywords': len(self.get_all_keywords())
        }


# Mapping des codes pays ISO vers noms anglais (pour EUR-Lex)
COUNTRY_CODE_TO_NAME = {
    'FR': 'France',
    'DE': 'Germany',
    'ES': 'Spain',
    'IT': 'Italy',
    'PL': 'Poland',
    'US': 'United States',
    'CN': 'China',
    'TH': 'Thailand',
    'MY': 'Malaysia',
    'ID': 'Indonesia',
    'IN': 'India',
    'TR': 'Turkey',
    'MX': 'Mexico',
    'AE': 'United Arab Emirates',
    'CI': "Ivory Coast",
    'BY': 'Belarus',
    'RU': 'Russia',
    'KR': 'Korea',
    'JP': 'Japan',
    'BR': 'Brazil',
    'VN': 'Vietnam',
}

# Mapping des noms de pays français vers anglais
COUNTRY_FR_TO_EN = {
    'France': 'France',
    'Allemagne': 'Germany',
    'Espagne': 'Spain',
    'Italie': 'Italy',
    'Pologne': 'Poland',
    'États-Unis': 'United States',
    'Chine': 'China',
    'Thaïlande': 'Thailand',
    'Malaisie': 'Malaysia',
    'Indonésie': 'Indonesia',
    'Inde': 'India',
    'Turquie': 'Turkey',
    'Mexique': 'Mexico',
    'Émirats arabes unis': 'United Arab Emirates',
    "Côte d'Ivoire": "Ivory Coast",
    'Biélorussie': 'Belarus',
    'Russie': 'Russia',
    'Corée': 'Korea',
    'Japon': 'Japan',
    'Brésil': 'Brazil',
    'Vietnam': 'Vietnam',
}

# Mots-clés de matières premières standards (anglais pour EUR-Lex)
MATERIAL_KEYWORDS = {
    # Caoutchouc
    'caoutchouc': ['rubber', 'natural rubber'],
    'caoutchouc naturel': ['natural rubber'],
    'caoutchouc synthétique': ['synthetic rubber'],
    'latex': ['latex', 'natural rubber'],
    'epdm': ['EPDM', 'synthetic rubber'],
    'sbr': ['SBR', 'synthetic rubber'],
    'hnbr': ['HNBR', 'synthetic rubber'],
    'elastomer': ['elastomer'],
    'élastomère': ['elastomer'],
    
    # Métaux
    'acier': ['steel'],
    'aluminium': ['aluminium', 'aluminum'],
    'fer': ['iron'],
    'cuivre': ['copper'],
    'zinc': ['zinc'],
    
    # Autres
    'plastique': ['plastic', 'plastics'],
    'noir de carbone': ['carbon black'],
    'carbon black': ['carbon black'],
}

# Secteurs d'activité (NACE vers mots-clés anglais)
NACE_TO_KEYWORDS = {
    'C22': ['rubber', 'plastic', 'manufacturing'],
    'C22.1': ['rubber products', 'tyres'],
    'C22.19': ['rubber articles', 'rubber products'],
    'C22.2': ['plastic products'],
    'C22.29': ['plastic articles'],
    'C25': ['metal products', 'fabricated metal'],
    'C25.6': ['machining', 'metal treatment'],
    'C29': ['motor vehicles', 'automotive'],
    'C30': ['transport equipment'],
    'C30.3': ['aerospace', 'aircraft'],
}

# Segments de marché vers mots-clés
SEGMENT_KEYWORDS = {
    'automotive': ['automotive', 'motor vehicle', 'car', 'vehicle'],
    'aerospace': ['aerospace', 'aircraft', 'aviation'],
    'aeronautics': ['aerospace', 'aircraft', 'aviation'],
    'defence': ['defence', 'defense', 'military'],
    'rail': ['railway', 'rail', 'train'],
    'railway': ['railway', 'rail'],
    'industrial': ['industrial', 'industry'],
    'energy': ['energy', 'power'],
    'sealing': ['sealing', 'seal', 'gasket'],
    'nvh': ['vibration', 'noise'],
    'fluid': ['fluid', 'hose', 'pipe'],
    'hydrogen': ['hydrogen'],
}


def load_company_profile(profile_path: str) -> Optional[Dict]:
    """
    Charge le profil JSON de l'entreprise.
    
    Args:
        profile_path: Chemin vers le fichier JSON du profil
        
    Returns:
        Dict contenant le profil ou None si erreur
    """
    try:
        path = Path(profile_path)
        if not path.exists():
            logger.error(f"Profile file not found: {profile_path}")
            return None
            
        with open(path, 'r', encoding='utf-8') as f:
            profile = json.load(f)
            
        logger.info(f"Loaded company profile from {profile_path}")
        return profile
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in profile: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading profile: {e}")
        return None


def extract_nc_codes(profile: Dict) -> List[str]:
    """
    Extrait les codes NC/CN du profil entreprise.
    
    Cherche dans:
    - nc_codes.imports[].code
    - nc_codes.exports[].code
    - supply_chain.*.suppliers[].nc_code
    - customs_and_trade_compliance.master_data.hs_items[].hs_code
    """
    codes = set()
    
    # Section nc_codes
    if 'nc_codes' in profile:
        nc_section = profile['nc_codes']
        
        # Imports
        for item in nc_section.get('imports', []):
            code = item.get('code', '')
            if code:
                # Extraire le code principal (ex: "4001.21" -> "4001")
                base_code = code.split('.')[0]
                codes.add(base_code)
                codes.add(code.replace('.', ''))  # Version sans point
        
        # Exports
        for item in nc_section.get('exports', []):
            code = item.get('code', '')
            if code:
                base_code = code.split('.')[0]
                codes.add(base_code)
    
    # Supply chain suppliers
    if 'supply_chain' in profile:
        for category, data in profile['supply_chain'].items():
            if isinstance(data, dict) and 'suppliers' in data:
                for supplier in data['suppliers']:
                    nc_code = supplier.get('nc_code', '')
                    if nc_code:
                        base_code = nc_code.split('.')[0]
                        codes.add(base_code)
    
    # Customs HS items
    if 'customs_and_trade_compliance' in profile:
        customs = profile['customs_and_trade_compliance']
        if 'master_data' in customs and 'hs_items' in customs['master_data']:
            for item in customs['master_data']['hs_items']:
                hs_code = item.get('hs_code', '')
                if hs_code:
                    base_code = hs_code.split('.')[0]
                    codes.add(base_code)
    
    return list(codes)


def extract_materials(profile: Dict) -> List[str]:
    """
    Extrait les matières premières du profil et les traduit en anglais.
    
    Cherche dans:
    - supply_chain.*.suppliers[].product
    - supply_chain.critical_materials[]
    """
    materials = set()
    
    if 'supply_chain' in profile:
        sc = profile['supply_chain']
        
        # Natural rubber suppliers
        if 'natural_rubber' in sc:
            materials.add('natural rubber')
            materials.add('rubber')
            
        # Synthetic rubber
        if 'synthetic_rubber' in sc:
            materials.add('synthetic rubber')
            materials.add('rubber')
            for supplier in sc['synthetic_rubber'].get('suppliers', []):
                product = supplier.get('product', '').lower()
                if 'sbr' in product:
                    materials.add('SBR')
                if 'epdm' in product:
                    materials.add('EPDM')
                if 'hnbr' in product:
                    materials.add('HNBR')
        
        # Metals and additives
        if 'metals_and_additives' in sc:
            for mat in sc['metals_and_additives'].get('critical_materials', []):
                desc = mat.get('description', '').lower()
                if 'aluminium' in desc or 'aluminum' in desc:
                    materials.add('aluminium')
                if 'steel' in desc:
                    materials.add('steel')
                if 'carbon black' in desc:
                    materials.add('carbon black')
                if 'iron' in desc:
                    materials.add('iron')
    
    # Aussi chercher dans products
    if 'products' in profile:
        for product in profile['products']:
            product_lower = product.lower()
            if 'caoutchouc' in product_lower or 'rubber' in product_lower:
                materials.add('rubber')
            if 'élastomère' in product_lower or 'elastomer' in product_lower:
                materials.add('elastomer')
    
    return list(materials)


def extract_countries(profile: Dict) -> List[str]:
    """
    Extrait les pays fournisseurs et de production.
    
    Cherche dans:
    - supply_chain.*.suppliers[].country
    - locations.production_sites[].country
    """
    countries = set()
    
    def normalize_country(country: str) -> Optional[str]:
        """Convertit un code ou nom de pays en nom anglais."""
        if not country:
            return None
        # D'abord essayer le code ISO
        if country in COUNTRY_CODE_TO_NAME:
            return COUNTRY_CODE_TO_NAME[country]
        # Puis essayer le nom français
        if country in COUNTRY_FR_TO_EN:
            return COUNTRY_FR_TO_EN[country]
        # Si c'est déjà en anglais et > 2 chars
        if len(country) > 2:
            return country
        return None
    
    # Supplier countries
    if 'supply_chain' in profile:
        for category, data in profile['supply_chain'].items():
            if isinstance(data, dict) and 'suppliers' in data:
                for supplier in data['suppliers']:
                    country = supplier.get('country', '')
                    country_en = normalize_country(country)
                    if country_en:
                        countries.add(country_en)
    
    # Production sites (pays non-EU principalement)
    if 'locations' in profile:
        for site in profile['locations'].get('production_sites', []):
            country = site.get('country', '')
            if country and country not in ['FR', 'DE', 'ES', 'IT', 'PL']:  # Non-EU focus
                country_en = normalize_country(country)
                if country_en:
                    countries.add(country_en)
    
    return list(countries)


def extract_sectors(profile: Dict) -> List[str]:
    """
    Extrait les secteurs d'activité.
    
    Cherche dans:
    - company.industry.sector
    - company.industry.segments
    - company.markets
    - organization.business_units[].name
    """
    sectors = set()
    
    if 'company' in profile:
        company = profile['company']
        
        # Industry sector
        if 'industry' in company:
            industry = company['industry']
            
            # Primary NACE
            nace = industry.get('primary_nace_code', '')
            if nace:
                nace_prefix = nace.split('.')[0]
                for code, keywords in NACE_TO_KEYWORDS.items():
                    if nace.startswith(code):
                        sectors.update(keywords)
            
            # Segments
            for segment in industry.get('segments', []):
                segment_lower = segment.lower()
                for key, keywords in SEGMENT_KEYWORDS.items():
                    if key in segment_lower:
                        sectors.update(keywords)
        
        # Markets
        if 'markets' in company:
            for market_key in company['markets'].keys():
                market_lower = market_key.lower()
                for key, keywords in SEGMENT_KEYWORDS.items():
                    if key in market_lower:
                        sectors.update(keywords)
    
    # Business units
    if 'organization' in profile:
        for bu in profile['organization'].get('business_units', []):
            bu_name = bu.get('name', '').lower()
            for key, keywords in SEGMENT_KEYWORDS.items():
                if key in bu_name:
                    sectors.update(keywords)
    
    return list(sectors)


def extract_products(profile: Dict) -> List[str]:
    """
    Extrait les types de produits fabriqués.
    
    Cherche dans:
    - products[]
    - organization.business_units[].main_products[]
    """
    products = set()
    
    # Product keywords mapping (français -> anglais)
    product_mapping = {
        'joint': ['seal', 'gasket', 'sealing'],
        'étanchéité': ['sealing', 'seal'],
        'amortisseur': ['damper', 'vibration'],
        'anti-vibration': ['vibration', 'damping'],
        'flexible': ['hose', 'flexible'],
        'tuyau': ['hose', 'pipe', 'tube'],
        'flexibles': ['hose', 'pipe'],
    }
    
    # Main products list
    if 'products' in profile:
        for product in profile['products']:
            product_lower = product.lower()
            for fr_term, en_terms in product_mapping.items():
                if fr_term in product_lower:
                    products.update(en_terms)
    
    # Business unit products
    if 'organization' in profile:
        for bu in profile['organization'].get('business_units', []):
            for product in bu.get('main_products', []):
                product_lower = product.lower()
                # Direct English terms
                if 'seal' in product_lower:
                    products.add('seal')
                    products.add('sealing')
                if 'gasket' in product_lower:
                    products.add('gasket')
                if 'hose' in product_lower:
                    products.add('hose')
                if 'vibration' in product_lower:
                    products.add('vibration')
                if 'mount' in product_lower:
                    products.add('mount')
                if 'pipe' in product_lower:
                    products.add('pipe')
    
    return list(products)


def extract_keywords_from_profile(profile_path: str) -> Optional[CompanyKeywords]:
    """
    Fonction principale: extrait tous les mots-clés du profil entreprise.
    
    Args:
        profile_path: Chemin vers le fichier JSON du profil
        
    Returns:
        CompanyKeywords contenant tous les mots-clés extraits
    """
    profile = load_company_profile(profile_path)
    if not profile:
        return None
    
    # Extraire les infos de base
    company_name = profile.get('company', {}).get('company_name', 'Unknown')
    company_id = profile.get('company', {}).get('company_id', 'Unknown')
    
    # Extraire chaque catégorie de mots-clés
    keywords = CompanyKeywords(
        company_name=company_name,
        company_id=company_id,
        nc_codes=extract_nc_codes(profile),
        materials=extract_materials(profile),
        countries=extract_countries(profile),
        sectors=extract_sectors(profile),
        products=extract_products(profile),
        trade_terms=['import', 'customs', 'tariff'],  # Termes génériques utiles
    )
    
    logger.info(
        f"Extracted keywords from {company_name}",
        nc_codes=len(keywords.nc_codes),
        materials=len(keywords.materials),
        countries=len(keywords.countries),
        sectors=len(keywords.sectors),
        products=len(keywords.products),
        total=len(keywords.get_all_keywords())
    )
    
    return keywords


def get_eurlex_search_keywords(
    keywords: CompanyKeywords,
    max_keywords: int = 20,
    priority_threshold: int = 3
) -> List[str]:
    """
    Retourne une liste de mots-clés optimisée pour la recherche EUR-Lex.
    
    Args:
        keywords: CompanyKeywords extraits du profil
        max_keywords: Nombre maximum de mots-clés à retourner
        priority_threshold: Inclure seulement les priorités <= à cette valeur
        
    Returns:
        Liste de mots-clés triés par priorité
    """
    prioritized = keywords.get_prioritized_keywords()
    
    # Filtrer par priorité
    filtered = [(kw, p, c) for kw, p, c in prioritized if p <= priority_threshold]
    
    # Trier par priorité puis alphabétiquement
    filtered.sort(key=lambda x: (x[1], x[0]))
    
    # Prendre les N premiers
    result = [kw for kw, _, _ in filtered[:max_keywords]]
    
    return result


# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def get_default_profile_path() -> str:
    """Retourne le chemin par défaut du profil Hutchinson."""
    base_path = Path(__file__).parent.parent.parent.parent  # backend/
    return str(base_path / "data" / "company_profiles" / "Hutchinson_SA.json")


def print_keywords_summary(keywords: CompanyKeywords):
    """Affiche un résumé des mots-clés extraits."""
    print(f"\n{'='*60}")
    print(f"Mots-clés extraits pour: {keywords.company_name}")
    print(f"{'='*60}")
    
    print(f"\n📦 Codes NC ({len(keywords.nc_codes)}):")
    for code in keywords.nc_codes:
        print(f"   - {code}")
    
    print(f"\n🧪 Matières ({len(keywords.materials)}):")
    for mat in keywords.materials:
        print(f"   - {mat}")
    
    print(f"\n🏭 Secteurs ({len(keywords.sectors)}):")
    for sector in keywords.sectors:
        print(f"   - {sector}")
    
    print(f"\n🌍 Pays ({len(keywords.countries)}):")
    for country in keywords.countries:
        print(f"   - {country}")
    
    print(f"\n📦 Produits ({len(keywords.products)}):")
    for product in keywords.products:
        print(f"   - {product}")
    
    print(f"\n📊 Total mots-clés uniques: {len(keywords.get_all_keywords())}")


if __name__ == "__main__":
    # Test du module
    profile_path = get_default_profile_path()
    print(f"Loading profile: {profile_path}")
    
    keywords = extract_keywords_from_profile(profile_path)
    
    if keywords:
        print_keywords_summary(keywords)
        
        print(f"\n{'='*60}")
        print("Mots-clés prioritaires pour EUR-Lex:")
        print(f"{'='*60}")
        search_kw = get_eurlex_search_keywords(keywords, max_keywords=15)
        for i, kw in enumerate(search_kw, 1):
            print(f"  {i:2}. {kw}")
