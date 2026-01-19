"""
Summarizer Tool - Génération de résumés de documents avec LLM

Responsable: Dev 1
"""

import os
from typing import Optional
from langchain.tools import tool
from langchain_anthropic import ChatAnthropic
import structlog

logger = structlog.get_logger()
# Instance LLM globale (lazy init) pour éviter réinitialisation
_llm_instance = None

def _get_llm():
    """Lazy initialization du LLM pour résumés."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = ChatAnthropic(
            model="claude-3-haiku-20240307",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.3,
            max_tokens=500,
            timeout=30
        )
        logger.info("llm_summarizer_initialized", model="claude-3-haiku")
    return _llm_instance

@tool
async def generate_summary_tool(document_content: str, document_title: str = "Document") -> str:
    """Résume document réglementaire (2-4 phrases)"""
    logger.info("summary_generation_started", title=document_title, content_length=len(document_content))
    
    try:
        # Limiter le contenu à 8k chars pour éviter rate limits
        content_preview = document_content[:8000]
        if len(document_content) > 8000:
            content_preview += "\n[...tronqué...]"
        
        # Récupérer LLM global (lazy init)
        llm = _get_llm()
        
        # Prompt ultra-court
        prompt = f"""Résume ce document réglementaire en 2-4 phrases. Identifie: sujet principal, secteurs concernés, dates clés, impacts business.

DOCUMENT: {document_title}

{content_preview}

RÉSUMÉ (texte brut uniquement):"""

        # Générer le résumé
        response = await llm.ainvoke(prompt)
        summary = response.content.strip()
        
        logger.info("summary_generation_completed", title=document_title, summary_length=len(summary))
        
        return summary
        
    except Exception as e:
        logger.error("summary_generation_error", error=str(e), title=document_title, exc_info=True)
        return f"Error generating summary: {str(e)}"


# Version synchrone pour compatibilité
def generate_summary_sync(document_content: str, document_title: str = "Document") -> str:
    """Version synchrone du générateur de résumés."""
    import asyncio
    return asyncio.run(generate_summary_tool.ainvoke({"document_content": document_content, "document_title": document_title}))


# Pour tester le module directement
if __name__ == "__main__":
    import asyncio
    
    async def test_summarizer():
        print("=" * 80)
        print("🤖 TEST SUMMARIZER - Génération de résumé")
        print("=" * 80)
        
        # Texte de test (extrait fictif d'une réglementation CBAM)
        test_content = """
        REGULATION (EU) 2023/956 OF THE EUROPEAN PARLIAMENT AND OF THE COUNCIL
        of 10 May 2023
        establishing a carbon border adjustment mechanism
        
        Article 1
        Subject matter and scope
        
        This Regulation establishes a carbon border adjustment mechanism (CBAM) for addressing 
        greenhouse gas emissions embedded in the goods listed in Annex I upon their importation 
        into the customs territory of the Union, in order to prevent the risk of carbon leakage.
        
        Article 2
        Definitions
        
        For the purposes of this Regulation, the following definitions apply:
        (1) 'embedded emissions' means direct emissions released during the production of goods, 
        calculated in accordance with the methods set out in Annex III;
        
        Article 5
        Goods covered
        
        This Regulation applies to the following goods classified under CN codes:
        - Iron and steel (CN codes 7208-7229)
        - Aluminium (CN codes 7601-7606)
        - Cement (CN codes 2507-2523)
        - Fertilizers (CN codes 3102-3105)
        - Electricity (CN code 2716)
        
        Article 30
        Entry into force and application
        
        This Regulation shall enter into force on the twentieth day following that of its 
        publication in the Official Journal of the European Union.
        
        It shall apply from 1 October 2023. However, the obligations under Chapter IV shall 
        apply from 1 January 2026.
        """
        
        # Générer le résumé
        summary = await generate_summary_tool.ainvoke({
            "document_content": test_content,
            "document_title": "Regulation (EU) 2023/956 - CBAM"
        })
        
        print(f"\n📄 Document: Regulation (EU) 2023/956 - CBAM")
        print(f"\n✅ Résumé généré:\n")
        print(summary)
        
        print("\n" + "=" * 80)
        print("✅ Test terminé !")
        print("=" * 80)
    
    asyncio.run(test_summarizer())