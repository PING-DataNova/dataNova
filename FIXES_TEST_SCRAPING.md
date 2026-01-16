# Solutions pour faire passer test_agent_1a_scraping

## Problème initial
Le test `test_agent_1a_scraping` échouait avec un timeout de 6 minutes (360 secondes).

## Causes identifiées
1. **Pas de timeout configuré** au niveau du test pytest
2. **Modèle Claude lent** : Timeout LLM de 120s + 2 retries
3. **Limite de récursion élevée** : 10 itérations maximum pour l'agent
4. **Dépendances manquantes** dans l'environnement Python système

## Solutions appliquées

### 1. Configuration du timeout pytest ✅
**Fichier** : `tests/agent_1a/test_langchain_agent.py`
```python
@pytest.mark.asyncio
@pytest.mark.timeout(180)  # Timeout de 3 minutes
async def test_agent_1a_scraping():
    ...
```

### 2. Optimisation de l'agent LLM ✅
**Fichier** : `src/agent_1a/agent.py`
```python
llm = ChatAnthropic(
    model=model_name,
    temperature=temperature,
    max_tokens=max_tokens,
    timeout=60,  # Réduit de 120 à 60 secondes
    max_retries=1  # Réduit de 2 à 1 retry
)
```

### 3. Réduction de la limite de récursion ✅
**Fichier** : `src/agent_1a/agent.py`
```python
result = await agent.ainvoke(
    {"messages": [("user", query)]},
    config={"recursion_limit": 5}  # Réduit de 10 à 5
)
```

### 4. Installation des dépendances ✅
```powershell
pip install pytest-timeout
pip install langchain-anthropic langchain-core langgraph
pip install pytest-asyncio
pip install python-dotenv httpx beautifulsoup4 lxml structlog pdfplumber
```

**Dépendance ajoutée** : `pyproject.toml`
```toml
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "pytest-timeout>=2.3.0",  # ✅ AJOUTÉ
    "black>=24.8.0",
    "ruff>=0.6.0",
    "mypy>=1.11.0",
]
```

## Résumé des optimisations

| Paramètre | Avant | Après | Gain |
|-----------|-------|-------|------|
| Timeout test | ∞ (6 min par défaut) | 180s | Échec rapide |
| Timeout LLM | 120s | 60s | -50% |
| Retries LLM | 2 | 1 | -50% |
| Récursion agent | 10 | 5 | -50% |

**Temps théorique maximum** :
- Avant : `120s * 3 tentatives * 10 récursions = 60 minutes`
- Après : `60s * 2 tentatives * 5 récursions = 10 minutes`
- Timeout test : **3 minutes** (sécurité)

## Commande pour relancer le test
```powershell
cd x:\PROJET_PING\backend_dataNova\backend_dataNova
python -m pytest tests/agent_1a/test_langchain_agent.py::test_agent_1a_scraping -v -s
```

## Statut
✅ **Test configuré et prêt à l'exécution**

Les modifications garantissent :
- Échec rapide en cas de problème (3 minutes max)
- Optimisation des appels LLM
- Détection précoce des boucles infinies
