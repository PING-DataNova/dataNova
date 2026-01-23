# 🗄️ Documentation Base de Données - Projet PING

**Projet PING** - Base de données pour la veille réglementaire automatisée

**Dernière mise à jour** : 9 janvier 2026

---

## 🔄 Workflow complet

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AGENT 1A - Collecte                         │
│  Scraping EUR-Lex → Extraction PDF/HTML → Texte brut              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
                    Table: documents
                    workflow_status: "raw"
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AGENT 1B - Analyse LLM                           │
│  Pertinence ? (mots-clés + codes NC + sémantique)                  │
│  → OUI: workflow_status="analyzed" + Création analysis             │
│  → NON: workflow_status="rejected_analysis"                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │ Si pertinent
                             ▼
                    Table: analyses
                    is_relevant: true
                    validation_status: "pending"
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   UI - Validation Juridique                         │
│  Juriste valide ou rejette l'analyse                               │
│  → APPROUVÉ: workflow_status="validated"                           │
│  → REJETÉ: workflow_status="rejected_validation"                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │ Si validé
                             ▼
                    validation_status: "approved"
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│              AGENT 2 - Impact & Recommandations                     │
│  Scoring (0-1) + Criticité (CRITICAL/HIGH/MEDIUM/LOW)             │
│  Impact fournisseurs + Coûts + Plan d'action                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
                Table: impact_assessments
                Table: alerts
                             │
                             ▼
                    📧 Envoi email
```

---

## 📋 Responsabilités par agent

### Agent 1A - Collecte

**Mission** : Scraper les sites réglementaires et extraire le contenu

**Tables modifiées** :
- `documents` (écriture)
  - `workflow_status = "raw"`
  - `content` (texte extrait)
  - `nc_codes` (extraits par regex)

**Outils** :
- `scraper.py` : Scrape pages EUR-Lex
- `document_fetcher.py` : Télécharge PDFs
- `pdf_extractor.py` : Extrait texte
- `change_detector.py` : Détecte modifications

---

### Agent 1B - Analyse de pertinence

**Mission** : Analyser si le document est pertinent (LLM uniquement)

**Input** : Documents avec `workflow_status = "raw"`

**Tables modifiées** :
- `documents`
  - `workflow_status = "analyzed"` (si pertinent)
  - `workflow_status = "rejected_analysis"` (si non pertinent)
- `analyses` (écriture)
  - `is_relevant = true/false`
  - `confidence` (0-1)
  - `validation_status = "pending"`

**Outil** :
- `semantic_analyzer.py` : Analyse LLM complète (mots-clés + NC codes + sémantique)

**⚠️ Changement** : Un seul appel LLM au lieu de triple filtrage

---

### UI - Validation juridique

**Mission** : Validation humaine des documents pertinents

**Input** : Analyses avec `validation_status = "pending"`

**Tables modifiées** :
- `documents`
  - `workflow_status = "validated"` (approuvé)
  - `workflow_status = "rejected_validation"` (rejeté)
- `analyses`
  - `validation_status = "approved"/"rejected"`
  - `validation_comment`

---

### Agent 2 - Analyse d'impact

**Mission** : Analyse détaillée + scoring + recommandations

**Input** : Analyses avec `validation_status = "approved"`

**Tables modifiées** :
- `impact_assessments` (écriture)
  - `total_score` (0-1)
  - `criticality` (CRITICAL/HIGH/MEDIUM/LOW)
  - `affected_suppliers`, `affected_products`
  - `recommended_actions`
- `alerts` (écriture)

**Responsable** : Dev 4 (voir `/src/agent_2/README.md`)

---

## 🗄️ Schéma de base de données

### Statuts workflow

#### `documents.workflow_status`

| Statut | Description | Créé par |
|--------|-------------|----------|
| `raw` | Document brut collecté | Agent 1A |
| `analyzed` | Pertinent selon LLM | Agent 1B |
| `rejected_analysis` | Non pertinent (LLM) | Agent 1B |
| `validated` | Validé par juriste → Agent 2 | UI |
| `rejected_validation` | Rejeté par juriste | UI |

#### `analyses.validation_status`

| Statut | Description | Créé par |
|--------|-------------|----------|
| `pending` | Attend validation UI | Agent 1B |
| `approved` | Approuvé → Agent 2 traite | UI |
| `rejected` | Rejeté par juriste | UI |

---

## 📊 Architecture Relationnelle

```
┌─────────────────┐
│   documents     │  ← Agent 1A : collecte documents (workflow_status="raw")
└────────┬────────┘
         │ 1:N
         │
┌────────▼────────┐
│   analyses      │  ← Agent 1B : analyse LLM (validation_status="pending")
└────────┬────────┘
         │         ↑
         │         │ UI : validation juridique (approved/rejected)
         │         ↓
         │ 1:1
┌────────▼─────────────┐
│ impact_assessments   │  ← Agent 2 : scoring + criticité + recommandations
└────────┬─────────────┘
         │ 1:N
         │
┌────────▼────────┐
│    alerts       │  ← Notifications enrichies
└─────────────────┘

┌─────────────────┐    ┌──────────────────┐
│ execution_logs  │    │ company_profiles │  ← Tables indépendantes
└─────────────────┘    └──────────────────┘
```

---

## 📋 Tables Détaillées

### 1️⃣ **documents**

Stocke les documents réglementaires collectés par l'Agent 1A.

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id`    | UUID | PRIMARY KEY | Identifiant unique |
| `title` | VARCHAR(500) | NOT NULL | Titre du document |
| `source_url` | VARCHAR(1000) | NOT NULL | URL d'origine (EUR-Lex, etc.) |
| `regulation_type` | VARCHAR(50) | NOT NULL | Type: CBAM, EUDR, CSRD, etc. |
| `publication_date` | DATETIME | NULL | Date de publication officielle |
| `hash_sha256` | VARCHAR(64) | UNIQUE, NOT NULL | Hash SHA-256 du contenu (détection changements) |
| `content` | TEXT | NULL | Texte extrait du PDF |
| `nc_codes` | JSON | NULL | Liste des codes NC trouvés `["4002.19", "7606"]` |
| `document_metadata` | JSON | NULL | Métadonnées diverses (auteur, type doc, annexes) |
| `status` | VARCHAR(20) | NOT NULL | Statut: `new`, `modified`, `unchanged` |
| **`workflow_status`** | **VARCHAR(20)** | **NOT NULL, DEFAULT='raw'** | **Workflow: `raw`, `analyzed`, `rejected_analysis`, `validated`, `rejected_validation`** |
| **`analyzed_at`** | **DATETIME** | **NULL** | **Date d'analyse par Agent 1B** |
| **`validated_at`** | **DATETIME** | **NULL** | **Date de validation UI** |
| **`validated_by`** | **VARCHAR(200)** | **NULL** | **Email du validateur (juriste)** |
| `first_seen` | DATETIME | NOT NULL | Date de première détection |
| `last_checked` | DATETIME | NOT NULL | Date de dernière vérification |
| `created_at` | DATETIME | NOT NULL | Date de création en base |

**Index** :
- `idx_documents_hash` sur `hash_sha256` (recherche rapide par hash)
- `idx_documents_status` sur `status` (filtrer nouveaux documents)
- `idx_documents_regulation` sur `regulation_type` (filtrer par type)
- **`idx_documents_workflow` sur `workflow_status` (filtrer par étape du workflow)**

**Statuts workflow** :
- `raw` : Document collecté, pas encore analysé
- `analyzed` : Analysé par Agent 1B, pertinent
- `rejected_analysis` : Analysé par Agent 1B, non pertinent
- `validated` : Validé par juriste (UI) → envoyé à Agent 2
- `rejected_validation` : Rejeté par juriste (UI)

**Exemple** :
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Commission Implementing Regulation (EU) 2023/956",
  "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R0956",
  "regulation_type": "CBAM",
### 2️⃣ **analyses**

Résultats d'analyse de pertinence par l'Agent 1B (analyse LLM unique).

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Identifiant unique |
| `document_id` | UUID | FOREIGN KEY → documents.id | Document analysé |
| **`is_relevant`** | **BOOLEAN** | **NOT NULL** | **Document pertinent ? (True/False)** |
| **`confidence`** | **FLOAT** | **NOT NULL** | **Confiance LLM (0.0 à 1.0)** |
| `matched_keywords` | JSON | NULL | Mots-clés trouvés par LLM `["carbon", "steel"]` |
| `matched_nc_codes` | JSON | NULL | Codes NC identifiés `["4002.19"]` |
| `llm_reasoning` | TEXT | NULL | Explication complète du LLM |
| **`validation_status`** | **VARCHAR(20)** | **NOT NULL, DEFAULT='pending'** | **`pending`, `approved`, `rejected`** |
| **`validation_comment`** | **TEXT** | **NULL** | **Commentaire du juriste** |
| **`validated_by`** | **VARCHAR(200)** | **NULL** | **Email du validateur** |
| **`validated_at`** | **DATETIME** | **NULL** | **Date de validation UI** |
| `created_at` | DATETIME | NOT NULL | Date de l'analyse |

**Index** :
- `idx_analyses_document` sur `document_id` (jointure avec documents)
- **`idx_analyses_validation` sur `validation_status` (filtrer analyses en attente)**
- **`idx_analyses_relevant` sur `is_relevant` (documents pertinents)**

**Statuts validation** :
- `pending` : En attente de validation juridique (UI)
- `approved` : Validé par juriste → envoyé à Agent 2
- `rejected` : Rejeté par juriste

**⚠️ Changement majeur** : Le scoring (`total_score`) et la criticité (`criticality`) ont été **déplacés** vers la table `impact_assessments` (Agent 2).OT NULL | Niveau 3 : score sémantique LLM (0.0 à 1.0) |
| `llm_reasoning` | TEXT | NULL | Explication du LLM (pourquoi pertinent/non pertinent) |
| `total_score` | FLOAT | NOT NULL | Score final pondéré (0.0 à 1.0) |
| `criticality` | VARCHAR(20) | NOT NULL | Criticité: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `relevant` | BOOLEAN | NOT NULL | Document pertinent pour l'entreprise ? |
| `created_at` | DATETIME | NOT NULL | Date de l'analyse |

**Index** :
- `idx_analyses_document` sur `document_id` (jointure avec documents)
- `idx_analyses_relevant` sur `relevant` (filtrer documents pertinents)
- `idx_analyses_criticality` sur `criticality` (trier par criticité)

**Formule score total** :
```
total_score = (keyword_score * 0.3) + (nc_code_score * 0.3) + (llm_score * 0.4)
```

**Mapping criticité** :
- `total_score >= 0.8` → CRITICAL
- `total_score >= 0.6` → HIGH
- `total_score >= 0.4` → MEDIUM
- `total_score < 0.4` → LOW

**Exemple** :
```json
{
  "id": "660f9511-f3ac-52e5-b827-557766551111",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "keyword_match": true,
  "keyword_score": 0.85,
  "matched_keywords": ["carbon", "steel", "imports"],
  "nc_code_match": true,
  "nc_code_score": 1.0,
  "matched_nc_codes": ["7206"],
  "llm_score": 0.92,
**Exemple** :
```json
{
  "id": "660f9511-f3ac-52e5-b827-557766551111",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_relevant": true,
  "confidence": 0.92,
  "matched_keywords": ["carbon", "steel", "imports"],
  "matched_nc_codes": ["7206"],
  "llm_reasoning": "Ce règlement CBAM affecte directement les importations d'acier (code NC 7206) avec un système de taxation carbone...",
  "validation_status": "approved",
  "validation_comment": "Impact confirmé sur nos fournisseurs chinois",
  "validated_by": "juriste@example.com",
  "validated_at": "2026-01-06T14:20:00Z"
}
```

---

### 3️⃣ **impact_assessments**

**🆕 NOUVEAU** - Analyses d'impact détaillées par Agent 2 (après validation UI).

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Identifiant unique |
| `analysis_id` | UUID | FOREIGN KEY → analyses.id | Analyse validée source |
| **`total_score`** | **FLOAT** | **NOT NULL** | **Score d'impact (0.0 à 1.0)** |
| **`criticality`** | **VARCHAR(20)** | **NOT NULL** | **`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`** |
| `affected_suppliers` | JSON | NULL | Fournisseurs impactés `[{id, name, impact_level}]` |
| `affected_products` | JSON | NULL | Produits impactés `[{id, name, nc_code}]` |
| `affected_customs_flows` | JSON | NULL | Flux douaniers `[{origin, destination, volume}]` |
| `financial_impact` | JSON | NULL | Estimation financière `{cost, currency, timeframe}` |
| `recommended_actions` | JSON | NOT NULL | Plan d'action `[{priority, action, deadline}]` |
| `risk_mitigation` | JSON | NULL | Stratégies d'atténuation `[{risk, strategy}]` |
| `llm_reasoning` | TEXT | NULL | Explication détaillée Agent 2 |
| `confidence_level` | VARCHAR(20) | NULL | `HIGH`, `MEDIUM`, `LOW` |
| `created_at` | DATETIME | NOT NULL | Date de création |

**Index** :
- `idx_impact_analysis` sur `analysis_id` (jointure avec analyses)
- `idx_impact_criticality` sur `criticality` (trier par criticité)
- `idx_impact_score` sur `total_score` (trier par score)

**Formule score** (Agent 2) :
```
total_score = (
    0.3 * supplier_impact_ratio +
    0.3 * product_impact_ratio +
    0.2 * financial_impact_normalized +
    0.2 * urgency_score
)
```

**Mapping criticité** :
- `total_score >= 0.8` → CRITICAL
- `total_score >= 0.6` → HIGH
- `total_score >= 0.4` → MEDIUM
- `total_score < 0.4` → LOW

**Exemple** :
```json
{
  "id": "770a1122-g4bd-63f6-c938-668877662222",
  "analysis_id": "660f9511-f3ac-52e5-b827-557766551111",
  "total_score": 0.85,
  "criticality": "CRITICAL",
  "affected_suppliers": [
    {"id": "sup_1", "name": "Shanghai Steel Co", "impact_level": "HIGH"}
  ],
  "affected_products": [
    {"id": "prod_123", "name": "Steel Rods", "nc_code": "7206"}
  ],
  "financial_impact": {
    "estimated_cost": 150000,
    "currency": "EUR",
    "timeframe": "12 months"
  },
  "recommended_actions": [
    {
      "priority": 1,
      "action": "Contact suppliers for CBAM emissions data",
      "deadline": "2026-02-01"
    }
  ]
}
```

---

### 4️⃣ **alerts**

Alertes enrichies générées par Agent 2 et statut d'envoi.

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Identifiant unique |
| **`impact_assessment_id`** | **UUID** | **FOREIGN KEY → impact_assessments.id** | **Impact assessment source** |
| `alert_type` | VARCHAR(50) | NOT NULL | Type: `email`, `webhook`, `slack` |
| `alert_data` | JSON | NOT NULL | Contenu structuré de l'alerte |
| `recipients` | JSON | NOT NULL | Liste des destinataires `["user@example.com"]` |
| `sent_at` | DATETIME | NULL | Date d'envoi (NULL si pas encore envoyé) |
| `status` | VARCHAR(20) | NOT NULL | Statut: `pending`, `sent`, `failed` |
| `error_message` | TEXT | NULL | Message d'erreur si échec d'envoi |
| `created_at` | DATETIME | NOT NULL | Date de création de l'alerte |

**Index** :
- **`idx_alerts_impact` sur `impact_assessment_id` (jointure avec impact_assessments)**
- `idx_alerts_status` sur `status` (filtrer alertes en attente)

**Structure `alert_data`** :
```json
{
  "document_title": "Regulation 2023/956",
  "regulation_type": "CBAM",
  "criticality": "CRITICAL",
  "total_score": 0.85,
  "summary": "5 fournisseurs chinois impactés par CBAM - 150K€ estimés",
  "affected_suppliers": 5,
  "affected_products": 12,
  "financial_impact": "150,000 EUR",
  "recommended_actions": [
    "Contacter fournisseurs pour données émissions",
    "Prévoir budget taxe carbone"
  ],
  "document_url": "https://..."
}
```

---

### 5️⃣ **execution_logs**

Logs d'exécution des agents (monitoring et debugging).

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Identifiant unique |
| `agent_type` | VARCHAR(20) | NOT NULL | Type d'agent: `agent_1a`, `agent_1b`, **`agent_2`** |
| `status` | VARCHAR(20) | NOT NULL | Statut: `success`, `error`, `running` |
| `start_time` | DATETIME | NOT NULL | Début de l'exécution |
| `end_time` | DATETIME | NULL | Fin de l'exécution (NULL si en cours) |
| `duration_seconds` | FLOAT | NULL | Durée totale (calculé) |
| `documents_processed` | INTEGER | DEFAULT 0 | Nombre de documents traités |
| `documents_new` | INTEGER | DEFAULT 0 | Nouveaux documents détectés |
| `documents_modified` | INTEGER | DEFAULT 0 | Documents modifiés détectés |
| `errors` | JSON | NULL | Liste des erreurs rencontrées |
| `metadata` | JSON | NULL | Métadonnées diverses (versions, config, etc.) |
| `created_at` | DATETIME | NOT NULL | Date de création du log |

**Index** :
- `idx_logs_agent` sur `agent_type` (filtrer par agent)
- `idx_logs_status` sur `status` (filtrer erreurs)
- `idx_logs_start_time` sur `start_time` (trier chronologiquement)

**Exemple** :
```json
{
  "id": "770g0622-g4bd-63f6-c938-668877662222",
  "agent_type": "agent_1a",
  "status": "success",
  "start_time": "2026-01-08T10:00:00Z",
  "end_time": "2026-01-08T10:05:23Z",
  "duration_seconds": 323.45,
  "documents_processed": 15,
  "documents_new": 2,
  "documents_modified": 1,
  "errors": [],
  "metadata": {
    "langchain_version": "0.3.0",
    "source": "CBAM"
  }
}
```

---

### 5️⃣ **company_profiles**

Profils entreprise pour le filtrage personnalisé (Agent 1B).

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Identifiant unique |
| `company_name` | VARCHAR(200) | NOT NULL | Nom de l'entreprise |
| `nc_codes` | JSON | NOT NULL | Codes NC pertinents `["4002.19", "7206"]` |
| `keywords` | JSON | NOT NULL | Mots-clés à surveiller `["rubber", "steel"]` |
| `regulations` | JSON | NOT NULL | Réglementations à surveiller `["CBAM", "EUDR"]` |
| `contact_emails` | JSON | NOT NULL | Emails pour alertes `["compliance@company.com"]` |
| `config` | JSON | NULL | Configuration personnalisée (seuils, fréquence) |
| `active` | BOOLEAN | DEFAULT TRUE | Profil actif ou non |
| `created_at` | DATETIME | NOT NULL | Date de création |
| `updated_at` | DATETIME | NOT NULL | Dernière mise à jour |

**Index** :
- `idx_profiles_active` sur `active` (filtrer profils actifs)

**Exemple (AeroRubber Industries)** :
```json
{
  "id": "880h1733-h5ce-74g7-d049-779988773333",
  "company_name": "AeroRubber Industries",
  "nc_codes": ["4002.19", "4002.11"],
  "keywords": ["rubber", "synthetic", "CBAM", "carbon"],
  "regulations": ["CBAM"],
  "contact_emails": ["compliance@aerorubber.com"],
  "config": {
    "min_score_threshold": 0.6,
    "alert_frequency": "immediate"
  },
  "active": true
}
```

---

## 🔗 Relations

```sql
-- documents → analyses (1:N)
ALTER TABLE analyses 
ADD CONSTRAINT fk_analyses_document 
FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE;

-- analyses → impact_assessments (1:1)
ALTER TABLE impact_assessments
ADD CONSTRAINT fk_impact_analysis 
FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE;

-- impact_assessments → alerts (1:N)
ALTER TABLE alerts 
ADD CONSTRAINT fk_alerts_impact 
FOREIGN KEY (impact_assessment_id) REFERENCES impact_assessments(id) ON DELETE CASCADE;
```

---

## 🔄 Workflow complet

```
1. Agent 1A collecte documents
   → INSERT documents (workflow_status="raw")

2. Agent 1B analyse pertinence (LLM unique)
   → Si pertinent:
     - INSERT analyses (is_relevant=true, validation_status="pending")
     - UPDATE documents SET workflow_status="analyzed"
   → Si non pertinent:
     - UPDATE documents SET workflow_status="rejected_analysis"

3. UI - Validation juridique
   → Juriste valide:
     - UPDATE analyses SET validation_status="approved"
     - UPDATE documents SET workflow_status="validated"
   → Juriste rejette:
     - UPDATE analyses SET validation_status="rejected"
     - UPDATE documents SET workflow_status="rejected_validation"

4. Agent 2 analyse impact (analyses avec validation_status="approved")
   → INSERT impact_assessments (total_score, criticality)
   → INSERT alerts (impact_assessment_id, status="pending")

5. Envoi notifications
   → UPDATE alerts SET status="sent", sent_at=NOW()
```
---

## 🛠️ Migrations Alembic

Les migrations seront gérées avec **Alembic** :

```bash
# Créer une migration
alembic revision -m "Initial schema"

# Appliquer les migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 🧪 Données de test

Fichiers JSON de test disponibles dans [`data/`](../data/) :
- `company_profiles/gmg_globex_manufacturing.json`
- `company_profiles/aerorubber_industries.json`
- `suppliers/gmg_suppliers.json`
- `customs_flows/gmg_customs_flows.json`

Ces données seront importées via script d'initialisation pour tester le système.

---

## 📝 Notes techniques

### Choix SQLite vs PostgreSQL

**SQLite** (développement) :
- ✅ Simple, pas de serveur
- ✅ Fichier unique portable
- ❌ Pas de concurrence avancée

**PostgreSQL** (production) :
- ✅ JSONB performant
- ✅ Full-text search
- ✅ Concurrence multi-utilisateurs
- ✅ Robustesse entreprise

Le code SQLAlchemy est compatible avec les deux.

### Types JSON

SQLAlchemy gère automatiquement :
- **SQLite** : TEXT (sérialisation JSON)
- **PostgreSQL** : JSONB (type natif optimisé)

---

## 🔄 Changelog

| Version | Date | Changements |
|---------|------|-------------|
| 0.1.0 | 2026-01-08 | Schéma initial (5 tables) |
| **0.2.0** | **2026-01-09** | **Ajout workflow validation, table impact_assessments, simplification analyses (LLM unique)** |

---

**Auteur** : Équipe Dev (Dev 1, 2, 3)  
**Projet** : PING DataNova - Backend multi-agents
