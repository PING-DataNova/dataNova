# 📋 CAHIER DES CHARGES - Projet PING DataNova

**Version:** 1.0  
**Date:** 06 février 2026  
**Client:** Hutchinson (Groupe TotalEnergies)  
**Équipe projet:** ESIGELEC PING

---

# PARTIE 1 : DEMANDE CLIENT

## 1.1 Contexte et enjeux

### 1.1.1 Présentation du client

**Hutchinson** est un équipementier automobile et aéronautique, filiale du groupe TotalEnergies. L'entreprise dispose de :
- **90 sites de production** répartis dans le monde entier
- **16 000 fournisseurs** actifs dans la supply chain
- Des activités dans les secteurs **automobile, aéronautique et industriel**

### 1.1.2 Problématique actuelle

La gestion des risques supply chain chez Hutchinson fait face à plusieurs défis majeurs :

| Problème | Impact |
|----------|--------|
| Analyse manuelle chronophage | 4 heures pour analyser UN seul fournisseur |
| Volume de données ingérable | Impossible de surveiller 16 000 fournisseurs manuellement |
| Approche réactive | Les problèmes sont découverts après leur survenue |
| Dispersion des sources | Informations réparties entre EUR-Lex, météo, actualités géopolitiques |
| Absence de vision globale | Pas de tableau de bord consolidé des risques |

### 1.1.3 Vision du client

> *"La valeur de l'application, c'est qu'elle, le matin, comme aux infos, elle vient vous dire : 'Tiens, il se passe quelque chose à tel endroit et ça impacte un fournisseur.' Ce n'est pas vous qui cherchez l'information. C'est l'information qui vient à vous."*
> — Citation du client, réunion du 03/02/2026

---

## 1.2 Expression des besoins fonctionnels

### 1.2.1 Objectif principal

Développer une **plateforme intelligente de surveillance proactive des risques supply chain** capable de :

1. **Collecter automatiquement** les informations depuis des sources officielles (réglementaires, météorologiques, géopolitiques)
2. **Analyser la pertinence** des informations collectées par rapport au profil de l'entreprise
3. **Évaluer l'impact** sur les sites Hutchinson et les fournisseurs
4. **Alerter les équipes** AVANT que les problèmes n'arrivent
5. **Générer des rapports actionnables** avec recommandations concrètes

### 1.2.2 Types de risques à surveiller

| Type de risque | Sources | Exemples |
|----------------|---------|----------|
| **Réglementaire** | EUR-Lex (API SOAP) | CBAM, EUDR, CSRD, sanctions, contrôle export |
| **Climatique** | Open-Meteo (API REST) | Inondations, tempêtes, sécheresses, tsunamis |
| **Géopolitique** | À définir (ACLED, OMS...) | Conflits, embargos, crises sanitaires |

### 1.2.3 Fonctionnalités demandées

#### A. Analyse automatique programmée (Priorité 1)

Le système doit pouvoir lancer des analyses de manière **automatique et planifiée** :

- **Fréquence paramétrable** : toutes les heures, quotidien, hebdomadaire, manuel
- **Heure configurable** : par défaut 06h00 pour avoir les résultats au matin
- **Périmètre** : tous les sites + tous les fournisseurs + toutes les sources configurées

> *"Au moins qu'il y ait la mécanique d'orchestration qui permet, de manière paramétrée, de dire combien de fois l'administrateur souhaite lancer l'analyse."*

#### B. Dashboard consolidé (Priorité 1)

Page d'accueil affichant :
- **KPIs synthétiques** : nombre de risques actifs par catégorie
- **TOP 5/10 des risques critiques** du jour
- **Carte mondiale** avec localisation des risques
- **Évolution sur 30 jours** des risques détectés

#### C. Pages par type de risque (Priorité 1)

Pour chaque catégorie (réglementaire, climatique, géopolitique) :
- **Matrice Risque × Impact** : visualisation graphique pour identifier les zones critiques
- **Liste filtrable** des risques avec scores
- **Filtres** : par période, région, matière, criticité

> *"Ce qui va nous intéresser, c'est la partie en haut à droite : risque fort, impact fort."*

#### D. Rapport détaillé (Priorité 1)

Chaque rapport doit obligatoirement contenir :

1. **Mention IA obligatoire** : "Ce rapport a été généré automatiquement par une IA. Score de confiance : XX%"
2. **Source citée** : document réglementaire avec lien vers EUR-Lex
3. **Entités impactées** : liste des sites et fournisseurs concernés
4. **Analyse d'impact** : financier, délais, risques associés
5. **Recommandations actionnables** : actions concrètes priorisées

> *"À chaque fois, vous mettez la source. L'utilisateur peut cliquer sur la source pour aller voir effectivement."*

#### E. Analyse à la demande (Priorité 2)

Permettre à un utilisateur de :
- Saisir les informations d'un fournisseur spécifique
- Lancer une analyse ciblée
- Obtenir un rapport personnalisé

#### F. Système de notifications (Priorité 2)

- **Notification email** automatique pour les risques critiques (score ≥ 7.0)
- **Cloche dans l'application** avec historique des alertes
- **Abonnements personnalisables** par type de risque, région, criticité

#### G. Administration (Priorité V2)

- Gestion des sources d'information (activer/désactiver)
- Ajout de nouvelles catégories de risques
- Paramétrage des fréquences d'analyse
- Gestion des utilisateurs et rôles

### 1.2.4 Données d'entrée requises

| Donnée | Description | Format |
|--------|-------------|--------|
| Sites Hutchinson | 4-5 sites avec coordonnées GPS, CA, employés | Excel/JSON |
| Fournisseurs | 5-10 fournisseurs avec pays, matières, codes NC | JSON |
| Profil entreprise | Codes NC, matières, secteurs d'activité | JSON existant |

---

## 1.3 Architecture technique demandée

### 1.3.1 Flux de traitement

```
Sources externes (EUR-Lex, Open-Meteo, ...)
           ↓
    [ORCHESTRATEUR CRON]
           ↓
    [AGENT 1A] - Collecte documents
           ↓
    [AGENT 1B] - Analyse pertinence + scoring
           ↓
    [AGENT 2] - Analyse d'impact + projections
           ↓
    [LLM JUDGE] - Score de confiance
           ↓
    Score < 7 → REJET
    Score ≥ 7 → AUTO-PUBLIÉ + EMAIL
           ↓
    [BASE DE DONNÉES] - Rapports stockés
           ↓
    [NOTIFICATIONS] - Email + Cloche
```

### 1.3.2 Exigences techniques

- **API RESTful** pour communication frontend/backend
- **Base de données** pour persistance des rapports
- **Scheduler** pour exécution automatique programmée
- **Intégration LLM** (Claude) pour l'analyse intelligente
- **Service email** (Brevo/Sendinblue) pour notifications

---

## 1.4 Priorités et planning

### Phase 1 - MVP (Obligatoire)

| # | Fonctionnalité | Priorité |
|---|----------------|----------|
| 1 | Collecte automatique EUR-Lex | 🔴 Critique |
| 2 | Analyse de pertinence (Agent 1B) | 🔴 Critique |
| 3 | Analyse d'impact (Agent 2) | 🔴 Critique |
| 4 | Dashboard avec TOP risques | 🔴 Critique |
| 5 | Rapport avec mention IA + source | 🔴 Critique |
| 6 | Orchestration programmable | 🔴 Critique |

### Phase 2 - Évolutions

| # | Fonctionnalité | Priorité |
|---|----------------|----------|
| 1 | Notifications email automatiques | 🟠 Haute |
| 2 | Risques climatiques (Open-Meteo) | 🟠 Haute |
| 3 | Interface administration | 🟡 Moyenne |
| 4 | Filtres enregistrables par utilisateur | 🟡 Moyenne |
| 5 | Risques géopolitiques | 🟢 Basse |

---

---

# PARTIE 2 : SCOPE RÉALISÉ

## 2.1 Vue d'ensemble des réalisations

### 2.1.1 Synthèse

Le projet PING DataNova a été développé avec succès selon une architecture multi-agents IA. Voici l'état d'avancement :

| Module | Statut | Commentaire |
|--------|--------|-------------|
| Agent 1A (Collecte) | ✅ Terminé | EUR-Lex opérationnel |
| Agent 1B (Analyse pertinence) | ✅ Terminé | Scoring multi-critères |
| Agent 2 (Analyse impact) | ✅ Terminé | Projections sur sites/fournisseurs |
| LLM Judge | ✅ Terminé | Score de confiance automatique |
| Orchestration | ✅ Terminé | APScheduler intégré |
| Notifications | ✅ Terminé | Email via Brevo |
| Frontend Dashboard | ✅ Terminé | React + TypeScript |
| Base de données | ✅ Terminé | SQLite + Alembic |
| API REST | ✅ Terminé | FastAPI |

---

## 2.2 Agent 1A - Collecte de documents

### 2.2.1 Fonctionnalités implémentées

| Fonctionnalité | Description | Fichier |
|----------------|-------------|---------|
| **Collecte EUR-Lex** | Scraping des documents réglementaires européens via l'API SOAP EUR-Lex | `src/agent_1a/tools/eurlex_collector.py` |
| **Extraction de texte** | Parsing HTML/PDF des documents collectés | `src/agent_1a/tools/pdf_extractor.py` |
| **Détection de codes NC** | Extraction automatique des codes nomenclature combinée | `src/agent_1a/tools/` |
| **Génération de mots-clés** | Extraction intelligente par LLM des mots-clés métier | `src/agent_1a/agent.py` |
| **Stockage documents** | Sauvegarde en base avec hash SHA-256 pour détection de changements | `src/storage/` |

### 2.2.2 Sources de données configurées

| Source | Type | API | Statut |
|--------|------|-----|--------|
| EUR-Lex | Réglementaire | SOAP | ✅ Opérationnel |
| Open-Meteo | Climatique | REST | ✅ Opérationnel |

### 2.2.3 Paramètres configurables

- **max_documents** : 8 documents par collecte (configurable)
- **max_keywords** : 8 mots-clés générés par le LLM
- **Filtres** : par type de document, date, domaines EUR-Lex

---

## 2.3 Agent 1B - Analyse de pertinence

### 2.3.1 Fonctionnalités implémentées

| Fonctionnalité | Description |
|----------------|-------------|
| **Scoring multi-critères** | Évaluation 30% codes NC + 30% mots-clés + 40% analyse LLM |
| **Extraction d'informations** | Dates d'application, périmètre géographique, matières concernées |
| **Classification criticité** | CRITICAL / HIGH / MEDIUM / LOW basée sur le score |
| **Identification processus** | Mapping automatique vers les processus métier impactés |

### 2.3.2 Critères d'évaluation

```
Score final = 0.30 × Score_NC + 0.30 × Score_Keywords + 0.40 × Score_LLM

Criticité :
- CRITICAL : score ≥ 80
- HIGH     : score ≥ 60
- MEDIUM   : score ≥ 40
- LOW      : score < 40
```

---

## 2.4 Agent 2 - Analyse d'impact

### 2.4.1 Fonctionnalités implémentées

| Fonctionnalité | Description | Fichier |
|----------------|-------------|---------|
| **Projection sur sites** | Identification des sites Hutchinson impactés | `src/agent_2/geographic_engine.py` |
| **Projection sur fournisseurs** | Matching fournisseurs par pays, matières, codes NC | `src/agent_2/regulatory_geopolitical_engine.py` |
| **Analyse climatique** | Évaluation des risques météo sur coordonnées GPS | `src/agent_2/weather_risk_engine.py` |
| **Calcul de criticité** | Scoring d'impact business | `src/agent_2/criticality_analyzer.py` |
| **Génération de recommandations** | Actions concrètes via LLM | `src/agent_2/llm_reasoning.py` |

### 2.4.2 Données métier intégrées

- **Sites Hutchinson** : 4 sites de démonstration avec coordonnées GPS
- **Fournisseurs** : 10 fournisseurs avec pays, matières, criticité
- **Profil entreprise** : Codes NC, secteurs, matières premières

---

## 2.5 LLM Judge - Validation automatique

### 2.5.1 Fonctionnalités implémentées

| Fonctionnalité | Description |
|----------------|-------------|
| **Score de confiance** | Évaluation 0-10 de la qualité du rapport |
| **Vérification des sources** | Contrôle que les sources sont citées correctement |
| **Détection d'hallucinations** | Identification des informations non vérifiables |
| **Auto-publication** | Rapports avec score ≥ 7.0 automatiquement publiés |

### 2.5.2 Workflow de validation

```
Rapport généré par Agent 2
         ↓
    [LLM JUDGE]
         ↓
    Score < 7.0 → Rejet (non publié)
    Score ≥ 7.0 → Publication automatique + Email
```

---

## 2.6 Orchestration et Scheduler

### 2.6.1 Fonctionnalités implémentées

| Fonctionnalité | Description | Fichier |
|----------------|-------------|---------|
| **Workflow LangGraph** | Pipeline complet Agent 1A → 1B → 2 → Judge | `src/orchestration/langgraph_workflow.py` |
| **Scheduler APScheduler** | Exécution automatique programmée | `src/api/routes/admin.py` |
| **Fréquences configurables** | Horaire, quotidien, hebdomadaire, manuel | Interface Admin |
| **Exécution manuelle** | Bouton "Lancer l'analyse" dans le dashboard | API `/api/admin/scheduler/run-now` |

### 2.6.2 Configuration du scheduler

- **BackgroundScheduler** avec APScheduler
- **CronTrigger** pour planification précise
- **Intégration FastAPI Lifespan** pour démarrage/arrêt automatique
- **Persistance configuration** en mémoire (améliorable avec Redis)

---

## 2.7 Système de notifications

### 2.7.1 Fonctionnalités implémentées

| Fonctionnalité | Description | Fichier |
|----------------|-------------|---------|
| **Email automatique** | Envoi via Brevo (Sendinblue) | `src/notifications/email_sender.py` |
| **Abonnements** | Système de souscription par utilisateur | `src/notifications/subscription_filter.py` |
| **Filtrage intelligent** | Par type de risque, région, criticité | `src/notifications/router.py` |
| **Mode dry-run** | Test sans envoi réel | Variable `EMAIL_DRY_RUN` |

### 2.7.2 Déclencheurs d'email

- Publication automatique d'un rapport (score ≥ 7.0)
- Nouveau risque critique détecté
- Mise à jour importante d'un risque existant

---

## 2.8 Frontend - Interface utilisateur

### 2.8.1 Pages implémentées

| Page | URL | Description | Statut |
|------|-----|-------------|--------|
| **Landing** | `/` | Page d'accueil publique | ✅ |
| **Login** | `/login` | Authentification | ✅ |
| **Register** | `/register` | Inscription | ✅ |
| **Dashboard** | `/dashboard` | Tableau de bord principal | ✅ |
| **Analyse Fournisseur** | `/supplier-analysis` | Analyse à la demande | ✅ |
| **Résultats Analyse** | `/supplier-analysis-results` | Affichage des résultats | ✅ |
| **Administration** | `/admin` | Paramétrage système | ✅ |

### 2.8.2 Composants développés

| Composant | Description |
|-----------|-------------|
| **RiskMatrix** | Matrice Risque × Impact interactive |
| **RiskTable** | Tableau des risques avec filtres |
| **SupplierMap** | Carte Leaflet avec markers |
| **RiskDonutChart** | Graphiques de répartition |
| **NotificationCenter** | Centre de notifications (cloche) |
| **SubscriptionSettings** | Gestion des abonnements |

### 2.8.3 Technologies utilisées

- **React 18** + **TypeScript**
- **Vite** comme build tool
- **TailwindCSS** pour le styling
- **Leaflet** pour les cartes
- **Recharts** pour les graphiques

---

## 2.9 API Backend

### 2.9.1 Endpoints implémentés

| Route | Méthode | Description |
|-------|---------|-------------|
| `/api/pipeline/agent1` | POST | Lancer Agent 1 (collecte + analyse) |
| `/api/pipeline/agent1/sync` | POST | Lancer Agent 1 en mode synchrone |
| `/api/pipeline/agent1/status` | GET | Statut de l'Agent 1 |
| `/api/pipeline/agent2` | POST | Lancer Agent 2 (impact) |
| `/api/pipeline/agent2/sync` | POST | Lancer Agent 2 en mode synchrone |
| `/api/pipeline/agent2/status` | GET | Statut de l'Agent 2 |
| `/api/admin/scheduler` | GET/POST | Configuration scheduler |
| `/api/admin/scheduler/run-now` | POST | Exécution manuelle |
| `/api/admin/data-sources` | GET/POST/PATCH | Gestion des sources |
| `/api/analyses` | GET | Liste des analyses |
| `/api/analyses/{id}` | GET | Détail d'une analyse |
| `/api/impacts` | GET | Liste des impacts |
| `/api/documents` | GET | Liste des documents |
| `/api/subscriptions` | GET/POST/PATCH/DELETE | Gestion abonnements |
| `/api/supplier/analyze` | POST | Analyse fournisseur à la demande |

### 2.9.2 Technologies

- **FastAPI** framework
- **Pydantic** pour validation
- **SQLAlchemy** pour ORM
- **Alembic** pour migrations

---

## 2.10 Base de données

### 2.10.1 Tables principales

| Table | Description |
|-------|-------------|
| `documents` | Documents collectés avec hash SHA-256 |
| `relevance_analyses` | Résultats Agent 1B |
| `risk_analyses` | Analyses d'impact Agent 2 |
| `hutchinson_sites` | Sites de production |
| `suppliers` | Fournisseurs référencés |
| `notifications` | Historique des notifications |
| `notification_subscriptions` | Abonnements utilisateur |
| `scheduler_config` | Configuration du scheduler |

### 2.10.2 Technologie

- **SQLite** pour développement
- **Alembic** pour gestion des migrations
- Prêt pour migration vers **PostgreSQL** en production

---

## 2.11 Infrastructure et déploiement

### 2.11.1 Configuration locale

```
Backend:  http://localhost:8000
Frontend: http://localhost:3005
```

### 2.11.2 Fichiers de déploiement

| Fichier | Description |
|---------|-------------|
| `docker-compose.yml` | Configuration Docker |
| `Dockerfile` (backend) | Image backend Python |
| `Dockerfile` (frontend) | Image frontend Node.js |
| `deploy.sh` | Script de déploiement |
| `terraform/` | Infrastructure as Code Azure |

---

## 2.12 Fonctionnalités non réalisées (V2)

| Fonctionnalité | Raison | Priorité V2 |
|----------------|--------|-------------|
| Risques géopolitiques | Sources à définir (ACLED, OMS) | Haute |
| Multi-utilisateurs | Besoin d'authentification OAuth | Moyenne |
| Filtres enregistrables | Nécessite profils utilisateur | Moyenne |
| Export PDF des rapports | Librairie à intégrer | Basse |
| Historique/versioning rapports | Architecture à définir | Basse |

---

## 2.13 Métriques du projet

### 2.13.1 Code source

| Composant | Langage | Lignes estimées |
|-----------|---------|-----------------|
| Backend | Python | ~8 000 |
| Frontend | TypeScript/React | ~5 000 |
| Total | | ~13 000 |

### 2.13.2 Tests

- Tests unitaires backend (pytest)
- Tests d'intégration API
- Tests Playwright pour le frontend

---

## 2.14 Documentation livrée

| Document | Description |
|----------|-------------|
| `README.md` | Guide d'installation et démarrage |
| `DEMANDES_CLIENT_COMPLETES.md` | Synthèse réunion client |
| `SPECIFICATIONS_FRONTEND.md` | Spécifications interface |
| `DATABASE_SCHEMA.md` | Schéma base de données |
| `API_CONTRACT.yaml` | Contrat OpenAPI |
| `ROADMAP.md` | Planning du projet |

---

# ANNEXES

## A. Glossaire

| Terme | Définition |
|-------|------------|
| **Agent 1A** | Module de collecte automatique de documents |
| **Agent 1B** | Module d'analyse de pertinence et scoring |
| **Agent 2** | Module d'analyse d'impact et recommandations |
| **LLM Judge** | Validateur automatique basé sur LLM |
| **CBAM** | Carbon Border Adjustment Mechanism (taxe carbone UE) |
| **EUR-Lex** | Portail officiel du droit de l'Union européenne |
| **Code NC** | Nomenclature Combinée (classification douanière) |
| **APScheduler** | Bibliothèque Python de planification de tâches |

## B. Variables d'environnement

```env
# LLM
ANTHROPIC_API_KEY=sk-ant-...

# Email
BREVO_API_KEY=xkeysib-...
EMAIL_SENDER=noreply@datanova.com
EMAIL_DRY_RUN=false

# Database
DATABASE_URL=sqlite:///./data/datanova.db

# API
API_HOST=0.0.0.0
API_PORT=8000
```

---

*Document généré le 06/02/2026*
*Projet PING DataNova - ESIGELEC*
