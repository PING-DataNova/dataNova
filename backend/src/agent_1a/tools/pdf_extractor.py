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
from datetime import datetime

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


class DocumentInfo(BaseModel):
    """Informations extraites d'un document EUR-Lex"""
    document_number: Optional[str] = None       # Ex: "2024/3210"
    celex_number: Optional[str] = None          # Ex: "32024R3210"
    document_type: Optional[str] = None         # REGULATION, DIRECTIVE, DECISION
    document_subtype: Optional[str] = None      # IMPLEMENTING, DELEGATED, None
    issuing_body: Optional[str] = None          # COMMISSION, PARLIAMENT_COUNCIL
    publication_date: Optional[datetime] = None # Date de publication JO
    publication_series: Optional[str] = None    # L (Legislation) ou C (Communications)
    full_title: Optional[str] = None            # Titre complet du document


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
    publication_date: Optional[datetime] = None  # Date de publication au Journal Officiel
    document_title: Optional[str] = None  # Titre du document (ex: "REGULATION (EU) 2024/3210")
    document_number: Optional[str] = None  # Numéro du document (ex: "2024/3210")
    document_info: Optional[DocumentInfo] = None  # Infos détaillées du document


async def extract_pdf_content(
    file_path: str,
    extract_tables: bool = True,
    extract_nc_codes: bool = True,
    max_file_size_mb: float = 30.0
) -> ExtractedContent:
    """
    Extrait le contenu d'un fichier PDF.
    
    Args:
        file_path: Chemin vers le fichier PDF
        extract_tables: Extraire les tableaux
        extract_nc_codes: Détecter les codes NC
        max_file_size_mb: Taille maximale du fichier en MB (défaut: 30MB)
    
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
        
        # Vérifier la taille du fichier
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > max_file_size_mb:
            logger.warning("pdf_too_large", file_path=file_path, size_mb=file_size_mb, max_mb=max_file_size_mb)
            return ExtractedContent(
                file_path=file_path,
                text=f"[PDF trop volumineux pour extraction: {file_size_mb:.1f}MB > {max_file_size_mb}MB]",
                nc_codes=[],
                tables=[],
                metadata={"file_size_mb": file_size_mb, "skipped": True},
                page_count=0,
                status="skipped",
                error=f"PDF too large: {file_size_mb:.1f}MB > {max_file_size_mb}MB"
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
        
        # Extraire toutes les infos du document depuis les premières pages
        document_info = None
        publication_date = None
        document_title = None
        document_number = None
        
        if text_content:
            first_pages_text = "".join(text_content[:3])  # Analyser les 2-3 premières pages
            
            # Extraire les infos détaillées
            document_info = _extract_document_info(first_pages_text)
            
            # Remplir les champs pour compatibilité
            publication_date = document_info.publication_date
            document_title = document_info.full_title
            document_number = document_info.document_number
            
            # Enrichir les métadonnées avec les infos extraites
            metadata["publication_date"] = publication_date.isoformat() if publication_date else None
            metadata["document_title"] = document_title
            metadata["document_number"] = document_number
            metadata["celex_number"] = document_info.celex_number
            metadata["document_type"] = document_info.document_type
            metadata["document_subtype"] = document_info.document_subtype
            metadata["issuing_body"] = document_info.issuing_body
            metadata["publication_series"] = document_info.publication_series
        
        logger.info(
            "pdf_extraction_completed",
            file_path=file_path,
            pages=page_count,
            text_length=len(full_text),
            nc_codes=len(nc_codes),
            tables=len(tables),
            publication_date=publication_date.isoformat() if publication_date else None,
            document_number=document_number,
            document_type=document_info.document_type if document_info else None,
            celex_number=document_info.celex_number if document_info else None
        )
        
        return ExtractedContent(
            file_path=file_path,
            text=full_text,
            nc_codes=nc_codes,
            tables=tables,
            metadata=metadata,
            page_count=page_count,
            status="success",
            publication_date=publication_date,
            document_title=document_title,
            document_number=document_number,
            document_info=document_info
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


def _extract_publication_date(text: str) -> Optional[datetime]:
    """
    Extrait la date de publication depuis le texte d'un document EUR-Lex.
    
    La date de publication apparaît généralement en haut à droite sous forme:
    - "30.12.2024" (format DD.MM.YYYY)
    - "30/12/2024" (format DD/MM/YYYY)
    
    Elle peut aussi apparaître dans le header "Official Journal of the European Union L series"
    
    Args:
        text: Texte des premières pages du PDF
        
    Returns:
        datetime ou None si non trouvée
    """
    # Pattern pour date format DD.MM.YYYY ou DD/MM/YYYY (en début de ligne ou après espace)
    # On cherche spécifiquement le format utilisé dans l'en-tête du Journal Officiel
    patterns = [
        # Format: "L series 2024/3210 30.12.2024" ou "L 228/94 EN ... 15.9.2023"
        r'L\s+(?:series\s+)?\d{1,4}[/\s]\d+\s+(\d{1,2}\.\d{1,2}\.\d{4})',
        # Format: date seule DD.MM.YYYY (au moins 2 chiffres pour jour et mois)
        r'(?:^|\s)(\d{1,2}\.\d{1,2}\.\d{4})(?:\s|$)',
        # Format: DD/MM/YYYY
        r'(?:^|\s)(\d{1,2}/\d{1,2}/\d{4})(?:\s|$)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        if matches:
            date_str = matches[0]
            # Essayer de parser la date
            for fmt in ['%d.%m.%Y', '%d/%m/%Y']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
    
    return None


def _extract_document_title(text: str) -> Optional[str]:
    """
    Extrait le titre du document EUR-Lex.
    
    Exemples:
    - "COMMISSION IMPLEMENTING REGULATION (EU) 2024/3210"
    - "REGULATION (EU) 2023/956 OF THE EUROPEAN PARLIAMENT AND OF THE COUNCIL"
    - "DIRECTIVE (EU) 2022/2464"
    
    Args:
        text: Texte des premières pages du PDF
        
    Returns:
        str ou None si non trouvé
    """
    # Pattern pour les différents types de documents EU
    patterns = [
        # Règlement d'implémentation de la Commission
        r'(COMMISSION\s+IMPLEMENTING\s+REGULATION\s*\(EU\)\s*\d{4}/\d+)',
        # Règlement délégué de la Commission
        r'(COMMISSION\s+DELEGATED\s+REGULATION\s*\(EU\)\s*\d{4}/\d+)',
        # Règlement du Parlement et du Conseil
        r'(REGULATION\s*\(EU\)\s*\d{4}/\d+\s+OF\s+THE\s+EUROPEAN\s+PARLIAMENT\s+AND\s+OF\s+THE\s+COUNCIL)',
        # Règlement simple
        r'(REGULATION\s*\(EU\)\s*\d{4}/\d+)',
        # Directive
        r'(DIRECTIVE\s*\(EU\)\s*\d{4}/\d+)',
        # Décision
        r'(DECISION\s*\(EU\)\s*\d{4}/\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None


def _extract_document_number(text: str) -> Optional[str]:
    """
    Extrait le numéro du document EUR-Lex (ex: "2024/3210").
    
    Args:
        text: Texte des premières pages du PDF
        
    Returns:
        str ou None si non trouvé
    """
    # Pattern pour numéro de document: YYYY/NNNN
    patterns = [
        # Dans le header "L series 2024/3210"
        r'L\s+series\s+(\d{4}/\d+)',
        # Dans le titre "(EU) 2024/3210"
        r'\(EU\)\s*(\d{4}/\d+)',
        # Format générique
        r'(?:^|\s)(\d{4}/\d{3,5})(?:\s|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return None


def _extract_document_info(text: str) -> DocumentInfo:
    """
    Extrait toutes les informations détaillées d'un document EUR-Lex.
    
    Args:
        text: Texte des premières pages du PDF
        
    Returns:
        DocumentInfo: Objet contenant toutes les infos extraites
    """
    info = DocumentInfo()
    
    # 1. Extraire la date de publication
    info.publication_date = _extract_publication_date(text)
    
    # 2. Extraire le numéro de document (2024/3210)
    info.document_number = _extract_document_number(text)
    
    # 3. Extraire le type et sous-type de document
    # Patterns pour identifier le type de document
    if re.search(r'IMPLEMENTING\s+REGULATION', text, re.IGNORECASE):
        info.document_type = "REGULATION"
        info.document_subtype = "IMPLEMENTING"
        info.issuing_body = "COMMISSION"
    elif re.search(r'DELEGATED\s+REGULATION', text, re.IGNORECASE):
        info.document_type = "REGULATION"
        info.document_subtype = "DELEGATED"
        info.issuing_body = "COMMISSION"
    elif re.search(r'REGULATION.*EUROPEAN\s+PARLIAMENT\s+AND.*COUNCIL', text, re.IGNORECASE):
        info.document_type = "REGULATION"
        info.document_subtype = None
        info.issuing_body = "PARLIAMENT_COUNCIL"
    elif re.search(r'COMMISSION\s+REGULATION', text, re.IGNORECASE):
        info.document_type = "REGULATION"
        info.document_subtype = None
        info.issuing_body = "COMMISSION"
    elif re.search(r'DIRECTIVE.*EUROPEAN\s+PARLIAMENT', text, re.IGNORECASE):
        info.document_type = "DIRECTIVE"
        info.document_subtype = None
        info.issuing_body = "PARLIAMENT_COUNCIL"
    elif re.search(r'COMMISSION\s+DIRECTIVE', text, re.IGNORECASE):
        info.document_type = "DIRECTIVE"
        info.document_subtype = None
        info.issuing_body = "COMMISSION"
    elif re.search(r'DECISION', text, re.IGNORECASE):
        info.document_type = "DECISION"
        info.document_subtype = None
        # Déterminer l'émetteur pour les décisions
        if re.search(r'COMMISSION\s+DECISION', text, re.IGNORECASE):
            info.issuing_body = "COMMISSION"
        else:
            info.issuing_body = "PARLIAMENT_COUNCIL"
    
    # 4. Extraire la série de publication (L ou C)
    series_match = re.search(r'Official\s+Journal.*?(L|C)\s+series', text, re.IGNORECASE)
    if series_match:
        info.publication_series = series_match.group(1).upper()
    else:
        # Fallback: chercher "L 228/94" ou similaire
        series_match2 = re.search(r'\b(L|C)\s+\d{1,4}[/\s]', text)
        if series_match2:
            info.publication_series = series_match2.group(1).upper()
    
    # 5. Générer le numéro CELEX à partir du numéro de document
    if info.document_number and info.document_type:
        # Format CELEX: 3 (secteur législation) + année + lettre type + numéro
        year, num = info.document_number.split('/')
        type_letter = {
            "REGULATION": "R",
            "DIRECTIVE": "L",
            "DECISION": "D"
        }.get(info.document_type, "X")
        info.celex_number = f"3{year}{type_letter}{num.zfill(4)}"
    
    # 6. Extraire le titre complet
    info.full_title = _extract_document_title(text)
    
    return info

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