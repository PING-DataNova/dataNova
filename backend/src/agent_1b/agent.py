"""
Agent 1B - Filtre de Pertinence Multi-Type
==========================================

Agent intelligent qui détermine si un événement (réglementaire, climatique, géopolitique)
concerne Hutchinson et identifie les entités affectées (sites + fournisseurs).

Architecture:
- Réglementaire: Approche triangulée (keywords 30% + NC codes 30% + LLM 40%)
- Climatique: Distance géographique (Haversine)
- Géopolitique: Correspondance pays/région

Sorties:
- decision: OUI / NON / PARTIELLEMENT
- confidence: 0.0 - 1.0
- reasoning: Explication détaillée
- affected_sites: Liste des IDs de sites concernés
- affected_suppliers: Liste des IDs de fournisseurs concernés
- matched_elements: Détails des correspondances trouvées

Auteur: DataNova PING
Date: 2026-02-01
"""

import structlog
import json
import math
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv

# Charger les variables d'environnement
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from src.storage.database import get_session
from src.storage.models import (
    Document, 
    PertinenceCheck, 
    HutchinsonSite, 
    Supplier,
    SupplierRelationship
)

logger = structlog.get_logger()


# ============================================================================
# CONSTANTES
# ============================================================================

# Seuils de distance pour événements climatiques (en km)
DISTANCE_THRESHOLD_DIRECT = 50  # < 50km = OUI
DISTANCE_THRESHOLD_INDIRECT = 200  # 50-200km = PARTIELLEMENT, > 200km = NON

# Seuils de confiance
CONFIDENCE_HIGH = 0.8
CONFIDENCE_MEDIUM = 0.5
CONFIDENCE_LOW = 0.3


# ============================================================================
# UTILITAIRES GÉOGRAPHIQUES
# ============================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcule la distance en km entre deux points GPS avec la formule de Haversine
    
    Args:
        lat1, lon1: Coordonnées du point 1
        lat2, lon2: Coordonnées du point 2
        
    Returns:
        Distance en kilomètres
    """
    R = 6371  # Rayon de la Terre en km
    
    # Convertir en radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Formule de Haversine
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return round(distance, 2)


def normalize_country_name(country: str) -> str:
    """
    Normalise un nom de pays pour la comparaison
    
    Args:
        country: Nom du pays (ex: "France", "FRANCE", "france")
        
    Returns:
        Nom normalisé en minuscules sans accents
    """
    import unicodedata
    
    # Supprimer les accents
    country = unicodedata.normalize('NFD', country)
    country = ''.join(char for char in country if unicodedata.category(char) != 'Mn')
    
    # Minuscules et strip
    country = country.lower().strip()
    
    # Mappings communs
    mappings = {
        "usa": "united states",
        "us": "united states",
        "états-unis": "united states",
        "etats-unis": "united states",
        "uk": "united kingdom",
        "royaume-uni": "united kingdom",
        "chine": "china",
        "inde": "india",
        "allemagne": "germany",
        "espagne": "spain",
        "italie": "italy",
    }
    
    return mappings.get(country, country)


# ============================================================================
# AGENT 1B - CLASSE PRINCIPALE
# ============================================================================

class Agent1B:
    """
    Agent 1B - Filtre de Pertinence Multi-Type
    
    Détermine si un événement concerne Hutchinson et identifie les entités affectées.
    """
    
    def __init__(self, anthropic_api_key: Optional[str] = None):
        """
        Initialise l'Agent 1B
        
        Args:
            anthropic_api_key: Clé API Anthropic (optionnel, utilise variable d'env par défaut)
        """
        api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.anthropic_client = Anthropic(api_key=api_key)
        logger.info("agent_1b_initialized")
    
    def check_pertinence(
        self,
        document_id: str,
        save_to_db: bool = True
    ) -> Dict:
        """
        Vérifie la pertinence d'un document et identifie les entités affectées
        
        Args:
            document_id: ID du document à analyser
            save_to_db: Si True, sauvegarde les résultats en BDD
            
        Returns:
            Dict avec decision, confidence, reasoning, affected_sites, affected_suppliers, matched_elements
        """
        session = get_session()
        
        try:
            # Récupérer le document
            document = session.query(Document).filter_by(id=document_id).first()
            
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            logger.info(
                "pertinence_check_started",
                document_id=document_id[:8],
                event_type=document.event_type
            )
            
            # Normaliser le type d'événement (supporter "regulation" et "reglementaire")
            event_type = document.event_type.lower()
            if event_type in ["regulation", "regulatory"]:
                event_type = "reglementaire"
            elif event_type in ["climate", "weather"]:
                event_type = "climatique"
            elif event_type in ["geopolitical", "geopolitic"]:
                event_type = "geopolitique"
            
            # Router vers la bonne méthode selon le type d'événement
            if event_type == "reglementaire":
                result = self._check_regulatory_pertinence(document, session)
            elif event_type == "climatique":
                result = self._check_climatic_pertinence(document, session)
            elif event_type == "geopolitique":
                result = self._check_geopolitical_pertinence(document, session)
            else:
                raise ValueError(f"Type d'événement non supporté: {document.event_type}")
            
            # Ajouter les métadonnées
            result["document_id"] = document_id
            result["event_type"] = document.event_type
            result["analysis_timestamp"] = datetime.utcnow().isoformat()
            
            # Sauvegarder en BDD si demandé
            if save_to_db:
                self._save_to_database(result, session)
            
            logger.info(
                "pertinence_check_completed",
                document_id=document_id[:8],
                decision=result["decision"],
                confidence=result["confidence"],
                affected_sites_count=len(result["affected_sites"]),
                affected_suppliers_count=len(result["affected_suppliers"])
            )
            
            return result
            
        finally:
            session.close()
    
    # ========================================================================
    # MÉTHODE 1: ÉVÉNEMENTS RÉGLEMENTAIRES
    # ========================================================================
    
    def _check_regulatory_pertinence(
        self,
        document: Document,
        session
    ) -> Dict:
        """
        Analyse de pertinence pour événements réglementaires
        
        Approche triangulée:
        - 30% Analyse par mots-clés
        - 30% Analyse par codes NC
        - 40% Analyse sémantique LLM
        
        Args:
            document: Document à analyser
            session: Session SQLAlchemy
            
        Returns:
            Dict avec decision, confidence, reasoning, affected_sites, affected_suppliers, matched_elements
        """
        logger.info("regulatory_pertinence_check", document_id=document.id[:8])
        
        # Charger le profil Hutchinson
        hutchinson_profile = self._load_hutchinson_profile()
        
        # 1. Analyse par mots-clés (30%)
        keyword_score, keyword_matches = self._analyze_keywords(
            document.content or document.summary or "",
            hutchinson_profile["keywords"]
        )
        
        # 2. Analyse par codes NC (30%)
        nc_score, nc_matches = self._analyze_nc_codes(
            document.content or document.summary or "",
            hutchinson_profile["nc_codes"]
        )
        
        # 3. Analyse sémantique LLM (40%)
        semantic_score, semantic_reasoning, semantic_matches = self._analyze_semantically_regulatory(
            document,
            hutchinson_profile
        )
        
        # Calcul du score final pondéré
        final_score = (
            keyword_score * 0.30 +
            nc_score * 0.30 +
            semantic_score * 0.40
        )
        
        # Déterminer la décision
        if final_score >= 0.7:
            decision = "OUI"
            confidence = min(final_score, 1.0)
        elif final_score >= 0.4:
            decision = "PARTIELLEMENT"
            confidence = final_score
        else:
            decision = "NON"
            confidence = 1.0 - final_score
        
        # Construire le reasoning
        reasoning = self._build_regulatory_reasoning(
            keyword_score, keyword_matches,
            nc_score, nc_matches,
            semantic_score, semantic_reasoning,
            final_score, decision
        )
        
        # Identifier les entités affectées (tous les sites et fournisseurs si pertinent)
        affected_sites = []
        affected_suppliers = []
        
        if decision in ["OUI", "PARTIELLEMENT"]:
            # Pour les événements réglementaires, tous les sites/fournisseurs peuvent être affectés
            # selon le scope géographique et les produits
            sites = session.query(HutchinsonSite).filter_by(active=True).all()
            suppliers = session.query(Supplier).filter_by(active=True).all()
            
            # Filtrer selon le scope géographique si disponible
            geo_scope = document.geographic_scope or {}
            countries = geo_scope.get("countries", [])
            
            if countries:
                affected_sites = [
                    site.id for site in sites
                    if normalize_country_name(site.country) in [normalize_country_name(c) for c in countries]
                ]
                affected_suppliers = [
                    supplier.id for supplier in suppliers
                    if normalize_country_name(supplier.country) in [normalize_country_name(c) for c in countries]
                ]
            else:
                # Pas de filtre géographique, tous sont potentiellement affectés
                affected_sites = [site.id for site in sites]
                affected_suppliers = [supplier.id for supplier in suppliers]
        
        # Construire matched_elements
        matched_elements = {
            "keyword_analysis": {
                "score": keyword_score,
                "matches": keyword_matches
            },
            "nc_code_analysis": {
                "score": nc_score,
                "matches": nc_matches
            },
            "semantic_analysis": {
                "score": semantic_score,
                "reasoning": semantic_reasoning,
                "matches": semantic_matches
            },
            "final_score": final_score,
            "weights": {
                "keywords": 0.30,
                "nc_codes": 0.30,
                "semantic": 0.40
            }
        }
        
        return {
            "decision": decision,
            "confidence": round(confidence, 3),
            "reasoning": reasoning,
            "affected_sites": affected_sites,
            "affected_suppliers": affected_suppliers,
            "matched_elements": matched_elements
        }
    
    def _analyze_keywords(self, text: str, keywords: List[str]) -> Tuple[float, List[str]]:
        """
        Analyse par mots-clés
        
        Returns:
            (score, keywords_found)
        """
        text_lower = text.lower()
        keywords_found = [kw for kw in keywords if kw.lower() in text_lower]
        
        if not keywords:
            return 0.0, []
        
        score = len(keywords_found) / len(keywords)
        return min(score, 1.0), keywords_found
    
    def _analyze_nc_codes(self, text: str, nc_codes: List[str]) -> Tuple[float, List[str]]:
        """
        Analyse par codes NC
        
        Returns:
            (score, nc_codes_found)
        """
        import re
        
        # Pattern pour détecter les codes NC (ex: 4001, 4001.22, 40.01)
        nc_pattern = r'\b\d{4}(?:[.\s]\d{2})?\b'
        found_codes = re.findall(nc_pattern, text)
        
        # Normaliser les codes trouvés
        found_codes_normalized = [code.replace('.', '').replace(' ', '') for code in found_codes]
        
        # Comparer avec les codes Hutchinson
        nc_codes_normalized = [code.replace('.', '').replace(' ', '') for code in nc_codes]
        
        matches = []
        for found in found_codes_normalized:
            for nc in nc_codes_normalized:
                # Correspondance exacte ou partielle (4 premiers chiffres)
                if found == nc or found[:4] == nc[:4]:
                    matches.append(found)
                    break
        
        if not nc_codes:
            return 0.0, []
        
        score = len(set(matches)) / len(nc_codes)
        return min(score, 1.0), list(set(matches))
    
    def _analyze_semantically_regulatory(
        self,
        document: Document,
        hutchinson_profile: Dict
    ) -> Tuple[float, str, Dict]:
        """
        Analyse sémantique LLM pour événements réglementaires
        
        Returns:
            (score, reasoning, matches)
        """
        prompt = f"""Tu es un expert en réglementation internationale et supply chain.

Analyse ce document réglementaire et détermine s'il est pertinent pour l'entreprise Hutchinson.

**Document:**
Titre: {document.title}
Type: {document.event_subtype or "Réglementation"}
Contenu: {(document.content or document.summary or "")[:3000]}

**Profil Hutchinson:**
- Secteurs: {', '.join(hutchinson_profile.get('sectors', []))}
- Produits: {', '.join(hutchinson_profile.get('products', [])[:10])}
- Pays d'opération: {', '.join(hutchinson_profile.get('countries', []))}
- Codes NC principaux: {', '.join(hutchinson_profile.get('nc_codes', [])[:20])}

**Ta mission:**
1. Détermine si cette réglementation s'applique à Hutchinson
2. Identifie les produits/secteurs/pays concernés
3. Évalue le niveau de pertinence (0.0 = non pertinent, 1.0 = très pertinent)

**Format de réponse (JSON):**
{{
    "is_pertinent": true/false,
    "pertinence_score": 0.0-1.0,
    "reasoning": "Explication détaillée de ton analyse",
    "matched_products": ["produit1", "produit2"],
    "matched_countries": ["pays1", "pays2"],
    "matched_sectors": ["secteur1"]
}}

Réponds UNIQUEMENT avec le JSON, sans texte avant ou après."""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text.strip()
            
            # Parser le JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            
            score = result.get("pertinence_score", 0.5)
            reasoning = result.get("reasoning", "Analyse sémantique effectuée")
            matches = {
                "products": result.get("matched_products", []),
                "countries": result.get("matched_countries", []),
                "sectors": result.get("matched_sectors", [])
            }
            
            return score, reasoning, matches
            
        except Exception as e:
            logger.error("semantic_analysis_failed", error=str(e))
            return 0.5, f"Erreur d'analyse sémantique: {str(e)}", {}
    
    def _build_regulatory_reasoning(
        self,
        keyword_score: float,
        keyword_matches: List[str],
        nc_score: float,
        nc_matches: List[str],
        semantic_score: float,
        semantic_reasoning: str,
        final_score: float,
        decision: str
    ) -> str:
        """
        Construit le reasoning pour événements réglementaires
        """
        reasoning_parts = [
            f"**Décision: {decision}** (Score final: {final_score:.2f})",
            "",
            "**Analyse triangulée:**",
            "",
            f"1. **Mots-clés (30%):** Score = {keyword_score:.2f}",
        ]
        
        if keyword_matches:
            reasoning_parts.append(f"   - Mots-clés trouvés: {', '.join(keyword_matches[:5])}")
        else:
            reasoning_parts.append("   - Aucun mot-clé trouvé")
        
        reasoning_parts.extend([
            "",
            f"2. **Codes NC (30%):** Score = {nc_score:.2f}",
        ])
        
        if nc_matches:
            reasoning_parts.append(f"   - Codes NC trouvés: {', '.join(nc_matches[:5])}")
        else:
            reasoning_parts.append("   - Aucun code NC trouvé")
        
        reasoning_parts.extend([
            "",
            f"3. **Analyse sémantique LLM (40%):** Score = {semantic_score:.2f}",
            f"   - {semantic_reasoning}",
            "",
            f"**Score final pondéré:** {final_score:.2f} = (0.30 × {keyword_score:.2f}) + (0.30 × {nc_score:.2f}) + (0.40 × {semantic_score:.2f})"
        ])
        
        return "\n".join(reasoning_parts)
    
    # ========================================================================
    # MÉTHODE 2: ÉVÉNEMENTS CLIMATIQUES
    # ========================================================================
    
    def _check_climatic_pertinence(
        self,
        document: Document,
        session
    ) -> Dict:
        """
        Analyse de pertinence pour événements climatiques
        
        Approche: Distance géographique (Haversine)
        - < 50 km = OUI (impact direct)
        - 50-200 km = PARTIELLEMENT (impact indirect possible)
        - > 200 km = NON (trop éloigné)
        
        Args:
            document: Document à analyser
            session: Session SQLAlchemy
            
        Returns:
            Dict avec decision, confidence, reasoning, affected_sites, affected_suppliers, matched_elements
        """
        logger.info("climatic_pertinence_check", document_id=document.id[:8])
        
        # Extraire les coordonnées de l'événement
        geo_scope = document.geographic_scope or {}
        coordinates = geo_scope.get("coordinates", {})
        
        event_lat = coordinates.get("latitude")
        event_lon = coordinates.get("longitude")
        
        if event_lat is None or event_lon is None:
            # Pas de coordonnées, impossible de déterminer
            return {
                "decision": "NON",
                "confidence": 0.0,
                "reasoning": "Impossible de déterminer la pertinence: coordonnées géographiques manquantes dans le document.",
                "affected_sites": [],
                "affected_suppliers": [],
                "matched_elements": {"error": "missing_coordinates"}
            }
        
        # Récupérer tous les sites et fournisseurs actifs
        sites = session.query(HutchinsonSite).filter_by(active=True).all()
        suppliers = session.query(Supplier).filter_by(active=True).all()
        
        # Calculer les distances
        site_distances = []
        for site in sites:
            if site.latitude and site.longitude:
                distance = haversine_distance(event_lat, event_lon, site.latitude, site.longitude)
                site_distances.append({
                    "entity_id": site.id,
                    "entity_name": site.name,
                    "entity_type": "site",
                    "distance_km": distance,
                    "country": site.country,
                    "city": site.city
                })
        
        supplier_distances = []
        for supplier in suppliers:
            if supplier.latitude and supplier.longitude:
                distance = haversine_distance(event_lat, event_lon, supplier.latitude, supplier.longitude)
                supplier_distances.append({
                    "entity_id": supplier.id,
                    "entity_name": supplier.name,
                    "entity_type": "supplier",
                    "distance_km": distance,
                    "country": supplier.country,
                    "city": supplier.city
                })
        
        # Trier par distance
        all_distances = site_distances + supplier_distances
        all_distances.sort(key=lambda x: x["distance_km"])
        
        # Déterminer la décision basée sur la distance minimale
        if not all_distances:
            return {
                "decision": "NON",
                "confidence": 0.0,
                "reasoning": "Aucun site ou fournisseur avec coordonnées géographiques disponibles.",
                "affected_sites": [],
                "affected_suppliers": [],
                "matched_elements": {"error": "no_entities_with_coordinates"}
            }
        
        min_distance = all_distances[0]["distance_km"]
        
        # Classifier les entités par zone d'impact
        direct_impact = [e for e in all_distances if e["distance_km"] < DISTANCE_THRESHOLD_DIRECT]
        indirect_impact = [e for e in all_distances if DISTANCE_THRESHOLD_DIRECT <= e["distance_km"] < DISTANCE_THRESHOLD_INDIRECT]
        no_impact = [e for e in all_distances if e["distance_km"] >= DISTANCE_THRESHOLD_INDIRECT]
        
        # Décision
        if direct_impact:
            decision = "OUI"
            confidence = 1.0 - (min_distance / DISTANCE_THRESHOLD_DIRECT)  # Plus proche = plus confiant
            confidence = max(min(confidence, 1.0), 0.7)  # Entre 0.7 et 1.0
        elif indirect_impact:
            decision = "PARTIELLEMENT"
            confidence = 1.0 - ((min_distance - DISTANCE_THRESHOLD_DIRECT) / (DISTANCE_THRESHOLD_INDIRECT - DISTANCE_THRESHOLD_DIRECT))
            confidence = max(min(confidence, 0.7), 0.4)  # Entre 0.4 et 0.7
        else:
            decision = "NON"
            confidence = min(min_distance / 500, 1.0)  # Plus loin = plus confiant dans le NON
            confidence = max(confidence, 0.7)
        
        # Construire le reasoning
        reasoning_parts = [
            f"**Décision: {decision}** (Confiance: {confidence:.2f})",
            "",
            f"**Événement climatique:** {document.event_subtype or 'Non spécifié'}",
            f"**Localisation:** Lat {event_lat:.4f}, Lon {event_lon:.4f}",
            "",
            "**Analyse de proximité:**"
        ]
        
        if direct_impact:
            reasoning_parts.append(f"- **{len(direct_impact)} entité(s) en impact DIRECT** (< {DISTANCE_THRESHOLD_DIRECT} km):")
            for e in direct_impact[:3]:
                reasoning_parts.append(f"  • {e['entity_name']} ({e['entity_type']}) - {e['distance_km']} km - {e['city']}, {e['country']}")
        
        if indirect_impact:
            reasoning_parts.append(f"- **{len(indirect_impact)} entité(s) en impact INDIRECT** ({DISTANCE_THRESHOLD_DIRECT}-{DISTANCE_THRESHOLD_INDIRECT} km):")
            for e in indirect_impact[:3]:
                reasoning_parts.append(f"  • {e['entity_name']} ({e['entity_type']}) - {e['distance_km']} km - {e['city']}, {e['country']}")
        
        if no_impact:
            reasoning_parts.append(f"- {len(no_impact)} entité(s) hors zone d'impact (> {DISTANCE_THRESHOLD_INDIRECT} km)")
        
        reasoning_parts.extend([
            "",
            f"**Distance minimale:** {min_distance:.1f} km",
            f"**Seuils utilisés:** Direct < {DISTANCE_THRESHOLD_DIRECT} km, Indirect < {DISTANCE_THRESHOLD_INDIRECT} km"
        ])
        
        reasoning = "\n".join(reasoning_parts)
        
        # Identifier les entités affectées
        affected_sites = [e["entity_id"] for e in direct_impact + indirect_impact if e["entity_type"] == "site"]
        affected_suppliers = [e["entity_id"] for e in direct_impact + indirect_impact if e["entity_type"] == "supplier"]
        
        # Matched elements
        matched_elements = {
            "event_location": {
                "latitude": event_lat,
                "longitude": event_lon
            },
            "distances": all_distances[:10],  # Top 10 les plus proches
            "direct_impact_count": len(direct_impact),
            "indirect_impact_count": len(indirect_impact),
            "no_impact_count": len(no_impact),
            "min_distance_km": min_distance,
            "thresholds": {
                "direct": DISTANCE_THRESHOLD_DIRECT,
                "indirect": DISTANCE_THRESHOLD_INDIRECT
            }
        }
        
        return {
            "decision": decision,
            "confidence": round(confidence, 3),
            "reasoning": reasoning,
            "affected_sites": affected_sites,
            "affected_suppliers": affected_suppliers,
            "matched_elements": matched_elements
        }
    
    # ========================================================================
    # MÉTHODE 3: ÉVÉNEMENTS GÉOPOLITIQUES
    # ========================================================================
    
    def _check_geopolitical_pertinence(
        self,
        document: Document,
        session
    ) -> Dict:
        """
        Analyse de pertinence pour événements géopolitiques
        
        Approche: Correspondance pays/région
        - Pays direct = OUI (site ou fournisseur dans le pays)
        - Pays indirect = PARTIELLEMENT (pays voisin ou région)
        - Aucun lien = NON
        
        Args:
            document: Document à analyser
            session: Session SQLAlchemy
            
        Returns:
            Dict avec decision, confidence, reasoning, affected_sites, affected_suppliers, matched_elements
        """
        logger.info("geopolitical_pertinence_check", document_id=document.id[:8])
        
        # Extraire les pays concernés par l'événement
        geo_scope = document.geographic_scope or {}
        event_countries = geo_scope.get("countries", [])
        event_regions = geo_scope.get("regions", [])
        
        if not event_countries and not event_regions:
            # Pas de scope géographique, impossible de déterminer
            return {
                "decision": "NON",
                "confidence": 0.0,
                "reasoning": "Impossible de déterminer la pertinence: scope géographique manquant dans le document.",
                "affected_sites": [],
                "affected_suppliers": [],
                "matched_elements": {"error": "missing_geographic_scope"}
            }
        
        # Normaliser les pays de l'événement
        event_countries_normalized = [normalize_country_name(c) for c in event_countries]
        
        # Récupérer tous les sites et fournisseurs actifs
        sites = session.query(HutchinsonSite).filter_by(active=True).all()
        suppliers = session.query(Supplier).filter_by(active=True).all()
        
        # Classifier les entités par type de correspondance
        direct_match_sites = []
        direct_match_suppliers = []
        indirect_match_sites = []
        indirect_match_suppliers = []
        
        # Sites
        for site in sites:
            site_country_normalized = normalize_country_name(site.country)
            
            if site_country_normalized in event_countries_normalized:
                direct_match_sites.append({
                    "entity_id": site.id,
                    "entity_name": site.name,
                    "country": site.country,
                    "match_type": "direct"
                })
            elif self._is_neighboring_country(site.country, event_countries):
                indirect_match_sites.append({
                    "entity_id": site.id,
                    "entity_name": site.name,
                    "country": site.country,
                    "match_type": "neighboring"
                })
        
        # Fournisseurs
        for supplier in suppliers:
            supplier_country_normalized = normalize_country_name(supplier.country)
            
            if supplier_country_normalized in event_countries_normalized:
                direct_match_suppliers.append({
                    "entity_id": supplier.id,
                    "entity_name": supplier.name,
                    "country": supplier.country,
                    "match_type": "direct"
                })
            elif self._is_neighboring_country(supplier.country, event_countries):
                indirect_match_suppliers.append({
                    "entity_id": supplier.id,
                    "entity_name": supplier.name,
                    "country": supplier.country,
                    "match_type": "neighboring"
                })
        
        # Décision
        total_direct = len(direct_match_sites) + len(direct_match_suppliers)
        total_indirect = len(indirect_match_sites) + len(indirect_match_suppliers)
        
        if total_direct > 0:
            decision = "OUI"
            confidence = min(0.7 + (total_direct * 0.05), 1.0)  # Plus d'entités = plus confiant
        elif total_indirect > 0:
            decision = "PARTIELLEMENT"
            confidence = min(0.4 + (total_indirect * 0.05), 0.7)
        else:
            decision = "NON"
            confidence = 0.9
        
        # Construire le reasoning
        reasoning_parts = [
            f"**Décision: {decision}** (Confiance: {confidence:.2f})",
            "",
            f"**Événement géopolitique:** {document.event_subtype or 'Non spécifié'}",
            f"**Pays concernés:** {', '.join(event_countries) if event_countries else 'Non spécifié'}",
            f"**Régions concernées:** {', '.join(event_regions) if event_regions else 'Non spécifié'}",
            "",
            "**Analyse de correspondance:**"
        ]
        
        if direct_match_sites:
            reasoning_parts.append(f"- **{len(direct_match_sites)} site(s) DIRECTEMENT concerné(s):**")
            for e in direct_match_sites[:5]:
                reasoning_parts.append(f"  • {e['entity_name']} - {e['country']}")
        
        if direct_match_suppliers:
            reasoning_parts.append(f"- **{len(direct_match_suppliers)} fournisseur(s) DIRECTEMENT concerné(s):**")
            for e in direct_match_suppliers[:5]:
                reasoning_parts.append(f"  • {e['entity_name']} - {e['country']}")
        
        if indirect_match_sites:
            reasoning_parts.append(f"- **{len(indirect_match_sites)} site(s) INDIRECTEMENT concerné(s)** (pays voisins):")
            for e in indirect_match_sites[:3]:
                reasoning_parts.append(f"  • {e['entity_name']} - {e['country']}")
        
        if indirect_match_suppliers:
            reasoning_parts.append(f"- **{len(indirect_match_suppliers)} fournisseur(s) INDIRECTEMENT concerné(s)** (pays voisins):")
            for e in indirect_match_suppliers[:3]:
                reasoning_parts.append(f"  • {e['entity_name']} - {e['country']}")
        
        if total_direct == 0 and total_indirect == 0:
            reasoning_parts.append("- Aucun site ou fournisseur dans les pays concernés ou voisins")
        
        reasoning = "\n".join(reasoning_parts)
        
        # Identifier les entités affectées
        affected_sites = [e["entity_id"] for e in direct_match_sites + indirect_match_sites]
        affected_suppliers = [e["entity_id"] for e in direct_match_suppliers + indirect_match_suppliers]
        
        # Matched elements
        matched_elements = {
            "event_countries": event_countries,
            "event_regions": event_regions,
            "direct_match": {
                "sites": direct_match_sites,
                "suppliers": direct_match_suppliers,
                "total": total_direct
            },
            "indirect_match": {
                "sites": indirect_match_sites,
                "suppliers": indirect_match_suppliers,
                "total": total_indirect
            }
        }
        
        return {
            "decision": decision,
            "confidence": round(confidence, 3),
            "reasoning": reasoning,
            "affected_sites": affected_sites,
            "affected_suppliers": affected_suppliers,
            "matched_elements": matched_elements
        }
    
    def _is_neighboring_country(self, country: str, event_countries: List[str]) -> bool:
        """
        Détermine si un pays est voisin d'un des pays de l'événement
        
        Note: Implémentation simplifiée. Pour une version production,
        utiliser une base de données de pays voisins.
        """
        # Mapping simplifié des pays voisins (Europe principalement)
        neighbors = {
            "france": ["spain", "italy", "germany", "belgium", "luxembourg", "switzerland"],
            "germany": ["france", "poland", "czech republic", "austria", "switzerland", "belgium", "netherlands", "denmark"],
            "spain": ["france", "portugal"],
            "italy": ["france", "switzerland", "austria", "slovenia"],
            "poland": ["germany", "czech republic", "slovakia", "ukraine", "belarus", "lithuania"],
            "ukraine": ["poland", "slovakia", "hungary", "romania", "moldova", "belarus", "russia"],
            "china": ["russia", "india", "vietnam", "north korea", "mongolia", "kazakhstan"],
            "india": ["china", "pakistan", "bangladesh", "nepal", "bhutan", "myanmar"],
        }
        
        country_normalized = normalize_country_name(country)
        
        for event_country in event_countries:
            event_country_normalized = normalize_country_name(event_country)
            
            # Vérifier si country est voisin de event_country
            if country_normalized in neighbors.get(event_country_normalized, []):
                return True
            
            # Vérifier l'inverse
            if event_country_normalized in neighbors.get(country_normalized, []):
                return True
        
        return False
    
    # ========================================================================
    # SAUVEGARDE EN BASE DE DONNÉES
    # ========================================================================
    
    def _save_to_database(self, result: Dict, session) -> str:
        """
        Sauvegarde les résultats d'analyse en base de données
        
        Args:
            result: Résultat de l'analyse de pertinence
            session: Session SQLAlchemy
            
        Returns:
            L'ID du PertinenceCheck créé ou mis à jour
        """
        try:
            # Vérifier si une analyse existe déjà pour ce document
            existing = session.query(PertinenceCheck).filter_by(
                document_id=result["document_id"]
            ).first()
            
            if existing:
                # Mettre à jour
                existing.decision = result["decision"]
                existing.confidence = result["confidence"]
                existing.reasoning = result["reasoning"]
                existing.matched_elements = result["matched_elements"]
                existing.affected_sites = result["affected_sites"]
                existing.affected_suppliers = result["affected_suppliers"]
                existing.analysis_metadata = {
                    "event_type": result["event_type"],
                    "analysis_timestamp": result["analysis_timestamp"]
                }
                
                logger.info("pertinence_check_updated", document_id=result["document_id"][:8])
                session.commit()
                result["check_id"] = existing.id  # Ajouter l'ID au résultat
                return existing.id
            else:
                # Créer nouveau
                pertinence_check = PertinenceCheck(
                    document_id=result["document_id"],
                    decision=result["decision"],
                    confidence=result["confidence"],
                    reasoning=result["reasoning"],
                    matched_elements=result["matched_elements"],
                    affected_sites=result["affected_sites"],
                    affected_suppliers=result["affected_suppliers"],
                    llm_model="claude-sonnet-4-20250514",
                    analysis_metadata={
                        "event_type": result["event_type"],
                        "analysis_timestamp": result["analysis_timestamp"]
                    }
                )
                
                session.add(pertinence_check)
                session.commit()
                logger.info("pertinence_check_created", document_id=result["document_id"][:8])
                result["check_id"] = pertinence_check.id  # Ajouter l'ID au résultat
                return pertinence_check.id
            
        except Exception as e:
            session.rollback()
            logger.error("save_to_database_failed", error=str(e))
            raise
    
    # ========================================================================
    # UTILITAIRES
    # ========================================================================
    
    def _load_hutchinson_profile(self) -> Dict:
        """
        Charge le profil Hutchinson depuis le fichier JSON ou la BDD
        
        Returns:
            Dict avec keywords, nc_codes, sectors, products, countries
        """
        # Pour l'instant, retourne un profil par défaut
        # TODO: Charger depuis data/company_profiles/Hutchinson_SA.json
        return {
            "keywords": [
                "caoutchouc", "rubber", "joint", "seal", "étanchéité",
                "automotive", "aerospace", "aluminium", "plastique",
                "CBAM", "EUDR", "CSRD", "carbone", "déforestation"
            ],
            "nc_codes": [
                "4001", "4002", "4016", "7601", "7604", "8708", "8803"
            ],
            "sectors": [
                "Automotive", "Aerospace", "Industry", "Defense"
            ],
            "products": [
                "Joints d'étanchéité", "Tuyaux", "Pièces en caoutchouc",
                "Composants automobiles", "Pièces aéronautiques"
            ],
            "countries": [
                "France", "Germany", "Spain", "Poland", "China", "India", "USA", "Mexico", "Brazil"
            ]
        }


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def run_agent_1b(document_id: str, save_to_db: bool = True) -> Dict:
    """
    Fonction principale pour exécuter l'Agent 1B sur un document
    
    Args:
        document_id: ID du document à analyser
        save_to_db: Si True, sauvegarde les résultats en BDD
        
    Returns:
        Dict avec les résultats de l'analyse
    """
    agent = Agent1B()
    return agent.check_pertinence(document_id, save_to_db=save_to_db)


def run_agent_1b_pipeline(batch_size: int = 100) -> Dict:
    """
    Pipeline automatique : traite tous les documents et weather_alerts non analysés
    
    Args:
        batch_size: Nombre maximum de documents à traiter
        
    Returns:
        Dict avec statistiques de traitement
    """
    from src.storage.models import WeatherAlert
    
    session = get_session()
    agent = Agent1B()
    
    results = {
        "documents_processed": 0,
        "weather_alerts_processed": 0,
        "pertinence_checks_created": 0,
        "errors": []
    }
    
    try:
        # 1. Traiter les documents non encore analysés
        unprocessed_docs = session.query(Document).outerjoin(
            PertinenceCheck,
            Document.id == PertinenceCheck.document_id
        ).filter(
            PertinenceCheck.id.is_(None)
        ).limit(batch_size).all()
        
        logger.info("pipeline_started", unprocessed_documents=len(unprocessed_docs))
        
        for doc in unprocessed_docs:
            try:
                agent.check_pertinence(doc.id, save_to_db=True)
                results["documents_processed"] += 1
                results["pertinence_checks_created"] += 1
            except Exception as e:
                logger.error("document_processing_failed", doc_id=doc.id, error=str(e))
                results["errors"].append({"doc_id": doc.id, "error": str(e)})
        
        # 2. Traiter les weather_alerts non encore converties en documents
        # (Les weather_alerts sont déjà des événements détectés, pas besoin de les analyser)
        # Elles sont utilisées par l'Agent 2 pour la projection géographique
        
        logger.info("pipeline_completed", **results)
        
    finally:
        session.close()
    
    return results


if __name__ == "__main__":
    # Test
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python agent.py <document_id> | python agent.py --pipeline")
        sys.exit(1)
    
    if sys.argv[1] == "--pipeline":
        result = run_agent_1b_pipeline()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        doc_id = sys.argv[1]
        result = run_agent_1b(doc_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))

