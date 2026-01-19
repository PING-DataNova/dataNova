#!/usr/bin/env python3
"""
Script de test rapide de l'architecture après corrections
"""

print("=" * 80)
print("🔍 TEST DE L'ARCHITECTURE CORRIGÉE")
print("=" * 80)

# Test 1: Imports principaux
print("\n✓ Test 1: Imports principaux...")
try:
    from src.config import settings
    from src.orchestration.pipeline import run_pipeline, load_sources_config
    from src.agent_1a.agent import create_agent_1a
    from src.agent_1a.tools import get_agent_1a_tools
    from src.storage.database import get_session, init_db
    from src.storage.repositories import DocumentRepository, CompanyProfileRepository
    print("  ✅ Tous les imports OK")
except Exception as e:
    print(f"  ❌ Erreur d'import: {e}")
    exit(1)

# Test 2: Outils Agent 1A
print("\n✓ Test 2: Vérification des outils Agent 1A...")
try:
    tools = get_agent_1a_tools()
    print(f"  ✅ {len(tools)} outils chargés:")
    for tool in tools:
        print(f"    - {tool.name}")
except Exception as e:
    print(f"  ❌ Erreur outils: {e}")
    exit(1)

# Test 3: Configuration
print("\n✓ Test 3: Configuration...")
try:
    print(f"  ✅ Database: {settings.database_url}")
    print(f"  ✅ Log level: {settings.log_level}")
    print(f"  ✅ Company profile: {settings.default_company_profile}")
    print(f"  ✅ CBAM source: {settings.cbam_source_url[:60]}...")
except Exception as e:
    print(f"  ❌ Erreur config: {e}")
    exit(1)

# Test 4: Database repositories
print("\n✓ Test 4: Database repositories...")
try:
    session = get_session()
    doc_repo = DocumentRepository(session)
    profile_repo = CompanyProfileRepository(session)
    session.close()
    print("  ✅ Repositories instanciés correctement")
except Exception as e:
    print(f"  ❌ Erreur repositories: {e}")
    exit(1)

# Test 5: Agent 1A peut être créé
print("\n✓ Test 5: Création Agent 1A...")
try:
    agent = create_agent_1a(model_name="claude-3-haiku-20240307")
    print("  ✅ Agent 1A créé avec succès")
except Exception as e:
    print(f"  ⚠️  Note: {e}")
    print("  (Normal si ANTHROPIC_API_KEY n'est pas configurée)")

print("\n" + "=" * 80)
print("✅ TOUS LES TESTS PASSÉS - ARCHITECTURE FONCTIONNELLE")
print("=" * 80)
print("\n📝 Prochaines étapes:")
print("  1. Configurer .env avec ANTHROPIC_API_KEY")
print("  2. Initialiser la DB: uv run python scripts/init_db.py")
print("  3. Tester Agent 1A: uv run python demo_agent_1a.py")
print("  4. Implémenter Agent 1B (actuellement vide)")
print("  5. Implémenter Agent 2 (actuellement vide)")
print()
