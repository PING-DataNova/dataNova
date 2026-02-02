# Agent 1A - Collecteur de Documents Réglementaires

## Vue d'ensemble

L'Agent 1A est responsable de la **collecte** des documents réglementaires européens depuis EUR-Lex. Conformément au CDC (Cahier des Charges), il collecte les documents de manière "neutre", sans filtrage par nom de réglementation.

**Rôle de l'Agent 1A :** Ingestion / Normalisation  
**Rôle de l'Agent 1B :** Pertinence / Classification

## Architecture

```
Profil Entreprise (JSON)
         │
         ▼
┌─────────────────────────┐
│   keyword_extractor.py  │  Extrait les mots-clés
│   - Codes NC/HS         │  (sans noms de réglementations)
│   - Matières premières  │
│   - Secteurs            │
│   - Pays fournisseurs   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│      scraper.py         │  Recherche EUR-Lex
│   - API SOAP EUR-Lex    │  avec les mots-clés
│   - Text~keyword        │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│      agent.py           │  Pipeline complet
│   - Téléchargement PDF  │
│   - Extraction contenu  │
│   - Sauvegarde BDD      │
└───────────┬─────────────┘
            │
            ▼
    Documents collectés
    (regulation_type = "TO_CLASSIFY")
            │
            ▼
┌─────────────────────────┐
│       Agent 1B          │  Détermine la pertinence
│   - Analyse contenu     │  et classifie les docs
│   - Classification      │
└─────────────────────────┘
```

## Modes de fonctionnement

### 1. Mode Profil Entreprise (Recommandé - CDC Conforme)

```python
from agent_1a.agent import run_agent_1a_from_profile

result = await run_agent_1a_from_profile(
    profile_path="data/company_profiles/Hutchinson_SA.json",  # Optionnel
    max_documents_per_keyword=20,
    max_total_documents=100,
    priority_threshold=2,  # 1=codes NC, 2=+matières, 3=+secteurs/pays
    save_to_db=True
)
```

**Fonctionnement :**
1. Lit le profil JSON de l'entreprise
2. Extrait automatiquement les mots-clés pertinents
3. Recherche sur EUR-Lex avec ces mots-clés
4. Télécharge et extrait le contenu des PDF
5. Sauvegarde en BDD avec `regulation_type="TO_CLASSIFY"`

### 2. Mode Legacy (par mot-clé de réglementation)

```python
from agent_1a.agent import run_agent_1a

result = await run_agent_1a(
    keyword="CBAM",  # Nom de la réglementation
    max_results=10
)
```

⚠️ Ce mode n'est **pas conforme** au CDC car il filtre par nom de réglementation.

## Extraction des mots-clés

Le module `keyword_extractor.py` extrait les données suivantes du profil entreprise :

| Catégorie | Source dans le JSON | Exemple | Priorité |
|-----------|---------------------|---------|----------|
| Codes NC | `nc_codes.imports[].code` | 4001, 7208 | 1 (haute) |
| Codes HS | `supply_chain.*.suppliers[].nc_code` | 400121 | 1 |
| Matières | `supply_chain.natural_rubber`, `synthetic_rubber` | rubber, steel | 2 |
| Produits | `products[]`, `business_units[].main_products` | seal, hose | 2 |
| Secteurs | `company.industry.segments` | automotive, aerospace | 3 |
| Pays | `supply_chain.*.suppliers[].country` | Thailand, China | 3 |

### Priorités

- **Priorité 1** : Codes NC/HS (très précis, ~200-600 docs chacun)
- **Priorité 2** : Matières et produits (~300-2000 docs)
- **Priorité 3** : Secteurs et pays (~1000-10000 docs)
- **Priorité 4** : Termes commerciaux génériques (>10000 docs)

## Configuration

### Variables d'environnement (.env)

```env
EURLEX_API_USERNAME=votre_username
EURLEX_API_PASSWORD=votre_password
EURLEX_SOAP_URL=https://eur-lex.europa.eu/EURLexWebService
```

### Fichiers de configuration

- `data/company_profiles/Hutchinson_SA.json` : Profil entreprise
- `config/eurlex_domains.json` : Configuration des domaines EUR-Lex (optionnel)

## Tests

```bash
# Test rapide (extraction + recherche)
python test_agent_1a_profile.py

# Test complet (avec téléchargement)
python test_agent_1a_profile.py --full
```

## Structure des fichiers

```
src/agent_1a/
├── __init__.py
├── agent.py                 # Pipeline principal
├── tools/
│   ├── keyword_extractor.py # Extraction mots-clés du profil
│   ├── scraper.py          # API EUR-Lex
│   ├── document_fetcher.py # Téléchargement PDF
│   └── pdf_extractor.py    # Extraction contenu PDF
```

## Résultat type

```json
{
  "status": "success",
  "mode": "company_profile",
  "company": {
    "name": "HUTCHINSON",
    "id": "HUT-001"
  },
  "keywords": {
    "extracted_total": 68,
    "used_for_search": 15,
    "priority_threshold": 2
  },
  "documents": {
    "unique_found": 45,
    "downloaded": 42,
    "extracted": 40,
    "saved": 40
  }
}
```

## Différence avec l'ancienne approche

| Aspect | Ancienne approche | Nouvelle approche (CDC) |
|--------|-------------------|-------------------------|
| Mots-clés | Noms de réglementations (CBAM, REACH) | Données entreprise (codes NC, matières) |
| Filtrage | Agent 1A filtre par réglementation | Agent 1A collecte, Agent 1B filtre |
| Classification | Connue à l'avance | Déterminée par Agent 1B |
| Conformité CDC | ❌ | ✅ |

## Prochaines étapes

1. L'Agent 1B analyse les documents collectés
2. L'Agent 1B détermine quelles réglementations (CBAM, REACH, EUDR...) s'appliquent
3. L'Agent 1B classifie chaque document
