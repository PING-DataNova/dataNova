"""
Test du pipeline complet : Agent 1A → Agent 1B

Exécute les deux agents en séquence :
1. Agent 1A collecte les documents
2. Agent 1B analyse SEULEMENT les nouveaux documents (workflow_status = 'raw')
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.orchestration.pipeline import run_pipeline

console = Console()


def main():
    console.print("\n" + "=" * 100)
    console.print("[bold cyan]🚀 PIPELINE COMPLET - AGENT 1A + AGENT 1B[/bold cyan]", justify="center")
    console.print("=" * 100)
    
    console.print("\n[bold yellow]📋 Configuration:[/bold yellow]")
    console.print("  • EUR-Lex: 10 documents CBAM")
    console.print("  • CBAM Guidance: Toutes catégories")
    console.print("  • Profil entreprise: Hutchinson SA")
    
    console.print("\n[bold cyan]🔄 Lancement du pipeline...[/bold cyan]\n")
    
    try:
        result = run_pipeline(
            keyword="CBAM",
            max_eurlex_documents=10,
            cbam_categories="all",
            max_cbam_documents=50
        )
        
        console.print("\n" + "=" * 100)
        console.print("[bold green]✓ PIPELINE TERMINÉ[/bold green]", justify="center")
        console.print("=" * 100)
        
        if result.get("status") != "success":
            console.print(f"\n[bold red]❌ Erreur: {result.get('error')}[/bold red]")
            return
        
        # Résultats Agent 1A
        agent_1a = result.get("agent_1a", {})
        agent_1b = result.get("agent_1b", {})
        
        console.print("\n[bold cyan]📊 RÉSULTATS DÉTAILLÉS[/bold cyan]")
        console.print("-" * 100)
        
        # Tableau récapitulatif
        results_table = Table(show_header=True, header_style="bold magenta")
        results_table.add_column("Agent", style="cyan", width=30)
        results_table.add_column("Métrique", style="white", width=40)
        results_table.add_column("Valeur", style="yellow", justify="right")
        
        # Agent 1A
        results_table.add_row(
            "[bold]Agent 1A[/bold]",
            "Documents trouvés (EUR-Lex)",
            f"[green]{agent_1a.get('sources', {}).get('eurlex', {}).get('found', 0)}[/green]"
        )
        results_table.add_row(
            "",
            "Documents trouvés (CBAM Guidance)",
            f"[green]{agent_1a.get('sources', {}).get('cbam_guidance', {}).get('found', 0)}[/green]"
        )
        results_table.add_row(
            "",
            "Documents traités",
            f"[cyan]{agent_1a.get('documents_processed', 0)}[/cyan]"
        )
        results_table.add_row(
            "",
            "Documents inchangés (skippés)",
            f"[dim]{agent_1a.get('documents_unchanged', 0)}[/dim]"
        )
        
        if agent_1a.get("download_errors", 0) > 0:
            results_table.add_row(
                "",
                "Erreurs téléchargement",
                f"[red]{agent_1a.get('download_errors')}[/red]"
            )
        
        # Séparateur
        results_table.add_row("", "", "")
        
        # Agent 1B
        results_table.add_row(
            "[bold]Agent 1B[/bold]",
            "Documents analysés",
            f"[cyan]{agent_1b.get('documents_analyzed', 0)}[/cyan]"
        )
        results_table.add_row(
            "",
            "Documents pertinents",
            f"[green]{agent_1b.get('relevant_count', 0)}[/green] {'✓' if agent_1b.get('relevant_count', 0) > 0 else ''}"
        )
        results_table.add_row(
            "",
            "Criticité CRITICAL",
            f"[red]{agent_1b.get('critical_count', 0)}[/red] {'🔴' if agent_1b.get('critical_count', 0) > 0 else ''}"
        )
        
        if agent_1b.get("errors", 0) > 0:
            results_table.add_row(
                "",
                "Erreurs d'analyse",
                f"[red]{agent_1b.get('errors')}[/red]"
            )
        
        console.print(results_table)
        
        # Message de synthèse
        console.print("\n[bold yellow]💡 Note:[/bold yellow]")
        console.print("  • Les documents déjà analysés ne sont PAS re-analysés")
        console.print("  • Seuls les documents avec [cyan]workflow_status = 'raw'[/cyan] sont traités")
        console.print("  • Après analyse, le statut devient [green]workflow_status = 'analyzed'[/green]")
        
        console.print("\n[bold green]✓ Pipeline terminé avec succès ![/bold green]\n")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Erreur fatale: {e}[/bold red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
