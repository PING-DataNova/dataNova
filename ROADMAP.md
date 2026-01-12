# 🗺️ ROADMAP - Projet PING Backend (Agent 1 + Agent 2)

## 📋 Vue d'ensemble

**Objectif**: Développer un système multi-agents backend de veille réglementaire automatisée avec validation humaine  
**Équipe Backend**: 5 développeurs (3 sur Agent 1, 2 sur Agent 2)  
**Frontend**: Équipe séparée (dépôt à part)  
**Durée estimée**: 8-10 semaines  
**Phase pilote**: CBAM uniquement  
**Phase extension**: Multi-sources (EUDR, CSRD, Sanctions)

**Architecture Backend**: Agent 1A → Agent 1B → [UI Validation Frontend] → Agent 2 → Notifications

---

## 🎯 Phase 1: Setup & Infrastructure (Semaine 1)

### Tous ensemble (5 devs backend)
- [x] Structure du projet créée
- [x] Migration Poetry → uv (10-100x plus rapide)
- [ ] Installation de l'environnement (uv install)
- [ ] Configuration .env
- [x] Base de données SQLite locale (56KB, 6 tables)
- [ ] Logs structurés avec structlog
- [ ] Tests unitaires de base (pytest)

**Livrable**: Environnement de dev fonctionnel pour les 5 devs backend

**✅ Statut**: Partiellement complété (structure + BDD OK)

---

## 🤖 Phase 2: Agent 1A - Collecte (Semaines 2-3)

### 👨‍💻 **Développeur 1 : Scraping & Sources**
**Responsabilité**: Récupération des données depuis les sources web

#### Tâches
1. [ ] **Scraper CBAM** (`src/agent_1a/tools/scraper.py`)
   - Scraper la page CBAM avec httpx + BeautifulSoup
   - Extraire liens vers documents EUR-Lex
   - Extraire métadonnées (titre, date, type)
   - Gérer les erreurs réseau (retry, timeout)
   - Tests unitaires

2. [ ] **Téléchargeur EUR-Lex** (`src/agent_1a/tools/document_fetcher.py`)
   - Télécharger PDF depuis EUR-Lex
   - Gérer redirections et formats (PDF/HTML)
   - Calculer hash SHA-256
   - Sauvegarder dans data/documents/
   - Tests avec mock

3. [ ] **Configuration sources** (`config/sources.json`)
   - Charger config sources dynamiquement
   - Valider structure JSON
   - Prévoir extension (EUDR, CSRD)

**Livrables**:
- Scraper CBAM fonctionnel
- ~10-15 documents test téléchargés
- Tests couvrant les cas d'erreur

---

### 👨‍💻 **Développeur 2 : Extraction & Parsing**
**Responsabilité**: Extraction du contenu des documents

#### Tâches
1. [ ] **Extracteur PDF** (`src/agent_1a/tools/pdf_extractor.py`)
   - Extraire texte avec pdfplumber
   - Extraire tableaux (codes NC)
   - Identifier les annexes
   - Gérer les PDF scannés (OCR optionnel)
   - Tests sur 5+ documents réels

2. [ ] **Détecteur codes NC** (regex dans pdf_extractor.py)
   - Regex pour codes NC (4-10 chiffres)
   - Valider format (4002.19, 7606, etc.)
   - Extraire contexte autour du code
   - Tests avec cas limites

3. [ ] **Détecteur de changements** (`src/agent_1a/tools/change_detector.py`)
   - Comparer hash avec base de données
   - Identifier: nouveau / modifié / inchangé
   - Logger les changements
   - Tests avec fixtures

**Livrables**:
- Extraction texte + codes NC pour tous les documents test
- Base de données populée avec métadonnées
- Tests couvrant PDF complexes
### 👨‍💻 **Développeur 3 : Agent 1A & Orchestration + Storage**
**Responsabilité**: Coordination de l'Agent 1A avec LangChain + Architecture BDD

#### Tâches
1. [ ] **Agent 1A ReAct** (`src/agent_1a/agent.py`) ⏳ **EN ATTENTE Dev 1/2**
   - Créer agent LangChain avec ReAct
   - Intégrer les 4 tools (scraper, fetcher, extractor, detector)
   - Définir le prompt système
   - Gérer l'état de l'agent
   - Logger les décisions

2. [x] **Stockage complet** (`src/storage/`) ✅ **TERMINÉ**
   - [x] 6 Modèles SQLAlchemy (documents, analyses, impact_assessments, alerts, execution_logs, company_profiles)
   - [x] 5 Repositories avec workflow de validation
   - [x] Méthodes `find_by_url()`, `upsert_document()`, `update_workflow_status()`, `update_validation()`
   - [ ] Migration Alembic (déferré Phase 3+)
   - [x] Tests CRUD (base testée)

3. [ ] **Pipeline Agent 1A** (`src/orchestration/pipeline.py`)
   - Orchestrer l'exécution de bout en bout
   - Gérer les erreurs par étape
   - Rapport d'exécution
   - Tests end-to-end

**Livrables**:
- [x] Base de données avec schéma complet (6 tables, workflow validation)
- [ ] Agent 1A fonctionnel end-to-end
- [ ] Exécution manuelle via `scripts/manual_run.py --agent 1a`

**✅ Statut Phase 2**: Storage 100% terminé, Agent 1A en attente outils Dev 1/2
- Agent 1A fonctionnel end-to-end
- Base de données avec schéma complet
- Exécution manuelle via `scripts/manual_run.py --agent 1a`
## 🧠 Phase 3: Agent 1B - Analyse Pertinence (Semaines 4-5)

**⚠️ CHANGEMENT MAJEUR**: Simplification vers **analyse LLM unique** (plus de triple filtrage)

### 👨‍💻 **Développeur 1 ou 2 : Analyse LLM Unique**
**Responsabilité**: Analyse de pertinence complète via LLM

#### Tâches
1. [x] ~~Filtre mots-clés~~ ❌ **SUPPRIMÉ** (intégré dans LLM)
2. [x] ~~Filtre codes NC~~ ❌ **SUPPRIMÉ** (intégré dans LLM)
3. [x] ~~Scoring multi-niveaux~~ ❌ **SUPPRIMÉ** (déplacé vers Agent 2)

4. [ ] **Analyseur LLM unique** (`src/agent_1b/tools/semantic_analyzer.py`) 🆕
   - Prompt LLM incluant : recherche mots-clés + codes NC + analyse sémantique
   - Retour JSON : `{is_relevant: bool, confidence: float, matched_keywords: [], matched_nc_codes: [], reasoning: str}`
   - Charger profil entreprise dans prompt
   - Chunking pour longs documents
   - Cache des réponses
   - Tests avec mocks

5. [ ] **Agent 1B simplifié** (`src/agent_1b/agent.py`)
   - Un seul outil : `semantic_analyzer`
   - Créer Analysis avec `is_relevant`, `confidence`, `validation_status="pending"`
   - Mettre à jour `document.workflow_status = "analyzed"` ou `"rejected_analysis"`
   - Tests end-to-end

**Livrables**:
- Agent 1B simplifié fonctionnel (LLM unique)
- Analyses sauvegardées avec `validation_status="pending"`
- Pipeline Agent 1A → Agent 1B opérationnel

**✅ Statut**: Outils obsolètes supprimés, schéma BDD adapté
- Agent 1B fonctionnel
- Alertes JSON générées pour documents test
- Pipeline Agent 1A → 1B opérationnel

---

## 📧 Phase 4: Notifications & Scheduling (Semaine 6)

### 👨‍💻 **Développeur 1 : Notifications Email**

#### Tâches
1. [ ] **Envoi emails** (`src/notifications/email_sender.py`)
   - Configuration SMTP (aiosmtplib)
   - Template HTML d'alerte
   - Envoi groupé par criticité
   - Tests avec serveur SMTP local

2. [ ] **Templates**
   - Email CRITIQUE (rouge)
   - Email ÉLEVÉ (orange)
   - Email résumé hebdomadaire
   - Tests de rendu HTML

**Livrables**:
- Emails fonctionnels
- Template professionnel

---

### 👨‍💻 **Développeur 2 : Scheduler**

#### Tâches
1. [ ] **APScheduler** (`src/orchestration/scheduler.py`)
   - Configuration cron hebdomadaire
   - Gestion démarrage/arrêt
   - Retry en cas d'échec
   - Tests avec mock time

2. [ ] **Point d'entrée** (`src/main.py`)
   - Initialisation app
   - Démarrage scheduler
   - Signal handling (SIGTERM)
   - Logs lifecycle

**Livrables**:
- Scheduler fonctionnel
- Application déployable

---

### 👨‍💻 **Développeur 3 : Tests & Documentation**

#### Tâches
1. [ ] **Tests d'intégration**
   - Test pipeline complet
   - Test avec vraies données CBAM
   - Test envoi emails
## 💼 Phase 4: Agent 2 - Analyse d'Impact (Semaines 6-7)

**🆕 NOUVEAU**: Agent d'analyse d'impact et recommandations

**Note**: Agent 2 lit les analyses avec `validation_status="approved"` (validation faite via frontend séparé)

### 👨‍💻 **Développeur 4 : Agent 2 Principal**
**Responsabilité**: Architecture Agent 2 et orchestration

#### Tâches
1. [ ] **Agent 2 ReAct** (`src/agent_2/agent.py`)
   - Créer agent LangChain avec 3 outils
   - Prompt système Agent 2
   - Lire analyses avec `validation_status="approved"`
   - Créer ImpactAssessment + Alert
   - Tests end-to-end

2. [ ] **Prompts Agent 2** (`src/agent_2/prompts/agent_2_prompt.py`)
   - Prompt incluant profil entreprise + document + analyse
   - Format JSON structuré
   - Tests qualité réponses

3. [ ] **API Endpoints Agent 2** (FastAPI)
   - `POST /api/agent2/analyze` : Lancer analyse d'impact
   - `GET /api/impact-assessments/{id}` : Récupérer impact assessment
   - `GET /api/impact-assessments?criticality=CRITICAL` : Filtrer par criticité
   - Tests API

### 👨‍💻 **Développeur 5 : Outils Agent 2**
**Responsabilité**: Implémentation des outils d'analyse

#### Tâches
1. [ ] **Scoring et criticité** (`src/agent_2/tools/scorer.py`)
   - Calculer `total_score` (0-1) basé sur impacts
   - Déterminer `criticality` (CRITICAL/HIGH/MEDIUM/LOW)
   - Formule : `0.3*suppliers + 0.3*products + 0.2*financial + 0.2*urgency`
   - Tests avec cas réels

2. [ ] **Analyse d'impact** (`src/agent_2/tools/impact_analyzer.py`)
   - Croiser avec fournisseurs (data/suppliers/*.json)
   - Identifier produits impactés (codes NC)
   - Analyser flux douaniers (data/customs_flows/*.json)
   - Estimation financière
   - Tests avec données GMG

3. [ ] **Recommandations** (`src/agent_2/tools/action_recommender.py`)
   - Générer plan d'action (priorités, deadlines)
   - Stratégies d'atténuation des risques
   - Timeline de mise en conformité
   - Tests de génération

**Livrables**:
- Agent 2 fonctionnel
- ImpactAssessments créés pour analyses validées
- Alertes enrichies générées
- API REST Agent 2 documentée
- Pipeline complet : Agent 1A → 1B → [UI Frontend] → Agent 2

**📋 Référence**: Voir `/src/agent_2/README.md` pour détails

---

## 📧 Phase 5: Notifications & Scheduling (Semaine 8)

### 👨‍💻 **Développeur 1 : Notifications Email**

#### Tâches
1. [ ] **Envoi emails** (`src/notifications/email_sender.py`)
   - Configuration SMTP (aiosmtplib)
   - Template HTML d'alerte
   - Envoi groupé par criticité
   - Tests avec serveur SMTP local

2. [ ] **Templates**
   - Email CRITIQUE (rouge)
   - Email ÉLEVÉ (orange)
   - Email résumé hebdomadaire
   - Tests de rendu HTML

**Livrables**:
- Emails fonctionnels
- Template professionnel

---

### 👨‍💻 **Développeur 2 : Scheduler**

#### Tâches
1. [ ] **APScheduler** (`src/orchestration/scheduler.py`)
   - Configuration cron hebdomadaire
   - Gestion démarrage/arrêt
   - Retry en cas d'échec
   - Tests avec mock time

2. [ ] **Point d'entrée** (`src/main.py`)
   - Initialisation app
   - Démarrage scheduler
   - Signal handling (SIGTERM)
   - Logs lifecycle

**Livrables**:
- Scheduler fonctionnel
- Application déployable

---

### 👨‍💻 **Développeur 3 : Tests & Documentation**

#### Tâches
1. [ ] **Tests d'intégration**
   - Test pipeline complet
   - Test avec vraies données CBAM
   - Test envoi emails

2. [ ] **Documentation**
   - README.md (installation, usage)
   - Architecture diagram
   - Guide de déploiement
   - Troubleshooting

**Livrables**:
- Suite de tests complète
- Documentation utilisateur

---

## 🚀 Phase 6: Déploiement & Extension (Semaines 9-10)

### Tous ensemble

#### Tâches
1. [ ] **Déploiement**
   - Docker Compose
   - Variables d'environnement production
   - Configuration PostgreSQL (si nécessaire)
   - Tests déploiement

2. [ ] **Monitoring**
   - Dashboard simple (logs)
   - Alertes si échec
   - Métriques (nb docs, nb alertes)

3. [ ] **Extension multi-sources**
   - Activer source EUDR
   - Tester généricité
   - Ajuster si nécessaire

**Livrables**:
- Système déployé et fonctionnel
- Validation client
- Plan d'extension documenté

---

## 📊 Indicateurs de Succès

| Métrique | Cible |
|----------|-------|
| Documents scrapés CBAM | 30-50 |
| **Taux validation UI** | **> 80% approuvés** (frontend) |
| Taux de faux positifs Agent 1B | < 30% (avant validation) |
| Taux de faux négatifs Agent 1B | < 5% |
| **Précision scoring Agent 2** | **± 15% estimation coûts** |
| Temps d'exécution hebdo | < 45 min (avec Agent 2) |
| Couverture tests | > 70% |
| Alertes enrichies (test) | 3-8 (après validation UI) |

## 🔄 Réunions d'équipe backend

- **Daily standup**: 15 min, 9h (optionnel)
- **Review hebdo**: Vendredi 16h (demo + retro)
- **Planning sprint**: Lundi 10h
- **Sync Dev 3 ↔ Dev 1/2**: Lundi 14h (coordination Agent 1A)
- **Sync Dev 4 ↔ Dev 5**: Mardi 14h (coordination Agent 2)
- **Sync Backend ↔ Frontend**: Mercredi 15h (API validation + impact assessments)

## 👥 Répartition équipe backend (5 devs)

| Dev | Responsabilité principale | Phases |
|-----|---------------------------|--------|
| **Dev 1** | Scraping + Sources (Agent 1A) | Phase 2 |
| **Dev 2** | Extraction PDF + Parsing (Agent 1A) | Phase 2 |
| **Dev 3** | Storage + Orchestration + Agent 1A | Phase 2-3 |
| **Dev 4** | Agent 2 Principal + API | Phase 4 |
| **Dev 5** | Agent 2 Tools (scoring, impacts) | Phase 4 |

**Frontend** : Équipe séparée (dépôt à part) - UI validation des analyses

---

## 📚 Ressources

- [LangChain Docs](https://python.langchain.com/)
- [Anthropic API](https://docs.anthropic.com/)
- [EUR-Lex](https://eur-lex.europa.eu/)
- [CBAM Source](https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism/cbam-legislation-and-guidance_en)
