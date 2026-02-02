# Schéma de Base de Données PING - Complet

## Vue d'Ensemble

Le schéma de base de données PING est organisé en 6 modules principaux :

1. **Documents & Collecte** - Données brutes collectées
2. **Données Métier** - Sites et fournisseurs Hutchinson
3. **Pipeline d'Analyse** - Résultats des agents LLM
4. **Alertes & Notifications** - Système d'alertes
5. **Ground Truth** - Données de référence pour amélioration
6. **Utilisateurs & Configuration** - Gestion des utilisateurs

---

## 1. Documents & Collecte (Agent 1A)

### Table: `documents`

Stocke tous les documents collectés (réglementaires, climatiques, géopolitiques).

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | Identifiant unique |
| `title` | String(500) | Titre du document |
| `source_url` | String(1000) | URL d'origine |
| `event_type` | String(50) | Type: reglementaire, climatique, geopolitique |
| `event_subtype` | String(100) | Sous-type (ex: CBAM, inondation, conflit) |
| `publication_date` | DateTime | Date de publication officielle |
| `collection_date` | DateTime | Date de collecte |
| `hash_sha256` | String(64) | Hash du contenu (détection changements) |
| `content` | Text | Texte extrait |
| `summary` | Text | Résumé automatique |
| `geographic_scope` | JSON | Portée géographique {countries: [], regions: [], coordinates: {}} |
| `metadata` | JSON | Métadonnées diverses |
| `status` | String(20) | new, modified, unchanged |
| `first_seen` | DateTime | Date de première détection |
| `last_checked` | DateTime | Date de dernière vérification |
| `created_at` | DateTime | Date de création |
| `updated_at` | DateTime | Date de mise à jour |

**Index:**
- `hash_sha256` (unique)
- `event_type`
- `publication_date`
- `status`

---

## 2. Données Métier Hutchinson

### Table: `hutchinson_sites`

Stocke les sites de production Hutchinson (80-90 sites).

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | Identifiant unique |
| `name` | String(200) | Nom du site |
| `code` | String(50) | Code interne Hutchinson |
| `country` | String(100) | Pays |
| `region` | String(100) | Région/État |
| `city` | String(100) | Ville |
| `address` | Text | Adresse complète |
| `latitude` | Float | Latitude |
| `longitude` | Float | Longitude |
| `sectors` | JSON | Liste des secteurs d'activité |
| `products` | JSON | Liste des produits fabriqués |
| `raw_materials` | JSON | Liste des matières premières utilisées |
| `certifications` | JSON | Certifications (ISO, etc.) |
| `employee_count` | Integer | Nombre d'employés |
| `annual_production_value` | Float | Valeur de production annuelle (€) |
| `strategic_importance` | String(20) | faible, moyen, fort, critique |
| `metadata` | JSON | Métadonnées diverses |
| `active` | Boolean | Site actif ou non |
| `created_at` | DateTime | Date de création |
| `updated_at` | DateTime | Date de mise à jour |

**Index:**
- `code` (unique)
- `country`
- `latitude, longitude` (spatial index)
- `active`

### Table: `suppliers`

Stocke les fournisseurs d'Hutchinson.

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | Identifiant unique |
| `name` | String(200) | Nom du fournisseur |
| `code` | String(50) | Code interne |
| `country` | String(100) | Pays |
| `region` | String(100) | Région/État |
| `city` | String(100) | Ville |
| `address` | Text | Adresse complète |
| `latitude` | Float | Latitude |
| `longitude` | Float | Longitude |
| `sector` | String(100) | Secteur d'activité |
| `products_supplied` | JSON | Produits fournis |
| `company_size` | String(20) | PME, ETI, Grand groupe |
| `certifications` | JSON | Certifications |
| `financial_health` | String(20) | excellent, bon, moyen, faible |
| `metadata` | JSON | Métadonnées diverses |
| `active` | Boolean | Fournisseur actif ou non |
| `created_at` | DateTime | Date de création |
| `updated_at` | DateTime | Date de mise à jour |

**Index:**
- `code` (unique)
- `country`
- `latitude, longitude` (spatial index)
- `active`

### Table: `supplier_relationships`

Stocke les relations entre sites Hutchinson et fournisseurs.

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | Identifiant unique |
| `hutchinson_site_id` | UUID | FK vers hutchinson_sites |
| `supplier_id` | UUID | FK vers suppliers |
| `products_supplied` | JSON | Produits fournis à ce site |
| `annual_volume` | Float | Volume annuel (€) |
| `criticality` | String(20) | Critique, Important, Standard |
| `is_sole_supplier` | Boolean | Fournisseur unique pour ce produit |
| `has_backup_supplier` | Boolean | Existe-t-il un fournisseur de secours |
| `backup_supplier_id` | UUID | FK vers suppliers (nullable) |
| `lead_time_days` | Integer | Délai de livraison (jours) |
| `contract_end_date` | Date | Date de fin de contrat |
| `risk_mitigation_plan` | Text | Plan de mitigation des risques |
| `metadata` | JSON | Métadonnées diverses |
| `active` | Boolean | Relation active ou non |
| `created_at` | DateTime | Date de création |
| `updated_at` | DateTime | Date de mise à jour |

**Index:**
- `hutchinson_site_id`
- `supplier_id`
- `criticality`
- `is_sole_supplier`

---

## 3. Pipeline d'Analyse

### Table: `pertinence_checks`

Stocke les résultats de l'Agent 1B (Pertinence Checker).

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | Identifiant unique |
| `document_id` | UUID | FK vers documents |
| `decision` | String(20) | OUI, NON, PARTIELLEMENT |
| `confidence` | Float | Confiance (0-1) |
| `reasoning` | Text | Raisonnement du LLM |
| `matched_elements` | JSON | Éléments pertinents identifiés |
| `llm_model` | String(50) | Modèle LLM utilisé |
| `llm_tokens` | Integer | Nombre de tokens utilisés |
| `processing_time_ms` | Integer | Temps de traitement (ms) |
| `analysis_metadata` | JSON | Métadonnées de l'analyse |
| `created_at` | DateTime | Date de création |

**Index:**
- `document_id` (unique)
- `decision`
- `created_at`

### Table: `risk_analyses`

Stocke les résultats de l'Agent 2 (Risk Analyzer).

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | Identifiant unique |
| `document_id` | UUID | FK vers documents |
| `pertinence_check_id` | UUID | FK vers pertinence_checks |
| `impacts_description` | Text | Description des impacts |
| `affected_sites` | JSON | Liste des sites impactés avec détails |
| `affected_suppliers` | JSON | Liste des fournisseurs impactés avec détails |
| `geographic_analysis` | JSON | Analyse géographique détaillée |
| `criticality_analysis` | JSON | Analyse de criticité (sole supplier, backup, etc.) |
| `risk_level` | String(20) | Faible, Moyen, Fort, Critique |
| `risk_score` | Float | Score de risque (0-10) |
| `supply_chain_impact` | String(20) | aucun, faible, moyen, fort, critique |
| `recommendations` | Text | Recommandations d'action |
| `reasoning` | Text | Raisonnement du LLM |
| `llm_model` | String(50) | Modèle LLM utilisé |
| `llm_tokens` | Integer | Nombre de tokens utilisés |
| `processing_time_ms` | Integer | Temps de traitement (ms) |
| `analysis_metadata` | JSON | Métadonnées de l'analyse |
| `created_at` | DateTime | Date de création |

**Index:**
- `document_id` (unique)
- `pertinence_check_id`
- `risk_level`
- `created_at`

### Table: `judge_evaluations`

Stocke les résultats du LLM Judge.

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | Identifiant unique |
| `risk_analysis_id` | UUID | FK vers risk_analyses |
| `score_completeness` | Float | Score complétude (0-10) |
| `score_accuracy` | Float | Score précision (0-10) |
| `score_relevance` | Float | Score pertinence (0-10) |
| `score_clarity` | Float | Score clarté (0-10) |
| `score_actionability` | Float | Score actionnabilité (0-10) |
| `score_traceability` | Float | Score traçabilité (0-10) |
| `overall_score` | Float | Score global (0-10) |
| `action` | String(20) | APPROVE, REVIEW, REJECT |
| `reasoning` | Text | Raisonnement du Judge |
| `improvement_suggestions` | JSON | Suggestions d'amélioration |
| `llm_model` | String(50) | Modèle LLM utilisé |
| `llm_tokens` | Integer | Nombre de tokens utilisés |
| `processing_time_ms` | Integer | Temps de traitement (ms) |
| `created_at` | DateTime | Date de création |

**Index:**
- `risk_analysis_id` (unique)
- `action`
- `overall_score`
- `created_at`

---

## 4. Alertes & Notifications

### Table: `alerts`

Stocke les alertes générées par le système.

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | Identifiant unique |
| `document_id` | UUID | FK vers documents |
| `risk_analysis_id` | UUID | FK vers risk_analyses |
| `judge_evaluation_id` | UUID | FK vers judge_evaluations (nullable) |
| `title` | String(500) | Titre de l'alerte |
| `description` | Text | Description |
| `severity` | String(20) | info, low, medium, high, critical |
| `affected_sites` | JSON | Sites impactés |
| `affected_suppliers` | JSON | Fournisseurs impactés |
| `recommendations` | Text | Recommandations |
| `status` | String(20) | new, acknowledged, in_progress, resolved, dismissed |
| `assigned_to` | UUID | FK vers users (nullable) |
| `acknowledged_at` | DateTime | Date de prise en compte |
| `resolved_at` | DateTime | Date de résolution |
| `resolution_notes` | Text | Notes de résolution |
| `created_at` | DateTime | Date de création |
| `updated_at` | DateTime | Date de mise à jour |

**Index:**
- `document_id`
- `risk_analysis_id`
- `severity`
- `status`
- `created_at`

### Table: `notifications`

Stocke les notifications envoyées aux utilisateurs.

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | Identifiant unique |
| `alert_id` | UUID | FK vers alerts |
| `user_id` | UUID | FK vers users |
| `channel` | String(20) | email, sms, push, in_app |
| `status` | String(20) | pending, sent, delivered, failed |
| `sent_at` | DateTime | Date d'envoi |
| `delivered_at` | DateTime | Date de livraison |
| `read_at` | DateTime | Date de lecture |
| `error_message` | Text | Message d'erreur (si échec) |
| `created_at` | DateTime | Date de création |

**Index:**
- `alert_id`
- `user_id`
- `status`
- `created_at`

---

## 5. Ground Truth (Amélioration Continue)

### Table: `ground_truth_cases`

Stocke les cas de référence validés par des experts.

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | Identifiant unique |
| `document_id` | UUID | FK vers documents |
| `expert_pertinence_decision` | String(20) | OUI, NON, PARTIELLEMENT |
| `expert_pertinence_reasoning` | Text | Raisonnement expert |
| `expert_risk_level` | String(20) | Faible, Moyen, Fort, Critique |
| `expert_affected_sites` | JSON | Sites impactés selon expert |
| `expert_affected_suppliers` | JSON | Fournisseurs impactés selon expert |
| `expert_recommendations` | Text | Recommandations expert |
| `expert_name` | String(200) | Nom de l'expert |
| `validated_at` | DateTime | Date de validation |
| `metadata` | JSON | Métadonnées diverses |
| `created_at` | DateTime | Date de création |

**Index:**
- `document_id` (unique)
- `validated_at`

### Table: `ground_truth_results`

Compare les résultats LLM avec les résultats experts.

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | Identifiant unique |
| `ground_truth_case_id` | UUID | FK vers ground_truth_cases |
| `pertinence_check_id` | UUID | FK vers pertinence_checks |
| `risk_analysis_id` | UUID | FK vers risk_analyses |
| `pertinence_match` | Boolean | Décision pertinence correspond |
| `risk_level_match` | Boolean | Niveau de risque correspond |
| `sites_match_score` | Float | Score de correspondance sites (0-1) |
| `suppliers_match_score` | Float | Score de correspondance fournisseurs (0-1) |
| `overall_match_score` | Float | Score global de correspondance (0-1) |
| `discrepancies` | JSON | Écarts détaillés |
| `created_at` | DateTime | Date de création |

**Index:**
- `ground_truth_case_id`
- `overall_match_score`
- `created_at`

---

## 6. Utilisateurs & Configuration

### Table: `users`

Stocke les utilisateurs du système.

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | Identifiant unique |
| `email` | String(255) | Email (unique) |
| `password_hash` | String(255) | Hash du mot de passe |
| `first_name` | String(100) | Prénom |
| `last_name` | String(100) | Nom |
| `role` | String(50) | admin, analyst, viewer |
| `department` | String(100) | Département |
| `notification_preferences` | JSON | Préférences de notification |
| `active` | Boolean | Compte actif ou non |
| `last_login` | DateTime | Dernière connexion |
| `created_at` | DateTime | Date de création |
| `updated_at` | DateTime | Date de mise à jour |

**Index:**
- `email` (unique)
- `role`
- `active`

### Table: `company_profile`

Stocke la configuration globale d'Hutchinson.

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | Identifiant unique |
| `company_name` | String(200) | Nom de l'entreprise |
| `headquarters_country` | String(100) | Pays du siège |
| `total_sites` | Integer | Nombre total de sites |
| `total_suppliers` | Integer | Nombre total de fournisseurs |
| `risk_tolerance` | String(20) | low, medium, high |
| `notification_settings` | JSON | Paramètres de notification |
| `data_sources_config` | JSON | Configuration des sources de données |
| `llm_config` | JSON | Configuration des LLM |
| `created_at` | DateTime | Date de création |
| `updated_at` | DateTime | Date de mise à jour |

---

## Relations Clés

```
documents 1 ──── 1 pertinence_checks
documents 1 ──── 1 risk_analyses
documents 1 ──── 0..1 ground_truth_cases

pertinence_checks 1 ──── 1 risk_analyses
risk_analyses 1 ──── 1 judge_evaluations
risk_analyses 1 ──── 0..* alerts

hutchinson_sites 1 ──── 0..* supplier_relationships
suppliers 1 ──── 0..* supplier_relationships

alerts 1 ──── 0..* notifications
users 1 ──── 0..* notifications
users 1 ──── 0..* alerts (assigned_to)

ground_truth_cases 1 ──── 0..* ground_truth_results
```

---

## Volumétrie Estimée

| Table | Volumétrie Estimée |
|-------|-------------------|
| `documents` | ~10,000 / an |
| `hutchinson_sites` | ~80-90 |
| `suppliers` | ~500-1000 |
| `supplier_relationships` | ~2000-5000 |
| `pertinence_checks` | ~10,000 / an |
| `risk_analyses` | ~3000-5000 / an |
| `judge_evaluations` | ~3000-5000 / an |
| `alerts` | ~1000-2000 / an |
| `notifications` | ~5000-10000 / an |
| `ground_truth_cases` | ~100-200 / an |
| `users` | ~20-50 |
