# Agent 1B - Analyse de Pertinence Réglementaire 🤖

## 📋 Vue d'ensemble

L'Agent 1B est un analyseur intelligent qui détermine la pertinence des documents réglementaires pour une entreprise spécifique. Il utilise une approche **triangulée** combinant analyse lexicale, technique et sémantique pour produire un verdict fiable.

## 🎯 Mission

Répondre à 3 questions clés :

1. **Est-ce pertinent ?** → Score de 0 à 100%
2. **Quelle urgence ?** → Criticité (CRITICAL/HIGH/MEDIUM/LOW)
3. **Qui est impacté ?** → Processus/départements concernés

## 🔬 Méthodologie d'Analyse

### Triple Filtrage Pondéré

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT 1B PIPELINE                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┴────────────────────┐
        │                                        │
        ↓                                        ↓
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   NIVEAU 1       │  │   NIVEAU 2       │  │   NIVEAU 3       │
│   Mots-Clés      │  │   Codes NC       │  │   LLM Sémantique │
│   (30%)          │  │   (30%)          │  │   (40%)          │
└──────────────────┘  └──────────────────┘  └──────────────────┘
        │                     │                      │
        └──────────┬──────────┴──────────┬───────────┘
                   ↓                     ↓
            ┌──────────────┐      ┌──────────────┐
            │ Score Final  │      │  Criticité   │
            │   56.1%      │      │   MEDIUM     │
            └──────────────┘      └──────────────┘
```

### 1️⃣ Niveau 1 : Analyse par Mots-Clés (30%)

**Objectif** : Scanner le document pour trouver les mots-clés métier de l'entreprise.

**Logique** :
- Liste de mots-clés depuis le profil entreprise (ex: "aluminium", "caoutchouc", "CBAM", "douane")
- Recherche case-insensitive
- Extraction du contexte autour de chaque mot-clé trouvé
- Score = (Mots-clés trouvés / Total mots-clés) × 1.5 (bonus diversité)

**Exemple** :
```
Profil: 50 mots-clés
Document: 12 mots-clés trouvés
→ Densité: 24%
→ Score Niveau 1: 34.3%
```

### 2️⃣ Niveau 2 : Analyse par Codes NC (30%)

**Objectif** : Détecter les codes NC/SH (nomenclature douanière) du profil dans le document.

**Logique** :
- Extraction de tous les codes NC du document (regex: `\b\d{4}(\.\d{2}){0,2}\b`)
- Correspondance exacte (ex: `4001.22`)
- Correspondance partielle (ex: `4001` vs `4001.22`)
- Bonus pour codes critiques
- Score basé sur le ratio de matchs

**Exemple** :
```
Profil: Codes 4001.22, 7606, 4016
Document: Mention de "4001" et "7606.10"
→ 1 exact match + 1 partial match
→ Score Niveau 2: 0.0% (aucun code trouvé dans cet exemple)
```

### 3️⃣ Niveau 3 : Analyse Sémantique LLM (40%)

**Objectif** : Comprendre le **contexte** et l'**applicabilité** réelle.

**Pourquoi c'est crucial ?**
- Un document peut mentionner "aluminium" mais dire "L'aluminium est EXCLU" → Niveau 1 dirait pertinent, Niveau 3 corrige
- Un document peut ne pas avoir de code NC mais parler de "produits en caoutchouc importés de Chine" → Niveau 3 détecte la pertinence

**Prompt LLM** :
```
Tu es un expert en analyse réglementaire. 

ENTREPRISE: Hutchinson (caoutchouc, aéro, auto)
CODES NC: 4001.22, 7606...
PAYS: France, Pologne, USA, Inde...

DOCUMENT: [Texte du règlement]

ANALYSE:
1. Ce document s'applique-t-il à cette entreprise ?
2. Quels produits/processus sont concernés ?
3. Quelles obligations sont imposées ?
4. Score de pertinence (0-1)
```

**Output Pydantic** :
```python
SemanticAnalysisResult(
    score=0.95,
    is_applicable=True,
    regulation_summary="Le CBAM impose une taxe carbone...",
    impact_explanation="Hutchinson devra déclarer les émissions...",
    obligations_identified=["Déclaration trimestrielle", "Achat certificats"],
    products_inferred=["Caoutchouc synthétique", "Aluminium"],
    confidence_level=0.85
)
```

## 🧮 Calcul du Score Final

```python
Score Final = (
    Score_Niveau1 × 0.30 +
    Score_Niveau2 × 0.30 +
    Score_Niveau3 × 0.40
)
```

**Exemple** :
```
Niveau 1 (mots-clés):  34.3% × 0.30 = 10.3%
Niveau 2 (codes NC):    0.0% × 0.30 =  0.0%
Niveau 3 (sémantique): 95.0% × 0.40 = 38.0%
──────────────────────────────────────────
Score Final:                     = 48.3%
```

## 📊 Détermination de la Criticité

Seuils par défaut :
- **CRITICAL** : ≥ 80% (Action immédiate requise)
- **HIGH** : ≥ 60% (Attention prioritaire)
- **MEDIUM** : ≥ 40% (Suivi recommandé)
- **LOW** : ≥ 20% (Information)
- **NOT_RELEVANT** : < 20%

**Facteurs de boost** :
- Présence de codes NC critiques → Upgrade de HIGH à CRITICAL
- Applicabilité élevée selon LLM (>70%) → Upgrade de MEDIUM à HIGH

## 🎯 Identification des Processus Impactés

L'agent identifie automatiquement les départements/processus concernés :

### Mapping par type de réglementation

| Réglementation | Processus Impactés |
|----------------|-------------------|
| **CBAM** | Customs & Trade, ESG Compliance, Procurement |
| **EUDR** | Supply Chain, ESG Compliance, Procurement |
| **CSRD** | ESG Compliance, Finance |

### Détection contextuelle

En analysant les **obligations identifiées** par le LLM :
- "douane" → Customs & Trade
- "déclaration" → ESG Compliance
- "fournisseur" → Supply Chain
- "production" → Production
- "qualité" → Quality

## 💾 Modèles de Données (Pydantic)

Toutes les données sont validées avec Pydantic pour garantir la fiabilité :

```python
# Résultat final complet
DocumentAnalysis(
    document_id="abc123...",
    company_profile_id="HUT-001",
    
    # Les 3 niveaux d'analyse
    keyword_analysis=KeywordAnalysisResult(...),
    nc_code_analysis=NCCodeAnalysisResult(...),
    semantic_analysis=SemanticAnalysisResult(...),
    
    # Score et criticité
    relevance_score=RelevanceScore(
        final_score=0.561,
        criticality=Criticality.MEDIUM
    ),
    
    # Impact
    impacted_processes=[ImpactedProcess.CUSTOMS_TRADE, ...],
    
    # Explication
    executive_summary="Le règlement CBAM...",
    law_explanation="Ce texte établit...",
    impact_justification="Hutchinson est concernée car...",
    recommended_actions=["Action 1", "Action 2"]
)
```

## 🚀 Utilisation

### Analyser un document depuis la BDD

```python
from src.agent_1b import run_agent_1b_on_document

# Analyser un document par son ID
analysis = run_agent_1b_on_document(
    document_id="abc123-...",
    company_profile_path="data/company_profiles/Hutchinson_SA.json"
)

print(f"Score: {analysis.relevance_score.final_score * 100:.1f}%")
print(f"Criticité: {analysis.relevance_score.criticality.value}")
print(f"Pertinent: {analysis.is_relevant}")
```

### Analyser avec un profil custom

```python
from src.agent_1b import Agent1B

# Créer l'agent avec un profil
agent = Agent1B(company_profile={
    "company_name": "HUTCHINSON",
    "keywords": ["caoutchouc", "aluminium", "CBAM"],
    "nc_codes": ["4001.22", "7606"],
    "products": ["Joints d'étanchéité", "Flexibles"],
    ...
})

# Analyser un document
analysis = agent.analyze_document(
    document_id="abc123",
    document_content="Texte du règlement...",
    document_title="Règlement CBAM 2023/956",
    regulation_type="CBAM"
)
```

### Script de démonstration

```bash
# Analyser tous les documents CBAM de la BDD
uv run python demo_agent_1b.py
```

## 📁 Structure du Code

```
src/agent_1b/
├── __init__.py                  # Exports principaux
├── agent.py                     # Agent 1B orchestrateur
├── models.py                    # Modèles Pydantic
└── tools/
    ├── keyword_filter.py        # Niveau 1: Mots-clés
    ├── nc_code_filter.py        # Niveau 2: Codes NC
    ├── semantic_analyzer.py     # Niveau 3: LLM
    └── relevance_scorer.py      # Scoring final
```

## 📊 Exemple de Résultat

```
================================================================================
📊 RÉSULTAT DE L'ANALYSE AGENT 1B
================================================================================

🏢 Entreprise: HUT-001
📄 Document: 3c88a0a3...
⏰ Analysé le: 2026-01-25 16:45:12

--------------------------------------------------------------------------------
📈 SCORES DÉTAILLÉS
--------------------------------------------------------------------------------

1️⃣  Score Mots-Clés (30%): 34.3%
   → 12 mots-clés trouvés sur 50
   → Trouvés: caoutchouc, CBAM, émissions, carbone, importations

2️⃣  Score Codes NC (30%): 0.0%
   → 0 correspondances exactes
   → 0 correspondances partielles

3️⃣  Score Sémantique LLM (40%): 95.0%
   → Applicable: OUI ✅
   → Confiance: 85%

--------------------------------------------------------------------------------
🎯 SCORE FINAL
--------------------------------------------------------------------------------

🟡 Criticité: MEDIUM
📊 Score Final: 56.1%
✓ Pertinent: OUI

--------------------------------------------------------------------------------
🎯 PROCESSUS IMPACTÉS
--------------------------------------------------------------------------------

Processus principal: Customs & Trade
Autres processus: ESG & Compliance, Procurement

--------------------------------------------------------------------------------
📜 CE QUE DIT LA LOI
--------------------------------------------------------------------------------

Le règlement CBAM (Carbon Border Adjustment Mechanism) est un mécanisme 
d'ajustement carbone aux frontières qui s'appliquera aux importations de 
produits à forte intensité carbone...

--------------------------------------------------------------------------------
⚠️  POURQUOI ÇA NOUS IMPACTE
--------------------------------------------------------------------------------

Hutchinson sera directement impactée car l'entreprise importe des produits en 
caoutchouc et polymères (codes NC 4001.22, 4016) provenant de pays tiers 
(Chine, Malaisie, Thaïlande, Mexique). Ces importations sont soumises à 
l'obligation de déclaration des émissions carbone incorporées...

--------------------------------------------------------------------------------
💡 ACTIONS RECOMMANDÉES
--------------------------------------------------------------------------------

1. Obligation de déclarer les émissions carbone incorporées dans les 
   importations de joints, durites et composants en caoutchouc

2. Coûts additionnels liés à l'achat de certificats CBAM si les fournisseurs 
   ne peuvent pas prouver un prix dans leur pays d'origine

3. Nécessité de mettre en place un système de traçabilité et de collecte des 
   données d'émissions carbone auprès de la chaîne d'approvisionnement asiatique

4. Convoquer une réunion avec les parties prenantes

5. Planifier une analyse d'impact détaillée
```

## 🔧 Configuration

### Pondération des scores

```python
from src.agent_1b.tools.relevance_scorer import RelevanceScorer

# Scorer personnalisé
scorer = RelevanceScorer(
    keyword_weight=0.25,      # 25% au lieu de 30%
    nc_code_weight=0.35,      # 35% au lieu de 30%
    semantic_weight=0.40,     # 40% (inchangé)
    thresholds={
        "critical": 0.85,     # Seuil plus élevé
        "high": 0.65,
        "medium": 0.45,
        "low": 0.25
    }
)
```

### Modèle LLM

```python
from src.agent_1b.tools.semantic_analyzer import SemanticAnalyzer

# Utiliser un modèle différent
analyzer = SemanticAnalyzer(
    model_name="claude-3-opus-20240229",  # Modèle plus puissant
    temperature=0.0                        # Déterministe
)
```

## 📝 Tests

```bash
# Tests unitaires (TODO)
uv run pytest tests/agent_1b/

# Test d'intégration
uv run python demo_agent_1b.py
```

## 🔗 Intégration avec Agent 1A

```python
# Pipeline complet Agent 1A → Agent 1B
from src.agent_1a.agent import run_agent_1a_combined
from src.agent_1b import run_agent_1b_on_document
from src.storage.database import get_session
from src.storage.models import Document

# 1. Collecter les documents (Agent 1A)
result_1a = await run_agent_1a_combined(keyword="CBAM", max_eurlex_documents=10)

# 2. Analyser chaque document pertinent (Agent 1B)
session = get_session()
documents = session.query(Document).filter(
    Document.workflow_status == "raw"
).all()

for doc in documents:
    analysis = run_agent_1b_on_document(doc.id)
    
    if analysis.is_relevant:
        print(f"✅ Pertinent: {doc.title}")
        print(f"   Score: {analysis.relevance_score.final_score:.2f}")
        # → Générer alerte, notifier, etc.
```

## 🎯 Roadmap

- [ ] Sauvegarder les analyses en base de données
- [ ] Générer des alertes emails automatiques
- [ ] Dashboard de visualisation des analyses
- [ ] Support multi-langues (documents EN/FR)
- [ ] Cache des analyses LLM pour éviter re-calcul
- [ ] API REST pour intégration externe

## 📚 Références

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [LangChain Documentation](https://python.langchain.com/)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [EUR-Lex CBAM](https://eur-lex.europa.eu/EN/legal-content/summary/carbon-border-adjustment-mechanism-cbam.html)
