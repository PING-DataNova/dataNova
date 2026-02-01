# Agent 1A - Documentation Complète

## 📋 Vue d'ensemble

L'**Agent 1A** est le premier agent du pipeline DataNova. Son rôle est de **collecter** les données brutes depuis des sources externes pour alimenter la base de données. Il ne fait **aucune analyse** - c'est le rôle de l'Agent 1B.

```
┌─────────────────────────────────────────────────────────────────┐
│                        AGENT 1A                                 │
│                    "Le Collecteur"                              │
├─────────────────────────────────────────────────────────────────┤
│  ENTRÉES:                                                       │
│  • Profil entreprise (Hutchinson_SA.json)                       │
│  • Configuration des sites (sites_locations.json)               │
│  • Informations fournisseur (saisie utilisateur)                │
│                                                                 │
│  SORTIES:                                                       │
│  • Documents réglementaires EUR-Lex (table: documents)          │
│  • Alertes météorologiques (table: weather_alerts)              │
│  • Analyses fournisseur (table: supplier_analyses)              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Les Deux Scénarios

### Scénario 1 : Collecte Automatique Complète
> **Fonction**: `run_agent_1a_full_collection()`  
> **Déclenchement**: Automatique (scheduler/cron) ou manuel par admin

Ce scénario effectue une collecte globale pour l'entreprise Hutchinson :

```python
from src.agent_1a.agent import run_agent_1a_full_collection

result = await run_agent_1a_full_collection(
    company_profile_path="data/company_profiles/Hutchinson_SA.json",
    sites_config_path="config/sites_locations.json",
    max_documents_per_keyword=10,
    max_keywords=0,  # 0 = tous les mots-clés
    save_to_db=True
)
```

#### Étapes du Scénario 1 :

```
┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 1: EXTRACTION DES MOTS-CLÉS                                    │
├──────────────────────────────────────────────────────────────────────┤
│ Lecture du profil Hutchinson_SA.json                                 │
│                                                                      │
│ Extraction depuis:                                                   │
│ • Secteurs: "aerospace elastomers", "automotive sealing"             │
│ • Matériaux: "natural rubber", "EPDM", "carbon black"                │
│ • Codes NC: "4001", "4002.59", "7208" (hot-rolled steel)             │
│ • Réglementations: "CBAM", "EUDR", "CSRD"                            │
│                                                                      │
│ Résultat: ~15-20 mots-clés pertinents                                │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 2: RECHERCHE EUR-LEX                                           │
├──────────────────────────────────────────────────────────────────────┤
│ Pour chaque mot-clé:                                                 │
│   → Requête SOAP vers EUR-Lex API                                    │
│   → Recherche dans CONSLEG (textes consolidés)                       │
│   → Récupération des métadonnées (CELEX, titre, URL PDF)             │
│                                                                      │
│ Dédoublonnage par CELEX ID                                           │
│                                                                      │
│ Résultat: Liste de documents uniques à télécharger                   │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 3: TÉLÉCHARGEMENT ET EXTRACTION PDF                            │
├──────────────────────────────────────────────────────────────────────┤
│ Pour chaque document:                                                │
│   → Téléchargement du PDF depuis EUR-Lex                             │
│   → Calcul du hash SHA256 (dédoublonnage)                            │
│   → Extraction du texte avec pdfplumber                              │
│   → Détection des codes NC dans le texte                             │
│   → Sauvegarde en BDD (table: documents)                             │
│                                                                      │
│ Protection: Skip les PDFs > 10 MB (évite les timeouts)               │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 4: COLLECTE MÉTÉO MULTI-SITES                                  │
├──────────────────────────────────────────────────────────────────────┤
│ Lecture de sites_locations.json:                                     │
│   • 10 usines Hutchinson (FR, PL, DE, US, MX, IN, CN, BR, ES)        │
│   • 8 fournisseurs critiques                                         │
│   • 4 hubs logistiques (ports, aéroports)                            │
│                                                                      │
│ Pour chaque site:                                                    │
│   → Requête Open-Meteo API (prévisions 16 jours)                     │
│   → Détection des alertes selon seuils:                              │
│       • Neige > 5 cm → risque routes bloquées                        │
│       • Pluie > 50 mm → risque inondations                           │
│       • Température > 40°C ou < -10°C → conditions extrêmes          │
│       • Vent > 80 km/h → fermeture ports/ponts                       │
│   → Sauvegarde des alertes (table: weather_alerts)                   │
└──────────────────────────────────────────────────────────────────────┘
```

---

### Scénario 2 : Analyse Fournisseur Manuelle
> **Fonction**: `run_agent_1a_for_supplier()`  
> **Déclenchement**: Utilisateur via l'interface web

Ce scénario permet d'analyser un fournisseur spécifique saisi par l'utilisateur :

```python
from src.agent_1a.agent import run_agent_1a_for_supplier

result = await run_agent_1a_for_supplier(
    supplier_name="Hutchinson Maroc",
    country="Maroc",
    city="Casablanca",
    latitude=33.57,
    longitude=-7.59,
    materials=["rubber", "elastomer"],
    nc_codes=["4001", "400121"],
    save_to_db=True
)
```

#### Étapes du Scénario 2 :

```
┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 1: RECHERCHE RÉGLEMENTAIRE                                     │
├──────────────────────────────────────────────────────────────────────┤
│ Mots-clés = materials + nc_codes fournis par l'utilisateur           │
│                                                                      │
│ Pour chaque mot-clé:                                                 │
│   → Recherche EUR-Lex (même process que Scénario 1)                  │
│   → Téléchargement et extraction des PDFs                            │
│   → Sauvegarde en BDD avec metadata "supplier_analysis"              │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 2: COLLECTE MÉTÉO LOCALE                                       │
├──────────────────────────────────────────────────────────────────────┤
│ Utilisation des coordonnées GPS fournies                             │
│   → Requête Open-Meteo pour ce site unique                           │
│   → Détection des alertes météo                                      │
│   → Génération des risques supply chain associés                     │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 3: SAUVEGARDE ANALYSE FOURNISSEUR                              │
├──────────────────────────────────────────────────────────────────────┤
│ Création d'un enregistrement SupplierAnalysis:                       │
│   • supplier_name, country, city, coordinates                        │
│   • regulatory_risks (JSON des risques réglementaires)               │
│   • weather_risks (JSON des alertes météo)                           │
│   • extra_metadata.document_ids (liens vers documents)               │
│   • status = "collected" (prêt pour Agent 1B)                        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Modèle de Données

### Table `documents`
```sql
-- Documents réglementaires collectés depuis EUR-Lex
documents (
    id              UUID PRIMARY KEY,
    title           TEXT,           -- "Regulation (EU) 2023/956 CBAM"
    source_url      TEXT,           -- URL du PDF EUR-Lex
    event_type      VARCHAR(50),    -- "regulation"
    event_subtype   VARCHAR(100),   -- "REGULATION", "DIRECTIVE", "DECISION"
    hash_sha256     VARCHAR(64),    -- Dédoublonnage
    content         TEXT,           -- Texte extrait du PDF
    extra_metadata  JSON,           -- {celex_id, matched_keyword, nc_codes}
    status          VARCHAR(20),    -- "new", "analyzed", "validated"
    created_at      TIMESTAMP
)
```

### Table `weather_alerts`
```sql
-- Alertes météorologiques par site
weather_alerts (
    id              UUID PRIMARY KEY,
    site_id         VARCHAR(50),    -- "FR-LEH-MFG1"
    site_name       VARCHAR(200),   -- "Hutchinson Le Havre"
    city            VARCHAR(100),
    country         VARCHAR(10),
    latitude        FLOAT,
    longitude       FLOAT,
    alert_type      VARCHAR(50),    -- "snow", "heavy_rain", "extreme_heat"
    severity        VARCHAR(20),    -- "low", "medium", "high", "critical"
    alert_date      DATE,
    value           FLOAT,          -- Valeur mesurée (mm, cm, °C)
    threshold       FLOAT,          -- Seuil dépassé
    unit            VARCHAR(20),    -- "mm", "cm", "°C", "km/h"
    description     TEXT,
    supply_chain_risk TEXT,         -- Impact supply chain
    status          VARCHAR(20),    -- "new", "acknowledged", "resolved"
    fetched_at      TIMESTAMP
)
```

### Table `supplier_analyses`
```sql
-- Analyses de fournisseurs (Scénario 2)
supplier_analyses (
    id              UUID PRIMARY KEY,
    supplier_name   VARCHAR(255),
    country         VARCHAR(100),
    city            VARCHAR(100),
    latitude        FLOAT,
    longitude       FLOAT,
    materials       JSON,           -- ["rubber", "elastomer"]
    nc_codes        JSON,           -- ["4001", "400121"]
    regulatory_risks JSON,          -- Risques réglementaires détectés
    weather_risks   JSON,           -- Alertes météo
    extra_metadata  JSON,           -- {document_ids: [...]}
    status          VARCHAR(50),    -- "collected", "analyzed", "approved"
    created_at      TIMESTAMP
)
```

---

## 🔌 Sources de Données

### EUR-Lex (Réglementations UE)
- **API**: SOAP WebService
- **URL**: `https://eur-lex.europa.eu/EURLexWebService`
- **Collection**: CONSLEG (textes consolidés)
- **Format**: PDF

### Open-Meteo (Météo)
- **API**: REST (gratuit, sans clé)
- **URL**: `https://api.open-meteo.com/v1/forecast`
- **Données**: Prévisions 16 jours
- **Paramètres**: température, précipitations, neige, vent

---

## ⚙️ Configuration

### Profil Entreprise (`data/company_profiles/Hutchinson_SA.json`)
```json
{
  "company": {
    "name": "Hutchinson SA",
    "industry": "Rubber & Elastomer Manufacturing"
  },
  "sectors": ["aerospace elastomers", "automotive sealing"],
  "materials": {
    "natural_rubber": {"nc_codes": ["4001.10", "4001.21"]},
    "synthetic_rubber": {"nc_codes": ["4002.19", "4002.59"]},
    "metals": {"nc_codes": ["7208.10", "7208.25"]}
  },
  "applicable_regulations": ["CBAM", "EUDR", "CSRD", "REACH"]
}
```

### Sites (`config/sites_locations.json`)
```json
{
  "hutchinson_facilities": [
    {
      "site_id": "FR-LEH-MFG1",
      "name": "Hutchinson Le Havre",
      "city": "Le Havre",
      "country": "FR",
      "latitude": 49.4944,
      "longitude": 0.1079,
      "type": "manufacturing",
      "criticality": "critical"
    }
  ],
  "suppliers": [...],
  "logistics_hubs": [...]
}
```

---

## 🚀 Utilisation

### Test Rapide
```bash
cd backend
python test_agent_1a_both_scenarios.py
```

### Intégration API
```python
# POST /api/v1/suppliers/analyze
{
    "supplier_name": "Fournisseur XYZ",
    "country": "Allemagne",
    "city": "Munich",
    "latitude": 48.1351,
    "longitude": 11.5820,
    "materials": ["steel", "aluminum"],
    "nc_codes": ["7208", "7601"]
}
```

### Scheduler (Collecte automatique)
```python
# Exécution quotidienne à 6h00
from src.agent_1a.agent import run_agent_1a_full_collection

async def daily_collection():
    result = await run_agent_1a_full_collection()
    logger.info(f"Collecte terminée: {result['eurlex']['documents_saved']} docs, "
                f"{result['weather']['alerts_detected']} alertes")
```

---

## 📈 Métriques Typiques

| Métrique | Scénario 1 (Full) | Scénario 2 (Fournisseur) |
|----------|-------------------|--------------------------|
| Temps d'exécution | 2-5 minutes | 10-30 secondes |
| Documents collectés | 30-100 | 5-15 |
| Sites météo | 22 | 1 |
| Alertes météo | 50-200 | 5-15 |

---

## 🔗 Liens avec les Autres Agents

```
Agent 1A (Collecte)
      │
      ▼
┌─────────────────┐
│   documents     │──────► Agent 1B (Analyse pertinence)
│ weather_alerts  │              │
│supplier_analyses│              ▼
└─────────────────┘        Agent 2 (Scoring risque)
                                 │
                                 ▼
                           Dashboard
```

L'Agent 1A ne fait **que collecter**. L'Agent 1B analyse la pertinence des documents pour Hutchinson, et l'Agent 2 calcule les scores de risque globaux.

---

## 📝 Logs

```
2026-02-01 16:51:54 [info] agent_1a_full_collection_started
2026-02-01 16:51:54 [info] step_1_completed keywords_extracted=15
2026-02-01 16:51:56 [info] eurlex_api_search_completed count=5 total_available=389
2026-02-01 16:52:02 [info] pdf_extraction_completed pages=38 nc_codes=25
2026-02-01 16:52:14 [info] openmeteo_fetch_completed days=16 site_id=FR-PAR-DC1
2026-02-01 16:52:14 [info] step_4_completed alerts_detected=92 sites_processed=10
2026-02-01 16:52:14 [info] agent_1a_full_collection_completed documents_saved=3 weather_alerts=92
```

---

## 📁 Structure des Fichiers

```
src/agent_1a/
├── __init__.py
├── agent.py                 # Fonctions principales (run_agent_1a_full_collection, run_agent_1a_for_supplier)
├── README.md                # Documentation courte
├── DOCUMENTATION.md         # Cette documentation détaillée
└── tools/
    ├── scraper.py           # API EUR-Lex (recherche SOAP)
    ├── document_fetcher.py  # Téléchargement PDFs
    ├── pdf_extractor.py     # Extraction texte + métadonnées
    └── weather.py           # API Open-Meteo (prévisions + alertes)
```
