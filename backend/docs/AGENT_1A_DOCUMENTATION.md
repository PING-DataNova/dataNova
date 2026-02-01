# Agent 1A - Documentation Technique

## 📋 Vue d'ensemble

L'**Agent 1A** est le module de **collecte de données** du système DataNova. Il est responsable de la veille réglementaire et météorologique pour la supply chain de l'entreprise Hutchinson.

---

## 🎯 Objectifs

1. **Veille réglementaire** : Collecter les documents EUR-Lex pertinents pour l'activité de l'entreprise
2. **Veille météorologique** : Surveiller les conditions météo sur les sites de production, fournisseurs et ports stratégiques

---

## 🏗️ Architecture

```
Agent 1A
├── Partie 1 : Collecte Réglementaire (EUR-Lex)
│   ├── Extraction des mots-clés depuis le profil entreprise
│   ├── Recherche via API SOAP EUR-Lex
│   ├── Téléchargement des PDFs
│   ├── Extraction du contenu (texte, tableaux, codes NC)
│   └── Sauvegarde en base de données (table: documents)
│
└── Partie 2 : Collecte Météorologique (Open-Meteo)
    ├── Chargement des sites à surveiller
    ├── Récupération des prévisions (16 jours)
    ├── Détection des alertes météo
    └── Sauvegarde en base de données (table: weather_alerts)
```

---

## 📁 Fichiers principaux

| Fichier | Description |
|---------|-------------|
| `src/agent_1a/agent.py` | Logique principale de l'agent |
| `src/agent_1a/tools/eurlex_client.py` | Client API SOAP EUR-Lex |
| `src/agent_1a/tools/pdf_extractor.py` | Extraction de contenu PDF |
| `src/agent_1a/tools/weather.py` | Client API Open-Meteo |
| `run_agent_1a_full.py` | Script d'exécution complet |
| `config/sites_locations.json` | Configuration des sites à surveiller |
| `data/company_profiles/Hutchinson_SA.json` | Profil entreprise |

---

## 🚀 Lancement

### Commande principale (Agent 1A complet)

```powershell
cd backend
python run_agent_1a_full.py
```

### Commandes alternatives

| Commande | Description |
|----------|-------------|
| `python run_agent_1a.py` | Réglementaire uniquement |
| `python test_agent_1a_weather.py` | Météo uniquement |

---

## 📊 Partie 1 : Collecte Réglementaire

### Étapes du pipeline

1. **Extraction des mots-clés** depuis le profil entreprise (Hutchinson_SA.json)
   - Codes NC (nomenclature combinée)
   - Matières premières
   - Secteurs d'activité
   - Pays d'opération

2. **Recherche EUR-Lex** via API SOAP
   - Domaines : LEGISLATION, CONSLEG, PREP_ACT
   - Maximum 10 documents par mot-clé
   - Maximum 50 documents au total

3. **Filtrage intelligent**
   - Documents publiés après 2000 (`min_publication_year=2000`)
   - Préférence pour les versions consolidées (CELEX préfixe `0`)
   - Dédoublication par numéro CELEX de base

4. **Téléchargement des PDFs**
   - Taille maximale : 30 MB
   - Stockage dans `data/documents/`

5. **Extraction du contenu**
   - Texte complet
   - Tableaux
   - Codes NC détectés
   - Métadonnées (date, type, numéro CELEX)

6. **Sauvegarde en base de données**
   - Table : `documents`
   - Status initial : `new`

### Paramètres configurables

```python
run_agent_1a_from_company_profile(
    max_documents_per_keyword=10,    # Documents max par mot-clé
    max_total_documents=50,          # Documents max au total
    priority_threshold=2,            # Seuil de priorité (codes NC + matières)
    min_publication_year=2000,       # Année minimum de publication
    prefer_consolidated=True,        # Préférer versions consolidées
    save_to_db=True                  # Sauvegarder en BDD
)
```

### Exemple de résultat

```
Documents trouvés : 57
Filtrés (< 2000) : 18
Téléchargés : 38
Extraits : 38
Sauvegardés : 38
```

---

## 🌤️ Partie 2 : Collecte Météorologique

### Sites surveillés

| Type | Nombre | Exemples |
|------|--------|----------|
| Usines Hutchinson | 9 | Paris, Le Havre, Wroclaw, Shanghai... |
| Fournisseurs critiques | 8 | Bangkok, Kuala Lumpur, Tokyo... |
| Ports stratégiques | 4 | Le Havre, Anvers, Rotterdam, Shanghai |
| Siège | 1 | Paris |

### Types d'alertes détectées

| Type | Seuils | Risque supply chain |
|------|--------|---------------------|
| `extreme_cold` | < -5°C (low) à < -20°C (critical) | Gel équipements, routes verglacées |
| `extreme_heat` | > 35°C (low) à > 45°C (critical) | Surchauffe équipements, incendies |
| `strong_wind` | > 50 km/h (low) à > 90 km/h (high) | Fermeture ports/ponts |
| `heavy_rain` | > 20mm (low) à > 100mm (critical) | Inondations, retards transport |
| `heavy_snow` | > 10cm (low) à > 50cm (critical) | Routes bloquées |
| `storm` | Code météo 95+ | Tous transports impactés |

### Paramètres configurables

```python
run_agent_1a_weather(
    sites_config_path=None,    # Chemin vers config (défaut: config/sites_locations.json)
    forecast_days=16,          # Jours de prévision (max 16)
    save_to_db=True            # Sauvegarder en BDD
)
```

### Exemple de résultat

```
Sites surveillés : 22
Prévisions collectées : 22
Alertes détectées : 181
  - Critical : 6
  - High : 16
  - Medium : 40
  - Low : 119
```

---

## 🗄️ Tables en Base de Données

### Table `documents`

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID | Identifiant unique |
| celex_number | String | Numéro CELEX EUR-Lex |
| title | String | Titre du document |
| document_type | String | Type (REGULATION, DECISION, DIRECTIVE) |
| publication_date | Date | Date de publication |
| source_url | String | URL du PDF |
| local_path | String | Chemin local du fichier |
| content_text | Text | Texte extrait |
| nc_codes | JSON | Codes NC détectés |
| status | String | Status (new, analyzed, validated) |
| created_at | DateTime | Date de création |

### Table `weather_alerts`

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID | Identifiant unique |
| site_id | String | Identifiant du site |
| site_name | String | Nom du site |
| city | String | Ville |
| country | String | Pays |
| latitude | Float | Latitude |
| longitude | Float | Longitude |
| site_type | String | Type (manufacturing, supplier, port) |
| site_criticality | String | Criticité (critical, high, medium) |
| alert_type | String | Type d'alerte |
| severity | String | Sévérité (critical, high, medium, low) |
| alert_date | Date | Date de l'alerte |
| value | Float | Valeur mesurée |
| threshold | Float | Seuil déclenché |
| unit | String | Unité |
| description | String | Description |
| supply_chain_risk | String | Risque supply chain |
| status | String | Status (new, acknowledged, resolved) |
| fetched_at | DateTime | Date de collecte |

---

## 🔗 APIs utilisées

### EUR-Lex SOAP API

- **URL** : `https://eur-lex.europa.eu/EURLexWebService`
- **Authentification** : Aucune (API publique)
- **Documentation** : [EUR-Lex Web Service](https://eur-lex.europa.eu/content/help/webservice.html)

### Open-Meteo API

- **URL** : `https://api.open-meteo.com/v1/forecast`
- **Authentification** : Aucune (API gratuite)
- **Limite** : 10,000 requêtes/jour
- **Documentation** : [Open-Meteo Docs](https://open-meteo.com/en/docs)

---

## 📈 Métriques typiques

| Métrique | Valeur typique |
|----------|----------------|
| Temps d'exécution total | ~10-15 minutes |
| Documents collectés | 30-50 |
| Alertes météo | 150-200 |
| Taille BDD | ~50-100 MB |

---

## 🔧 Dépendances

```
httpx          # Client HTTP async
pdfplumber     # Extraction PDF
structlog      # Logging structuré
sqlalchemy     # ORM base de données
pydantic       # Validation données
rich           # Affichage console
```

---

## 📝 Logs

Les logs sont structurés et incluent :
- Timestamp
- Niveau (info, warning, error)
- Étape en cours
- Métriques (compteurs, durées)

Exemple :
```
2026-02-01 04:00:59 [info] step_5_completed saved=38 errors=0
2026-02-01 04:07:51 [info] step_3_completed saved=181 errors=0
```

---

## 🚨 Gestion des erreurs

- **Timeout API** : Retry automatique (3 tentatives)
- **PDF corrompu** : Skip avec log d'erreur
- **Site météo indisponible** : Continue avec les autres sites
- **Erreur BDD** : Rollback et log détaillé

---

## 📅 Fréquence d'exécution recommandée

| Collecte | Fréquence |
|----------|-----------|
| Réglementaire | 1x par jour (matin) |
| Météorologique | 2x par jour (matin + soir) |

---

*Documentation générée le 1er février 2026*
