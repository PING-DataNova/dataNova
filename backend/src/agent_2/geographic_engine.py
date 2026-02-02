"""
Moteur de Projection Géographique pour Agent 2

Ce module gère la projection géographique des événements climatiques
sur les sites et fournisseurs en utilisant les coordonnées GPS.
"""

import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Location:
    """Représente une localisation géographique"""
    id: str
    name: str
    latitude: float
    longitude: float
    type: str  # "site" ou "supplier"
    metadata: Dict = None


@dataclass
class GeographicImpact:
    """Résultat de l'analyse géographique pour une entité"""
    entity_id: str
    entity_name: str
    entity_type: str  # "site" ou "supplier"
    distance_km: float
    impact_level: str  # "critique", "fort", "moyen", "faible", "negligeable"
    coordinates: Tuple[float, float]


class GeographicEngine:
    """
    Moteur de projection géographique utilisant la formule de Haversine
    pour calculer les distances et déterminer les impacts.
    """
    
    # Rayons d'impact en kilomètres
    IMPACT_ZONES = {
        "critique": 10,      # 0-10 km
        "fort": 50,          # 10-50 km
        "moyen": 100,        # 50-100 km
        "faible": 200,       # 100-200 km
        "negligeable": float('inf')  # > 200 km
    }
    
    def __init__(self):
        """Initialise le moteur géographique"""
        pass
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcule la distance entre deux points GPS en kilomètres
        en utilisant la formule de Haversine.
        
        Args:
            lat1, lon1: Coordonnées du premier point (degrés)
            lat2, lon2: Coordonnées du second point (degrés)
            
        Returns:
            Distance en kilomètres
        """
        # Rayon de la Terre en kilomètres
        R = 6371.0
        
        # Conversion en radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Différences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Formule de Haversine
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        return distance
    
    @staticmethod
    def determine_impact_level(distance_km: float) -> str:
        """
        Détermine le niveau d'impact en fonction de la distance.
        
        Args:
            distance_km: Distance en kilomètres
            
        Returns:
            Niveau d'impact: "critique", "fort", "moyen", "faible", "negligeable"
        """
        if distance_km <= GeographicEngine.IMPACT_ZONES["critique"]:
            return "critique"
        elif distance_km <= GeographicEngine.IMPACT_ZONES["fort"]:
            return "fort"
        elif distance_km <= GeographicEngine.IMPACT_ZONES["moyen"]:
            return "moyen"
        elif distance_km <= GeographicEngine.IMPACT_ZONES["faible"]:
            return "faible"
        else:
            return "negligeable"
    
    def find_affected_entities(
        self,
        event_lat: float,
        event_lon: float,
        entities: List[Location],
        max_distance_km: float = 200
    ) -> List[GeographicImpact]:
        """
        Trouve toutes les entités (sites/fournisseurs) affectées par un événement
        dans un rayon donné.
        
        Args:
            event_lat, event_lon: Coordonnées de l'événement
            entities: Liste des sites et fournisseurs à analyser
            max_distance_km: Distance maximale à considérer (défaut: 200 km)
            
        Returns:
            Liste des entités affectées avec leur niveau d'impact
        """
        affected = []
        
        for entity in entities:
            # Calculer la distance
            distance = self.haversine_distance(
                event_lat, event_lon,
                entity.latitude, entity.longitude
            )
            
            # Filtrer par distance maximale
            if distance <= max_distance_km:
                impact_level = self.determine_impact_level(distance)
                
                affected.append(GeographicImpact(
                    entity_id=entity.id,
                    entity_name=entity.name,
                    entity_type=entity.type,
                    distance_km=round(distance, 2),
                    impact_level=impact_level,
                    coordinates=(entity.latitude, entity.longitude)
                ))
        
        # Trier par distance (plus proche en premier)
        affected.sort(key=lambda x: x.distance_km)
        
        return affected
    
    def analyze_geographic_impact(
        self,
        event_coordinates: Tuple[float, float],
        sites: List[Dict],
        suppliers: List[Dict],
        max_distance_km: float = 200
    ) -> Dict:
        """
        Analyse l'impact géographique complet d'un événement.
        
        Args:
            event_coordinates: (latitude, longitude) de l'événement
            sites: Liste des sites Hutchinson
            suppliers: Liste des fournisseurs
            max_distance_km: Distance maximale à considérer
            
        Returns:
            Dictionnaire avec les résultats de l'analyse
        """
        event_lat, event_lon = event_coordinates
        
        # Convertir les sites en objets Location
        site_locations = [
            Location(
                id=site['id'],
                name=site['name'],
                latitude=site['latitude'],
                longitude=site['longitude'],
                type="site",
                metadata=site
            )
            for site in sites
        ]
        
        # Convertir les fournisseurs en objets Location
        supplier_locations = [
            Location(
                id=sup['id'],
                name=sup['name'],
                latitude=sup['latitude'],
                longitude=sup['longitude'],
                type="supplier",
                metadata=sup
            )
            for sup in suppliers
        ]
        
        # Trouver les entités affectées
        all_entities = site_locations + supplier_locations
        affected_entities = self.find_affected_entities(
            event_lat, event_lon,
            all_entities,
            max_distance_km
        )
        
        # Séparer sites et fournisseurs
        affected_sites = [e for e in affected_entities if e.entity_type == "site"]
        affected_suppliers = [e for e in affected_entities if e.entity_type == "supplier"]
        
        # Statistiques
        impact_stats = {
            "critique": len([e for e in affected_entities if e.impact_level == "critique"]),
            "fort": len([e for e in affected_entities if e.impact_level == "fort"]),
            "moyen": len([e for e in affected_entities if e.impact_level == "moyen"]),
            "faible": len([e for e in affected_entities if e.impact_level == "faible"])
        }
        
        return {
            "event_coordinates": event_coordinates,
            "total_affected": len(affected_entities),
            "affected_sites_count": len(affected_sites),
            "affected_suppliers_count": len(affected_suppliers),
            "affected_sites": [
                {
                    "id": s.entity_id,
                    "name": s.entity_name,
                    "distance_km": s.distance_km,
                    "impact_level": s.impact_level,
                    "coordinates": s.coordinates
                }
                for s in affected_sites
            ],
            "affected_suppliers": [
                {
                    "id": s.entity_id,
                    "name": s.entity_name,
                    "distance_km": s.distance_km,
                    "impact_level": s.impact_level,
                    "coordinates": s.coordinates
                }
                for s in affected_suppliers
            ],
            "impact_statistics": impact_stats,
            "max_distance_analyzed_km": max_distance_km
        }


# Fonction utilitaire pour tests rapides
def test_geographic_engine():
    """Test rapide du moteur géographique"""
    engine = GeographicEngine()
    
    # Événement: Inondation à Bangkok
    event_lat, event_lon = 13.7563, 100.5018
    
    # Sites fictifs
    sites = [
        {"id": "site1", "name": "Bangkok Plant", "latitude": 13.7563, "longitude": 100.5018},
        {"id": "site2", "name": "Rayong Plant", "latitude": 12.6814, "longitude": 101.2815},
    ]
    
    # Fournisseurs fictifs
    suppliers = [
        {"id": "sup1", "name": "Thai Rubber Co", "latitude": 13.8000, "longitude": 100.5500},
        {"id": "sup2", "name": "Bangkok Materials", "latitude": 13.7000, "longitude": 100.4500},
    ]
    
    result = engine.analyze_geographic_impact(
        (event_lat, event_lon),
        sites,
        suppliers,
        max_distance_km=200
    )
    
    print("=== Test Moteur Géographique ===")
    print(f"Total affecté: {result['total_affected']}")
    print(f"Sites affectés: {result['affected_sites_count']}")
    print(f"Fournisseurs affectés: {result['affected_suppliers_count']}")
    print("\nDétails:")
    for site in result['affected_sites']:
        print(f"  - {site['name']}: {site['distance_km']} km ({site['impact_level']})")
    for sup in result['affected_suppliers']:
        print(f"  - {sup['name']}: {sup['distance_km']} km ({sup['impact_level']})")


if __name__ == "__main__":
    test_geographic_engine()
