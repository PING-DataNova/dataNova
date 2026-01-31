#!/usr/bin/env python3
"""
Test Agent 1A - Collecte de TOUTES les réglementations européennes

Ce script recherche les documents consolidés pour CHAQUE réglementation
dans la liste REGULATIONS_CONFIG de scraper.py.

Usage:
    uv run python test_agent_1a_all_regulations.py
"""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Ajouter le chemin src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent_1a.tools.scraper import (
    search_eurlex, 
    REGULATIONS_CONFIG, 
    get_all_regulations,
    get_search_keywords_for_regulation
)
from agent_1a.tools.document_fetcher import fetch_document
from agent_1a.tools.pdf_extractor import extract_pdf_content
from storage.database import init_db, get_session
from storage.models import Document

console = Console()

# ========================================
# CONFIGURATION
# ========================================

# Nombre maximum de documents par réglementation
MAX_DOCS_PER_REGULATION = 1  # Seulement le dernier texte consolidé

# Liste des réglementations à collecter (None = toutes)
# Mettre une liste pour filtrer: ["CBAM", "REACH", "EUDR"]
REGULATIONS_TO_COLLECT = None  # Toutes les 27 réglementations


async def collect_regulation_documents(
    regulation_code: str,
    max_docs: int = MAX_DOCS_PER_REGULATION
) -> dict:
    """
    Collecte les documents consolidés pour une réglementation donnée.
    Ne garde que le document le plus récent (dernière version consolidée).
    
    Args:
        regulation_code: Code de la réglementation (CBAM, REACH, etc.)
        max_docs: Nombre maximum de documents à récupérer (1 = dernier seulement)
        
    Returns:
        dict avec les statistiques de collecte
    """
    config = REGULATIONS_CONFIG.get(regulation_code)
    if not config:
        return {"error": f"Réglementation inconnue: {regulation_code}"}
    
    keywords = config["search_keywords"]
    all_documents = []
    seen_urls = set()
    
    for keyword in keywords:
        console.print(f"  🔍 Recherche: [cyan]{keyword}[/cyan]")
        
        # Récupérer plus de docs pour pouvoir trier et prendre le plus récent
        result = await search_eurlex(
            keyword=keyword,
            max_results=10,  # Récupérer 10 pour avoir le choix
            consolidated_only=True
        )
        
        if result.status == "success":
            # Dédoublonner par URL PDF
            for doc in result.documents:
                if doc.pdf_url not in seen_urls:
                    seen_urls.add(doc.pdf_url)
                    # Ajouter le code de réglementation au document
                    doc.metadata["regulation_code"] = regulation_code
                    doc.metadata["regulation_name"] = config["name"]
                    all_documents.append(doc)
            
            console.print(f"    ✅ {len(result.documents)} trouvés (total dispo: {result.total_available})")
        else:
            console.print(f"    ❌ Erreur: {result.error}")
    
    # Trier par date de publication (plus récent en premier)
    # Les documents sans date sont mis à la fin
    from datetime import datetime
    all_documents.sort(
        key=lambda d: d.publication_date if d.publication_date else datetime.min,
        reverse=True
    )
    
    # Ne garder que le nombre demandé (par défaut 1 = le plus récent)
    selected_documents = all_documents[:max_docs]
    
    if selected_documents and selected_documents[0].publication_date:
        console.print(f"  📅 Sélectionné: [green]{selected_documents[0].title[:60]}...[/green]")
        console.print(f"     Date: [yellow]{selected_documents[0].publication_date.strftime('%Y-%m-%d')}[/yellow]")
    
    return {
        "regulation_code": regulation_code,
        "regulation_name": config["name"],
        "keywords_searched": keywords,
        "documents_found": len(selected_documents),
        "total_available": len(all_documents),
        "documents": selected_documents
    }


async def main():
    """Point d'entrée principal."""
    
    console.print(Panel.fit(
        "🧪 TEST AGENT 1A - COLLECTE TOUTES RÉGLEMENTATIONS",
        style="bold blue"
    ))
    
    # Déterminer les réglementations à collecter
    if REGULATIONS_TO_COLLECT:
        regulations = REGULATIONS_TO_COLLECT
    else:
        regulations = get_all_regulations()
    
    console.print(f"\n📋 Réglementations à collecter : [bold]{len(regulations)}[/bold]")
    console.print(f"📊 Max documents par réglementation : [bold]{MAX_DOCS_PER_REGULATION}[/bold]")
    console.print(f"📄 Mode : [bold green]Textes consolidés uniquement[/bold green]\n")
    
    # === ÉTAPE 0 : Initialiser la BDD ===
    console.print(Panel("📋 ÉTAPE 0 : Initialisation de la base de données", style="cyan"))
    init_db()
    console.print("✅ Base de données initialisée\n")
    
    # === ÉTAPE 1 : Collecter les documents pour chaque réglementation ===
    console.print(Panel("📋 ÉTAPE 1 : Collecte des documents par réglementation", style="cyan"))
    
    all_results = []
    total_documents = 0
    
    for i, reg_code in enumerate(regulations, 1):
        config = REGULATIONS_CONFIG.get(reg_code, {})
        reg_name = config.get("name", reg_code)
        
        console.print(f"\n[bold]({i}/{len(regulations)}) {reg_code}[/bold] - {reg_name}")
        
        result = await collect_regulation_documents(reg_code, MAX_DOCS_PER_REGULATION)
        all_results.append(result)
        total_documents += result.get("documents_found", 0)
    
    # === AFFICHAGE DES RÉSULTATS ===
    console.print("\n" + "=" * 80)
    console.print(Panel("📊 RÉSULTATS DE LA COLLECTE", style="bold green"))
    
    # Tableau récapitulatif
    table = Table(title="Documents collectés par réglementation")
    table.add_column("Code", style="cyan", no_wrap=True)
    table.add_column("Nom", style="white")
    table.add_column("Documents", justify="right", style="green")
    table.add_column("Mots-clés", style="dim")
    
    for result in all_results:
        if "error" not in result:
            table.add_row(
                result["regulation_code"],
                result["regulation_name"][:40] + "..." if len(result["regulation_name"]) > 40 else result["regulation_name"],
                str(result["documents_found"]),
                ", ".join(result["keywords_searched"][:2]) + ("..." if len(result["keywords_searched"]) > 2 else "")
            )
    
    console.print(table)
    
    # Statistiques globales
    stats_table = Table(title="Statistiques globales")
    stats_table.add_column("Métrique", style="cyan")
    stats_table.add_column("Valeur", justify="right", style="bold")
    
    stats_table.add_row("📚 Réglementations traitées", str(len(regulations)))
    stats_table.add_row("📄 Total documents collectés", str(total_documents))
    stats_table.add_row("📊 Moyenne docs/réglementation", f"{total_documents/len(regulations):.1f}")
    
    # Compter les réglementations avec/sans documents
    with_docs = sum(1 for r in all_results if r.get("documents_found", 0) > 0)
    without_docs = len(all_results) - with_docs
    
    stats_table.add_row("✅ Réglementations avec documents", str(with_docs))
    stats_table.add_row("⚠️ Réglementations sans documents", str(without_docs))
    
    console.print(stats_table)
    
    # === ÉTAPE 2 : Sauvegarde en BDD (optionnel) ===
    console.print(Panel("📋 ÉTAPE 2 : Sauvegarde en base de données", style="cyan"))
    
    saved_count = 0
    db = get_session()
    
    try:
        for result in all_results:
            if "documents" in result:
                for doc in result["documents"]:
                    try:
                        import hashlib
                        # Créer un hash unique pour le document
                        hash_content = f"{doc.pdf_url or ''}{doc.title or ''}"
                        hash_sha256 = hashlib.sha256(hash_content.encode()).hexdigest()
                        
                        # Vérifier si le document existe déjà par hash
                        existing = db.query(Document).filter(
                            Document.hash_sha256 == hash_sha256
                        ).first()
                        
                        if not existing:
                            db_doc = Document(
                                title=doc.title[:500] if doc.title else "Sans titre",
                                source_url=doc.pdf_url or doc.url or "",
                                event_type="reglementaire",
                                event_subtype=result["regulation_code"],
                                publication_date=doc.publication_date,  # Date de publication
                                hash_sha256=hash_sha256,
                                status="new",
                                extra_metadata={
                                    "celex_number": doc.celex_number,
                                    "document_type": doc.document_type,
                                    "regulation_code": result["regulation_code"],
                                    "regulation_name": result["regulation_name"],
                                    "html_url": doc.url,
                                    "pdf_url": doc.pdf_url,
                                    **doc.metadata
                                }
                            )
                            db.add(db_doc)
                            saved_count += 1
                    except Exception as e:
                        console.print(f"[red]Erreur sauvegarde: {e}[/red]")
        
        db.commit()
    finally:
        db.close()
    
    console.print(f"✅ {saved_count} nouveaux documents sauvegardés en BDD")
    
    # === ÉTAPE 3 : Téléchargement des PDFs ===
    console.print(Panel("📋 ÉTAPE 3 : Téléchargement des documents PDF", style="cyan"))
    
    download_count = 0
    download_errors = 0
    
    # Créer le dossier de destination
    from pathlib import Path
    pdf_output_dir = Path("data/documents")
    pdf_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Récupérer tous les documents avec leurs URLs PDF
    all_docs_to_download = []
    for result in all_results:
        if "documents" in result:
            for doc in result["documents"]:
                if doc.pdf_url:
                    all_docs_to_download.append({
                        "pdf_url": doc.pdf_url,
                        "regulation_code": result["regulation_code"],
                        "celex_number": doc.celex_number or "unknown",
                        "title": doc.title
                    })
    
    console.print(f"📥 {len(all_docs_to_download)} documents à télécharger...")
    
    for i, doc_info in enumerate(all_docs_to_download, 1):
        pdf_url = doc_info["pdf_url"]
        reg_code = doc_info["regulation_code"]
        celex = doc_info["celex_number"]
        
        # Nom de fichier basé sur CELEX et réglementation
        filename = f"{reg_code}_{celex}.pdf".replace("/", "_").replace(":", "_")
        
        console.print(f"  ({i}/{len(all_docs_to_download)}) [cyan]{filename}[/cyan]...", end=" ")
        
        try:
            result = await fetch_document(
                url=pdf_url,
                output_dir=str(pdf_output_dir),
                filename=filename,
                timeout=60
            )
            
            if result.success:
                download_count += 1
                file_size_kb = result.document.file_size / 1024 if result.document else 0
                console.print(f"[green]✓[/green] ({file_size_kb:.1f} KB)")
            else:
                download_errors += 1
                console.print(f"[red]✗ {result.error}[/red]")
        except Exception as e:
            download_errors += 1
            console.print(f"[red]✗ {str(e)[:50]}[/red]")
    
    console.print(f"\n✅ {download_count} PDFs téléchargés dans [cyan]{pdf_output_dir}[/cyan]")
    if download_errors > 0:
        console.print(f"⚠️ {download_errors} erreurs de téléchargement")
    
    # === ÉTAPE 4 : Extraction du contenu des PDFs ===
    console.print(Panel("📋 ÉTAPE 4 : Extraction du contenu des PDFs", style="cyan"))
    
    extraction_count = 0
    extraction_errors = 0
    
    # Récupérer tous les documents de la BDD pour mise à jour du content
    db = get_session()
    try:
        # Parcourir les fichiers PDF téléchargés
        pdf_files = list(pdf_output_dir.glob("*.pdf"))
        console.print(f"📄 {len(pdf_files)} fichiers PDF à traiter...")
        
        for i, pdf_file in enumerate(pdf_files, 1):
            filename = pdf_file.name
            console.print(f"  ({i}/{len(pdf_files)}) [cyan]{filename}[/cyan]...", end=" ")
            
            try:
                # Extraire le contenu du PDF (augmenter la limite à 10MB pour les gros règlements)
                extracted = await extract_pdf_content(
                    str(pdf_file),
                    extract_tables=False,  # Pas besoin des tableaux pour le moment
                    extract_nc_codes=False,  # Pas besoin des codes NC pour le moment
                    max_file_size_mb=10.0  # Augmenter la limite pour les gros PDF
                )
                
                if extracted.status == "success" and extracted.text:
                    # Trouver le document en BDD par le CELEX dans le nom de fichier
                    # Format: REGULATION_CODE_CELEX.pdf -> extraire CELEX (commence par un chiffre)
                    # Ex: CO2_VEHICLES_02023R2866.pdf -> CELEX = 02023R2866
                    parts = filename.replace(".pdf", "").split("_")
                    # Le CELEX est la dernière partie qui commence par un chiffre
                    celex = None
                    for part in reversed(parts):
                        if part and part[0].isdigit():
                            celex = part
                            break
                    
                    if celex:
                        # Chercher le document avec ce CELEX - utiliser LIKE pour JSON
                        docs = db.query(Document).filter(
                            Document.extra_metadata.like(f'%"celex_number": "{celex}"%')
                        ).all()
                        
                        if docs:
                            for doc in docs:
                                doc.content = extracted.text[:50000]  # Limiter à 50k caractères
                            extraction_count += 1
                            console.print(f"[green]✓[/green] ({len(extracted.text)} chars, {len(docs)} docs)")
                        else:
                            console.print(f"[yellow]⚠ Doc non trouvé en BDD (CELEX: {celex})[/yellow]")
                    else:
                        console.print(f"[yellow]⚠ Format nom invalide[/yellow]")
                elif extracted.status == "skipped":
                    console.print(f"[yellow]⚠ {extracted.error}[/yellow]")
                else:
                    extraction_errors += 1
                    console.print(f"[red]✗ {extracted.error or 'Erreur extraction'}[/red]")
                    
            except Exception as e:
                extraction_errors += 1
                console.print(f"[red]✗ {str(e)[:50]}[/red]")
        
        db.commit()
        
    finally:
        db.close()
    
    console.print(f"\n✅ {extraction_count} documents avec contenu extrait")
    if extraction_errors > 0:
        console.print(f"⚠️ {extraction_errors} erreurs d'extraction")
    
    # === RÉSUMÉ FINAL ===
    console.print("\n" + "=" * 80)
    console.print(Panel.fit(
        f"🎉 COLLECTE TERMINÉE\n\n"
        f"Réglementations : {len(regulations)}\n"
        f"Documents collectés : {total_documents}\n"
        f"Documents sauvegardés : {saved_count}\n"
        f"PDFs téléchargés : {download_count}\n"
        f"Contenus extraits : {extraction_count}\n"
        f"Erreurs téléchargement : {download_errors}\n"
        f"Erreurs extraction : {extraction_errors}\n"
        f"Dossier PDFs : {pdf_output_dir}\n"
        f"Base de données : data/datanova.db",
        style="bold green"
    ))
    
    return all_results


if __name__ == "__main__":
    asyncio.run(main())
