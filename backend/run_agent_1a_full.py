"""
Execution complete de l'Agent 1A avec sauvegarde en base de donnees.
- Collecte reglementaire (EUR-Lex)
- Collecte meteorologique (Open-Meteo)
"""
import asyncio
import sys
sys.path.insert(0, 'src')

async def main():
    from agent_1a.agent import run_agent_1a_from_profile, run_agent_1a_weather
    
    # ================================================================
    # PARTIE 1 : COLLECTE REGLEMENTAIRE
    # ================================================================
    print('='*70)
    print('AGENT 1A - PARTIE 1 : COLLECTE REGLEMENTAIRE (EUR-Lex)')
    print('='*70)
    print()
    print('Configuration:')
    print('  - max_documents_per_keyword: 10')
    print('  - max_total_documents: 50')
    print('  - priority_threshold: 2 (codes NC + matieres)')
    print('  - min_publication_year: 2000 (documents depuis 2000)')
    print('  - prefer_consolidated: True (versions consolidees privilegiees)')
    print('  - save_to_db: True')
    print()
    print('Demarrage...')
    print()
    
    result_reg = await run_agent_1a_from_profile(
        max_documents_per_keyword=10,
        max_total_documents=50,
        priority_threshold=2,
        min_publication_year=2000,
        save_to_db=True
    )
    
    print()
    print('='*70)
    print('RESULTAT COLLECTE REGLEMENTAIRE')
    print('='*70)
    
    if result_reg['status'] == 'success':
        print('Status: SUCCESS')
        print()
        print(f"Entreprise: {result_reg['company']['name']}")
        print()
        print('Mots-cles:')
        print(f"  - Extraits du profil: {result_reg['keywords']['extracted_total']}")
        print(f"  - Utilises pour recherche: {result_reg['keywords']['used_for_search']}")
        print()
        print('Documents:')
        print(f"  - Trouves uniques: {result_reg['documents']['unique_found']}")
        print(f"  - Telecharges: {result_reg['documents']['downloaded']}")
        print(f"  - Extraits: {result_reg['documents']['extracted']}")
        print(f"  - Sauvegardes en BDD: {result_reg['documents']['saved']}")
        print()
        print('Erreurs:')
        print(f"  - Telechargement: {result_reg['errors']['download']}")
        print(f"  - Extraction: {result_reg['errors']['extraction']}")
        print(f"  - Sauvegarde: {result_reg['errors']['save']}")
    else:
        print('Status: ERREUR')
        print(f"Erreur: {result_reg.get('error')}")
    
    # ================================================================
    # PARTIE 2 : COLLECTE METEOROLOGIQUE
    # ================================================================
    print()
    print('='*70)
    print('AGENT 1A - PARTIE 2 : COLLECTE METEOROLOGIQUE (Open-Meteo)')
    print('='*70)
    print()
    print('Configuration:')
    print('  - forecast_days: 16 jours')
    print('  - sites: usines Hutchinson + fournisseurs + ports')
    print('  - save_to_db: True')
    print()
    print('Demarrage...')
    print()
    
    result_weather = await run_agent_1a_weather(
        forecast_days=16,
        save_to_db=True
    )
    
    print()
    print('='*70)
    print('RESULTAT COLLECTE METEOROLOGIQUE')
    print('='*70)
    
    if result_weather['status'] == 'success':
        print('Status: SUCCESS')
        print()
        print('Sites surveilles:')
        print(f"  - Total: {result_weather['sites']['total']}")
        print(f"  - Previsions recues: {result_weather['sites']['forecasts_fetched']}")
        print()
        print('Alertes meteo:')
        print(f"  - Total detectees: {result_weather['alerts']['total']}")
        print(f"  - Sauvegardees en BDD: {result_weather['alerts']['saved']}")
        print()
        print('Par severite:')
        for sev, count in result_weather['alerts']['by_severity'].items():
            icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(sev, '⚪')
            print(f"  {icon} {sev}: {count}")
        print()
        print('Par type:')
        for alert_type, count in result_weather['alerts'].get('by_type', {}).items():
            print(f"  - {alert_type}: {count}")
    else:
        print('Status: ERREUR')
        print(f"Erreur: {result_weather.get('error')}")
    
    # ================================================================
    # RESUME FINAL
    # ================================================================
    print()
    print('='*70)
    print('RESUME AGENT 1A - COLLECTE COMPLETE')
    print('='*70)
    print()
    print('Documents reglementaires:')
    if result_reg['status'] == 'success':
        print(f"  ✅ {result_reg['documents']['saved']} documents sauvegardes")
    else:
        print(f"  ❌ Erreur: {result_reg.get('error')}")
    print()
    print('Alertes meteorologiques:')
    if result_weather['status'] == 'success':
        print(f"  ✅ {result_weather['alerts']['saved']} alertes sauvegardees")
    else:
        print(f"  ❌ Erreur: {result_weather.get('error')}")

if __name__ == '__main__':
    asyncio.run(main())
