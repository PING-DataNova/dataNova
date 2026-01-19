# 🚀 Guide de démarrage rapide

## ✅ Étapes complétées

- [x] Architecture analysée et corrigée
- [x] Conflits de merge résolus
- [x] Dépendances installées (`docling` ajouté)
- [x] Configuration `.env` corrigée (format JSON pour listes)
- [x] Base de données initialisée
- [x] Profils entreprise chargés

## 📋 État actuel

### ✅ Fonctionnel
- Agent 1A complet avec 4 outils :
  - `search_eurlex_tool` - Recherche EUR-Lex
  - `fetch_document_tool` - Téléchargement documents
  - `extract_pdf_content_tool` - Extraction PDF avec Docling
  - `generate_summary_tool` - Résumés LLM
- Pipeline orchestration (base)
- Base de données SQLite
- 2 profils entreprise de test

### ⚠️ À implémenter
- Agent 1B (analyse de pertinence)
- Agent 2 (analyse d'impact)
- Notifications email
- Interface validation UI

## 🧪 Tests rapides

### 1. Vérifier l'architecture
```bash
uv run python test_architecture.py
```

### 2. Tester Agent 1A (recherche EUR-Lex)
```bash
uv run python demo_agent_1a.py
```

### 3. Vérifier la base de données
```bash
uv run python -c "
from src.storage.database import get_session
from src.storage.models import CompanyProfile
session = get_session()
print(f'Profils: {session.query(CompanyProfile).count()}')
session.close()
"
```

## 📝 Prochaines étapes prioritaires

### 1. Tester Agent 1A en production
```bash
# Lancer une recherche CBAM sur EUR-Lex
uv run python -c "
import asyncio
from src.agent_1a.agent import run_agent_1a_eurlex

async def test():
    result = await run_agent_1a_eurlex(keyword='CBAM', max_documents=3)
    print(result)

asyncio.run(test())
"
```

### 2. Développer Agent 1B
**Fichiers à compléter** :
- `src/agent_1b/tools.py` - Implémenter les 6 outils
- `src/agent_1b/agent.py` - Logique d'analyse
- `src/agent_1b/tools/semantic_analyzer.py` - Analyse LLM

**Outils à implémenter** :
1. `filter_by_keywords()` - Filtrage mots-clés
2. `verify_nc_codes()` - Vérification codes NC
3. `semantic_analysis()` - Analyse sémantique LLM
4. `calculate_relevance_score()` - Calcul score pondéré
5. `generate_alert()` - Génération alertes JSON
6. `save_analysis()` - Sauvegarde en DB

### 3. Tester le pipeline complet
```bash
uv run python -c "
from src.orchestration.pipeline import run_pipeline
result = run_pipeline()
print(result)
"
```

### 4. Développer Agent 2
**Fichiers à compléter** :
- `src/agent_2/agent.py`
- `src/agent_2/tools/impact_analyzer.py`
- `src/agent_2/tools/scorer.py`
- `src/agent_2/tools/action_recommender.py`

## 🐛 Problèmes courants

### Erreur "No module named 'docling'"
```bash
uv sync  # Réinstaller les dépendances
```

### Erreur JSON parsing dans .env
Vérifier que `ALERT_RECIPIENTS` est au format JSON :
```bash
# ❌ MAUVAIS
ALERT_RECIPIENTS=email1@example.com,email2@example.com

# ✅ BON
ALERT_RECIPIENTS=["email1@example.com", "email2@example.com"]
```

### Base de données non initialisée
```bash
uv run python scripts/init_db.py
```

## 📊 Architecture des données

### Tables créées
- `documents` - Documents réglementaires collectés
- `analyses` - Analyses de pertinence (Agent 1B)
- `impact_assessments` - Analyses d'impact (Agent 2)
- `alerts` - Alertes générées
- `execution_logs` - Logs d'exécution
- `company_profiles` - Profils entreprise

### Profils entreprise
- **AeroRubber Industries** - Profil unique configuré avec :
  - 3 codes NC (imports caoutchouc naturel et synthétique)
  - Réglementations critiques : CBAM, EUDR
  - Réglementations haute priorité : CSRD, Sanctions internationales
  - Réglementations moyennes : Droits de douane, REACH, Dual-use, Normes sectorielles

## 🔑 Variables d'environnement importantes

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...  # Clé API Claude
DATABASE_URL=sqlite:///./data/datanova.db
LOG_LEVEL=INFO
DEFAULT_COMPANY_PROFILE=aerorubber_industries
SCHEDULER_ENABLED=true
CRON_SCHEDULE="0 8 * * 1"  # Lundi 8h
```

## 📚 Documentation

- [CORRECTIONS_APPLIQUEES.md](CORRECTIONS_APPLIQUEES.md) - Détails des corrections
- [DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) - Schéma de base de données
- [README.md](README.md) - Documentation générale

## 🎯 Objectif final

Pipeline complet fonctionnel :
```
Agent 1A (Collecte EUR-Lex)
    ↓
Agent 1B (Analyse pertinence)
    ↓
UI Validation (Interface juriste)
    ↓
Agent 2 (Analyse impact)
    ↓
Notifications (Email/Slack)
```

---

**Dernière mise à jour** : 16 janvier 2026  
**Statut** : ✅ Agent 1A opérationnel, DB initialisée, prêt pour développement Agent 1B
