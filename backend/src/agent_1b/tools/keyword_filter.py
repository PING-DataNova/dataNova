"""
Filtre Niveau 1 - Analyse par mots-clés

Scanne le document pour trouver les mots-clés du profil entreprise.
"""

import re
import structlog
from typing import List, Dict
from src.agent_1b.models import KeywordAnalysisResult

logger = structlog.get_logger()


class KeywordFilter:
    """Filtre de pertinence basé sur les mots-clés métier"""
    
    def __init__(self, keywords: List[str]):
        """
        Args:
            keywords: Liste des mots-clés du profil entreprise
        """
        self.keywords = [k.lower().strip() for k in keywords]
        self.total_keywords = len(self.keywords)
    
    def analyze(self, document_text: str) -> KeywordAnalysisResult:
        """
        Analyse le document pour trouver les mots-clés
        
        Args:
            document_text: Texte complet du document
            
        Returns:
            KeywordAnalysisResult avec score et détails
        """
        logger.info("keyword_filter_started", total_keywords=self.total_keywords)
        
        document_lower = document_text.lower()
        
        keywords_found = []
        context_snippets = {}
        
        for keyword in self.keywords:
            # Recherche case-insensitive
            if keyword in document_lower:
                keywords_found.append(keyword)
                
                # Extraire le contexte (100 caractères avant/après)
                context = self._extract_context(document_text, keyword)
                context_snippets[keyword] = context
        
        # Calculer le score
        if self.total_keywords == 0:
            keyword_density = 0.0
            score = 0.0
        else:
            keyword_density = len(keywords_found) / self.total_keywords
            
            # Score avec bonus pour diversité
            # Plus on trouve de mots-clés différents, meilleur est le score
            score = min(1.0, keyword_density * 1.5)  # Bonus jusqu'à 50%
        
        logger.info(
            "keyword_filter_completed",
            keywords_found=len(keywords_found),
            density=round(keyword_density, 3),
            score=round(score, 3)
        )
        
        return KeywordAnalysisResult(
            score=score,
            keywords_found=keywords_found,
            total_keywords_searched=self.total_keywords,
            keyword_density=keyword_density,
            context_snippets=context_snippets
        )
    
    def _extract_context(self, text: str, keyword: str, chars_before: int = 100, chars_after: int = 100) -> str:
        """
        Extrait le contexte autour du mot-clé
        
        Args:
            text: Texte complet
            keyword: Mot-clé à chercher
            chars_before: Caractères avant le mot-clé
            chars_after: Caractères après le mot-clé
            
        Returns:
            Contexte autour du mot-clé
        """
        # Recherche case-insensitive
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        match = pattern.search(text)
        
        if not match:
            return ""
        
        start_pos = match.start()
        end_pos = match.end()
        
        # Extraire le contexte
        context_start = max(0, start_pos - chars_before)
        context_end = min(len(text), end_pos + chars_after)
        
        context = text[context_start:context_end].strip()
        
        # Ajouter des ellipses si tronqué
        if context_start > 0:
            context = "..." + context
        if context_end < len(text):
            context = context + "..."
        
        return context


def analyze_keywords(document_text: str, company_keywords: List[str]) -> KeywordAnalysisResult:
    """
    Fonction helper pour analyser les mots-clés
    
    Args:
        document_text: Texte du document à analyser
        company_keywords: Liste des mots-clés du profil entreprise
        
    Returns:
        KeywordAnalysisResult
    """
    filter_tool = KeywordFilter(company_keywords)
    return filter_tool.analyze(document_text)
