#!/bin/bash
set -e

echo "🚀 Démarrage du backend DataNova..."

# Vérifier si alembic_version existe
echo "📋 Vérification de l'état des migrations..."

# Essayer d'exécuter les migrations
# Si la base existe déjà sans alembic_version, on stamp d'abord
if ! alembic current 2>/dev/null | grep -q "head"; then
    echo "⚠️  Migrations non initialisées, vérification des tables existantes..."
    
    # Tester si la base a déjà des tables (via Python)
    python3 -c "
from sqlalchemy import create_engine, inspect
import os

url = os.environ.get('DATABASE_URL', 'sqlite:///./data/datanova.db')
engine = create_engine(url)
inspector = inspect(engine)
tables = inspector.get_table_names()

if 'users' in tables and 'alembic_version' not in tables:
    print('STAMP_NEEDED')
elif 'alembic_version' in tables:
    print('ALREADY_MANAGED')
else:
    print('FRESH_DB')
" > /tmp/db_status.txt

    DB_STATUS=$(cat /tmp/db_status.txt)
    echo "   Status: $DB_STATUS"
    
    if [ "$DB_STATUS" = "STAMP_NEEDED" ]; then
        echo "📌 Tables existantes sans Alembic - Stamping à la dernière version..."
        alembic stamp head
    fi
fi

echo "📦 Exécution des migrations Alembic..."
alembic upgrade head

echo "✅ Migrations terminées, démarrage de l'API..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000
