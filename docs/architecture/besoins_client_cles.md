# Besoins Client Hutchinson - Points Clés de la Transcription

## 🎯 Référence : Prewave
- Le client veut une solution **similaire à Prewave**
- Prewave fait : scruter toute la documentation + remonter dans les fournisseurs + croiser événements avec base fournisseur + mapping avec niveau de risque + recommandations

## 📋 Deux Priorités Principales

### Priorité 1 : Monitoring Réglementaire
**Objectif** : Monitorer, connecter les infos sur les risques réglementaires et les projeter sur l'entreprise
- Exemple : "Il y a une réglementation en Tunisie, est-ce qu'on a un site en Tunisie, qu'est-ce qui est conservé ?"
- Automatiser la collecte, analyser la pertinence, mettre au contexte de l'entreprise
- Intégrer une validation humaine

### Priorité 2 : Projection des Risques (comme Prewave)
**Objectif** : Croiser les événements (réglementaires, climatiques, géopolitiques) avec les fournisseurs
- Scanner les fournisseurs
- Superposer les risques sur les fournisseurs
- Détecter les fournisseurs concernés
- Vérifier : double-source ? criticité ? impact supply chain ?

## 📊 3 Types de Risques à Traiter

### 1. Risques Réglementaires
- Réglementations européennes (CBAM, CRCD, etc.)
- Réglementations nationales/locales
- Sources : EUR-Lex, JO, sites officiels

### 2. Risques Climatiques
- Événements météo (inondations, tempêtes, etc.)
- Forecast météo (3-5 jours à l'avance)
- Sources : APIs météo, sites de confiance

### 3. Risques Géopolitiques
- Tensions géopolitiques
- Conflits, sanctions
- Sources : sites publics, ministère intérieur, etc.

## 🔄 Flux de Travail Attendu

1. **Collecte automatique** des données (web scraping, APIs)
2. **Structuration** des informations
3. **Croisement** avec base fournisseur OU base Hutchinson
4. **Analyse de risque** avec recommandations
5. **Système de suggestion** et alertes

## 🎨 Vision Système End-to-End

**Important** : Le client veut un système complet de bout en bout
- Collecte → Stockage → Analyse → IA → Suggestion → Interface utilisateur
- Système **évolutif** : on peut le reprendre en interne et l'industrialiser
- Système **paramétrable** : 
  - Typologies de risques configurables (réglementaire, climatique, géopolitique)
  - Sources configurables (site web, API)
  - Catégories et sources définies par paramétrage JSON

## 📍 Projection Géographique

**Données nécessaires** :
- 80-90 sites Hutchinson avec adresse et infos
- Base fournisseurs avec caractéristiques, adresse, taille, localisation, type de matériaux, risque

**Analyse** :
- Analyser systématiquement par rapport à la localisation
- Analyser par rapport à la spécificité de chaque site
- Ressortir analyse des données et système de suggestion

## 🚀 Approche Développement

- Livrable courant février
- Phase d'industrialisation chez Hutchinson ensuite
- Système doit être **facilement évolutif**
- Toutes les briques doivent être présentes dans l'architecture
- Peut faire des hypothèses sur certains scénarios
- Application évolutive qu'on peut compléter et industrialiser

## ⚠️ Ce qui Manque (selon le client)

- La **projection des risques** réglementaires, climatiques, géopolitiques
- Le **croisement automatique** avec les sites et fournisseurs
- L'**analyse de criticité** (double-source, impact supply chain)
- Les **recommandations** basées sur l'analyse

## ✅ Ce qui est OK

- Collecte et identification de facilité de travail (base du hackathon)
- Analyse de pertinence
- Validation humaine
- Synthèses de recommandations
