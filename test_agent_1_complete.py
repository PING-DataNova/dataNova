"""
Test Intégré : Agent 1A + Agent 1B
Teste le pipeline complet de collecte et analyse de documents
"""

import asyncio
import sys
from datetime import datetime

# Imports des agents
from src.agent_1a.agent import run_agent_1a_eurlex_scenario_2
from src.agent_1b.agent import run_agent_1b

# Couleurs pour le terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_section(title):
    """Affiche un titre de section"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}\n")


def print_success(message):
    """Affiche un message de succès"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")


def print_error(message):
    """Affiche un message d'erreur"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")


def print_info(message):
    """Affiche un message d'information"""
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.END}")


def print_warning(message):
    """Affiche un avertissement"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")


async def test_agent_1_complete():
    """Test complet du pipeline Agent 1A + Agent 1B"""
    
    print_section("🤖 TEST INTÉGRÉ : AGENT 1A + AGENT 1B")
    print_info(f"Démarrage : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ========================================================================
    # ÉTAPE 1 : AGENT 1A - COLLECTE DE DOCUMENTS
    # ========================================================================
    print_section("ÉTAPE 1️⃣  : AGENT 1A - COLLECTE DE DOCUMENTS")
    
    try:
        print_info("Lancement de l'Agent 1A (scraping EUR-Lex)...")
        
        result_1a = await run_agent_1a_eurlex_scenario_2(
            keyword="CBAM",
            max_documents=5
        )
        
        if result_1a.get("status") == "success":
            print_success(f"Agent 1A exécuté avec succès")
            
            # Gérer les différents formats de résultat
            documents_list = result_1a.get("documents_processed", [])
            if isinstance(documents_list, list):
                documents_processed = len(documents_list)
                print_info(f"Documents trouvés : {result_1a.get('total_found', 0)}")
                print_info(f"Documents traités : {documents_processed}")
                
                if documents_processed > 0:
                    print_success(f"{documents_processed} document(s) sauvegardé(s) en BDD")
                    print_info("Statut des documents : workflow_status='raw' (en attente d'analyse)")
                    
                    # Afficher les documents traités
                    print_info(f"\n📄 Documents traités par Agent 1A ({documents_processed}):")
                    for idx, doc in enumerate(documents_list, 1):
                        title = doc.get("title", "Unknown")[:60]
                        celex = doc.get("celex_number", "Unknown")
                        nc_codes = doc.get("nc_codes_count", 0)
                        print(f"  {idx}. {title}...")
                        print(f"     CELEX: {celex}")
                        print(f"     Codes NC: {nc_codes}")
                else:
                    print_warning("Aucun nouveau document trouvé")
            else:
                print_error("Format de résultat inattendu de l'Agent 1A")
                return
        else:
            print_error(f"Agent 1A a échoué : {result_1a.get('error', 'Erreur inconnue')}")
            return
    
    except Exception as e:
        print_error(f"Erreur lors de l'exécution de l'Agent 1A : {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # ========================================================================
    # ÉTAPE 2 : AGENT 1B - ANALYSE DE PERTINENCE
    # ========================================================================
    print_section("ÉTAPE 2️⃣  : AGENT 1B - ANALYSE DE PERTINENCE")
    
    try:
        print_info("Lancement de l'Agent 1B (analyse sémantique)...")
        
        result_1b = await run_agent_1b(
            company_id="GMG-001",
            max_documents=5,
            skip_analyzed=True
        )
        
        if result_1b.get("status") == "success":
            print_success(f"Agent 1B exécuté avec succès")
            
            company_name = result_1b.get("company_name", "Unknown")
            documents_processed = result_1b.get("documents_processed", 0)
            documents_relevant = result_1b.get("documents_relevant", 0)
            documents_irrelevant = result_1b.get("documents_irrelevant", 0)
            
            print_info(f"Entreprise analysée : {company_name}")
            print_info(f"Documents traités : {documents_processed}")
            print_success(f"Documents pertinents : {documents_relevant}")
            print_info(f"Documents non-pertinents : {documents_irrelevant}")
            
            # Afficher les analyses créées
            analyses = result_1b.get("analyses_created", [])
            if analyses:
                print_info(f"\n📄 Analyses créées par Agent 1B ({len(analyses)}):")
                for idx, analysis in enumerate(analyses, 1):
                    title = analysis.get("title", "Unknown")[:60]
                    is_relevant = analysis.get("is_relevant", False)
                    confidence = analysis.get("confidence", 0.0)
                    
                    relevance_icon = "✅" if is_relevant else "❌"
                    print(f"  {idx}. {title}...")
                    print(f"     {relevance_icon} Pertinent : {is_relevant}")
                    print(f"     📊 Confiance : {confidence:.2f} (0-1)")
                    
                    summary = analysis.get("summary", "")
                    if summary:
                        summary_short = summary[:80] + "..." if len(summary) > 80 else summary
                        print(f"     📝 Résumé : {summary_short}")
                    print()
            else:
                print_warning("Aucune analyse créée (tous les documents étaient déjà analysés)")
            
            # Afficher les erreurs s'il y en a
            errors = result_1b.get("errors")
            if errors:
                print_warning(f"\n⚠️  Erreurs rencontrées ({len(errors)}):")
                for error in errors:
                    print(f"  • {error.get('title', 'Unknown')[:60]}")
                    print(f"    Erreur : {error.get('error', 'Unknown')[:80]}")
        else:
            print_error(f"Agent 1B a échoué : {result_1b.get('error', 'Erreur inconnue')}")
            return
    
    except Exception as e:
        print_error(f"Erreur lors de l'exécution de l'Agent 1B : {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # ========================================================================
    # RÉSUMÉ FINAL
    # ========================================================================
    print_section("📊 RÉSUMÉ FINAL DU PIPELINE")
    
    # Compter les documents de l'Agent 1A
    documents_1a_list = result_1a.get("documents_processed", [])
    documents_1a_count = len(documents_1a_list) if isinstance(documents_1a_list, list) else 0
    
    print_info("Agent 1A (Collecte)")
    print(f"  • Documents trouvés : {result_1a.get('total_found', 0)}")
    print(f"  • Documents traités : {documents_1a_count}")
    
    print_info("\nAgent 1B (Analyse)")
    print(f"  • Documents analysés : {result_1b.get('documents_processed', 0)}")
    print(f"  • Documents pertinents : {result_1b.get('documents_relevant', 0)}")
    print(f"  • Documents non-pertinents : {result_1b.get('documents_irrelevant', 0)}")
    
    print_info("\nÉtat de la BDD")
    print(f"  • Documents avec workflow_status='analyzed' : {result_1b.get('documents_processed', 0)}")
    print(f"  • Analyses créées : {len(result_1b.get('analyses_created', []))}")
    
    print_section("✅ TEST COMPLET TERMINÉ AVEC SUCCÈS")
    print_info(f"Fin : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 Pipeline Agent 1A → Agent 1B OPÉRATIONNEL !{Colors.END}\n")


if __name__ == "__main__":
    print(f"\n{Colors.BOLD}{Colors.CYAN}Initialisation du test intégré...{Colors.END}\n")
    
    try:
        asyncio.run(test_agent_1_complete())
    except KeyboardInterrupt:
        print_error("\nTest interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print_error(f"Erreur fatale : {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)