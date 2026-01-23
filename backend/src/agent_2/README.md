# Agent 2 - Analyse d'impact

**Responsable** : Dev 4

## 📋 Mission

Analyser l'impact détaillé des réglementations **validées par l'UI** et générer des recommandations actionnables.

## 🔄 Workflow

```
Input: Analyses avec validation_status="approved"
   ↓
1. Charger l'analyse et le document
   ↓
2. Calculer score (0-1) et criticité (CRITICAL/HIGH/MEDIUM/LOW)
   ↓
3. Analyser impacts :
   - Fournisseurs (data/suppliers/*.json)
   - Produits (codes NC)
   - Flux douaniers (data/customs_flows/*.json)
   - Impact financier
   ↓
4. Générer recommandations et plan d'action
   ↓
5. Créer ImpactAssessment
   ↓
6. Créer Alert enrichie
   ↓
Output: ImpactAssessment + Alert (status="pending")
```

## 📊 Base de données

### Input (lecture)
- `analyses` (validation_status="approved")
- `documents` (workflow_status="validated")
- `company_profiles`

### Output (écriture)
- `impact_assessments` (nouvelle entrée)
- `alerts` (nouvelle entrée)
- `documents` (mise à jour workflow_status si nécessaire)

## 🛠️ Fichiers à implémenter

### 1. `agent.py`
Classe principale `Agent2` avec :
- `__init__()`: Initialisation LLM + outils
- `run()`: Pipeline principal
- `analyze_impact(analysis_id)`: Analyse une réglementation validée

### 2. `tools/impact_analyzer.py`
```python
@tool
def analyze_impact(document_content, regulation_type, nc_codes) -> dict:
    """
    Analyser l'impact détaillé
    - Croiser avec fournisseurs
    - Identifier produits
    - Analyser flux douaniers
    - Estimer coûts
    """
```

### 3. `tools/scorer.py`
```python
@tool
def calculate_score(suppliers_count, products_count, financial_impact, deadline_days) -> dict:
    """
    Calculer score (0-1) et criticité
    - CRITICAL: >= 0.8
    - HIGH: >= 0.6
    - MEDIUM: >= 0.4
    - LOW: < 0.4
    """
```

### 4. `tools/action_recommender.py`
```python
@tool
def generate_recommendations(regulation_type, impacts, criticality, deadline) -> dict:
    """
    Générer recommandations :
    - Actions prioritaires
    - Stratégies d'atténuation
    - Timeline
    - Estimation effort
    """
```

### 5. `prompts/agent_2_prompt.py`
```python
AGENT_2_PROMPT = PromptTemplate.from_template("""
Tu es l'Agent 2, expert en analyse d'impact réglementaire.

Mission : Analyser l'impact de {document_title} pour {company_name}

Profil entreprise :
- Secteur : {sector}
- Codes NC : {nc_codes}
- Fournisseurs : {suppliers_count}

Document :
{document_content}

Instructions :
1. Analyser l'impact sur les fournisseurs
2. Identifier les produits concernés
3. Estimer l'impact financier
4. Calculer le score (0-1)
5. Déterminer la criticité
6. Proposer un plan d'action

Format de sortie : JSON structuré
...
""")
```

## 📦 Dépendances

### Données externes
- `data/suppliers/*.json` : Liste des fournisseurs
- `data/products/*.json` : Catalogue produits avec codes NC
- `data/customs_flows/*.json` : Flux douaniers

### Modèles SQLAlchemy
- `ImpactAssessment` (déjà créé dans `src/storage/models.py`)
- `Alert` (mis à jour pour pointer vers ImpactAssessment)

### Repositories
- `ImpactAssessmentRepository` (déjà créé dans `src/storage/repositories.py`)
- `AnalysisRepository.find_by_validation_status("approved")`
- `AlertRepository`

## 🎯 Critères de scoring

### Score total (0-1)

Formule suggérée :
```
score = (
    0.3 * supplier_impact_ratio +    # % fournisseurs impactés
    0.3 * product_impact_ratio +      # % produits impactés
    0.2 * financial_impact_score +    # Impact financier normalisé
    0.2 * urgency_score               # Urgence (délai)
)
```

### Criticité

| Score | Criticité | Action |
|-------|-----------|--------|
| >= 0.8 | CRITICAL | Alerte immédiate, plan d'urgence |
| >= 0.6 | HIGH | Alerte prioritaire, plan sous 1 semaine |
| >= 0.4 | MEDIUM | Alerte standard, plan sous 1 mois |
| < 0.4 | LOW | Information, veille continue |

## 🧪 Tests

TODO: Créer `tests/test_agent_2.py` avec :
- Test `calculate_score()`
- Test `analyze_impact()` avec fournisseurs fictifs
- Test `generate_recommendations()`
- Test création `ImpactAssessment`
- Test création `Alert`

## 📝 Exemple d'output

### ImpactAssessment
```python
{
    "id": "impact_123",
    "analysis_id": "analysis_456",
    "total_score": 0.85,
    "criticality": "CRITICAL",
    "affected_suppliers": [
        {"id": "supplier_1", "name": "Acme Steel", "impact_level": "HIGH"}
    ],
    "affected_products": [
        {"id": "prod_1", "name": "Steel Rod", "nc_code": "7206", "impact": "Taxe CBAM"}
    ],
    "financial_impact": {
        "estimated_cost": 150000,
        "currency": "EUR",
        "timeframe": "12 months"
    },
    "recommended_actions": [
        {
            "priority": 1,
            "action": "Contacter fournisseurs pour données CBAM",
            "deadline": "2026-02-01",
            "resources": "Supply Chain Manager"
        }
    ],
    "confidence_level": "HIGH"
}
```

### Alert
```python
{
    "id": "alert_789",
    "impact_assessment_id": "impact_123",
    "alert_type": "email",
    "alert_data": {
        "subject": "[CRITICAL] CBAM : 5 fournisseurs impactés",
        "body": "...",
        "criticality": "CRITICAL",
        "score": 0.85
    },
    "recipients": ["compliance@example.com", "supply@example.com"],
    "status": "pending"
}
```

## 🚀 Démarrage

1. **Lire la doc workflow** : `/docs/README.md`
2. **Étudier les modèles** : `src/storage/models.py` (ImpactAssessment)
3. **Implémenter les outils** : Commencer par `scorer.py` (simple)
4. **Définir le prompt** : `prompts/agent_2_prompt.py`
5. **Créer l'agent** : `agent.py` avec LangChain
6. **Tester** : `python -m pytest tests/test_agent_2.py`

## 📞 Questions ?

- **Dev 3** (vous) : Architecture BDD, repositories, workflow
- **Dev 1/2** : Agent 1A, collecte de documents
- **Lead** : Décisions architecture, validation technique
