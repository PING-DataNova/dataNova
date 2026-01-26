"""
Filtre Niveau 3 - Analyse sémantique avec LLM

Utilise Claude pour une analyse contextuelle approfondie.
"""

import structlog
from typing import List, Dict
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from src.agent_1b.models import SemanticAnalysisResult
from src.config import settings

logger = structlog.get_logger()


# Prompt pour l'analyse sémantique
SEMANTIC_ANALYSIS_PROMPT = PromptTemplate.from_template(
    """Tu es un expert en analyse réglementaire et compliance internationale. 

Ta mission est d'analyser un document réglementaire pour déterminer s'il est pertinent et applicable pour une entreprise spécifique.

# CONTEXTE ENTREPRISE
Nom: {company_name}
Secteur: {industry}
Produits: {products}
Codes NC/SH: {nc_codes}
Pays d'opération: {countries}
Réglementations suivies: {regulations}

# DOCUMENT À ANALYSER
Titre: {document_title}
Type: {regulation_type}
Contenu (extrait):
{document_content}

# TA TÂCHE
1. **Lire et comprendre** le document dans son contexte
2. **Résumer** ce que dit la loi/réglementation en 2-3 phrases claires
3. **Déterminer l'applicabilité**: Est-ce que ce document s'applique à cette entreprise ?
4. **Identifier les impacts**: Si applicable, quels processus/produits sont concernés ?
5. **Détecter les produits**: Même si les codes NC ne sont pas explicites, quels matériaux/produits sont mentionnés ?
6. **Repérer les obligations**: Quelles actions sont requises (déclaration, taxe, interdiction, etc.) ?
7. **Analyser la portée géographique**: Quels pays/régions sont concernés ?

# INSTRUCTIONS SPÉCIFIQUES
- Si le mot "aluminium" ou "caoutchouc" est mentionné mais dans un contexte d'EXCLUSION (ex: "L'aluminium est exclu"), alors l'applicabilité est FAIBLE
- Si les codes NC de l'entreprise sont explicitement listés, l'applicabilité est ÉLEVÉE
- Si le document parle de processus que l'entreprise utilise (ex: "déclaration CBAM", "traçabilité EUDR"), c'est PERTINENT
- Utilise ton jugement pour inférer la pertinence même sans match exact

# FORMAT DE RÉPONSE
{format_instructions}

# CRITÈRES DE SCORE (0-1)
- 0.0-0.2: Non pertinent (ne concerne pas l'entreprise)
- 0.2-0.4: Faible pertinence (mention tangentielle)
- 0.4-0.6: Pertinence moyenne (applicable indirectement)
- 0.6-0.8: Haute pertinence (applicable directement)
- 0.8-1.0: Pertinence critique (impact majeur immédiat)

Procède à l'analyse maintenant.
"""
)


class SemanticAnalyzer:
    """Analyseur sémantique utilisant un LLM"""
    
    def __init__(self, model_name: str = "claude-sonnet-4-5-20250929", temperature: float = 0.1):
        """
        Args:
            model_name: Nom du modèle Anthropic à utiliser
            temperature: Température pour la génération (0-1)
        """
        self.llm = ChatAnthropic(
            model=model_name,
            api_key=settings.anthropic_api_key,
            temperature=temperature,
            max_tokens=2000
        )
        
        # Parser Pydantic pour structurer la sortie
        self.output_parser = PydanticOutputParser(pydantic_object=SemanticAnalysisResult)
        
        # Créer la chaîne LangChain
        self.chain = SEMANTIC_ANALYSIS_PROMPT | self.llm | self.output_parser
    
    def analyze(
        self,
        document_content: str,
        document_title: str,
        regulation_type: str,
        company_profile: Dict
    ) -> SemanticAnalysisResult:
        """
        Analyse sémantique d'un document
        
        Args:
            document_content: Texte du document (peut être tronqué)
            document_title: Titre du document
            regulation_type: Type de réglementation (CBAM, EUDR, etc.)
            company_profile: Dictionnaire du profil entreprise
            
        Returns:
            SemanticAnalysisResult
        """
        logger.info(
            "semantic_analysis_started",
            document_title=document_title[:50],
            regulation_type=regulation_type
        )
        
        # Préparer le contenu (limiter à 8000 tokens ~= 32000 chars)
        content_excerpt = self._prepare_content(document_content, max_chars=32000)
        
        # Extraire les infos du profil
        company_name = company_profile.get("company_name", "Unknown")
        industry = company_profile.get("industry", "")
        products = ", ".join(company_profile.get("products", [])[:5])  # Top 5 produits
        
        # nc_codes peut être un dict ou une liste
        nc_codes_raw = company_profile.get("nc_codes", {})
        if isinstance(nc_codes_raw, dict):
            nc_codes = ", ".join(list(nc_codes_raw.keys())[:20])  # Top 20 codes
        else:
            nc_codes = ", ".join(nc_codes_raw[:20])
        
        countries = company_profile.get("countries", "")
        regulations = ", ".join(company_profile.get("regulations", []))
        
        try:
            # Invoquer la chaîne LangChain
            result = self.chain.invoke({
                "company_name": company_name,
                "industry": industry,
                "products": products,
                "nc_codes": nc_codes,
                "countries": countries,
                "regulations": regulations,
                "document_title": document_title,
                "regulation_type": regulation_type,
                "document_content": content_excerpt,
                "format_instructions": self.output_parser.get_format_instructions()
            })
            
            logger.info(
                "semantic_analysis_completed",
                score=result.score,
                is_applicable=result.is_applicable,
                confidence=result.confidence_level
            )
            
            return result
            
        except Exception as e:
            logger.error("semantic_analysis_failed", error=str(e))
            
            # Retourner un résultat par défaut en cas d'erreur
            return SemanticAnalysisResult(
                score=0.0,
                is_applicable=False,
                explanation="Erreur lors de l'analyse sémantique. Impossible d'obtenir une réponse du LLM.",
                regulation_summary="Document non analysable par le LLM en raison d'une erreur technique.",
                impact_explanation="",
                confidence_level=0.0
            )
    
    def _prepare_content(self, content: str, max_chars: int = 32000) -> str:
        """
        Prépare le contenu pour l'analyse (chunking si nécessaire)
        
        Args:
            content: Contenu complet
            max_chars: Nombre maximum de caractères
            
        Returns:
            Contenu tronqué intelligemment
        """
        if len(content) <= max_chars:
            return content
        
        # Stratégie: Prendre le début (contient souvent le contexte) 
        # et la fin (contient souvent les annexes/tableaux importants)
        first_part_size = int(max_chars * 0.7)
        last_part_size = int(max_chars * 0.3)
        
        first_part = content[:first_part_size]
        last_part = content[-last_part_size:]
        
        excerpt = first_part + "\n\n[...CONTENU TRONQUÉ...]\n\n" + last_part
        
        logger.warning(
            "content_truncated",
            original_length=len(content),
            truncated_length=len(excerpt)
        )
        
        return excerpt


def analyze_semantically(
    document_content: str,
    document_title: str,
    regulation_type: str,
    company_profile: Dict
) -> SemanticAnalysisResult:
    """
    Fonction helper pour l'analyse sémantique
    
    Args:
        document_content: Texte du document
        document_title: Titre du document
        regulation_type: Type de réglementation
        company_profile: Profil entreprise
        
    Returns:
        SemanticAnalysisResult
    """
    analyzer = SemanticAnalyzer()
    return analyzer.analyze(
        document_content,
        document_title,
        regulation_type,
        company_profile
    )
