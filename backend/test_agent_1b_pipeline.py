"""
Test du pipeline Agent 1B
==========================

Ce script teste le pipeline automatique de l'Agent 1B qui :
1. Lit tous les documents non analysés depuis la table documents
2. Analyse chaque document pour déterminer la pertinence
3. Identifie les sites et fournisseurs affectés
4. Sauvegarde les résultats dans pertinence_checks
"""

import sys
sys.path.insert(0, '/Users/noradossou-gbete/Documents/Projet_PING/Datanova_perso/dataNova/backend')

from src.agent_1b.agent import run_agent_1b_pipeline
from src.storage.database import get_session
from src.storage.models import Document, PertinenceCheck
import sqlite3


def print_database_stats():
    """Affiche les statistiques de la base de données"""
    conn = sqlite3.connect('data/datanova.db')
    cur = conn.cursor()
    
    # Compter les documents
    cur.execute("SELECT COUNT(*) FROM documents")
    doc_count = cur.fetchone()[0]
    
    # Compter les pertinence_checks
    cur.execute("SELECT COUNT(*) FROM pertinence_checks")
    check_count = cur.fetchone()[0]
    
    # Documents non analysés
    cur.execute("""
        SELECT COUNT(*) FROM documents d
        LEFT JOIN pertinence_checks p ON d.id = p.document_id
        WHERE p.id IS NULL
    """)
    unprocessed = cur.fetchone()[0]
    
    print("\n📊 ÉTAT DE LA BASE DE DONNÉES")
    print("=" * 70)
    print(f"   Documents totaux:        {doc_count}")
    print(f"   Analyses (pertinence):   {check_count}")
    print(f"   Documents non analysés:  {unprocessed}")
    print("=" * 70)
    
    conn.close()


def main():
    """Point d'entrée principal"""
    print("\n" + "=" * 70)
    print("🔄 PIPELINE AGENT 1B - TRAITEMENT AUTOMATIQUE")
    print("=" * 70)
    
    # Afficher l'état initial
    print_database_stats()
    
    # Exécuter le pipeline
    print("\n🚀 Démarrage du pipeline...\n")
    result = run_agent_1b_pipeline(batch_size=50)
    
    # Afficher les résultats
    print("\n" + "=" * 70)
    print("✅ PIPELINE TERMINÉ")
    print("=" * 70)
    print(f"   Documents traités:       {result['documents_processed']}")
    print(f"   Analyses créées:         {result['pertinence_checks_created']}")
    print(f"   Erreurs:                 {len(result['errors'])}")
    
    if result['errors']:
        print("\n⚠️  ERREURS:")
        for error in result['errors'][:5]:  # Afficher max 5 erreurs
            print(f"   - {error['doc_id']}: {error['error']}")
    
    # Afficher l'état final
    print_database_stats()
    
    # Afficher quelques exemples d'analyses
    print("\n📋 EXEMPLES D'ANALYSES CRÉÉES:")
    print("=" * 70)
    
    conn = sqlite3.connect('data/datanova.db')
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            p.document_id,
            d.title,
            p.decision,
            p.confidence,
            json_array_length(p.affected_sites) as sites,
            json_array_length(p.affected_suppliers) as suppliers
        FROM pertinence_checks p
        JOIN documents d ON p.document_id = d.id
        ORDER BY p.created_at DESC
        LIMIT 5
    """)
    
    for row in cur.fetchall():
        doc_id, title, decision, confidence, sites, suppliers = row
        title_short = title[:60] + "..." if len(title) > 60 else title
        print(f"\n   {title_short}")
        print(f"   Décision: {decision} | Confiance: {confidence:.2f}")
        print(f"   Sites: {sites or 0} | Fournisseurs: {suppliers or 0}")
    
    conn.close()
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
