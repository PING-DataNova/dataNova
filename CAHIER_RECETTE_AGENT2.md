# CAHIER DE RECETTE - AGENT 2

Plateforme de veille réglementaire durable

**Projet** : Plateforme de veille réglementaire durable  
**Module** : Agent 2 - Analyse d'impact  
**Responsable** : Dev 4  
**Date** : 26/01/2026  
**Version** : 1.0

## 1. CONTEXTE ET PÉRIMÈTRE

### 1.1 Objectif de la recette

Valider le fonctionnement complet du workflow de veille réglementaire, de la collecte à l'analyse d'impact :
- Agent 1A : Collecte de documents (EUR-Lex)
- Agent 1B : Analyse de pertinence
- Interface Juriste : Validation humaine
- Agent 2 : Analyse d'impact détaillée
- Dashboard Décideur : Visualisation des impacts

### 1.2 Périmètre fonctionnel

#### Fonctionnalités couvertes
- Connexion utilisateur (juriste / décideur)
- Liste des réglementations par statut
- Validation/Rejet/À revoir des analyses
- Génération d'analyses d'impact (Agent 2)
- Calcul des métriques qualitatives
- Dashboard décideur avec indicateurs

#### Hors périmètre
- Agent 1A (collecte automatique)
- Envoi de notifications emails
- Export PDF avancé
- Gestion des utilisateurs

---

## 2. ENVIRONNEMENT DE TEST

### 2.1 Prérequis techniques

| Élément | Configuration requise |
|---------|----------------------|
| **Frontend** | React + Vite (port 3000) |
| **Backend** | Python 3.11+ avec FastAPI |
| **Base de données** | SQLite locale |
| **LLM** | Google Gemini 2.5 Flash |
| **Navigateur** | Chrome/Edge (dernière version) |

### 2.2 Données de test

#### Utilisateurs de test

Juriste
Email : juriste@hutchinson.com
Rôle : Validation des réglementations
Accès : Interface juridique

Décideur
Email : decideur@hutchinson.com
Rôle : Visualisation des impacts
Accès : Dashboard décideur

#### Jeux de données

Réglementations de test :

1. Règlement sur les produits biocides (EU) 528/2012
   Type : CBAM
   Codes NC : 4016, 4009
   Statut initial : EN ATTENTE

2. Directive protection travailleurs (98/24/CE)
   Type : EUDR
   Codes NC : 7606
   Statut initial : EN ATTENTE

3. Règlement REACH sur substances chimiques
   Type : REACH
   Codes NC : 3824
   Statut initial : EN ATTENTE

4. Règlement CSRD reporting durabilité
   Type : CSRD
   Codes NC : N/A
   Statut initial : EN ATTENTE

### 2.3 État initial de la base de données

Documents (Agent 1A)
4 documents avec workflow_status = 'raw'

Analyses (Agent 1B)
4 analyses avec validation_status = 'pending'

ImpactAssessments
0 enregistrements (vide au démarrage)

CompanyProcesses
1 profil Hutchinson avec :
- 2 fournisseurs (CN, DE)
- 2 produits (NC 4016, 4009)
- 2 flux import/export

---

## 3. SCÉNARIOS DE TEST DÉTAILLÉS

---

## SCÉNARIO 1 : WORKFLOW COMPLET - VALIDATION SIMPLE

**Objectif** : Tester le parcours nominal d'une réglementation de la validation à l'analyse d'impact

**Acteurs** : Juriste + Agent 2 + Décideur

**Durée estimée** : 15 minutes

---

### ÉTAPE 1.1 : Connexion Interface Juriste

**Action** :
1. Ouvrir navigateur → `http://localhost:3000`
2. Saisir email : `juriste@hutchinson.com`
3. Saisir mot de passe : `****`
4. Cliquer sur **"Connexion"**

**Résultat attendu** :
- Redirection vers interface juridique
- Message de bienvenue : "Juriste Hutchinson"
- Sidebar visible avec :
  - Réglementations (badge rouge "2")
  - À revoir (badge orange "1")
  - Validées (badge vert "1")
  - Rejetées
- Onglet "Réglementations" actif par défaut

**Critères de validation** :
□ Connexion réussie en < 2 secondes  
□ Tous les éléments d'interface affichés  
□ Nombre de réglementations en attente correct

---

### ÉTAPE 1.2 : Consultation de la liste "En attente"

**Action** :
1. Observer la page principale
2. Vérifier le nombre total : "4 réglementations au total"
3. Identifier la première réglementation :
   - **"Règlement sur les produits biocides (EU) 528/2012"**
   - Statut : **EN ATTENTE** (pastille orange)

**Résultat attendu** :
- Liste affichée avec 4 cartes de réglementations
- Chaque carte contient :
  - Titre de la réglementation
  - Référence (EU 528/2012)
  - Description courte
  - Badge de statut "EN ATTENTE"
  - 3 boutons : Valider | Rejeter | À revoir
- Message d'erreur backend visible : "Mode démo - Backend non connecté"

**Critères de validation** :
□ 4 cartes visibles  
□ Informations complètes sur chaque carte  
□ Boutons d'action cliquables

---

### ÉTAPE 1.3 : Validation de la réglementation biocides

**Action** :
1. Sur la carte **"Règlement biocides (EU) 528/2012"**
2. Cliquer sur le bouton **"Valider"** (vert)
3. Observer l'animation de la carte
4. Attendre la mise à jour (1-2 secondes)

**Résultat attendu** :
- Animation de sortie de la carte (slide out)
- Carte disparaît de la liste "En attente"
- Compteur mis à jour : "3 réglementations au total"
- Badge sidebar "Validées" incrémenté : 2 vers 3
- Badge sidebar "Réglementations" décrémenté : 2 vers 1

**Vérification base de données** :
Vérifier que le champ validation_status dans la table analyses est 'approved'
Vérifier que le champ workflow_status dans la table documents est 'validated'

**Critères de validation** :
□ Carte supprimée de la vue  
□ Compteurs mis à jour  
□ Status DB = 'approved'  
□ Temps de réponse < 3 secondes

---

### ÉTAPE 1.4 : Vérification onglet "Validées"

**Action** :
1. Cliquer sur **"Validées"** dans la sidebar (badge vert "3")
2. Observer la liste des réglementations validées
3. Rechercher **"Règlement biocides"**

**Résultat attendu** :
- Vue change vers "Réglementations validées"
- Sous-titre : "Validées par l'équipe juridique"
- 3 cartes affichées
- Carte "Règlement biocides" présente avec :
  - Badge "VALIDÉE" (vert)
  - Icône CheckCircle verte
  - Aucun bouton d'action (désactivés post-validation)
- Date de validation affichée

**Critères de validation** :
□ Réglementation visible dans "Validées"  
□ Badge statut correct  
□ Boutons désactivés  
□ Métadonnées de validation affichées

---

### ÉTAPE 1.5 : Déclenchement Agent 2 (Analyse d'impact)

**Action** :
1. Ouvrir terminal backend
2. Exécuter :
   ```bash
   cd c:\Users\Utilisateur\dataNova
   python -m src.agent_2.agent
   ```
3. Observer les logs de l'agent

**Résultat attendu - Logs Agent 2** :
L'agent doit afficher son initialisation avec le LLM Gemini 2.5 Flash et confirmer le chargement de 3 outils.
Il doit trouver 3 analyses approuvées et traiter le Règlement biocides (EU) 528/2012.
Pour cette réglementation, l'agent charge les données Hutchinson (2 fournisseurs CN et DE, 2 produits NC 4016 et 4009).
L'agent identifie que les 2 produits sont impactés.
Il calcule les métriques : risque fiscal, niveau élevé, modalité certificat, deadline 12-2025.
Un impact assessment est créé et sauvegardé avec succès.

**Vérification base de données** :
Vérifier dans la table impact_assessments qu'un enregistrement a été créé pour le règlement biocides.
Les champs attendus sont : risk_main='fiscal', impact_level='eleve', modality='certificat', deadline='12-2025'
Un champ recommendation doit contenir du texte et created_at doit avoir la date du jour.

**Critères de validation** :
□ Agent 2 détecte 3 analyses approuvées  
□ Matching produits correct (2/2)  
□ Métriques générées conformes  
□ ImpactAssessment créé en DB  
□ Pas d'erreurs dans les logs  
□ Temps d'exécution < 30 secondes

---

### ÉTAPE 1.6 : Visualisation Dashboard Décideur

**Action** :
1. Se déconnecter de l'interface juriste
2. Se connecter avec : `decideur@hutchinson.com`
3. Accéder au Dashboard

**Résultat attendu - Indicateurs clés** :
L'indicateur "Réglementations suivies" doit afficher 123.
Le ratio "En cours vs Validées" doit être 78% / 22%.
L'indicateur "Risques élevés détectés" doit passer de 15 à 16 après l'exécution d'Agent 2.
L'indicateur "Deadlines critiques" doit afficher 7.

**Vérification graphiques** :
- Graphique "Répartition par date d'application"
  - Nouvelle barre pour "12-2025" (deadline biocides)
- Graphique "Répartition par processus"
  - Catégorie "Risques fiscaux" incrémentée

**Critères de validation** :
□ Indicateur "Risques élevés" = 16  
□ Graphiques mis à jour  
□ Pas d'erreur d'affichage  
□ Export PDF fonctionnel

---

### ÉTAPE 1.7 : Vérification impact financier (optionnel)

**Action** :
1. Cliquer sur la carte "Risques élevés détectés"
2. Voir détail de la nouvelle réglementation

**Résultat attendu** :
La page de détail doit afficher le titre du règlement biocides.
Les informations principales doivent être : Impact principal FISCAL, Niveau d'impact ÉLEVÉ, Modalité CERTIFICAT, Échéance 12-2025.
Les détails doivent mentionner les taxes sur imports et les codes NC 4016 et 4009.
Les fournisseurs concernés doivent être listés.
Les recommandations doivent inclure la certification de conformité et le budget taxes avec des actions prioritaires.

**Critères de validation** :
□ Détails complets affichés  
□ Métriques qualitatives correctes  
□ Recommandations exploitables  
□ Codes NC alignés avec profil Hutchinson

---

## RÉSULTATS SCÉNARIO 1

| Étape | Attendu | Résultat | Statut | Commentaires |
|-------|---------|----------|--------|--------------|
| 1.1 Connexion juriste | Accès interface | | ☐ | |
| 1.2 Liste en attente | 4 réglementations | | ☐ | |
| 1.3 Validation | Carte supprimée | | ☐ | |
| 1.4 Onglet validées | Réglementation visible | | ☐ | |
| 1.5 Agent 2 | Impact créé | | ☐ | |
| 1.6 Dashboard | Indicateurs mis à jour | | ☐ | |
| 1.7 Détail impact | Infos complètes | | ☐ | |

**Durée réelle** : ___ minutes  
**Anomalies détectées** : ___  
**Bloquant** : ☐ Oui ☐ Non

---RÉSULTATS SCÉNARIO 1

| Étape | Attendu | Résultat | Statut | Commentaires |
|-------|---------|----------|--------|--------------|
| 1.1 Connexion juriste | Accès interface | | [ ] | |
| 1.2 Liste en attente | 4 réglementations | | [ ] | |
| 1.3 Validation | Carte supprimée | | [ ] | |
| 1.4 Onglet validées | Réglementation visible | | [ ] | |
| 1.5 Agent 2 | Impact créé | | [ ] | |
| 1.6 Dashboard | Indicateurs mis à jour | | [ ] | |
| 1.7 Détail impact | Infos complètes | | [ ] | |

**Durée réelle** : ___ minutes  
**Anomalies détectées** : ___  
**Bloquant** : [ ] Oui [ ] Non

---

## SCÉNARIO 2 : REJET ET RÉVISION - WORKFLOW ALTERNATIF

**Objectif** : Tester les parcours de rejet et de mise en révision

**Acteurs** : Juriste + Agent 2

**Durée estimée** : 12 minutes

---

### ÉTAPE 2.1 : Rejet d'une réglementation

**Action** :
1. Interface juriste connectée
2. Onglet "Réglementations" actif
3. Sur la carte **"Directive protection travailleurs (98/24/CE)"**
4. Cliquer sur **"Rejeter"** (rouge)
5. Modal de confirmation apparaît avec champ "Raison du rejet"
6. Saisir raison : "Non applicable - Pas d'exposition chimique"
7. Cliquer **"Confirmer le rejet"**

**Résultat attendu** :
- Modal se ferme
- Animation de sortie de la carte
- Carte disparaît de "Réglementations"
- Badge "Rejetées" incrémenté : 0 vers 1
- Notification temporaire : "Réglementation rejetée avec succès"

**Vérification base de données** :
Dans la table analyses, vérifier que validation_status est 'rejected'.
Le champ validation_comment doit contenir "Non applicable - Pas d'exposition chimique".
Les champs validated_at et validated_by doivent être renseignés.

**Critères de validation** :
□ Modal de confirmation affichée  
□ Commentaire obligatoire  
□ Carte supprimée après confirmation  
□ Badge mis à jour  
□ Status DB = 'rejected'

---

### ÉTAPE 2.2 : Vérification onglet "Rejetées"

**Action** :
1. Cliquer sur **"Rejetées"** dans la sidebar
2. Observer la liste

**Résultat attendu** :
- Vue "Réglementations rejetées"
- 1 carte affichée : "Directive protection travailleurs"
- Badge "REJETÉE" (rouge)
- Icône XCircle rouge
- Commentaire de rejet visible avec motif, auteur et date
- Boutons d'action désactivés

**Critères de validation** :
□ Réglementation dans onglet correct  
□ Métadonnées complètes  
□ Commentaire affiché  
□ Historique de validation visible

### ÉTAPE 2.3 : Mise en révision d'une réglementation

**Action** :
1. Retour onglet "Réglementations"
2. Sur la carte **"Règlement REACH substances chimiques"**
3. Cliquer sur **"À revoir"** (orange)
4. Modal de commentaire apparaît
5. Saisir : "Nécessite avis service R&D sur substances concernées"
6. Cliquer **"Confirmer"**

**Résultat attendu** :
- Carte passe dans onglet "À revoir"
- Badge sidebar "À revoir" : 1 vers 2
- Badge "Réglementations" : 3 vers 2
- Animation de changement de statut

**Vérification base de données** :
Dans la table analyses, vérifier que validation_status est 'to-review'.
Le champ validation_comment doit contenir le texte saisi sur l'avis R&D.

**Critères de validation** :
□ Carte déplacée vers "À revoir"  
□ Commentaire sauvegardé  
□ Badges sidebar corrects  
□ Status DB = 'to-review'

---

### ÉTAPE 2.4 : Consultation onglet "À revoir"

**Action** :
1. Cliquer sur **"À revoir"** (badge orange "2")
2. Observer la liste

**Résultat attendu** :
- Vue "Réglementations à revoir"
- 2 cartes affichées :
  - "Règlement REACH" (nouvellement ajouté)
  - "Règlement CSRD" (existant)
- Badge "À REVOIR" (orange)
- Icône AlertCircle orange
- Boutons d'action actifs (peut encore valider/rejeter)
- Commentaire visible

**Critères de validation** :
□ 2 réglementations affichées  
□ Statut orange correct  
□ Boutons toujours actifs  
□ Commentaire affiché

---

### ÉTAPE 2.5 : Re-validation depuis "À revoir"

**Action** :
1. Sur la carte **"Règlement REACH"** (à revoir)
2. Cliquer sur **"Valider"**
3. Observer le changement

**Résultat attendu** :
- Carte disparaît de "À revoir"
- Badge "À revoir" : 2 vers 1
- Badge "Validées" : 3 vers 4
- Carte apparaît dans "Validées"
- Status DB : 'to-review' vers 'approved'

**Critères de validation** :
□ Transition de statut correcte  
□ Badges mis à jour  
□ Réglementation dans "Validées"

---

### ÉTAPE 2.6 : Exécution Agent 2 sur nouvelle validation

**Action** :
1. Relancer Agent 2 :
   ```bash
   python -m src.agent_2.agent
   ```
2. Observer traitement de REACH

**Résultat attendu - Logs** :
L'agent doit indiquer qu'il a trouvé 4 analyses dont 1 nouvelle.
Il traite le Règlement REACH avec le code NC 3824.
L'agent détecte qu'aucun produit Hutchinson ne correspond au code NC 3824.
L'impact calculé est FAIBLE avec risque de conformité.
Les métriques sont : impact_level faible, modality reporting, deadline 06-2026.
Un impact assessment est créé avec succès.

**Vérification base de données** :
Dans la table impact_assessments, vérifier que l'enregistrement REACH a impact_level='faible' et risk_main='conformite'.

**Critères de validation** :
□ Agent 2 traite 4 analyses  
□ Détection absence de matching  
□ Impact level = 'faible'  
□ Recommendation cohérente  
□ ImpactAssessment créé

---

### ÉTAPE 2.7 : Dashboard - Vérification répartition impacts

**Action** :
1. Connexion décideur
2. Consulter graphique "Répartition par criticité"

**Résultat attendu** :
Le graphique de répartition doit afficher 3 impacts élevés (dont biocides), 2 impacts moyens, et 1 impact faible (REACH).

**Critères de validation** :
□ 3 impacts "élevé"  
□ 2 impacts "moyen"  
□ 1 impact "faible" (REACH)  
□ Total = 6 impacts analysés

---

## RÉSULTATS SCÉNARIO 2

| Étape | Attendu | Résultat | Statut | Commentaires |
|-------|---------|----------|--------|--------------|
| 2.1 Rejet réglementation | Carte dans "Rejetées" | | [ ] | |
| 2.2 Onglet rejetées | 1 réglementation | | [ ] | |
| 2.3 Mise en révision | Carte dans "À revoir" | | [ ] | |
| 2.4 Onglet à revoir | 2 réglementations | | [ ] | |
| 2.5 Re-validation | Transition vers "Validées" | | [ ] | |
| 2.6 Agent 2 REACH | Impact faible créé | | [ ] | |
| 2.7 Dashboard | Répartition correcte | | [ ] | |

**Durée réelle** : ___ minutes  
**Anomalies détectées** : ___  
**Bloquant** : [ ] Oui [ ] Non

---

## 4. TESTS UNITAIRES DÉTAILLÉS

### 4.1 Tests Agent 2 - Outils

#### TEST 4.1.1 : fetch_analyses

**Objectif** : Vérifier récupération analyses validées

```python
# Test
from src.agent_2.tools import fetch_analyses

result = fetch_analyses(validation_status="approved", limit=10)

# Assertions
assert len(result) == 4
assert result[0]['validation_status'] == 'approved'
assert result[0]['document_title'] is not None
assert result[0]['regulation_type'] in ['CBAM', 'EUDR', 'REACH', 'CSRD']
```

**Critères de succès** :
□ Retourne liste non vide  
□ Tous les status = 'approved'  
□ Champs obligatoires présents  
□ Temps d'exécution < 1 seconde

---

#### TEST 4.1.2 : fetch_company_processes

**Objectif** : Vérifier chargement profil entreprise

```python
# Test
from src.agent_2.tools import fetch_company_processes

result = fetch_company_processes(limit=5)

# Assertions
assert len(result) == 1
assert result[0]['company_name'] == 'Hutchinson'
assert len(result[0]['suppliers']) == 2
assert len(result[0]['products']) == 2
assert result[0]['products'][0]['nc_code'] == '4016'
```

**Critères de succès** :
- [ ] Profil Hutchinson chargé
- [ ] 2 fournisseurs (CN, DE)
- [ ] 2 produits avec NC
- [ ] Structure JSON valide

---

#### TEST 4.1.3 : save_impact_assessment - Données valides

**Objectif** : Vérifier sauvegarde avec données conformes

```python
# Test
from src.agent_2.tools import save_impact_assessment

result = save_impact_assessment(
    analysis_id="analysis_test_001",
    risk_main="fiscal",
    impact_level="eleve",
    risk_details="Test impact fiscal",
    modality="taxe",
    deadline="12-2025",
    recommendation="Action de test",
    llm_reasoning="Raisonnement LLM"
)

# Assertions
assert result['saved'] == True
assert result['impact_assessment_id'] is not None
```

**Critères de succès** :
- [ ] Sauvegarde réussie
- [ ] ID généré
- [ ] Pas d'erreur

---

#### TEST 4.1.4 : save_impact_assessment - Validation erreurs

**Objectif** : Vérifier rejet de données invalides

```python
# Test - risk_main invalide
result = save_impact_assessment(
    analysis_id="test",
    risk_main="INVALIDE",  # ← Valeur non autorisée
    impact_level="eleve",
    risk_details="Test",
    modality="taxe",
    deadline="12-2025",
    recommendation="Test"
)

# Assertions
assert result['saved'] == False
assert 'errors' in result
assert 'risk_main invalide' in result['errors'][0]
assert 'allowed' in result  # Liste des valeurs autorisées
```

**Tests à effectuer** :
- [ ] risk_main invalide → rejeté
- [ ] impact_level invalide → rejeté
- [ ] modality invalide → rejeté
- [ ] deadline format incorrect → rejeté
- [ ] Liste des valeurs autorisées retournée

---

### 4.2 Tests Interface Utilisateur

#### TEST 4.2.1 : Connexion

| Cas | Email | Password | Résultat attendu |
|-----|-------|----------|------------------|
| TC01 | juriste@hutchinson.com | ✓ | Connexion réussie |
| TC02 | decideur@hutchinson.com | ✓ | Connexion réussie |
| TC03 | invalide@test.com | ✓ | Erreur "Utilisateur inconnu" |
| TC04 | juriste@hutchinson.com | ✗ | Erreur "Mot de passe incorrect" |
| TC05 | (vide) | (vide) | Champs obligatoires |

---

#### TEST 4.2.2 : Navigation onglets

**Séquence** :
1. Clic "Réglementations" → Liste "EN ATTENTE"
2. Clic "Validées" → Liste "VALIDÉE"
3. Clic "Rejetées" → Liste "REJETÉE"
4. Clic "À revoir" → Liste "À REVOIR"

**Critères** :
- [ ] Changement de vue instantané (< 0.5s)
- [ ] Titre de page mis à jour
- [ ] Filtre appliqué correctement
- [ ] Badge actif souligné
- [ ] URL mise à jour (si routing activé)

---

#### TEST 4.2.3 : Actions boutons

| Bouton | État avant | État après | Badge modifié |
|--------|-----------|------------|---------------|
| Valider | EN ATTENTE | VALIDÉE | Validées +1 |
| Rejeter | EN ATTENTE | REJETÉE | Rejetées +1 |
| À revoir | EN ATTENTE | À REVOIR | À revoir +1 |

**Animations à vérifier** :
- [ ] Slide out (sortie de carte)
- [ ] Fade out (disparition)
- [ ] Badge pulse (clignotement)
- [ ] Notification toast

---

#### TEST 4.2.4 : Recherche

**Actions** :
1. Saisir "biocides" → Filtre appliqué
2. Saisir "EU 528" → 1 résultat
3. Saisir "xxxxx" → Aucun résultat
4. Vider champ → Liste complète

**Critères** :
- [ ] Recherche insensible à la casse
- [ ] Recherche dans titre + référence
- [ ] Résultats instantanés (< 0.3s)
- [ ] Message "Aucun résultat" si vide

---

#### TEST 4.2.5 : Filtres avancés

**Action** :
1. Cliquer "Filtres" (bouton vert)
2. Panel de filtres s'ouvre
3. Sélectionner :
   - Type : CBAM
   - Date : Dernier mois
   - Confiance : > 0.8
4. Appliquer

**Résultat** :
- [ ] Panel slide-in animé
- [ ] Filtres appliqués cumulativement
- [ ] Compteur mis à jour
- [ ] Bouton "Réinitialiser" actif

---

#### TEST 4.2.6 : Export JSON

**Action** :
1. Onglet "Validées"
2. Cliquer "Export JSON"
3. Téléchargement fichier

**Vérification fichier** :
```json
{
  "export_date": "2026-01-26T10:45:00Z",
  "total": 4,
  "regulations": [
    {
      "id": "...",
      "title": "Règlement biocides...",
      "status": "validated",
      "validation_date": "2026-01-26",
      "validated_by": "juriste@hutchinson.com"
    }
  ]
}
```

**Critères** :
- [ ] Fichier téléchargé
- [ ] Format JSON valide
- [ ] Données complètes
- [ ] Nom fichier : `regulations_validated_YYYYMMDD.json`

---

### 4.3 Tests Dashboard Décideur

#### TEST 4.3.1 : Indicateurs clés

**Vérifications** :
1. **Réglementations suivies** = 123
2. **En cours vs Validées** = 78% / 22%
3. **Risques élevés** = 15 (puis 16 après Agent 2)
4. **Deadlines critiques** = 7

**Critères** :
- [ ] Valeurs numériques correctes
- [ ] Pourcentages calculés dynamiquement
- [ ] Animations au hover
- [ ] Couleurs par criticité

---

#### TEST 4.3.2 : Export PDF Dashboard

**Action** :
1. Cliquer "Exporter Dashboard PDF"
2. Téléchargement PDF

**Vérification PDF** :
- [ ] En-tête : "Dashboard Décideurs - Hutchinson"
- [ ] Date d'export
- [ ] 4 indicateurs clés
- [ ] Graphiques (images)
- [ ] Mise en page propre

---

#### TEST 4.3.3 : Profil utilisateur

**Action** :
1. Cliquer "Profil" dans sidebar
2. Vue profil décideur

Contenu attendu :

Décideur Hutchinson
Email: decideur@hutchinson.com
Département: Direction Générale
Permissions: Lecture Dashboard, Export PDF
Dernière connexion: 15/01/2026 - 14:30

Statistiques d'utilisation:
- 47 connexions ce mois
- 23 exports PDF
- 156 réglementations consultées

**Critères** :
- [ ] Informations complètes
- [ ] Statistiques correctes
- [ ] Avatar affiché

---

## 5. GESTION DES ANOMALIES

### 5.1 Grille de criticité

| Niveau | Définition | Action | Délai |
|--------|-----------|--------|-------|
| **BLOQUANT** | Empêche utilisation totale | Correction immédiate | 4h |
| **MAJEUR** | Fonction principale indisponible | Correction prioritaire | 24h |
| **MINEUR** | Fonction secondaire défaillante | Correction planifiée | 3j |
| **COSMÉTIQUE** | Affichage / ergonomie | Backlog | - |

---

### 5.2 Template de déclaration d'anomalie

```markdown
## ANOMALIE #___

**Date** : __/__/____
**Testeur** : ___________
**Scénario** : ___________
**Étape** : ___________

**Criticité** : [ ] BLOQUANT [ ] MAJEUR [ ] MINEUR [ ] COSMÉTIQUE
**Description** :
_Décrire le problème constaté_

**Résultat attendu** :
_Ce qui devrait se passer_

**Résultat obtenu** :
_Ce qui se passe réellement_

**Reproduction** :
1. _Étape 1_
2. _Étape 2_
3. _Erreur apparaît_

**Logs** :
```
_Copier logs d'erreur_
```

**Capture d'écran** : [ ] Jointe

**Environnement** :
- OS : ___________
- Navigateur : ___________
- Version : ___________
```

---

## 6. MÉTRIQUES DE QUALITÉ

### 6.1 Critères d'acceptation globaux

| Critère | Objectif | Mesuré |
|---------|----------|--------|
| **Taux de succès tests** | ≥ 95% | ___ % |
| **Anomalies bloquantes** | 0 | ___ |
| **Anomalies majeures** | ≤ 2 | ___ |
| **Temps de réponse UI** | < 2s | ___ s |
| **Temps exécution Agent 2** | < 30s | ___ s |
| **Précision matching produits** | ≥ 90% | ___ % |
| **Taux de disponibilité** | 99% | ___ % |

---

### 6.2 Couverture fonctionnelle

| Module | Couverture |
|--------|------------|
| Agent 1A - Collecte | 50% (hors périmètre) |
| Agent 1B - Analyse | 100% (mock data) |
| Interface Juriste - Validation | 100% |
| Agent 2 - Analyse d'impact | 100% |
| Dashboard Décideur | 80% |
| Notifications emails | 0% (hors périmètre) |
| **Total couverture** | **82%** |

---

### 6.3 Performances

| Opération | Objectif | Mesuré | Écart |
|-----------|----------|--------|-------|
| Connexion | < 2s | ___ s | ___ |
| Chargement liste (50 items) | < 1s | ___ s | ___ |
| Validation réglementation | < 3s | ___ s | ___ |
| Agent 2 - 1 analyse | < 10s | ___ s | ___ |
| Agent 2 - 10 analyses | < 60s | ___ s | ___ |
| Export PDF dashboard | < 5s | ___ s | ___ |
| Recherche + filtre | < 0.5s | ___ s | ___ |

---

## 7. VALIDATION FINALE

### 7.1 Checklist de recette

#### Scénario 1 : Workflow complet
□ Connexion juriste réussie  
□ Validation réglementation  
□ Carte déplacée vers "Validées"  
□ Agent 2 exécuté sans erreur  
□ ImpactAssessment créé en DB  
□ Dashboard décideur mis à jour  
□ Métriques qualitatives correctes

#### Scénario 2 : Rejet et révision
□ Rejet avec commentaire  
□ Carte dans "Rejetées"  
□ Mise en révision  
□ Carte dans "À revoir"  
□ Re-validation possible  
□ Agent 2 traite nouvelle validation

#### Tests unitaires
□ fetch_analyses : OK  
□ fetch_company_processes : OK  
□ save_impact_assessment : OK  
□ Validation erreurs : OK

#### Interface utilisateur
□ Navigation onglets : OK  
□ Actions boutons : OK  
□ Recherche : OK  
□ Filtres : OK  
□ Export JSON : OK

#### Dashboard
□ Indicateurs clés : OK  
□ Graphiques : OK  
□ Export PDF : OK  
□ Profil : OK

---

### 7.2 Décision de recette

**Date de recette** : __/__/____  
**Testeurs** : ___________  

**Résultats globaux** :
- Tests réussis : ___ / ___
- Taux de succès : ___ %
- Anomalies bloquantes : ___
- Anomalies majeures : ___

**Avis** :

□ **VALIDÉ** - Recette conforme, mise en production autorisée

□ **VALIDÉ AVEC RÉSERVES** - Corrections mineures nécessaires  
   Réserves : __________________________________________  
   Date de levée : __/__/____

□ **REJETÉ** - Corrections majeures requises  
   Raisons : __________________________________________  
   Nouvelle recette : __/__/____

---

**Signatures** :

| Rôle | Nom | Signature | Date |
|------|-----|-----------|------|
| Testeur | | | |
| Responsable Agent 2 (Dev 4) | | | |
| Chef de projet | | | |
| Décideur final | | | |

---

## ANNEXES

### Annexe A : Valeurs prédéfinies Agent 2

```python
# Listes de valeurs autorisées
risk_main = [
    "fiscal",
    "operationnel",
    "conformite",
    "reputationnel",
    "juridique"
]

impact_level = [
    "faible",
    "moyen",
    "eleve"
]

modality = [
    "certificat",
    "reporting",
    "taxe",
    "quota",
    "interdiction",
    "autorisation"
]

# Format deadline
deadline_pattern = r"^(0[1-9]|1[0-2])-[0-9]{4}$"
# Exemples : "01-2026", "12-2025"
```

### Annexe B : Structure base de données

```sql
-- Table analyses
CREATE TABLE analyses (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    is_relevant BOOLEAN NOT NULL,
    confidence REAL NOT NULL,
    validation_status TEXT NOT NULL,
    validation_comment TEXT,
    validated_by TEXT,
    validated_at TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- Table impact_assessments
CREATE TABLE impact_assessments (
    id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL,
    risk_main TEXT NOT NULL,
    impact_level TEXT NOT NULL,
    risk_details TEXT NOT NULL,
    modality TEXT NOT NULL,
    deadline TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    llm_reasoning TEXT,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);

-- Table company_processes
CREATE TABLE company_processes (
    id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    processes JSON NOT NULL,
    transport_modes JSON,
    suppliers JSON,
    products JSON,
    import_export_flows JSON,
    notes TEXT,
    created_at TIMESTAMP NOT NULL
);
```

### Annexe C : Exemple de rapport Agent 2

```json
{
  "impact_assessment_id": "ia_001",
  "analysis_id": "analysis_biocides_001",
  "regulation": {
    "title": "Règlement sur les produits biocides (EU) 528/2012",
    "type": "CBAM",
    "nc_codes": ["4016", "4009"]
  },
  "metrics": {
    "risk_main": "fiscal",
    "impact_level": "eleve",
    "risk_details": "Taxes carbone sur imports produits biocides. 2 produits Hutchinson concernés.",
    "modality": "certificat",
    "deadline": "12-2025"
  },
  "affected_entities": {
    "suppliers": [
      {"name": "Supplier A", "country": "CN", "impact": "direct"}
    ],
    "products": [
      {"name": "Seal", "nc_code": "4016", "volume_annual": 1200},
      {"name": "Hose", "nc_code": "4009", "volume_annual": 800}
    ],
    "flows": [
      {"origin": "CN", "destination": "FR", "volume": 1200}
    ]
  },
  "recommendation": "Certifier conformité biocides + budget taxes. Actions prioritaires : (1) Audit fournisseurs chinois Q2 2025, (2) Certification produits NC 4016/4009, (3) Prévoir budget additionnel taxes carbone 150k€.",
  "llm_reasoning": "Analyse complète croisant codes NC réglementation avec catalogue Hutchinson. Impact élevé car 2/2 produits principaux concernés et 100% du flux CN impacté. Modalité certificat requise avant deadline 12-2025.",
  "created_at": "2026-01-26T10:30:00Z"
}
```

---

## FIN DU CAHIER DE RECETTE

Document généré le 26/01/2026  
Version : 1.0  
Projet : Plateforme de veille réglementaire durable