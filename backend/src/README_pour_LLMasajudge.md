# Agent 3 : LLM Judge - Évaluation de Qualité (Anthropic Claude)

Agent 3 évalue la qualité des analyses produites par Agent 1B (Pertinence Checker) et Agent 2 (Risk Analyzer) selon 8 critères avec scoring pondéré adaptatif.

**Version** : Anthropic Claude API (SDK natif)

---

## 📊 Fonctionnalités

### 1. Évaluation Multi-Critères

**Pour Pertinence Checker (4 critères)** :

- Source Relevance
- Company Data Alignment
- Logical Coherence
- Traceability

**Pour Risk Analyzer (8 critères)** :

- Source Relevance
- Company Data Alignment
- Logical Coherence
- Completeness
- Recommendation Appropriateness
- Traceability
- Strategic Alignment (nouveau)
- Actionability Timeline (nouveau)

### 2. Scoring Pondéré par Type de Risque

Les critères ont des poids différents selon le type d'événement :

- **Climatique** : Traceability et Company Data Alignment plus importants
- **Réglementaire** : Source Relevance et Traceability critiques
- **Géopolitique** : Strategic Alignment et Recommendation Appropriateness prioritaires

### 3. Confidence Score

Chaque critère a un score de confiance (0-1) permettant de détecter les évaluations incertaines.

### 4. Explainability Renforcée

Pour chaque critère :

- **Score** (0-10)
- **Confidence** (0-1)
- **Comment** (1-2 phrases)
- **Evidence** (liste de preuves)
- **Weaknesses** (liste de faiblesses)

### 5. Décision Automatique

| Score Global | Confiance | Action |
|--------------|-----------|--------|
| ≥ 8.5 | ≥ 0.85 | **APPROVE** (Alerte immédiate) |
| ≥ 8.5 | < 0.85 | **REVIEW** (Validation humaine) |
| 7.0-8.4 | ≥ 0.80 | **REVIEW** |
| 7.0-8.4 | < 0.80 | **REVIEW_PRIORITY** |
| < 7.0 | - | **REJECT** (Archiver) |

### 6. Feedback Loop

Système d'amélioration continue basé sur les validations humaines :

- Log des désaccords Judge vs Humain
- Analyse des patterns tous les 10 cas
- Ajustement automatique des seuils
- Métriques de performance (cible: ≥ 92% accuracy)

---

## 📁 Structure des Fichiers

```

agent_3/
├── __init__.py                  # Exports du module
├── judge.py                     # Agent Judge principal (Anthropic)
├── criteria_evaluator.py        # Évaluation des critères avec Claude
├── weights_config.py            # Configuration des poids par type de risque
├── prompts.py                   # Prompts structurés pour Claude
├── feedback_loop.py             # Système d'amélioration continue
├── test_judge.py                # Tests avec données réelles
└── README.md                    # Cette documentation
```

---

## 🚀 Installation

### 1. Installer le SDK Anthropic

```bash
pip install anthropic
```

### 2. Copier les Fichiers

```bash
# Dans votre dépôt dataNova
cd backend/src

# Créer le dossier agent_3
mkdir -p agent_3

# Copier tous les fichiers du package
cp /path/to/agent_3_anthropic/agent_3/* agent_3/
```

### 3. Configuration

Créez ou modifiez le fichier `.env` :

```bash
# API Key Anthropic
ANTHROPIC_API_KEY=sk-ant-api03-...

# (Optionnel) Pour Agent 2 si vous utilisez aussi OpenAI
OPENAI_API_KEY=your_openai_key_here
```

**Important** : Le SDK Anthropic cherche automatiquement `ANTHROPIC_API_KEY` dans les variables d'environnement.

---

## 🧪 Tests

### Test Complet avec Données Réelles

```bash
cd backend/src/agent_3

# Exécuter le test
python test_judge.py
```

**Résultat attendu** :

```
================================================================================
🧪 TESTS AGENT 3 (JUDGE) - Évaluation de Qualité
================================================================================

📊 Données chargées:
  - 8 sites
  - 10 fournisseurs
  - 10 relations
  - 3 documents

================================================================================
🧪 TEST : Inondations majeures à Bangkok...
   Type: climatique
================================================================================

🔄 Étape 1 : Analyse d'Agent 2...

📊 Résultat Agent 2:
   - Sites impactés: 1
   - Fournisseurs impactés: 1
   - Niveau de risque: CRITIQUE
   - Recommandations: 9

🔄 Étape 2 : Évaluation du Judge...

🎯 Évaluation Judge pour document: doc_bangkok_flood
   Type d'événement: climatique

📋 Évaluation du Pertinence Checker...
   ✅ Score pondéré: 9.1/10
   ✅ Confiance: 0.93

📊 Évaluation du Risk Analyzer...
   ✅ Score pondéré: 8.4/10
   ✅ Confiance: 0.88

🎯 Score global: 8.7/10
🎯 Confiance globale: 0.90

🤔 Détermination de l'action...
   ✅ Action: APPROVE
   📝 Raisonnement: Score global de 8.7 (> 8.5) avec confiance élevée (0.90)...

================================================================================
✅ RÉSULTAT DE L'ÉVALUATION JUDGE
================================================================================

📋 Pertinence Checker:
   Score pondéré: 9.1/10
   Confiance: 0.93

📊 Risk Analyzer:
   Score pondéré: 8.4/10
   Confiance: 0.88

🎯 Score Global: 8.7/10
🎯 Confiance Globale: 0.90

🚦 Décision: APPROVE
📝 Raisonnement: Score global de 8.7 (> 8.5) avec confiance élevée (0.90)...

💾 Résultat complet sauvegardé dans: judge_result.json

================================================================================
✅ TEST TERMINÉ
================================================================================
```

---

## 💻 Utilisation Programmatique

### Exemple Simple

```python
from agent_3.judge import Judge

# Initialiser le Judge (utilise ANTHROPIC_API_KEY automatiquement)
judge = Judge(llm_model="claude-sonnet-4-20250514")

# Évaluer une analyse
result = judge.evaluate(
    document=document_dict,
    pertinence_result=pertinence_result,
    risk_analysis=risk_analysis,
    sites=sites_list,
    suppliers=suppliers_list,
    supplier_relationships=relationships_list
)

# Récupérer la décision
action = result['judge_evaluation']['action_recommended']
score = result['judge_evaluation']['overall_quality_score']
reasoning = result['judge_evaluation']['reasoning']

print(f"Décision: {action}")
print(f"Score: {score}/10")
print(f"Raisonnement: {reasoning}")
```

### Exemple avec Feedback Loop

```python
from agent_3.judge import Judge
from agent_3.feedback_loop import JudgeFeedbackLoop

judge = Judge()
feedback = JudgeFeedbackLoop()

# Évaluer
result = judge.evaluate(...)
judge_decision = result['judge_evaluation']['action_recommended']
judge_score = result['judge_evaluation']['overall_quality_score']

# Validation humaine
human_decision = "APPROVE"  # Décision de l'humain
human_reasoning = "Analyse complète et bien justifiée"

if judge_decision != human_decision:
    # Log du désaccord
    feedback.log_disagreement(
        case_id=document_id,
        judge_decision=judge_decision,
        human_decision=human_decision,
        human_reasoning=human_reasoning,
        judge_score=judge_score
    )
else:
    # Log de l'accord
    feedback.log_agreement(
        case_id=document_id,
        decision=judge_decision,
        score=judge_score
    )

# Récupérer les métriques
metrics = feedback.get_metrics()
print(f"Précision du Judge: {metrics['judge_accuracy'] * 100}%")
```

---

## 🔧 Modèles Claude Disponibles

Le SDK Anthropic supporte plusieurs modèles Claude :

- **`claude-sonnet-4-20250514`** (recommandé) : Meilleur équilibre qualité/coût
- **`claude-opus-4-20250514`** : Qualité maximale (plus coûteux)
- **`claude-haiku-4-20250514`** : Plus rapide et économique

Pour changer de modèle :

```python
judge = Judge(llm_model="claude-opus-4-20250514")
```

---

## 📊 Différences avec la Version OpenAI

| Aspect | Version Anthropic | Version OpenAI (Proxy) |
|--------|-------------------|------------------------|
| SDK | `anthropic` | `openai` |
| API Key | `ANTHROPIC_API_KEY` | `OPENAI_API_KEY` |
| Modèle | `claude-sonnet-4-20250514` | `claude-sonnet-4-5-20250929` |
| Appel API | `client.messages.create()` | `client.chat.completions.create()` |
| Réponse | `response.content[0].text` | `response.choices[0].message.content` |

---

## 🐛 Résolution de Problèmes

### Erreur : "ANTHROPIC_API_KEY not found"

```bash
# Créer le fichier .env
echo "ANTHROPIC_API_KEY=sk-ant-api03-..." > backend/.env

# Vérifier
cat backend/.env
```

### Erreur : "Module 'anthropic' not found"

```bash
# Installer le SDK
pip install anthropic

# Vérifier
python -c "import anthropic; print(anthropic.__version__)"
```

### Scores trop bas ou trop élevés

Ajuster les poids dans `weights_config.py` ou utiliser le feedback loop pour calibrer automatiquement.

---

## 💰 Coûts Estimés

**Avec Claude Sonnet 4** :
- ~2-3 appels API par évaluation
- ~4000 tokens par appel (input + output)
- Coût : ~$0.02-0.03 par évaluation complète

**Pour 1000 évaluations/mois** : ~$20-30/mois

---

## 📝 Notes Importantes

- **Modèle LLM** : Claude Sonnet 4 recommandé pour la meilleure qualité
- **Performance** : ~10-15 secondes par évaluation complète
- **Précision cible** : ≥ 92% d'accord avec les validations humaines
- **Rate Limits** : Respecter les limites de l'API Anthropic (vérifier votre tier)

---

**Créé le 31 janvier 2026 pour le projet PING (Hutchinson)**
**Version Anthropic Claude API**
