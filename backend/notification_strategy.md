# 📧 Stratégie de Notification PING - Équipe Achats

## 🎯 Objectif

Après l'analyse de l'Agent 2, notifier **les bonnes personnes** avec **les bonnes informations** au **bon moment** pour permettre une **action rapide**.

---

## 👥 Segmentation des Destinataires

### 1. **Notification par Niveau de Risque**

| Niveau de Risque | Destinataires | Délai | Format |
|------------------|---------------|-------|--------|
| **CRITIQUE** (≥80) | • Directeur Achats<br>• Directeur Supply Chain<br>• Direction Générale<br>• Responsables sites affectés | **IMMÉDIAT** (0-5 min) | Email + SMS + PDF détaillé |
| **ÉLEVÉ** (60-79) | • Directeur Achats<br>• Responsables Achats concernés<br>• Responsables sites affectés | **URGENT** (0-15 min) | Email + PDF détaillé |
| **MOYEN** (40-59) | • Responsables Achats concernés<br>• Responsables sites affectés | **PRIORITAIRE** (0-30 min) | Email + PDF résumé |
| **FAIBLE** (<40) | • Responsables Achats concernés | **NORMAL** (0-1h) | Email résumé + Lien dashboard |

---

### 2. **Notification par Type d'Entité Affectée**

| Entité Affectée | Destinataires Spécifiques |
|-----------------|---------------------------|
| **Site Hutchinson** | • Directeur du site<br>• Responsable Production du site<br>• Responsable Supply Chain du site |
| **Fournisseur** | • Responsable Achats de la catégorie<br>• Acheteur en charge du fournisseur<br>• Responsable Qualité Fournisseurs |
| **Fournisseur UNIQUE** | **+ Directeur Achats**<br>**+ Directeur Supply Chain** |

---

### 3. **Notification par Type d'Événement**

| Type d'Événement | Destinataires Additionnels |
|------------------|----------------------------|
| **Réglementaire** | • Responsable Conformité<br>• Responsable Juridique<br>• Responsable RSE |
| **Climatique** | • Responsable HSE<br>• Responsable Continuité d'Activité<br>• Responsable Assurances |
| **Géopolitique** | • Directeur des Achats Internationaux<br>• Responsable Risques Pays<br>• Direction Générale |

---

## 📧 Contenu des Notifications

### **Email CRITIQUE (Risque ≥80)**

#### Objet
```
🚨 ALERTE CRITIQUE - [Type Événement] - [Titre] - Action Immédiate Requise
```

Exemple :
```
🚨 ALERTE CRITIQUE - Réglementaire CBAM - Impact 7.5M€ - Action Immédiate Requise
```

#### Corps de l'Email

```
Bonjour [Prénom],

Une alerte CRITIQUE vient d'être détectée par le système PING et nécessite votre attention IMMÉDIATE.

═══════════════════════════════════════════════════════════════════════════════
📋 RÉSUMÉ EXÉCUTIF
═══════════════════════════════════════════════════════════════════════════════

ÉVÉNEMENT : Regulation (EU) 2023/956 - Carbon Border Adjustment Mechanism (CBAM)
TYPE : Réglementaire
NIVEAU DE RISQUE : CRITIQUE (Score 82.75/100)

IMPACT FINANCIER :
• Impact annuel estimé : 7.5M€
• Surcoût CBAM : +2.3M€/an
• Perte de production potentielle : -5.2M€/an

ENTITÉS AFFECTÉES :
• 8 sites Hutchinson
• 10 fournisseurs (dont 2 fournisseurs uniques)

URGENCE : IMMÉDIATE (Action requise sous 48h)

═══════════════════════════════════════════════════════════════════════════════
🎯 ACTIONS PRIORITAIRES
═══════════════════════════════════════════════════════════════════════════════

1. [IMMEDIATE] Diversifier l'approvisionnement en caoutchouc
   • Fournisseur : Thai Rubber Industries Co., Ltd. (fournisseur unique)
   • Impact si inaction : 4.05M€ de pertes sur 90 jours
   • Budget : 590k€ | ROI : 6.9x
   • Responsable : Directeur Achats Matières Premières
   • Délai : 30 jours

2. [HIGH] Réduire les émissions CO2 du site Toulouse
   • Impact : 960k€ de surcoût CBAM évité
   • Budget : 380k€ | ROI : 2.5x
   • Responsable : Directeur du site Toulouse
   • Délai : 60 jours

3. [MEDIUM] Augmenter les stocks de sécurité Munich
   • Impact : 304k€ de pertes évitées
   • Budget : 140k€ | ROI : 2.2x
   • Responsable : Responsable Supply Chain Munich
   • Délai : 45 jours

═══════════════════════════════════════════════════════════════════════════════
📎 PIÈCES JOINTES
═══════════════════════════════════════════════════════════════════════════════

• Rapport d'analyse détaillé (PDF, 15 pages)
• Liste des entités affectées (Excel)
• Plan d'action recommandé (PDF, 3 pages)

═══════════════════════════════════════════════════════════════════════════════
🔗 ACTIONS DISPONIBLES
═══════════════════════════════════════════════════════════════════════════════

[Voir le Rapport Complet] [Approuver les Recommandations] [Demander une Révision]

[Accéder au Dashboard PING] [Contacter l'Équipe Risques]

═══════════════════════════════════════════════════════════════════════════════

⚠️ Cette alerte nécessite une action IMMÉDIATE. Merci de confirmer la prise en compte sous 48h.

Cordialement,
Système PING - Hutchinson Risk Management
```

---

### **Email ÉLEVÉ (Risque 60-79)**

#### Objet
```
⚠️ ALERTE ÉLEVÉE - [Type Événement] - [Titre] - Action Urgente
```

#### Corps de l'Email

```
Bonjour [Prénom],

Une alerte de niveau ÉLEVÉ vient d'être détectée par le système PING.

═══════════════════════════════════════════════════════════════════════════════
📋 RÉSUMÉ
═══════════════════════════════════════════════════════════════════════════════

ÉVÉNEMENT : [Titre]
TYPE : [Type]
NIVEAU DE RISQUE : ÉLEVÉ (Score XX/100)

IMPACT FINANCIER : X.XM€
ENTITÉS AFFECTÉES : X sites, X fournisseurs
URGENCE : HAUTE (Action requise sous 7 jours)

═══════════════════════════════════════════════════════════════════════════════
🎯 ACTIONS RECOMMANDÉES (Top 3)
═══════════════════════════════════════════════════════════════════════════════

[Liste des 3 recommandations principales avec budget et ROI]

═══════════════════════════════════════════════════════════════════════════════
📎 PIÈCES JOINTES
═══════════════════════════════════════════════════════════════════════════════

• Rapport d'analyse détaillé (PDF)

═══════════════════════════════════════════════════════════════════════════════

[Voir le Rapport Complet] [Accéder au Dashboard]

Cordialement,
Système PING
```

---

### **Email MOYEN (Risque 40-59)**

#### Objet
```
ℹ️ ALERTE MOYENNE - [Type Événement] - [Titre]
```

#### Corps de l'Email

```
Bonjour [Prénom],

Une nouvelle alerte de niveau MOYEN a été détectée.

ÉVÉNEMENT : [Titre]
NIVEAU DE RISQUE : MOYEN (Score XX/100)
IMPACT FINANCIER : X.XM€
ENTITÉS AFFECTÉES : X sites, X fournisseurs

📎 Rapport résumé en pièce jointe (PDF, 3 pages)

[Voir le Rapport Complet] [Accéder au Dashboard]

Cordialement,
Système PING
```

---

### **Email FAIBLE (Risque <40)**

#### Objet
```
📊 Nouvelle Alerte - [Type Événement] - [Titre]
```

#### Corps de l'Email

```
Bonjour [Prénom],

Une nouvelle alerte a été détectée.

ÉVÉNEMENT : [Titre]
NIVEAU DE RISQUE : FAIBLE (Score XX/100)

[Accéder au Dashboard pour plus de détails]

Cordialement,
Système PING
```

---

## 📄 Contenu du Rapport PDF

### **PDF Détaillé (Risque CRITIQUE/ÉLEVÉ)**

**Structure (15-20 pages) :**

1. **Page de Garde**
   - Logo Hutchinson
   - Titre : "Rapport d'Analyse de Risque - [Événement]"
   - Niveau de risque (badge coloré)
   - Date de génération
   - Numéro de référence

2. **Résumé Exécutif (1 page)**
   - Événement
   - Niveau de risque
   - Impact financier
   - Entités affectées
   - Actions prioritaires (top 3)

3. **Contexte et Enjeux (2 pages)**
   - Qu'est-ce que l'événement ?
   - Pourquoi est-ce critique ?
   - Calendrier d'application

4. **Entités Affectées (3-4 pages)**
   - Liste complète des sites avec scores
   - Liste complète des fournisseurs avec scores
   - Carte géographique des entités affectées

5. **Analyse Financière Détaillée (2-3 pages)**
   - Impact direct (surcoût, perte de production)
   - Coût des mesures de mitigation
   - ROI calculé
   - Graphiques (répartition des coûts, timeline des impacts)

6. **Recommandations Prioritaires (4-5 pages)**
   - Chaque recommandation sur 1 page
   - Contexte + Risque + Actions + Budget + ROI
   - Timeline visuelle

7. **Matrice de Priorisation (1 page)**
   - Graphique impact vs urgence

8. **Scénario "Ne Rien Faire" (1 page)**
   - Coût de l'inaction sur 3 horizons

9. **Annexes (2-3 pages)**
   - Méthodologie d'analyse
   - Sources de données
   - Contacts utiles

---

### **PDF Résumé (Risque MOYEN)**

**Structure (3-5 pages) :**

1. **Page de Garde**
2. **Résumé Exécutif (1 page)**
3. **Entités Affectées (1 page)**
4. **Recommandations (1-2 pages)**
5. **Contacts (1 page)**

---

## ⏰ Timing des Notifications

### **Workflow de Notification**

```
Agent 2 Termine l'Analyse
         ↓
    [Décision Judge]
         ↓
   ┌─────┴─────┐
   │           │
Score ≥ 8.5   Score 7.0-8.4
   │           │
   ↓           ↓
APPROVE    VALIDATION HUMAINE
   │           │
   ↓           ↓
Génération PDF  Attente Validation
   │           │
   ↓           ↓ (si validé)
Envoi Email    Génération PDF
   │           │
   ↓           ↓
IMMÉDIAT      Envoi Email
(0-5 min)     │
              ↓
           IMMÉDIAT
           (0-5 min)
```

---

### **Délais par Niveau de Risque**

| Niveau | Génération PDF | Envoi Email | Total |
|--------|----------------|-------------|-------|
| **CRITIQUE** | 30s | 10s | **40s** |
| **ÉLEVÉ** | 45s | 10s | **55s** |
| **MOYEN** | 60s | 10s | **70s** |
| **FAIBLE** | N/A (pas de PDF) | 10s | **10s** |

---

## 🔔 Canaux de Notification

### **Niveau CRITIQUE**

1. **Email** (priorité haute)
2. **SMS** (pour Directeur Achats + Direction)
3. **Notification Push** (si app mobile)
4. **Slack/Teams** (canal #alertes-critiques)

### **Niveau ÉLEVÉ**

1. **Email** (priorité haute)
2. **Slack/Teams** (canal #alertes-achats)

### **Niveau MOYEN**

1. **Email** (priorité normale)

### **Niveau FAIBLE**

1. **Email** (priorité basse)
2. **Dashboard** (notification in-app)

---

## 📊 Tableau de Bord des Notifications

### **Dashboard PING - Vue Achats**

**Widgets :**

1. **Alertes Actives** (carte)
   - Nombre d'alertes par niveau
   - Clic → Liste des alertes

2. **Actions en Attente** (liste)
   - Recommandations non traitées
   - Responsable assigné
   - Délai restant

3. **Historique des Notifications** (timeline)
   - Dernières 10 notifications
   - Statut (lu/non lu, traité/non traité)

4. **Carte des Risques** (carte géographique)
   - Sites et fournisseurs affectés
   - Couleur selon niveau de risque

---

## 🎯 Résumé : Que Doit Contenir la Notification ?

### **Email**

1. ✅ **Objet clair** avec niveau de risque et urgence
2. ✅ **Résumé exécutif** (événement, impact, entités)
3. ✅ **Top 3 des actions prioritaires** avec budget et ROI
4. ✅ **Pièces jointes** (PDF détaillé, Excel entités)
5. ✅ **Boutons d'action** (Voir rapport, Approuver, Dashboard)
6. ✅ **Délai d'action** (sous 48h, 7 jours, etc.)

### **PDF**

1. ✅ **Page de garde** professionnelle
2. ✅ **Résumé exécutif** (1 page)
3. ✅ **Contexte explicatif** (qu'est-ce que l'événement ?)
4. ✅ **Liste complète des entités** avec scores et impacts
5. ✅ **Analyse financière détaillée** avec ROI
6. ✅ **Recommandations enrichies** (contexte + actions + budget)
7. ✅ **Timeline visuelle**
8. ✅ **Matrice de priorisation**
9. ✅ **Scénario "ne rien faire"**

---

## 🚀 Prochaines Étapes

1. Créer les templates d'emails (HTML)
2. Créer le générateur de PDF (Python + ReportLab/WeasyPrint)
3. Créer le système d'envoi d'emails (SMTP/SendGrid)
4. Créer la logique de routage des notifications
5. Tester avec des cas réels (CBAM, inondation, conflit)
