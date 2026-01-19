"""
Demo Agent 1A + 1B Pipeline

Workflow complet:
1. Agent 1A: Scan EUR-Lex + extraction PDF
2. Agent 1B: Analyse pertinence + scoring
"""

import asyncio
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.agent_1a.agent_pipeline import run_agent_1a_simple_pipeline
from src.agent_1b.agent_pipeline import run_agent_1b_pipeline

# Initialiser Rich Console
console = Console()


async def main():
    # Banner
    banner = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║              🤖 AGENT 1A + 1B - Pipeline Complet                              ║
║          Scan EUR-Lex → Analyse Pertinence → Scoring                          ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")
    console.print(f"[dim]Démarrage - {datetime.now().strftime('%d/%m/%Y %H:%M')}[/dim]\n")
    
    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 1 : Agent 1A - Scan EUR-Lex
    # ═══════════════════════════════════════════════════════════
    console.print("\n[bold blue]═══════════════════════════════════════════════════[/bold blue]")
    console.print("[bold blue]          🔍 AGENT 1A - Scan EUR-Lex              [/bold blue]")
    console.print("[bold blue]═══════════════════════════════════════════════════[/bold blue]\n")
    
    with console.status("[bold cyan]Recherche documents CBAM...", spinner="dots"):
        result_1a = await run_agent_1a_simple_pipeline(
            keyword="CBAM",
            max_documents=3
        )
    
    if "error" in result_1a:
        console.print(f"[red]❌ Erreur Agent 1A: {result_1a['error']}[/red]")
        return
    
    documents_1a = result_1a.get("documents", [])
    stats_1a = result_1a.get("stats", {})
    
    console.print(f"[green]✓ Agent 1A terminé[/green]")
    console.print(f"[dim]  {stats_1a.get('successful', 0)} documents téléchargés et extraits[/dim]\n")
    
    if not documents_1a:
        console.print("[yellow]⚠️  Aucun document à analyser[/yellow]")
        return
    
    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 2 : Agent 1B - Analyse Pertinence
    # ═══════════════════════════════════════════════════════════
    console.print("[bold magenta]═══════════════════════════════════════════════════[/bold magenta]")
    console.print("[bold magenta]       🎯 AGENT 1B - Analyse Pertinence          [/bold magenta]")
    console.print("[bold magenta]═══════════════════════════════════════════════════[/bold magenta]\n")
    
    with console.status("[bold magenta]Analyse des documents...", spinner="dots"):
        result_1b = await run_agent_1b_pipeline(documents_1a)
    
    analyzed_docs = result_1b.get("analyzed_documents", [])
    stats_1b = result_1b.get("stats", {})
    
    console.print(f"[green]✓ Agent 1B terminé[/green]")
    console.print(f"[dim]  {stats_1b.get('relevant', 0)}/{stats_1b.get('analyzed', 0)} documents pertinents[/dim]\n")
    
    # ═══════════════════════════════════════════════════════════
    # RÉSULTATS
    # ═══════════════════════════════════════════════════════════
    console.print("\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]              📊 RÉSULTATS FINAUX                   [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n")
    
    # Tableau de synthèse
    summary_table = Table(
        title="📈 Synthèse Pipeline",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    
    summary_table.add_column("Étape", style="cyan", width=30)
    summary_table.add_column("Résultat", style="bold yellow", justify="right", width=40)
    
    summary_table.add_row("Agent 1A - Documents scannés", str(stats_1a.get('total', 0)))
    summary_table.add_row("Agent 1A - Extractions réussies", str(stats_1a.get('successful', 0)))
    summary_table.add_row("Agent 1B - Documents analysés", str(stats_1b.get('analyzed', 0)))
    summary_table.add_row("Agent 1B - Documents pertinents", f"{stats_1b.get('relevant', 0)} ✅")
    summary_table.add_row("Agent 1B - Criticité CRITICAL", f"{stats_1b.get('critical', 0)} 🚨")
    
    console.print(summary_table)
    console.print()
    
    # Afficher documents pertinents
    relevant_docs = [d for d in analyzed_docs if d.get('analysis', {}).get('is_relevant', False)]
    
    if relevant_docs:
        console.print(f"[bold green]🎯 {len(relevant_docs)} DOCUMENT(S) PERTINENT(S) POUR HUTCHINSON[/bold green]\n")
        
        for idx, doc in enumerate(relevant_docs, 1):
            analysis = doc.get('analysis', {})
            
            # Couleur selon criticité
            criticality = analysis.get('criticality', 'LOW')
            if criticality == "CRITICAL":
                border_color = "red"
                crit_icon = "🚨"
            elif criticality == "HIGH":
                border_color = "yellow"
                crit_icon = "⚠️"
            elif criticality == "MEDIUM":
                border_color = "blue"
                crit_icon = "ℹ️"
            else:
                border_color = "dim"
                crit_icon = "📄"
            
            title = doc.get('title', 'Sans titre')[:70]
            
            # Contenu du panel
            content = f"""[bold]CELEX :[/bold] {doc.get('celex_number', 'N/A')}
[bold]Criticité :[/bold] {crit_icon} {criticality}
[bold]Score final :[/bold] {analysis.get('final_score', 0.0):.1%}

[bold cyan]📊 DÉTAILS SCORING[/bold cyan]
  • Keywords (30%) : {analysis.get('level_1_keywords', {}).get('score', 0):.1%}
    → {len(analysis.get('level_1_keywords', {}).get('matched', []))} mots-clés trouvés
  
  • Codes NC (30%) : {analysis.get('level_2_nc_codes', {}).get('score', 0):.1%}
    → {len(analysis.get('level_2_nc_codes', {}).get('found', []))} codes matchés
  
  • Sémantique LLM (40%) : {analysis.get('level_3_semantic', {}).get('score', 0):.1%}

[bold cyan]💡 ANALYSE SÉMANTIQUE[/bold cyan]
  {analysis.get('level_3_semantic', {}).get('reasoning', 'N/A')}
"""
            
            # Impacts
            impacts = analysis.get('level_3_semantic', {}).get('impacts', [])
            if impacts:
                content += f"\n[bold cyan]⚡ IMPACTS POTENTIELS[/bold cyan]\n"
                for impact in impacts[:3]:
                    content += f"  • {impact}\n"
            
            # Panel
            panel = Panel(
                content,
                title=f"[bold]📄 DOCUMENT #{idx}[/bold] — {title}...",
                border_style=border_color,
                box=box.DOUBLE
            )
            
            console.print(panel)
            console.print()
    
    else:
        console.print("[yellow]⚠️  Aucun document pertinent trouvé[/yellow]\n")
    
    # Footer
    console.print("═" * 80)
    console.print("[bold green]✅ Pipeline 1A + 1B terminé avec succès ![/bold green]".center(80))
    console.print("[dim]Prochaine étape : Agent 2 (Scoring & Recommandations)[/dim]".center(80))
    console.print("═" * 80)


if __name__ == "__main__":
    asyncio.run(main())
