# 🔧 AMÉLIORATIONS NÉCESSAIRES POUR L'AGENT 2
## Basé sur les demandes client du 03/02/2026

---

## ❌ PROBLÈMES IDENTIFIÉS DANS LE RAPPORT ACTUEL

### 1. Informations manquantes pour chaque entité affectée

**Actuel:** Juste le nom des sites/fournisseurs  
**Attendu par le client:**
- ✅ Nom de l'entité
- ❌ **Niveau d'impact par entité** (CRITIQUE/FORT/MOYEN/FAIBLE)
- ❌ **Raison spécifique** de l'impact pour chaque entité

**Exemple actuel:**
```
1. Bangkok Manufacturing Plant (N/A)
   Impact: N/A
```

**Exemple attendu:**
```
1. Bangkok Manufacturing Plant (Thaïlande)
   Impact: CRITIQUE
   Raison: Site situé en zone inondable, produit des composants pour l'aéronautique 
           avec un CA de 450K€/jour. Risque d'arrêt de production pendant 5-7 jours.
```

---

### 2. SECTION 4 : ANALYSE D'IMPACT - Presque vide

**Actuel:**
```
💰 IMPACT FINANCIER:
   • À évaluer en détail (données insuffisantes)

⏰ DÉLAIS:
   • Information non disponible dans l'analyse
```

**Attendu par le client (voir DEMANDES_CLIENT_COMPLETES.md):**
```
💰 IMPACT FINANCIER:
   • Surcoût douanier estimé: +15% sur imports concernés
   • Impact CA annuel: ~2.3M€
   • Coût mise en conformité: ~150K€ (audit + process)
   • Perte potentielle par jour d'interruption: 450K€

⏰ DÉLAIS:
   • Loi en vigueur depuis: 01/01/2026
   • Date d'application effective: 01/01/2026
   • Délai mise en conformité recommandé: 6 mois
   • Période de transition: Jusqu'au 31/12/2026

⚠️ RISQUES ASSOCIÉS:
   • Pénalités si non-conformité: jusqu'à 50K€ par infraction
   • Perte de compétitivité vs concurrents conformes
   • Rupture d'approvisionnement si fournisseurs non-conformes
   • Impact réputation auprès clients aéronautique
```

---

### 3. SOURCE - Résumé du document manquant

**Actuel:** URL et titre seulement  
**Attendu:** Extrait pertinent du document source

**Citation client:**
> *"À chaque fois, vous mettez la source. L'utilisateur peut cliquer sur la source pour aller voir effectivement."*

**Amélioration à faire:**
```python
# Dans agent.py, ajouter dans risk_analysis:
"source_extract": document.get('summary', '')[:500] + "...",
"source_url": document.get('source_url'),
"publication_date": document.get('publication_date'),
"application_date": self._extract_application_date(document)
```

---

### 4. Score d'impact toujours à 0

**Actuel:**
```
Score d'impact: 0.00/100
```

**Problème:** L'agent calcule `risk_score` mais pas `impact_score` séparé

**Solution:** Calculer un score d'impact basé sur:
- Nombre d'entités affectées
- CA quotidien total des entités
- Criticité des fournisseurs
- Stock coverage

---

### 5. Projections sans niveau de risque

**Actuel:**
```
- Unknown: 18 entité(s)
```

**Attendu:**
```
- CRITIQUE: 3 entités
- FORT: 5 entités
- MOYEN: 7 entités
- FAIBLE: 3 entités
```

**Problème:** Le champ `risk_level` n'est pas renseigné dans les projections

---

## ✅ PLAN D'ACTION POUR CORRIGER

### Priorité 1 : Enrichir les entités affectées avec impact_level et reason

**Fichier:** `backend/src/agent_2/regulatory_geopolitical_engine.py`

La fonction `_determine_regulatory_impact_level()` existe déjà mais n'est pas utilisée correctement.

**Action:**
```python
# Dans analyze_regulatory_geopolitical_risk(), ligne ~185
affected_sites.append({
    "id": s.id,
    "name": s.name,
    "country": s.country,
    "impact_level": s.impact_level,  # ✅ Déjà présent
    "reason": s.reason  # ✅ Déjà présent
})
```

**Vérification:** Ces champs existent déjà dans SiteImpact et SupplierImpact !

---

### Priorité 2 : Calculer l'impact financier dans risk_analysis

**Fichier:** `backend/src/agent_2/agent.py`

**Action:** Dans `analyze()`, après le calcul des projections, ajouter:

```python
# Calculer l'impact financier total
total_daily_impact = sum(
    proj.get('business_impact_details', {}).get('total_daily_impact_eur', 0)
    for proj in risk_projections
    if proj.get('is_concerned')
)

# Estimer l'impact sur différentes périodes
financial_impact = {
    "total_daily_impact_eur": total_daily_impact,
    "total_weekly_impact_eur": total_daily_impact * 5,  # 5 jours ouvrés
    "total_monthly_impact_eur": total_daily_impact * 20,
    "total_annual_impact_eur": total_daily_impact * 250,
    "compliance_cost_eur": "À évaluer",  # Pourrait venir du LLM
    "currency": "EUR"
}

risk_analysis["financial_impact"] = financial_impact
```

---

### Priorité 3 : Extraire les délais du document

**Fichier:** `backend/src/agent_2/agent.py`

**Action:** Créer une méthode pour extraire les dates:

```python
def _extract_timeline(self, document: Dict) -> Dict:
    """
    Extrait les informations de délais du document
    """
    timeline = {
        "publication_date": document.get('publication_date'),
        "effective_date": None,  # Pourrait venir d'un parsing du contenu
        "compliance_deadline": None,
        "urgency": self._determine_urgency(document)
    }
    
    # Si c'est un document réglementaire, chercher les dates d'application
    if document.get('event_type') == 'reglementaire':
        # TODO: Parser le contenu pour trouver "entre en vigueur le..."
        pass
    
    return timeline

def _determine_urgency(self, document: Dict) -> str:
    """Détermine l'urgence basée sur le type et la date"""
    event_type = document.get('event_type')
    
    if event_type == 'climatique':
        return "IMMEDIATE"  # Tempête dans 48h
    elif event_type == 'geopolitique':
        return "HIGH"  # Conflit en cours
    else:
        return "MEDIUM"  # Réglementaire = délais de mise en conformité
```

---

### Priorité 4 : Ajouter associated_risks dans risk_analysis

**Fichier:** `backend/src/agent_2/agent.py`

**Action:** Après avoir calculé les impacts:

```python
# Identifier les risques associés
associated_risks = []

# Risques liés aux fournisseurs uniques
sole_suppliers = [
    proj for proj in risk_projections
    if proj.get('is_concerned') and 
       proj.get('business_impact_details', {}).get('is_sole_supplier')
]
if sole_suppliers:
    associated_risks.append(
        f"Risque de rupture d'approvisionnement : {len(sole_suppliers)} "
        f"fournisseur(s) unique(s) affecté(s)"
    )

# Risques liés aux stocks faibles
low_stock = [
    proj for proj in risk_projections
    if proj.get('is_concerned') and 
       proj.get('business_impact_details', {}).get('stock_coverage_days', 999) < 15
]
if low_stock:
    associated_risks.append(
        f"Stocks de sécurité insuffisants : {len(low_stock)} entité(s) "
        f"avec moins de 15 jours de couverture"
    )

# Risques météo
if weather_risk_summary and weather_risk_summary.get('total_alerts', 0) > 0:
    associated_risks.append(
        f"Risques météorologiques : {weather_risk_summary.get('total_alerts')} "
        f"alertes actives sur {weather_risk_summary.get('sites_with_alerts')} sites"
    )

# Risques réglementaires
if document.get('event_type') == 'reglementaire':
    associated_risks.extend([
        "Non-conformité réglementaire : risque de pénalités",
        "Perte de compétitivité face aux concurrents déjà conformes"
    ])

risk_analysis["associated_risks"] = associated_risks
```

---

### Priorité 5 : Calculer le score d'impact séparé

**Fichier:** `backend/src/agent_2/agent.py`

**Action:** Dans `analyze()`:

```python
# Calculer le score d'impact (0-100) basé sur :
# - Nombre d'entités (30%)
# - Impact financier (40%)
# - Criticité (30%)

entities_score = min(30, (len(affected_sites) + len(affected_suppliers)) * 1.5)

financial_score = min(40, (total_daily_impact / 100000) * 5)  # 100K€ = 5 pts

criticality_score = 0
if criticality_results.get('critical_suppliers_count', 0) > 0:
    criticality_score += 15
if criticality_results.get('unique_suppliers_count', 0) > 0:
    criticality_score += 15

impact_score = entities_score + financial_score + criticality_score

risk_analysis["impact_score"] = round(impact_score, 2)
```

---

### Priorité 6 : Renseigner risk_level dans les projections

**Fichier:** `backend/src/agent_2/agent.py`

**Action:** Dans `_generate_risk_projection()`:

```python
# Après avoir calculé risk_score
risk_level = "FAIBLE"
if risk_score >= 70:
    risk_level = "CRITIQUE"
elif risk_score >= 50:
    risk_level = "FORT"
elif risk_score >= 30:
    risk_level = "MOYEN"

projection = {
    # ... champs existants
    "risk_level": risk_level,  # ✅ AJOUTER
    "risk_score": risk_score
}
```

---

## 📊 RÉSULTAT ATTENDU APRÈS CORRECTIONS

```
====================================================================================================
SECTION 1 : SYNTHÈSE
====================================================================================================

🎯 SCORES:
   • Niveau de risque: CRITIQUE
   • Score de risque: 82.75/100
   • Score d'impact: 68.50/100  ← ✅ Calculé
   • Score 360°: 82.75/100

====================================================================================================
SECTION 2 : SOURCE DU DOCUMENT
====================================================================================================

📜 Titre: Regulation (EU) 2023/956 - CBAM
📅 Date de publication: 10/05/2023
📅 Date d'application: 01/01/2026
🔗 URL: https://eur-lex.europa.eu/...

📝 RÉSUMÉ:  ← ✅ Ajouté
   Le mécanisme d'ajustement carbone aux frontières (CBAM) impose aux importateurs
   de déclarer les émissions de CO2 incorporées dans certains produits (acier,
   aluminium, ciment, engrais, électricité, hydrogène) et d'acheter des certificats
   correspondants...

====================================================================================================
SECTION 3 : ENTITÉS IMPACTÉES
====================================================================================================

🏭 SITES (8 sites affectés):

1. Bangkok Manufacturing Plant (Thaïlande)  ← ✅ Pays affiché
   Impact: CRITIQUE  ← ✅ Niveau d'impact
   Raison: Production de composants aluminium pour aéronautique.  ← ✅ Raison
           CA quotidien 450K€. Située en zone inondable.

====================================================================================================
SECTION 4 : ANALYSE D'IMPACT
====================================================================================================

💰 IMPACT FINANCIER:  ← ✅ Calculé et détaillé
   • Impact quotidien total: 1,245,000 €
   • Impact hebdomadaire: 6,225,000 €
   • Impact mensuel: 24,900,000 €
   • Impact annuel estimé: 311,250,000 €

⏰ DÉLAIS:  ← ✅ Extrait du document
   • Date de publication: 10/05/2023
   • Date d'application: 01/01/2026
   • Délai de mise en conformité: 6 mois recommandés
   • Urgence: HIGH

⚠️ RISQUES ASSOCIÉS:  ← ✅ Liste générée
   • Risque de rupture : 2 fournisseur(s) unique(s) affecté(s)
   • Stocks insuffisants : 5 entité(s) avec < 15j de couverture
   • Non-conformité réglementaire : risque de pénalités
   • Perte de compétitivité

====================================================================================================
PROJECTIONS PAR ENTITÉ
====================================================================================================

Total: 18 entités analysées

   • CRITIQUE: 3 entité(s)  ← ✅ Niveaux calculés
   • FORT: 5 entité(s)
   • MOYEN: 7 entité(s)
   • FAIBLE: 3 entité(s)

🔴 Détail des 3 entités CRITIQUE (score >= 70):

   - Warsaw Assembly Plant (site)
     Score: 72.8/100 | Niveau: CRITIQUE  ← ✅
     Impact quotidien: 185K€
     Raison: Fournisseur unique polonais affecté, stock < 10 jours
```

---

## 🎯 PRIORISATION

| Priorité | Tâche | Impact | Temps estimé |
|----------|-------|--------|--------------|
| 🔴 P1 | Impact financier calculé | ⭐⭐⭐ | 30 min |
| 🔴 P1 | Risques associés listés | ⭐⭐⭐ | 20 min |
| 🔴 P1 | Risk_level dans projections | ⭐⭐⭐ | 15 min |
| 🟠 P2 | Impact_score calculé | ⭐⭐ | 30 min |
| 🟠 P2 | Timeline extrait | ⭐⭐ | 45 min |
| 🟡 P3 | Résumé document affiché | ⭐ | 10 min |

**Total estimé:** 2h30

---

## 📝 CITATIONS CLIENT RAPPEL

> *"À chaque fois, vous mettez la source. L'utilisateur peut cliquer sur la source pour aller voir effectivement."*

> *"Ce rapport a été généré automatiquement par des agents. Il n'a pas fait l'objet d'une validation humaine."*

> *"Impact financier estimé (€), Délais (mise en conformité, fermeture estimée, etc.), Risques associés (pénalités, rupture stock, etc.)"*

---

Date: 04/02/2026  
Statut: À implémenter
