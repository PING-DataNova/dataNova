#!/bin/bash
# =============================================================================
# Script de démarrage du backend DataNova
# 
# Gère les migrations Alembic puis lance le serveur uvicorn
# Variables d'environnement:
#   DATABASE_URL   - URL PostgreSQL (obligatoire en production)
#   RESET_DB       - Si "true", supprime et recrée toutes les tables (DANGER)
# =============================================================================

echo "============================================="
echo "  DataNova Backend - Démarrage"
echo "============================================="

# Vérifier que DATABASE_URL est défini en production
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL non défini, utilisation SQLite par défaut"
else
    echo "🗄️  PostgreSQL détecté"
fi

# --- Mode RESET (uniquement si explicitement demandé) ---
if [ "$RESET_DB" = "true" ]; then
    echo ""
    echo "🔴 RESET_DB=true → Suppression et recréation de toutes les tables"
    echo "   (Ceci est irréversible !)"
    
    if [ -n "$DATABASE_URL" ]; then
        python -c "
from sqlalchemy import create_engine, text
import os
engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    conn.execute(text('DROP SCHEMA public CASCADE'))
    conn.execute(text('CREATE SCHEMA public'))
    conn.commit()
print('✅ Schema public recréé')
" || echo "⚠️  Erreur lors du reset, on continue..."
    fi
    
    echo "📦 Application des migrations depuis zéro..."
    alembic upgrade head || { echo "❌ Alembic upgrade failed"; exit 1; }
    echo "✅ Toutes les migrations appliquées"
else
    # --- Mode normal: appliquer les migrations manquantes ---
    echo ""
    echo "📦 Application des migrations Alembic..."
    alembic upgrade head || { echo "❌ Alembic upgrade failed"; exit 1; }
    echo "✅ Migrations à jour"
fi

# --- Charger les données de référence (sites, fournisseurs, sources) ---
echo ""
echo "📂 Chargement des données initiales (seed)..."
python scripts/seed_database.py 2>&1 || echo "⚠️  seed_database.py: erreur ou données déjà présentes"

# --- Démarrer le serveur ---
echo ""
echo "🚀 Démarrage du serveur uvicorn..."
echo "============================================="
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000
