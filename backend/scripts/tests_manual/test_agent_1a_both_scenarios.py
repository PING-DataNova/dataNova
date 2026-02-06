"""
Test complet de l'Agent 1A - Les deux scénarios
================================================

Scénario 1: Collecte automatique (run_agent_1a)
Scénario 2: Analyse fournisseur manuelle (run_agent_1a_for_supplier)
"""

import asyncio
import sqlite3
import json
from datetime import datetime

# Configuration
DB_PATH = "data/datanova.db"


async def test_scenario_1():
    """Scénario 1: Collecte automatique complète (profil Hutchinson + tous les sites)"""
    print("\n" + "=" * 70)
    print("🔄 SCÉNARIO 1: COLLECTE AUTOMATIQUE COMPLÈTE")
    print("   - Extraction mots-clés depuis profil Hutchinson")
    print("   - Collecte EUR-Lex par mots-clés")
    print("   - Collecte météo pour tous les sites (usines, fournisseurs, ports)")
    print("=" * 70)
    
    from src.agent_1a.agent import run_agent_1a_full_collection
    
    result = await run_agent_1a_full_collection(
        company_profile_path="data/company_profiles/Hutchinson_SA.json",
        min_publication_year=2000,
        max_documents_per_keyword=3,  # Limiter pour le test
        max_keywords=2,  # Seulement 2 mots-clés pour le test
        save_to_db=True,
        use_database=True  # Lire les sites depuis la BDD
    )
    
    print(f"\n✅ Statut: {result.get('status')}")
    print(f"🔍 Mode: {result.get('mode')}")
    
    eurlex = result.get('eurlex', {})
    print(f"\n📄 EUR-Lex:")
    print(f"   - Mots-clés utilisés: {len(eurlex.get('keywords_used', []))}")
    print(f"   - Documents trouvés: {eurlex.get('documents_found', 0)}")
    print(f"   - Documents sauvegardés: {eurlex.get('documents_saved', 0)}")
    
    weather = result.get('weather', {})
    print(f"\n🌤️  Météo:")
    print(f"   - Sites surveillés: {weather.get('sites_monitored', 0)}")
    print(f"   - Sites traités: {weather.get('sites_processed', 0)}")
    print(f"   - Alertes détectées: {weather.get('alerts_detected', 0)}")
    
    print(f"\n⏱️  Temps: {result.get('processing_time_ms', 0)} ms")
    
    return result


async def test_scenario_2():
    """Scénario 2: Analyse fournisseur manuelle"""
    print("\n" + "=" * 70)
    print("🏭 SCÉNARIO 2: ANALYSE FOURNISSEUR MANUELLE")
    print("=" * 70)
    
    from src.agent_1a.agent import run_agent_1a_for_supplier
    
    # Fournisseur test: Hutchinson au Maroc
    supplier_info = {
        "name": "Hutchinson Maroc",
        "country": "Maroc",
        "city": "Casablanca",
        "latitude": 33.57,
        "longitude": -7.59,
        "materials": ["rubber", "elastomer"],
        "nc_codes": ["4001", "400121"],
        "criticality": "Critique",
        "annual_volume": 5000000
    }
    
    result = await run_agent_1a_for_supplier(
        supplier_info=supplier_info,
        save_to_db=True
    )
    
    print(f"\n✅ Statut: {result.get('status')}")
    print(f"📋 Analysis ID: {result.get('analysis_id')}")
    
    collected = result.get('collected_data', {})
    print(f"📄 Risques réglementaires: {collected.get('regulatory', {}).get('count', 0)}")
    print(f"🌤️  Alertes météo: {collected.get('weather', {}).get('count', 0)}")
    print(f"💾 Documents sauvegardés: {collected.get('documents_saved_count', 0)}")
    print(f"⏱️  Temps: {result.get('processing_time_ms', 0)} ms")
    
    return result


def verify_database():
    """Vérifier le contenu de la BDD après les deux scénarios"""
    print("\n" + "=" * 70)
    print("🔍 VÉRIFICATION DE LA BASE DE DONNÉES")
    print("=" * 70)
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Compter les documents
    cur.execute("SELECT COUNT(*) FROM documents")
    doc_count = cur.fetchone()[0]
    
    # Compter les supplier_analyses
    cur.execute("SELECT COUNT(*) FROM supplier_analyses")
    analysis_count = cur.fetchone()[0]
    
    # Compter les weather_alerts
    cur.execute("SELECT COUNT(*) FROM weather_alerts")
    weather_count = cur.fetchone()[0]
    
    print(f"\n📊 Résumé des tables:")
    print(f"   • documents: {doc_count} enregistrements")
    print(f"   • supplier_analyses: {analysis_count} enregistrements")
    print(f"   • weather_alerts: {weather_count} enregistrements")
    
    # Détails des documents
    print(f"\n📄 Documents (par source):")
    cur.execute("""
        SELECT 
            CASE 
                WHEN extra_metadata LIKE '%supplier_analysis%' THEN 'Scénario 2 (Fournisseur)'
                ELSE 'Scénario 1 (Automatique)'
            END as source,
            COUNT(*) as count
        FROM documents
        GROUP BY source
    """)
    for row in cur.fetchall():
        print(f"   • {row[0]}: {row[1]}")
    
    # Détails des supplier_analyses
    if analysis_count > 0:
        print(f"\n🏭 Supplier Analyses:")
        cur.execute("""
            SELECT supplier_name, regulatory_risks_count, weather_risks_count, 
                   status, extra_metadata
            FROM supplier_analyses
        """)
        for row in cur.fetchall():
            meta = json.loads(row[4]) if row[4] else {}
            doc_ids = meta.get('document_ids', [])
            print(f"   • {row[0]}: {row[1]} réglementaires, {row[2]} météo")
            print(f"     Status: {row[3]}, Documents liés: {len(doc_ids)}")
    
    # Exemples de documents
    print(f"\n📑 Exemples de documents sauvegardés:")
    cur.execute("""
        SELECT title, event_subtype, 
               json_extract(extra_metadata, '$.celex_id') as celex,
               json_extract(extra_metadata, '$.supplier_analysis') as supplier
        FROM documents
        LIMIT 5
    """)
    for i, row in enumerate(cur.fetchall(), 1):
        title = row[0][:60] + "..." if len(row[0]) > 60 else row[0]
        source = f"Fournisseur: {row[3]}" if row[3] else "Auto"
        print(f"   {i}. [{row[1]}] {title}")
        print(f"      CELEX: {row[2]} | Source: {source}")
    
    conn.close()


async def main():
    """Exécuter les deux scénarios et vérifier"""
    print("\n" + "🚀" * 35)
    print("   TEST COMPLET AGENT 1A - DEUX SCÉNARIOS")
    print("🚀" * 35)
    print(f"\n📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = asyncio.get_event_loop().time()
    
    # Scénario 1
    result1 = await test_scenario_1()
    
    # Scénario 2
    result2 = await test_scenario_2()
    
    # Vérification BDD
    verify_database()
    
    total_time = asyncio.get_event_loop().time() - start_time
    
    # Résumé final
    print("\n" + "=" * 70)
    print("✅ TEST TERMINÉ")
    print("=" * 70)
    print(f"⏱️  Temps total: {total_time:.2f} secondes")
    print(f"\n📋 Résultats:")
    print(f"   • Scénario 1: {result1.get('status')}")
    print(f"   • Scénario 2: {result2.get('status')}")
    print("\n" + "🎉" * 35)


if __name__ == "__main__":
    asyncio.run(main())
