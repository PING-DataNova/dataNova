"""
Moteurs de Projection Réglementaire et Géopolitique pour Agent 2

Ce module gère la projection des événements réglementaires et géopolitiques
sur les sites et fournisseurs en utilisant les critères de pays, régions et secteurs.
"""

from typing import List, Dict, Set, Optional
from dataclasses import dataclass


@dataclass
class RegulatoryImpact:
    """Résultat de l'analyse réglementaire pour une entité"""
    entity_id: str
    entity_name: str
    entity_type: str  # "site" ou "supplier"
    impact_level: str  # "critique", "fort", "moyen", "faible"
    matching_criteria: List[str]  # Critères de correspondance (pays, secteur, produit)
    compliance_required: bool


@dataclass
class GeopoliticalImpact:
    """Résultat de l'analyse géopolitique pour une entité"""
    entity_id: str
    entity_name: str
    entity_type: str  # "site" ou "supplier"
    impact_level: str  # "critique", "fort", "moyen", "faible"
    risk_factors: List[str]  # Facteurs de risque identifiés
    proximity_to_conflict: Optional[float]  # Distance en km si applicable


class RegulatoryEngine:
    """
    Moteur de projection réglementaire.
    Identifie les sites et fournisseurs impactés par des changements réglementaires.
    """
    
    def __init__(self):
        """Initialise le moteur réglementaire"""
        pass
    
    @staticmethod
    def normalize_country(country: str) -> str:
        """Normalise le nom d'un pays (minuscules, sans accents)"""
        return country.lower().strip()
    
    @staticmethod
    def normalize_sector(sector: str) -> str:
        """Normalise le nom d'un secteur"""
        return sector.lower().strip()
    
    def find_affected_by_regulation(
        self,
        regulation_countries: List[str],
        regulation_sectors: Optional[List[str]],
        regulation_products: Optional[List[str]],
        sites: List[Dict],
        suppliers: List[Dict]
    ) -> Dict:
        """
        Trouve les entités affectées par une réglementation.
        
        Args:
            regulation_countries: Pays concernés par la réglementation
            regulation_sectors: Secteurs concernés (optionnel)
            regulation_products: Produits concernés (optionnel)
            sites: Liste des sites Hutchinson
            suppliers: Liste des fournisseurs
            
        Returns:
            Dictionnaire avec les résultats de l'analyse
        """
        # Normaliser les critères
        reg_countries = set(self.normalize_country(c) for c in regulation_countries)
        reg_sectors = set(self.normalize_sector(s) for s in (regulation_sectors or []))
        reg_products = set(p.lower().strip() for p in (regulation_products or []))
        
        affected_sites = []
        affected_suppliers = []
        
        # Analyser les sites
        for site in sites:
            matching_criteria = []
            
            # Vérifier le pays
            site_country = self.normalize_country(site.get('country', ''))
            if site_country in reg_countries:
                matching_criteria.append(f"pays:{site['country']}")
            
            # Vérifier les secteurs
            site_sectors = site.get('sectors', [])
            for sector in site_sectors:
                if self.normalize_sector(sector) in reg_sectors:
                    matching_criteria.append(f"secteur:{sector}")
            
            # Vérifier les produits
            # Vérifier les produits fabriqués
            site_products = site.get('products', [])
            for product in site_products:
                product_lower = product.lower().strip()
                # Matching flexible : substring match
                if any(reg_prod in product_lower or product_lower in reg_prod for reg_prod in reg_products):
                    matching_criteria.append(f"produit:{product}")

            # Vérifier les matières premières (IMPORTANT pour CBAM !)
            site_raw_materials = site.get('raw_materials', [])
            for material in site_raw_materials:
                material_lower = material.lower().strip()
                # Matching flexible : substring match
                if any(reg_prod in material_lower or material_lower in reg_prod for reg_prod in reg_products):
                    matching_criteria.append(f"matière_première:{material}")

            
            # Si au moins un critère correspond
            if matching_criteria:
                impact_level = self._determine_regulatory_impact_level(
                    len(matching_criteria),
                    site.get('strategic_importance', 'moyen')
                )
                
                affected_sites.append(RegulatoryImpact(
                    entity_id=site['id'],
                    entity_name=site['name'],
                    entity_type="site",
                    impact_level=impact_level,
                    matching_criteria=matching_criteria,
                    compliance_required=True
                ))
        
        # Analyser les fournisseurs
        for supplier in suppliers:
            matching_criteria = []
            
            # Vérifier le pays
            supplier_country = self.normalize_country(supplier.get('country', ''))
            if supplier_country in reg_countries:
                matching_criteria.append(f"pays:{supplier['country']}")
            
            # Vérifier les secteurs
            supplier_sector = supplier.get('sector', '')
            if self.normalize_sector(supplier_sector) in reg_sectors:
                matching_criteria.append(f"secteur:{supplier_sector}")
            
            # Vérifier les produits
            # Vérifier les produits fournis
            supplier_products = supplier.get('products_supplied', [])
            for product in supplier_products:
                product_lower = product.lower().strip()
                # Matching flexible : substring match
                if any(reg_prod in product_lower or product_lower in reg_prod for reg_prod in reg_products):
                    matching_criteria.append(f"produit:{product}")

            
            # Si au moins un critère correspond
            if matching_criteria:
                impact_level = self._determine_regulatory_impact_level(
                    len(matching_criteria),
                    "moyen"  # Par défaut pour les fournisseurs
                )
                
                affected_suppliers.append(RegulatoryImpact(
                    entity_id=supplier['id'],
                    entity_name=supplier['name'],
                    entity_type="supplier",
                    impact_level=impact_level,
                    matching_criteria=matching_criteria,
                    compliance_required=True
                ))
        
        return {
            "regulation_scope": {
                "countries": list(regulation_countries),
                "sectors": list(regulation_sectors or []),
                "products": list(regulation_products or [])
            },
            "total_affected": len(affected_sites) + len(affected_suppliers),
            "affected_sites_count": len(affected_sites),
            "affected_suppliers_count": len(affected_suppliers),
            "affected_sites": [
                {
                    "id": s.entity_id,
                    "name": s.entity_name,
                    "impact_level": s.impact_level,
                    "matching_criteria": s.matching_criteria,
                    "compliance_required": s.compliance_required
                }
                for s in affected_sites
            ],
            "affected_suppliers": [
                {
                    "id": s.entity_id,
                    "name": s.entity_name,
                    "impact_level": s.impact_level,
                    "matching_criteria": s.matching_criteria,
                    "compliance_required": s.compliance_required
                }
                for s in affected_suppliers
            ]
        }
    
    def _determine_regulatory_impact_level(
        self,
        matching_count: int,
        strategic_importance: str
    ) -> str:
        """
        Détermine le niveau d'impact réglementaire.
        
        Args:
            matching_count: Nombre de critères correspondants
            strategic_importance: Importance stratégique de l'entité
            
        Returns:
            Niveau d'impact
        """
        # Plus il y a de critères correspondants, plus l'impact est fort
        if matching_count >= 3:
            return "critique"
        elif matching_count == 2:
            return "fort"
        elif matching_count == 1:
            if strategic_importance in ["critique", "fort"]:
                return "fort"
            else:
                return "moyen"
        else:
            return "faible"


class GeopoliticalEngine:
    """
    Moteur de projection géopolitique.
    Identifie les sites et fournisseurs impactés par des événements géopolitiques.
    """
    
    def __init__(self):
        """Initialise le moteur géopolitique"""
        pass
    
    @staticmethod
    def normalize_country(country: str) -> str:
        """Normalise le nom d'un pays"""
        return country.lower().strip()
    
    def find_affected_by_geopolitical_event(
        self,
        affected_countries: List[str],
        neighboring_countries: Optional[List[str]],
        event_type: str,  # "conflit", "sanction", "instabilite", "greve"
        sites: List[Dict],
        suppliers: List[Dict]
    ) -> Dict:
        """
        Trouve les entités affectées par un événement géopolitique.
        
        Args:
            affected_countries: Pays directement affectés
            neighboring_countries: Pays voisins potentiellement impactés
            event_type: Type d'événement géopolitique
            sites: Liste des sites Hutchinson
            suppliers: Liste des fournisseurs
            
        Returns:
            Dictionnaire avec les résultats de l'analyse
        """
        # Normaliser les pays
        direct_countries = set(self.normalize_country(c) for c in affected_countries)
        neighbor_countries = set(self.normalize_country(c) for c in (neighboring_countries or []))
        
        affected_sites = []
        affected_suppliers = []
        
        # Analyser les sites
        for site in sites:
            site_country = self.normalize_country(site.get('country', ''))
            risk_factors = []
            impact_level = None
            
            if site_country in direct_countries:
                risk_factors.append(f"Pays directement affecté: {site['country']}")
                impact_level = "critique"
            elif site_country in neighbor_countries:
                risk_factors.append(f"Pays voisin affecté: {site['country']}")
                impact_level = "fort"
            
            if risk_factors:
                # Ajouter le type d'événement
                risk_factors.append(f"Type d'événement: {event_type}")
                
                # Ajuster selon l'importance stratégique
                strategic_importance = site.get('strategic_importance', 'moyen')
                if strategic_importance == "critique" and impact_level == "fort":
                    impact_level = "critique"
                
                affected_sites.append(GeopoliticalImpact(
                    entity_id=site['id'],
                    entity_name=site['name'],
                    entity_type="site",
                    impact_level=impact_level,
                    risk_factors=risk_factors,
                    proximity_to_conflict=None  # Pourrait être calculé si coordonnées disponibles
                ))
        
        # Analyser les fournisseurs
        for supplier in suppliers:
            supplier_country = self.normalize_country(supplier.get('country', ''))
            risk_factors = []
            impact_level = None
            
            if supplier_country in direct_countries:
                risk_factors.append(f"Pays directement affecté: {supplier['country']}")
                impact_level = "critique"
            elif supplier_country in neighbor_countries:
                risk_factors.append(f"Pays voisin affecté: {supplier['country']}")
                impact_level = "fort"
            
            if risk_factors:
                risk_factors.append(f"Type d'événement: {event_type}")
                
                affected_suppliers.append(GeopoliticalImpact(
                    entity_id=supplier['id'],
                    entity_name=supplier['name'],
                    entity_type="supplier",
                    impact_level=impact_level,
                    risk_factors=risk_factors,
                    proximity_to_conflict=None
                ))
        
        return {
            "event_type": event_type,
            "affected_countries": list(affected_countries),
            "neighboring_countries": list(neighboring_countries or []),
            "total_affected": len(affected_sites) + len(affected_suppliers),
            "affected_sites_count": len(affected_sites),
            "affected_suppliers_count": len(affected_suppliers),
            "affected_sites": [
                {
                    "id": s.entity_id,
                    "name": s.entity_name,
                    "impact_level": s.impact_level,
                    "risk_factors": s.risk_factors
                }
                for s in affected_sites
            ],
            "affected_suppliers": [
                {
                    "id": s.entity_id,
                    "name": s.entity_name,
                    "impact_level": s.impact_level,
                    "risk_factors": s.risk_factors
                }
                for s in affected_suppliers
            ]
        }


# Tests unitaires
if __name__ == "__main__":
    print("=== Test Moteur Réglementaire ===")
    reg_engine = RegulatoryEngine()
    
    sites = [
        {"id": "site1", "name": "Paris Plant", "country": "France", "sectors": ["automotive"], 
         "main_products": ["rubber components"], "strategic_importance": "fort"},
        {"id": "site2", "name": "Berlin Plant", "country": "Germany", "sectors": ["automotive"], 
         "main_products": ["seals"], "strategic_importance": "moyen"},
    ]
    
    suppliers = [
        {"id": "sup1", "name": "French Rubber", "country": "France", "sector": "materials",
         "products_supplied": ["raw rubber"]},
    ]
    
    result = reg_engine.find_affected_by_regulation(
        regulation_countries=["France", "Germany"],
        regulation_sectors=["automotive"],
        regulation_products=["rubber components"],
        sites=sites,
        suppliers=suppliers
    )
    
    print(f"Total affecté: {result['total_affected']}")
    print(f"Sites: {result['affected_sites_count']}, Fournisseurs: {result['affected_suppliers_count']}")
    
    print("\n=== Test Moteur Géopolitique ===")
    geo_engine = GeopoliticalEngine()
    
    result2 = geo_engine.find_affected_by_geopolitical_event(
        affected_countries=["Ukraine"],
        neighboring_countries=["Poland", "Romania"],
        event_type="conflit",
        sites=sites,
        suppliers=suppliers
    )
    
    print(f"Total affecté: {result2['total_affected']}")
