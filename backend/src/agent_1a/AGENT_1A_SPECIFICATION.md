# 🔍 Agent 1A - Spécification Complète

## 📋 Vue d'ensemble

**L'Agent 1A est l'agent de COLLECTE de données.** Il ne fait PAS d'analyse, PAS de scoring, PAS de recommandations. Son rôle est uniquement de récupérer les données brutes depuis les sources externes.

---

## 🎯 Rôle de l'Agent 1A

| ✅ Ce que fait l'Agent 1A | ❌ Ce que ne fait PAS l'Agent 1A |
|---------------------------|----------------------------------|
| Collecter les réglementations EUR-Lex | Calculer des scores de risque |
| Collecter les alertes météo | Analyser la pertinence |
| Sauvegarder les données brutes | Générer des recommandations |
| Géocoder les localisations | Filtrer les documents |

---

## 🔗 Position dans le Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                        AGENT 1A                             │
│                    🔍 COLLECTE                              │
├─────────────────────────────────────────────────────────────┤
│  • Recherche EUR-Lex (réglementations européennes)          │
│  • Recherche Open-Meteo (prévisions météo)                  │
│  • Sauvegarde dans : DOCUMENTS, WEATHER_ALERTS              │
│  • Statut de sortie : "collected"                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                        AGENT 1B                             │
│                📊 ANALYSE DE PERTINENCE                     │
├─────────────────────────────────────────────────────────────┤
│  • Évalue si chaque document est pertinent                  │
│  • Score de pertinence (confidence 0-1)                     │
│  • Sauvegarde dans : PERTINENCE_CHECKS                      │
│  • Statut de sortie : "pertinence_analyzed"                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                        AGENT 2                              │
│            ⚠️ ANALYSE DE RISQUES + RECOMMANDATIONS          │
├─────────────────────────────────────────────────────────────┤
│  • Analyse approfondie des risques                          │
│  • Calcul du score de risque (impact_score)                 │
│  • Génération des recommandations                           │
│  • Sauvegarde dans : RISK_ANALYSES                          │
│  • Statut de sortie : "completed"                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Tables de la Base de Données

### Tables remplies par l'Agent 1A

| Table | Description | Champs principaux |
|-------|-------------|-------------------|
| `DOCUMENTS` | Réglementations collectées | celex_id, title, content, source_type, source_url |
| `WEATHER_ALERTS` | Alertes météo collectées | site_id, alert_type, severity, date, value |

### Tables remplies par les autres agents

| Table | Agent | Description |
|-------|-------|-------------|
| `PERTINENCE_CHECKS` | Agent 1B | Analyse de pertinence des documents |
| `RISK_ANALYSES` | Agent 2 | Analyse de risques + recommandations |
| `ALERTS` | Agent 2 | Alertes générées pour l'utilisateur |

---

## 🚀 Les Deux Scénarios d'Utilisation

### Scénario 1 : Collecte Automatique (Scheduled)

**Déclencheur :** Scheduler (cron quotidien/hebdomadaire)

**Flux :**
```
Scheduler
    │
    ▼
Agent 1A (collecte pour TOUS les fournisseurs/sites configurés)
    │
    ├── EUR-Lex : recherche par mots-clés des profils entreprise
    │   └── Sauvegarde → table DOCUMENTS
    │
    └── Open-Meteo : météo pour tous les sites Hutchinson
        └── Sauvegarde → table WEATHER_ALERTS
    │
    ▼
Agent 1B (analyse de pertinence automatique)
    │
    ▼
Agent 2 (analyse de risques si pertinent)
    │
    ▼
Notifications (si alertes critiques)
```

**Configuration :**
- Sites : `config/sites_locations.json` (sites Hutchinson)
- Mots-clés : extraits des profils entreprise (`data/company_profiles/`)
- Fréquence : configurable dans le scheduler

**Fonction principale :** `run_agent_1a()` dans `agent.py`

---

### Scénario 2 : Analyse Ponctuelle Fournisseur (UI)

**Déclencheur :** Utilisateur via l'interface web

**Flux :**
```
Utilisateur (saisit les infos fournisseur dans l'UI)
    │
    ▼
POST /api/supplier/analyze
    │
    ├── supplier_name: "Thai Rubber Co."
    ├── country: "Thailand"
    ├── city: "Bangkok"
    ├── materials: ["Caoutchouc naturel", "Latex"]
    ├── nc_codes: ["4001", "400121"]
    └── criticality: "Important"
    │
    ▼
Agent 1A (collecte pour CE fournisseur spécifique)
    │
    ├── EUR-Lex : recherche par matières + codes NC
    │   └── Données collectées (pas encore sauvées dans DOCUMENTS)
    │
    └── Open-Meteo : météo pour la localisation du fournisseur
        └── Données collectées
    │
    ▼
Sauvegarde dans SUPPLIER_ANALYSES (table temporaire)
    │
    status: "collected"
    risk_score: NULL (sera rempli par Agent 2)
    risk_level: "pending_analysis"
    │
    ▼
Réponse à l'UI avec les données collectées
    │
    ▼
(Plus tard) Agent 1B + Agent 2 pour analyse complète
```

**Fonction principale :** `run_agent_1a_for_supplier()` dans `agent.py`

---

## 📁 Structure des Fichiers

```
src/agent_1a/
├── __init__.py
├── agent.py                 # Fonctions principales
│   ├── run_agent_1a()                    # Scénario 1 : collecte automatique
│   └── run_agent_1a_for_supplier()       # Scénario 2 : analyse ponctuelle
│
├── tools/
│   ├── scraper.py           # API EUR-Lex (SOAP)
│   │   ├── search_eurlex()
│   │   └── search_eurlex_by_domain()
│   │
│   ├── weather.py           # API Open-Meteo
│   │   ├── OpenMeteoClient
│   │   ├── get_forecast()
│   │   └── detect_alerts()
│   │
│   ├── keyword_extractor.py # Extraction mots-clés
│   └── document_fetcher.py  # Téléchargement PDF
│
└── AGENT_1A_SPECIFICATION.md  # Ce fichier
```

---

## 🔧 Sources de Données

### 1. EUR-Lex (Réglementations Européennes)

| Paramètre | Valeur |
|-----------|--------|
| API | SOAP Web Service |
| URL | `https://eur-lex.europa.eu/EURLexWebService` |
| Type de recherche | Textes consolidés (Collection = CONSLEG) |
| Données collectées | CELEX ID, titre, résumé, date, URL |

**Mots-clés de recherche :**
- Matières premières (caoutchouc, latex, polymères, acier, aluminium...)
- Codes NC/douaniers (4001, 400121, 7206, 7601...)

> ⚠️ **Important** : On ne cherche PAS par nom de réglementation (CBAM, REACH, EUDR...).
> On cherche par **matière/produit** pour trouver les réglementations qui les concernent.

### 2. Open-Meteo (Météo)

| Paramètre | Valeur |
|-----------|--------|
| API | REST API (gratuite) |
| URL | `https://api.open-meteo.com/v1/forecast` |
| Prévisions | 16 jours |
| Données collectées | Température, précipitations, vent, neige |

**Seuils d'alerte :**
| Type | Seuil | Sévérité |
|------|-------|----------|
| Neige | > 10 cm | high |
| Pluie forte | > 50 mm | high |
| Chaleur extrême | > 40°C | critical |
| Froid extrême | < -15°C | high |
| Vent fort | > 80 km/h | high |

---

## 📝 Modèle SupplierAnalysis (pour Scénario 2)

Cette table stocke les résultats de collecte pour les analyses ponctuelles :

```python
class SupplierAnalysis(Base):
    __tablename__ = "supplier_analyses"
    
    # Identifiant
    id = Column(String, primary_key=True)
    
    # Informations fournisseur (saisies par l'utilisateur)
    supplier_name = Column(String)
    country = Column(String)
    city = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    nc_codes = Column(JSON)        # ["4001", "400121"]
    materials = Column(JSON)       # ["Caoutchouc", "Latex"]
    criticality = Column(String)   # Critique, Important, Standard
    annual_volume = Column(Float)
    
    # Données collectées par Agent 1A
    regulatory_risks_count = Column(Integer)
    regulatory_risks = Column(JSON)      # Documents EUR-Lex trouvés
    weather_risks_count = Column(Integer)
    weather_risks = Column(JSON)         # Alertes météo détectées
    
    # Champs pour Agent 2 (remplis plus tard)
    risk_score = Column(Float, nullable=True)      # NULL jusqu'à analyse
    risk_level = Column(String, default="pending_analysis")
    recommendations = Column(JSON, nullable=True)  # NULL jusqu'à analyse
    
    # Métadonnées
    status = Column(String)  # "collected" → "analyzed" → "completed"
    processing_time_ms = Column(Integer)
    created_at = Column(DateTime)
```

---

## 🔄 Statuts de Traitement

| Statut | Description | Agent responsable |
|--------|-------------|-------------------|
| `pending` | En attente de traitement | - |
| `collecting` | Collecte en cours | Agent 1A |
| `collected` | Collecte terminée | Agent 1A ✅ |
| `pertinence_analyzing` | Analyse pertinence en cours | Agent 1B |
| `pertinence_analyzed` | Pertinence analysée | Agent 1B |
| `risk_analyzing` | Analyse risques en cours | Agent 2 |
| `completed` | Traitement terminé | Agent 2 ✅ |
| `error` | Erreur survenue | - |

---

## 📡 Endpoints API (Scénario 2)

### POST /api/supplier/analyze

Lance une collecte pour un fournisseur spécifique.

**Request :**
```json
{
  "name": "Thai Rubber Co.",
  "country": "Thailand",
  "city": "Bangkok",
  "latitude": 13.7563,
  "longitude": 100.5018,
  "nc_codes": ["4001", "400121", "400122"],
  "materials": ["Caoutchouc naturel", "Latex"],
  "criticality": "Important",
  "annual_volume": 2500000
}
```

**Response :**
```json
{
  "analysis_id": "uuid-xxx",
  "status": "collected",
  "supplier_info": { ... },
  "collected_data": {
    "regulatory": {
      "count": 5,
      "items": [ ... ]
    },
    "weather": {
      "count": 3,
      "items": [ ... ]
    }
  },
  "processing_time_ms": 4500,
  "next_step": "Agent 1B analysis pending"
}
```

### GET /api/supplier/analyses

Liste toutes les analyses ponctuelles.

### GET /api/supplier/analyses/{id}

Récupère une analyse spécifique.

### DELETE /api/supplier/analyses/{id}

Supprime une analyse.

---

## ✅ Checklist d'Implémentation

### Scénario 1 (Collecte Automatique)
- [x] `run_agent_1a()` - Fonction principale
- [x] Intégration EUR-Lex SOAP API
- [x] Intégration Open-Meteo API
- [x] Détection des alertes météo
- [x] Sauvegarde dans `DOCUMENTS`
- [x] Sauvegarde dans `WEATHER_ALERTS`
- [ ] Intégration avec le Scheduler

### Scénario 2 (Analyse Ponctuelle)
- [x] `run_agent_1a_for_supplier()` - Fonction principale
- [x] Modèle `SupplierAnalysis`
- [x] Migration Alembic
- [x] Endpoint POST `/api/supplier/analyze`
- [x] Endpoint GET `/api/supplier/analyses`
- [x] Endpoint DELETE `/api/supplier/analyses/{id}`
- [x] Tests de validation

---

## 🧪 Comment Tester

```bash
# Test complet de l'Agent 1A
cd backend
python test_agent_1a_complete.py

# Test de l'endpoint API
python test_supplier_analysis.py
```

---

## 📌 Points Importants à Retenir

1. **Agent 1A = COLLECTE UNIQUEMENT**
   - Pas de scoring
   - Pas de recommandations
   - Pas d'analyse de pertinence

2. **Deux scénarios distincts**
   - Automatique : pour tous les sites/fournisseurs configurés
   - Ponctuel : pour un fournisseur spécifique saisi par l'utilisateur

3. **Chaîne de traitement**
   - 1A (collecte) → 1B (pertinence) → 2 (risques + recommandations)

4. **Tables de sortie**
   - Scénario 1 : `DOCUMENTS`, `WEATHER_ALERTS`
   - Scénario 2 : `SUPPLIER_ANALYSES` (puis repris par 1B et 2)
