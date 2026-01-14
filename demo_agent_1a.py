#!/usr/bin/env python3
"""
Script de démonstration de l'Agent 1A
"""

import asyncio
from src.agent_1a.agent import run_agent_1a


async def main():
    print("\n" + "="*80)
    print("🤖 DÉMONSTRATION AGENT 1A - SCRAPING CBAM")
    print("="*80)
    
    # Test 1: Scraping simple
    print("\n📝 Test 1: Scraping simple")
    print("-" * 80)
    query1 = "Scrape la page CBAM et retourne le nombre de documents trouvés en JSON"
    result1 = await run_agent_1a(query1)
    
    print(f"Status: {result1['status']}")
    print(f"\n=== RÉSULTAT ===\n")
    print(result1['output'])
    
    # Test 2: Scraping + téléchargement
    print("\n\n📝 Test 2: Scraping + Téléchargement + Extraction")
    print("-" * 80)
    query2 = """Scrape la page CBAM, télécharge le premier document PDF trouvé, 
    puis extrait son contenu et compte les codes NC"""
    result2 = await run_agent_1a(query2)
    
    print(f"Status: {result2['status']}")
    print(f"\n=== RÉSULTAT ===\n")
    print(result2['output'])
    
    print("\n" + "="*80)
    print("✅ Tests terminés !")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
