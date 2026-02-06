# 📘 Documentation Technique — Projet PING DataNova

**Version :** 1.0  
**Date :** 06 février 2026  
**Client :** Hutchinson (Groupe TotalEnergies)  
**Équipe :** ESIGELEC PING — DataNova  

---

## Table des matières

1. [Vue d'ensemble du projet](#1-vue-densemble-du-projet)
2. [Architecture technique](#2-architecture-technique)
3. [Stack technologique](#3-stack-technologique)
4. [Backend — API FastAPI](#4-backend--api-fastapi)
5. [Agents IA — Pipeline de traitement](#5-agents-ia--pipeline-de-traitement)
6. [Base de données — Schéma complet](#6-base-de-données--schéma-complet)
7. [Frontend — Interface React](#7-frontend--interface-react)
8. [Orchestration LangGraph](#8-orchestration-langgraph)
9. [Système de notifications](#9-système-de-notifications)
10. [API REST — Référence complète](#10-api-rest--référence-complète)
11. [Configuration et variables d'environnement](#11-configuration-et-variables-denvironnement)
12. [Déploiement](#12-déploiement)
13. [Guide d'installation](#13-guide-dinstallation)
14. [Tests](#14-tests)
15. [Annexes](#15-annexes)

---

## 1. Vue d'ensemble du projet

### 1.1 Objectif

DataNova PING est une **plateforme intelligente de surveillance proactive des risques supply chain** développée pour Hutchinson. Elle collecte automatiquement des informations depuis des sources officielles (réglementaires, météorologiques, géopolitiques), analyse leur pertinence, évalue l'impact sur les sites et fournisseurs, et génère des alertes avec recommandations actionnables.

### 1.2 Principes de fonctionnement

```
Sources externes (EUR-Lex, Open-Meteo)
              ↓
       [SCHEDULER CRON]
              ↓
       [AGENT 1A] — Collecte de documents + alertes météo
              ↓
       [AGENT 1B] — Analyse de pertinence (100% LLM)
              ↓
         OUI / PARTIELLEMENT → [AGENT 2] — Analyse d'impact 360°
         NON → FIN (archivé)
              ↓
       [LLM JUDGE] — Score de confiance qualité
              ↓
         Score ≥ 7.0 → APPROVE → Notification email
         Score < 7.0 → REJECT → Archivé
              ↓
       [BASE DE DONNÉES] — Rapports stockés
              ↓
       [DASHBOARD FRONTEND] — Visualisation temps réel
```

### 1.3 Périmètre fonctionnel

| Module | Description | Statut |
|--------|-------------|--------|
| Agent 1A (Collecte) | Collecte EUR-Lex + Open-Meteo | ✅ Opérationnel |
| Agent 1B (Pertinence) | Scoring 100% LLM sémantique | ✅ Opérationnel |
| Agent 2 (Impact) | Analyse 360° + Business Interruption | ✅ Opérationnel |
| LLM Judge | Validation qualité automatique | ✅ Opérationnel |
| Orchestration | Pipeline LangGraph + APScheduler | ✅ Opérationnel |
| Notifications | Email via Brevo (Sendinblue) | ✅ Opérationnel |
| Frontend | Dashboard React + TypeScript | ✅ Opérationnel |
| API REST | FastAPI — 69 endpoints | ✅ Opérationnel |
| Base de données | SQLite (dev) / PostgreSQL (prod) | ✅ Opérationnel |
| Déploiement | Docker + Terraform (Azure) | ✅ Prêt |

---

## 2. Architecture technique

### 2.1 Architecture globale

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
│  Port 3000 (dev) / Port 80 (prod via Nginx)                    │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Dashboard │ │ Admin     │ │ Supplier │ │ Agent Dashboard  │ │
│  │           │ │ Panel     │ │ Analysis │ │                  │ │
│  └──────────┘ └───────────┘ └──────────┘ └──────────────────┘ │
│                         │                                       │
│              Proxy Vite /api → localhost:8000                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP REST (JSON)
┌─────────────────────────┴───────────────────────────────────────┐
│                     BACKEND (FastAPI)                            │
│  Port 8000                                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API Routes                             │   │
│  │  /api/regulations  /api/impacts  /api/pipeline            │   │
│  │  /api/admin        /api/supplier /api/subscriptions       │   │
│  │  /api/auth         /api/documents                         │   │
│  └──────────────┬───────────────────────────────────────────┘   │
│                 │                                                │
│  ┌──────────────┴───────────────────────────────────────────┐   │
│  │              ORCHESTRATION (LangGraph)                     │   │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌───────┐  ┌──────────┐ │   │
│  │  │ 1A   │→ │ 1B   │→ │  2   │→ │ Judge │→ │ Notif.   │ │   │
│  │  └──────┘  └──────┘  └──────┘  └───────┘  └──────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                 │                                                │
│  ┌──────────────┴───────────────────────────────────────────┐   │
│  │             STORAGE (SQLAlchemy + Alembic)                │   │
│  │  SQLite (dev) ←──→ PostgreSQL (prod)                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
   ┌──────────┐    ┌───────────┐    ┌──────────┐
   │ EUR-Lex  │    │ Open-Meteo│    │  Brevo   │
   │ SOAP API │    │ REST API  │    │ Email API│
   └──────────┘    └───────────┘    └──────────┘
```

### 2.2 Organisation des dossiers

```
dataNova/
├── backend/                     # Backend Python
│   ├── src/
│   │   ├── api/                 # API FastAPI
│   │   │   ├── main.py          # Point d'entrée app
│   │   │   └── routes/          # 8 fichiers de routes
│   │   ├── agent_1a/            # Agent 1A — Collecte
│   │   │   ├── agent.py         # Logique principale (2979 lignes)
│   │   │   ├── data_sources.py  # Gestion sources de données
│   │   │   └── tools/           # Outils (scraper, PDF, météo)
│   │   ├── agent_1b/            # Agent 1B — Pertinence
│   │   │   └── agent.py         # Scoring 100% LLM (1114 lignes)
│   │   ├── agent_2/             # Agent 2 — Analyse d'impact
│   │   │   ├── agent.py         # Orchestrateur 360° (2699 lignes)
│   │   │   ├── geographic_engine.py
│   │   │   ├── weather_risk_engine.py
│   │   │   ├── criticality_analyzer.py
│   │   │   ├── regulatory_geopolitical_engine.py
│   │   │   └── llm_reasoning.py
│   │   ├── llm_judge/           # Agent 3 — Validation qualité
│   │   │   ├── judge.py
│   │   │   ├── criteria_evaluator.py
│   │   │   ├── prompts.py
│   │   │   └── weights_config.py
│   │   ├── orchestration/       # Workflow LangGraph
│   │   │   ├── langgraph_workflow.py  # Pipeline complet (1611 lignes)
│   │   │   ├── pipeline.py
│   │   │   └── scheduler.py
│   │   ├── notifications/       # Système de notifications
│   │   │   ├── notification_service.py
│   │   │   ├── email_sender.py
│   │   │   ├── router.py
│   │   │   └── subscription_filter.py
│   │   ├── storage/             # Couche données
│   │   │   ├── database.py      # Configuration SQLAlchemy
│   │   │   ├── models.py        # 20 modèles (840 lignes)
│   │   │   └── repositories.py
│   │   ├── config.py            # Configuration Pydantic Settings
│   │   └── risk_categories.py   # Service catégories de risques
│   ├── config/                  # Fichiers de configuration JSON
│   ├── data/                    # Données runtime (BDD, PDFs, profils)
│   ├── alembic/                 # Migrations de base de données
│   ├── tests/                   # Tests unitaires et d'intégration
│   ├── pyproject.toml           # Dépendances Python
│   ├── Dockerfile               # Image Docker backend
│   └── .env                     # Variables d'environnement (non versionné)
│
├── frontend/                    # Frontend React
│   ├── src/
│   │   ├── pages/               # 7 pages
│   │   ├── components/          # 9 composants réutilisables
│   │   ├── services/            # 7 services API
│   │   ├── config/              # Configuration app
│   │   ├── types/               # Types TypeScript
│   │   ├── hooks/               # Custom hooks
│   │   └── App.tsx              # Composant racine
│   ├── package.json             # Dépendances Node.js
│   ├── vite.config.ts           # Configuration Vite + proxy
│   ├── Dockerfile               # Image Docker frontend
│   └── nginx.conf               # Configuration Nginx (prod)
│
├── terraform/                   # Infrastructure as Code (Azure)
├── docker-compose.yml           # Orchestration Docker
└── deploy.sh                    # Script de déploiement
```

---

## 3. Stack technologique

### 3.1 Backend

| Technologie | Version | Usage |
|-------------|---------|-------|
| **Python** | ≥ 3.11 | Langage principal |
| **FastAPI** | ≥ 0.128 | Framework API REST |
| **Uvicorn** | ≥ 0.40 | Serveur ASGI |
| **SQLAlchemy** | ≥ 2.0 | ORM base de données |
| **Alembic** | ≥ 1.13 | Migrations BDD |
| **LangChain** | ≥ 0.3 | Framework LLM |
| **LangGraph** | ≥ 1.0.5 | Orchestration workflow |
| **APScheduler** | ≥ 3.10 | Planification tâches |
| **Pydantic** | ≥ 2.8 | Validation données |
| **Structlog** | ≥ 24.4 | Logging structuré |
| **Anthropic SDK** | — | API Claude (LLM) |
| **OpenAI SDK** | — | API GPT (Judge) |
| **httpx** | ≥ 0.27 | Client HTTP async |
| **BeautifulSoup4** | ≥ 4.12 | Parsing HTML |
| **pdfplumber** | ≥ 0.11 | Extraction PDF |
| **PyMuPDF** | ≥ 1.24 | Extraction PDF avancée |
| **Brevo SDK** | — | Envoi d'emails |

### 3.2 Frontend

| Technologie | Version | Usage |
|-------------|---------|-------|
| **React** | 18.2 | Framework UI |
| **TypeScript** | 5.2 | Typage statique |
| **Vite** | 5.0 | Build tool + dev server |
| **Leaflet** | 1.9 | Cartes interactives |
| **Recharts** | 2.6 | Graphiques et charts |
| **Lucide React** | 0.292 | Icônes |
| **jsPDF** | 4.1 | Export PDF |
| **html2canvas** | 1.4 | Capture d'écran |
| **Playwright** | 1.57 | Tests E2E |

### 3.3 Infrastructure

| Technologie | Usage |
|-------------|-------|
| **Docker** | Conteneurisation |
| **Docker Compose** | Orchestration locale |
| **PostgreSQL 16** | BDD production |
| **SQLite** | BDD développement |
| **Nginx** | Reverse proxy frontend |
| **Terraform** | Infrastructure as Code Azure |
| **Azure Static Web Apps** | Hébergement frontend |

### 3.4 LLMs utilisés

| Agent | Provider | Modèle | Usage |
|-------|----------|--------|-------|
| Agent 1B | Anthropic | `claude-sonnet-4-20250514` | Analyse de pertinence |
| Agent 2 | Anthropic | `claude-sonnet-4-20250514` | Génération de rapports |
| LLM Judge | OpenAI | `gpt-4o-mini` | Validation qualité |

---

## 4. Backend — API FastAPI

### 4.1 Point d'entrée

**Fichier :** `backend/src/api/main.py`

```python
app = FastAPI(
    title="DataNova API",
    description="API de veille réglementaire pour Hutchinson SA",
    version="1.0.0"
)
```

**Cycle de vie (Lifespan) :**
- **Startup :** Initialisation du scheduler automatique (APScheduler)
- **Shutdown :** Arrêt propre du scheduler

**CORS :** Configuré pour accepter les origines `localhost:3000-3007`, `localhost:5173`, et `*.azurestaticapps.net`.

**Routes enregistrées :**

| Router | Préfixe | Fichier |
|--------|---------|---------|
| Auth | `/api/auth` | `routes/auth.py` |
| Regulations | `/api/regulations` | `routes/analyses.py` |
| Impacts | `/api/impacts` | `routes/impacts.py` |
| Pipeline | `/api/pipeline` | `routes/pipeline.py` |
| Supplier | `/api/supplier` | `routes/supplier.py` |
| Admin | `/api/admin` | `routes/admin.py` |
| Documents | `/api/documents` | `routes/documents.py` |
| Subscriptions | `/api/subscriptions` | `routes/subscriptions.py` |

### 4.2 Endpoints utilitaires

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/` | Informations API (nom, version, status) |
| `GET` | `/health` | Health check pour monitoring |
| `GET` | `/docs` | Documentation OpenAPI Swagger |

---

## 5. Agents IA — Pipeline de traitement

### 5.1 Agent 1A — Collecte de documents

**Fichier principal :** `backend/src/agent_1a/agent.py` (2979 lignes)

#### Rôle
Collecte automatique de documents depuis des sources officielles :
- **EUR-Lex** : Réglementations européennes (API SOAP)
- **Open-Meteo** : Alertes météorologiques (API REST, prévisions 16 jours)

#### Fonctionnalités

| Fonctionnalité | Description | Fichier |
|----------------|-------------|---------|
| Collecte EUR-Lex | Recherche par mots-clés et domaines via API SOAP | `tools/scraper.py` |
| Extraction texte | Parsing HTML + extraction PDF (pdfplumber, PyMuPDF) | `tools/pdf_extractor.py` |
| Détection codes NC | Extraction automatique des codes nomenclature combinée | `tools/scraper.py` |
| Collecte météo | Prévisions 16j pour tous les sites et fournisseurs | `tools/weather.py` |
| Gestion sources | Activation/désactivation des sources via admin | `data_sources.py` |
| Déduplication | Hash SHA-256 pour éviter les doublons | `agent.py` |

#### Modes de fonctionnement

1. **Collecte automatique complète** (`run_agent_1a_full_collection`) :
   - Lit le profil entreprise (JSON)
   - Extrait les mots-clés pertinents
   - Recherche EUR-Lex avec ces mots-clés
   - Télécharge et extrait les PDFs
   - Collecte la météo pour tous les sites (BDD)
   - Sauvegarde en base

2. **Collecte par mot-clé** (`run_agent_1a`) :
   - Recherche ciblée par mot-clé unique (ex: "CBAM")

#### Paramètres configurables

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `max_documents` | 8 | Documents max par collecte |
| `max_keywords` | 8 | Mots-clés LLM générés |
| `min_publication_year` | 2000 | Année minimum de publication |

#### Données de sortie

Chaque document collecté est stocké avec :
- `title`, `source_url`, `celex_id`
- `event_type` : "regulation", "climate", "geopolitical"
- `content` : Texte extrait du PDF/HTML
- `summary` : Résumé auto-généré
- `geographic_scope` : Pays/régions concernés (JSON)
- `hash_sha256` : Hash pour détection de changements

---

### 5.2 Agent 1B — Analyse de pertinence

**Fichier principal :** `backend/src/agent_1b/agent.py` (1114 lignes)

#### Rôle
Détermine si un document collecté est pertinent pour Hutchinson et identifie les entités affectées (sites + fournisseurs).

#### Architecture multi-type

| Type d'événement | Méthode d'analyse |
|------------------|-------------------|
| **Réglementaire** | 100% LLM sémantique (Claude) |
| **Climatique** | Distance géographique (Haversine) |
| **Géopolitique** | Correspondance pays/région |

#### Analyse réglementaire (100% LLM)

L'analyse réglementaire utilise une approche **100% LLM sémantique**. Les analyses par mots-clés et codes NC sont conservées uniquement pour le reporting et la traçabilité.

```
Score final = score_sémantique_LLM (0.0 à 1.0)

Décision :
  ≥ 0.6 → OUI (pertinent)
  ≥ 0.4 → PARTIELLEMENT
  < 0.4 → NON
```

Le LLM reçoit :
- Le titre et contenu du document
- Le profil Hutchinson (secteurs, produits, pays, codes NC)
- Des instructions pour évaluer la pertinence

**Retour :** `is_pertinent`, `pertinence_score`, `reasoning`, `matched_products`, `matched_countries`, `matched_sectors`

#### Analyse climatique (Haversine)

```
Distance < 50 km  → OUI (impact direct)
Distance 50-200 km → PARTIELLEMENT (impact indirect)
Distance > 200 km  → NON
```

#### Analyse géopolitique

Correspondance par pays et régions entre l'événement et les entités Hutchinson, avec prise en compte des pays voisins.

#### Données de sortie

| Champ | Type | Description |
|-------|------|-------------|
| `decision` | String | OUI / NON / PARTIELLEMENT |
| `confidence` | Float | Score de confiance 0.0–1.0 |
| `reasoning` | Text | Explication détaillée |
| `affected_sites` | JSON | Liste des IDs sites concernés |
| `affected_suppliers` | JSON | Liste des IDs fournisseurs concernés |
| `matched_elements` | JSON | Détails des correspondances |

---

### 5.3 Agent 2 — Analyse d'impact 360°

**Fichier principal :** `backend/src/agent_2/agent.py` (2699 lignes)

#### Rôle
Analyse complète de l'impact d'un événement sur CHAQUE site et fournisseur individuellement, calcule des scores de risque sophistiqués, et génère des recommandations actionnables.

#### Architecture modulaire

```
Agent 2 (Orchestrateur)
   ├── GeographicEngine         — Projection Haversine (événements climatiques)
   ├── RegulatoryEngine         — Projection réglementaire (pays/secteur/produit)
   ├── GeopoliticalEngine       — Projection géopolitique (conflits/sanctions)
   ├── CriticalityAnalyzer      — Analyse de criticité supply chain
   ├── WeatherRiskEngine        — Agrégation risques météo
   └── LLMReasoning             — Génération recommandations (Claude/GPT)
```

#### Sous-modules

| Module | Fichier | Lignes | Description |
|--------|---------|--------|-------------|
| Geographic Engine | `geographic_engine.py` | 292 | Projection Haversine, zones d'impact : critique (<10km), fort (<50km), moyen (<100km), faible (<200km) |
| Weather Risk Engine | `weather_risk_engine.py` | 567 | Lecture `weather_alerts`, score climat par entité. Sévérité : critical=1.0, high=0.8, medium=0.5, low=0.2 |
| Criticality Analyzer | `criticality_analyzer.py` | 398 | Évalue criticité supply chain : fournisseur unique, importance stratégique, délais remplacement |
| Regulatory Engine | `regulatory_geopolitical_engine.py` | 399 | Projection réglementaire par pays/secteur/produit, projection géopolitique (conflits) |
| LLM Reasoning | `llm_reasoning.py` | 719 | Génération recommandations en cascade. Provider configurable : Anthropic (Claude) ou OpenAI (GPT-4o) |

#### Normalisation event_type

Agent 1A stocke les `event_type` en anglais. Agent 2 travaille en français. Une normalisation est appliquée à l'entrée de la méthode `analyze()` :

```python
event_type_mapping = {
    "regulation": "reglementaire",
    "regulatory": "reglementaire",
    "climate": "climatique",
    "weather": "climatique",
    "geopolitical": "geopolitique",
    "geopolitic": "geopolitique",
}
```

#### Score de risque 360°

```
risk_score_360 = 0.30 × severity + 0.25 × probability + 0.25 × exposure + 0.20 × urgency
```

| Sous-score | Poids | Description |
|------------|-------|-------------|
| **Severity** | 30% | Gravité de l'événement (type, amplitude) |
| **Probability** | 25% | Probabilité d'impact sur l'entité (distance, correspondance) |
| **Exposure** | 25% | Exposition de l'entité (fournisseur unique, volume, criticité) |
| **Urgency** | 20% | Urgence d'action (dates limites, délais de conformité) |

**Ajustement météo :** +15% max si alertes météo actives sur la zone.

#### Business Interruption Score

Calcul de l'impact financier réel par entité :
- **Jours de perturbation estimés** (par type d'événement)
- **Impact CA** : basé sur `daily_revenue`, `daily_delivery_value`
- **Couverture stock** : `stock_coverage_days`, `safety_stock_days`
- **Capacité de repli** : `backup_production_sites`, `switch_time_days`
- **Pénalités contractuelles** : `contract_penalties_per_day`

#### Niveaux de risque

| Score 360° | Niveau | Couleur |
|------------|--------|---------|
| 0–25 | FAIBLE | 🟢 Vert |
| 25–50 | MOYEN | 🟡 Jaune |
| 50–75 | ÉLEVÉ | 🟠 Orange |
| 75–100 | CRITIQUE | 🔴 Rouge |

#### Rapport détaillé généré (7 sections LLM)

1. **Contexte et enjeux** — Situation et implications
2. **Entités affectées** — Liste complète sites + fournisseurs
3. **Analyse financière** — Impact chiffré
4. **Recommandations** — Actions concrètes priorisées
5. **Timeline** — Planning d'actions
6. **Matrice de priorisation** — Urgence × Impact
7. **Scénario d'inaction** — Conséquences si rien n'est fait

---

### 5.4 LLM Judge — Agent 3

**Fichier principal :** `backend/src/llm_judge/judge.py` (249 lignes)

#### Rôle
Évalue la qualité des analyses produites par les Agents 1B et 2, détermine un score de confiance global, et décide de la publication automatique.

#### Critères d'évaluation

| Critère | Description |
|---------|-------------|
| **Completeness** | Analyse complète de tous les aspects |
| **Accuracy** | Exactitude des informations |
| **Relevance** | Pertinence par rapport au profil entreprise |
| **Clarity** | Clarté et lisibilité du rapport |
| **Actionability** | Recommandations concrètes et applicables |
| **Traceability** | Sources citées et vérifiables |

#### Processus d'évaluation

1. **Évaluation Agent 1B (Pertinence)** — Score pondéré par critères
2. **Pause 5 secondes** — Éviter le rate limit API
3. **Évaluation Agent 2 (Impact)** — Score pondéré par critères
4. **Score global** = moyenne des deux scores pondérés
5. **Décision** via LLM ou règles de fallback

#### Règles de décision

| Condition | Action |
|-----------|--------|
| Score ≥ 8.5 et confiance ≥ 0.85 | **APPROVE** → Publication + Email |
| Score ≥ 7.0 et confiance ≥ 0.80 | **REVIEW** → Relecture humaine |
| Score ≥ 7.0 et confiance < 0.80 | **REVIEW_PRIORITY** → Relecture urgente |
| Score < 7.0 | **REJECT** → Archivé, non publié |

#### Configuration

Le Judge utilise **OpenAI GPT-4o-mini** par défaut (configurable via `JUDGE_LLM_PROVIDER` et `JUDGE_MODEL`) pour éviter les conflits de rate-limit avec Anthropic utilisé par les Agents 1B et 2.

---

## 6. Base de données — Schéma complet

### 6.1 Configuration

| Environnement | Base | URL |
|---------------|------|-----|
| Développement | SQLite | `sqlite:///./data/datanova.db` |
| Production | PostgreSQL 16 | `postgresql://user:pass@host/datanova` |

**ORM :** SQLAlchemy 2.0 avec `declarative_base()`  
**Migrations :** Alembic (dossier `backend/alembic/`)

### 6.2 Modèles de données (20 tables)

#### Documents & Collecte

| Table | Description | Clés principales |
|-------|-------------|-----------------|
| `documents` | Documents collectés (Agent 1A) | id, title, source_url, event_type, celex_id, hash_sha256, content, geographic_scope |
| `weather_alerts` | Alertes météo collectées | id, site_id, alert_type, severity, value, threshold, supply_chain_risk |

#### Données métier Hutchinson

| Table | Description | Colonnes clés |
|-------|-------------|--------------|
| `hutchinson_sites` | Sites de production (~90) | id, name, code, country, lat/lng, sectors, products, daily_revenue, strategic_importance |
| `suppliers` | Fournisseurs (~16 000) | id, name, code, country, sector, products_supplied, criticality_score, annual_purchase_volume |
| `supplier_relationships` | Relations site↔fournisseur | site_id, supplier_id, criticality, is_sole_supplier, daily_consumption_value, stock_coverage_days |

**Colonnes Business Interruption** ajoutées sur les 3 tables ci-dessus pour le calcul d'impact financier réel :
- Sites : `daily_revenue`, `raw_material_stock_days`, `key_customers`, `backup_production_sites`
- Fournisseurs : `annual_purchase_volume`, `switch_time_days`, `max_capacity_increase_percent`
- Relations : `daily_consumption_value`, `stock_coverage_days`, `contract_penalties_per_day`, `percent_site_production_dependent`

#### Pipeline d'analyse

| Table | Description | Colonnes clés |
|-------|-------------|--------------|
| `pertinence_checks` | Résultats Agent 1B | document_id, decision (OUI/NON/PARTIELLEMENT), confidence, reasoning, affected_sites, affected_suppliers |
| `risk_analyses` | Résultats Agent 2 | document_id, risk_level, risk_score, affected_sites, affected_suppliers, recommendations, 7 sections rapport |
| `risk_projections` | Projections par entité | event_id, entity_id, entity_type, risk_score, business_interruption_score, severity/probability/exposure/urgency |
| `judge_evaluations` | Résultats LLM Judge | risk_analysis_id, scores (6 critères), overall_score, action (APPROVE/REVIEW/REJECT) |

#### Alertes & Notifications

| Table | Description |
|-------|-------------|
| `alerts` | Alertes générées (severity, affected_sites/suppliers, status) |
| `notifications` | Notifications envoyées (channel, status, sent_at) |
| `alert_subscriptions` | Abonnements personnalisés (event_types, min_criticality, countries, supplier_ids) |

#### Utilisateurs & Configuration

| Table | Description |
|-------|-------------|
| `users` | Utilisateurs (email, role: admin/analyst/viewer) |
| `company_profile` | Profil global Hutchinson |
| `data_sources` | Sources de données configurables (EUR-Lex, Open-Meteo, etc.) |
| `execution_logs` | Logs d'exécution des agents (monitoring) |
| `supplier_analyses` | Analyses ponctuelles fournisseurs (mode à la demande) |

#### Amélioration continue

| Table | Description |
|-------|-------------|
| `ground_truth_cases` | Cas de référence validés par experts |
| `ground_truth_results` | Comparaison LLM vs experts |

### 6.3 Relations principales

```
Document ──1:1── PertinenceCheck ──1:1── RiskAnalysis ──1:1── JudgeEvaluation
    │                                         │
    │                                         ├──1:N── RiskProjection
    │                                         └──1:N── Alert ──1:N── Notification
    │
    └──1:N── WeatherAlert

HutchinsonSite ──1:N── SupplierRelationship ──N:1── Supplier

User ──1:N── AlertSubscription
User ──1:N── Notification
```

---

## 7. Frontend — Interface React

### 7.1 Technologies

- **React 18** + **TypeScript** pour le typage statique
- **Vite** comme build tool et serveur de développement
- **TailwindCSS** (via utility classes) pour le styling
- **Leaflet** pour les cartes interactives
- **Recharts** pour les graphiques
- **Lucide React** pour les icônes

### 7.2 Configuration

**Fichier :** `frontend/vite.config.ts`

```typescript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
```

En développement, le proxy Vite redirige `/api/*` vers le backend sur `localhost:8000`. En production, Nginx assure le même rôle.

**Configuration API :** `frontend/src/config/app.config.ts`
- `apiUrl` : vide en dev (utilise le proxy) ; URL complète en prod via `VITE_API_URL`

### 7.3 Pages

| Page | Composant | URL | Description |
|------|-----------|-----|-------------|
| Landing | `Landing.tsx` | `/` | Page d'accueil publique |
| Login | `Login.tsx` | `/login` | Authentification |
| Register | `Register.tsx` | `/register` | Inscription |
| Dashboard | `Dashboard.tsx` | `/dashboard` | Tableau de bord principal avec KPIs, matrice de risques, carte |
| Agent Dashboard | `AgentDashboard.tsx` | `/agent` | Suivi des agents IA en temps réel |
| Supplier Analysis | `SupplierAnalysis.tsx` | `/supplier-analysis` | Analyse de risques fournisseur à la demande |
| Admin Panel | `AdminPanel.tsx` | `/admin` | Paramétrage : scheduler, sources, sites, fournisseurs, utilisateurs |

### 7.4 Composants réutilisables

| Composant | Description |
|-----------|-------------|
| `RiskMatrix.tsx` | Matrice Risque × Impact (5×5) interactive |
| `RiskMatrixAdvanced.tsx` | Version avancée avec filtres |
| `RiskTable.tsx` | Tableau des risques avec tri, filtres, pagination |
| `RiskDonutChart.tsx` | Graphiques de répartition des risques (Recharts) |
| `SupplierMap.tsx` | Carte Leaflet avec markers sites/fournisseurs |
| `RiskDetailModal.tsx` | Modal de détail d'une analyse (7 sections rapport) |
| `NotificationCenter.tsx` | Centre de notifications (icône cloche) |
| `SubscriptionSettings.tsx` | Gestion des abonnements aux alertes |
| `SupplierProfileModal.tsx` | Profil détaillé d'un fournisseur |

### 7.5 Services API

| Service | Fichier | Endpoints consommés |
|---------|---------|---------------------|
| API base | `api.ts` | Configuration fetch commune |
| Auth | `authService.ts` | `/api/auth/login`, `/api/auth/register`, `/api/auth/me` |
| Regulations | `regulationsService.ts` | `/api/regulations`, `/api/regulations/stats` |
| Impacts | `impactsService.ts` | `/api/impacts`, `/api/impacts/stats/dashboard`, `/api/impacts/{id}/details` |
| Subscriptions | `subscriptionService.ts` | `/api/subscriptions/*` |
| Supplier | `supplierService.ts` | `/api/supplier/analyze`, `/api/supplier/db/*` |

---

## 8. Orchestration LangGraph

**Fichier principal :** `backend/src/orchestration/langgraph_workflow.py` (1611 lignes)

### 8.1 Workflow StateGraph

```python
StateGraph: PingWorkflowState
  ├── node_agent_1a()     — Collecte documents + météo
  ├── node_agent_1b()     — Analyse pertinence
  ├── route_after_1b()    — Routage OUI/PARTIELLEMENT → Agent 2, NON → END
  ├── node_agent_2()      — Analyse d'impact 360°
  ├── node_judge()        — Validation qualité
  ├── node_notification() — Envoi alertes email
  └── END
```

### 8.2 État du workflow (TypedDict)

```python
class PingWorkflowState(TypedDict):
    keyword: str
    max_documents: int
    company_name: str
    documents: List[Dict]
    weather_alerts: List[Dict]
    pertinence_results: List[Dict]
    risk_analyses: List[Dict]
    judge_results: List[Dict]
    notifications: List[Dict]
    errors: List[str]
    summary: Dict
```

### 8.3 Fonction d'entrée

```python
def run_ping_workflow(
    keyword: str = "CBAM",
    max_documents: int = 8,
    company_name: str = "HUTCHINSON"
) -> Dict
```

### 8.4 Scheduler APScheduler

**Configuration :** `backend/src/api/routes/admin.py`

| Paramètre | Défaut | Options |
|-----------|--------|---------|
| `frequency` | `daily` | hourly, daily, weekly, manual |
| `time` | `06:00` | HH:MM |
| `day_of_week` | `mon` | mon-sun |
| `enabled` | `true` | true/false |

Le scheduler utilise `BackgroundScheduler` avec `CronTrigger`. Il est initialisé au startup de FastAPI via le lifespan et arrêté proprement au shutdown.

**Exécution manuelle :** `POST /api/admin/scheduler/run-now` déclenche `run_ping_workflow(keyword="CBAM", max_documents=8, company_name="HUTCHINSON")`.

### 8.5 Logging d'exécution

Chaque étape du workflow est enregistrée dans la table `execution_logs` avec :
- `agent_name` : agent_1a, agent_1b, agent_2, judge
- `status` : success, error, warning
- `execution_time_ms` : Temps d'exécution
- `error_message` : Message d'erreur si échec

---

## 9. Système de notifications

### 9.1 Architecture

```
NotificationService (orchestrateur)
   ├── NotificationRouter     — Détermine qui notifier
   ├── SubscriptionFilter     — Filtre par abonnement
   └── EmailSender            — Envoi via Brevo (Sendinblue)
```

### 9.2 Déclencheurs

| Événement | Condition | Action |
|-----------|-----------|--------|
| Publication rapport | Score Judge ≥ 7.0 | Email aux abonnés correspondants |
| Risque critique | risk_score ≥ 75 | Email immédiat |

### 9.3 Filtrage des abonnements

Un abonnement (`AlertSubscription`) filtre sur :
- **Types d'événements** : réglementaire, climatique, géopolitique, ou tous
- **Fournisseurs** : liste d'IDs spécifiques ou tous
- **Sites** : liste d'IDs spécifiques ou tous
- **Pays** : liste de pays ou tous
- **Criticité minimum** : FAIBLE, MOYEN, ÉLEVÉ, CRITIQUE

### 9.4 Envoi email via Brevo

**Fichier :** `backend/src/notifications/email_sender.py` (381 lignes)

- **SDK :** `sib_api_v3_sdk` (Brevo/Sendinblue)
- **Quota :** 300 emails/jour (plan gratuit)
- **Mode dry-run :** Variable `EMAIL_DRY_RUN=true` pour tester sans envoyer
- **Template HTML :** Email professionnel avec risque, entités affectées, recommandations

---

## 10. API REST — Référence complète

### 10.1 Authentification (`/api/auth`)

| Méthode | Route | Description |
|---------|-------|-------------|
| `POST` | `/api/auth/register` | Inscription (email, password, name, role) |
| `POST` | `/api/auth/login` | Connexion → JWT token |
| `GET` | `/api/auth/me?token=xxx` | Info utilisateur courant |

**Rôles :** `juridique`, `decisive`  
**Auth :** JWT (python-jose)

### 10.2 Réglementations (`/api/regulations`)

| Méthode | Route | Description | Paramètres |
|---------|-------|-------------|------------|
| `GET` | `/api/regulations` | Liste paginée | `status` (all/pending/validated/rejected), `search`, `page`, `limit` |
| `GET` | `/api/regulations/stats` | Statistiques | — |
| `GET` | `/api/regulations/{id}` | Détail | — |
| `PUT` | `/api/regulations/{id}/status` | Modifier statut | `{status, comment}` |

**Statuts dérivés :**
- `validated` = a une RiskAnalysis associée
- `rejected` = PertinenceCheck.decision == "NON"
- `pending` = ni l'un ni l'autre

### 10.3 Analyses d'impact (`/api/impacts`)

| Méthode | Route | Description | Paramètres |
|---------|-------|-------------|------------|
| `GET` | `/api/impacts` | Liste paginée | `impact_level` (faible/moyen/eleve/critique), `page`, `limit` (max 200) |
| `GET` | `/api/impacts/stats/dashboard` | Stats dashboard | — |
| `GET` | `/api/impacts/stats/timeline` | Timeline 30j | — |
| `GET` | `/api/impacts/{id}` | Résumé analyse | — |
| `GET` | `/api/impacts/{id}/details` | Détail complet | — |

**Réponse `/stats/dashboard` :**
```json
{
  "total_regulations": 26,
  "total_impacts": 11,
  "high_risks": 3,
  "medium_risks": 5,
  "low_risks": 3,
  "critical_deadlines": 2,
  "average_score": 65.5,
  "by_risk_type": {"Réglementations": 8, "Climat": 2, "Géopolitique": 1}
}
```

**Réponse `/impacts/{id}/details` :**
```json
{
  "id": "...",
  "regulation_title": "Règlement CBAM...",
  "risk_level": "CRITIQUE",
  "risk_score": 82.75,
  "affected_sites": [{"id": "...", "name": "Le Havre", "risk_score": 85.2, "reasoning": "..."}],
  "affected_suppliers": [{"id": "...", "name": "Supplier X", "risk_score": 78.1}],
  "recommendations": "1. Auditer les fournisseurs...",
  "weather_risk_summary": {"max_severity": "high", "alerts_count": 3},
  "source_url": "https://eur-lex.europa.eu/...",
  "source_excerpt": "Article 1..."
}
```

### 10.4 Pipeline (`/api/pipeline`)

| Méthode | Route | Description |
|---------|-------|-------------|
| `POST` | `/api/pipeline/agent1/trigger` | Lancer Agent 1 (async) |
| `POST` | `/api/pipeline/agent1/trigger-sync` | Lancer Agent 1 (synchrone) |
| `GET` | `/api/pipeline/agent1/status` | Statut Agent 1 |
| `POST` | `/api/pipeline/agent2/trigger` | Lancer Agent 2 (async) |
| `POST` | `/api/pipeline/agent2/trigger-sync` | Lancer Agent 2 (synchrone) |
| `GET` | `/api/pipeline/agent2/status` | Statut Agent 2 |

**Protection concurrence :** Retourne HTTP 409 si un agent est déjà en cours d'exécution.

### 10.5 Administration (`/api/admin`)

#### Sources de données

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/api/admin/sources` | Lister les sources |
| `POST` | `/api/admin/sources` | Créer une source |
| `PUT` | `/api/admin/sources/{id}` | Modifier une source |
| `DELETE` | `/api/admin/sources/{id}` | Supprimer |
| `POST` | `/api/admin/sources/{id}/toggle` | Activer/Désactiver |

#### Catégories de risques

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/api/admin/risk-categories` | Lister les catégories |
| `POST` | `/api/admin/risk-categories` | Créer une catégorie |
| `POST` | `/api/admin/risk-categories/{code}/toggle` | Activer/Désactiver |

#### Scheduler

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/api/admin/scheduler/config` | Configuration actuelle |
| `PUT` | `/api/admin/scheduler/config` | Modifier la configuration |
| `POST` | `/api/admin/scheduler/run-now` | Exécution immédiate |

#### Fournisseurs et Sites (CRUD complet)

6 endpoints chacun : `GET` (liste), `POST` (créer), `GET` (détail), `PUT` (modifier), `DELETE`, `POST` (toggle).

#### Utilisateurs

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/api/admin/users` | Lister les utilisateurs |
| `PUT` | `/api/admin/users/{id}` | Modifier |
| `POST` | `/api/admin/users/{id}/approve` | Approuver |
| `POST` | `/api/admin/users/{id}/reject` | Rejeter |
| `DELETE` | `/api/admin/users/{id}` | Supprimer |

#### Statistiques globales

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/api/admin/stats` | Stats système (documents, analyses, entités, sources, scheduler) |

### 10.6 Analyse fournisseur (`/api/supplier`)

| Méthode | Route | Description |
|---------|-------|-------------|
| `POST` | `/api/supplier/analyze` | Lancer analyse à la demande |
| `GET` | `/api/supplier/analyses` | Historique analyses |
| `GET` | `/api/supplier/analyses/{id}` | Détail analyse |
| `DELETE` | `/api/supplier/analyses/{id}` | Supprimer |
| `GET` | `/api/supplier/db/list` | Fournisseurs en BDD |
| `GET` | `/api/supplier/db/{id}` | Détail fournisseur + relations |
| `GET` | `/api/supplier/db/by-name/{name}` | Recherche par nom |

**Formule score risque fournisseur :**
```
risk_score = min(10, (reg_count × 0.5 + weather_count × 0.8) × multiplicateur_criticité)
```
Multiplicateurs : Standard=1.0, Important=1.2, Critique=1.5

### 10.7 Documents PDF (`/api/documents`)

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/api/documents/mapping` | Mapping CELEX ID → fichier PDF |
| `GET` | `/api/documents/by-celex/{celex_id}` | Télécharger PDF par CELEX ID |
| `GET` | `/api/documents/{filename}` | Télécharger PDF par nom de fichier |

### 10.8 Abonnements (`/api/subscriptions`)

| Méthode | Route | Description |
|---------|-------|-------------|
| `POST` | `/api/subscriptions` | Créer un abonnement |
| `GET` | `/api/subscriptions` | Lister (filtrer par email) |
| `GET` | `/api/subscriptions/{id}` | Détail |
| `PUT` | `/api/subscriptions/{id}` | Modifier |
| `DELETE` | `/api/subscriptions/{id}` | Supprimer |
| `POST` | `/api/subscriptions/{id}/toggle` | Activer/Désactiver |
| `GET` | `/api/subscriptions/options/suppliers` | Options fournisseurs |
| `GET` | `/api/subscriptions/options/sites` | Options sites |
| `GET` | `/api/subscriptions/options/countries` | Options pays |
| `GET` | `/api/subscriptions/options/event-types` | Options types d'événements |
| `GET` | `/api/subscriptions/options/criticality-levels` | Options niveaux criticité |

### 10.9 Récapitulatif

| Module | Préfixe | Endpoints |
|--------|---------|-----------|
| Auth | `/api/auth` | 3 |
| Regulations | `/api/regulations` | 4 |
| Impacts | `/api/impacts` | 5 |
| Pipeline | `/api/pipeline` | 6 |
| Admin | `/api/admin` | 30 |
| Supplier | `/api/supplier` | 7 |
| Documents | `/api/documents` | 3 |
| Subscriptions | `/api/subscriptions` | 11 |
| **Total** | | **69 endpoints** |

---

## 11. Configuration et variables d'environnement

### 11.1 Variables d'environnement backend (`.env`)

```env
# ===== LLM =====
ANTHROPIC_API_KEY=sk-ant-api03-...       # Clé API Anthropic (Claude) — Agents 1B et 2
GOOGLE_API_KEY=...                        # Clé API Google (Gemini) — optionnel
LLM_PROVIDER=anthropic                    # Provider LLM principal (anthropic ou openai)

# ===== Judge =====
OPENAI_API_KEY=sk-...                     # Clé API OpenAI — Judge
JUDGE_LLM_PROVIDER=openai                 # Provider pour le Judge
JUDGE_MODEL=gpt-4o-mini                   # Modèle Judge

# ===== Base de données =====
DATABASE_URL=sqlite:///./data/datanova.db  # Dev: SQLite | Prod: postgresql://...

# ===== Email (Brevo) =====
BREVO_API_KEY=xkeysib-...                 # Clé API Brevo
SENDER_EMAIL=ping@hutchinson.com          # Email expéditeur
SENDER_NAME=Système PING - Hutchinson     # Nom expéditeur
EMAIL_DRY_RUN=false                       # true = pas d'envoi réel

# ===== Scheduler =====
SCHEDULER_ENABLED=true                     # Activer le scheduler
CRON_SCHEDULE=0 8 * * 1                   # Expression cron par défaut

# ===== Seuils Agent 1B =====
KEYWORD_WEIGHT=0.3                         # Poids mots-clés (reporting uniquement)
NC_CODE_WEIGHT=0.3                         # Poids codes NC (reporting uniquement)
LLM_SEMANTIC_WEIGHT=0.4                    # Poids LLM (reporting uniquement)
CRITICAL_THRESHOLD=0.8                     # Seuil risque critique
HIGH_THRESHOLD=0.6                         # Seuil risque élevé
MEDIUM_THRESHOLD=0.4                       # Seuil risque moyen
```

### 11.2 Configuration Pydantic Settings

**Fichier :** `backend/src/config.py`

La classe `Settings` (hérite de `BaseSettings`) charge automatiquement les variables depuis `.env`. Crée les dossiers `data/` et `logs/` au démarrage si inexistants.

### 11.3 Catégories de risques

**Fichier :** `backend/config/risk_categories.json`

```json
[
  {"code": "regulatory", "name": "Réglementaire", "event_type": "reglementaire", "icon": "📜"},
  {"code": "climate", "name": "Climatique", "event_type": "climatique", "icon": "🌡️"},
  {"code": "geopolitical", "name": "Géopolitique", "event_type": "geopolitique", "icon": "🌍"}
]
```

Le service `risk_categories.py` fournit un cache thread-safe avec rechargement automatique si le fichier est modifié. Supporte l'ajout/suppression de catégories via l'API admin.

---

## 12. Déploiement

### 12.1 Docker Compose (Production)

**Fichier :** `docker-compose.yml`

| Service | Image | Port | Description |
|---------|-------|------|-------------|
| `postgres` | `postgres:16-alpine` | 5432 | Base de données PostgreSQL |
| `backend` | Build `./backend` | 8000 | API FastAPI |
| `frontend` | Build `./frontend` | 3001→80 | Interface React (Nginx) |
| `adminer` | `adminer:latest` | 8080 | Interface admin BDD (dev) |

```bash
# Lancer tous les services
docker-compose up -d

# Vérifier les logs
docker-compose logs -f backend
```

### 12.2 Dockerfile Backend

Multi-stage build :
1. **Builder** : Python 3.13-slim + uv (installeur rapide)
2. **Production** : Image slim, utilisateur non-root `appuser`

### 12.3 Dockerfile Frontend

Multi-stage build :
1. **Builder** : Node 20 Alpine + `npm ci` + `npm run build`
2. **Production** : Nginx Alpine servant les fichiers statiques

### 12.4 Terraform (Azure)

**Dossier :** `terraform/`

| Fichier | Description |
|---------|-------------|
| `main.tf` | Ressources Azure (App Service, Static Web App, PostgreSQL) |
| `variables.tf` | Variables paramétrables |
| `terraform.tfvars.example` | Exemple de valeurs |
| `outputs.tf` | URLs de sortie |
| `providers.tf` | Configuration provider Azure |

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

---

## 13. Guide d'installation

### 13.1 Prérequis

| Outil | Version minimum |
|-------|----------------|
| Python | 3.11+ |
| Node.js | 18+ |
| Git | 2.x |
| Docker (optionnel) | 20+ |

### 13.2 Installation backend

```bash
cd backend

# Créer l'environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# Installer les dépendances
pip install -e .

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos clés API

# Initialiser la base de données
alembic upgrade head

# Lancer le serveur
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 13.3 Installation frontend

```bash
cd frontend

# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev
# → http://localhost:3000

# Build production
npm run build
```

### 13.4 Lancement rapide (développement)

**Terminal 1 — Backend :**
```bash
cd backend && source .venv/bin/activate && uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend :**
```bash
cd frontend && npm run dev
```

**Vérification :**
```bash
curl http://localhost:8000/health          # → {"status": "healthy"}
curl http://localhost:3000/api/regulations/stats  # → {"total": N, ...}
```

### 13.5 Lancer le workflow manuellement

```bash
# Via API
curl -X POST http://localhost:8000/api/admin/scheduler/run-now

# Via Python
cd backend && source .venv/bin/activate
python -c "
from src.orchestration.langgraph_workflow import run_ping_workflow
result = run_ping_workflow(keyword='CBAM', max_documents=8, company_name='HUTCHINSON')
print(f'Status: {result[\"status\"]}')
print(f'Documents collectés: {result[\"summary\"][\"documents_collected\"]}')
print(f'Documents pertinents: {result[\"summary\"][\"documents_pertinent\"]}')
print(f'Analyses de risque: {result[\"summary\"][\"risk_analyses\"]}')
"
```

---

## 14. Tests

### 14.1 Tests backend (pytest)

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

| Type | Description | Dossier |
|------|-------------|---------|
| Unitaires | Tests des agents individuels | `tests/` |
| Intégration | Tests du pipeline complet | `tests/` |
| API | Tests des endpoints FastAPI | `tests/` |

### 14.2 Tests frontend (Playwright)

```bash
cd frontend

# Installer les navigateurs
npx playwright install

# Lancer les tests
npm run test

# Mode interactif
npm run test:ui

# Mode debug
npm run test:debug
```

### 14.3 Tests Cucumber (BDD)

```bash
cd frontend
npm run test:cucumber
```

---

## 15. Annexes

### 15.1 Glossaire

| Terme | Définition |
|-------|------------|
| **Agent 1A** | Module de collecte automatique de documents (EUR-Lex + météo) |
| **Agent 1B** | Module d'analyse de pertinence et scoring (100% LLM) |
| **Agent 2** | Module d'analyse d'impact 360° et recommandations |
| **LLM Judge** | Validateur automatique basé sur LLM |
| **CBAM** | Carbon Border Adjustment Mechanism (taxe carbone UE) |
| **EUR-Lex** | Portail officiel du droit de l'Union européenne |
| **Code NC** | Nomenclature Combinée (classification douanière) |
| **LangGraph** | Framework d'orchestration de workflows basé sur des graphes d'état |
| **APScheduler** | Bibliothèque Python de planification de tâches |
| **Haversine** | Formule calculant la distance entre deux points GPS sur une sphère |
| **Business Interruption** | Score d'impact financier d'une interruption d'activité |
| **360° Risk Score** | Score composite : severity (30%) + probability (25%) + exposure (25%) + urgency (20%) |
| **Brevo** | Service d'envoi d'emails transactionnels (anciennement Sendinblue) |

### 15.2 Codes de référence

**Types d'événements :**

| Code interne | event_type (FR) | Description |
|-------------|-----------------|-------------|
| regulation | reglementaire | Nouvelles réglementations européennes |
| climate | climatique | Alertes météo et risques climatiques |
| geopolitical | geopolitique | Conflits, sanctions, instabilité |

**Niveaux de risque :**

| Score | Niveau | Action |
|-------|--------|--------|
| 0–25 | FAIBLE | Surveillance |
| 25–50 | MOYEN | Analyse approfondie |
| 50–75 | ÉLEVÉ | Plan d'action requis |
| 75–100 | CRITIQUE | Action immédiate |

**Décisions de pertinence :**

| Décision | Score LLM | Signification |
|----------|-----------|---------------|
| OUI | ≥ 0.6 | Document pertinent pour Hutchinson |
| PARTIELLEMENT | ≥ 0.4 | Pertinence partielle, à surveiller |
| NON | < 0.4 | Non pertinent |

### 15.3 Métriques du projet

| Composant | Langage | Lignes estimées |
|-----------|---------|-----------------|
| Backend (agents + API) | Python | ~12 000 |
| Frontend (UI) | TypeScript/React | ~5 000 |
| Configuration (Docker, Terraform) | YAML/HCL | ~500 |
| **Total** | | **~17 500** |

### 15.4 Dépendances principales

**Backend (pyproject.toml) :**
- LangChain (≥0.3), LangGraph (≥1.0.5) — orchestration IA
- FastAPI (≥0.128), Uvicorn (≥0.40) — API REST
- SQLAlchemy (≥2.0), Alembic (≥1.13) — BDD
- httpx (≥0.27), BeautifulSoup4, pdfplumber, PyMuPDF — scraping/extraction
- APScheduler (≥3.10) — planification
- Pydantic (≥2.8), python-dotenv — configuration
- python-jose, passlib, bcrypt — authentification
- Brevo SDK (`sib_api_v3_sdk`) — emails

**Frontend (package.json) :**
- React 18, React DOM, React Router DOM 6
- Leaflet 1.9, React-Leaflet 4.2 — cartes
- Recharts 2.6 — graphiques
- TypeScript 5.2, Vite 5.0 — build
- Playwright 1.57 — tests E2E

---

*Document généré le 06/02/2026*  
*Projet PING DataNova — ESIGELEC*  
*Version 1.0*
