"""
Test du pipeline combiné Agent 1A : EUR-Lex + CBAM Guidance

Teste la collecte depuis deux sources en parallèle :
1. EUR-Lex : Lois et règlements CBAM
2. CBAM Guidance : Documents officiels CBAM
"""

import asyncio
from src.agent_1a.agent import run_agent_1a_combined

async def test_combined():
    print('=' * 80)
    print('TEST AGENT 1A - PIPELINE COMBINE (EUR-Lex + CBAM Guidance)')
    print('=' * 80)
    
    print('\nConfiguration:')
    print('  - EUR-Lex: 10 documents CBAM')
    print('  - CBAM Guidance: Toutes categories')
    print('\nCollecte en cours...\n')
    
    result = await run_agent_1a_combined(
        keyword='CBAM',
        max_eurlex_documents=10,
        cbam_categories='all',
        max_cbam_documents=50
    )
    
    print('\n' + '=' * 80)
    print('RESULTATS')
    print('=' * 80)
    
    print(f'\nStatut: {result.get("status")}')
    
    if result.get('status') == 'error':
        print(f'Erreur: {result.get("error")}')
        return
    
    print(f'\nSources:')
    print(f'  EUR-Lex:')
    print(f'    - Trouves: {result["sources"]["eurlex"]["found"]}')
    print(f'    - Traites: {result["sources"]["eurlex"]["processed"]}')
    
    print(f'  CBAM Guidance:')
    print(f'    - Trouves: {result["sources"]["cbam_guidance"]["found"]}')
    print(f'    - Traites: {result["sources"]["cbam_guidance"]["processed"]}')
    
    print(f'\nTotal:')
    print(f'  - Documents trouves: {result.get("total_found", 0)}')
    print(f'  - Documents traites: {result.get("documents_processed", 0)}')
    print(f'  - Documents inchanges: {result.get("documents_unchanged", 0)}')
    
    if result.get("download_errors", 0) > 0:
        print(f'\nErreurs de telechargement: {result["download_errors"]}')
    
    if result.get("extraction_errors", 0) > 0:
        print(f'Erreurs d\'extraction: {result["extraction_errors"]}')
    
    if result.get("save_errors", 0) > 0:
        print(f'Erreurs de sauvegarde: {result["save_errors"]}')
    
    print('\n' + '=' * 80)
    print('Test termine !')
    print('=' * 80)
    
    print('\nVerifier les fichiers telecharges:')
    print('  ls data/documents/*.pdf')

if __name__ == "__main__":
    asyncio.run(test_combined())
