"""
Test de collecte EUR-Lex avec mots-clés simples
Date: 04/02/2026
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le dossier backend au path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from src.agent_1a.agent import run_agent_1a_by_domain


async def main():
    print("\n" + "="*70)
    print("📜 COLLECTE EUR-LEX - MOTS-CLÉS SIMPLES")
    print("="*70)
    print("\nRecherche avec des termes simples (rubber, automotive)...")
    print("\n" + "-"*70)
    
    try:
        # Utiliser la collecte par domaines avec des mots-clés simples
        result = await run_agent_1a_by_domain(
            domains=["12.20"],  # Domaine "Libre circulation des marchandises"
            max_documents=10
        )
        
        print("\n" + "="*70)
        print("📊 RÉSULTAT")
        print("="*70)
        
        status = result.get("status", "unknown")
        print(f"\nStatut: {status}")
        
        if status == "skipped":
            print(f"  Message: {result.get('message')}")
            return
        
        if status == "error":
            print(f"  Erreur: {result.get('error')}")
            return
        
        # Statistiques
        print(f"\n📄 Documents trouvés: {result.get('documents_found', 0)}")
        print(f"   Documents traités: {result.get('documents_processed', 0)}")
        
        print("\n" + "="*70)
        print("✅ Test terminé !")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
