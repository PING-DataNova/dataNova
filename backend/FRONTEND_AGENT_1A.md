# 📱 Frontend Agent 1A - Spécification

## 🎯 Contexte

L'Agent 1A a **2 scénarios**, mais seul le **Scénario 2** nécessite un frontend :

| Scénario | Déclencheur | Frontend ? |
|----------|-------------|------------|
| **Scénario 1** : Collecte automatique | Scheduler (cron) | ❌ NON - Batch en arrière-plan |
| **Scénario 2** : Analyse fournisseur | Utilisateur | ✅ OUI - Ce document |

---

## 🖥️ Pages à Développer

```
┌─────────────────────────────────────────────────────────────┐
│                     DATANOVA - AGENT 1A                     │
│                                                             │
│    ┌─────────────────┐         ┌─────────────────┐          │
│    │  📝 FORMULAIRE  │  ────►  │  📊 RÉSULTATS   │          │
│    │   Fournisseur   │         │   de l'analyse  │          │
│    └─────────────────┘         └─────────────────┘          │
│                                                             │
│    (Optionnel: 📜 Historique des analyses)                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# 📝 PAGE 1 : Formulaire d'Analyse Fournisseur

## URL suggérée
```
/supplier-analysis
```

## Maquette

```
┌─────────────────────────────────────────────────────────────┐
│  🔍 ANALYSE DE RISQUES FOURNISSEUR                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Nom du fournisseur *     [____________________________]    │
│                                                             │
│  Pays *                   [▼ Sélectionner un pays     ]     │
│                                                             │
│  Ville                    [____________________________]    │
│                                                             │
│  Coordonnées GPS          Lat: [______] Long: [______]      │
│  (optionnel)                                                │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Matières fournies *      [+] Ajouter une matière           │
│                           ┌─────────────────────────────┐   │
│                           │ • Caoutchouc naturel    [x] │   │
│                           │ • Latex                 [x] │   │
│                           └─────────────────────────────┘   │
│                                                             │
│  Codes NC (douaniers)     [+] Ajouter un code NC            │
│                           ┌─────────────────────────────┐   │
│                           │ • 4001                  [x] │   │
│                           │ • 400121                [x] │   │
│                           └─────────────────────────────┘   │
│                                                             │
│  Criticité                (○) Standard                      │
│                           (○) Important                     │
│                           (○) Critique                      │
│                                                             │
│  Volume annuel (€)        [________________] (optionnel)    │
│                                                             │
│                           ┌───────────────────────────┐     │
│                           │   🔍 ANALYSER LES RISQUES │     │
│                           └───────────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Champs du formulaire

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `name` | text | ✅ OUI | Nom du fournisseur |
| `country` | select/text | ✅ OUI | Pays du fournisseur |
| `city` | text | ❌ NON | Ville |
| `latitude` | number | ❌ NON | Coordonnée GPS (auto-géocodé si absent) |
| `longitude` | number | ❌ NON | Coordonnée GPS |
| `materials` | array[string] | ✅ OUI (min 1) | Liste des matières fournies |
| `nc_codes` | array[string] | ❌ NON | Codes douaniers NC |
| `criticality` | select | ❌ NON | `Standard` (défaut), `Important`, `Critique` |
| `annual_volume` | number | ❌ NON | Volume annuel en euros |

## Appel API

```http
POST /api/supplier/analyze
Content-Type: application/json
```

**Request Body :**
```json
{
  "name": "Thai Rubber Co.",
  "country": "Thailand",
  "city": "Bangkok",
  "latitude": 13.7563,
  "longitude": 100.5018,
  "materials": ["Caoutchouc naturel", "Latex"],
  "nc_codes": ["4001", "400121"],
  "criticality": "Important",
  "annual_volume": 2500000
}
```

## États du bouton

| État | Affichage |
|------|-----------|
| Formulaire invalide | Bouton grisé/désactivé |
| Prêt | `🔍 Analyser les risques` |
| En cours | `⏳ Analyse en cours...` + spinner |
| Erreur | Toast/alert avec message d'erreur |

---

# 📊 PAGE 2 : Résultats de l'Analyse

## URL suggérée
```
/supplier-analysis/results/{id}
```
ou affichage direct après soumission

## Response API (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "supplier_info": {
    "name": "Thai Rubber Co.",
    "country": "Thailand",
    "city": "Bangkok",
    "latitude": 13.7563,
    "longitude": 100.5018,
    "nc_codes": ["4001", "400121"],
    "materials": ["Caoutchouc naturel", "Latex"],
    "criticality": "Important",
    "annual_volume": 2500000
  },
  "regulatory_risks": {
    "count": 5,
    "items": [
      {
        "celex_id": "32023R0956",
        "title": "Regulation (EU) 2023/956 - CBAM",
        "publication_date": "2023-05-16",
        "document_type": "REGULATION",
        "source_url": "https://eur-lex.europa.eu/...",
        "matched_keyword": "Caoutchouc naturel",
        "relevance": "high"
      }
    ]
  },
  "weather_risks": {
    "count": 3,
    "items": [
      {
        "alert_type": "heavy_rain",
        "severity": "high",
        "date": "2026-02-10",
        "value": 85.5,
        "threshold": 50.0,
        "unit": "mm",
        "description": "Fortes précipitations prévues",
        "supply_chain_risk": "Retards de livraison possibles"
      }
    ]
  },
  "risk_score": 6.5,
  "risk_level": "Moyen",
  "recommendations": [
    {
      "type": "regulatory",
      "priority": "high",
      "action": "Vérifier la conformité EUDR",
      "details": "Demander les certificats de traçabilité."
    }
  ],
  "processing_time_ms": 4523
}
```

## Maquette des Résultats

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📊 RÉSULTATS - Thai Rubber Co. (Thailand)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     SCORE DE RISQUE GLOBAL                           │   │
│  │                                                                      │   │
│  │        ████████████░░░░░░░░  6.5 / 10  ⚠️ MOYEN                      │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────┐        ┌──────────────────────┐                   │
│  │  📜 RÉGLEMENTAIRES   │        │  🌤️ MÉTÉO            │                   │
│  │         5            │        │         3            │                   │
│  │      risques         │        │      alertes         │                   │
│  └──────────────────────┘        └──────────────────────┘                   │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  📜 RISQUES RÉGLEMENTAIRES                                                  │
│  ─────────────────────────                                                  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ 🔴 HIGH   CBAM - Carbon Border Adjustment Mechanism                  │   │
│  │           Regulation (EU) 2023/956                                   │   │
│  │           Matière concernée: Caoutchouc naturel                      │   │
│  │           [🔗 Voir sur EUR-Lex]                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ 🔴 HIGH   EUDR - Deforestation-free products                         │   │
│  │           Regulation (EU) 2023/1115                                  │   │
│  │           Matière concernée: Latex                                   │   │
│  │           [🔗 Voir sur EUR-Lex]                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  🌤️ ALERTES MÉTÉO (16 prochains jours)                                     │
│  ──────────────────────────────────────                                     │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ 🔴 HIGH   Fortes précipitations                                      │   │
│  │           📅 10/02/2026                                              │   │
│  │           💧 85.5 mm (seuil: 50 mm)                                  │   │
│  │           ⚠️ Impact: Retards de livraison possibles                  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ 🟠 MEDIUM Canicule                                                   │   │
│  │           📅 15/02/2026                                              │   │
│  │           🌡️ 42.3°C (seuil: 40°C)                                    │   │
│  │           ⚠️ Impact: Conditions de stockage à risque                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  💡 RECOMMANDATIONS                                                         │
│  ──────────────────                                                         │
│                                                                             │
│  1. 🔴 [HAUTE PRIORITÉ] Vérifier la conformité EUDR                         │
│     → Demander les certificats de traçabilité au fournisseur.               │
│                                                                             │
│  2. 🟠 [MOYENNE] Anticiper les retards météo                                │
│     → Prévoir un stock de sécurité de 2-3 semaines.                         │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐                           │
│  │  🔄 Nouvelle analyse │  │  📜 Historique      │                           │
│  └─────────────────────┘  └─────────────────────┘                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 📜 PAGE 3 (Optionnel) : Historique des Analyses

## URL suggérée
```
/supplier-analysis/history
```

## Appel API

```http
GET /api/supplier/analyses?page=1&limit=10
```

**Query Parameters :**
| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `page` | int | 1 | Numéro de page |
| `limit` | int | 10 | Éléments par page (max 100) |
| `country` | string | - | Filtrer par pays |
| `risk_level` | string | - | Filtrer: `Faible`, `Moyen`, `Fort`, `Critique` |

**Response :**
```json
{
  "analyses": [
    {
      "id": "uuid-1",
      "status": "completed",
      "supplier_info": {...},
      "risk_score": 6.5,
      "risk_level": "Moyen",
      ...
    }
  ],
  "total": 42,
  "page": 1,
  "limit": 10
}
```

## Maquette Historique

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📜 HISTORIQUE DES ANALYSES                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Pays: [▼ Tous    ]    Risque: [▼ Tous    ]    [🔍 Filtrer]                │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Thai Rubber Co.              Thailand        6.5  ⚠️ Moyen          │   │
│  │  01/02/2026                                   [Voir détails →]       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  German Steel GmbH            Germany         3.2  🟢 Faible         │   │
│  │  28/01/2026                                   [Voir détails →]       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Brazil Latex SA              Brazil          8.1  🔴 Fort           │   │
│  │  25/01/2026                                   [Voir détails →]       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [◀ Précédent]  Page 1/5  [Suivant ▶]                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 🔌 Récapitulatif des Endpoints API

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/supplier/analyze` | Lancer une analyse |
| `GET` | `/api/supplier/analyses` | Liste des analyses (historique) |
| `GET` | `/api/supplier/analyses/{id}` | Détail d'une analyse |
| `DELETE` | `/api/supplier/analyses/{id}` | Supprimer une analyse |

---

# 📐 Types TypeScript

```typescript
// ========== REQUEST ==========

interface SupplierAnalysisRequest {
  name: string;                    // Obligatoire
  country: string;                 // Obligatoire
  city?: string;
  latitude?: number;
  longitude?: number;
  materials: string[];             // Obligatoire, min 1
  nc_codes?: string[];
  criticality?: 'Standard' | 'Important' | 'Critique';
  annual_volume?: number;
}

// ========== RESPONSE ==========

interface SupplierAnalysisResponse {
  id: string;
  status: 'pending' | 'completed' | 'error';
  supplier_info: SupplierInfo;
  regulatory_risks: {
    count: number;
    items: RegulatoryRiskItem[];
  };
  weather_risks: {
    count: number;
    items: WeatherRiskItem[];
  };
  risk_score: number;              // 0-10
  risk_level: 'Faible' | 'Moyen' | 'Fort' | 'Critique';
  recommendations: RecommendationItem[];
  processing_time_ms: number;
}

interface SupplierInfo {
  name: string;
  country: string;
  city?: string;
  latitude?: number;
  longitude?: number;
  nc_codes: string[];
  materials: string[];
  criticality: string;
  annual_volume?: number;
}

interface RegulatoryRiskItem {
  celex_id: string;
  title: string;
  publication_date?: string;
  document_type?: string;
  source_url: string;
  matched_keyword: string;
  relevance: 'high' | 'medium' | 'low';
}

interface WeatherRiskItem {
  alert_type: 'snow' | 'heavy_rain' | 'extreme_heat' | 'extreme_cold' | 'high_wind';
  severity: 'critical' | 'high' | 'medium' | 'low';
  date: string;
  value: number;
  threshold: number;
  unit: string;
  description: string;
  supply_chain_risk: string;
}

interface RecommendationItem {
  type: 'regulatory' | 'weather' | 'general';
  priority: 'high' | 'medium' | 'low';
  action: string;
  details: string;
}

// ========== LIST RESPONSE ==========

interface SupplierAnalysisListResponse {
  analyses: SupplierAnalysisResponse[];
  total: number;
  page: number;
  limit: number;
}
```

---

# 🎨 Codes Couleur Suggérés

| Niveau | Couleur | Hex |
|--------|---------|-----|
| `critical` / `Critique` | 🔴 Rouge vif | `#DC2626` |
| `high` / `Fort` | 🔴 Rouge | `#EF4444` |
| `medium` / `Moyen` | 🟠 Orange | `#F59E0B` |
| `low` / `Faible` | 🟢 Vert | `#10B981` |

---

# 🚦 Codes d'Erreur HTTP

| Code | Signification | Action Frontend |
|------|---------------|-----------------|
| `200` | Succès | Afficher les résultats |
| `400` | Requête invalide | Afficher erreur de validation |
| `500` | Erreur serveur | Toast "Erreur, réessayez" |

**Format d'erreur :**
```json
{
  "detail": "Message d'erreur explicite"
}
```

---

# ⏱️ Temps de Réponse Attendus

| Opération | Temps typique |
|-----------|---------------|
| `POST /analyze` | 10-30 secondes |
| `GET /analyses` | < 500ms |
| `GET /analyses/{id}` | < 200ms |

> ⚠️ L'analyse prend du temps car elle fait des appels à EUR-Lex et Open-Meteo. Prévoir un **loading state** approprié.

---

*Document généré le 01/02/2026 - Version 1.0*
