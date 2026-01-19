"""
PDF Extractor with PyMuPDF - Agent 1A Tool
Extrait texte et codes NC des PDFs réglementaires EUR-Lex
Utilise PyMuPDF (fitz) - 10-100x plus rapide que Docling
"""

import os
import logging
import tempfile
import re
from pathlib import Path
from typing import List, Dict, Optional

import requests

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("pip install pymupdf")

logger = logging.getLogger(__name__)


class PDFExtractor:
    """
    Extrait contenu structuré des PDFs EUR-Lex avec PyMuPDF (ultra rapide).
    
    Fonctionnalités :
    - Extraction texte complet (très rapide)
    - Détection automatique codes NC (regex)
    - Extraction montants (EUR, %, tonnes)
    """
    
    def __init__(self):
        """Initialiser l'extracteur PDF rapide"""
        logger.info("✅ PyMuPDF PDF Extractor initialized (fast mode)")
    
    def extract_from_url(self, pdf_url: str) -> Dict[str, any]:
        """
        Extrait contenu d'un PDF depuis une URL.
        
        Args:
            pdf_url: URL du PDF EUR-Lex
        
        Returns:
            Dict avec text, tables, nc_codes, metadata
        """
        logger.info(f"📄 Extracting PDF from URL: {pdf_url[:80]}...")
        
        try:
            # Télécharger dans fichier temporaire
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                response = requests.get(pdf_url, timeout=30)
                response.raise_for_status()
                tmp_file.write(response.content)
                tmp_path = tmp_file.name
            
            # Extraire avec Docling
            result = self.extract_from_file(tmp_path)
            
            # Nettoyer fichier temporaire
            os.unlink(tmp_path)
            
            result["source_url"] = pdf_url
            return result
        
        except Exception as e:
            logger.error(f"❌ PDF URL extraction error: {e}")
            return {
                "text": "",
                "tables": [],
                "nc_codes": [],
                "metadata": {},
                "error": str(e)
            }
    
    def extract_from_file(self, pdf_path: str) -> Dict[str, any]:
        """
        Extrait contenu d'un fichier PDF local avec PyMuPDF (rapide).
        
        Args:
            pdf_path: Chemin vers le PDF
        
        Returns:
            Dict avec text, nc_codes, metadata
        """
        logger.info(f"📄 Extracting PDF: {pdf_path}")
        
        try:
            # Ouvrir le PDF avec PyMuPDF
            doc = fitz.open(pdf_path)
            
            # Structure de données
            extracted = {
                "text": "",
                "tables": [],  # Non supporté avec PyMuPDF basique
                "sections": [],
                "metadata": {},
                "nc_codes": [],
                "amounts": []
            }
            
            # Extraire le texte de toutes les pages
            text_parts = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text_parts.append(page.get_text())
            
            extracted["text"] = "\n\n".join(text_parts)
            
            # Métadonnées
            extracted["metadata"] = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "pages": len(doc)
            }
            
            # Fermer le document
            doc.close()
            
            # Extraction spécifique : NC codes
            extracted["nc_codes"] = self._extract_nc_codes(extracted["text"])
            
            # Extraction spécifique : montants (EUR, %)
            extracted["amounts"] = self._extract_amounts(extracted["text"])
            
            logger.info(f"✅ Extracted: {len(extracted['text'])} chars, "
                       f"{len(extracted['nc_codes'])} NC codes from {extracted['metadata']['pages']} pages")
            
            return extracted
        
        except Exception as e:
            logger.error(f"❌ PDF extraction error: {e}")
            return {
                "text": "",
                "tables": [],
                "sections": [],
                "nc_codes": [],
                "amounts": [],
                "metadata": {},
                "error": str(e)
            }
    
    def _extract_table_data(self, table) -> Dict[str, any]:
        """Convertit un objet Table Docling en dict structuré"""
        table_dict = {
            "headers": [],
            "rows": [],
            "row_count": 0,
            "col_count": 0
        }
        
        try:
            if hasattr(table, 'data'):
                data = table.data
                if len(data) > 0:
                    table_dict["headers"] = data[0]
                    table_dict["rows"] = data[1:]
                    table_dict["row_count"] = len(data) - 1
                    table_dict["col_count"] = len(data[0]) if data[0] else 0
        except Exception as e:
            logger.warning(f"⚠️ Table extraction issue: {e}")
        
        return table_dict
    
    def _extract_nc_codes(self, text: str) -> List[str]:
        """
        Extrait les codes NC (Nomenclature Combinée) du texte.
        Pattern : 4 ou 8 chiffres (ex: 7208, 4002.19)
        Exige indicateur CN/NC/TARIC pour réduire faux positifs.
        """
        # Pattern NC amélioré : exiger CN/NC/TARIC autour
        nc_pattern = r'(?:CN|NC|TARIC)[\s:]+code[s]?[\s:]*([\d\.\s,-]+)|(?:CN|NC|TARIC)[\s:]+(\d{4}(?:\.\d{2})?)'
        matches = re.findall(nc_pattern, text, re.IGNORECASE)
        
        # Flatten tuples et nettoyer
        nc_codes = set()
        for match in matches:
            for group in match:
                if group:
                    # Extraire tous les codes numériques
                    codes = re.findall(r'\d{4}(?:\.\d{2})?', group)
                    nc_codes.update(codes)
        
        # Filtrer années/numéros d'articles (éviter 2023, 2024, etc.)
        filtered = [code for code in nc_codes if not (len(code) == 4 and code.startswith('20'))]
        
        return sorted(filtered)
    
    def _extract_amounts(self, text: str) -> List[Dict[str, any]]:
        """
        Extrait les montants (EUR, %, tonnes) du texte.
        Utile pour taux CBAM, seuils financiers.
        """
        amounts = []
        
        # Pattern EUR
        eur_pattern = r'([\d\s,\.]+)\s*(?:EUR|€|euros?)'
        for match in re.finditer(eur_pattern, text, re.IGNORECASE):
            amounts.append({
                "type": "EUR",
                "value": match.group(1).strip(),
                "context": text[max(0, match.start()-50):match.end()+50]
            })
        
        # Pattern %
        percent_pattern = r'(\d+(?:[.,]\d+)?)\s*%'
        for match in re.finditer(percent_pattern, text):
            amounts.append({
                "type": "PERCENT",
                "value": match.group(1),
                "context": text[max(0, match.start()-50):match.end()+50]
            })
        
        return amounts


# ═══════════════════════════════════════════════════════════
# LANGCHAIN TOOL WRAPPER
# ═══════════════════════════════════════════════════════════

from langchain.tools import tool
import json

MAX_TEXT_PREVIEW = 8000  # Limite preview texte pour éviter rate limits

@tool
def extract_pdf_content_tool(file_path: str) -> dict:
    """Extrait PDF. Retourne dict: {text_preview,text_path,nc_codes,metadata,stats}"""
    extractor = PDFExtractor()
    
    # Détecter si c'est une URL ou un fichier local
    if file_path.startswith('http'):
        result = extractor.extract_from_url(file_path)
    else:
        result = extractor.extract_from_file(file_path)
    
    # Sauvegarder texte complet sur disque
    text_path = str(Path(file_path).with_suffix(".txt"))
    Path(text_path).write_text(result["text"], encoding="utf-8")
    
    # Retourner dict optimisé (preview seulement)
    return {
        "text_preview": result["text"][:MAX_TEXT_PREVIEW],
        "text_path": text_path,
        "text_chars": len(result["text"]),
        "nc_codes": result["nc_codes"][:50],  # Limiter NC codes
        "amounts": result["amounts"][:20],    # Limiter montants
        "metadata": result["metadata"],
        "stats": {
            "pages": result["metadata"].get("pages", 0),
            "nc_codes_count": len(result["nc_codes"]),
            "amounts_count": len(result["amounts"])
        }
    }
