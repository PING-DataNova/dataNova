# Agent 1A - Pipeline vs ReAct

## 📌 Version Recommandée : Pipeline (Option B)

Le **pipeline** est maintenant la version par défaut de l'Agent 1A.

### ✅ Avantages

- **3-5x plus rapide** que ReAct
- **Aucun risque de rate limit 429** (tokens minimaux)
- **Contrôle total** du workflow
- **Plus simple** à déboguer
- **LLM appelé uniquement** pour les résumés (1 appel/document)

### 🚀 Utilisation

```python
from src.agent_1a import run_agent_1a_simple_pipeline

# Rechercher et traiter des documents EUR-Lex
result = await run_agent_1a_simple_pipeline(
    keyword="CBAM",
    max_documents=10
)

# Résultat
{
    "documents": [
        {
            "title": "...",
            "celex_number": "32023R0956",
            "document_type": "REGULATION",
            "publication_date": "2023-05-10",
            "url": "...",
            "pdf_url": "...",
            "file_path": "data/documents/document_xxx.pdf",
            "text_path": "data/documents/document_xxx.txt",
            "text_chars": 177690,
            "nc_codes": ["7208", "7606", ...],
            "summary": "...",
            "status": "completed"
        }
    ],
    "stats": {
        "total": 2,
        "successful": 2,
        "errors": 0
    }
}
```

### 🔧 Workflow Interne

1. **Recherche EUR-Lex** : `search_eurlex(keyword)`
2. **Pour chaque document** :
   - Téléchargement PDF : `fetch_document(pdf_url)`
   - Extraction contenu : `extract_pdf(file_path)` → texte complet sauvegardé sur disque
   - Génération résumé : `generate_summary(text_preview)` → **seul appel LLM**
3. **Retour** : documents enrichis avec métadonnées + résumés

### 📂 Fichiers Générés

- `data/documents/document_*.pdf` : PDFs téléchargés
- `data/documents/document_*.txt` : Texte extrait complet (pour analyse ultérieure)

---

## 🔄 Version Alternative : ReAct (Option A)

Utilise **LangGraph** avec pattern ReAct pour laisser l'agent décider du workflow.

### ⚠️ Limitations

- Plus lent (3-5x)
- Risque de rate limits avec gros documents
- Plus de tokens consommés (contexte réinjecté)

### 💡 Quand l'utiliser ?

- Workflow **non-déterministe** (ordre variable)
- Besoin de **reasoning complexe**
- L'agent doit **décider** du workflow

### 🚀 Utilisation

```python
from src.agent_1a import run_agent_1a_simple  # ReAct version

result = await run_agent_1a_simple(
    keyword="CBAM",
    max_documents=3
)
```

---

## 🎯 Comparaison

| Critère | Pipeline (B) | ReAct (A) |
|---------|--------------|-----------|
| **Vitesse** | ⚡ 8-10s pour 2 docs | 🐢 30-40s pour 2 docs |
| **Rate limits** | ✅ Aucun risque | ⚠️ Risque avec >3 docs |
| **Tokens** | ✅ Minimum (résumés only) | ❌ Élevé (contexte réinjecté) |
| **Contrôle** | ✅ Total | ⚠️ Délégué à l'agent |
| **Debugging** | ✅ Simple | ❌ Complexe |
| **Workflow** | ✅ Déterministe | ⚠️ Non-déterministe |

---

## 📊 Optimisations Appliquées

### PDF Extractor
- ✅ Sauvegarde texte complet sur disque
- ✅ Renvoie seulement preview (8k chars) à l'agent
- ✅ Regex NC codes amélioré (moins de faux positifs)

### Summarizer
- ✅ Instance LLM globale (lazy init)
- ✅ Preview limité à 8k chars
- ✅ Prompt ultra-court (~150 chars)

### Agent (ReAct seulement)
- ✅ `max_tokens` réduit à 900
- ✅ `recursion_limit` dynamique : `10 + 5*max_documents`

---

## 🧪 Tests

```bash
# Pipeline (recommandé)
uv run python demo_agent_1a.py

# Pipeline (version alternative)
uv run python demo_agent_pipeline.py
```

---

## 📝 Notes Techniques

### Pourquoi le Pipeline est meilleur ?

Ton workflow Agent 1A est **déterministe** :
```
search → fetch → extract → summarize
```

ReAct est fait pour des tâches où l'**ordre n'est pas sûr**. Ici, il ajoute juste :
- Overhead (planning, reasoning)
- Tokens inutiles (réinjection contexte)
- Latence (appels LLM supplémentaires)

Le pipeline supprime tout ça → **3-5x plus rapide, aucun rate limit**.

### Consommation Tokens (2 documents)

| Étape | Pipeline | ReAct |
|-------|----------|-------|
| Planning | 0 | ~2k tokens |
| Search | 0 | ~1k tokens |
| Fetch | 0 | ~500 tokens |
| Extract | 0 | ~3k tokens (texte complet réinjecté) |
| Summarize | ~3k tokens | ~5k tokens |
| **Total** | **~3k** | **~11.5k** |

→ Pipeline = **74% moins de tokens** ! 🎯
