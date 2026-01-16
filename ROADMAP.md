# 🗺️ ROADMAP - Projet PING (Backend + Frontend)

## 📋 Vue d'ensemble

**Objectif**: Développer un système multi-agents de veille réglementaire automatisée avec validation humaine  
**Équipe Complète**: 6 développeurs
- **Backend**: 5 développeurs (Dev 1, 2, 3, 4, 5)
- **Frontend**: 1 développeur (Dev 6)
**Durée estimée**: 8-10 semaines  
**Phase pilote**: CBAM uniquement  
**Phase extension**: Multi-sources (EUDR, CSRD, Sanctions)

**Architecture**: Agent 1A → Agent 1B → [UI Validation] → Agent 2 → Notifications

---

## 🎯 Phase 1: Setup & Infrastructure (Semaine 1)

### 👨‍💻 Dev 1 (Godson) : Scraping Setup
- [ ] Structure projet scraping (`src/agent_1a/tools/`)
- [ ] Configuration httpx + BeautifulSoup
- [ ] Tests unitaires scraping
- [ ] Documentation API EUR-Lex

### 👨‍💻 Dev 2 : PDF Processing Setup
- [ ] Configuration pdfplumber + pymupdf
- [ ] Fixtures PDF pour tests
- [ ] Tests extraction basique
- [ ] Documentation format PDF EUR-Lex

### 👨‍💻 Dev 3 : Database & Infrastructure
- [x] Structure complète du projet
- [x] Migration Poetry → uv (10-100x plus rapide)
- [x] Base de données SQLite (6 tables, workflow validation)
- [x] Modèles SQLAlchemy (Document, Analysis, ImpactAssessment, Alert, ExecutionLog, CompanyProfile)
- [x] 5 Repositories avec méthodes workflow
- [ ] Script init_db.py amélioré
- [ ] Configuration .env template

### 👨‍💻 Dev 4 (Khadidja) : Agent 2 Setup
- [ ] Structure Agent 2 (`src/agent_2/`)
- [ ] Configuration LangChain
- [ ] Comprendre schéma BDD (analyses, impact_assessments)
- [ ] Tests d'accès BDD basiques

### 👨‍💻 Dev 5 (Willy) : Agent 2 Tools Setup
- [ ] Structure outils Agent 2 (`src/agent_2/tools/`)
- [ ] Étudier données fournisseurs/produits
- [ ] Configuration environnement LLM
- [ ] Tests basiques LangChain

### 👨‍💻 Dev 6 (Narjiss) : Frontend Setup
- [ ] Initialiser projet frontend (Vue.js/React)
- [ ] Configuration API client (axios/fetch)
- [ ] Mock données analyses
- [ ] Interface basique liste

**Livrable Phase 1**: Environnements de dev fonctionnels pour les 6 devs

**✅ Statut**: Dev 3 partiellement complété (BDD OK)

---

## 🤖 Phase 2: Agent 1A + Fondations Agent 2 (Semaine 2) 
### **Jalon : Mercredi 14/01/2026**

### 👨‍💻 Dev 1 (Godson) : Scraping CBAM
**Fichiers**: `src/agent_1a/tools/scraper.py`, `src/agent_1a/tools/document_fetcher.py`

#### Tâches
1. [ ] **Scraper la page CBAM**
   - httpx + BeautifulSoup pour parser HTML
   - Extraire liens EUR-Lex (regex/CSS selectors)
   - Extraire métadonnées (titre, date, type document)
   - Gérer erreurs réseau (retry, timeout)

2. [ ] **Télécharger documents officiels**
   - Télécharger PDF depuis EUR-Lex
   - Calculer hash SHA-256 pour chaque document
   - Sauvegarder dans `data/documents/`
   - Gérer redirections et formats multiples

3. [ ] **Ajouter tests scraping/téléchargement**
   - Tests avec mocks httpx
   - Tests gestion erreurs réseau
   - Tests validation URLs

**Livrables Dev 1**:
- Scraper CBAM fonctionnel
- ~10-15 documents EUR-Lex téléchargés
- Tests couvrant erreurs réseau

---

### 👨‍💻 Dev 2 : Extraction & Détection
**Fichiers**: `src/agent_1a/tools/pdf_extractor.py`, `src/agent_1a/tools/change_detector.py`

#### Tâches
1. [ ] **Extraire texte des PDF**
   - pdfplumber pour extraction texte
   - Extraire tableaux (codes NC notamment)
   - Gérer PDF scannés (OCR si nécessaire)

2. [ ] **Détecter les codes NC**
   - Regex codes NC (format 4002.19, 7606, etc.)
   - Extraire contexte autour du code
   - Valider format codes

3. [ ] **Gérer tableaux, annexes, PDF complexes**
   - Parser tableaux récapitulatifs
   - Identifier sections d'annexes
   - Gérer multi-colonnes et layouts complexes

4. [ ] **Détecter documents nouveaux/modifiés**
   - Comparer hash avec BDD
   - Identifier: nouveau / modifié / inchangé
   - Logger changements détectés

5. [ ] **Tester sur vrais documents CBAM**
   - Tests sur 5+ documents réels
   - Tests cas limites (PDF corrompus)
   - Validation extraction codes NC

**Livrables Dev 2**:
- Extraction texte + codes NC pour tous documents test
- Détecteur de changements fonctionnel
- Tests sur documents CBAM réels

---

### 👨‍💻 Dev 3 : Orchestration Agent 1A
**Fichiers**: `src/agent_1a/agent.py`, `src/orchestration/pipeline.py`, `scripts/manual_run.py`

#### Tâches
1. [ ] **Intégrer les outils Dev 1 & 2 dans Agent 1A**
   - Créer agent LangChain ReAct
   - Intégrer 4 tools: scraper, document_fetcher, pdf_extractor, change_detector
   - Définir prompt système Agent 1A
   - Gérer état et décisions de l'agent

2. [ ] **Piloter le pipeline de bout en bout**
   - Orchestration: scrape → download → extract → detect → save
   - Gestion erreurs par étape
   - Rapport d'exécution détaillé
   - Rollback en cas d'échec

3. [ ] **Gérer les statuts workflow en base**
   - Utiliser DocumentRepository.upsert_document()
   - Mettre à jour workflow_status (raw, analyzed, validated)
   - Sauvegarder ExecutionLog pour chaque run

4. [ ] **Logger exécutions & erreurs**
   - structlog pour logs structurés
   - Niveaux: DEBUG, INFO, WARNING, ERROR
   - Traçabilité complète du pipeline

5. [ ] **Permettre un lancement manuel Agent 1A**
   - Script `scripts/manual_run.py --agent 1a`
   - Arguments: --source cbam, --limit 10
   - Afficher progression en temps réel

**Livrables Dev 3**:
- Agent 1A fonctionnel end-to-end
- Pipeline orchestré avec gestion erreurs
- Lancement manuel opérationnel
- Logs structurés complets

---

### 👨‍💻 Dev 4 (Khadidja) : Récupération Validations
**Fichiers**: `src/agent_2/data_loader.py`, `tests/test_validation_data.py`

#### Tâches
1. [ ] **Récupérer les validations juridiques dans la base de données**
   - Utiliser AnalysisRepository.find_by_validation_status("approved")
   - Lire analyses avec joined documents
   - Charger profil entreprise associé

2. [ ] **Tester la récupération des données par l'Agent 2 depuis la table**
   - Créer données fictives (analyses approved)
   - Tests unitaires récupération
   - Valider structure données retournées
   - Tests avec plusieurs statuts validation

**Livrables Dev 4**:
- Module data_loader.py fonctionnel
- Tests récupération analyses validées
- Documentation format données

---

### 👨‍💻 Dev 5 (Willy) : Agent 2 ReAct Basique
**Fichiers**: `src/agent_2/agent.py`, `src/agent_2/prompts/agent_2_prompt.py`

#### Tâches
1. [ ] **Créer l'Agent 2 ReAct**
   - Initialiser agent LangChain avec ChatAnthropic
   - Structure basique ReAct agent
   - Configuration modèle (Claude 3.5 Sonnet)

2. [ ] **Lire les analyses validées (données fictives)**
   - Intégrer avec data_loader de Dev 4
   - Parser analyses dans prompt
   - Tester avec 3-5 analyses fictives
   - Valider format entrée agent

**Livrables Dev 5**:
- Agent 2 structure basique créée
- Lecture analyses validées fonctionnelle
- Tests avec données fictives

---

### 👨‍💻 Dev 6 (Narjiss) : Frontend Validation UI
**Fichiers**: `frontend/`, `src/api/validation_endpoints.py` (backend)

#### Tâches
1. [ ] **Faire un Frontend fonctionnel**
   - Interface liste analyses (pending validation)
   - Vue détail analyse + document
   - Boutons Approuver/Rejeter + commentaire
   - Design responsive basique

2. [ ] **Créer une logique permettant de lister les données validées (juridiques) dans un format JSON**
   - API endpoint: GET /api/analyses?validation_status=pending
   - API endpoint: POST /api/analyses/{id}/validate
   - Format JSON standardisé
   - **Polling automatique toutes les 30s** (pas de notifications push nécessaires)
   - Tests API avec Postman/curl

**Livrables Dev 6**:
- Frontend liste + détail analyses
- API validation JSON fonctionnelle
- **Système de polling pour nouvelles analyses**
- Documentation API endpoints

**🎯 JALON PHASE 2** : Mercredi 14/01/2026
- Agent 1A collecte documents CBAM
- Agent 2 lit analyses validées
- Frontend affiche et valide analyses

---

## 🧠 Phase 3: Agent 1B + Agent 2 Tools (Semaine 3)

### 👨‍💻 Dev 2  : Analyse LLM Unique
**Fichiers**: `src/agent_1b/tools/semantic_analyzer.py`, `src/agent_1b/agent.py`

#### Tâches
1. [ ] **Analyseur LLM unique**
   - Prompt LLM: recherche mots-clés + codes NC + analyse sémantique
   - Retour JSON: `{is_relevant, confidence, matched_keywords, matched_nc_codes, reasoning}`
   - Charger profil entreprise dans prompt
   - Chunking pour documents longs
   - Cache réponses LLM
   - Tests avec mocks Claude

2. [ ] **Agent 1B simplifié**
   - Un seul outil: semantic_analyzer
   - Créer Analysis avec validation_status="pending"
   - Mettre à jour document.workflow_status
   - Tests end-to-end Agent 1A → 1B

**Livrables Dev 1**:
- Agent 1B fonctionnel
- Analyses sauvegardées en BDD
- Pipeline complet Agent 1A → 1B

---

### 👨‍💻 Dev 1 : Tests & Fixtures
**Fichiers**: `tests/`, `data/fixtures/`

#### Tâches
1. [ ] **Tests Agent 1A**
   - Tests unitaires scraper/fetcher
   - Tests extraction PDF
   - Tests détection changements
   - Fixtures documents CBAM réels

2. [ ] **Tests Agent 1B**
   - Tests semantic_analyzer avec mocks
   - Tests création analyses
   - Tests workflow_status transitions
   - Fixtures analyses attendues

3. [ ] **Données de test complètes**
   - 5+ documents PDF CBAM réels
   - Analyses attendues pour chaque document
   - Profils entreprise variés
   - Couverture > 70%

**Livrables Dev 2**:
- Suite tests Agent 1 complète
- Fixtures réutilisables
- Documentation tests

---

### 👨‍💻 Dev 3 : Scheduler & Pipeline
**Fichiers**: `src/orchestration/scheduler.py`, `src/main.py`

#### Tâches
1. [ ] **APScheduler**
   - Configuration cron hebdomadaire
   - Gestion démarrage/arrêt
   - Retry automatique en cas d'échec
   - Tests avec mock time

2. [ ] **Point d'entrée application**
   - Initialisation app complète
   - Démarrage scheduler automatique
   - Signal handling (SIGTERM, SIGINT)
   - Logs lifecycle application

3. [ ] **Tests d'intégration complets**
   - Test pipeline Agent 1A → 1B
   - Test avec vraies données CBAM
   - Test workflow_status transitions
   - Documentation troubleshooting

**Livrables Dev 3**:
- Scheduler fonctionnel
- Application déployable
- Tests E2E complets

---

### 👨‍💻 Dev 4 (Khadidja) : API Validation
**Fichiers**: `src/api/validation_endpoints.py`, `src/api/server.py`

#### Tâches
1. [ ] **API REST validation**
   - FastAPI ou Flask setup
   - GET /api/analyses?validation_status=pending
   - POST /api/analyses/{id}/validate
   - GET /api/documents/{id}
   - Middleware CORS pour frontend

2. [ ] **Intégration repositories**
   - AnalysisRepository.find_by_validation_status()
   - AnalysisRepository.update_validation()
   - DocumentRepository pour documents complets
   - Tests API (pytest + httpx)

**Livrables Dev 4**:
- API REST documentée (OpenAPI/Swagger)
- Tests endpoints validation

---

### 👨‍💻 Dev 5 (Willy) : Outils Agent 2
**Fichiers**: `src/agent_2/tools/scorer.py`, `src/agent_2/tools/impact_analyzer.py`, `src/agent_2/tools/action_recommender.py`

#### Tâches
1. [ ] **Scoring et criticité**
   - Calculer total_score (0-1)
   - Déterminer criticality (CRITICAL/HIGH/MEDIUM/LOW)
   - Formule: 0.3*suppliers + 0.3*products + 0.2*financial + 0.2*urgency
   - Tests avec cas réels

2. [ ] **Analyse d'impact**
   - Croiser avec fournisseurs (data/suppliers/*.json)
   - Identifier produits impactés (codes NC)
   - Analyser flux douaniers (data/customs_flows/*.json)
   - Estimation financière
   - Tests avec données GMG

3. [ ] **Recommandations**
   - Générer plan d'action (priorités, deadlines)
   - Stratégies atténuation risques
   - Timeline mise en conformité
   - Tests génération

**Livrables Dev 5**:
- 3 outils Agent 2 fonctionnels
- Tests unitaires complets
- Documentation outils

---

### 👨‍💻 Dev 6 (Narjiss) : Frontend Complet
**Fichiers**: `frontend/src/`

#### Tâches
1. [ ] **Interface validation complète**
   - Liste analyses filtrées (pending/approved/rejected)
   - Vue détail enrichie (document + analyse + reasoning)
   - Actions validation (approuver/rejeter + commentaire)
   - Filtres par date, criticité, confiance

2. [ ] **Intégration API backend**
   - Appels API validation
   - Gestion états loading/error
   - Refresh automatique après validation
   - Tests E2E (Playwright/Cypress)

3. [ ] **Dashboard statistiques**
   - Nombre analyses par statut
   - Taux approbation
   - Graphiques évolution
   - Export JSON/CSV

**Livrables Dev 6**:
- Frontend production-ready
- Tests E2E complets
- Documentation utilisateur

**🎯 JALON PHASE 3** :
- Pipeline Agent 1A → 1B → UI validation fonctionnel
- Outils Agent 2 prêts
- API REST documentée
- **Note** : Validation UI via polling API (pas de notifications push nécessaires)

---

## 💼 Phase 4: Agent 2 Production (Semaine 4)

### 👨‍💻 Dev 1 (Godson) : Tests & Documentation
**Fichiers**: `tests/`, `docs/`

#### Tâches
1. [ ] **Tests Agent 1A/1B**
   - Tests unitaires tools
   - Tests intégration agents
   - Tests avec mocks LLM
   - Couverture > 70%

2. [ ] **Documentation technique**
   - README.md (installation, usage)
   - Architecture diagram
   - Guide déploiement
   - Troubleshooting

**Livrables Dev 1**:
- Suite tests complète Agent 1
- Documentation exhaustive

---

### 👨‍💻 Dev 2 : Notifications Email (après Agent 2)
**Fichiers**: `src/notifications/email_sender.py`, `templates/email/`

#### Tâches
1. [ ] **Configuration SMTP**
   - aiosmtplib pour envoi async
   - Lire table `alerts` (status="pending")
   - Envoi groupé par criticité
   - Tests serveur SMTP local

2. [ ] **Templates emails**
   - Email CRITIQUE (rouge) avec impacts financiers
   - Email ÉLEVÉ (orange) avec recommandations
   - Email résumé hebdomadaire
   - Tests rendu HTML

3. [ ] **Monitoring & Logs**
   - Dashboard simple (logs)
   - Métriques (nb alertes envoyées)
   - Health check SMTP

**Livrables Dev 2**:
- Système email fonctionnel pour alertes finales
- Templates professionnels
- Monitoring envoi emails

---

### 👨‍💻 Dev 3 : Déploiement
**Fichiers**: `docker-compose.yml`, `Dockerfile`, `.env.production`

#### Tâches
1. [ ] **Containerisation**
   - Dockerfile optimisé
   - Docker Compose (app + PostgreSQL optionnel)
   - Variables environnement production
   - Tests déploiement local

2. [ ] **Extension multi-sources**
   - Activer source EUDR
   - Tester généricité scraping
   - Ajuster si nécessaire
   - Documentation ajout sources

**Livrables Dev 3**:
- Déploiement Docker fonctionnel
- Guide extension sources

---

### 👨‍💻 Dev 4 (Khadidja) : API Agent 2
**Fichiers**: `src/api/agent2_endpoints.py`

#### Tâches
1. [ ] **Endpoints Agent 2**
   - POST /api/agent2/analyze : Lancer analyse impact
   - GET /api/impact-assessments/{id}
   - GET /api/impact-assessments?criticality=CRITICAL
   - GET /api/alerts (enrichies)

2. [ ] **Tests API Agent 2**
   - Tests endpoints
   - Tests format réponses
   - Tests gestion erreurs
   - Documentation OpenAPI

**Livrables Dev 4**:
- API Agent 2 REST complète
- Documentation Swagger

---

### 👨‍💻 Dev 5 (Willy) : Agent 2 Production
**Fichiers**: `src/agent_2/agent.py`, `src/agent_2/prompts/`

#### Tâches
1. [ ] **Agent 2 complet**
   - Intégrer 3 outils (scorer, impact_analyzer, action_recommender)
   - Prompt système Agent 2 optimisé
   - Lire analyses validation_status="approved"
   - Créer ImpactAssessment + Alert enrichie
   - Tests end-to-end

2. [ ] **Optimisation prompts**
   - Inclure profil entreprise + document + analyse
   - Format JSON structuré
   - Tests qualité réponses
   - Cache décisions similaires

**Livrables Dev 5**:
- Agent 2 production-ready
- ImpactAssessments + Alertes enrichies
- Pipeline complet : 1A → 1B → UI → Agent 2

---

### 👨‍💻 Dev 6 (Narjiss) : Frontend Agent 2
**Fichiers**: `frontend/src/pages/ImpactAssessments.vue`

#### Tâches
1. [ ] **Interface Impact Assessments**
   - Liste impact assessments par criticité
   - Vue détail (score, impacts, recommandations)
   - Filtres criticité/date/fournisseur
   - Export JSON/PDF rapports

2. [ ] **Tableau de bord alertes**
   - Liste alertes enrichies
   - Priorités visuelles (rouge/orange/jaune)
   - Actions (archiver, marquer lu)
   - Notifications temps réel

**Livrables Dev 6**:
- Frontend Agent 2 complet
- Tableaux de bord opérationnels

**🎯 JALON PHASE 4** :
- Pipeline complet 1A → 1B → UI → Agent 2 → Notifications
- Système production-ready
- Tests E2E validés

---

## 🚀 Phase 5: Production & Extension (Semaines 5-6)

### Tous ensemble : Validation Client & Extension

#### Tâches communes
1. [ ] **Tests charge et performance**
   - Chaque dev teste son module
   - Tests avec 50+ documents
   - Optimisation requêtes BDD
   - Optimisation prompts LLM

2. [ ] **Validation client**
   - Demo système complet
   - Feedback utilisateur
   - Ajustements UX/UI
   - Formation utilisateurs

3. [ ] **Extension multi-sources**
   - Dev 1 : Scraper EUDR
   - Dev 2 : Adapter extraction
   - Dev 3 : Configuration sources multiples
   - Dev 4-5-6 : Tests nouveaux documents

4. [ ] **Documentation finale**
   - Guide administrateur
   - Guide utilisateur final
   - Runbook opérations
   - Plan maintenance

**Livrables Phase 5**:
- Système déployé en production
- Validation client approuvée
- Extension EUDR opérationnelle
- Documentation complète

---

## 📊 Indicateurs de Succès

| Métrique | Cible |
|----------|-------|
| Documents scrapés CBAM | 30-50 |
| **Taux validation UI** | **> 80% approuvés** |
| Taux de faux positifs Agent 1B | < 30% (avant validation) |
| Taux de faux négatifs Agent 1B | < 5% |
| **Précision scoring Agent 2** | **± 15% estimation coûts** |
| Temps d'exécution hebdo | < 45 min (avec Agent 2) |
| Couverture tests | > 70% |
| Alertes enrichies (test) | 3-8 (après validation UI) |

---

## 👥 Répartition équipe complète (6 devs)

| Dev | Nom | Responsabilité principale | Phases principales |
|-----|-----|---------------------------|-------------------|
| **Dev 1** | Godson | Scraping + Agent 1B | Phase 2, 3 |
| **Dev 2** | - | Extraction PDF + Notifications | Phase 2, 3 |
| **Dev 3** | - | Storage + Orchestration + Pipeline | Phase 2, 3, 4 |
| **Dev 4** | Khadidja | API + Agent 2 Principal | Phase 2, 3, 4 |
| **Dev 5** | Willy | Agent 2 + Tools | Phase 2, 3, 4 |
| **Dev 6** | Narjiss | Frontend (UI Validation + Agent 2) | Phase 2, 3, 4 |

**Architecture**: Backend (5 devs) + Frontend (1 dev) - Repos séparés

---

## 🔄 Réunions d'équipe

- **Daily standup**: 15 min, 9h (optionnel)
- **Review hebdo**: Vendredi 16h (demo + retro)
- **Planning sprint**: Lundi 10h
- **Sync Dev 1/2/3** (Agent 1): Lundi 14h
- **Sync Dev 4/5** (Agent 2): Mardi 14h  
- **Sync Backend ↔ Frontend**: Mercredi 15h

---

## 📚 Ressources

- [LangChain Docs](https://python.langchain.com/)
- [Anthropic API](https://docs.anthropic.com/)
- [EUR-Lex](https://eur-lex.europa.eu/)
- [CBAM Source](https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism/cbam-legislation-and-guidance_en)

