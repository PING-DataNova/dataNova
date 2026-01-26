# DataNova - Agent 1 & Frontend

**Projet PING** - Monorepo Agent IA de surveillance réglementaire + Interface Juridique

## 📁 Structure du projet

```
dataNova/
├── frontend/              # Interface React juridique
│   ├── src/              # Code source TypeScript/React
│   ├── tests/            # Tests Playwright
│   └── package.json      # Dépendances frontend
│
├── src/                  # Backend Python - Agents IA
│   ├── agent_1a/        # Collecte de documents
│   ├── agent_1b/        # Analyse & scoring
│   └── orchestration/   # Coordination
│
├── data/                 # Données métier
└── config/              # Configuration
```

---

# 🤖 Backend - Agent 1 - Veille Réglementaire Automatisée

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

---

# Frontend PING - Équipe Juridique

## Connexion à l'Application

### Profils de Test

**Interface Juridique :**
- Email : `juriste@hutchinson.com` 
- Mot de passe : n'importe lequel (mode démo)

**Dashboard Décideur :**
- Email : `decideur@hutchinson.com`
- Mot de passe : n'importe lequel (mode démo)

### Démarrage

```bash
npm install
npm run dev
```

Accès : http://localhost:3005

## Connexion Frontend/Backend

### Configuration pour les développeurs Backend

Le frontend communique avec votre API via ces endpoints :

#### Endpoints Réglementations
```
GET    /api/regulations                    # Liste des réglementations
PUT    /api/regulations/:id/status         # Mettre à jour le statut
GET    /api/regulations/:id                # Détails d'une réglementation
GET    /api/regulations/stats              # Statistiques
```

#### Endpoints Authentification (optionnel)
```
POST   /api/auth/login                     # Connexion
POST   /api/auth/logout                    # Déconnexion
GET    /api/auth/me                        # Utilisateur actuel
```

### Structure des données attendues

#### Regulation Object
```typescript
interface Regulation {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'validated' | 'rejected' | 'to-review';
  type: string;
  dateCreated: Date;
  reference?: string;
}
```

#### API Response Format
```typescript
// GET /api/regulations
{
  "regulations": Regulation[],
  "total": number,
  "page": number,
  "limit": number
}

// PUT /api/regulations/:id/status
{
  "status": "validated" | "rejected" | "to-review",
  "comment": string (optionnel)
}
```

### Configuration du Frontend

1. **Copiez le fichier d'environnement :**
   ```bash
   cp .env.example .env.local
   ```

2. **Modifiez `.env.local` avec l'URL de votre backend :**
   ```
   VITE_API_BASE_URL=http://localhost:VOTRE_PORT/api
   ```

3. **Démarrez le frontend :**
   ```bash
   npm install
   npm run dev
   ```

### CORS Configuration

Pour éviter les erreurs CORS, configurez votre backend pour accepter les requêtes depuis :
- `http://localhost:3000` (dev frontend)
- `http://localhost:3005` (si port 3000 occupé)

#### Exemple Express.js :
```javascript
const cors = require('cors');
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:3005'],
  credentials: true
}));
```

#### Exemple FastAPI (Python) :
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3005"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Tests et Debuggage

- **Activer les logs** : `VITE_DEBUG=true` dans `.env.local`
- **Tester les endpoints** : Utilisez Postman ou curl
- **Vérifier la console** : F12 → Console pour voir les requêtes API

### Contact

Frontend: [Votre nom]
Backend: [Noms de vos collègues]
