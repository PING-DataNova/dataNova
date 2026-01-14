"""
Test de l'Agent 1A avec LangChain
"""

import pytest
import asyncio
from src.agent_1a.agent import run_agent_1a, create_agent_1a


@pytest.mark.asyncio
@pytest.mark.timeout(180)  # Timeout de 3 minutes (suffisant pour scraping)
async def test_agent_1a_scraping():
    """Test : L'agent peut scraper la page CBAM"""
    query = "Scrape la page CBAM et retourne le nombre de documents trouvés en JSON"
    result = await run_agent_1a(query)
    
    assert result["status"] == "success"
    assert "output" in result
    print(f"\n✅ Scraping test passed: {result['output']}")


@pytest.mark.asyncio
async def test_agent_1a_download():
    """Test : L'agent peut télécharger un document"""
    query = """Scrape la page CBAM, prends le premier document PDF, 
    télécharge-le et donne-moi son hash SHA-256"""
    result = await run_agent_1a(query)
    
    assert result["status"] == "success"
    assert "hash" in result["output"].lower() or "sha" in result["output"].lower()
    print(f"\n✅ Download test passed: {result['output']}")


@pytest.mark.asyncio
async def test_agent_1a_full_pipeline():
    """Test : Pipeline complet (scrape → download → extract)"""
    query = """
    1. Scrape la page CBAM
    2. Télécharge le premier PDF trouvé
    3. Extrait le contenu du PDF
    4. Compte les codes NC trouvés
    5. Retourne un JSON avec : nombre de documents, taille du PDF, nombre de codes NC
    """
    result = await run_agent_1a(query)
    
    assert result["status"] == "success"
    print(f"\n✅ Full pipeline test passed")
    print(f"Output: {result['output']}")


def test_agent_creation():
    """Test : L'agent peut être créé sans erreur"""
    agent = create_agent_1a()
    assert agent is not None
    print("\n✅ Agent creation test passed")


if __name__ == "__main__":
    print("=" * 80)
    print("🧪 TESTS AGENT 1A - LangChain")
    print("=" * 80)
    
    # Exécuter les tests
    asyncio.run(test_agent_1a_scraping())
    asyncio.run(test_agent_1a_download())
    asyncio.run(test_agent_1a_full_pipeline())
    test_agent_creation()
    
    print("\n" + "=" * 80)
    print("✅ Tous les tests sont passés !")
    print("=" * 80)