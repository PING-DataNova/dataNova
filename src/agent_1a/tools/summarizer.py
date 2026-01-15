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


@tool
async def generate_summary_tool(document_content: str, document_title: str = "Document") -> str:
    """
    Génère un résumé concis d'un document réglementaire en utilisant Claude.
    
    Args:
        document_content: Contenu textuel complet du document
        document_title: Titre du document (optionnel)
    
    Returns:
        str: Résumé en 2-4 phrases (JSON string)
    """
    logger.info("summary_generation_started", title=document_title, content_length=len(document_content))
    
    try:
        # Limiter le contenu à 15000 caractères pour éviter les timeouts
        content_preview = document_content[:15000]
        if len(document_content) > 15000:
            content_preview += "\n\n[...contenu tronqué...]"
        
        # Initialiser Claude
        llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            api_key="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",  # ⬅️ Ajoutez cette ligne
            temperature=0.3,
            max_tokens=500,
            timeout=30
        )

        
        # Prompt pour générer le résumé
        prompt = f"""Tu es un expert en réglementation européenne. Analyse ce document et génère un résumé concis.

DOCUMENT: {document_title}

CONTENU:
{content_preview}

INSTRUCTIONS:
- Résumé en 2-4 phrases maximum
- Identifier le sujet principal et l'objectif de la réglementation
- Mentionner les secteurs/produits concernés (codes NC si présents)
- Indiquer les dates clés (entrée en vigueur, deadlines)
- Mentionner les impacts business principaux
- Être factuel et précis

FORMAT DE SORTIE:
Retourne UNIQUEMENT le résumé en texte brut (pas de JSON, pas de formatage markdown)."""

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