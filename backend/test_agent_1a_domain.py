"""
Test du nouvel Agent 1A - Collecte par domaines (Option 3)

Ce script teste la nouvelle approche de collecte par domaines EUR-Lex
au lieu de la recherche par mots-clés de réglementation.
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le chemin du backend au PYTHONPATH
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


async def test_domain_config():
    """Test 1: Vérifier que la configuration des domaines se charge correctement"""
    console.print("\n[bold blue]═══ TEST 1: Configuration des domaines ═══[/bold blue]\n")
    
    from src.agent_1a.tools.scraper import load_eurlex_domains_config, get_enabled_domains, get_enabled_document_types
    
    # Charger la config
    config = load_eurlex_domains_config()
    
    if not config:
        console.print("[red]❌ Erreur: Configuration non trouvée[/red]")
        return False
    
    console.print("[green]✅ Configuration chargée[/green]")
    
    # Afficher les domaines
    domains = config.get("domains", {})
    table = Table(title="Domaines configurés")
    table.add_column("Clé", style="cyan")
    table.add_column("Nom", style="white")
    table.add_column("Code", style="yellow")
    table.add_column("Activé", style="green")
    
    for key, domain in domains.items():
        table.add_row(
            key,
            domain.get("name", ""),
            domain.get("code", ""),
            "✅" if domain.get("enabled") else "❌"
        )
    
    console.print(table)
    
    # Afficher les domaines activés
    enabled_domains = get_enabled_domains()
    console.print(f"\n[cyan]Domaines activés:[/cyan] {enabled_domains}")
    
    # Afficher les types de documents
    doc_types = get_enabled_document_types()
    console.print(f"[cyan]Types de documents:[/cyan] {doc_types}")
    
    return True


async def test_domain_query_builder():
    """Test 2: Vérifier la construction de la requête par domaines"""
    console.print("\n[bold blue]═══ TEST 2: Construction de la requête ═══[/bold blue]\n")
    
    from src.agent_1a.tools.scraper import _build_domain_query
    
    # Test avec paramètres par défaut
    query = _build_domain_query(
        domains=["15", "13", "11"],
        document_types=["R", "L"],
        max_age_days=365,
        collections=["LEGISLATION", "CONSLEG"]
    )
    
    console.print("[cyan]Requête générée:[/cyan]")
    console.print(Panel(query, title="Expert Query EUR-Lex"))
    
    # Vérifier que la requête contient les bons éléments
    checks = [
        ("DC=15*" in query or "DC=13*" in query, "Filtres par domaine"),
        ("FM=" in query, "Filtres par type de document"),
        ("DD>=" in query, "Filtre par date"),
        ("DTS_SUBDOM=" in query, "Filtre par collection"),
    ]
    
    all_ok = True
    for check, name in checks:
        status = "[green]✅[/green]" if check else "[red]❌[/red]"
        console.print(f"  {status} {name}")
        if not check:
            all_ok = False
    
    return all_ok


async def test_search_eurlex_by_domain():
    """Test 3: Tester la recherche EUR-Lex par domaines (requête réelle)"""
    console.print("\n[bold blue]═══ TEST 3: Recherche EUR-Lex par domaines ═══[/bold blue]\n")
    
    from src.agent_1a.tools.scraper import search_eurlex_by_domain
    
    console.print("[yellow]⏳ Envoi de la requête à EUR-Lex...[/yellow]")
    console.print("[dim]   (Recherche par domaines, sans mot-clé de réglementation)[/dim]\n")
    
    # Recherche limitée pour le test
    result = await search_eurlex_by_domain(
        domains=["15"],  # Environnement uniquement pour le test
        document_types=["R"],  # Règlements uniquement
        max_age_days=90,  # 3 derniers mois
        max_results=5  # Limité pour le test
    )
    
    if result.status != "success":
        console.print(f"[red]❌ Erreur: {result.error}[/red]")
        return False
    
    console.print(f"[green]✅ Recherche réussie[/green]")
    console.print(f"   Documents trouvés: [cyan]{result.total_found}[/cyan]")
    console.print(f"   Total disponible sur EUR-Lex: [cyan]{result.total_available}[/cyan]")
    
    if result.documents:
        console.print("\n[bold]Documents récupérés:[/bold]")
        table = Table()
        table.add_column("CELEX", style="cyan", width=15)
        table.add_column("Type", style="yellow", width=12)
        table.add_column("Titre", style="white", width=60)
        table.add_column("Date", style="green", width=12)
        
        for doc in result.documents[:5]:
            date_str = doc.publication_date.strftime("%Y-%m-%d") if doc.publication_date else "N/A"
            title = doc.title[:57] + "..." if len(doc.title) > 60 else doc.title
            table.add_row(
                doc.celex_number or "N/A",
                doc.document_type,
                title,
                date_str
            )
        
        console.print(table)
        
        # Vérifier qu'il n'y a PAS de filtrage par mot-clé réglementation
        console.print("\n[bold]Vérification - Pas de filtrage par réglementation:[/bold]")
        console.print(f"   Keyword stocké: [cyan]{result.documents[0].keyword}[/cyan]")
        if result.documents[0].keyword == "DOMAIN_SEARCH":
            console.print("   [green]✅ Collecte par domaine (pas de mot-clé réglementation)[/green]")
        else:
            console.print("   [red]❌ Un mot-clé réglementation a été utilisé[/red]")
    
    return True


async def test_comparison_old_vs_new():
    """Test 4: Comparer l'ancienne et la nouvelle approche"""
    console.print("\n[bold blue]═══ TEST 4: Comparaison Ancienne vs Nouvelle approche ═══[/bold blue]\n")
    
    from src.agent_1a.tools.scraper import search_eurlex, search_eurlex_by_domain
    
    # Ancienne approche (par mot-clé)
    console.print("[yellow]📌 Ancienne approche: recherche par mot-clé 'CBAM'[/yellow]")
    old_result = await search_eurlex(keyword="CBAM", max_results=3)
    console.print(f"   Status: {old_result.status}")
    console.print(f"   Documents: {old_result.total_found}")
    if old_result.documents:
        console.print(f"   Keyword: [red]{old_result.documents[0].keyword}[/red] ← Filtré par réglementation")
    
    console.print()
    
    # Nouvelle approche (par domaine)
    console.print("[yellow]📌 Nouvelle approche: recherche par domaine 'Environnement'[/yellow]")
    new_result = await search_eurlex_by_domain(
        domains=["15"],
        max_results=3,
        max_age_days=365
    )
    console.print(f"   Status: {new_result.status}")
    console.print(f"   Documents: {new_result.total_found}")
    if new_result.documents:
        console.print(f"   Keyword: [green]{new_result.documents[0].keyword}[/green] ← Collecte générique")
    
    # Résumé
    console.print("\n[bold]Résumé:[/bold]")
    table = Table()
    table.add_column("Aspect", style="white")
    table.add_column("Ancienne", style="red")
    table.add_column("Nouvelle", style="green")
    
    table.add_row("Filtrage", "Par réglementation (CBAM)", "Par domaine (15=Environnement)")
    table.add_row("Keyword", old_result.documents[0].keyword if old_result.documents else "N/A", 
                  new_result.documents[0].keyword if new_result.documents else "N/A")
    table.add_row("Rôle Agent 1A", "Collecte + Filtre", "Collecte uniquement")
    table.add_row("Rôle Agent 1B", "Analyse pertinence", "Filtre + Analyse pertinence")
    
    console.print(table)
    
    return True


async def main():
    """Exécuter tous les tests"""
    console.print(Panel.fit(
        "[bold white]🧪 TEST AGENT 1A - COLLECTE PAR DOMAINES (Option 3)[/bold white]\n"
        "[dim]Vérifie que l'Agent 1A collecte par domaines sans filtrer par réglementation[/dim]",
        border_style="blue"
    ))
    
    tests = [
        ("Configuration des domaines", test_domain_config),
        ("Construction de la requête", test_domain_query_builder),
        ("Recherche EUR-Lex par domaines", test_search_eurlex_by_domain),
        ("Comparaison ancienne vs nouvelle", test_comparison_old_vs_new),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            console.print(f"[red]❌ Erreur dans {name}: {e}[/red]")
            results.append((name, False))
    
    # Résumé final
    console.print("\n" + "="*60)
    console.print("[bold]RÉSUMÉ DES TESTS[/bold]\n")
    
    all_passed = True
    for name, passed in results:
        status = "[green]✅ PASS[/green]" if passed else "[red]❌ FAIL[/red]"
        console.print(f"  {status} {name}")
        if not passed:
            all_passed = False
    
    console.print()
    if all_passed:
        console.print(Panel("[bold green]✅ Tous les tests sont passés ![/bold green]", border_style="green"))
    else:
        console.print(Panel("[bold red]❌ Certains tests ont échoué[/bold red]", border_style="red"))


if __name__ == "__main__":
    asyncio.run(main())
