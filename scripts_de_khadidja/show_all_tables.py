"""Script simple pour visualiser toutes les tables de datanova.db"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import SessionLocal, engine
from src.storage.models import Base
from sqlalchemy import inspect, text

def show_all_tables():
    """Afficher toutes les tables et leurs contenus."""
    
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    
    print("\n" + "=" * 100)
    print(f"BASE DE DONNÉES: datanova.db")
    print("=" * 100)
    print(f"\nTables disponibles: {len(table_names)}")
    for table in table_names:
        print(f"  - {table}")
    
    db = SessionLocal()
    
    try:
        # TABLE DOCUMENTS
        print("\n" + "=" * 100)
        print("TABLE: documents")
        print("=" * 100)
        
        result = db.execute(text("SELECT COUNT(*) FROM documents")).scalar()
        print(f"\nNombre total: {result} documents\n")
        
        docs = db.execute(text("""
            SELECT id, title, status, regulation_type 
            FROM documents 
            LIMIT 10
        """)).fetchall()
        
        print(f"{'ID (8 car.)':<12} {'Titre':<60} {'Status':<10} {'Type'}")
        print("-" * 100)
        for row in docs:
            print(f"{row[0][:8]:<12} {row[1][:58]:<60} {row[2]:<10} {row[3]}")
        
        # TABLE ANALYSES
        print("\n" + "=" * 100)
        print("TABLE: analyses")
        print("=" * 100)
        
        result = db.execute(text("SELECT COUNT(*) FROM analyses")).scalar()
        print(f"\nNombre total: {result} analyses\n")
        
        analyses = db.execute(text("""
            SELECT id, document_id, validation_status, is_relevant, confidence 
            FROM analyses 
            ORDER BY validation_status
        """)).fetchall()
        
        print(f"{'ID (8 car.)':<12} {'Doc ID (8 car.)':<14} {'Status':<12} {'Pertinent':<10} {'Confiance'}")
        print("-" * 100)
        for row in analyses:
            status = row[2]
            relevant = "Oui" if row[3] else "Non"
            print(f"{row[0][:8]:<12} {row[1][:8]:<14} {status:<12} {relevant:<10} {row[4]:.2f}")
        
        # Statistiques analyses
        stats = db.execute(text("""
            SELECT validation_status, COUNT(*) 
            FROM analyses 
            GROUP BY validation_status
        """)).fetchall()
        
        print("\nRépartition par statut:")
        for status, count in stats:
            print(f"  {status}: {count}")
        
        # TABLE COMPANY_PROFILES
        print("\n" + "=" * 100)
        print("TABLE: company_profiles")
        print("=" * 100)
        
        result = db.execute(text("SELECT COUNT(*) FROM company_profiles")).scalar()
        print(f"\nNombre total: {result} profils\n")
        
        if result > 0:
            profiles = db.execute(text("""
                SELECT id, name, industry_sector 
                FROM company_profiles 
                LIMIT 10
            """)).fetchall()
            
            print(f"{'ID (8 car.)':<12} {'Nom':<40} {'Secteur'}")
            print("-" * 100)
            for row in profiles:
                print(f"{row[0][:8]:<12} {row[1][:38]:<40} {row[2]}")
        else:
            print("  (Aucun profil enregistré)")
        
        # TABLE ALERTS
        print("\n" + "=" * 100)
        print("TABLE: alerts")
        print("=" * 100)
        
        result = db.execute(text("SELECT COUNT(*) FROM alerts")).scalar()
        print(f"\nNombre total: {result} alertes")
        
        if result > 0:
            alerts = db.execute(text("""
                SELECT id, alert_type, status, priority 
                FROM alerts 
                LIMIT 10
            """)).fetchall()
            
            print(f"\n{'ID (8 car.)':<12} {'Type':<20} {'Status':<12} {'Priorité'}")
            print("-" * 100)
            for row in alerts:
                print(f"{row[0][:8]:<12} {row[1]:<20} {row[2]:<12} {row[3]}")
        else:
            print("  (Aucune alerte)")
        
        # TABLE IMPACT_ASSESSMENTS
        print("\n" + "=" * 100)
        print("TABLE: impact_assessments")
        print("=" * 100)
        
        result = db.execute(text("SELECT COUNT(*) FROM impact_assessments")).scalar()
        print(f"\nNombre total: {result} évaluations d'impact")
        
        if result > 0:
            impacts = db.execute(text("""
                SELECT id, analysis_id, criticality, estimated_cost 
                FROM impact_assessments 
                LIMIT 10
            """)).fetchall()
            
            print(f"\n{'ID (8 car.)':<12} {'Analysis ID':<12} {'Criticité':<12} {'Coût estimé'}")
            print("-" * 100)
            for row in impacts:
                print(f"{row[0][:8]:<12} {row[1][:8]:<12} {row[2]:<12} {row[3]}")
        else:
            print("  (Aucune évaluation)")
        
        # TABLE EXECUTION_LOGS
        print("\n" + "=" * 100)
        print("TABLE: execution_logs")
        print("=" * 100)
        
        result = db.execute(text("SELECT COUNT(*) FROM execution_logs")).scalar()
        print(f"\nNombre total: {result} logs d'exécution")
        
        if result > 0:
            logs = db.execute(text("""
                SELECT id, agent_name, status, created_at 
                FROM execution_logs 
                ORDER BY created_at DESC
                LIMIT 5
            """)).fetchall()
            
            print(f"\n{'ID (8 car.)':<12} {'Agent':<20} {'Status':<12} {'Date'}")
            print("-" * 100)
            for row in logs:
                print(f"{row[0][:8]:<12} {row[1]:<20} {row[2]:<12} {str(row[3])[:19]}")
        else:
            print("  (Aucun log)")
        
        print("\n" + "=" * 100 + "\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    show_all_tables()
