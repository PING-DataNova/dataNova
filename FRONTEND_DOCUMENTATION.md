# 📱 Frontend - Plateforme Veille Réglementaire Hutchinson SA

## 🎯 Résumé du Projet

Application web développée pour aider l'équipe juridique et les décideurs de Hutchinson SA à gérer les réglementations européennes détectées automatiquement par des agents d'intelligence artificielle.

**Objectif** : Créer deux interfaces distinctes pour deux types d'utilisateurs différents
- **Interface Juridique** : Pour valider ou rejeter les réglementations détectées
- **Dashboard Décideur** : Pour consulter les statistiques et indicateurs clés

---

## 🛠️ Technologies Utilisées

Nous avons construit l'application avec des technologies modernes pour garantir performance et maintenabilité :

- **React 18** : Bibliothèque JavaScript pour construire l'interface utilisateur
- **TypeScript** : Pour un code plus robuste et sécurisé avec typage fort
- **Vite** : Outil de build ultra-rapide pour le développement
- **React Router DOM** : Gestion de la navigation entre les pages
- **Lucide React** : Bibliothèque d'icônes modernes
- **CSS custom** : Styles personnalisés pour le thème rouge et noir

**Pourquoi TypeScript ?**
- Détection des erreurs avant l'exécution
- Autocomplétion intelligente dans l'éditeur
- Code plus facile à maintenir et comprendre
- Documentation automatique des interfaces

---

## 📁 Organisation du Code

Le projet est organisé de manière claire avec des dossiers séparés pour chaque type de fichier :

- **pages/** : Les 3 pages principales (Login, Interface Juridique, Dashboard)
- **components/** : Composants réutilisables (Sidebar, Cartes, Filtres)
- **data/** : Données de test pour le développement
- **utils/** : Fonctions utilitaires (export JSON)

Cette organisation permet de retrouver facilement chaque partie du code.

---

## 👥 Ce Qui a Été Développé

### 1️⃣ Interface pour l'Équipe Juridique

**Problème résolu** : L'équipe juridique avait besoin d'un outil pour valider rapidement les réglementations détectées par l'IA.

**Solution créée** : Une interface complète avec :

#### Système de Recherche et Filtrage Avancé
Nous avons développé un système de filtres puissant permettant de :
- **Rechercher** dans le texte des réglementations
- **Filtrer par date** : voir les réglementations de la dernière semaine, du dernier mois, ou période personnalisée
- **Filtrer par type** : Réglement, Directive ou Décision
- **Filtrer par codes NC** : codes douaniers spécifiques (2804, 2901, 4001...)
- **Filtrer par confiance IA** : slider pour ajuster le niveau de confiance minimum/maximum (0-100%)

**Logique technique** : Tous ces filtres fonctionnent ensemble et sont appliqués en temps réel sur la liste des réglementations.

#### Actions de Validation
Chaque réglementation peut être :
- **Validée** avec un clic → marquée comme pertinente
- **Rejetée** avec un clic → marquée comme non pertinente
- Ces actions mettent à jour immédiatement l'affichage

#### Affichage des Réglementations
Chaque réglementation est affichée dans une carte visuelle contenant :
- Titre et description
- Source (EUR-Lex)
- Type de document
- Dates importantes (publication et application)
- Codes NC concernés
- **Badge de confiance IA** : coloré selon le niveau (vert = haute confiance, orange = moyenne)
- Statut actuel (en attente, validé, rejeté)

#### Système d'Export JSON
Une fonctionnalité importante pour transmettre les données validées :
- **Télécharger** : génère un fichier JSON avec toutes les réglementations validées
- **Copier** : copie le JSON dans le presse-papier
- **Console** : affiche le JSON dans la console du navigateur

Le format JSON est standardisé et compatible avec le backend pour faciliter l'intégration.

---

### 2️⃣ Dashboard pour les Décideurs

**Problème résolu** : La direction a besoin d'une vue d'ensemble rapide des réglementations sans entrer dans les détails.

**Solution créée** : Un tableau de bord avec indicateurs clés.

#### Indicateurs Statistiques (KPIs)
Affichage immédiat de 4 indicateurs principaux :
1. **Total des réglementations** suivies
2. **Pourcentage de traitement** : combien sont en cours vs validées
3. **Risques élevés** : nombre de réglementations critiques
4. **Deadlines** : réglementations à appliquer dans les 6 prochains mois

**Logique** : Ces chiffres donnent une vision rapide de la situation sans avoir à consulter les détails.

#### Zones de Graphiques
Deux emplacements prévus pour des graphiques futurs :
- Répartition temporelle des réglementations
- Répartition par processus métier

> **Note** : Actuellement affichés en placeholder, seront connectés aux vraies données quand le backend sera prêt.

#### Page Profil Utilisateur
Navigation possible vers une page profil qui affiche :
- Informations personnelles (nom, email, département)
- Permissions de l'utilisateur
- Statistiques d'utilisation personnelles (connexions, exports, consultations)

**Logique** : Le système bascule entre vue Dashboard et vue Profil selon l'onglet cliqué dans la sidebar.

---

### 3️⃣ Système d'Authentification

**Problème résolu** : Séparer l'accès selon le type d'utilisateur.

**Solution créée** : Une page de connexion intelligente.

#### Connexion Simple
- Formulaire avec email et mot de passe
- Bouton pour afficher/masquer le mot de passe
- Messages d'erreur clairs en cas de problème

#### Routage Automatique
**Logique intelligente** basée sur l'email :
- Si l'email contient "juriste" ou "legal" → redirige vers l'interface juridique
- Si l'email contient "decideur" ou "decision" → redirige vers le dashboard

Exemples :
- `juriste@hutchinson.com` → Interface de validation
- `decideur@hutchinson.com` → Dashboard statistiques

Cette logique permet de tester facilement les deux interfaces pendant le développement.

---

## 🎨 Choix de Design

### Identité Visuelle
Nous avons créé un thème cohérent pour toute l'application :

**Couleurs principales** :
- **Rouge** (#dc2626) : Couleur primaire, utilisée pour les éléments importants
- **Noir** (#000000) : Fond de la sidebar et textes principaux
- **Gris foncé** (#1a1a1a) : Dégradés et variations

**Couleurs de statut** :
- Vert : Validation, succès, haute confiance
- Orange : Avertissement, confiance moyenne
- Rouge : Rejet, erreur, attention requise

**Pourquoi ces choix ?**
- Contraste fort pour une lecture facile
- Identité visuelle professionnelle
- Cohérence sur toutes les pages

### Design Responsive
L'application s'adapte automatiquement aux différentes tailles d'écran :
- **Desktop** : Layout complet avec sidebar visible
- **Tablette** : Layout adapté
- **Mobile** : Sidebar masquée par défaut

### Composants Visuels
Nous avons créé des composants réutilisables :
- **Cartes de réglementation** : Design uniforme pour chaque réglementation
- **Panel de filtres** : Système d'accordéon pour gagner de l'espace
- **Badges colorés** : Indication visuelle du niveau de confiance IA
- **Sidebar** : Navigation fixe sur le côté gauche

---

## 🔌 Connexion avec le Backend

### Préparation pour l'API
Nous avons préparé l'application pour se connecter au backend (FastAPI) développé par l'équipe.

**Endpoints prévus** :
- **Authentification** : Login/logout
- **Liste des réglementations** : Avec tous les filtres
- **Actions** : Validation et rejet
- **Export** : Génération du JSON
- **Dashboard** : Récupération des statistiques

### Système de Mock Data
Pour développer sans attendre le backend, nous avons créé un système de données de test :
- 20+ réglementations fictives mais réalistes
- Simulation des appels API
- Format identique à ce que retournera le vrai backend

**Avantage** : Permet de développer et tester l'interface indépendamment du backend.

### Format JSON Standard
Nous avons défini un format JSON standardisé pour l'export des réglementations validées, compatible avec le backend. Ce format garantit que les données peuvent être facilement échangées entre frontend et backend.

---

## 📊 Logique de Fonctionnement

### Flux de Travail Utilisateur

**Pour l'équipe juridique** :
1. Connexion avec email juridique
2. Affichage automatique de toutes les réglementations en attente
3. Application optionnelle de filtres (date, type, NC, confiance)
4. Consultation détaillée de chaque réglementation
5. Décision : Valider ou Rejeter
6. Export des réglementations validées en JSON

**Pour les décideurs** :
1. Connexion avec email décideur
2. Affichage automatique du dashboard avec KPIs
3. Consultation des statistiques
4. Navigation vers profil pour infos personnelles
5. Export optionnel en PDF

### Gestion des États
L'application gère plusieurs états :
- **État de connexion** : Utilisateur connecté ou non
- **État des filtres** : Filtres actifs ou non
- **État des données** : Chargement, succès, erreur
- **État de navigation** : Page active (dashboard ou profil)

Ces états sont gérés avec React pour mettre à jour l'interface automatiquement.

---

## 🚀 Utilisation de l'Application

### Démarrage pour le Développement

1. **Installation des dépendances** :
   ```bash
   npm install
   ```

2. **Lancement du serveur de développement** :
   ```bash
   npm run dev
   ```

3. **Accès à l'application** :
   Ouvrir le navigateur sur : **http://localhost:3005**

### Emails de Test
Pour tester les deux interfaces :
- `juriste@hutchinson.com` → Interface de validation
- `decideur@hutchinson.com` → Dashboard statistiques

Mot de passe : n'importe quoi (en mode mock)

---

## ✅ Fonctionnalités Implémentées

### Interface Juridique ✓
- [x] Liste complète des réglementations
- [x] Recherche textuelle instantanée
- [x] Filtres avancés (4 types de filtres combinables)
- [x] Boutons Valider/Rejeter fonctionnels
- [x] Export JSON (3 méthodes : télécharger, copier, console)
- [x] Design responsive avec sidebar
- [x] Badges colorés selon confiance IA

### Dashboard Décideur ✓
- [x] 4 indicateurs KPIs affichés
- [x] Indicateurs de risques et deadlines
- [x] Navigation entre Dashboard et Profil
- [x] Page profil avec statistiques utilisateur
- [x] Placeholders pour graphiques futurs
- [x] Bouton export PDF (UI prêt, fonctionnalité à connecter)

### Authentification ✓
- [x] Page de connexion avec email/password
- [x] Affichage/masquage du mot de passe
- [x] Routage automatique selon le type d'utilisateur
- [x] Gestion de session
- [x] Bouton déconnexion

### Design ✓
- [x] Thème rouge et noir uniforme
- [x] Interface responsive (mobile/tablette/desktop)
- [x] Animations et transitions fluides
- [x] Icônes modernes (Lucide React)

---

## 🚧 Prochaines Étapes

### À court terme (nécessite backend)
- Connecter les vraies API backend
- Implémenter l'authentification JWT
- Remplacer les données mock par les vraies données
- Tester l'intégration complète

### À moyen terme
- Ajouter les graphiques interactifs (Chart.js)
- Implémenter l'export PDF fonctionnel
- Ajouter les notifications temps réel
- Historique des actions utilisateur

### À long terme
- Interface d'administration
- Mode multi-langue (FR/EN)
- Mode sombre optionnel
- Application mobile (PWA)

---

## 🎯 Exemples d'Utilisation

### Scénario 1 : Juriste valide une réglementation CBAM

1. Connexion avec `juriste@hutchinson.com`
2. Affichage de 50 réglementations en attente
3. Application des filtres :
   - Date : 30 derniers jours
   - Type : Réglement
   - Code NC : 4001 (caoutchouc)
   - Confiance IA : > 80%
4. Résultat : 5 réglementations correspondent
5. Lecture de "Regulation (EU) 2023/956 - CBAM"
6. Clic sur "Valider" → badge passe au vert
7. Clic sur "Export JSON" → téléchargement du fichier
8. Fichier contient les 12 réglementations validées aujourd'hui

### Scénario 2 : Décideur consulte les KPIs

1. Connexion avec `decideur@hutchinson.com`
2. Dashboard s'affiche immédiatement
3. Vue d'ensemble :
   - 123 réglementations suivies
   - 78% en cours de validation
   - 15 risques élevés
   - 7 deadlines critiques dans 6 mois
4. Clic sur "Profil" dans sidebar
5. Affichage des infos personnelles :
   - 47 connexions ce mois
   - 23 exports PDF
   - 156 réglementations consultées
6. Retour au Dashboard
7. Clic sur "Export PDF" → génération du rapport

---

## 📁 Fichiers Importants

### Documentation Complémentaire
- **API Documentation** : Voir `backend_dataNova/API_DOCUMENTATION.md`
  - Tous les endpoints disponibles
  - Formats de requêtes/réponses
  - Gestion des erreurs
  - Authentification

### Code Source Principal
- **LoginPage.tsx** : Page de connexion
- **LegalTeamPage.tsx** : Interface juridique complète
- **DecisionDashboard.tsx** : Dashboard + page profil
- **AdvancedFilters.tsx** : Système de filtres
- **exportData.ts** : Logique d'export JSON
- **mockData.ts** : Données de test

---

## 👥 Équipe et Contacts

**Développement Frontend** : Goddy  
**Équipe Backend** : Khadidja, Willy  
**Coordination** : Nora

---

## 📄 Informations Projet

**Nom du projet** : Le Détective - Plateforme de Veille Réglementaire  
**Client** : Hutchinson SA  
**Version** : 1.0.0  
**Date** : Janvier 2026  

---

## 📌 Points Clés à Retenir

✅ **Deux interfaces distinctes** selon le profil utilisateur (juridique/décideur)  
✅ **Filtres avancés** pour faciliter la recherche des réglementations  
✅ **Export JSON standardisé** compatible avec le backend  
✅ **Design responsive** rouge et noir  
✅ **Données de test (mock)** permettant le développement sans backend  
✅ **Prêt pour l'intégration API** avec le backend FastAPI  

---

**Dernière mise à jour** : 16 Janvier 2026
