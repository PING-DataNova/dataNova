"""
Test de collecte EUR-Lex Agent 1A
Date: 04/02/2026
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le dossier backend au path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from src.agent_1a.agent import run_agent_1a_full_collection


async def main():
    print("\n" + "="*70)
    print("📜 COLLECTE EUR-LEX - AGENT 1A")
    print("="*70)
    print("\nLancement de la collecte des réglementations européennes...")
    print("  - Source: EUR-Lex")
    print("  - Mots-clés: CBAM, REACH, caoutchouc, automobile...")
    print("  - Max documents: 20")
    print("\n" + "-"*70)
    
    try:
        result = await run_agent_1a_full_collection(
            max_documents_per_keyword=5,
            max_keywords=3,
            save_to_db=True
        )
        
        print("\n" + "="*70)
        print("📊 RÉSULTAT DE LA COLLECTE EUR-LEX")
        print("="*70)
        
        status = result.get("status", "unknown")
        print(f"\nStatut: {status}")
        
        if status == "skipped":
            print(f"  Message: {result.get('message')}")
            print("\n⚠️ La source EUR-Lex est désactivée dans l'admin.")
            return
        
        if status == "error":
            print(f"  Erreur: {result.get('error')}")
            return
        
        # Statistiques
        print(f"\n📄 Documents:")
        print(f"  - Trouvés: {result.get('documents_found', result.get('total_found', 0))}")
        print(f"  - Traités: {result.get('documents_processed', 0)}")
        print(f"  - Nouveaux: {result.get('documents_new', 0)}")
        print(f"  - Inchangés: {result.get('documents_unchanged', 0)}")
        
        # Erreurs
        errors = result.get('errors', {})
        if errors:
            print(f"\n⚠️ Erreurs:")
            print(f"  - Téléchargement: {errors.get('download', 0)}")
            print(f"  - Extraction: {errors.get('extraction', 0)}")
            print(f"  - Sauvegarde: {errors.get('save', 0)}")
        
        print("\n" + "="*70)
        print("✅ Collecte EUR-Lex terminée !")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
