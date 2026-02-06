# Manuel d'Installation et d'Utilisation — DataNova PING

**Version :** 1.0  
**Date :** 06 février 2026  
**Destinataire :** Équipes Hutchinson SA  
**Projet :** PING DataNova — Plateforme de veille proactive des risques supply chain  

---

## Table des matières

### Partie 1 — Présentation de la solution
- [1.1 Qu'est-ce que DataNova PING ?](#11-quest-ce-que-datanova-ping-)
- [1.2 Comment ça marche ?](#12-comment-ça-marche-)
- [1.3 Ce que la plateforme fait pour vous](#13-ce-que-la-plateforme-fait-pour-vous)

### Partie 2 — Manuel d'installation
- [2.1 Prérequis](#21-prérequis)
- [2.2 Récupérer le code source](#22-récupérer-le-code-source)
- [2.3 Installer le backend](#23-installer-le-backend)
- [2.4 Configurer les clés API (obligatoire)](#24-configurer-les-clés-api-obligatoire)
- [2.5 Initialiser la base de données](#25-initialiser-la-base-de-données)
- [2.6 Installer le frontend](#26-installer-le-frontend)
- [2.7 Lancer l'application](#27-lancer-lapplication)
- [2.8 Vérifier que tout fonctionne](#28-vérifier-que-tout-fonctionne)
- [2.9 Déploiement avec Docker (production)](#29-déploiement-avec-docker-production)
- [2.10 Déploiement sur Azure](#210-déploiement-sur-azure)

### Partie 3 — Manuel d'utilisation du frontend
- [3.1 Accéder à l'application](#31-accéder-à-lapplication)
- [3.2 Créer un compte](#32-créer-un-compte)
- [3.3 Se connecter](#33-se-connecter)
- [3.4 Le tableau de bord principal](#34-le-tableau-de-bord-principal)
- [3.5 Onglet Réglementations](#35-onglet-réglementations)
- [3.6 Onglet Climat](#36-onglet-climat)
- [3.7 Onglet Géopolitique](#37-onglet-géopolitique)
- [3.8 Consulter le détail d'un risque](#38-consulter-le-détail-dun-risque)
- [3.9 La carte des fournisseurs](#39-la-carte-des-fournisseurs)
- [3.10 Analyser un fournisseur à la demande](#310-analyser-un-fournisseur-à-la-demande)
- [3.11 Gérer ses abonnements aux alertes](#311-gérer-ses-abonnements-aux-alertes)
- [3.12 Le centre de notifications](#312-le-centre-de-notifications)
- [3.13 Panneau d'administration](#313-panneau-dadministration)
- [3.14 Exporter un rapport PDF](#314-exporter-un-rapport-pdf)

### Partie 4 — Continuer le projet
- [4.1 Architecture du code](#41-architecture-du-code)
- [4.2 Ajouter une nouvelle source de données](#42-ajouter-une-nouvelle-source-de-données)
- [4.3 Modifier les seuils de risque](#43-modifier-les-seuils-de-risque)
- [4.4 Ajouter une catégorie de risque](#44-ajouter-une-catégorie-de-risque)
- [4.5 Mettre à jour le profil Hutchinson](#45-mettre-à-jour-le-profil-hutchinson)
- [4.6 Maintenir et mettre à jour les dépendances](#46-maintenir-et-mettre-à-jour-les-dépendances)
- [4.7 Problèmes courants et solutions](#47-problèmes-courants-et-solutions)

---

# Partie 1 — Présentation de la solution

## 1.1 Qu'est-ce que DataNova PING ?

DataNova PING est une **plateforme de veille proactive intelligent** qui surveille automatiquement les risques pouvant affecter les opérations d'Hutchinson :

- **Risques réglementaires** : nouvelles lois et réglementations européennes (CBAM, REACH, etc.)
- **Risques climatiques** : alertes météo (tempêtes, canicules, inondations) près de vos sites et fournisseurs
- **Risques géopolitiques** : tensions, sanctions et instabilités dans les pays de votre supply chain

La plateforme utilise **4 agents d'intelligence artificielle** qui travaillent en chaîne pour collecter, filtrer, analyser et valider automatiquement les informations.

## 1.2 Comment ça marche ?

```
   📡 COLLECTE             🔍 FILTRAGE            📊 ANALYSE           ✅ VALIDATION
   ─────────              ──────────             ──────────           ──────────────
   Agent 1A               Agent 1B               Agent 2              LLM Judge
   Récupère les           Détermine si           Calcule le           Vérifie la
   documents depuis       c'est pertinent        score de risque      qualité de
   EUR-Lex et les         pour Hutchinson        à 360° et génère     l'analyse et
   alertes météo          (scoring IA)           des recommandations  décide de publier
   
              →                      →                      →
   
   Résultat :             Résultat :             Résultat :           Résultat :
   Documents bruts        OUI / NON /            Rapport détaillé     APPROVE → Email
   + alertes météo        PARTIELLEMENT          + score + actions    REJECT → Archivé
```

**Cycle automatique :** Par défaut, ce pipeline s'exécute **chaque jour à 6h** (configurable). Vous pouvez aussi le déclencher manuellement depuis le panneau d'administration.

## 1.3 Ce que la plateforme fait pour vous

| Fonctionnalité | Description |
|----------------|-------------|
| **Surveillance automatique** | Collecte quotidienne depuis EUR-Lex et Open-Meteo |
| **Filtrage intelligent** | Seuls les documents pertinents pour Hutchinson sont analysés |
| **Score de risque 360°** | Chaque menace reçoit un score combinant gravité, probabilité, exposition et urgence |
| **Impact par entité** | Chaque site et fournisseur reçoit son propre score d'impact |
| **Business Interruption** | Estimation de l'impact financier (CA, stocks, pénalités) |
| **Recommandations** | Actions concrètes priorisées avec timeline et budget estimé |
| **Alertes email** | Notifications automatiques selon vos abonnements |
| **Rapports PDF** | Export professionnel en un clic |
| **Dashboard interactif** | Matrice de risques, carte mondiale, graphiques temps réel |
| **Analyse fournisseur** | Audit à la demande de n'importe quel fournisseur |

---

# Partie 2 — Manuel d'installation

## 2.1 Prérequis

### Logiciels à installer

| Logiciel | Version minimum | Téléchargement | Vérification |
|----------|----------------|----------------|--------------|
| **Python** | 3.11 ou plus | [python.org](https://www.python.org/downloads/) | `python3 --version` |
| **Node.js** | 18 ou plus | [nodejs.org](https://nodejs.org/) | `node --version` |
| **Git** | 2.x | [git-scm.com](https://git-scm.com/) | `git --version` |
| **Docker** (optionnel) | 20+ | [docker.com](https://www.docker.com/) | `docker --version` |

### Clés API nécessaires

| Service | Usage | Comment l'obtenir |
|---------|-------|-------------------|
| **Anthropic** (Claude) | Agents 1B et 2 — analyse IA | [console.anthropic.com](https://console.anthropic.com/) → API Keys |
| **OpenAI** | LLM Judge — validation qualité | [platform.openai.com](https://platform.openai.com/) → API Keys |
| **Brevo** (optionnel) | Envoi d'emails de notification | [app.brevo.com](https://app.brevo.com/) → SMTP & API → API Keys |

> **Coût estimé des API IA :** ~2-5€ par exécution complète du pipeline (8 documents).

### Configuration machine

- **RAM :** 4 Go minimum (8 Go recommandé)
- **Disque :** 1 Go d'espace libre
- **Réseau :** Accès internet requis (pour les API EUR-Lex, Open-Meteo, LLM)

---

## 2.2 Récupérer le code source

```bash
# Cloner le dépôt
git clone https://github.com/votre-organisation/dataNova.git

# Entrer dans le projet
cd dataNova
```

> **Note :** Remplacez l'URL par celle de votre dépôt Git interne.

---

## 2.3 Installer le backend

```bash
# 1. Aller dans le dossier backend
cd backend

# 2. Créer un environnement virtuel Python
python3 -m venv .venv

# 3. Activer l'environnement virtuel
# Sur macOS / Linux :
source .venv/bin/activate
# Sur Windows :
# .venv\Scripts\activate

# 4. Installer toutes les dépendances
pip install -e .

# 5. Vérifier que l'installation est réussie
python -c "from src.api.main import app; print('✅ Backend installé avec succès')"
```

**Résultat attendu :** `✅ Backend installé avec succès`

Si vous voyez une erreur, vérifiez que :
- Python 3.11+ est bien installé (`python3 --version`)
- L'environnement virtuel est activé (vous voyez `(.venv)` dans votre terminal)

---

## 2.4 Configurer les clés API (obligatoire)

### Créer le fichier de configuration

Le fichier `.env` contient toutes les clés secrètes. Il existe un fichier modèle `.env.example` à copier :

```bash
# Toujours dans le dossier backend/
cp .env.example .env
```

### Éditer le fichier `.env`

Ouvrez le fichier `.env` avec votre éditeur de texte (VS Code, Notepad++, nano...) et remplissez les valeurs :

```env
# ══════════════════════════════════════════════════════
# CONFIGURATION DATANOVA PING — À REMPLIR
# ══════════════════════════════════════════════════════

# ─── CLÉS API (OBLIGATOIRE) ───────────────────────────

# Clé Anthropic (Claude) — nécessaire pour les Agents 1B et 2
# Obtenez sur : https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-api03-VOTRE_CLE_ICI

# Clé OpenAI — nécessaire pour le LLM Judge
# Obtenez sur : https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-VOTRE_CLE_ICI

# ─── BASE DE DONNÉES ──────────────────────────────────

# SQLite pour développement (par défaut, rien à changer) :
DATABASE_URL=sqlite:///./data/datanova.db

# Pour PostgreSQL (production) décommentez et adaptez :
# DATABASE_URL=postgresql://utilisateur:motdepasse@localhost:5432/datanova

# ─── NOTIFICATIONS EMAIL (OPTIONNEL) ──────────────────

# Brevo (anciennement Sendinblue) — pour envoyer des emails
# Obtenez sur : https://app.brevo.com/ → SMTP & API
BREVO_API_KEY=xkeysib-VOTRE_CLE_ICI
SENDER_EMAIL=ping@hutchinson.com
SENDER_NAME=Système PING - Hutchinson

# Mode test : les emails sont simulés sans envoi réel
# Mettez "true" pour tester sans envoyer, "false" pour l'envoi réel
EMAIL_DRY_RUN=true

# ─── PLANIFICATION ─────────────────────────────────────

# Active le scheduler automatique (true/false)
SCHEDULER_ENABLED=true

# Expression cron : "0 6 * * *" = tous les jours à 6h
CRON_SCHEDULE=0 6 * * *

# ─── LOGGING ───────────────────────────────────────────
LOG_LEVEL=INFO
```

> **Important :** Le fichier `.env` contient des clés secrètes. **Ne le partagez jamais** et ne le commitez pas sur Git (il est déjà dans `.gitignore`).

### Vérifier que les clés fonctionnent

```bash
# Test rapide de la clé Anthropic
python -c "
import anthropic
client = anthropic.Anthropic()
print('✅ Clé Anthropic valide')
"

# Test rapide de la clé OpenAI
python -c "
import openai
client = openai.OpenAI()
print('✅ Clé OpenAI valide')
"
```

---

## 2.5 Initialiser la base de données

```bash
# Toujours dans backend/ avec l'environnement activé

# Créer toutes les tables
alembic upgrade head
```

**Résultat attendu :** Plusieurs lignes `Running upgrade ...` puis retour au prompt sans erreur.

La base de données SQLite sera créée automatiquement dans `backend/data/datanova.db`.

### Données pré-chargées

Le système est livré avec :
- **Profil Hutchinson** (`data/company_profiles/Hutchinson_SA.json`) : sites, fournisseurs, produits, codes NC
- **Fichier hutchinson.json** (`data/company_profiles/hutchinson.json`) : profil simplifié
- **Configuration des sources** (`config/sources.json`) : sources EUR-Lex pré-configurées
- **Catégories de risques** (`config/risk_categories.json`) : réglementaire, climatique, géopolitique

> Ces fichiers sont essentiels au bon fonctionnement. Ne les supprimez pas.

### Charger les sites et fournisseurs (première fois)

Si la base est vide (première installation), les sites et fournisseurs Hutchinson seront chargés automatiquement lors de la première exécution du workflow, ou vous pouvez les créer via le **Panneau d'Administration** (voir section 3.13).

---

## 2.6 Installer le frontend

```bash
# Revenir à la racine du projet
cd ../frontend

# Installer les dépendances Node.js
npm install

# Vérifier l'installation
npm run build
```

**Résultat attendu :** `✓ built in X.Xs` sans erreur.

---

## 2.7 Lancer l'application

Il faut ouvrir **2 terminaux** : un pour le backend, un pour le frontend.

### Terminal 1 — Backend (API)

```bash
cd backend
source .venv/bin/activate
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Résultat attendu :**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### Terminal 2 — Frontend (Interface)

```bash
cd frontend
npm run dev
```

**Résultat attendu :**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
```

### Accéder à l'application

Ouvrez votre navigateur et allez sur : **http://localhost:3000**

---

## 2.8 Vérifier que tout fonctionne

### Test 1 — API Backend active

```bash
curl http://localhost:8000/health
```

**Réponse attendue :** `{"status":"healthy"}`

### Test 2 — Frontend connecté au backend

```bash
curl http://localhost:3000/api/regulations/stats
```

**Réponse attendue :** Un JSON avec `total`, `pending`, etc.

### Test 3 — Lancer le pipeline complet

```bash
# Dans le terminal backend (avec l'environnement activé)
curl -X POST http://localhost:8000/api/admin/scheduler/run-now
```

Ou depuis Python :
```bash
cd backend && source .venv/bin/activate
python -c "
from src.orchestration.langgraph_workflow import run_ping_workflow
result = run_ping_workflow(keyword='CBAM', max_documents=8, company_name='HUTCHINSON')
print(f'Statut: {result[\"status\"]}')
print(f'Documents collectés: {result[\"summary\"][\"documents_collected\"]}')
print(f'Documents pertinents: {result[\"summary\"][\"documents_pertinent\"]}')
print(f'Analyses de risque: {result[\"summary\"][\"risk_analyses\"]}')
"
```

> **Attention :** La première exécution peut prendre **3 à 10 minutes** (téléchargement de documents + analyse par IA). Les exécutions suivantes seront plus rapides grâce à la déduplication.

---

## 2.9 Déploiement avec Docker (production)

### Prérequis
- Docker et Docker Compose installés

### Lancement

```bash
# À la racine du projet
docker-compose up -d
```

Cela lance 4 services :

| Service | Port | URL |
|---------|------|-----|
| **PostgreSQL** | 5432 | (interne) |
| **Backend** | 8000 | http://localhost:8000 |
| **Frontend** | 3001 | http://localhost:3001 |
| **Adminer** (admin BDD) | 8080 | http://localhost:8080 |

### Variables d'environnement Docker

Créez un fichier `.env` à la racine du projet avec :
```env
POSTGRES_USER=datanova
POSTGRES_PASSWORD=un_mot_de_passe_securise
POSTGRES_DB=datanova
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
BREVO_API_KEY=xkeysib-...
```

### Commandes utiles

```bash
# Voir les logs en temps réel
docker-compose logs -f backend

# Redémarrer un service
docker-compose restart backend

# Tout arrêter
docker-compose down

# Tout arrêter et supprimer les données
docker-compose down -v
```

---

## 2.10 Déploiement sur Azure

Le projet inclut un script `deploy.sh` et des fichiers Terraform pour le déploiement Azure.

### Avec Terraform

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Éditez terraform.tfvars avec vos valeurs Azure

terraform init
terraform plan
terraform apply
```

### Avec le script de déploiement

```bash
# Se connecter à Azure d'abord
az login

# Lancer le déploiement
./deploy.sh
```

---

# Partie 3 — Manuel d'utilisation du frontend

## 3.1 Accéder à l'application

Ouvrez votre navigateur (Chrome, Firefox, Edge, Safari) et allez sur :

- **En développement :** `http://localhost:3000`
- **En production :** L'URL fournie par votre administrateur

Vous arrivez sur la **page d'accueil** :

```
┌──────────────────────────────────────────────────┐
│  🏭 HUTCHINSON                   [S'identifier]  │
│                                  [Créer un compte]│
│                                                    │
│  Propulsé par IA Agentique                        │
│                                                    │
│  MAÎTRISEZ LE PRÉSENT,                           │
│  DÉFINISSEZ LE FUTUR.                             │
│                                                    │
│  Plateforme d'Intelligence Proactive              │
│  pour la Veille Réglementaire                     │
│                                                    │
│           [Démarrer l'audit →]                    │
│                                                    │
└──────────────────────────────────────────────────┘
```

---

## 3.2 Créer un compte

1. Cliquez sur **« Créer un compte »** (en haut à droite ou bouton vert)
2. Remplissez le formulaire :

| Champ | Description | Exemple |
|-------|-------------|---------|
| Nom complet | Votre nom et prénom | Jean Dupont |
| Rôle | Votre fonction | « Analyste Juridique » ou « Décisionnaire » |
| Email corporatif | Votre email professionnel | j.dupont@hutchinson.com |
| Mot de passe | Minimum 6 caractères | ••••••••• |
| Conditions | Cochez la case d'acceptation | ☑ |

3. Cliquez sur **« Créer mon compte »**
4. Un message de confirmation apparaît, puis vous êtes redirigé vers la page de connexion

> **Rôles disponibles :**
> - **Analyste Juridique** : accès aux analyses, réglementations, rapports
> - **Décisionnaire** : accès complet + panneau d'administration

---

## 3.3 Se connecter

1. Cliquez sur **« S'identifier »**
2. Entrez votre email et mot de passe
3. Cliquez sur **« Authentification »**
4. Vous êtes redirigé vers le **tableau de bord**

> Votre session reste active même si vous fermez l'onglet. Pour vous déconnecter, utilisez le bouton **« Logout »** dans la barre latérale gauche.

---

## 3.4 Le tableau de bord principal

C'est la page centrale de l'application. Elle est composée de :

### La barre latérale gauche (toujours visible)

```
┌─────────────────┐
│ 🏭 HUTCHINSON   │
│ DATANOVA RISK   │
│ PLATFORM        │
│                 │
│ 📊 Dashboard   │  ← Vue d'ensemble
│ 📜 Réglementat.│  ← Risques réglementaires
│ 🌡️ Climat      │  ← Risques climatiques
│ 🌍 Géopolitique│  ← Risques géopolitiques
│ ⚙️ Administr.  │  ← (admin uniquement)
│                 │
│ 👤 Jean Dupont │
│    Analyste    │
│                 │
│ 🔔 Abonnements│  ← Gérer les alertes email
│ 🚪 Logout     │
└─────────────────┘
```

### La vue d'ensemble (onglet « Dashboard »)

En haut :

**1. Matrice de risques avancée** — Un graphique interactif qui place chaque risque selon sa probabilité (axe X) et son impact (axe Y). Les points sont colorés par niveau :
- 🟢 **Vert** (0-25%) : Risque faible
- 🟡 **Jaune** (25-50%) : Risque moyen
- 🟠 **Orange** (50-75%) : Risque élevé
- 🔴 **Rouge** (75-100%) : Risque critique

> **Astuce :** Cliquez sur un point pour voir le détail de ce risque.

**2. Top 10 des risques critiques** — Un tableau listant les menaces les plus graves :

| Colonne | Description |
|---------|-------------|
| # | Numéro d'ordre |
| Risque | Titre du document + extrait |
| Catégorie | Badge coloré : Réglementations / Climat / Géopolitique |
| Niveau | Badge : Critique / Élevé / Moyen / Faible (avec couleur) |
| Date | Date de collecte |
| Action | Bouton **« Détails »** pour ouvrir le rapport complet |

**3. Carte mondiale** — Une carte interactive (Leaflet) montrant :
- **Marqueurs ronds** : Fournisseurs (taille proportionnelle au risque)
- **Marqueurs carrés « H »** : Sites Hutchinson
- Couleurs : 🟢 faible, 🟡 moyen, 🔴 élevé
- Les marqueurs à haut risque pulsent pour attirer l'attention

> **Astuce :** Cliquez sur un marqueur pour voir les détails du fournisseur ou du site.

**4. Cartes KPI** — 4 indicateurs clés en bas :

| Carte | Ce qu'elle montre |
|-------|-------------------|
| Alertes Actives | Nombre total d'analyses d'impact + nombre critique |
| Risques Critiques | Nombre de risques au niveau CRITIQUE |
| Score de Risque | Score moyen global sur 100 |
| Documents | Nombre total de réglementations traitées |

**5. Bouton « Analyser un Fournisseur »** — Lance l'analyse à la demande (voir section 3.10).

---

## 3.5 Onglet Réglementations

Cliquez sur **« Réglementations »** dans la barre latérale. Cette vue se concentre sur les risques réglementaires européens.

### Ce que vous voyez

**En haut — Deux panneaux côte à côte :**
- **À gauche :** Matrice de risques (uniquement réglementaire)
- **À droite :** Carte des fournisseurs impactés

**En bas — Inventaire des menaces :**

Une grille de cartes, chacune représentant un risque. Chaque carte affiche :
- Le titre de la réglementation
- La date de collecte
- Un badge d'impact (Faible → Critique) avec point coloré
- Un graphique circulaire montrant le score
- Le nombre de sites et fournisseurs affectés
- Un extrait de la synthèse (cliquez « Voir plus » pour l'intégralité)
- Un bouton **« Voir détails → »** pour ouvrir le rapport complet

### Filtrer les risques

1. Cliquez sur le bouton **« Filtrer »** (icône entonnoir en haut de l'inventaire)
2. Cochez les niveaux qui vous intéressent :
   - ☑ Critique
   - ☑ Élevé
   - ☐ Moyen
   - ☐ Faible
3. Cliquez **« Appliquer »**

Un badge sur le bouton filtre indique combien de filtres sont actifs.

### Rechercher un risque

Utilisez la **barre de recherche** en haut à droite (loupe) pour rechercher par mot-clé.

---

## 3.6 Onglet Climat

Cliquez sur **« Climat »** dans la barre latérale. Même disposition que Réglementations, mais filtrée sur les risques climatiques.

La carte montre à la fois les fournisseurs ET les sites Hutchinson, avec des compteurs en haut à droite (ex: « 3 fournisseurs à risque élevé / 12 total »).

Les risques climatiques incluent :
- Tempêtes et vents violents
- Canicules et vagues de froid
- Fortes pluies et inondations
- Chutes de neige

---

## 3.7 Onglet Géopolitique

Cet onglet est **en cours de développement**. Il affichera à terme :
- Tensions internationales et conflits
- Sanctions économiques
- Instabilités politiques
- Perturbations supply chain liées à la géopolitique

---

## 3.8 Consulter le détail d'un risque

Quand vous cliquez sur **« Détails »** ou **« Voir détails → »** sur n'importe quel risque, une fenêtre modale s'ouvre avec le rapport complet :

```
┌──────────────────────────────────────────────────────┐
│  [X Fermer]                                          │
│                                                       │
│  📄 Règlement (UE) 2023/956 — CBAM                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━              │
│  Niveau : 🔴 CRITIQUE    Score : 82.75 / 100         │
│                                                       │
│  ── Résumé exécutif ──────────────────────            │
│  Sévérité: 85/100  Urgence: 78/100  BI: 71/100      │
│                                                       │
│  ── Sites affectés ───────────────────────            │
│  ┌──────────────┬──────────┬──────────┬──────┐       │
│  │ Site         │ Score    │ Proba    │ Jours│       │
│  ├──────────────┼──────────┼──────────┼──────┤       │
│  │ Le Havre     │ 85.2/100 │ 92%      │ 45   │       │
│  │ Montargis    │ 72.1/100 │ 78%      │ 30   │       │
│  └──────────────┴──────────┴──────────┴──────┘       │
│                                                       │
│  ── Fournisseurs affectés ────────────────            │
│  ┌──────────────┬──────────┬──────────┬──────┐       │
│  │ Fournisseur  │ Score    │ Proba    │ Jours│       │
│  ├──────────────┼──────────┼──────────┼──────┤       │
│  │ Supplier X   │ 78.1/100 │ 85%      │ 60   │       │
│  └──────────────┴──────────┴──────────┴──────┘       │
│                                                       │
│  ── Recommandations ──────────────────────            │
│  1. 🔴 HAUTE PRIORITÉ                                │
│     Action : Auditer les fournisseurs CBAM            │
│     Timeline : Q1 2026                                │
│     Budget : 50 000 €                                 │
│     Risque si inaction : Surtaxe carbone 35%          │
│                                                       │
│  2. 🟠 MOYENNE PRIORITÉ                              │
│     Action : Former les équipes achats                │
│     ...                                               │
│                                                       │
│              [📥 Télécharger le rapport PDF]          │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### Informations disponibles dans le rapport

| Section | Contenu |
|---------|---------|
| **Résumé exécutif** | Scores de sévérité, urgence et Business Interruption |
| **Sites affectés** | Tableau avec score de risque, probabilité d'impact, durée estimée |
| **Fournisseurs affectés** | Même format que les sites |
| **Résumé météo** | Alertes météo actives dans la zone (si applicable) |
| **Analyse détaillée** | Évaluation globale, détail par entité, analyse de criticité |
| **Recommandations** | Actions priorisées avec urgence, timeline, budget, responsable, ROI estimé |

---

## 3.9 La carte des fournisseurs

La carte interactive est présente sur le Dashboard et les onglets par catégorie.

### Comment l'utiliser

1. **Zoom** : Molette de la souris ou boutons +/- en haut à gauche
2. **Naviguer** : Cliquer-glisser pour se déplacer
3. **Cliquer sur un marqueur** : Ouvre une bulle d'information

### Bulle fournisseur

En cliquant sur un fournisseur (cercle), vous voyez :
- Son nom, ville et pays
- Son niveau de risque (badge coloré)
- Le nombre d'alertes actives
- Les 3 premières réglementations qui le touchent
- Un bouton **« Voir détails »**

### Profil fournisseur complet

En cliquant sur **« Voir profil complet »** dans la bulle, une fenêtre modale s'ouvre avec :

| Section | Contenu |
|---------|---------|
| **Informations générales** | Code, secteur, année de fondation, effectifs |
| **Données financières** | Chiffre d'affaires, volume d'achats, valeur livraisons quotidiennes |
| **Logistique** | Stock moyen (jours), délai de substitution, capacité extensible |
| **Produits fournis** | Liste sous forme de badges bleus |
| **Certifications** | Badges verts (ISO 9001, IATF 16949, etc.) |
| **Exposition aux risques** | Sites desservis, relations critiques, fournisseur unique, couverture backup |
| **Sites desservis** | Liste détaillée : criticité, volume annuel, produits par site |

---

## 3.10 Analyser un fournisseur à la demande

Cette fonctionnalité permet d'auditer n'importe quel fournisseur en dehors du cycle automatique.

### Étapes

1. Depuis le Dashboard, cliquez sur **« Lancer une Analyse »** (carte sombre en bas)
   - Ou naviguez via le menu si disponible

2. **Remplissez le formulaire :**

```
┌──────────────────────────────────────────────┐
│                                               │
│  📋 Informations du fournisseur               │
│  ─────────────────────────────                │
│  Nom* :     [Fournisseur Alpha         ]     │
│  Pays* :    [France ▼                   ]     │
│  Ville :    [Lyon                       ]     │
│  Latitude : [45.764]  Longitude: [4.835]     │
│                                               │
│  📦 Matières fournies*                        │
│  ─────────────────────                        │
│  [Caoutchouc] [Élastomère] [+ Ajouter]      │
│                                               │
│  🏷️ Codes NC (douaniers)                      │
│  ────────────────────────                     │
│  [4002.19] [4016.93] [+ Ajouter]             │
│                                               │
│  ⚡ Importance                                │
│  ────────────                                 │
│  (○) Standard  (●) Important  (○) Critique   │
│  Volume annuel (€) : [2 500 000]             │
│                                               │
│        [🔍 Analyser les risques]              │
│                                               │
└──────────────────────────────────────────────┘
```

3. Cliquez sur **« Analyser les risques »**
4. Attendez ~30 secondes (l'IA analyse les risques réglementaires + météo)

### Page de résultats

Après l'analyse, vous voyez :

| Section | Description |
|---------|-------------|
| **Score de risque global** | Barre colorée de 0 à 10 avec badge de niveau |
| **Statistiques rapides** | Nombre de risques réglementaires + alertes météo |
| **Risques réglementaires** | Liste de documents EUR-Lex pertinents avec badge de pertinence (HIGH/MEDIUM/LOW), lien direct vers EUR-Lex, bouton téléchargement PDF |
| **Alertes météo** | Liste d'alertes avec type, sévérité, date, mesure vs seuil, impact supply chain |
| **Recommandations** | Actions priorisées (Haute/Moyenne/Basse) avec détails |
| **Résumé du fournisseur** | Récapitulatif de toutes les informations saisies |

---

## 3.11 Gérer ses abonnements aux alertes

Les abonnements vous permettent de recevoir des **emails automatiques** quand un nouveau risque est détecté correspondant à vos critères.

### Accéder aux abonnements

Cliquez sur **« Abonnements »** dans la barre latérale gauche (en bas).

### Créer un abonnement

1. Cliquez sur **« Nouvel abonnement »**
2. Remplissez le formulaire :

| Champ | Description | Exemple |
|-------|-------------|---------|
| Nom | Nom de l'abonnement | « Alertes CBAM critiques » |
| Types d'alertes | Cochez les types souhaités | ☑ Réglementaire ☑ Climatique |
| Criticité minimum | Seuil minimum pour être alerté | « Élevé » = vous ne recevez que les élevés et critiques |
| Fournisseurs | Fournisseurs spécifiques (ou laissez vide = tous) | ☑ Supplier Alpha ☑ Supplier Beta |
| Sites | Sites spécifiques (ou laissez vide = tous) | ☑ Le Havre |
| Pays | Pays spécifiques (ou laissez vide = tous) | France, Allemagne |
| Options | Notifications immédiates, inclure météo, etc. | ☑ Notification immédiate |

3. Cliquez sur **« Créer »**

### Gérer ses abonnements existants

Pour chaque abonnement, vous pouvez :
- **Pause/Play** : Suspendre temporairement sans supprimer
- **Modifier** : Changer les critères
- **Supprimer** : Supprimer définitivement

---

## 3.12 Le centre de notifications

### Accéder aux notifications

Cliquez sur l'**icône cloche** 🔔 en haut à droite du Dashboard.

Un badge rouge indique le nombre de notifications non lues.

### Ce que vous voyez

- Liste des notifications récentes, chacune avec :
  - Un point coloré indiquant la catégorie (🟢 Climat, 🔴 Géopolitique, 🔵 Réglementations)
  - Le titre de l'alerte
  - Une description courte
  - L'horodatage
- Bouton **« Tout marquer comme lu »** en bas

### Notifications temps réel

Quand un nouveau risque est détecté par le pipeline, une notification **toast** apparaît en haut à droite de l'écran avec une animation.

---

## 3.13 Panneau d'administration

> **Accès réservé** aux utilisateurs ayant le rôle « Décisionnaire » (admin).

Cliquez sur **« Administration »** dans la barre latérale pour accéder au panneau complet.

### Onglets disponibles

#### 1. Sources de données

Gérer les sources utilisées par l'Agent 1A pour collecter les documents.

| Action | Comment |
|--------|---------|
| Voir les sources | Liste avec nom, type, statut (actif/inactif) |
| Ajouter une source | Bouton « + Ajouter une source » → formulaire |
| Activer/Désactiver | Toggle sur chaque carte |
| Modifier | Bouton crayon sur chaque carte |
| Supprimer | Bouton poubelle |

#### 2. Fournisseurs

Gestion CRUD des fournisseurs dans la base de données.

| Champ | Description |
|-------|-------------|
| Nom, Code | Identifiants |
| Pays, Région, Ville | Localisation |
| Latitude, Longitude | Coordonnées GPS (pour la carte et le calcul de distance) |
| Secteur, Produits | Activité |
| Taille | PME / ETI / Grande Entreprise |
| Score de criticité | Curseur 0–10 |
| Actif | Toggle on/off |

#### 3. Sites Hutchinson

Même principe que les fournisseurs, pour les propres sites d'Hutchinson.

Champs supplémentaires :
- Importance stratégique (Faible / Moyenne / Élevée / Critique)
- Effectifs, valeur production annuelle
- Chiffre d'affaires journalier
- Secteurs, produits, matières premières
- Certifications

#### 4. Catégories de risques

Gérer les types de risques surveillés :
- **Réglementaire** (📜)
- **Climatique** (🌡️)
- **Géopolitique** (🌍)

Vous pouvez ajouter de nouvelles catégories ou désactiver des catégories existantes.

#### 5. Planification (Scheduler)

Configurer la fréquence d'exécution automatique du pipeline :

| Paramètre | Options |
|-----------|---------|
| Fréquence | Quotidien / Hebdomadaire / Mensuel |
| Heure | Heure d'exécution |
| Jour (si hebdo) | Lundi, Mardi, ... Dimanche |
| Actif | Active/désactive le scheduler |

**Bouton « Lancer une analyse maintenant »** : Déclenche immédiatement le pipeline complet. Après exécution, affiche :
- Nombre de documents collectés
- Nombre d'analyses de risque générées
- Nombre de notifications envoyées

#### 6. Statistiques

Vue d'ensemble de l'état du système :
- Total documents en base
- Total analyses
- Nombre de sites et fournisseurs
- Sources actives / inactives
- Statut du scheduler

#### 7. Utilisateurs

Gérer les comptes utilisateurs :

| Action | Description |
|--------|-------------|
| Approuver | Valider un nouveau compte (bouton vert) |
| Rejeter | Refuser un compte (bouton rouge) |
| Rechercher | Barre de recherche par nom ou email |
| Filtrer | Onglets : En attente / Approuvés / Rejetés / Tous |

---

## 3.14 Exporter un rapport PDF

### Depuis le détail d'un risque

1. Ouvrez le détail d'un risque (bouton « Détails »)
2. Cliquez sur **« Télécharger le rapport PDF »** en bas de la fenêtre
3. Un fichier PDF professionnel est généré avec :
   - En-tête avec logo et informations du rapport
   - Résumé exécutif avec scores
   - Tableaux des sites et fournisseurs affectés
   - Données météo
   - Recommandations priorisées
   - Tout est coloré par niveau de risque

### Depuis l'inventaire des menaces

1. Dans un onglet (Réglementations, Climat), cliquez sur le bouton **« Rapport PDF »** en haut de l'inventaire
2. Un PDF récapitulatif est généré avec la liste de tous les risques visibles

---

# Partie 4 — Continuer le projet

## 4.1 Architecture du code

### Backend (Python)

```
backend/src/
├── api/
│   ├── main.py              ← Point d'entrée FastAPI
│   └── routes/              ← 8 fichiers de routes (69 endpoints au total)
├── agent_1a/                ← Agent 1A : collecte EUR-Lex + météo
│   ├── agent.py             ← Logique principale
│   └── tools/               ← Scraper, PDF, météo, mots-clés
├── agent_1b/                ← Agent 1B : pertinence (100% LLM)
│   └── agent.py             ← Scoring sémantique
├── agent_2/                 ← Agent 2 : analyse d'impact 360°
│   ├── agent.py             ← Orchestrateur
│   ├── geographic_engine.py ← Calcul distance Haversine
│   ├── weather_risk_engine.py ← Agrégation risques météo
│   ├── criticality_analyzer.py ← Criticité supply chain
│   ├── regulatory_geopolitical_engine.py ← Projection réglementaire
│   └── llm_reasoning.py     ← Génération recommandations (LLM)
├── llm_judge/               ← LLM Judge : validation qualité
│   ├── judge.py             ← Évaluation + décision
│   └── prompts.py           ← Prompts d'évaluation
├── orchestration/           ← Workflow complet
│   ├── langgraph_workflow.py ← Pipeline LangGraph
│   └── scheduler.py         ← Planification APScheduler
├── notifications/           ← Envoi d'emails
│   ├── notification_service.py
│   └── email_sender.py      ← Intégration Brevo
├── storage/                 ← Base de données
│   ├── models.py            ← 20 modèles SQLAlchemy
│   └── database.py          ← Configuration connexion
├── config.py                ← Configuration Pydantic Settings
└── risk_categories.py       ← Gestion catégories de risques
```

### Frontend (React TypeScript)

```
frontend/src/
├── App.tsx                  ← Composant racine + routage
├── pages/
│   ├── Landing.tsx          ← Page d'accueil
│   ├── Login.tsx            ← Connexion
│   ├── Register.tsx         ← Inscription
│   ├── Dashboard.tsx        ← Tableau de bord principal (1681 lignes)
│   ├── AgentDashboard.tsx   ← Lancement agents
│   ├── SupplierAnalysis.tsx ← Formulaire analyse fournisseur
│   ├── SupplierAnalysisResults.tsx ← Résultats analyse
│   └── AdminPanel.tsx       ← Panneau administration (2183 lignes)
├── components/
│   ├── RiskMatrixAdvanced.tsx   ← Matrice probabilité × impact
│   ├── RiskMatrix.tsx           ← Matrice 3×3 simplifiée
│   ├── RiskTable.tsx            ← Grille de cartes risques
│   ├── RiskDetailModal.tsx      ← Rapport détaillé (1205 lignes)
│   ├── SupplierMap.tsx          ← Carte Leaflet interactive
│   ├── SupplierProfileModal.tsx ← Profil complet fournisseur
│   ├── NotificationCenter.tsx   ← Centre de notifications
│   ├── SubscriptionSettings.tsx ← Gestion abonnements
│   └── RiskDonutChart.tsx       ← Graphiques répartition
├── services/
│   ├── api.ts                   ← Configuration fetch commune
│   ├── authService.ts           ← Authentification
│   ├── regulationsService.ts    ← Réglementations
│   ├── impactsService.ts        ← Analyses d'impact
│   ├── supplierService.ts       ← Fournisseurs
│   └── subscriptionService.ts   ← Abonnements
└── config/
    └── app.config.ts            ← URL API
```

---

## 4.2 Ajouter une nouvelle source de données

### Via l'interface (sans code)

1. Allez dans **Administration → Sources de données**
2. Cliquez **« Ajouter une source »**
3. Remplissez : nom, description, type, type de risque, URL, clé API

### Via le code (pour développeurs)

Pour ajouter un nouveau collecteur (ex: une API RSS d'actualités) :

1. Créez un nouveau fichier dans `backend/src/agent_1a/tools/` (ex: `rss_scraper.py`)
2. Implémentez une fonction de collecte qui retourne une liste de documents
3. Intégrez-la dans `backend/src/agent_1a/agent.py` → méthode `run_agent_1a_full_collection()`
4. Ajoutez la source dans `backend/config/sources.json`

---

## 4.3 Modifier les seuils de risque

### Score de pertinence (Agent 1B)

Dans `backend/src/agent_1b/agent.py`, les seuils de décision sont :

```python
# Score LLM ≥ 0.6  → OUI (pertinent)
# Score LLM ≥ 0.4  → PARTIELLEMENT
# Score LLM < 0.4  → NON (non pertinent)
```

### Score de risque 360° (Agent 2)

Formule dans `backend/src/agent_2/agent.py` :

```python
risk_score_360 = 0.30 × severity + 0.25 × probability + 0.25 × exposure + 0.20 × urgency
```

Les poids sont modifiables dans le même fichier.

### Niveaux de risque

```python
0–25   → FAIBLE
25–50  → MOYEN
50–75  → ÉLEVÉ
75–100 → CRITIQUE
```

### Décisions du Judge

Dans `backend/src/llm_judge/judge.py` :

```python
Score ≥ 8.5 et confiance ≥ 0.85  → APPROVE (publié)
Score ≥ 7.0                       → REVIEW (relecture humaine)
Score < 7.0                       → REJECT (archivé)
```

---

## 4.4 Ajouter une catégorie de risque

### Via l'interface

Administration → Catégories de risques → « Ajouter une catégorie »

### Via le fichier de configuration

Éditez `backend/config/risk_categories.json` :

```json
[
  {"code": "regulatory", "name": "Réglementaire", "event_type": "reglementaire", "icon": "📜", "active": true},
  {"code": "climate", "name": "Climatique", "event_type": "climatique", "icon": "🌡️", "active": true},
  {"code": "geopolitical", "name": "Géopolitique", "event_type": "geopolitique", "icon": "🌍", "active": true},
  {"code": "cyber", "name": "Cybersécurité", "event_type": "cyber", "icon": "🔒", "active": true}
]
```

> **Note :** L'ajout d'une catégorie nécessite aussi de coder la logique de collecte et d'analyse correspondante dans les Agents 1A, 1B et 2.

---

## 4.5 Mettre à jour le profil Hutchinson

Le profil entreprise est stocké dans `backend/data/company_profiles/Hutchinson_SA.json`.

Ce fichier contient :
- **Informations entreprise** : nom, secteur, pays
- **Sites** : liste complète avec coordonnées GPS
- **Fournisseurs** : principaux avec localisation
- **Produits** : catalogue de produits
- **Codes NC** : nomenclature douanière
- **Supply chain** : détails logistiques
- **Réglementations surveillées** : mots-clés prioritaires

Pour mettre à jour :
1. Éditez le fichier JSON directement
2. Ou utilisez le panneau d'administration pour ajouter/modifier des sites et fournisseurs

---

## 4.6 Maintenir et mettre à jour les dépendances

### Backend

```bash
cd backend
source .venv/bin/activate

# Mettre à jour toutes les dépendances
pip install --upgrade -e .

# Appliquer les migrations de base de données (si nouvelles)
alembic upgrade head
```

### Frontend

```bash
cd frontend

# Vérifier les mises à jour disponibles
npm outdated

# Mettre à jour
npm update

# Rebuilder
npm run build
```

---

## 4.7 Problèmes courants et solutions

### Le backend ne démarre pas

| Symptôme | Solution |
|----------|----------|
| `ModuleNotFoundError` | Vérifiez que l'environnement virtuel est activé : `source .venv/bin/activate` |
| `Address already in use` (port 8000) | Un autre processus utilise le port. Tuez-le : `lsof -ti :8000 \| xargs kill -9` |
| `ANTHROPIC_API_KEY not set` | Vérifiez que le fichier `.env` existe et contient la clé |
| Erreur de base de données | Relancez les migrations : `alembic upgrade head` |

### Le frontend affiche une page blanche

| Symptôme | Solution |
|----------|----------|
| Erreur réseau dans la console | Vérifiez que le backend tourne sur le port 8000 |
| `npm run dev` échoue | Relancez `npm install` puis `npm run dev` |
| Proxy erreur | Vérifiez que `vite.config.ts` redirige vers `localhost:8000` |

### Le pipeline ne produit pas de résultats

| Symptôme | Solution |
|----------|----------|
| 0 documents collectés | Vérifiez votre connexion internet et l'accès à EUR-Lex |
| 0 documents pertinents | La clé Anthropic est peut-être invalide. Vérifiez dans `.env` |
| Erreur rate limit | Attendez 1 minute et relancez. Les API ont des limites d'appels |
| Score Judge toujours REJECT | La clé OpenAI est peut-être invalide |

### Réinitialiser la base de données

```bash
cd backend
source .venv/bin/activate

# Option 1 : Supprimer et recréer toutes les tables
rm data/datanova.db
alembic upgrade head

# Option 2 : Vider uniquement les données d'analyse
python -c "
import sqlite3
conn = sqlite3.connect('data/datanova.db')
cursor = conn.cursor()
cursor.execute('DELETE FROM risk_projections')
cursor.execute('DELETE FROM risk_analyses')
cursor.execute('DELETE FROM pertinence_checks')
cursor.execute('DELETE FROM documents')
conn.commit()
conn.close()
print('Base vidée avec succès')
"
```

### Arrêter et relancer proprement

```bash
# Arrêter le backend
# Dans le terminal backend : Ctrl+C

# Arrêter le frontend
# Dans le terminal frontend : Ctrl+C

# Relancer le backend
cd backend && source .venv/bin/activate && uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Relancer le frontend
cd frontend && npm run dev
```

---

## Contact et support

Pour toute question technique sur le projet, consultez :
- **Documentation technique détaillée :** `docs/DOCUMENTATION_TECHNIQUE.md`
- **Contrat d'API :** `backend/docs/API_CONTRACT.yaml`
- **Schéma BDD complet :** `docs/schema_bdd_ping_complet.md`

---

*Document rédigé le 06/02/2026*  
*Projet PING DataNova — Équipe ESIGELEC*  
*Version 1.0*
