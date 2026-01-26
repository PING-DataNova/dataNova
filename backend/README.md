# Backend - Agent 1 Veille Réglementaire

**Python + FastAPI** - Agents IA de surveillance réglementaire

## 🚀 Installation

```bash
cd backend

# Installer uv (gestionnaire de dépendances)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Créer l'environnement virtuel
uv venv

# Activer l'environnement
source .venv/bin/activate  # macOS/Linux
# ou : .venv\Scripts\activate  # Windows

# Installer les dépendances
uv pip install -e .

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env et ajouter votre ANTHROPIC_API_KEY

# Créer la base de données
python scripts/init_db.py
```

## 📦 Structure

```
backend/
├── src/
│   ├── agent_1a/          # Collecte documents
│   ├── agent_1b/          # Analyse & scoring
│   ├── agent_2/           # Impact & recommandations
│   ├── orchestration/     # Coordination agents
│   ├── storage/           # Base de données
│   └── notifications/     # Alertes
│
├── config/                # Configurations JSON
├── data/                  # Données métier
├── tests/                 # Tests unitaires
├── docs/                  # Documentation
└── pyproject.toml         # Dépendances Python
```

## 🧪 Tests

```bash
# Lancer les tests
uv run pytest

# Avec couverture
uv run pytest --cov=src --cov-report=html
```

## 🏃 Exécution

```bash
# Mode manuel (une fois)
python -m src.main --run-once

# Mode scheduler (production)
python -m src.main

# Avec Docker
docker-compose up -d
```

## 📚 Documentation

- [DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) - Schéma de base de données
- [ROADMAP.md](ROADMAP.md) - Planning du projet
