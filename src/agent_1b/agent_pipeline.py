"""
Agent 1B Pipeline - Version orchestration manuelle (sans ReAct)

Analyse de pertinence et scoring des documents Agent 1A.
Workflow: Keywords → NC Codes → Sémantique → Score Global
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any
from anthropic import Anthropic
from dotenv import load_dotenv
import structlog
import os

# Charger .env
load_dotenv()

logger = structlog.get_logger()


class Agent1BPipeline:
    """Pipeline d'analyse de pertinence Agent 1B"""
    
    def __init__(self, company_profile_path: str = "data/company_profiles/Hutchinson_SA.json"):
        """
        Initialise l'Agent 1B avec le profil entreprise
        
        Args:
            company_profile_path: Chemin vers le profil HUTCHINSON
        """
        logger.info("agent_1b_pipeline_initialized", mode="manual_orchestration")
        
        # Charger profil entreprise
        with open(company_profile_path, 'r', encoding='utf-8') as f:
            self.company_profile = json.load(f)
        
        # Extraire les éléments clés
        self.company_nc_codes = self._extract_nc_codes()
        self.company_keywords = self._extract_keywords()
        self.company_countries = self._extract_countries()
        
        # LLM pour analyse sémantique
        self.llm = None  # Lazy init
        
        logger.info(
            "company_profile_loaded",
            nc_codes=len(self.company_nc_codes),
            keywords=len(self.company_keywords),
            countries=len(self.company_countries)
        )
    
    def _extract_nc_codes(self) -> List[str]:
        """Extrait les codes NC du catalogue produits et supply_chain"""
        nc_codes = []
        
        # Extraire depuis nc_codes si disponible
        if "nc_codes" in self.company_profile:
            nc_data = self.company_profile["nc_codes"]
            # Format: {"imports": [...], "exports": [...]}
            for category in ["imports", "exports"]:
                if category in nc_data:
                    for item in nc_data[category]:
                        if isinstance(item, dict) and "code" in item:
                            nc_codes.append(item["code"])
        
        # Extraire depuis supply_chain si disponible
        if "supply_chain" in self.company_profile:
            supply_chain = self.company_profile["supply_chain"]
            
            # Natural rubber
            if "natural_rubber" in supply_chain:
                for supplier in supply_chain["natural_rubber"].get("suppliers", []):
                    if "nc_code" in supplier:
                        nc_codes.append(supplier["nc_code"])
            
            # Synthetic rubber
            if "synthetic_rubber" in supply_chain:
                for supplier in supply_chain["synthetic_rubber"].get("suppliers", []):
                    if "nc_code" in supplier:
                        nc_codes.append(supplier["nc_code"])
            
            # Metals and additives
            if "metals_and_additives" in supply_chain:
                for material in supply_chain["metals_and_additives"].get("critical_materials", []):
                    if "hs_code" in material:
                        nc_codes.append(material["hs_code"])
        
        # Fallback: codes NC génériques caoutchouc
        if not nc_codes:
            nc_codes = ["4001", "4002", "4016", "3917", "7208", "7601"]
        
        return list(set(nc_codes))  # Unique
    
    def _extract_keywords(self) -> List[str]:
        """Extrait les keywords de surveillance"""
        base_keywords = [
            # CBAM
            "carbon border adjustment", "CBAM", "carbon price",
            "embedded emissions", "indirect emissions",
            
            # Customs
            "customs", "tariff", "duty", "import declaration",
            "origin", "preferential treatment", "AEO",
            
            # Matériaux
            "rubber", "elastomer", "polymer", "synthetic rubber",
            "natural rubber", "latex",
            
            # Codes NC génériques
            "4002", "4016", "3901", "3902",
            
            # Environnement
            "environmental compliance", "sustainable", "green deal",
            "circular economy",
            
            # Supply chain
            "supply chain", "procurement", "sourcing",
            "sanctions", "export control"
        ]
        
        # Ajouter produits du profil (gérer liste de strings ou dicts)
        products = self.company_profile.get("products", [])
        if isinstance(products, list):
            for product in products:
                if isinstance(product, str):
                    # Format simple: liste de strings
                    base_keywords.append(product)
                elif isinstance(product, dict):
                    # Format dict avec name/description
                    base_keywords.append(product.get("name", ""))
                    base_keywords.append(product.get("description", ""))
        
        return [k.lower() for k in base_keywords if k]
    
    def _extract_countries(self) -> List[str]:
        """Extrait les pays des fournisseurs"""
        countries = []
        
        # Extraire depuis supply_chain
        if "supply_chain" in self.company_profile:
            supply_chain = self.company_profile["supply_chain"]
            
            # Natural rubber suppliers
            if "natural_rubber" in supply_chain:
                for supplier in supply_chain["natural_rubber"].get("suppliers", []):
                    if "country" in supplier:
                        countries.append(supplier["country"])
            
            # Synthetic rubber suppliers
            if "synthetic_rubber" in supply_chain:
                for supplier in supply_chain["synthetic_rubber"].get("suppliers", []):
                    if "country" in supplier:
                        countries.append(supplier["country"])
        
        # Extraire depuis sites (production locations)
        if "sites" in self.company_profile:
            for site in self.company_profile["sites"]:
                if "country" in site:
                    countries.append(site["country"])
        
        # Fallback
        if not countries:
            countries = ["FR", "DE", "US", "CN", "TH"]
        
        return list(set(countries))
    
    def _get_llm(self):
        """Lazy init du LLM Claude"""
        if self.llm is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            self.llm = Anthropic(api_key=api_key)
            logger.info("llm_initialized", model="claude-3-haiku")
        return self.llm
    
    async def analyze_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse un document Agent 1A
        
        Args:
            document: Document enrichi de Agent 1A
        
        Returns:
            dict: Document + analyse (scores, criticité, raison)
        """
        doc_title = document.get('title', 'N/A')[:60]
        logger.info("analyzing_document", title=doc_title)
        
        # Charger le texte complet
        text_path = document.get('text_path')
        if not text_path or not Path(text_path).exists():
            logger.warning("text_file_not_found", text_path=text_path)
            return {**document, "analysis": {"error": "No text file"}}
        
        with open(text_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
        
        # NIVEAU 1 : Keywords
        keyword_result = self._filter_keywords(full_text)
        logger.info(
            "level_1_keywords",
            score=keyword_result['score'],
            matched=len(keyword_result['matched'])
        )
        
        # NIVEAU 2 : NC Codes
        nc_result = self._verify_nc_codes(full_text, document.get('nc_codes', []))
        logger.info(
            "level_2_nc_codes",
            score=nc_result['score'],
            found=len(nc_result['found'])
        )
        
        # NIVEAU 3 : Analyse sémantique LLM
        semantic_result = await self._semantic_analysis(
            full_text[:15000],  # Limiter à 15k chars
            doc_title,
            keyword_result['matched'],
            nc_result['found']
        )
        logger.info(
            "level_3_semantic",
            score=semantic_result['score'],
            reasoning_length=len(semantic_result.get('reasoning', ''))
        )
        
        # SCORE GLOBAL PONDÉRÉ
        final_score, criticality = self._calculate_final_score(
            keyword_result['score'],
            nc_result['score'],
            semantic_result['score']
        )
        
        logger.info(
            "analysis_completed",
            final_score=final_score,
            criticality=criticality
        )
        
        # Enrichir le document
        return {
            **document,
            "analysis": {
                "final_score": final_score,
                "criticality": criticality,
                "level_1_keywords": keyword_result,
                "level_2_nc_codes": nc_result,
                "level_3_semantic": semantic_result,
                "is_relevant": final_score >= 0.5  # Seuil de pertinence
            }
        }
    
    def _filter_keywords(self, text: str) -> Dict[str, Any]:
        """
        Niveau 1 : Filtrage par mots-clés
        
        Returns:
            dict: {score: float, matched: list, total_keywords: int}
        """
        text_lower = text.lower()
        matched_keywords = []
        
        for keyword in self.company_keywords:
            if keyword and keyword in text_lower:
                matched_keywords.append(keyword)
        
        # Score = ratio mots-clés trouvés
        score = len(matched_keywords) / max(len(self.company_keywords), 1)
        
        return {
            "score": min(score, 1.0),  # Cap à 1.0
            "matched": matched_keywords[:20],  # Top 20
            "total_keywords": len(self.company_keywords)
        }
    
    def _verify_nc_codes(self, text: str, extracted_nc_codes: List[str]) -> Dict[str, Any]:
        """
        Niveau 2 : Vérification codes NC
        
        Args:
            text: Texte du document
            extracted_nc_codes: Codes NC extraits par Agent 1A
        
        Returns:
            dict: {score: float, found: list, company_codes: list}
        """
        # Intersection codes Agent 1A et codes entreprise
        doc_codes_set = set(extracted_nc_codes)
        company_codes_set = set(self.company_nc_codes)
        
        # Chercher aussi dans le texte directement
        nc_pattern = r'\b(?:NC|CN|TARIC)\s*[:\-]?\s*(\d{4}(?:\.\d{2})?(?:\.\d{2})?)'
        found_in_text = re.findall(nc_pattern, text, re.IGNORECASE)
        
        all_found = doc_codes_set.union(set(found_in_text))
        matched_codes = all_found.intersection(company_codes_set)
        
        # Score basé sur le nombre de codes matchés
        if len(company_codes_set) > 0:
            score = len(matched_codes) / len(company_codes_set)
        else:
            score = 0.0
        
        return {
            "score": min(score, 1.0),
            "found": list(matched_codes),
            "company_codes": list(company_codes_set)[:10]
        }
    
    async def _semantic_analysis(
        self,
        text: str,
        title: str,
        matched_keywords: List[str],
        matched_nc_codes: List[str]
    ) -> Dict[str, Any]:
        """
        Niveau 3 : Analyse sémantique par LLM
        
        Returns:
            dict: {score: float, reasoning: str, impacts: list}
        """
        llm = self._get_llm()
        
        # Construire le contexte
        context = f"""Entreprise : HUTCHINSON
Secteur : Automobile (joints, durites caoutchouc)
Matériaux : {', '.join(self.company_profile.get('products', [])[:3])}
Pays fournisseurs : {', '.join(self.company_countries[:5])}
Codes NC : {', '.join(self.company_nc_codes[:5])}
"""
        
        prompt = f"""Analyse ce document réglementaire pour déterminer sa pertinence pour l'entreprise.

{context}

DOCUMENT:
Titre: {title}
Keywords trouvés: {', '.join(matched_keywords[:10])}
Codes NC matchés: {', '.join(matched_nc_codes)}

Extrait:
{text[:5000]}

TÂCHE:
1. Score de pertinence (0.0 à 1.0) - 1.0 = très pertinent, 0.0 = pas pertinent
2. Raison en 2-3 phrases expliquant pourquoi
3. Impacts potentiels pour l'entreprise (liste de 1-3 items)

IMPORTANT: Réponds UNIQUEMENT avec du JSON valide, sans texte avant ou après.
Format JSON attendu:
{{
  "score": 0.8,
  "reasoning": "Ce règlement concerne...",
  "impacts": ["Impact 1", "Impact 2"]
}}
"""
        
        try:
            response = llm.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=500,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Extraire le JSON de la réponse (même si texte autour)
            content = response.content[0].text
            
            # Chercher le JSON dans la réponse
            # Claude peut retourner: "Voici l'analyse: {json}" ou juste "{json}"
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
            else:
                # Fallback: essayer de parser directement
                result = json.loads(content)
            
            return {
                "score": float(result.get("score", 0.0)),
                "reasoning": result.get("reasoning", ""),
                "impacts": result.get("impacts", [])
            }
        
        except Exception as e:
            logger.error("semantic_analysis_failed", error=str(e), content_preview=content[:200] if 'content' in locals() else 'N/A')
            return {
                "score": 0.0,
                "reasoning": f"Erreur parsing: {str(e)}",
                "impacts": []
            }
    
    def _calculate_final_score(
        self,
        keyword_score: float,
        nc_code_score: float,
        semantic_score: float
    ) -> tuple:
        """
        Calcule le score final pondéré et la criticité
        
        Pondération:
        - Keywords: 25%
        - NC Codes: 25%
        - Sémantique: 50%
        
        Returns:
            tuple: (final_score, criticality)
        """
        final_score = (
            0.25 * keyword_score +
            0.25 * nc_code_score +
            0.5 * semantic_score
        )
        
        # Criticité
        if final_score >= 0.8:
            criticality = "CRITICAL"
        elif final_score >= 0.6:
            criticality = "HIGH"
        elif final_score >= 0.4:
            criticality = "MEDIUM"
        else:
            criticality = "LOW"
        
        return round(final_score, 3), criticality
    
    async def run(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Exécute le pipeline sur une liste de documents
        
        Args:
            documents: Liste de documents Agent 1A
        
        Returns:
            dict: {
                "status": "success",
                "analyzed_documents": [...],
                "stats": {...}
            }
        """
        logger.info("pipeline_started", total_documents=len(documents))
        
        analyzed_docs = []
        errors = 0
        
        for idx, doc in enumerate(documents, 1):
            try:
                analyzed = await self.analyze_document(doc)
                analyzed_docs.append(analyzed)
            except Exception as e:
                logger.error("document_analysis_failed", index=idx, error=str(e))
                errors += 1
        
        # Stats
        relevant_docs = [d for d in analyzed_docs if d.get('analysis', {}).get('is_relevant', False)]
        critical_docs = [d for d in analyzed_docs if d.get('analysis', {}).get('criticality') == 'CRITICAL']
        
        stats = {
            "total": len(documents),
            "analyzed": len(analyzed_docs),
            "errors": errors,
            "relevant": len(relevant_docs),
            "critical": len(critical_docs)
        }
        
        logger.info("pipeline_completed", **stats)
        
        return {
            "status": "success",
            "analyzed_documents": analyzed_docs,
            "stats": stats
        }


# ═══════════════════════════════════════════════════════════
# API PUBLIQUE
# ═══════════════════════════════════════════════════════════

async def run_agent_1b_pipeline(
    documents: List[Dict[str, Any]],
    company_profile_path: str = "data/company_profiles/Hutchinson_SA.json"
) -> Dict[str, Any]:
    """
    Exécute Agent 1B sur des documents Agent 1A
    
    Args:
        documents: Liste de documents enrichis par Agent 1A
        company_profile_path: Chemin vers profil entreprise
    
    Returns:
        dict: {"status": "success", "analyzed_documents": [...], "stats": {...}}
    """
    pipeline = Agent1BPipeline(company_profile_path)
    return await pipeline.run(documents)
