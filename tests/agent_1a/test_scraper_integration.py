# tests/agent_1a/test_scraper_integration.py

import pytest
from src.agent_1a.tools.scraper import scrape_cbam_page

@pytest.mark.integration
@pytest.mark.asyncio
async def test_scrape_real_cbam_page():
    """Test avec la vraie page CBAM (nécessite Internet)."""
    url = "https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism/cbam-legislation-and-guidance_en"
    
    result = await scrape_cbam_page(url)
    
    assert result.status == "success"
    assert result.total_found > 0
    print(f"\n✅ Documents trouvés: {result.total_found}")
    
    for doc in result.documents[:5]:
        print(f"  - {doc.title} ({doc.celex_id})")