"""Script pour lancer Agent 1A + 1B et afficher les résultats"""
import json
from src.orchestration.langgraph_workflow import run_ping_workflow

print("🚀 Lancement Agent 1A (collecte) + Agent 1B (pertinence)...")
print("=" * 60)

result = run_ping_workflow(keyword="CBAM", max_documents=8, company_name="HUTCHINSON")

print("=" * 60)
print(f"Status: {result['status']}")

# Résumé Agent 1A
if "agent_1a" in result:
    a1a = result["agent_1a"]
    print(f"\n📥 AGENT 1A - Collecte:")
    print(f"   Documents collectés: {a1a.get('documents_collected', '?')}")
    print(f"   Documents en BDD: {a1a.get('documents_in_db', '?')}")

# Résumé Agent 1B
if "agent_1b" in result:
    a1b = result["agent_1b"]
    print(f"\n🔍 AGENT 1B - Pertinence:")
    print(f"   Documents analysés: {a1b.get('documents_processed', '?')}")
    print(f"   Pertinents (OUI): {a1b.get('pertinent_count', '?')}")
    print(f"   Partiellement: {a1b.get('partial_count', '?')}")
    print(f"   Non pertinents: {a1b.get('non_pertinent_count', '?')}")

# Détails des checks si dispo
if "pertinence_results" in result.get("agent_1b", {}):
    print("\n📋 Détails par document:")
    for r in result["agent_1b"]["pertinence_results"]:
        title = r.get("title", r.get("document_id", "?"))[:50]
        decision = r.get("decision", "?")
        confidence = r.get("confidence", 0)
        print(f"   [{decision}] ({confidence:.2f}) {title}")

# Dump complet (tronqué)
print("\n📦 Résultat complet (tronqué):")
print(json.dumps(result, indent=2, ensure_ascii=False, default=str)[:3000])
