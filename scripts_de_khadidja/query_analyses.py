#!/usr/bin/env python
"""Script pour interroger directement la table analyses"""

import sqlite3
from pathlib import Path

# Connexion à la base de données
db_path = Path(__file__).parent.parent / "datanova.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("\n" + "=" * 120)
print("📊 TABLE analyses - Vue détaillée")
print("=" * 120)

# Récupérer toutes les analyses avec leurs informations
cursor.execute("""
    SELECT 
        a.id,
        SUBSTR(a.document_id, 1, 8) as doc_id_short,
        a.validation_status,
        a.is_relevant,
        a.confidence,
        SUBSTR(d.title, 1, 60) as title
    FROM analyses a
    LEFT JOIN documents d ON a.document_id = d.id
    ORDER BY 
        CASE a.validation_status 
            WHEN 'approved' THEN 1
            WHEN 'pending' THEN 2
            WHEN 'rejected' THEN 3
        END,
        a.created_at
""")

results = cursor.fetchall()

# En-têtes
print(f"\n{'ID (8 premiers car.)':<20} {'Doc ID':<10} {'Status':<12} {'Pertinent':<10} {'Conf.':<8} {'Titre du document'}")
print("-" * 120)

# Données
for row in results:
    id_short = row[0][:8]
    doc_id = row[1] if row[1] else "N/A"
    status = row[2]
    relevant = "✓ Oui" if row[3] else "✗ Non"
    confidence = f"{row[4]:.2f}"
    title = row[5] if row[5] else "N/A"
    
    # Emoji selon le statut
    status_emoji = {
        'approved': '✅',
        'pending': '⏳',
        'rejected': '❌'
    }.get(status, '❓')
    
    print(f"{id_short:<20} {doc_id:<10} {status_emoji} {status:<10} {relevant:<10} {confidence:<8} {title}")

# Statistiques
print("\n" + "=" * 120)
print("📈 STATISTIQUES PAR STATUT")
print("=" * 120)

cursor.execute("""
    SELECT validation_status, COUNT(*) 
    FROM analyses 
    GROUP BY validation_status
    ORDER BY validation_status
""")

stats = cursor.fetchall()
total = sum(count for _, count in stats)

for status, count in stats:
    emoji = {'approved': '✅', 'pending': '⏳', 'rejected': '❌'}.get(status, '❓')
    percentage = (count / total * 100) if total > 0 else 0
    print(f"{emoji} {status.upper():<12} : {count:>2} analyses ({percentage:>5.1f}%)")

print(f"\n📊 TOTAL: {total} analyses")

# Détails de l'analyse approuvée récemment
print("\n" + "=" * 120)
print("🔍 DERNIÈRE ANALYSE APPROUVÉE")
print("=" * 120)

cursor.execute("""
    SELECT 
        a.id,
        d.title,
        a.confidence,
        a.llm_reasoning
    FROM analyses a
    LEFT JOIN documents d ON a.document_id = d.id
    WHERE a.validation_status = 'approved'
    ORDER BY a.created_at DESC
    LIMIT 1
""")

last_approved = cursor.fetchone()
if last_approved:
    print(f"\nID: {last_approved[0]}")
    print(f"Document: {last_approved[1]}")
    print(f"Confiance: {last_approved[2]:.2f}")
    print(f"Raisonnement: {last_approved[3][:200]}...")

conn.close()
print("\n" + "=" * 120 + "\n")
