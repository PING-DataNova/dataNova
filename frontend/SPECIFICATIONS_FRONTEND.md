# Spécifications Frontend - Hutchinson DataNova

**Version:** 1.0.0  
**Date:** 4 Février 2026  
**Application:** Plateforme de veille réglementaire et analyse des risques fournisseurs

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture technique](#2-architecture-technique)
3. [Pages et navigation](#3-pages-et-navigation)
4. [Composants réutilisables](#4-composants-réutilisables)
5. [Flux utilisateur](#5-flux-utilisateur)
6. [Cas de test recommandés](#6-cas-de-test-recommandés)
7. [Données de test](#7-données-de-test)
8. [Accessibilité](#8-accessibilité)

---

## 1. Vue d'ensemble

### 1.1 Objectif de l'application

DataNova est une plateforme de veille réglementaire permettant aux équipes Hutchinson de :
- Surveiller les risques réglementaires, climatiques et géopolitiques
- Analyser les risques liés aux fournisseurs
- Visualiser les menaces sur une carte géographique
- Gérer les accès utilisateurs (administration)

### 1.2 Utilisateurs cibles

| Rôle | Accès | Description |
|------|-------|-------------|
| **Analyste** | Dashboard, Analyse Fournisseur | Utilisateur standard, consulte et analyse les risques |
| **Manager** | Dashboard, Analyse Fournisseur | Supervision des analyses |
| **Administrateur** | Toutes les pages + Admin | Gestion des comptes utilisateurs |

### 1.3 Branding

- **Logo:** Hutchinson (fichier: `/public/hutchinson-logo.svg`)
- **Couleurs principales:**
  - Primaire: Lime (#A3E635 / `lime-400`)
  - Fond: Slate (#F8FAFC / `slate-50`)
  - Sidebar: Slate foncé (#0F172A / `slate-950`)
  - Texte: Slate (#0F172A / `slate-900`)
- **Typographie:** Font système (system-ui, sans-serif)
- **Style:** Moderne, coins très arrondis (`rounded-2xl`, `rounded-[2rem]`)

---

## 2. Architecture technique

### 2.1 Stack technologique

| Technologie | Version | Usage |
|-------------|---------|-------|
| React | 18.x | Framework UI |
| TypeScript | 5.x | Typage statique |
| Vite | 5.4.21 | Build tool |
| TailwindCSS | 3.x | Styling |
| Leaflet / react-leaflet | 1.9.4 / 4.2.1 | Cartes interactives |
| Recharts | 2.6.2 | Graphiques |

### 2.2 Structure des fichiers

```
frontend/src/
├── App.tsx                 # Routage principal
├── main.tsx                # Point d'entrée
├── types/                  # Définitions TypeScript
├── pages/                  # Pages principales
│   ├── Landing.tsx         # Page d'accueil publique
│   ├── Login.tsx           # Connexion
│   ├── Register.tsx        # Inscription
│   ├── Dashboard.tsx       # Tableau de bord principal
│   ├── SupplierAnalysis.tsx # Analyse fournisseur
│   ├── AdminPanel.tsx      # Administration
│   └── AgentDashboard.tsx  # Dashboard agent (legacy)
├── components/             # Composants réutilisables
│   ├── RiskMatrix.tsx      # Matrice de risques
│   ├── RiskTable.tsx       # Tableau des risques
│   ├── SupplierMap.tsx     # Carte des fournisseurs
│   └── NotificationCenter.tsx
├── data/                   # Données mock
│   └── mockImpacts.ts      # 18 risques de démonstration
├── services/               # Appels API
└── config/                 # Configuration
```

### 2.3 Configuration

| Variable | Valeur dev | Description |
|----------|------------|-------------|
| Port Frontend | 3001+ | Vite dev server |
| Port Backend | 8000 | API FastAPI |
| Mode Mock | `USE_MOCK_DATA = true` | Active les données de démo |

---

## 3. Pages et navigation

### 3.1 Flux de navigation

```
┌─────────────┐
│   Landing   │ (Page publique)
└──────┬──────┘
       │
       ├──────────────────┐
       ▼                  ▼
┌─────────────┐    ┌─────────────┐
│    Login    │    │  Register   │
└──────┬──────┘    └─────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│              Dashboard                   │
│  ┌─────────┬────────────┬─────────────┐ │
│  │Dashboard│Réglementations│Climat│Géo.│ │ (Onglets)
│  └─────────┴────────────┴─────────────┘ │
└──────┬──────────────────────────────────┘
       │
       ├──────────────────┬───────────────┐
       ▼                  ▼               ▼
┌─────────────┐    ┌─────────────┐ ┌─────────────┐
│  Supplier   │    │    Admin    │ │   Logout    │
│  Analysis   │    │   Panel     │ │             │
└─────────────┘    └─────────────┘ └─────────────┘
```

---

### 3.2 Page: Landing (`/`)

**Fichier:** `pages/Landing.tsx`

**Description:** Page d'accueil publique présentant la plateforme.

**Éléments UI:**
| Élément | Type | Action |
|---------|------|--------|
| Logo Hutchinson | Image | - |
| Titre "DataNova" | H1 | - |
| Description | Texte | - |
| Bouton "Se connecter" | Button primaire | → Login |
| Bouton "S'inscrire" | Button secondaire | → Register |

**Critères d'acceptation:**
- [ ] La page s'affiche sans authentification
- [ ] Les boutons redirigent correctement
- [ ] Le logo Hutchinson est visible

---

### 3.3 Page: Login (`/login`)

**Fichier:** `pages/Login.tsx`

**Description:** Formulaire de connexion utilisateur.

**Champs du formulaire:**
| Champ | Type | Requis | Validation |
|-------|------|--------|------------|
| Email | email | ✅ | Format email valide |
| Mot de passe | password | ✅ | Min 6 caractères |

**Compte de test:**
```
Email: khadidja2@hutchinson.com
Mot de passe: password123
```

**Actions:**
| Action | Résultat attendu |
|--------|------------------|
| Connexion réussie | Redirection → Dashboard |
| Connexion échouée | Message d'erreur affiché |
| Clic "S'inscrire" | Redirection → Register |
| Clic "Retour" | Redirection → Landing |

**Critères d'acceptation:**
- [ ] Validation des champs en temps réel
- [ ] Message d'erreur clair si échec
- [ ] Indicateur de chargement pendant la requête
- [ ] Persistance de session (localStorage)

---

### 3.4 Page: Register (`/register`)

**Fichier:** `pages/Register.tsx`

**Description:** Formulaire d'inscription nouvel utilisateur.

**Champs du formulaire:**
| Champ | Type | Requis | Validation |
|-------|------|--------|------------|
| Nom complet | text | ✅ | Min 2 caractères |
| Email | email | ✅ | Format @hutchinson.com recommandé |
| Mot de passe | password | ✅ | Min 6 caractères |
| Confirmation | password | ✅ | Doit correspondre |

**Critères d'acceptation:**
- [ ] Vérification que les mots de passe correspondent
- [ ] Message de succès après inscription
- [ ] Redirection vers Login après succès

---

### 3.5 Page: Dashboard (`/dashboard`)

**Fichier:** `pages/Dashboard.tsx`  
**Authentification:** ✅ Requise

**Description:** Tableau de bord principal avec 4 onglets.

#### 3.5.1 Structure générale

```
┌────────────────────────────────────────────────────┐
│ SIDEBAR (gauche)           │ CONTENU PRINCIPAL    │
│ ─────────────────          │ ─────────────────    │
│ [Logo Hutchinson]          │ [Header blanc]       │
│                            │ "Tableau de bord"    │
│ [Dashboard]     ← Onglets  │ [Recherche] [Notif]  │
│ [Réglementations]          │                      │
│ [Climat]                   │ [Contenu dynamique]  │
│ [Géopolitique]             │                      │
│                            │                      │
│ [Administration] ← Bouton  │                      │
│                            │                      │
│ [Utilisateur]              │                      │
│ [Logout]                   │                      │
└────────────────────────────────────────────────────┘
```

#### 3.5.2 Onglet: Dashboard

**Sections affichées:**

1. **Bandeau de bienvenue**
   - Texte: "Bienvenue, [Nom utilisateur]"
   - Sous-titre: "Analysez les risques de votre chaîne d'approvisionnement"
   - Bouton CTA: "Analyse Fournisseur" (vert lime, très visible)

2. **Notifications récentes**
   - Liste des 5 dernières notifications
   - Badge compteur "X non lues"
   - Icône par catégorie (Climat/Géopolitique/Réglementations)

3. **Accès rapide aux typologies**
   - 3 cartes cliquables:
     - Réglementations (orange)
     - Climat (vert)
     - Géopolitique (violet)

4. **Liste de tous les risques**
   - Affiche TOUS les risques de toutes catégories
   - **Options de tri:**
     - Par risque (Élevé → Faible ou Faible → Élevé)
     - Par date (Récent → Ancien ou Ancien → Récent)
   - Clic sur un risque → navigue vers l'onglet correspondant

**Critères d'acceptation:**
- [ ] Le nom de l'utilisateur s'affiche correctement
- [ ] Le bouton "Analyse Fournisseur" redirige vers la page d'analyse
- [ ] Les notifications en temps réel apparaissent (simulation)
- [ ] Le tri des risques fonctionne dans les 2 sens
- [ ] Le compteur de risques est correct

#### 3.5.3 Onglets: Réglementations / Climat / Géopolitique

**Sections communes:**

1. **Matrice Risque/Impact**
   - Grille 3x3 (Faible/Moyen/Élevé)
   - Axes: Risque (vertical) / Impact (horizontal)
   - Cellules cliquables → modal avec détails
   - Badge "X critiques" si risques élevé/fort

2. **Carte des fournisseurs**
   - Carte Leaflet interactive (style Voyager clair)
   - Marqueurs colorés selon niveau de risque:
     - 🔴 Rouge = Élevé (avec animation pulse)
     - 🟠 Orange = Moyen
     - 🟢 Vert = Faible
   - Clic sur marqueur → modal fournisseur

3. **Tableau des risques filtrés**
   - Liste des risques de la catégorie sélectionnée
   - Colonnes: Titre, Niveau, Modalité, Deadline

4. **Stats rapides**
   - 4 cartes: Risques actifs, Niveau d'urgence, Recommandations, Temps réponse

**Critères d'acceptation:**
- [ ] Chaque onglet filtre correctement les données
- [ ] La matrice affiche les bons compteurs par cellule
- [ ] La carte affiche les 6 sites Hutchinson
- [ ] Les marqueurs ont les bonnes couleurs
- [ ] Le modal s'ouvre au clic sur une cellule/marqueur

---

### 3.6 Page: Analyse Fournisseur (`/supplier-analysis`)

**Fichier:** `pages/SupplierAnalysis.tsx`  
**Authentification:** ✅ Requise

**Description:** Formulaire pour analyser les risques d'un fournisseur.

#### 3.6.1 Structure

```
┌─────────────────────────────────────────┐
│ [←] Analyse Fournisseur                 │ ← Header avec flèche retour
│     Évaluez les risques...              │
├─────────────────────────────────────────┤
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 🏢 Informations du fournisseur      │ │ Section 1
│ │    Nom*, Pays*, Ville, Lat, Lng     │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 📦 Matières fournies *              │ │ Section 2
│ │    [Tags] + [Ajouter]               │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 🏷️ Codes NC (douaniers)             │ │ Section 3
│ │    [Tags] + [Sélecteur]             │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ ⚡ Importance                        │ │ Section 4
│ │    [Standard] [Important] [Critique]│ │
│ │    Volume annuel (€)                │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [══════ ANALYSER LES RISQUES ══════]   │ ← Bouton submit
│                                         │
└─────────────────────────────────────────┘
```

#### 3.6.2 Champs du formulaire

| Champ | Type | Requis | Validation |
|-------|------|--------|------------|
| Nom du fournisseur | text | ✅ | Non vide |
| Pays | select | ✅ | Liste prédéfinie |
| Ville | text | ❌ | - |
| Latitude | number | ❌ | -90 à 90 |
| Longitude | number | ❌ | -180 à 180 |
| Matières | tags | ✅ | Au moins 1 |
| Codes NC | tags | ❌ | Format XXXX.XX |
| Criticité | radio | ❌ | Standard (défaut) |
| Volume annuel | number | ❌ | >= 0 |

#### 3.6.3 Pays disponibles

```
Allemagne, Belgique, Brésil, Chine, Espagne, États-Unis, 
France, Inde, Italie, Japon, Maroc, Mexique, Pologne, 
République tchèque, Roumanie, Royaume-Uni, Thaïlande, Tunisie, Turquie
```

#### 3.6.4 Matières suggérées

```
Caoutchouc naturel, Caoutchouc synthétique, Silicone,
Plastique, Métal, Textile, Composites, Adhésifs
```

#### 3.6.5 Codes NC courants

| Code | Description |
|------|-------------|
| 4001.10 | Latex de caoutchouc naturel |
| 4001.22 | Caoutchouc naturel TSNR |
| 4002.19 | Caoutchouc styrène-butadiène |
| 4002.20 | Caoutchouc butadiène |
| 3910.00 | Silicones |
| 3901.10 | Polyéthylène |
| 7326.90 | Articles en fer/acier |

**Critères d'acceptation:**
- [ ] Le formulaire valide les champs requis
- [ ] Les tags s'ajoutent/suppriment correctement
- [ ] Le message d'erreur s'affiche si formulaire incomplet
- [ ] Le bouton est désactivé si formulaire invalide
- [ ] L'animation de chargement apparaît pendant l'analyse
- [ ] La flèche retour ramène au Dashboard

---

### 3.7 Page: Administration (`/admin`)

**Fichier:** `pages/AdminPanel.tsx`  
**Authentification:** ✅ Requise  
**Rôle:** Visible pour tous (démo) / Prod: Admin uniquement

**Description:** Gestion des demandes de création de compte.

#### 3.7.1 Structure

```
┌─────────────────────────────────────────┐
│ [←] Administration                       │
│     Gestion des demandes d'accès        │
├─────────────────────────────────────────┤
│                                         │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│ │ 4        │ │ 1        │ │ 1        │ │ Stats
│ │En attente│ │ Approuvés│ │ Rejetés  │ │
│ └──────────┘ └──────────┘ └──────────┘ │
│                                         │
│ [En attente(4)] [Approuvés(1)] [Tous]  │ ← Filtres
│                                [🔍]    │ ← Recherche
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ [MD] Marie Dupont                   │ │
│ │     marie.dupont@hutchinson.com     │ │
│ │     Analyste | Supply Chain | 03/02 │ │
│ │                    [✓ Approuver] [✗]│ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ [PM] Pierre Martin                  │ │
│ │     ...                             │ │
│ └─────────────────────────────────────┘ │
│                                         │
└─────────────────────────────────────────┘
```

#### 3.7.2 Fonctionnalités

| Fonctionnalité | Description |
|----------------|-------------|
| Filtrer par statut | En attente / Approuvés / Rejetés / Tous |
| Rechercher | Par nom, email ou département |
| Approuver | Bouton vert → Modal confirmation → Statut "Approuvé" |
| Rejeter | Bouton rouge → Modal confirmation → Statut "Rejeté" |

#### 3.7.3 Données mock (6 utilisateurs)

| Nom | Email | Statut initial |
|-----|-------|----------------|
| Marie Dupont | marie.dupont@hutchinson.com | pending |
| Pierre Martin | pierre.martin@hutchinson.com | pending |
| Sophie Bernard | sophie.bernard@hutchinson.com | pending |
| Lucas Petit | lucas.petit@hutchinson.com | pending |
| Emma Leroy | emma.leroy@hutchinson.com | approved |
| Thomas Moreau | thomas.moreau@external.com | rejected |

**Critères d'acceptation:**
- [ ] Les compteurs se mettent à jour après action
- [ ] Le filtre fonctionne correctement
- [ ] La recherche filtre en temps réel
- [ ] Le modal de confirmation s'affiche
- [ ] Le statut change après confirmation

---

## 4. Composants réutilisables

### 4.1 RiskMatrix

**Fichier:** `components/RiskMatrix.tsx`

**Props:**
```typescript
interface RiskMatrixProps {
  items: RiskMatrixItem[];
  onCellClick?: (riskLevel: string, impactLevel: string, items: RiskMatrixItem[]) => void;
}
```

**Comportement:**
- Grille 3x3 avec axes Risque/Impact
- Labels: Faible / Moyen / Élevé (même terme pour les 2 axes)
- Couleurs des cellules selon danger (vert → jaune → orange → rouge)
- Compteur dans chaque cellule
- Cliquable si `onCellClick` fourni

### 4.2 SupplierMap

**Fichier:** `components/SupplierMap.tsx`

**Props:**
```typescript
interface SupplierMapProps {
  suppliers: SupplierLocation[];
  onSupplierClick?: (supplier: SupplierLocation) => void;
}
```

**Comportement:**
- Carte Leaflet avec tuiles CartoDB Voyager (clair)
- Zoom automatique pour inclure tous les marqueurs
- Marqueurs personnalisés avec couleur selon risque
- Animation pulse pour risques élevés
- Popup au survol avec nom du fournisseur

### 4.3 NotificationCenter

**Fichier:** `components/NotificationCenter.tsx`

**Comportement:**
- Icône cloche avec badge compteur
- Dropdown avec liste des notifications
- Marquer comme lu au clic

### 4.4 RiskTable

**Fichier:** `components/RiskTable.tsx`

**Colonnes:**
| Colonne | Description |
|---------|-------------|
| Risque | Titre du risque |
| Niveau | Badge coloré (critique/élevé/moyen/faible) |
| Modalité | Description courte |
| Deadline | Date limite |
| Recommandation | Action suggérée |

---

## 5. Flux utilisateur

### 5.1 Flux: Connexion et accès au Dashboard

```
1. Utilisateur arrive sur Landing
2. Clic "Se connecter"
3. Saisie email + mot de passe
4. Clic "Connexion"
   ├─ Si succès → Redirection Dashboard
   └─ Si échec → Message d'erreur
5. Dashboard s'affiche avec données chargées
```

### 5.2 Flux: Analyse d'un fournisseur

```
1. Depuis Dashboard, clic "Analyse Fournisseur"
2. Remplir formulaire:
   a. Nom du fournisseur
   b. Sélectionner pays
   c. Ajouter au moins 1 matière
   d. (Optionnel) Ajouter codes NC
   e. (Optionnel) Définir criticité
3. Clic "Analyser les risques"
4. Attendre résultat (loading)
5. Affichage page résultats
6. Retour Dashboard via flèche
```

### 5.3 Flux: Exploration des risques

```
1. Depuis Dashboard onglet principal
2. Voir liste "Tous les Risques"
3. Trier par risque ou par date
4. Clic sur un risque
5. Redirection vers onglet de la catégorie
6. Consultation matrice + carte + tableau
7. Clic cellule matrice → Modal détails
8. Clic marqueur carte → Modal fournisseur
```

### 5.4 Flux: Administration des comptes

```
1. Depuis Dashboard, clic "Administration" (sidebar)
2. Vue des demandes en attente
3. Filtrer/Rechercher si besoin
4. Clic "Approuver" sur une demande
5. Modal confirmation
6. Clic "Confirmer"
7. Demande passe en "Approuvé"
8. Compteurs mis à jour
```

---

## 6. Cas de test recommandés

### 6.1 Tests fonctionnels - Authentification

| ID | Cas de test | Données | Résultat attendu |
|----|-------------|---------|------------------|
| AUTH-01 | Connexion valide | khadidja2@hutchinson.com / password123 | Redirection Dashboard |
| AUTH-02 | Email invalide | test@test / password123 | Erreur "Format email invalide" |
| AUTH-03 | Mot de passe incorrect | khadidja2@hutchinson.com / wrongpass | Erreur "Identifiants incorrects" |
| AUTH-04 | Champs vides | (vide) | Bouton désactivé |
| AUTH-05 | Déconnexion | Clic Logout | Retour Landing, session supprimée |
| AUTH-06 | Persistance session | Rafraîchir page après login | Reste connecté |

### 6.2 Tests fonctionnels - Dashboard

| ID | Cas de test | Action | Résultat attendu |
|----|-------------|--------|------------------|
| DASH-01 | Affichage nom utilisateur | Login | "Bienvenue, [Nom]" affiché |
| DASH-02 | Navigation onglets | Clic sur chaque onglet | Contenu change, sidebar stable |
| DASH-03 | Tri risques par niveau | Clic "Par risque" puis inverser | Liste triée correctement |
| DASH-04 | Tri risques par date | Clic "Par date" puis inverser | Liste triée par date |
| DASH-05 | Clic carte typologie | Clic "Réglementations" | Onglet Réglementations activé |
| DASH-06 | Bouton Analyse Fournisseur | Clic | Page SupplierAnalysis s'ouvre |

### 6.3 Tests fonctionnels - Matrice de risques

| ID | Cas de test | Action | Résultat attendu |
|----|-------------|--------|------------------|
| MAT-01 | Affichage compteurs | Charger onglet | Chaque cellule affiche bon compte |
| MAT-02 | Clic cellule vide | Clic sur cellule à 0 | Rien ne se passe |
| MAT-03 | Clic cellule remplie | Clic sur cellule > 0 | Modal avec liste risques |
| MAT-04 | Fermer modal | Clic overlay ou bouton | Modal se ferme |
| MAT-05 | Badge critique | Si risques élevé/fort | Badge rouge "X critiques" visible |

### 6.4 Tests fonctionnels - Carte

| ID | Cas de test | Action | Résultat attendu |
|----|-------------|--------|------------------|
| MAP-01 | Chargement carte | Ouvrir onglet | Carte s'affiche avec tuiles |
| MAP-02 | Marqueurs visibles | Charger | 6 marqueurs Hutchinson visibles |
| MAP-03 | Couleurs marqueurs | Vérifier | Rouge/Orange/Vert selon risque |
| MAP-04 | Animation pulse | Risque élevé | Animation sur marqueurs rouges |
| MAP-05 | Clic marqueur | Clic | Modal fournisseur s'ouvre |
| MAP-06 | Zoom/Pan | Scroll/Drag | Carte interactive |

### 6.5 Tests fonctionnels - Analyse Fournisseur

| ID | Cas de test | Action | Résultat attendu |
|----|-------------|--------|------------------|
| SUP-01 | Formulaire vide | Tenter submit | Bouton désactivé, message validation |
| SUP-02 | Nom seul | Remplir nom | Bouton désactivé (pays + matière requis) |
| SUP-03 | Formulaire valide | Nom + Pays + 1 matière | Bouton activé |
| SUP-04 | Ajouter matière | Taper + Entrée ou clic Ajouter | Tag apparaît |
| SUP-05 | Supprimer matière | Clic × sur tag | Tag disparaît |
| SUP-06 | Sélection criticité | Clic radio | Radio sélectionné, style change |
| SUP-07 | Retour Dashboard | Clic flèche | Retour au Dashboard |

### 6.6 Tests fonctionnels - Administration

| ID | Cas de test | Action | Résultat attendu |
|----|-------------|--------|------------------|
| ADM-01 | Accès page | Clic Administration | Page Admin s'ouvre |
| ADM-02 | Compteurs initiaux | Charger | 4 pending, 1 approved, 1 rejected |
| ADM-03 | Filtre "En attente" | Clic onglet | 4 utilisateurs affichés |
| ADM-04 | Filtre "Approuvés" | Clic onglet | 1 utilisateur affiché |
| ADM-05 | Recherche nom | Taper "Marie" | Seule Marie Dupont visible |
| ADM-06 | Approuver demande | Clic Approuver → Confirmer | Statut passe à "Approuvé" |
| ADM-07 | Rejeter demande | Clic Rejeter → Confirmer | Statut passe à "Rejeté" |
| ADM-08 | Annuler action | Clic Annuler dans modal | Modal se ferme, pas de changement |

---

## 7. Données de test

### 7.1 Risques mock (18 entrées)

**Catégorie: Réglementations (8)**

| ID | Titre | Niveau Impact | Niveau Risque |
|----|-------|---------------|---------------|
| 1 | CSRD - Directive durabilité | eleve | eleve |
| 2 | EUDR - Déforestation | moyen | eleve |
| 3 | CBAM - Mécanisme carbone | eleve | moyen |
| 4 | REACh - Substances chimiques | moyen | moyen |
| 5 | RoHS - Substances dangereuses | faible | moyen |
| 6 | Taxonomie verte UE | moyen | faible |
| 7 | Directive batteries | faible | faible |
| 8 | Directive emballages | faible | faible |

**Catégorie: Climat (5)**

| ID | Titre | Niveau Impact | Niveau Risque |
|----|-------|---------------|---------------|
| 9 | Vagues de chaleur Asie Sud-Est | eleve | eleve |
| 10 | Inondations Europe Centrale | moyen | eleve |
| 11 | Sécheresse Ibérie | eleve | moyen |
| 12 | Typhons Pacifique | moyen | moyen |
| 13 | Gel tardif Europe Nord | faible | faible |

**Catégorie: Géopolitique (5)**

| ID | Titre | Niveau Impact | Niveau Risque |
|----|-------|---------------|---------------|
| 14 | Sanctions Russie | eleve | eleve |
| 15 | Tensions Taïwan | eleve | eleve |
| 16 | Instabilité Mer Rouge | moyen | eleve |
| 17 | Droits douane US-Chine | moyen | moyen |
| 18 | Embargo minéraux rares | faible | moyen |

### 7.2 Fournisseurs mock (6 sites Hutchinson)

| Nom | Pays | Ville | Lat | Lng | Risque |
|-----|------|-------|-----|-----|--------|
| Hutchinson Montargis | France | Montargis | 47.9969 | 2.7337 | moyen |
| Hutchinson Lodz | Pologne | Łódź | 51.7592 | 19.4560 | eleve |
| Hutchinson Celaya | Mexique | Celaya | 20.5167 | -100.8167 | moyen |
| Hutchinson Suzhou | Chine | Suzhou | 31.2989 | 120.5853 | eleve |
| Hutchinson Manila | Philippines | Manille | 14.5995 | 120.9842 | faible |
| Hutchinson São Paulo | Brésil | São Paulo | -23.5505 | -46.6333 | moyen |

---

## 8. Accessibilité

### 8.1 Recommandations implémentées

| Critère | Status | Notes |
|---------|--------|-------|
| Contraste couleurs | ✅ | Texte slate sur fond clair |
| Focus visible | ✅ | Outline sur éléments focusables |
| Labels formulaires | ✅ | Labels explicites |
| Textes alt images | ✅ | Logo avec alt |
| Navigation clavier | ⚠️ | Partiellement implémenté |
| Screen reader | ⚠️ | À améliorer |

### 8.2 Améliorations suggérées

1. Ajouter `aria-label` sur les boutons icônes
2. Ajouter `role="alert"` sur les messages d'erreur
3. Améliorer le focus trap dans les modals
4. Ajouter des skip links

---

## Annexes

### A. URLs de développement

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3001 (ou 3002, 3003...) |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

### B. Commandes utiles

```bash
# Démarrer le frontend
cd frontend && npm run dev

# Démarrer le backend
cd backend && source .venv/bin/activate && uvicorn src.api.main:app --port 8000

# Lancer les tests Playwright
cd frontend && npx playwright test
```

### C. Contact

Pour toute question sur ces spécifications, contacter l'équipe de développement.

---

*Document généré le 4 Février 2026*
