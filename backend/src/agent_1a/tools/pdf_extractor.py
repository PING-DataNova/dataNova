"""
TODO: Outil d'extraction de contenu PDF (LangChain @tool)

Tâches:
1. Décorer avec @tool
2. Extraire texte avec pdfplumber
3. Extraire tableaux (codes NC)
4. Identifier les annexes
5. Détecter les codes NC avec regex

Regex codes NC:
- Format: 4 à 10 chiffres
- Exemples: 4002.19, 7606, 8537
"""
"""
PDF Extractor - Extraction de contenu et codes NC depuis PDFs

Responsable: Dev 1 (ou Dev 2)
"""
from langchain.tools import tool
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

import pdfplumber
import structlog
from pydantic import BaseModel

logger = structlog.get_logger()


class NCCode(BaseModel):
    """Modèle pour un code NC (Nomenclature Combinée) détecté"""
    code: str
    context: str
    page: int
    confidence: float = 1.0


class ExtractedContent(BaseModel):
    """Modèle pour le contenu extrait d'un PDF"""
    file_path: str
    text: str
    nc_codes: List[NCCode]
    tables: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    page_count: int
    status: str
    error: Optional[str] = None


async def extract_pdf_content(
    file_path: str,
    extract_tables: bool = True,
    extract_nc_codes: bool = True
) -> ExtractedContent:
    """
    Extrait le contenu d'un fichier PDF.
    
    Args:
        file_path: Chemin vers le fichier PDF
        extract_tables: Extraire les tableaux
        extract_nc_codes: Détecter les codes NC
    
    Returns:
        ExtractedContent: Contenu extrait avec métadonnées
    """
    logger.info("pdf_extraction_started", file_path=file_path)
    
    try:
        path = Path(file_path)
        
        if not path.exists():
            return ExtractedContent(
                file_path=file_path,
                text="",
                nc_codes=[],
                tables=[],
                metadata={},
                page_count=0,
                status="error",
                error=f"File not found: {file_path}"
            )
        
        text_content = []
        tables = []
        nc_codes = []
        page_count = 0
        
        # Ouvrir le PDF avec pdfplumber
        with pdfplumber.open(path) as pdf:
            page_count = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages, start=1):
                # Extraire le texte
                page_text = page.extract_text()
                
                if page_text:
                    text_content.append(f"\n--- Page {page_num} ---\n")
                    text_content.append(page_text)
                    
                    # Détecter les codes NC dans le texte de cette page
                    if extract_nc_codes:
                        page_nc_codes = _extract_nc_codes(page_text, page_num)
                        nc_codes.extend(page_nc_codes)
                
                # Extraire les tableaux
                if extract_tables:
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table_idx, table in enumerate(page_tables):
                            tables.append({
                                "page": page_num,
                                "table_index": table_idx,
                                "rows": len(table),
                                "columns": len(table[0]) if table else 0,
                                "data": table
                            })
        
        # Joindre tout le texte
        full_text = "".join(text_content)
        
        # Métadonnées du PDF
        metadata = {
            "filename": path.name,
            "file_size": path.stat().st_size,
            "extension": path.suffix,
            "page_count": page_count,
            "tables_found": len(tables),
            "nc_codes_found": len(nc_codes)
        }
        
        logger.info(
            "pdf_extraction_completed",
            file_path=file_path,
            pages=page_count,
            text_length=len(full_text),
            nc_codes=len(nc_codes),
            tables=len(tables)
        )
        
        return ExtractedContent(
            file_path=file_path,
            text=full_text,
            nc_codes=nc_codes,
            tables=tables,
            metadata=metadata,
            page_count=page_count,
            status="success"
        )
        
    except Exception as e:
        logger.error("pdf_extraction_error", file_path=file_path, error=str(e), exc_info=True)
        return ExtractedContent(
            file_path=file_path,
            text="",
            nc_codes=[],
            tables=[],
            metadata={},
            page_count=0,
            status="error",
            error=f"Extraction error: {str(e)}"
        )


def _extract_nc_codes(text: str, page_num: int) -> List[NCCode]:
    """
    Extrait les codes NC (Nomenclature Combinée) depuis un texte.
    
    Format des codes NC :
    - 4 chiffres minimum (ex: 7606)
    - Jusqu'à 10 chiffres (ex: 7606.12.92.10)
    - Souvent avec points (ex: 4002.19)
    - Parfois avec espaces (ex: 8537 10 99)
    
    Args:
        text: Texte à analyser
        page_num: Numéro de page
    
    Returns:
        List[NCCode]: Liste des codes NC détectés
    """
    nc_codes = []
    
    # Patterns de codes NC (du plus spécifique au plus général)
    patterns = [
        # Format: 1234.56.78.90 (10 chiffres avec points)
        r'\b(\d{4}\.\d{2}\.\d{2}\.\d{2})\b',
        # Format: 1234.56.78 (8 chiffres avec points)
        r'\b(\d{4}\.\d{2}\.\d{2})\b',
        # Format: 1234.56 (6 chiffres avec points)
        r'\b(\d{4}\.\d{2})\b',
        # Format: 1234 56 78 (8 chiffres avec espaces)
        r'\b(\d{4}\s+\d{2}\s+\d{2})\b',
        # Format: 1234 56 (6 chiffres avec espaces)
        r'\b(\d{4}\s+\d{2})\b',
        # Format: 12345678 (8 chiffres sans séparateur)
        r'\b(\d{8})\b',
        # Format: 123456 (6 chiffres sans séparateur)
        r'\b(\d{6})\b',
        # Format: 1234 (4 chiffres)
        r'\b(\d{4})\b',
    ]
    
    seen_codes = set()
    
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        
        for match in matches:
            code = match.group(1)
            
            # Normaliser le code (retirer espaces, garder points)
            normalized_code = code.replace(' ', '')
            
            # Éviter les doublons
            if normalized_code in seen_codes:
                continue
            
            # Filtrer les faux positifs
            if not _is_valid_nc_code(normalized_code, text, match.start()):
                continue
            
            seen_codes.add(normalized_code)
            
            # Extraire le contexte autour du code (50 caractères avant/après)
            context_start = max(0, match.start() - 50)
            context_end = min(len(text), match.end() + 50)
            context = text[context_start:context_end].replace('\n', ' ').strip()
            
            nc_codes.append(NCCode(
                code=normalized_code,
                context=context,
                page=page_num,
                confidence=_calculate_nc_confidence(normalized_code, context)
            ))
    
    return nc_codes


# def _is_valid_nc_code(code: str, text: str, position: int) -> bool:
#     """
#     Vérifie si un code NC est valide (pas un faux positif).
    
#     Args:
#         code: Code NC à vérifier
#         text: Texte complet
#         position: Position du code dans le texte
    
#     Returns:
#         bool: True si le code semble valide
#     """
#     # Codes trop courts (moins de 4 chiffres) = peu fiables
#     clean_code = code.replace('.', '')
#     if len(clean_code) < 4:
#         return False
    
#     # Vérifier le contexte autour du code
#     context_start = max(0, position - 100)
#     context_end = min(len(text), position + 100)
#     context = text[context_start:context_end].lower()
    
#     # Mots-clés indiquant un code NC
#     nc_keywords = [
#         'nc code', 'code nc', 'cn code', 'nomenclature',
#         'tariff', 'heading', 'subheading', 'chapter',
#         'hs code', 'customs', 'taric'
#     ]
    
#     # Si le contexte contient des mots-clés NC, c'est probablement valide
#     if any(keyword in context for keyword in nc_keywords):
#         return True
    
#     # Éviter les années (ex: 2023, 2024)
#     if code in ['2020', '2021', '2022', '2023', '2024', '2025', '2026', '2027', '2028', '2029', '2030']:
#         return False
    
#     # Éviter les numéros de page/article
#     if 'page' in context or 'article' in context:
#         return False
    
#     # Si le code a au moins 6 chiffres, le garder (probablement un vrai code NC)
#     if len(clean_code) >= 6:
#         return True
    
#     # Sinon, rejeter les codes courts sans contexte NC
#     return False
def _is_valid_nc_code(code: str, text: str, position: int) -> bool:
    """
    Vérifie si un code NC est valide (pas un faux positif).
    
    Args:
        code: Code NC à vérifier
        text: Texte complet
        position: Position du code dans le texte
    
    Returns:
        bool: True si le code semble valide
    """
    # Codes trop courts (moins de 4 chiffres) = peu fiables
    clean_code = code.replace('.', '')
    if len(clean_code) < 4:
        return False
    
    # ✅ NOUVEAU : Éviter TOUTES les années (1900-2100)
    if code.isdigit() and 1900 <= int(code) <= 2100:
        return False
    
    # Vérifier le contexte autour du code (élargi à 200 caractères)
    context_start = max(0, position - 200)
    context_end = min(len(text), position + 200)
    context = text[context_start:context_end].lower()
    
    # Mots-clés indiquant un code NC (liste étendue)
    nc_keywords = [
        'nc code', 'code nc', 'cn code', 'nomenclature', 'combined nomenclature',
        'tariff', 'heading', 'subheading', 'chapter',
        'hs code', 'customs', 'taric',
        'goods', 'products falling under', 'classified under',
        'annex i', 'annex ii', 'listed in annex'
    ]
    
    # Si le contexte contient des mots-clés NC, c'est probablement valide
    if any(keyword in context for keyword in nc_keywords):
        return True
    
    # ✅ NOUVEAU : Rejeter si contexte contient des mots de faux positifs
    false_positive_keywords = [
        'regulation (eu)', 'regulation (eec)', 'directive',
        'article', 'paragraph', 'dated', 'year',
        'published', 'official journal', 'oj l'
    ]
    
    if any(keyword in context for keyword in false_positive_keywords):
        return False
    
    # Éviter les numéros de page/article
    if 'page' in context or ('article' in context and 'article' not in nc_keywords):
        return False
    
    # ✅ NOUVEAU : Codes avec points ou espaces = plus fiables (format NC typique)
    if '.' in code or ' ' in code:
        if len(clean_code) >= 4:
            return True
    
    # Si le code a au moins 8 chiffres sans contexte clair, le garder
    if len(clean_code) >= 8:
        return True
    
    # Rejeter les codes courts (4-6 chiffres) sans contexte NC
    return False


def _calculate_nc_confidence(code: str, context: str) -> float:
    """
    Calcule un score de confiance pour un code NC détecté.
    
    Args:
        code: Code NC
        context: Contexte du code
    
    Returns:
        float: Score de confiance (0.0 à 1.0)
    """
    confidence = 0.5  # Base
    
    # Plus le code est long, plus c'est fiable
    clean_code = code.replace('.', '')
    if len(clean_code) >= 8:
        confidence += 0.3
    elif len(clean_code) >= 6:
        confidence += 0.2
    elif len(clean_code) >= 4:
        confidence += 0.1
    
    # Mots-clés NC dans le contexte = plus fiable
    nc_keywords = ['nc code', 'code nc', 'nomenclature', 'tariff', 'heading']
    context_lower = context.lower()
    
    keyword_count = sum(1 for kw in nc_keywords if kw in context_lower)
    confidence += min(0.2, keyword_count * 0.1)
    
    return min(1.0, confidence)


def extract_pdf_content_sync(
    file_path: str,
    extract_tables: bool = True,
    extract_nc_codes: bool = True
) -> ExtractedContent:
    """Version synchrone de l'extracteur (pour compatibilité)."""
    import asyncio
    return asyncio.run(extract_pdf_content(file_path, extract_tables, extract_nc_codes))


# Pour tester le module directement
if __name__ == "__main__":
    import asyncio
    
    # Chemin vers le PDF téléchargé précédemment
    test_pdf = "data/documents/document_332f671132b3.pdf"
    
    # Extraire le contenu
    result = asyncio.run(extract_pdf_content(test_pdf))
    
    if result.status == "success":
        print(f"\n✅ Extraction réussie !")
        print(f"Fichier: {result.file_path}")
        print(f"Pages: {result.page_count}")
        print(f"Texte: {len(result.text)} caractères")
        print(f"Tableaux: {len(result.tables)}")
        print(f"Codes NC détectés: {len(result.nc_codes)}")
        
        if result.nc_codes:
            print("\n📋 Premiers codes NC:")
            for i, nc in enumerate(result.nc_codes[:5], 1):
                print(f"  {i}. {nc.code} (page {nc.page}, confiance: {nc.confidence:.2f})")
                print(f"     Contexte: ...{nc.context[:80]}...")
        
        if result.tables:
            print(f"\n📊 Premier tableau:")
            table = result.tables[0]
            print(f"   Page {table['page']}, {table['rows']} lignes × {table['columns']} colonnes")
    else:
        print(f"\n❌ Erreur: {result.error}")

@tool
async def extract_pdf_content_tool(file_path: str) -> str:
    """
    Extrait le contenu d'un PDF : texte, tableaux, et codes NC (Nomenclature Combinée).
    
    Args:
        file_path: Chemin vers le fichier PDF
    
    Returns:
        JSON string avec le texte extrait, les tableaux et les codes NC détectés
    """
    result = await extract_pdf_content(file_path)
    return json.dumps({
        "status": result.status,
        "file_path": result.file_path,
        "page_count": result.page_count,
        "text_preview": result.text[:500] + "..." if len(result.text) > 500 else result.text,
        "total_characters": len(result.text),
        "table_count": len(result.tables),
        "nc_codes_count": len(result.nc_codes),
        "nc_codes": [
            {
                "code": nc.code,
                "context": nc.context[:100] + "..." if len(nc.context) > 100 else nc.context,
                "confidence": nc.confidence
            }
            for nc in result.nc_codes[:10]  # Limiter à 10 codes
        ],
        "error": result.error
    }, ensure_ascii=False, indent=2)