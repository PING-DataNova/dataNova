# 🔍 ANALYSE TECHNIQUE DES ÉCARTS
## État actuel vs Demandes client - Projet PING

**Date d'analyse** : 03/02/2026  
**Branche analysée** : Suite_godson  
**Objectif** : Identifier précisément ce qui est fait, ce qui manque, et où intervenir dans le code
**Dernière mise à jour** : 03/02/2026 - Audit code réel effectué

---

# ⚠️ PROBLÈME CRITIQUE IDENTIFIÉ

> **Le champ `workflow_status` est utilisé dans 6 fichiers mais N'EXISTE PAS dans `models.py` !**
> 
> Le pipeline va PLANTER si on l'exécute.

**Fichiers concernés :**
- `orchestration/pipeline.py` (lignes 97-99, 161) - filtre sur `Document.workflow_status`
- `storage/repositories.py` (lignes 207-235) - méthodes `find_by_workflow_status`, `update_workflow_status`
- `storage/analysis_repository.py` (ligne 133) - `document.workflow_status = "analyzed"`
- `api/routes/analyses.py` (lignes 156, 159) - mise à jour du statut

**Mais dans `storage/models.py` :** Le champ n'existe pas sur `Document` !

**Il existait dans `models_old_backup.py` (ligne 54) mais a été perdu lors d'une refonte.**

---

# 1. ✅ CE QUI EST DÉJÀ IMPLÉMENTÉ

## 1.1 Backend - Agents IA

| Composant | Fichier(s) | Statut | Description |
|-----------|------------|--------|-------------|
| **Agent 1A** | `backend/src/agent_1a/agent.py` | ✅ Complet | Collecte EUR-Lex + extraction PDF + collecte météo OpenMeteo |
| **Agent 1B** | `backend/src/agent_1b/agent.py` | ✅ Complet | Analyse de pertinence (triple filtrage 30%+30%+40%) |
| **Agent 2** | `backend/src/agent_2/agent.py` | ✅ Complet | Analyse d'impact + projection géographique + recommandations |
| **LLM Judge** | `backend/src/llm_judge/` | ✅ Complet | Évaluation qualité des analyses (score 0-10) |

### Fonctions clés disponibles :

```python
# Agent 1A
run_agent_1a_full_collection(company_profile_path, ...)  # Collecte complète
run_agent_1a_combined(keyword, ...)                       # Mode legacy par mot-clé

# Agent 1B  
Agent1B(company_profile).analyze_document(...)           # Analyse pertinence

# Agent 2
Agent2().analyze_impact(analysis_id)                     # Analyse d'impact
Agent2().run(validation_status="approved", limit=10)     # Batch processing
```

## 1.2 Backend - Base de données

| Modèle | Fichier | Statut | Description |
|--------|---------|--------|-------------|
| `Document` | `storage/models.py` | ✅ | Documents collectés (EUR-Lex, météo, géopolitique) |
| `HutchinsonSite` | `storage/models.py` | ✅ | Sites de production (90 sites) |
| `Supplier` | `storage/models.py` | ✅ | Fournisseurs |
| `SupplierRelationship` | `storage/models.py` | ✅ | Relations sites-fournisseurs |
| `PertinenceCheck` | `storage/models.py` | ✅ | Résultats Agent 1B |
| `RiskAnalysis` | `storage/models.py` | ✅ | Résultats Agent 2 |
| `JudgeEvaluation` | `storage/models.py` | ✅ | Scores LLM Judge |
| `RiskProjection` | `storage/models.py` | ✅ | Projection par entité |
| `WeatherAlert` | `storage/models.py` | ✅ | Alertes météo |
| `Alert` | `storage/models.py` | ✅ | Alertes générées |
| `Notification` | `storage/models.py` | ✅ | Notifications utilisateurs |
| `User` | `storage/models.py` | ✅ | Utilisateurs système |
| `SupplierAnalysis` | `storage/models.py` | ✅ | Analyses ponctuelles fournisseurs |
| `ExecutionLog` | `storage/models.py` | ✅ | Logs d'exécution agents |

## 1.3 Backend - Orchestration

| Composant | Fichier | Statut | Description |
|-----------|---------|--------|-------------|
| **Pipeline** | `orchestration/pipeline.py` | ⚠️ BUG | Agent1A → Agent1B mais utilise `workflow_status` qui n'existe pas |
| **Scheduler** | `orchestration/scheduler.py` | ✅ Présent | APScheduler configuré (cron) |
| **LangGraph** | `orchestration/langgraph_workflow.py` | ✅ Présent | Workflow avancé |

### Code existant du scheduler :
```python
# backend/src/orchestration/scheduler.py
def start_scheduler():
    scheduler = BlockingScheduler()
    trigger = CronTrigger.from_crontab(settings.cron_schedule)
    scheduler.add_job(scheduled_job, trigger=trigger, ...)
```

## 1.4 Backend - API Endpoints

| Endpoint | Fichier | Statut | Description |
|----------|---------|--------|-------------|
| `POST /pipeline/agent1/trigger` | `api/routes/pipeline.py` | ✅ | Déclencher Agent 1 |
| `POST /pipeline/agent2/trigger` | `api/routes/pipeline.py` | ✅ | Déclencher Agent 2 |
| `GET /pipeline/agent1/status` | `api/routes/pipeline.py` | ✅ | Statut Agent 1 |
| `GET /pipeline/agent2/status` | `api/routes/pipeline.py` | ✅ | Statut Agent 2 |
| `GET /impacts` | `api/routes/impacts.py` | ✅ | Liste des impacts |
| `GET /impacts/stats/dashboard` | `api/routes/impacts.py` | ✅ | Stats dashboard |
| `GET /analyses` | `api/routes/analyses.py` | ✅ | Liste analyses |
| `POST /supplier/analyze` | `api/routes/supplier.py` | ✅ | Analyse fournisseur |

## 1.5 Backend - Repositories (Data Access Layer)

| Repository | Fichier | Statut |
|------------|---------|--------|
| `DocumentRepository` | `storage/repositories.py` | ✅ |
| `AnalysisRepository` | `storage/repositories.py` | ✅ |
| `ImpactAssessmentRepository` | `storage/repositories.py` | ✅ |
| `AlertRepository` | `storage/repositories.py` | ✅ |

---

# 2. ❌ CE QUI MANQUE (par priorité)

## 2.1 🔴 PRIORITÉ 1 - Obligatoire pour jeudi

### A. 🚨 BUG CRITIQUE - Ajouter `workflow_status` dans models.py

**Problème identifié lors de l'audit :**
- Le code utilise `Document.workflow_status` dans 6 fichiers
- MAIS ce champ N'EXISTE PAS dans `storage/models.py`
- Le pipeline va PLANTER si on l'exécute !

**Ce qu'il faut faire IMMÉDIATEMENT :**

| Fichier | Action | Description |
|---------|--------|-------------|
| `backend/src/storage/models.py` | **MODIFIER** | Ajouter colonnes sur `Document` |

**Colonnes à ajouter sur `Document` (classe ligne ~82) :**
```python
# Workflow de validation (Agent 1A -> 1B -> UI -> Agent 2)
workflow_status = Column(String(20), nullable=False, default="raw")
# Valeurs: raw, analyzed, rejected_analysis, validated, rejected_validation
regulation_type = Column(String(50), nullable=True)  # CBAM, EUDR, CSRD...
analyzed_at = Column(DateTime, nullable=True)
validated_at = Column(DateTime, nullable=True)
validated_by = Column(String(200), nullable=True)
```

---

### B. Analyse automatique globale (batch tous sites/fournisseurs)

**Demande client :**
> *"L'application se lance toute seule, scanne toutes les sources, croise avec TOUS les sites et fournisseurs, et produit des rapports."*

**État actuel (vérifié par audit) :**
- `orchestration/pipeline.py` a `run_pipeline(keyword)` (265 lignes)
- Cette fonction fait Agent1A → Agent1B sur les **documents par mot-clé**
- **MAIS NE BOUCLE PAS** sur chaque site/fournisseur
- Pas de fonction `run_global_analysis()` trouvée dans le code

**Ce qu'il faut créer :**

| Fichier | Action | Description |
|---------|--------|-------------|
| `backend/src/orchestration/pipeline.py` | **MODIFIER** | Ajouter fonction `run_global_analysis()` |
| `backend/src/api/routes/pipeline.py` | **MODIFIER** | Ajouter endpoint `POST /pipeline/global/trigger` |

**Code à ajouter dans `pipeline.py` :**
```python
async def run_global_analysis(
    include_sites: bool = True,
    include_suppliers: bool = True,
    max_entities: int = 0,  # 0 = tous
    save_to_db: bool = True
) -> Dict:
    """
    Analyse automatique globale sur tous les sites et fournisseurs.
    
    Workflow:
    1. Charger tous les HutchinsonSite depuis la BDD
    2. Charger tous les Supplier depuis la BDD
    3. Pour chaque entité:
       - Lancer Agent 1A (collecte docs pertinents + météo)
       - Lancer Agent 1B (pertinence)
       - Lancer Agent 2 (analyse d'impact)
       - Créer RiskProjection
       - Créer Alert si risque critique
    4. Calculer TOP 10 des risques
    5. Stocker rapports en BDD
    """
    # TODO: Implémenter
```

---

### C. Endpoint TOP 10 des risques

**Demande client :**
> *"Je veux voir le TOP 10 des risques critiques quand je me connecte le matin."*

**État actuel :** N'existe pas

**Ce qu'il faut créer :**

| Fichier | Action | Description |
|---------|--------|-------------|
| `backend/src/api/routes/reports.py` | **CRÉER** | Nouveau fichier pour endpoints rapports |

**Endpoints à créer :**
```python
# GET /api/reports/top-risks?limit=10&type=all
# GET /api/reports/{id}
# GET /api/reports/{id}/pdf
```

**Structure réponse TOP 10 :**
```json
{
  "generated_at": "2026-02-03T06:00:00Z",
  "total_analyzed": 156,
  "top_risks": [
    {
      "rank": 1,
      "id": "risk-001",
      "type": "regulatory",
      "title": "CBAM - Taxe carbone",
      "risk_score": 85,
      "impact_score": 78,
      "entities_impacted": 12,
      "source_url": "https://eur-lex.europa.eu/...",
      "report_url": "/api/reports/risk-001"
    }
  ]
}
```

---

### D. Génération et stockage des rapports PDF

**Demande client :**
> *"Ce rapport a été généré automatiquement par une IA. Score de confiance: 92%"*

**État actuel (vérifié par audit) :**
- Pas de fichier `pdf_generator.py` dans `utils/`
- Pas de champs `pdf_url`, `generated_by_ai` dans les modèles

**Ce qu'il faut créer :**

| Fichier | Action | Description |
|---------|--------|-------------|
| `backend/src/utils/pdf_generator.py` | **CRÉER** | Générateur PDF (WeasyPrint) |
| `backend/src/storage/models.py` | **MODIFIER** | Ajouter champs `pdf_url`, `generated_by_ai` |

**Champs à ajouter dans `RiskAnalysis` :**
```python
# Dans storage/models.py
pdf_url = Column(String(500), nullable=True)  # URL du PDF généré
generated_by_ai = Column(Boolean, default=True)
ai_confidence_score = Column(Float, nullable=True)  # Score LLM Judge
```

---

## 2.2 🟡 PRIORITÉ 2 - Important mais peut attendre

### E. Notifications email

**Demande client :**
> *"Une notification est envoyée aux équipes achats."*

**État actuel (vérifié par audit) :**
- Modèle `Notification` existe dans `storage/models.py`
- Fichier `notifications/email_sender.py` existe mais est **VIDE** (seulement 15 lignes de TODO)

**Ce qu'il faut faire :**

| Fichier | Action | Description |
|---------|--------|-------------|
| `backend/src/notifications/email_sender.py` | **IMPLÉMENTER** | Client SMTP (aiosmtplib) |
| `backend/src/api/routes/notifications.py` | **CRÉER** | Endpoints notifications |

**Code minimal à implémenter :**
```python
# backend/src/notifications/email_sender.py
import aiosmtplib
from email.mime.text import MIMEText

async def send_alert_email(
    recipients: List[str],
    subject: str,
    body_html: str,
    alert_id: str
) -> bool:
    """Envoie un email d'alerte."""
    # TODO: Implémenter avec config SMTP
```

---

### F. Interface d'administration (paramétrage)

**Demande client :**
> *"Rajouter une source d'information, rajouter un type de risque, sans toucher au code."*

**État actuel :** N'existe pas

**Ce qu'il faut créer :**

| Fichier | Action | Description |
|---------|--------|-------------|
| `backend/src/api/routes/admin.py` | **CRÉER** | Endpoints admin |
| `backend/src/storage/models.py` | **MODIFIER** | Modèle `DataSource` pour sources paramétrables |

**Endpoints admin à créer :**
```python
# Sources
GET  /api/admin/sources          # Liste des sources
POST /api/admin/sources          # Ajouter une source
PUT  /api/admin/sources/{id}     # Modifier une source

# Catégories de risques
GET  /api/admin/risk-categories
POST /api/admin/risk-categories

# Scheduler
GET  /api/admin/scheduler/config
PUT  /api/admin/scheduler/config
POST /api/admin/scheduler/run-now
```

---

### G. Filtres enregistrables par utilisateur

**Demande client :**
> *"Elle fait ses filtres, elle les enregistre."*

**État actuel :** N'existe pas

**Ce qu'il faut créer :**

| Fichier | Action | Description |
|---------|--------|-------------|
| `backend/src/storage/models.py` | **MODIFIER** | Ajouter modèle `UserFilter` |
| `backend/src/api/routes/filters.py` | **CRÉER** | CRUD filtres utilisateur |

**Modèle à ajouter :**
```python
class UserFilter(Base):
    __tablename__ = "user_filters"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    filter_config = Column(JSON, nullable=False)  # {region: "Europe", risk_type: "regulatory", ...}
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 2.3 ⚪ PRIORITÉ 3 - V2 (différé)

### H. Workflow validation humaine complet

**Demande client :**
> *"Workflow de validation avec statuts, relances, versioning."*

**État actuel :**
- Modèles `JudgeEvaluation` et logique de score existent
- Pas d'UI de validation, pas de relances automatiques

**Ce qu'il faut créer (V2) :**

| Fichier | Action | Description |
|---------|--------|-------------|
| `backend/src/api/routes/validation.py` | **CRÉER** | Approve/Reject endpoints |
| `backend/src/orchestration/validation_workflow.py` | **CRÉER** | Logique relances |

---

### I. Multi-utilisateurs avec rôles

**État actuel :**
- Modèle `User` existe avec champ `role`
- Pas d'authentification implémentée

**Ce qu'il faut créer (V2) :**

| Fichier | Action | Description |
|---------|--------|-------------|
| `backend/src/api/routes/auth.py` | **COMPLÉTER** | Login/logout/JWT |
| `backend/src/api/deps.py` | **MODIFIER** | Middleware authentification |

---

# 3. 📁 FICHIERS À MODIFIER/CRÉER (RÉSUMÉ)

## 3.1 Fichiers à MODIFIER

| Fichier | Modifications |
|---------|---------------|
| `backend/src/storage/models.py` | Ajouter colonnes: `workflow_status`, `pdf_url`, `generated_by_ai`, `ai_confidence_score` sur Document/RiskAnalysis |
| `backend/src/orchestration/pipeline.py` | Ajouter `run_global_analysis()` |
| `backend/src/orchestration/scheduler.py` | Lire config depuis DB au lieu de settings |
| `backend/src/api/routes/pipeline.py` | Ajouter `POST /pipeline/global/trigger` |
| `backend/src/api/main.py` | Enregistrer nouveaux routers (reports, admin, notifications) |
| `backend/src/notifications/email_sender.py` | Implémenter envoi email |

## 3.2 Fichiers à CRÉER

| Fichier | Description |
|---------|-------------|
| `backend/src/api/routes/reports.py` | Endpoints TOP risks, détail rapport, PDF |
| `backend/src/api/routes/admin.py` | Endpoints administration (sources, scheduler) |
| `backend/src/api/routes/notifications.py` | Endpoints notifications |
| `backend/src/api/routes/validation.py` | Endpoints validation humaine |
| `backend/src/api/routes/filters.py` | Endpoints filtres utilisateur |
| `backend/src/utils/pdf_generator.py` | Générateur de rapports PDF |
| `backend/alembic/versions/xxx_add_missing_columns.py` | Migration DB |

---

# 4. 📊 ESTIMATION DES EFFORTS

## 4.1 Pour livraison jeudi (P1 uniquement)

| Tâche | Effort estimé | Fichiers concernés |
|-------|---------------|-------------------|
| **🚨 URGENT: Fix bug workflow_status** | **0.25 jour** | **`models.py`, migration alembic** |
| Harmoniser DB (autres colonnes) | 0.25 jour | `models.py`, migration alembic |
| Implémenter `run_global_analysis()` | 1-1.5 jour | `pipeline.py` |
| Endpoint TOP 10 + détail rapport | 0.5 jour | `reports.py` (nouveau) |
| Génération PDF basique | 0.5-1 jour | `pdf_generator.py` (nouveau) |
| Endpoint trigger global + scheduler | 0.25 jour | `pipeline.py`, `scheduler.py` |
| Tests unitaires basiques | 0.5 jour | `tests/` |
| **TOTAL Backend P1** | **3-4 jours** | |

## 4.2 Frontend (estimation séparée)

| Tâche | Effort estimé |
|-------|---------------|
| Dashboard avec TOP 10 (appel API) | 0.5-1 jour |
| Page risques avec matrice | 1 jour |
| Page détail rapport | 0.5 jour |
| Connexion analyse fournisseur existante | 0.25 jour |
| **TOTAL Frontend P1** | **2-3 jours** |

## 4.3 Phase 2 (après jeudi)

| Tâche | Effort estimé |
|-------|---------------|
| Notifications email complètes | 1 jour |
| Interface admin (sources, scheduler) | 1-2 jours |
| Filtres enregistrables | 1 jour |
| Workflow validation humaine | 2-3 jours |
| Multi-utilisateurs + auth | 2 jours |
| **TOTAL Phase 2** | **7-10 jours** |

---

# 5. 🚀 PLAN D'ACTION RECOMMANDÉ

## Jour 1 (03/02) - Fondations

| Heure | Tâche | Responsable |
|-------|-------|-------------|
| **IMMÉDIAT** | **🚨 Fix bug `workflow_status` dans models.py** | **Backend** |
| Matin | Créer migration Alembic | Backend |
| Après-midi | Implémenter `run_global_analysis()` (début) | Backend |
| Après-midi | Créer `reports.py` avec endpoint TOP 10 | Backend |

## Jour 2 (04/02) - Core features

| Heure | Tâche | Responsable |
|-------|-------|-------------|
| Matin | Finir `run_global_analysis()` | Backend |
| Matin | Créer `pdf_generator.py` | Backend |
| Après-midi | Endpoint `/pipeline/global/trigger` | Backend |
| Après-midi | Tests unitaires pipeline global | Backend |

## Jour 3 (05/02) - Intégration + Frontend

| Heure | Tâche | Responsable |
|-------|-------|-------------|
| Matin | Connecter scheduler au pipeline global | Backend |
| Matin | Dashboard frontend (appel API top-risks) | Frontend |
| Après-midi | Page détail rapport frontend | Frontend |
| Après-midi | Tests d'intégration | Tous |

## Jour 4 (06/02) - Finalisation + Démo

| Heure | Tâche | Responsable |
|-------|-------|-------------|
| Matin | Corrections bugs | Tous |
| Matin | Données de test (5 sites, 10 fournisseurs) | Backend |
| Après-midi | Démo interne | Tous |
| Après-midi | Préparation présentation client | Tous |

---

# 6. ⚠️ POINTS D'ATTENTION

## 6.1 Risques techniques

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Volume données (16k fournisseurs) | Timeout, coûts LLM élevés | Limiter batch à 100 entités pour POC |
| Migration DB | Perte de données | Backup avant migration |
| Intégration frontend | Blocages | Définir contrat API d'abord |

## 6.2 Questions à valider avec le client

1. **Budget LLM** : Combien d'analyses/jour max ? (coût API Claude)
2. **SMTP** : Config serveur email fournie ou mock ?
3. **Authentification** : Nécessaire pour jeudi ou V2 ?
4. **Données réelles** : Fichier Excel sites reçu de Guillaume ?

## 6.3 Dépendances externes

| Dépendance | Status | Action |
|------------|--------|--------|
| API EUR-Lex | ✅ Fonctionnel | - |
| API OpenMeteo | ✅ Fonctionnel | - |
| API Claude (Anthropic) | ✅ Fonctionnel | Vérifier quotas |
| Serveur SMTP | ❓ À configurer | Demander config au client |

---

# 7. 📝 CHECKLIST AVANT LIVRAISON

## Backend

- [ ] **🚨 Bug `workflow_status` corrigé dans models.py**
- [ ] Migration DB appliquée sans erreur
- [ ] `run_global_analysis()` fonctionne sur 5 sites test
- [ ] Endpoint `/api/reports/top-risks` retourne données
- [ ] Endpoint `/api/reports/{id}` retourne détail
- [ ] PDF généré avec mention "Généré par IA"
- [ ] Scheduler configuré pour 1x/jour
- [ ] Logs d'exécution enregistrés

## Frontend

- [ ] Dashboard affiche TOP 10 depuis API
- [ ] Page détail rapport fonctionnelle
- [ ] Analyse fournisseur connectée au backend
- [ ] Notifications (cloche) affichées

## Documentation

- [ ] Schéma architecture mis à jour (fait vs V2)
- [ ] README mis à jour avec nouvelles instructions
- [ ] Endpoints API documentés

## Tests

- [ ] Tests unitaires passent
- [ ] Test d'intégration pipeline global
- [ ] Test UAT sur cas CBAM

---

*Document généré le 03/02/2026*
*À utiliser comme référence pour le développement*
