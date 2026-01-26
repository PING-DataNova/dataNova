"""
Filtre Niveau 2 - Analyse par codes NC/SH

Détecte les codes NC (nomenclature combinée) dans le document.
"""

import re
import structlog
from typing import List, Dict, Set
from src.agent_1b.models import NCCodeAnalysisResult

logger = structlog.get_logger()


class NCCodeFilter:
    """Filtre de pertinence basé sur les codes NC/SH douaniers"""
    
    # Pattern pour détecter les codes NC (4 à 10 chiffres avec points possibles)
    NC_CODE_PATTERN = re.compile(r'\b(\d{4}(?:\.\d{2})?(?:\.\d{2})?)\b')
    
    def __init__(self, company_nc_codes: List[str], critical_codes: List[str] = None):
        """
        Args:
            company_nc_codes: Codes NC du profil entreprise
            critical_codes: Codes considérés comme critiques (optionnel)
        """
        self.company_nc_codes = [self._normalize_code(code) for code in company_nc_codes]
        self.critical_codes = [self._normalize_code(code) for code in (critical_codes or [])]
        
    def analyze(self, document_text: str) -> NCCodeAnalysisResult:
        """
        Analyse le document pour trouver les codes NC
        
        Args:
            document_text: Texte complet du document
            
        Returns:
            NCCodeAnalysisResult avec score et détails
        """
        logger.info("nc_code_filter_started", company_codes=len(self.company_nc_codes))
        
        # Extraire tous les codes NC du document
        document_codes = self._extract_nc_codes(document_text)
        
        logger.debug("nc_codes_extracted", count=len(document_codes))
        
        # Comparer avec les codes de l'entreprise
        exact_matches = []
        partial_matches = []
        critical_codes_found = []
        context_snippets = {}
        
        for doc_code in document_codes:
            is_match = False
            
            # Vérifier correspondance exacte
            if doc_code in self.company_nc_codes:
                exact_matches.append(doc_code)
                is_match = True
            else:
                # Vérifier correspondance partielle (ex: 4001 vs 4001.22)
                for company_code in self.company_nc_codes:
                    if self._is_partial_match(doc_code, company_code):
                        partial_matches.append(doc_code)
                        is_match = True
                        break
            
            # Vérifier si code critique
            if doc_code in self.critical_codes or any(
                self._is_partial_match(doc_code, crit) for crit in self.critical_codes
            ):
                critical_codes_found.append(doc_code)
            
            # Extraire contexte pour les codes matchés
            if is_match:
                context = self._extract_context(document_text, doc_code)
                context_snippets[doc_code] = context
        
        # Calculer le score
        nc_codes_found = list(set(exact_matches + partial_matches))
        score = self._calculate_score(exact_matches, partial_matches, critical_codes_found)
        
        logger.info(
            "nc_code_filter_completed",
            exact_matches=len(exact_matches),
            partial_matches=len(partial_matches),
            critical_codes=len(critical_codes_found),
            score=round(score, 3)
        )
        
        return NCCodeAnalysisResult(
            score=score,
            nc_codes_found=nc_codes_found,
            exact_matches=exact_matches,
            partial_matches=partial_matches,
            critical_codes=critical_codes_found,
            context_snippets=context_snippets
        )
    
    def _extract_nc_codes(self, text: str) -> List[str]:
        """Extrait tous les codes NC du texte"""
        matches = self.NC_CODE_PATTERN.findall(text)
        # Normaliser et dédupliquer
        codes = list(set(self._normalize_code(code) for code in matches))
        return codes
    
    def _normalize_code(self, code: str) -> str:
        """Normalise un code NC (enlever espaces, formater)"""
        return code.strip().replace(' ', '')
    
    def _is_partial_match(self, code1: str, code2: str) -> bool:
        """
        Vérifie si deux codes correspondent partiellement
        Ex: 4001 vs 4001.22 -> True
        """
        # Le plus court code doit être le préfixe du plus long
        shorter = min(code1, code2, key=len)
        longer = max(code1, code2, key=len)
        
        # Enlever les points pour comparaison
        shorter_clean = shorter.replace('.', '')
        longer_clean = longer.replace('.', '')
        
        return longer_clean.startswith(shorter_clean)
    
    def _calculate_score(self, exact_matches: List[str], partial_matches: List[str], critical_codes: List[str]) -> float:
        """
        Calcule le score basé sur les correspondances
        
        Logique:
        - Exact match: 1.0 point
        - Partial match: 0.5 point
        - Critical code: +0.3 bonus
        """
        if len(self.company_nc_codes) == 0:
            return 0.0
        
        score = 0.0
        
        # Points pour exact matches
        score += len(exact_matches) * 1.0
        
        # Points pour partial matches
        score += len(partial_matches) * 0.5
        
        # Bonus pour codes critiques
        score += len(critical_codes) * 0.3
        
        # Normaliser par rapport au nombre de codes de l'entreprise
        max_possible_score = len(self.company_nc_codes) * 1.3  # 1.0 + bonus critique
        normalized_score = min(1.0, score / max_possible_score)
        
        return normalized_score
    
    def _extract_context(self, text: str, code: str, chars_before: int = 150, chars_after: int = 150) -> str:
        """Extrait le contexte autour d'un code NC"""
        # Chercher le code avec le pattern
        pattern = re.compile(re.escape(code))
        match = pattern.search(text)
        
        if not match:
            return ""
        
        start_pos = match.start()
        end_pos = match.end()
        
        context_start = max(0, start_pos - chars_before)
        context_end = min(len(text), end_pos + chars_after)
        
        context = text[context_start:context_end].strip()
        
        if context_start > 0:
            context = "..." + context
        if context_end < len(text):
            context = context + "..."
        
        return context


def analyze_nc_codes(
    document_text: str,
    company_nc_codes: List[str],
    critical_codes: List[str] = None
) -> NCCodeAnalysisResult:
    """
    Fonction helper pour analyser les codes NC
    
    Args:
        document_text: Texte du document
        company_nc_codes: Codes NC du profil entreprise
        critical_codes: Codes critiques (optionnel)
        
    Returns:
        NCCodeAnalysisResult
    """
    filter_tool = NCCodeFilter(company_nc_codes, critical_codes)
    return filter_tool.analyze(document_text)
