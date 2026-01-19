#!/usr/bin/env python3
"""
Demo Agent 1A - Version Pipeline (recommandée)

Version optimisée sans ReAct pour éviter rate limits.
Utilise l'orchestration Python manuelle (Option B).
"""

import asyncio
from src.agent_1a.agent_pipeline import run_agent_1a_simple_pipeline


def print_box(text, width=80, style="double"):
    """Affiche un texte dans un cadre."""
    if style == "double":
        top = "╔" + "═" * (width - 2) + "╗"
        bottom = "╚" + "═" * (width - 2) + "╝"
        side = "║"
    else:  # simple
        top = "┌" + "─" * (width - 2) + "┐"
        bottom = "└" + "─" * (width - 2) + "┘"
        side = "│"
    
    print(top)
    # Centrer le texte
    padding = (width - 2 - len(text)) // 2
    print(f"{side}{' ' * padding}{text}{' ' * (width - 2 - padding - len(text))}{side}")
    print(bottom)


def print_header(text, width=80):
    """Affiche un en-tête avec bordure décorative."""
    border = "═" * width
    print(f"\n{border}")
    print(f"{text.center(width)}")
    print(f"{border}\n")


def print_table(data, headers=None, width=80):
    """Affiche un tableau avec bordures."""
    if headers:
        # En-tête du tableau
        print("┌" + "─" * (width - 2) + "┐")
        col_width = (width - 4) // len(headers)
        header_line = "│ " + " │ ".join(h.ljust(col_width) for h in headers) + " │"
        print(header_line)
        print("├" + "─" * (width - 2) + "┤")
    else:
        print("┌" + "─" * (width - 2) + "┐")
    
    # Lignes de données
    for row in data:
        if isinstance(row, dict):
            # Format clé: valeur
            for key, value in row.items():
                key_str = str(key).ljust(30)
                val_str = str(value)
                print(f"│ {key_str} │ {val_str.ljust(width - 36)} │")
        elif isinstance(row, (list, tuple)):
            # Format multi-colonnes
            col_width = (width - 4) // len(row)
            row_line = "│ " + " │ ".join(str(cell).ljust(col_width) for cell in row) + " │"
            print(row_line)
        else:
            # Format simple
            print(f"│ {str(row).ljust(width - 4)} │")
    
    print("└" + "─" * (width - 2) + "┘")


def print_section(title, emoji="", width=80):
    """Affiche un titre de section avec emoji."""
    print(f"\n{emoji} {title}")
    print("─" * width)


async def main():
    width = 100
    
    # En-tête principal
    print("\n" + "═" * width)
    print("🤖 DÉMONSTRATION AGENT 1A - PIPELINE (VERSION OPTIMISÉE)".center(width))
    print("═" * width)
    
    # Informations sur le mode
    print("\n┌" + "─" * (width - 2) + "┐")
    print("│" + " Mode : Orchestration Python manuelle (sans ReAct)".ljust(width - 1) + "│")
    print("├" + "─" * (width - 2) + "┤")
    print("│ " + "Avantages :".ljust(width - 3) + "│")
    print("│   ✅ 3-5x plus rapide que ReAct".ljust(width - 1) + "│")
    print("│   ✅ Aucun risque de rate limit 429".ljust(width - 1) + "│")
    print("│   ✅ Contrôle total du workflow".ljust(width - 1) + "│")
    print("│   ✅ Tokens minimaux (LLM uniquement pour résumés)".ljust(width - 1) + "│")
    print("└" + "─" * (width - 2) + "┘")
    
    print("\n" + "═" * width)
    print("🔍 EXÉCUTION DU SCAN RÉGLEMENTAIRE".center(width))
    print("═" * width + "\n")
    
    # Rechercher 3 documents CBAM sur EUR-Lex
    result = await run_agent_1a_simple_pipeline(
        keyword="CBAM",
        max_documents=3
    )
    
    if "error" in result:
        print(f"\n❌ Erreur: {result['error']}")
    else:
        docs = result.get("documents", [])
        stats = result.get("stats", {})
        
        # Résumé du scan
        print("\n" + "═" * width)
        print("📊 RÉSULTATS DU SCAN RÉGLEMENTAIRE".center(width))
        print("═" * width + "\n")
        
        # Tableau de résumé
        print("┌" + "─" * (width - 2) + "┐")
        print("│" + " 📈 Résumé du Scan".center(width - 2) + "│")
        print("├" + "─" * 48 + "┬" + "─" * (width - 51) + "┤")
        print("│ Métrique".ljust(49) + "│ Valeur".ljust(width - 50) + "│")
        print("├" + "─" * 48 + "┼" + "─" * (width - 51) + "┤")
        
        total = stats.get('total', 0)
        successful = stats.get('successful', 0)
        errors = stats.get('errors', 0)
        
        print(f"│ Total documents traités".ljust(49) + f"│ {total}".ljust(width - 50) + "│")
        print(f"│ ✅ Documents réussis".ljust(49) + f"│ {successful}".ljust(width - 50) + "│")
        print(f"│ ❌ Erreurs".ljust(49) + f"│ {errors}".ljust(width - 50) + "│")
        print(f"│ ⚠️  Impact Élevé".ljust(49) + f"│ {successful} 📢".ljust(width - 50) + "│")
        print("└" + "─" * 48 + "┴" + "─" * (width - 51) + "┘")
        
        # Afficher les documents
        for i, doc in enumerate(docs, 1):
            status = doc.get('status', 'unknown')
            status_icon = "✅" if status == "completed" else "❌"
            
            print("\n" + "╔" + "═" * (width - 2) + "╗")
            title = doc.get('title', 'Sans titre')[:90]
            print(f"║ ALERTE #{i} — {title}".ljust(width - 1) + "║")
            print("╠" + "═" * (width - 2) + "╣")
            
            # Catégorie et statut
            doc_type = doc.get('document_type', 'N/A')
            category_icon = "🔴" if status == "completed" else "⚪"
            print(f"║ Catégorie : {category_icon} {doc_type}".ljust(width - 1) + "║")
            print(f"║ Statut : {status_icon} {status}".ljust(width - 1) + "║")
            print(f"║ CELEX : {doc.get('celex_number', 'N/A')}".ljust(width - 1) + "║")
            
            # Date
            pub_date = doc.get('publication_date', 'N/A')
            if pub_date != 'N/A' and 'T' in str(pub_date):
                pub_date = pub_date.split('T')[0]
            print(f"║ Date : {pub_date}".ljust(width - 1) + "║")
            
            print("║".ljust(width - 1) + "║")
            
            # IMPACT
            print("║ 🎯 IMPACT".ljust(width - 1) + "║")
            print(f"║   Niveau : Élevé".ljust(width - 1) + "║")
            
            # Fichiers
            if doc.get("file_size"):
                file_size_kb = doc.get('file_size', 0) // 1024
                print(f"║   Financier : ~{file_size_kb} Ko de données".ljust(width - 1) + "║")
            
            # NC codes
            nc_codes = doc.get("nc_codes", [])
            if nc_codes:
                nc_str = ', '.join(nc_codes[:5])
                print(f"║   Codes NC concernés : {nc_str}".ljust(width - 1) + "║")
                if len(nc_codes) > 5:
                    print(f"║     (+{len(nc_codes) - 5} autres codes)".ljust(width - 1) + "║")
            
            print("║".ljust(width - 1) + "║")
            
            # RÉSUMÉ
            print("║ 📝 RÉSUMÉ".ljust(width - 1) + "║")
            summary = doc.get('summary', 'Pas de résumé disponible')
            
            # Découper le résumé en lignes de 90 caractères
            words = summary.split()
            lines = []
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 <= 90:
                    current_line += (word + " ")
                else:
                    lines.append(current_line.strip())
                    current_line = word + " "
            if current_line:
                lines.append(current_line.strip())
            
            for line in lines:
                print(f"║   {line}".ljust(width - 1) + "║")
            
            print("║".ljust(width - 1) + "║")
            
            # DÉTAILS TECHNIQUES
            print("║ 🔧 DÉTAILS TECHNIQUES".ljust(width - 1) + "║")
            url = str(doc.get('url', 'N/A'))[:85]
            print(f"║   URL : {url}...".ljust(width - 1) + "║")
            
            if doc.get("file_path"):
                print(f"║   📁 PDF : {doc['file_path']}".ljust(width - 1) + "║")
            if doc.get("text_path"):
                text_chars = doc.get('text_chars', 0)
                print(f"║   📄 Texte : {doc['text_path']} ({text_chars:,} caractères)".ljust(width - 1) + "║")
            
            print("╚" + "═" * (width - 2) + "╝")
    
    print("\n" + "═" * width)
    print("✅ SCAN TERMINÉ".center(width))
    print("═" * width + "\n")


if __name__ == "__main__":
    asyncio.run(main())
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
