"""
Test fonctionnel de l'Agent 1A avec profil entreprise.

Ce test valide le flux complet:
1. Lecture du profil entreprise (Hutchinson_SA.json)
2. Extraction des mots-clés
3. Recherche EUR-Lex
4. (Optionnel) Téléchargement et extraction

Usage:
    python test_agent_1a_profile.py [--full]
    
    --full : Exécute le pipeline complet avec téléchargement
"""

import sys
import asyncio
sys.path.insert(0, 'src')

from pathlib import Path


async def test_keyword_extraction():
    """Test 1: Extraction des mots-clés depuis le profil."""
    print("\n" + "="*60)
    print("TEST 1: Extraction des mots-clés du profil entreprise")
    print("="*60)
    
    from agent_1a.tools.keyword_extractor import (
        extract_keywords_from_profile,
        get_eurlex_search_keywords,
        get_default_profile_path
    )
    
    profile_path = get_default_profile_path()
    print(f"\n📁 Profil: {profile_path}")
    
    # Extraction
    keywords = extract_keywords_from_profile(profile_path)
    
    if not keywords:
        print("❌ ÉCHEC: Impossible d'extraire les mots-clés")
        return False, None
    
    print(f"\n✓ Entreprise: {keywords.company_name} ({keywords.company_id})")
    print(f"\n📊 Mots-clés extraits:")
    print(f"   - Codes NC:    {len(keywords.nc_codes):3} ({', '.join(keywords.nc_codes[:5])}...)")
    print(f"   - Matières:    {len(keywords.materials):3} ({', '.join(keywords.materials[:5])}...)")
    print(f"   - Secteurs:    {len(keywords.sectors):3} ({', '.join(list(keywords.sectors)[:5])}...)")
    print(f"   - Pays:        {len(keywords.countries):3} ({', '.join(keywords.countries[:5])}...)")
    print(f"   - Produits:    {len(keywords.products):3} ({', '.join(keywords.products[:5])}...)")
    print(f"   - TOTAL:       {len(keywords.get_all_keywords()):3} mots-clés uniques")
    
    # Mots-clés prioritaires
    search_kw = get_eurlex_search_keywords(keywords, max_keywords=15, priority_threshold=2)
    print(f"\n🎯 Mots-clés prioritaires pour EUR-Lex (priorité ≤ 2):")
    for i, kw in enumerate(search_kw, 1):
        print(f"   {i:2}. {kw}")
    
    print("\n✅ TEST 1 RÉUSSI")
    return True, keywords


async def test_eurlex_search(keywords):
    """Test 2: Recherche EUR-Lex avec les mots-clés."""
    print("\n" + "="*60)
    print("TEST 2: Recherche EUR-Lex avec les mots-clés entreprise")
    print("="*60)
    
    from agent_1a.tools.keyword_extractor import get_eurlex_search_keywords
    from agent_1a.tools.scraper import search_eurlex
    
    # Sélectionner quelques mots-clés pour le test
    search_kw = get_eurlex_search_keywords(keywords, max_keywords=5, priority_threshold=2)
    
    print(f"\n🔍 Test avec {len(search_kw)} mots-clés: {search_kw}")
    
    results = {}
    total_docs = 0
    
    for kw in search_kw:
        print(f"\n   Recherche: {kw}...", end=" ")
        
        result = await search_eurlex(
            keyword=kw,
            max_results=5,
            consolidated_only=False
        )
        
        if result.status == "success":
            count = len(result.documents)
            total_available = result.total_available
            results[kw] = {"found": count, "total": total_available}
            total_docs += count
            print(f"✓ {count} docs (sur {total_available} disponibles)")
            
            # Afficher un exemple
            if result.documents:
                doc = result.documents[0]
                print(f"      └─ Exemple: {doc.title[:60]}...")
        else:
            results[kw] = {"error": result.error}
            print(f"✗ Erreur: {result.error}")
    
    print(f"\n📊 Résumé:")
    print(f"   - Mots-clés testés: {len(search_kw)}")
    print(f"   - Documents trouvés: {total_docs}")
    
    success = sum(1 for r in results.values() if "found" in r)
    if success == len(search_kw):
        print("\n✅ TEST 2 RÉUSSI - Tous les mots-clés retournent des résultats")
        return True
    elif success > 0:
        print(f"\n⚠️ TEST 2 PARTIEL - {success}/{len(search_kw)} mots-clés OK")
        return True
    else:
        print("\n❌ TEST 2 ÉCHEC - Aucun résultat")
        return False


async def test_full_pipeline():
    """Test 3: Pipeline complet Agent 1A."""
    print("\n" + "="*60)
    print("TEST 3: Pipeline complet Agent 1A (sans sauvegarde BDD)")
    print("="*60)
    
    from agent_1a.agent import run_agent_1a_from_profile
    
    print("\n⏳ Exécution du pipeline (peut prendre 1-2 minutes)...")
    print("   - max_documents_per_keyword: 3")
    print("   - max_total_documents: 10")
    print("   - priority_threshold: 1 (codes NC uniquement)")
    print("   - save_to_db: False")
    
    result = await run_agent_1a_from_profile(
        max_documents_per_keyword=3,
        max_total_documents=10,
        priority_threshold=1,  # Codes NC uniquement pour test rapide
        save_to_db=False  # Pas de sauvegarde pour le test
    )
    
    print(f"\n📊 Résultat du pipeline:")
    print(f"   Status: {result.get('status')}")
    
    if result.get("status") == "success":
        company = result.get("company", {})
        keywords = result.get("keywords", {})
        documents = result.get("documents", {})
        errors = result.get("errors", {})
        
        print(f"\n   🏭 Entreprise: {company.get('name')}")
        print(f"\n   🔑 Mots-clés:")
        print(f"      - Extraits: {keywords.get('extracted_total')}")
        print(f"      - Utilisés: {keywords.get('used_for_search')}")
        
        print(f"\n   📄 Documents:")
        print(f"      - Trouvés (uniques): {documents.get('unique_found')}")
        print(f"      - Téléchargés: {documents.get('downloaded')}")
        print(f"      - Extraits: {documents.get('extracted')}")
        
        print(f"\n   ⚠️ Erreurs:")
        print(f"      - Téléchargement: {errors.get('download')}")
        print(f"      - Extraction: {errors.get('extraction')}")
        
        # Stats par mot-clé
        keyword_stats = result.get("keyword_stats", {})
        if keyword_stats:
            print(f"\n   📈 Stats par mot-clé:")
            for kw, stats in list(keyword_stats.items())[:5]:
                if "found" in stats:
                    print(f"      - {kw}: {stats['found']} docs (sur {stats['total_available']})")
        
        print("\n✅ TEST 3 RÉUSSI")
        return True
    else:
        print(f"\n   ❌ Erreur: {result.get('error')}")
        print("\n❌ TEST 3 ÉCHEC")
        return False


async def main():
    """Exécute tous les tests."""
    print("\n" + "#"*60)
    print("# TEST AGENT 1A - COLLECTE DEPUIS PROFIL ENTREPRISE")
    print("#"*60)
    
    full_test = "--full" in sys.argv
    
    # Test 1: Extraction
    success1, keywords = await test_keyword_extraction()
    if not success1:
        print("\n❌ Tests arrêtés (extraction échouée)")
        return
    
    # Test 2: Recherche EUR-Lex
    success2 = await test_eurlex_search(keywords)
    
    # Test 3: Pipeline complet (optionnel)
    if full_test:
        success3 = await test_full_pipeline()
    else:
        print("\n" + "="*60)
        print("TEST 3: IGNORÉ (utiliser --full pour exécuter)")
        print("="*60)
        success3 = True
    
    # Résumé
    print("\n" + "#"*60)
    print("# RÉSUMÉ DES TESTS")
    print("#"*60)
    print(f"\n   Test 1 (Extraction mots-clés):  {'✅' if success1 else '❌'}")
    print(f"   Test 2 (Recherche EUR-Lex):     {'✅' if success2 else '❌'}")
    print(f"   Test 3 (Pipeline complet):      {'✅' if success3 else '❌'} {'(skipped)' if not full_test else ''}")
    
    if success1 and success2:
        print("\n🎉 L'Agent 1A est prêt à collecter depuis le profil entreprise!")
        print("\n   Utilisation:")
        print("   ```python")
        print("   from agent_1a.agent import run_agent_1a_from_profile")
        print("   result = await run_agent_1a_from_profile(")
        print("       max_documents_per_keyword=20,")
        print("       max_total_documents=100,")
        print("       priority_threshold=2  # codes NC + matières")
        print("   )")
        print("   ```")


if __name__ == "__main__":
    asyncio.run(main())
