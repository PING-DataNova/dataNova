"""
Démonstration de l'Agent 1B - Analyse + Affichage Rich + Sauvegarde BDD
"""

import json
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

from src.agent_1b.agent import Agent1B, _extract_keywords_from_profile, _extract_regulations_from_profile, _extract_countries_from_profile
from src.agent_1b.display import process_and_display_analysis
from src.storage.database import get_session
from src.storage.models import Document

console = Console()


def main():
    """Point d'entrée principal"""
    
    console.print("\n" + "=" * 90)
    console.print("[bold cyan]🤖 AGENT 1B - DÉMO COMPLÈTE[/bold cyan]", justify="center")
    console.print("[bold white]Analyse + Affichage Rich + Sauvegarde BDD[/bold white]", justify="center")
    console.print("=" * 90)
    
    # Récupérer les documents de la base
    session = get_session()
    
    try:
        documents = session.query(Document).filter(
            Document.regulation_type == "CBAM"
        ).all()
        
        if not documents:
            console.print("\n[bold red]⚠️  Aucun document trouvé dans la base de données.[/bold red]")
            console.print("Exécutez d'abord: [cyan]uv run python test_agent1a_combined.py[/cyan]")
            return
        
        console.print(f"\n[bold green]✓ {len(documents)} document(s) CBAM trouvé(s)[/bold green]")
        
        # Afficher la liste des documents
        console.print("\n[bold cyan]📄 Documents disponibles:[/bold cyan]")
        console.print("-" * 90)
        
        docs_table = Table(show_header=True, header_style="bold magenta")
        docs_table.add_column("#", style="cyan")
        docs_table.add_column("Titre", style="white")
        docs_table.add_column("Taille", style="yellow")
        
        for i, doc in enumerate(documents, 1):
            docs_table.add_row(
                str(i),
                doc.title[:70],
                f"{len(doc.content) if doc.content else 0:,} chars"
            )
        
        console.print(docs_table)
        
        # Analyser TOUS les documents automatiquement
        console.print("\n" + "=" * 90)
        console.print(f"[bold cyan]🚀 Lancement de l'analyse en batch ({len(documents)} documents)...[/bold cyan]")
        
        docs_to_analyze = documents
        
        # Charger le profil entreprise
        console.print("\n[bold cyan]📂 Chargement du profil entreprise...[/bold cyan]")
        
        profile_path = Path("data/company_profiles/Hutchinson_SA.json")
        if not profile_path.exists():
            console.print(f"[bold red]✗ Fichier profil non trouvé: {profile_path}[/bold red]")
            return
        
        with open(profile_path, 'r', encoding='utf-8') as f:
            company_profile_data = json.load(f)
        
        company_name = (
            company_profile_data.get("company", {}).get("company_name") or
            company_profile_data.get("company_name") or
            "HUTCHINSON"
        )
        
        profile = {
            "company_id": company_profile_data.get("company", {}).get("company_id", "HUT-001"),
            "company_name": company_name,
            "industry": company_profile_data.get("company", {}).get("industry", {}).get("sector", ""),
            "products": company_profile_data.get("products", []),
            "nc_codes": company_profile_data.get("nc_codes", {}),
            "keywords": _extract_keywords_from_profile(company_profile_data),
            "regulations": _extract_regulations_from_profile(company_profile_data),
            "countries": _extract_countries_from_profile(company_profile_data)
        }
        
        console.print(f"[bold green]✓ Profil chargé: {company_name}[/bold green]")
        console.print(f"  • {len(profile['keywords'])} mots-clés")
        console.print(f"  • {len(profile.get('nc_codes', {}))} codes NC")
        console.print(f"  • {len(profile['regulations'])} réglementations")
        
        # Analyser les documents
        console.print("\n" + "=" * 90)
        console.print(f"[bold cyan]🔍 Analyse de {len(docs_to_analyze)} document(s)...[/bold cyan]")
        console.print("=" * 90)
        
        agent = Agent1B(profile)
        analyses_created = []
        relevant_count = 0
        critical_count = 0
        
        for idx, doc in enumerate(docs_to_analyze, 1):
            console.print(f"\n[bold cyan]📄 Document {idx}/{len(docs_to_analyze)}[/bold cyan]")
            console.print(f"[white]{doc.title[:80]}...[/white]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[cyan]Analyse en cours...", total=None)
                
                try:
                    # Analyser le document
                    analysis = agent.analyze_document(
                        document_id=doc.id,
                        document_content=doc.content or "",
                        document_title=doc.title,
                        regulation_type=doc.regulation_type or "CBAM"
                    )
                    
                    progress.stop()
                    
                    # Compter les stats
                    if analysis.is_relevant:
                        relevant_count += 1
                    if analysis.relevance_score.criticality.value == "CRITICAL":
                        critical_count += 1
                    
                    # Afficher et sauvegarder
                    analysis_id = process_and_display_analysis(analysis, save_to_db=True)
                    
                    if analysis_id:
                        analyses_created.append(analysis_id)
                    
                except Exception as e:
                    progress.stop()
                    console.print(f"[bold red]✗ Erreur lors de l'analyse: {e}[/bold red]")
                    import traceback
                    traceback.print_exc()
            
            # Pause avant le prochain document (sauf le dernier)
            if idx < len(docs_to_analyze):
                console.print("\n[dim]─[/dim]" * 90)
        
        # Résumé final
        console.print("\n" + "=" * 90)
        console.print("[bold green]✓ Analyse terminée ![/bold green]", justify="center")
        console.print("=" * 90)
        
        if analyses_created:
            console.print(f"\n[bold cyan]📊 SYNTHÈSE PIPELINE[/bold cyan]")
            console.print("-" * 90)
            
            pipeline_table = Table(show_header=True, header_style="bold magenta", box=None)
            pipeline_table.add_column("Étape", style="cyan", width=60)
            pipeline_table.add_column("Résultat", style="yellow", justify="right", width=20)
            
            pipeline_table.add_row(
                "Agent 1A — Documents scannés",
                f"[green]{len(docs_to_analyze)}[/green]"
            )
            pipeline_table.add_row(
                "Agent 1A — Extractions réussies",
                f"[green]{len(docs_to_analyze)}[/green]"
            )
            pipeline_table.add_row(
                "Agent 1B — Documents analysés",
                f"[cyan]{len(analyses_created)}[/cyan]"
            )
            pipeline_table.add_row(
                "Agent 1B — Documents pertinents",
                f"[green]{relevant_count}[/green] {'✓' if relevant_count > 0 else ''}"
            )
            pipeline_table.add_row(
                "Agent 1B — Criticité CRITICAL",
                f"[red]{critical_count}[/red] {'🚫' if critical_count == 0 else '🔴'}"
            )
            
            console.print(pipeline_table)
            
            console.print(f"\n[bold yellow]💾 {len(analyses_created)} analyse(s) sauvegardée(s) en BDD[/bold yellow]")
        
        console.print()
        
    finally:
        session.close()


if __name__ == "__main__":
    main()

