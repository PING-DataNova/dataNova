"""
PDF Extractor with Docling - Agent 1A Tool
Extrait texte, tableaux et codes NC des PDFs réglementaires EUR-Lex
Utilise Docling au lieu de pdfplumber (meilleur pour tableaux et structure)
"""

import os
import logging
import tempfile
import re
from pathlib import Path
from typing import List, Dict, Optional

import requests

try:
    from docling.document_converter import DocumentConverter
except ImportError:
    raise ImportError("pip install docling")

logger = logging.getLogger(__name__)


class PDFExtractor:
    """
    Extrait contenu structuré des PDFs EUR-Lex avec Docling.
    
    Fonctionnalités :
    - Extraction texte complet avec structure (sections, chapitres)
    - Extraction tableaux (taux CBAM, listes NC codes)
    - Détection automatique codes NC (regex)
    - Extraction montants (EUR, %, tonnes)
    """
    
    def __init__(self):
        """Initialiser le converter Docling"""
        self.converter = DocumentConverter()
        logger.info("✅ Docling PDF Extractor initialized")
    
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
        Extrait contenu d'un fichier PDF local.
        
        Args:
            pdf_path: Chemin vers le PDF
        
        Returns:
            Dict avec text, tables, nc_codes, sections, metadata
        """
        logger.info(f"📄 Extracting PDF: {pdf_path}")
        
        try:
            # Convertir le PDF avec Docling
            result = self.converter.convert(pdf_path)
            
            # Structure de données
            extracted = {
                "text": "",
                "tables": [],
                "sections": [],
                "metadata": {},
                "nc_codes": [],
                "amounts": []
            }
            
            # Extraire le contenu
            if hasattr(result, 'document'):
                doc = result.document
                
                # Texte complet en Markdown
                extracted["text"] = doc.export_to_markdown()
                
                # Métadonnées
                if hasattr(doc, 'metadata'):
                    extracted["metadata"] = {
                        "title": getattr(doc.metadata, 'title', ''),
                        "author": getattr(doc.metadata, 'author', ''),
                        "pages": getattr(doc.metadata, 'num_pages', 0)
                    }
                
                # Tableaux structurés
                if hasattr(doc, 'tables'):
                    for table in doc.tables:
                        table_data = self._extract_table_data(table)
                        extracted["tables"].append(table_data)
                
                # Sections (Chapitres, Articles)
                if hasattr(doc, 'sections'):
                    for section in doc.sections:
                        extracted["sections"].append({
                            "title": getattr(section, 'title', ''),
                            "level": getattr(section, 'level', 0),
                            "text": getattr(section, 'text', '')
                        })
            
            # Extraction spécifique : NC codes
            extracted["nc_codes"] = self._extract_nc_codes(extracted["text"])
            
            # Extraction spécifique : montants (EUR, %)
            extracted["amounts"] = self._extract_amounts(extracted["text"])
            
            logger.info(f"✅ Extracted: {len(extracted['text'])} chars, "
                       f"{len(extracted['tables'])} tables, "
                       f"{len(extracted['nc_codes'])} NC codes")
            
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
        """
        # Pattern NC : 4 chiffres, parfois avec point et 2 chiffres (4002.19)
        nc_pattern = r'\b(?:NC[:\s]+)?(\d{4}(?:\.\d{2})?)\b'
        matches = re.findall(nc_pattern, text, re.IGNORECASE)
        
        # Dédupliquer et filtrer
        nc_codes = list(set(matches))
        
        return sorted(nc_codes)
    
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
