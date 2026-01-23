# 🗺️ ROADMAP - Projet PING Agent 1

## 📋 Vue d'ensemble

**Objectif**: Développer un agent IA de veille réglementaire automatisée  
**Équipe**: 3 développeurs  
**Durée estimée**: 6-8 semaines  
**Phase pilote**: CBAM uniquement  
**Phase extension**: Multi-sources (EUDR, CSRD, Sanctions)

---

## 🎯 Phase 1: Setup & Infrastructure (Semaine 1)

### Tous ensemble
- [x] Structure du projet créée
- [ ] Installation de l'environnement (Poetry install)
- [ ] Configuration .env
- [ ] Base de données SQLite locale
- [ ] Logs structurés avec structlog
- [ ] Tests unitaires de base (pytest)

**Livrable**: Environnement de dev fonctionnel pour les 3 devs

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

---

### 👨‍💻 **Développeur 3 : Agent 1A & Orchestration**
**Responsabilité**: Coordination de l'Agent 1A avec LangChain

#### Tâches
1. [ ] **Agent 1A ReAct** (`src/agent_1a/agent.py`)
   - Créer agent LangChain avec ReAct
   - Intégrer les 4 tools (scraper, fetcher, extractor, detector)
   - Définir le prompt système
   - Gérer l'état de l'agent
   - Logger les décisions

2. [ ] **Stockage** (`src/storage/`)
   - Modèles SQLAlchemy (documents, execution_logs)
   - Repositories (DocumentRepository)
   - Migration Alembic
   - Tests CRUD

3. [ ] **Pipeline Agent 1A** (`src/orchestration/pipeline.py`)
   - Orchestrer l'exécution de bout en bout
   - Gérer les erreurs par étape
   - Rapport d'exécution
   - Tests end-to-end

**Livrables**:
- Agent 1A fonctionnel end-to-end
- Base de données avec schéma complet
- Exécution manuelle via `scripts/manual_run.py --agent 1a`

---

## 🧠 Phase 3: Agent 1B - Analyse (Semaines 4-5)

### 👨‍💻 **Développeur 1 : Filtrage Niveau 1 & 2**
**Responsabilité**: Filtres basiques (mots-clés, codes NC)

#### Tâches
1. [ ] **Filtre mots-clés** (`src/agent_1b/tools/keyword_filter.py`)
   - Charger keywords depuis profil entreprise
   - Recherche case-insensitive
   - Score = nb_matches / nb_keywords
   - Tests avec GMG et AeroRubber

2. [ ] **Filtre codes NC** (`src/agent_1b/tools/nc_code_filter.py`)
   - Charger NC codes depuis profil
   - Matching exact + partiel (4002 vs 4002.19)
   - Score basé sur criticité du code
   - Tests avec faux positifs/négatifs

3. [ ] **Profils entreprises** (charger depuis data/company_profiles/)
   - Parser JSON GMG + AeroRubber
   - Interface pour sélectionner profil actif
   - Tests de validation

**Livrables**:
- Filtres Niveau 1 & 2 fonctionnels
- Scores pour ~10 documents test
- Tests avec différents profils

---

### 👨‍💻 **Développeur 2 : Analyse Sémantique LLM**
**Responsabilité**: Filtrage intelligent avec Claude/GPT

#### Tâches
1. [ ] **Analyseur sémantique** (`src/agent_1b/tools/semantic_analyzer.py`)
   - Prompt template LangChain
   - Chunking pour longs documents
   - Appel Claude API (ou GPT-4)
   - Parser réponse en score 0-1
   - Cache des réponses (éviter double appels)
   - Tests avec mocks

2. [ ] **Prompts contextualisés**
   - Inclure profil entreprise dans prompt
   - Inclure type de réglementation
   - Exemples few-shot si nécessaire
   - Tests A/B sur qualité des réponses

3. [ ] **Gestion coûts API**
   - Logger nb tokens utilisés
   - Alerter si dépassement budget
   - Statistiques par analyse

**Livrables**:
- Analyse sémantique fonctionnelle
- Scores LLM pour documents test
- Documentation des prompts utilisés

---

### 👨‍💻 **Développeur 3 : Scoring & Alertes**
**Responsabilité**: Calcul final et génération alertes

#### Tâches
1. [ ] **Calculateur de score** (`src/agent_1b/tools/relevance_scorer.py`)
   - Agréger 3 scores (0.3 + 0.3 + 0.4)
   - Déterminer criticité (seuils)
   - Charger pondérations depuis config
   - Tests avec cas limites

2. [ ] **Générateur d'alertes** (`src/agent_1b/tools/alert_generator.py`)
   - Créer JSON structuré
   - Sauvegarder en base
   - Générer résumé lisible
   - Tests de sérialisation

3. [ ] **Agent 1B ReAct** (`src/agent_1b/agent.py`)
   - Créer agent LangChain
   - Intégrer les 5 tools
   - Prompt système pour analyse
   - Tests end-to-end

**Livrables**:
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
   - Couverture de code > 70%

2. [ ] **Documentation**
   - README.md (installation, usage)
   - Architecture diagram
   - Guide de déploiement
   - Troubleshooting

**Livrables**:
- Suite de tests complète
- Documentation utilisateur

---

## 🚀 Phase 5: Déploiement & Extension (Semaines 7-8)

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
| Taux de faux positifs | < 20% |
| Taux de faux négatifs | < 5% |
| Temps d'exécution hebdo | < 30 min |
| Couverture tests | > 70% |
| Alertes générées (test) | 5-10 |

---

## 🔄 Réunions d'équipe

- **Daily standup**: 15 min, 9h (optionnel)
- **Review hebdo**: Vendredi 16h (demo + retro)
- **Planning sprint**: Lundi 10h

---

## 📚 Ressources

- [LangChain Docs](https://python.langchain.com/)
- [Anthropic API](https://docs.anthropic.com/)
- [EUR-Lex](https://eur-lex.europa.eu/)
- [CBAM Source](https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism/cbam-legislation-and-guidance_en)
