# Agent 1 - Veille Réglementaire Automatisée

**Projet PING** - Agent IA de surveillance et analyse réglementaire

## 📋 Vue d'ensemble

Système d'agents IA pour la veille réglementaire automatisée :
- **Agent 1A** : Collecte et extraction de documents réglementaires
- **Agent 1B** : Analyse de pertinence et génération d'alertes

### Réglementations surveillées
- 🎯 **Pilote** : CBAM (Carbon Border Adjustment Mechanism)
- 🔜 **Phase 2** : EUDR, CSRD, Sanctions, REACH, Export Control

## 🏗️ Architecture

```
src/
├── agent_1a/          # Collecte de données (Responsable: Dev 1)
├── agent_1b/          # Analyse & scoring (Responsable: Dev 2)
├── orchestration/     # Coordination agents (Responsable: Dev 3)
├── storage/           # Persistance données (Commun)
└── notifications/     # Alertes email (Commun)
```

## 🚀 Installation

### Prérequis
- Python 3.11+
- uv (gestionnaire de dépendances ultra-rapide)

### Setup

```bash
# 1. Cloner le repo
git clone https://github.com/PING-DataNova/backend_dataNova.git
cd backend_dataNova

# 2. Installer uv (si nécessaire)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Créer l'environnement virtuel
uv venv

# 4. Activer l'environnement
source .venv/bin/activate  # Linux/macOS
# ou : .venv\Scripts\activate  # Windows

# 5. Installer les dépendances (⚡ 10-100x plus rapide que pip/poetry)
uv pip install -e .

# 6. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env et ajouter votre ANTHROPIC_API_KEY

# 7. Créer la base de données
python -m src.storage.init_db
```

## 📦 Structure des données

```
data/
├── company_profiles/      # Profils entreprises (GMG, AeroRubber)
├── products/              # Catalogues produits
├── suppliers/             # Référentiel fournisseurs
├── customs_flows/         # Flux douaniers
├── risks/                 # Registre des risques
├── actions/               # Plans d'actions
├── kpis/                  # Indicateurs
├── documents/             # Politiques internes
└── sources_config.json    # Configuration des sources à surveiller
```

## 🧪 Tests

```bash
# Lancer tous les tests
uv run pytest

# Tests avec couverture
uv run pytest --cov=src --cov-report=html

# Tests d'un module spécifique
uv run pytest tests/agent_1a/
```

## 🔧 Développement

### Organisation du travail (3 développeurs)

| Développeur | Module | Responsabilité |
|-------------|--------|----------------|
| **Dev 1** | `agent_1a/` | Scraping, téléchargement, extraction PDF |
| **Dev 2** | `agent_1b/` | Filtrage, analyse LLM, scoring |
| **Dev 3** | `orchestration/` | Scheduling, pipeline, coordination |

### Workflow Git

```bash
# Créer une branche pour votre module
git checkout -b feature/agent-1a-scraper

# Travailler sur votre code
# ...

# Committer
git add .
git commit -m "feat(agent-1a): implement CBAM page scraper"

# Pousser et créer une Pull Request
git push origin feature/agent-1a-scraper
```

### Convention de nommage

- **Branches** : `feature/module-description`, `fix/issue-description`
- **Commits** : Convention Conventional Commits
  - `feat(scope): description`
  - `fix(scope): description`
  - `docs(scope): description`

## 🏃 Exécution

### Mode manuel (développement)

```bash
# Lancer l'agent une fois
python -m src.main --run-once

# Lancer avec logging détaillé
python -m src.main --log-level DEBUG
```

### Mode scheduler (production)

```bash
# Démarrer le scheduler (exécution hebdomadaire automatique)
python -m src.main

# Avec Docker
docker-compose up -d
```

## 📧 Notifications

Les alertes sont envoyées par email aux destinataires configurés dans `.env` :
- Format JSON structuré
- Score de pertinence (0-1)
- Niveau de criticité (CRITICAL/HIGH/MEDIUM/LOW)
- Actions recommandées

## 📊 Monitoring

Logs disponibles dans `logs/agent.log` :
- Exécutions planifiées
- Documents collectés
- Analyses effectuées
- Erreurs et warnings

## 🗺️ Roadmap

Voir le fichier [ROADMAP.md](./ROADMAP.md) pour le planning détaillé sur 4 semaines et la répartition des tâches entre les 3 développeurs.

**Sprint actuel** : Semaine 1 - Setup & Agent 1A Core

## 🤝 Contribution

1. Créer une branche depuis `main`
2. Développer votre fonctionnalité
3. Ajouter des tests
4. Créer une Pull Request
5. Revue de code par les pairs

## 📝 Licence

Projet académique - PING DataNova

## 👥 Équipe

- Développeur 1 : Agent 1A
- Développeur 2 : Agent 1B
- Développeur 3 : Orchestration