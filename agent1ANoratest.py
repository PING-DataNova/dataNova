"""
Demo Agent 1A Pipeline - Version orchestration manuelle (Option B)

Test du workflow sans ReAct pour éviter rate limits.
"""

import asyncio
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from src.agent_1a.agent_pipeline import run_agent_1a_simple_pipeline

# Initialiser Rich Console
console = Console()


async def main():
    # Banner de démarrage
    banner = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║              🚀 AGENT 1A PIPELINE - Orchestration Python                      ║
║                   Version optimisée sans ReAct                                ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")
    console.print(f"[dim]Démarrage - {datetime.now().strftime('%d/%m/%Y %H:%M')}[/dim]\n")
    
    # Panel d'informations
    info_panel = Panel(
        """[bold cyan]Avantages vs ReAct :[/bold cyan]
  ✅ Pas de réinjection de contexte massif
  ✅ LLM appelé uniquement pour résumés
  ✅ 3-5x plus rapide
  ✅ Aucun risque de rate limit 429""",
        title="[bold]ℹ️  Configuration Pipeline[/bold]",
        border_style="blue",
        box=box.ROUNDED
    )
    console.print(info_panel)
    console.print("\n" + "═" * 80 + "\n")
    
    # Rechercher 3 documents CBAM sur EUR-Lex
    with console.status("[bold cyan]🔍 Scan EUR-Lex en cours...", spinner="dots"):
        result = await run_agent_1a_simple_pipeline(
            keyword="CBAM",
            max_documents=3
        )
    
    console.print("[green]✓ Scan terminé[/green]\n")
    
    if "error" in result:
        console.print(f"[red]❌ Erreur: {result['error']}[/red]")
    else:
        docs = result.get("documents", [])
        stats = result.get("stats", {})
        
        # Tableau de résumé avec Rich
        console.print("\n[bold magenta]═══════════════════════════════════════════════════[/bold magenta]")
        console.print("[bold magenta]              📊 RÉSULTATS DU SCAN                  [/bold magenta]")
        console.print("[bold magenta]═══════════════════════════════════════════════════[/bold magenta]\n")
        
        summary_table = Table(
            title="📈 Statistiques",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        summary_table.add_column("Métrique", style="cyan", width=40)
        summary_table.add_column("Valeur", style="bold yellow", justify="right", width=30)
        
        summary_table.add_row("Total documents traités", str(stats.get('total', 0)))
        summary_table.add_row("✅ Documents réussis", str(stats.get('successful', 0)))
        summary_table.add_row("❌ Erreurs", str(stats.get('errors', 0)))
        
        console.print(summary_table)
        console.print()
        
        # Afficher les documents dans des panels stylés
        for i, doc in enumerate(docs, 1):
            # Couleur selon le statut
            status = doc.get('status', 'N/A')
            if status == "completed":
                border_color = "green"
                status_icon = "✅"
            else:
                border_color = "red"
                status_icon = "❌"
            
            title = doc.get('title', 'Sans titre')
            
            # Construire le contenu du panel
            content = f"""[bold]CELEX :[/bold] {doc.get('celex_number', 'N/A')}
[bold]Type :[/bold] {doc.get('document_type', 'N/A')}
[bold]Statut :[/bold] {status_icon} {status}
"""
            
            # Date
            pub_date = doc.get('publication_date', 'N/A')
            if pub_date != 'N/A' and 'T' in str(pub_date):
                pub_date = pub_date.split('T')[0]
            content += f"[bold]Date :[/bold] {pub_date}\n\n"
            
            # URLs
            content += f"[bold cyan]🔗 LIENS[/bold cyan]\n"
            url = str(doc.get('url', 'N/A'))[:70]
            content += f"  URL : {url}...\n"
            pdf_url = str(doc.get('pdf_url', 'N/A'))[:70]
            content += f"  PDF : {pdf_url}...\n\n"
            
            # Fichiers locaux
            if doc.get("file_path"):
                content += f"[bold cyan]📁 FICHIERS LOCAUX[/bold cyan]\n"
                content += f"  PDF téléchargé : {doc['file_path']}\n"
                content += f"  Taille : {doc.get('file_size', 0):,} bytes\n"
            
            if doc.get("text_path"):
                content += f"  Texte extrait : {doc['text_path']}\n"
                content += f"  Caractères : {doc.get('text_chars', 0):,}\n\n"
            
            # NC codes
            nc_codes = doc.get("nc_codes", [])
            if nc_codes:
                content += f"[bold cyan]🏷️  CODES NC[/bold cyan]\n"
                nc_str = ', '.join(nc_codes[:10])
                content += f"  {nc_str}\n"
                if len(nc_codes) > 10:
                    content += f"  [dim](+ {len(nc_codes) - 10} autres codes)[/dim]\n"
                content += "\n"
            
            # Résumé
            content += f"[bold cyan]📝 RÉSUMÉ[/bold cyan]\n"
            summary = doc.get('summary', 'Pas de résumé')
            
            # Découper le résumé en lignes
            words = summary.split()
            lines = []
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 <= 70:
                    current_line += (word + " ")
                else:
                    lines.append(current_line.strip())
                    current_line = word + " "
            if current_line:
                lines.append(current_line.strip())
            
            # Limiter à 8 lignes
            for line in lines[:8]:
                content += f"  {line}\n"
            
            if len(lines) > 8:
                content += "  [dim]...[/dim]"
            
            # Créer le panel
            panel = Panel(
                content,
                title=f"[bold]📄 DOCUMENT #{i}[/bold] — {title[:60]}...",
                border_style=border_color,
                box=box.DOUBLE
            )
            
            console.print(panel)
            console.print()
    
    # Footer
    console.print("═" * 80)
    console.print("[bold green]✅ Demo terminée ![/bold green]".center(80))
    console.print("═" * 80)


if __name__ == "__main__":
    asyncio.run(main())
