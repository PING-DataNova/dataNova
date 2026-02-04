#!/bin/bash
set -e

echo "🚀 Démarrage du backend DataNova..."

# Reset complet de la base si RESET_DB=true
if [ "$RESET_DB" = "true" ]; then
    echo "⚠️  RESET_DB=true - Suppression de toutes les tables..."
    python3 -c "
from sqlalchemy import create_engine, text
import os

url = os.environ.get('DATABASE_URL')
if url:
    engine = create_engine(url)
    with engine.connect() as conn:
        conn.execute(text('DROP SCHEMA public CASCADE'))
        conn.execute(text('CREATE SCHEMA public'))
        conn.commit()
    print('✅ Base de données réinitialisée')
"
fi

echo "📦 Exécution des migrations Alembic..."
alembic upgrade head

echo "✅ Migrations terminées, démarrage de l'API..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000
