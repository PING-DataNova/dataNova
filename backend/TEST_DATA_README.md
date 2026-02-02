# 📊 Données de Test PING

Ce document décrit les données de test créées pour tester Agent 2 (Risk Analyzer).

## 🎯 Objectif

Les données de test sont inspirées de **Prewave** et du document `donnees_minimales.pdf`. Elles permettent de tester les 3 types de risques :
1. **Climatique** (projection géographique GPS)
2. **Réglementaire** (projection pays/secteur/produit)
3. **Géopolitique** (pays affectés + voisins)

## 📦 Contenu de la Base de Données

### 🏭 Sites Hutchinson (8 sites)

| Site | Pays | Secteur | Importance Stratégique |
|------|------|---------|------------------------|
| Bangkok Manufacturing Plant | Thailand | Automobile, Aéronautique | Fort |
| Paris R&D Center | France | R&D, Innovation | Critique |
| Munich Production Facility | Germany | Automobile | Critique |
| Warsaw Assembly Plant | Poland | Automobile, Industriel | Moyen |
| Shanghai Manufacturing Hub | China | Automobile, Électronique | Fort |
| Monterrey Production Center | Mexico | Automobile | Moyen |
| Toulouse Aerospace Plant | France | Aéronautique | Critique |
| Detroit Manufacturing Plant | USA | Automobile | Fort |

### 🏢 Fournisseurs (10 fournisseurs)

| Fournisseur | Pays | Produits | Santé Financière |
|-------------|------|----------|------------------|
| Thai Rubber Industries Co. | Thailand | Caoutchouc naturel, Latex | Bon |
| Deutsche Stahlwerke GmbH | Germany | Acier haute résistance | Excellent |
| Polska Komponenty Sp. z o.o. | Poland | Composants mécaniques | Moyen |
| Shenzhen Electronics Manufacturing Ltd. | China | Composants électroniques | Excellent |
| Polymères de France SA | France | Polymères techniques | Excellent |
| Aceros Mexicanos SA de CV | Mexico | Acier, Tôles | Bon |
| American Hydraulics Inc. | USA | Huiles hydrauliques | Excellent |
| Vietnam Rubber Export Corporation | Vietnam | Caoutchouc naturel | Bon |
| Ukrainian Titanium Works | Ukraine | Titane, Alliages | Faible |
| Compositi Italiani SpA | Italy | Matériaux composites | Excellent |

### 🔗 Relations Site-Fournisseur (10 relations)

| Site | Fournisseur | Criticité | Fournisseur Unique | Stock (jours) | Délai (jours) |
|------|-------------|-----------|-------------------|---------------|---------------|
| Bangkok | Thai Rubber | **Critique** | ✅ Oui | 14 | 7 |
| Bangkok | Vietnam Rubber | Important | ❌ Non | 21 | 10 |
| Munich | German Steel | **Critique** | ❌ Non | 30 | 14 |
| Munich | French Polymers | Important | ❌ Non | 45 | 7 |
| Warsaw | Polish Components | **Critique** | ✅ Oui | 10 | 5 |
| Shanghai | Chinese Electronics | **Critique** | ❌ Non | 20 | 14 |
| Mexico | Mexican Steel | Important | ❌ Non | 25 | 10 |
| Detroit | US Hydraulics | Important | ❌ Non | 60 | 7 |
| **Toulouse** | **Ukrainian Titanium** | **Critique** | ✅ **Oui** | **90** | **30** |
| Toulouse | Italian Composites | Important | ❌ Non | 45 | 14 |

### 📄 Documents de Test (3 événements)

#### 1. 🌊 Risque Climatique : Inondations à Bangkok

**Type** : `climatique` / `Inondation`

**Résumé** : Inondations sévères à Bangkok (rayon 50km) pendant 2-3 semaines. Routes coupées, port partiellement fermé.

**Impact attendu** :
- ✅ Site Bangkok directement impacté (dans le rayon)
- ✅ Fournisseur Thai Rubber impacté (fournisseur unique, critique)
- ⚠️ Stock de sécurité : 14 jours
- ⚠️ Durée de l'événement : 21 jours
- 🚨 **Risque de rupture de stock après 14 jours**

**Cascade d'impacts** :
```
Inondation Bangkok (21 jours)
  ↓
Thai Rubber arrête production (fournisseur unique)
  ↓
Stock Bangkok épuisé après 14 jours
  ↓
Production Bangkok arrêtée après 14 jours
  ↓
Clients automobiles/aéronautiques impactés
  ↓
Recommandations : Activer fournisseur backup Vietnam, transport aérien d'urgence
```

#### 2. 📜 Risque Réglementaire : CBAM Europe

**Type** : `reglementaire` / `CBAM`

**Résumé** : Taxe carbone sur importations d'acier et aluminium en UE. Augmentation des coûts de 10-30%.

**Impact attendu** :
- ✅ Sites européens impactés : Munich, Toulouse, Paris
- ✅ Fournisseurs hors UE impactés : Chine, Mexique, USA
- 💰 Augmentation des coûts de 10-30%
- 📅 Deadline de conformité : 31 mars 2026

**Cascade d'impacts** :
```
CBAM entre en vigueur (1er janvier 2026)
  ↓
Fournisseurs hors UE doivent déclarer émissions CO2
  ↓
Coûts d'importation augmentent de 10-30%
  ↓
Sites européens voient leurs coûts augmenter
  ↓
Recommandations : Sourcing local UE, négociation prix, certification fournisseurs
```

#### 3. ⚔️ Risque Géopolitique : Conflit Ukraine

**Type** : `geopolitique` / `Conflit`

**Résumé** : Escalade du conflit en Ukraine. Suspension des exportations de titane. Prix +45%. Durée estimée : 6 mois.

**Impact attendu** :
- ✅ Fournisseur Ukrainian Titanium directement impacté
- ✅ Site Toulouse dépend exclusivement de ce fournisseur
- ⚠️ Stock de sécurité : 90 jours
- ⚠️ Durée de l'événement : 6 mois (180 jours)
- 🚨 **Risque de rupture de stock après 90 jours**
- 💰 Prix du titane +45%

**Cascade d'impacts** :
```
Conflit Ukraine s'intensifie (6 mois)
  ↓
Ukrainian Titanium arrête exportations (fournisseur unique)
  ↓
Stock Toulouse épuisé après 90 jours
  ↓
Production aéronautique Toulouse arrêtée après 90 jours
  ↓
Clients Airbus/Safran impactés (pièces structurelles critiques)
  ↓
Recommandations : Sourcing alternatif USA/Japon, rationnement, priorisation commandes
```

## 🧪 Comment Utiliser ces Données

### 1. Populer la Base de Données

```bash
cd /home/ubuntu/dataNova/backend
python populate_test_data.py
```

### 2. Vérifier les Données

```bash
python -c "
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
sys.path.insert(0, 'src')
from storage.models import HutchinsonSite, Supplier, Document

engine = create_engine('sqlite:///ping_test.db')
Session = sessionmaker(bind=engine)
session = Session()

print(f'Sites: {session.query(HutchinsonSite).count()}')
print(f'Fournisseurs: {session.query(Supplier).count()}')
print(f'Documents: {session.query(Document).count()}')
"
```

### 3. Tester Agent 2

```bash
cd /home/ubuntu/dataNova/backend/src/agents/agent_2
python test_agent_2.py
```

## 📝 Scénarios de Test Recommandés

### Scénario 1 : Bangkok Flood (Risque Climatique)
- **Objectif** : Tester la projection géographique GPS
- **Attendu** : Agent 2 détecte Bangkok + Thai Rubber dans le rayon de 50km
- **Criticité** : Fournisseur unique, stock 14 jours < durée 21 jours

### Scénario 2 : CBAM Europe (Risque Réglementaire)
- **Objectif** : Tester la projection réglementaire (pays/secteur/produit)
- **Attendu** : Agent 2 détecte sites UE + fournisseurs hors UE d'acier/alu
- **Criticité** : Impact financier, deadline de conformité

### Scénario 3 : Ukraine Conflict (Risque Géopolitique)
- **Objectif** : Tester la projection géopolitique (pays + voisins)
- **Attendu** : Agent 2 détecte Ukrainian Titanium + site Toulouse
- **Criticité** : Fournisseur unique, stock 90 jours < durée 180 jours

## 🎯 Métriques de Succès

Pour chaque scénario, Agent 2 doit :

1. ✅ **Identifier correctement les entités impactées**
   - Sites dans la zone géographique / réglementaire / géopolitique
   - Fournisseurs dans la zone

2. ✅ **Analyser la criticité**
   - Fournisseur unique vs. double source
   - Stock de sécurité vs. durée de l'événement
   - Importance stratégique du site

3. ✅ **Calculer le risque en cascade**
   - Timeline : Quand le stock sera épuisé ?
   - Impact production : Quand la production s'arrêtera ?
   - Impact clients : Quels clients seront impactés ?

4. ✅ **Générer des recommandations actionnables**
   - Actions immédiates (< 7 jours)
   - Actions court terme (7-30 jours)
   - Actions moyen terme (1-6 mois)

## 📊 Exemple de Résultat Attendu (Scénario 3 - Ukraine)

```json
{
  "risk_level": "Critique",
  "risk_score": 0.92,
  "affected_sites": [
    {
      "site_id": "site_toulouse",
      "site_name": "Toulouse Aerospace Plant",
      "impact_level": "critique",
      "reason": "Dépend exclusivement du fournisseur Ukrainian Titanium"
    }
  ],
  "affected_suppliers": [
    {
      "supplier_id": "supplier_ukrainian_titanium",
      "supplier_name": "Ukrainian Titanium Works",
      "impact_level": "critique",
      "reason": "Situé en Ukraine, exportations suspendues"
    }
  ],
  "criticality_analysis": {
    "is_sole_supplier": true,
    "has_backup": false,
    "stock_days": 90,
    "event_duration_days": 180,
    "stock_depletion_date": "2026-04-25",
    "production_stop_date": "2026-04-25"
  },
  "recommendations": [
    {
      "action": "Identifier sources alternatives de titane (USA, Japon, Kazakhstan)",
      "urgency": "Immédiate",
      "timeline": "< 7 jours"
    },
    {
      "action": "Négocier contrats d'urgence avec fournisseurs alternatifs",
      "urgency": "Haute",
      "timeline": "7-30 jours"
    },
    {
      "action": "Rationner le stock existant, prioriser commandes critiques",
      "urgency": "Haute",
      "timeline": "Immédiat"
    }
  ]
}
```

## 🔧 Maintenance

Pour ajouter de nouvelles données de test :

1. Modifier `/tmp/test_data.json`
2. Réexécuter `python populate_test_data.py`
3. Tester avec Agent 2

## 📚 Références

- `donnees_minimales.pdf` : Spécification des données minimales
- `ESIGELEC5_Transcription_Reunion.pdf` : Transcription client avec exemple cascade
- Architecture Prewave : Projection géographique + criticité + cascade reasoning
