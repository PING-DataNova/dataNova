"""
Analyseur de Criticité pour Agent 2

Ce module analyse la criticité des impacts identifiés en fonction de :
- Fournisseur unique vs double-source
- Importance stratégique
- Impact sur la supply chain
- Délais de remplacement
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class CriticalityAnalysis:
    """Résultat de l'analyse de criticité pour une entité"""
    entity_id: str
    entity_name: str
    entity_type: str  # "site" ou "supplier"
    overall_criticality: str  # "critique", "fort", "moyen", "faible"
    criticality_factors: Dict[str, any]
    supply_chain_impact: str
    mitigation_options: List[str]
    urgency_level: int  # 1-5 (5 = urgent)


class CriticalityAnalyzer:
    """
    Analyseur de criticité qui évalue l'impact réel d'un événement
    sur la supply chain en fonction de multiples facteurs.
    """
    
    def __init__(self):
        """Initialise l'analyseur de criticité"""
        pass
    
    def analyze_site_criticality(
        self,
        site: Dict,
        impact_level: str,
        all_sites: List[Dict]
    ) -> CriticalityAnalysis:
        """
        Analyse la criticité d'un site impacté.
        
        Args:
            site: Données du site impacté
            impact_level: Niveau d'impact initial (géographique/réglementaire/géopolitique)
            all_sites: Liste de tous les sites (pour identifier les backups)
            
        Returns:
            Analyse de criticité complète
        """
        criticality_factors = {}
        mitigation_options = []
        
        # 1. Importance stratégique
        strategic_importance = site.get('strategic_importance', 'moyen')
        criticality_factors['strategic_importance'] = strategic_importance
        
        # 2. Production annuelle
        production_value = site.get('annual_production_value', 0)
        criticality_factors['production_value_eur'] = production_value
        
        # 3. Nombre d'employés
        employee_count = site.get('employee_count', 0)
        criticality_factors['employee_count'] = employee_count
        
        # 4. Produits fabriqués
        main_products = site.get('main_products', [])
        criticality_factors['main_products'] = main_products
        
        # 5. Secteurs desservis
        sectors = site.get('sectors', [])
        criticality_factors['sectors_served'] = sectors
        
        # 6. Sites de backup possibles (même produits)
        backup_sites = [
            s for s in all_sites 
            if s['id'] != site['id'] 
            and any(p in s.get('main_products', []) for p in main_products)
        ]
        has_backup = len(backup_sites) > 0
        criticality_factors['has_backup_sites'] = has_backup
        criticality_factors['backup_sites_count'] = len(backup_sites)
        
        if has_backup:
            mitigation_options.append(f"Transférer production vers {len(backup_sites)} site(s) alternatif(s)")
        else:
            mitigation_options.append("AUCUN site de backup identifié - Risque critique")
        
        # 7. Calcul de la criticité globale
        overall_criticality = self._calculate_site_criticality(
            impact_level,
            strategic_importance,
            has_backup,
            production_value
        )
        
        # 8. Impact supply chain
        supply_chain_impact = self._assess_supply_chain_impact(
            overall_criticality,
            has_backup,
            sectors
        )
        
        # 9. Niveau d'urgence
        urgency_level = self._calculate_urgency(
            overall_criticality,
            impact_level,
            has_backup
        )
        
        # 10. Options de mitigation supplémentaires
        if production_value > 10_000_000:  # > 10M€
            mitigation_options.append("Site à forte valeur - Priorité maximale")
        
        if employee_count > 500:
            mitigation_options.append("Site majeur - Impact social important")
        
        return CriticalityAnalysis(
            entity_id=site['id'],
            entity_name=site['name'],
            entity_type="site",
            overall_criticality=overall_criticality,
            criticality_factors=criticality_factors,
            supply_chain_impact=supply_chain_impact,
            mitigation_options=mitigation_options,
            urgency_level=urgency_level
        )
    
    def analyze_supplier_criticality(
        self,
        supplier: Dict,
        impact_level: str,
        supplier_relationships: List[Dict]
    ) -> CriticalityAnalysis:
        """
        Analyse la criticité d'un fournisseur impacté.
        
        Args:
            supplier: Données du fournisseur impacté
            impact_level: Niveau d'impact initial
            supplier_relationships: Relations fournisseur-site
            
        Returns:
            Analyse de criticité complète
        """
        criticality_factors = {}
        mitigation_options = []
        
        # 1. Trouver les relations pour ce fournisseur
        relations = [r for r in supplier_relationships if r['supplier_id'] == supplier['id']]
        criticality_factors['sites_served_count'] = len(relations)
        
        # 2. Fournisseur unique ?
        is_unique_supplier = any(r.get('is_unique_supplier', False) for r in relations)
        criticality_factors['is_unique_supplier'] = is_unique_supplier
        
        # 3. Backup disponible ?
        has_backup = any(r.get('backup_supplier_id') is not None for r in relations)
        criticality_factors['has_backup_supplier'] = has_backup
        
        # 4. Criticité de la relation
        if relations:
            max_criticality = max([r.get('criticality', 'Standard') for r in relations], 
                                 key=lambda x: ['Standard', 'Important', 'Critique'].index(x) if x in ['Standard', 'Important', 'Critique'] else 0)
        else:
            max_criticality = 'Standard'
        criticality_factors['relationship_criticality'] = max_criticality
        
        # 5. Volume annuel
        total_volume = sum(r.get('annual_volume_eur', 0) for r in relations)
        criticality_factors['annual_volume_eur'] = total_volume
        
        # 6. Délais de livraison
        avg_lead_time = sum(r.get('lead_time_days', 0) for r in relations) / len(relations) if relations else 0
        criticality_factors['average_lead_time_days'] = round(avg_lead_time, 1)
        
        # 7. Santé financière
        financial_health = supplier.get('financial_health', 'moyen')
        criticality_factors['financial_health'] = financial_health
        
        # 8. Options de mitigation
        if is_unique_supplier and not has_backup:
            mitigation_options.append("FOURNISSEUR UNIQUE SANS BACKUP - RISQUE CRITIQUE")
            mitigation_options.append("Action urgente: Identifier fournisseurs alternatifs")
        elif is_unique_supplier and has_backup:
            mitigation_options.append("Fournisseur unique mais backup identifié")
            mitigation_options.append("Action: Activer le fournisseur de backup")
        elif not is_unique_supplier:
            mitigation_options.append("Double-source disponible")
            mitigation_options.append("Action: Basculer vers fournisseur alternatif")
        
        if total_volume > 5_000_000:  # > 5M€
            mitigation_options.append(f"Volume élevé ({total_volume:,.0f}€) - Impact financier majeur")
        
        if avg_lead_time > 30:
            mitigation_options.append(f"Délais longs ({avg_lead_time:.0f} jours) - Anticiper les commandes")
        
        # 9. Calcul de la criticité globale
        overall_criticality = self._calculate_supplier_criticality(
            impact_level,
            is_unique_supplier,
            has_backup,
            max_criticality,
            total_volume
        )
        
        # 10. Impact supply chain
        supply_chain_impact = self._assess_supplier_supply_chain_impact(
            overall_criticality,
            len(relations),
            is_unique_supplier
        )
        
        # 11. Niveau d'urgence
        urgency_level = self._calculate_urgency(
            overall_criticality,
            impact_level,
            has_backup
        )
        
        return CriticalityAnalysis(
            entity_id=supplier['id'],
            entity_name=supplier['name'],
            entity_type="supplier",
            overall_criticality=overall_criticality,
            criticality_factors=criticality_factors,
            supply_chain_impact=supply_chain_impact,
            mitigation_options=mitigation_options,
            urgency_level=urgency_level
        )
    
    def _calculate_site_criticality(
        self,
        impact_level: str,
        strategic_importance: str,
        has_backup: bool,
        production_value: float
    ) -> str:
        """Calcule la criticité globale d'un site"""
        # Matrice de criticité
        score = 0
        
        # Impact initial
        impact_scores = {"critique": 4, "fort": 3, "moyen": 2, "faible": 1}
        score += impact_scores.get(impact_level, 1)
        
        # Importance stratégique
        strategic_scores = {"critique": 3, "fort": 2, "moyen": 1, "faible": 0}
        score += strategic_scores.get(strategic_importance, 1)
        
        # Backup
        if not has_backup:
            score += 2
        
        # Valeur de production
        if production_value > 20_000_000:
            score += 2
        elif production_value > 10_000_000:
            score += 1
        
        # Déterminer la criticité
        if score >= 8:
            return "critique"
        elif score >= 6:
            return "fort"
        elif score >= 4:
            return "moyen"
        else:
            return "faible"
    
    def _calculate_supplier_criticality(
        self,
        impact_level: str,
        is_unique: bool,
        has_backup: bool,
        relationship_criticality: str,
        volume: float
    ) -> str:
        """Calcule la criticité globale d'un fournisseur"""
        score = 0
        
        # Impact initial
        impact_scores = {"critique": 4, "fort": 3, "moyen": 2, "faible": 1}
        score += impact_scores.get(impact_level, 1)
        
        # Fournisseur unique sans backup = CRITIQUE
        if is_unique and not has_backup:
            score += 4
        elif is_unique and has_backup:
            score += 2
        
        # Criticité de la relation
        rel_scores = {"Critique": 3, "Important": 2, "Standard": 1}
        score += rel_scores.get(relationship_criticality, 1)
        
        # Volume
        if volume > 10_000_000:
            score += 2
        elif volume > 5_000_000:
            score += 1
        
        # Déterminer la criticité
        if score >= 9:
            return "critique"
        elif score >= 6:
            return "fort"
        elif score >= 4:
            return "moyen"
        else:
            return "faible"
    
    def _assess_supply_chain_impact(
        self,
        criticality: str,
        has_backup: bool,
        sectors: List[str]
    ) -> str:
        """Évalue l'impact sur la supply chain pour un site"""
        if criticality == "critique" and not has_backup:
            return "Rupture de supply chain probable - Impact majeur sur production"
        elif criticality == "critique" and has_backup:
            return "Perturbation majeure - Backup disponible mais délais attendus"
        elif criticality == "fort":
            return "Perturbation significative - Réorganisation nécessaire"
        elif criticality == "moyen":
            return "Impact modéré - Ajustements possibles"
        else:
            return "Impact limité - Gestion standard"
    
    def _assess_supplier_supply_chain_impact(
        self,
        criticality: str,
        sites_count: int,
        is_unique: bool
    ) -> str:
        """Évalue l'impact sur la supply chain pour un fournisseur"""
        if criticality == "critique" and is_unique:
            return f"Rupture d'approvisionnement critique - {sites_count} site(s) impacté(s)"
        elif criticality == "critique":
            return f"Perturbation majeure - {sites_count} site(s) à réorganiser"
        elif criticality == "fort":
            return f"Impact significatif sur {sites_count} site(s)"
        elif criticality == "moyen":
            return f"Impact modéré - {sites_count} site(s) concerné(s)"
        else:
            return "Impact limité"
    
    def _calculate_urgency(
        self,
        criticality: str,
        impact_level: str,
        has_backup: bool
    ) -> int:
        """Calcule le niveau d'urgence (1-5)"""
        if criticality == "critique" and not has_backup:
            return 5
        elif criticality == "critique" and has_backup:
            return 4
        elif criticality == "fort":
            return 3
        elif criticality == "moyen":
            return 2
        else:
            return 1


# Test unitaire
if __name__ == "__main__":
    analyzer = CriticalityAnalyzer()
    
    print("=== Test Analyse de Criticité Site ===")
    site = {
        "id": "site1",
        "name": "Bangkok Plant",
        "strategic_importance": "critique",
        "annual_production_value": 25_000_000,
        "employee_count": 800,
        "main_products": ["rubber seals", "gaskets"],
        "sectors": ["automotive"]
    }
    
    all_sites = [
        site,
        {"id": "site2", "name": "Rayong Plant", "main_products": ["rubber seals"], "sectors": ["automotive"]}
    ]
    
    result = analyzer.analyze_site_criticality(site, "critique", all_sites)
    print(f"Criticité globale: {result.overall_criticality}")
    print(f"Impact supply chain: {result.supply_chain_impact}")
    print(f"Urgence: {result.urgency_level}/5")
    print(f"Options de mitigation: {len(result.mitigation_options)}")
    for option in result.mitigation_options:
        print(f"  - {option}")
