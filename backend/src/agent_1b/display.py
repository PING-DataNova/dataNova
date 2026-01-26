"""
Affichage Rich et sauvegarde BDD pour l'Agent 1B
"""

import structlog
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from src.agent_1b.models import DocumentAnalysis, Criticality
from src.storage.database import get_session
from src.storage.analysis_repository import AnalysisRepository

logger = structlog.get_logger()
console = Console()


def display_document_analysis(analysis: DocumentAnalysis) -> None:
    """
    Affiche une analyse de document avec Rich
    
    Args:
        analysis: DocumentAnalysis Pydantic
    """
    
    # Couleurs par criticité
    criticality_color = {
        Criticality.CRITICAL: "red",
        Criticality.HIGH: "orange1",
        Criticality.MEDIUM: "yellow",
        Criticality.LOW: "green",
        Criticality.NOT_RELEVANT: "white"
    }
    
    criticality_emoji = {
        Criticality.CRITICAL: "🔴",
        Criticality.HIGH: "🟠",
        Criticality.MEDIUM: "🟡",
        Criticality.LOW: "🟢",
        Criticality.NOT_RELEVANT: "⚪"
    }
    
    color = criticality_color[analysis.relevance_score.criticality]
    emoji = criticality_emoji[analysis.relevance_score.criticality]
    
    # ========== HEADER ==========
    console.print("\n" + "=" * 90)
    console.print(f"[bold {color}]{emoji} ANALYSE AGENT 1B - {analysis.relevance_score.criticality.value}[/bold {color}]", justify="center")
    console.print("=" * 90)
    
    # ========== DOCUMENT INFO ==========
    console.print("\n[bold cyan]📄 DOCUMENT[/bold cyan]")
    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_row("ID", f"[cyan]{analysis.document_id[:16]}...[/cyan]")
    info_table.add_row("Entreprise", f"[cyan]{analysis.company_profile_id}[/cyan]")
    info_table.add_row("Analysé", f"[cyan]{analysis.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/cyan]")
    console.print(info_table)
    
    # ========== SCORES DÉTAILLÉS ==========
    console.print("\n[bold cyan]📈 SCORES DÉTAILLÉS[/bold cyan]")
    
    scores_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    scores_table.add_column("Niveau", style="cyan")
    scores_table.add_column("Score", style="yellow")
    scores_table.add_column("Poids", style="green")
    scores_table.add_column("Détails", style="white")
    
    # Niveau 1
    keywords_text = f"{len(analysis.keyword_analysis.keywords_found)} mots-clés trouvés"
    scores_table.add_row(
        "1️⃣  Mots-Clés",
        f"{analysis.relevance_score.keyword_score * 100:.1f}%",
        "30%",
        keywords_text
    )
    
    # Niveau 2
    nc_text = f"{len(analysis.nc_code_analysis.exact_matches)} exact + {len(analysis.nc_code_analysis.partial_matches)} partiel"
    scores_table.add_row(
        "2️⃣  Codes NC",
        f"{analysis.relevance_score.nc_code_score * 100:.1f}%",
        "30%",
        nc_text
    )
    
    # Niveau 3
    semantic_text = f"Confiance: {analysis.semantic_analysis.confidence_level * 100:.0f}%"
    scores_table.add_row(
        "3️⃣  Sémantique LLM",
        f"{analysis.relevance_score.semantic_score * 100:.1f}%",
        "40%",
        semantic_text
    )
    
    console.print(scores_table)
    
    # ========== SCORE FINAL ==========
    console.print("\n[bold cyan]🎯 SCORE FINAL[/bold cyan]")
    
    score_pct = analysis.relevance_score.final_score * 100
    
    # Barre de progression
    bar_length = 40
    filled = int(bar_length * analysis.relevance_score.final_score)
    bar = "█" * filled + "░" * (bar_length - filled)
    
    final_table = Table(show_header=False, box=None, padding=(0, 2))
    final_table.add_row(
        f"[bold {color}]{emoji} Criticité[/bold {color}]",
        f"[bold {color}]{analysis.relevance_score.criticality.value}[/bold {color}]"
    )
    final_table.add_row(
        "[bold yellow]Score[/bold yellow]",
        f"[bold yellow]{score_pct:.1f}%[/bold yellow]"
    )
    final_table.add_row(
        "[bold white]Barre[/bold white]",
        f"[{color}]{bar}[/{color}]"
    )
    final_table.add_row(
        "[bold green]Pertinent[/bold green]",
        f"[bold green]✓ OUI[/bold green]" if analysis.is_relevant else "[bold red]✗ NON[/bold red]"
    )
    console.print(final_table)
    
    # ========== PROCESSUS IMPACTÉS ==========
    if analysis.impacted_processes:
        console.print("\n[bold cyan]🎯 PROCESSUS IMPACTÉS[/bold cyan]")
        
        processes_table = Table(show_header=False, box=None, padding=(0, 2))
        
        if analysis.primary_impact_process:
            processes_table.add_row(
                "[bold]Principal[/bold]",
                f"[yellow]{analysis.primary_impact_process.value}[/yellow]"
            )
        
        if len(analysis.impacted_processes) > 1:
            other_processes = ", ".join([p.value for p in analysis.impacted_processes[1:]])
            processes_table.add_row(
                "[bold]Autres[/bold]",
                f"[cyan]{other_processes}[/cyan]"
            )
        
        console.print(processes_table)
    
    # ========== EXPLICATION DE LA LOI ==========
    console.print("\n[bold cyan]📜 CE QUE DIT LA LOI[/bold cyan]")
    console.print(Panel(analysis.law_explanation, border_style="cyan"))
    
    # ========== IMPACT ==========
    if analysis.impact_justification:
        console.print("\n[bold orange1]⚠️  POURQUOI ÇA NOUS IMPACTE[/bold orange1]")
        console.print(Panel(analysis.impact_justification, border_style="orange1"))
    
    # ========== RÉSUMÉ EXÉCUTIF ==========
    console.print("\n[bold cyan]📋 RÉSUMÉ EXÉCUTIF[/bold cyan]")
    console.print(Panel(analysis.executive_summary, border_style="cyan"))
    
    console.print("\n" + "=" * 90 + "\n")


def save_analysis_to_database(analysis: DocumentAnalysis) -> str:
    """
    Sauvegarde l'analyse en base de données
    
    Args:
        analysis: DocumentAnalysis Pydantic
        
    Returns:
        ID de l'analyse sauvegardée
    """
    session = get_session()
    
    try:
        repo = AnalysisRepository(session)
        
        # Sauvegarder l'analyse
        db_analysis = repo.save_from_document_analysis(
            document_analysis=analysis,
            document_id=analysis.document_id
        )
        
        logger.info(
            "analysis_saved_to_db",
            analysis_id=db_analysis.id[:8],
            is_relevant=db_analysis.is_relevant,
            confidence=db_analysis.confidence
        )
        
        console.print(f"\n[bold green]✓ Analyse sauvegardée en BDD[/bold green]")
        console.print(f"  ID: [cyan]{db_analysis.id}[/cyan]")
        console.print(f"  Status: [yellow]{db_analysis.validation_status}[/yellow]")
        
        return db_analysis.id
        
    except Exception as e:
        logger.error("failed_to_save_analysis", error=str(e))
        console.print(f"[bold red]✗ Erreur lors de la sauvegarde: {e}[/bold red]")
        return None
    
    finally:
        session.close()


def process_and_display_analysis(analysis: DocumentAnalysis, save_to_db: bool = True) -> str:
    """
    Traite une analyse complète : affichage + sauvegarde
    
    Args:
        analysis: DocumentAnalysis Pydantic
        save_to_db: Sauvegarder en BDD ?
        
    Returns:
        ID de l'analyse en BDD (ou None si pas sauvegardée)
    """
    # Afficher l'analyse
    display_document_analysis(analysis)
    
    # Sauvegarder en BDD si demandé
    if save_to_db:
        analysis_id = save_analysis_to_database(analysis)
        return analysis_id
    
    return None


def display_analysis_summary(analysis_id: str) -> None:
    """
    Affiche un résumé d'une analyse depuis la BDD
    
    Args:
        analysis_id: ID de l'analyse
    """
    session = get_session()
    
    try:
        repo = AnalysisRepository(session)
        analysis = repo.find_by_id(analysis_id)
        
        if not analysis:
            console.print(f"[bold red]✗ Analyse {analysis_id} non trouvée[/bold red]")
            return
        
        # Afficher un résumé
        console.print("\n" + "=" * 90)
        console.print("[bold cyan]📊 RÉSUMÉ DE L'ANALYSE[/bold cyan]", justify="center")
        console.print("=" * 90)
        
        summary_table = Table(show_header=True, header_style="bold magenta")
        summary_table.add_column("Propriété", style="cyan")
        summary_table.add_column("Valeur", style="yellow")
        
        summary_table.add_row("ID Analyse", analysis.id[:16])
        summary_table.add_row("Document ID", analysis.document_id[:16])
        summary_table.add_row("Pertinent", "✓ OUI" if analysis.is_relevant else "✗ NON")
        summary_table.add_row("Confiance", f"{analysis.confidence * 100:.1f}%")
        summary_table.add_row("Statut Validation", analysis.validation_status)
        summary_table.add_row("Créée", analysis.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        
        if analysis.matched_keywords:
            summary_table.add_row("Mots-clés", ", ".join(analysis.matched_keywords[:5]))
        
        if analysis.matched_nc_codes:
            summary_table.add_row("Codes NC", ", ".join(analysis.matched_nc_codes[:5]))
        
        console.print(summary_table)
        console.print("=" * 90 + "\n")
        
    finally:
        session.close()
