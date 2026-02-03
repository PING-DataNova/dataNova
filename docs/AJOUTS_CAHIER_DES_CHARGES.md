# 📝 AJOUTS AU CAHIER DES CHARGES
## Suite à la réunion client du 03/02/2026

Ce document liste tous les éléments à ajouter ou modifier dans le cahier des charges existant, basé sur les demandes explicites du client.

---

# 1. 📚 DOCUMENTATION DES SOURCES (OBLIGATOIRE)

## 1.1 À ajouter dans le CDC

**Citation du client :**
> *"Ce sera bien de mettre les sources pour justifier pourquoi vous avez fait ce choix."*

### Section à créer : "Sources de données externes"

```markdown
## Sources de données externes

### 1. EUR-Lex (Risques réglementaires)

| Attribut | Valeur |
|----------|--------|
| **URL** | https://eur-lex.europa.eu |
| **Type d'API** | SOAP (SRU - Search/Retrieve via URL) |
| **Documentation** | https://eur-lex.europa.eu/content/help/data-reuse/webservice.html |
| **Coût** | Gratuit |
| **Authentification** | Non requise |
| **Limite de requêtes** | Pas de limite documentée |

**Justification du choix :**
- Site officiel de l'Union Européenne
- API bien documentée et stable
- Données fiables et à jour
- Accès aux documents consolidés (lois avec toutes les modifications)
- Permet la recherche par mots-clés (text~keyword)

**Données récupérées :**
- Titre du règlement
- CELEX (identifiant unique)
- Date de publication
- Date d'entrée en vigueur
- Texte intégral ou résumé
- Lien vers le document original

### 2. OpenMeteo (Risques climatiques)

| Attribut | Valeur |
|----------|--------|
| **URL** | https://open-meteo.com |
| **Type d'API** | REST |
| **Documentation** | https://open-meteo.com/en/docs |
| **Coût** | Gratuit (usage non commercial) |
| **Authentification** | Non requise |
| **Limite de requêtes** | 10 000/jour |

**Justification du choix :**
- API gratuite et sans authentification
- Prévisions jusqu'à J+16
- Granularité GPS (latitude/longitude)
- Alertes météo incluses
- Données historiques disponibles

**Données récupérées :**
- Prévisions température, précipitations, vent
- Alertes météo (niveau de risque)
- Conditions extrêmes (tempêtes, inondations, canicules)

### 3. Sources géopolitiques (À définir)

| Source candidate | Type | Coût | Notes |
|------------------|------|------|-------|
| ACLED | Conflits | Payant | Données conflits armés |
| GDELT | Actualités | Gratuit | Analyse médias mondiaux |
| OMS | Sanitaire | Gratuit | Alertes épidémies (V2) |
| Gouvernements | Sanctions | Gratuit | Listes noires, embargos |

**À valider avec le client pour la V1.**
```

---

# 2. 💰 BUDGET ET COÛTS (À COMPLÉTER)

## 2.1 Structure demandée par le client

**Citation du client :**
> *"Au niveau des ressources humaines, mettez juste le nombre de jours-hommes nécessaire par typologie."*

### Section à créer/modifier : "Budget prévisionnel"

```markdown
## Budget prévisionnel

### 1. Ressources humaines (en jours-hommes)

| Profil | Phase 1 (MVP) | Phase 2 | Total | TJM estimé* |
|--------|---------------|---------|-------|-------------|
| Chef de projet | 5 j | 10 j | 15 j | - |
| Développeur Backend Python | 15 j | 20 j | 35 j | - |
| Développeur Frontend React | 10 j | 15 j | 25 j | - |
| Data Engineer | 8 j | 10 j | 18 j | - |
| Expert LLM/IA | 10 j | 8 j | 18 j | - |
| Testeur QA | 5 j | 8 j | 13 j | - |
| **TOTAL** | **53 j** | **71 j** | **124 j** | - |

*TJM (Taux Journalier Moyen) à appliquer selon les tarifs Hutchinson/prestataires.

### 2. Infrastructure et services

| Service | Coût mensuel | Coût annuel | Notes |
|---------|--------------|-------------|-------|
| Hébergement Cloud (Azure/AWS) | 200-500€ | 2 400-6 000€ | Selon volumétrie |
| API LLM (Claude/OpenAI) | 100-300€ | 1 200-3 600€ | Selon nb analyses |
| Base de données | Inclus | Inclus | PostgreSQL managé |
| **TOTAL Infrastructure** | **300-800€** | **3 600-9 600€** | - |

### 3. Sources de données (potentiellement payantes)

| Source | Coût | Notes |
|--------|------|-------|
| EUR-Lex | Gratuit | API officielle UE |
| OpenMeteo | Gratuit | Usage non commercial |
| API Météo Hutchinson | Inclus | Déjà disponible en interne |
| ACLED (géopolitique) | ~500€/an | À valider si nécessaire |
| Autres sources premium | À définir | Selon besoins identifiés |

### 4. Récapitulatif budget total

| Poste | Phase 1 | Phase 2 | Total |
|-------|---------|---------|-------|
| Ressources humaines | XX j × TJM | XX j × TJM | XX € |
| Infrastructure (1 an) | - | - | 3 600-9 600€ |
| Sources de données | - | - | 0-1 000€ |
| **TOTAL** | - | - | **À calculer** |
```

---

# 3. 📅 PLANNING ET DÉLAIS (À DÉTAILLER)

## 3.1 Structure demandée

**Citation du client :**
> *"Il faudrait peut-être concrétiser les dates."*

### Section à modifier : "Planning projet"

```markdown
## Planning projet

### Phase 1 : MVP (Sprint 1-4)

| Sprint | Dates | Objectifs | Livrables |
|--------|-------|-----------|-----------|
| Sprint 1 | 27/01 - 02/02 | Spécifications, Architecture | CDC v1, Schéma architecture |
| Sprint 2 | 03/02 - 09/02 | Développement core | Agents 1A, 1B, 2 fonctionnels |
| Sprint 3 | 10/02 - 16/02 | Intégration, Orchestration | Analyse automatique, API |
| Sprint 4 | 17/02 - 23/02 | Tests, Démo | MVP déployé, Documentation |

### Phase 2 : Fonctionnalités avancées (Sprint 5-8)

| Sprint | Dates | Objectifs | Livrables |
|--------|-------|-----------|-----------|
| Sprint 5 | 24/02 - 02/03 | Workflow validation | Statuts, relances, versioning |
| Sprint 6 | 03/03 - 09/03 | Interface admin | Paramétrage sources/risques |
| Sprint 7 | 10/03 - 16/03 | Notifications | Emails, filtres enregistrables |
| Sprint 8 | 17/03 - 23/03 | Tests acceptance | Validation métier, corrections |

### Jalons clés

| Jalon | Date | Critères de validation |
|-------|------|------------------------|
| **J1 : CDC validé** | 02/02/2026 | Approbation client |
| **J2 : MVP fonctionnel** | 06/02/2026 | Démo réussie |
| **J3 : Recette interne** | 23/02/2026 | Tests passés |
| **J4 : Mise en production** | À définir | Validation finale |
```

---

# 4. ✅ TESTS ET QUALITÉ (À ENRICHIR)

## 4.1 Tests d'acceptance utilisateur (UAT)

**Citation du client :**
> *"Il va falloir formaliser des scénarios et des tests d'acceptance qui vous permettent de vérifier que les modèles sont explicables."*

### Section à ajouter : "Tests d'acceptance"

```markdown
## Tests d'acceptance utilisateur (UAT)

### Objectif
Valider que l'application répond aux attentes métier et que les analyses IA sont fiables et explicables.

### Scénarios de test

#### Scénario UAT-01 : Analyse automatique globale

| Étape | Action | Résultat attendu | Validé |
|-------|--------|------------------|--------|
| 1 | Lancer l'analyse batch sur 5 sites | Analyse terminée sans erreur | ☐ |
| 2 | Vérifier les rapports générés | 1 rapport par site avec risques identifiés | ☐ |
| 3 | Vérifier les sources citées | Chaque risque a un lien source cliquable | ☐ |
| 4 | Vérifier les recommandations | Actions concrètes et pertinentes | ☐ |

#### Scénario UAT-02 : Analyse à la demande fournisseur

| Étape | Action | Résultat attendu | Validé |
|-------|--------|------------------|--------|
| 1 | Saisir un fournisseur chinois (aluminium) | Formulaire accepté | ☐ |
| 2 | Lancer l'analyse | Résultats en < 2 min | ☐ |
| 3 | Vérifier risques réglementaires | CBAM, anti-dumping détectés | ☐ |
| 4 | Vérifier risques météo | Prévisions J+16 affichées | ☐ |

#### Scénario UAT-03 : Explicabilité des résultats

| Étape | Action | Résultat attendu | Validé |
|-------|--------|------------------|--------|
| 1 | Ouvrir un rapport | Source originale accessible | ☐ |
| 2 | Vérifier l'extrait cité | Passage pertinent surligné | ☐ |
| 3 | Vérifier le raisonnement | Logique claire et traçable | ☐ |
| 4 | Cliquer sur lien EUR-Lex | Document original s'ouvre | ☐ |

#### Scénario UAT-04 : Fiabilité des scores

| Étape | Action | Résultat attendu | Validé |
|-------|--------|------------------|--------|
| 1 | Analyser un cas connu (CBAM) | Risque détecté comme CRITIQUE | ☐ |
| 2 | Analyser un cas non pertinent | Risque détecté comme FAIBLE ou rejeté | ☐ |
| 3 | Comparer avec analyse manuelle | Écart < 20% | ☐ |

### Checklist de validation métier

| Critère | Description | Validateur | Statut |
|---------|-------------|------------|--------|
| Pertinence des risques | Les risques détectés sont réels | Équipe Achats | ☐ |
| Pertinence des impacts | Les impacts financiers sont réalistes | Équipe Finance | ☐ |
| Pertinence des recommandations | Les actions proposées sont faisables | Équipe Supply | ☐ |
| Conformité réglementaire | Les lois citées sont correctes | Équipe Juridique | ☐ |
| Utilisabilité | L'interface est intuitive | Tous utilisateurs | ☐ |
```

## 4.2 Explicabilité IA

**Citation du client :**
> *"Il y a un mécanisme d'explicabilité parce que si vous sortez un risque, il va falloir expliquer à l'utilisateur comment on est arrivé à ce risque."*

### Section à ajouter : "Explicabilité et traçabilité"

```markdown
## Explicabilité et traçabilité IA

### Principe
Chaque analyse doit être traçable et explicable. L'utilisateur doit pouvoir comprendre POURQUOI un risque a été détecté.

### Mécanismes implémentés

#### 1. Citation des sources
- Chaque risque détecté est associé à sa source (URL)
- Extrait du texte original inclus dans le rapport
- Lien cliquable vers le document complet

#### 2. Score de confiance LLM Judge
- Score 0-10 affiché sur chaque rapport
- Critères d'évaluation :
  - Sources citées correctement
  - Raisonnement cohérent
  - Pas d'hallucination détectée
  - Pertinence par rapport au profil entreprise

#### 3. Traçabilité du pipeline
- ID unique pour chaque rapport
- Timestamp de génération
- Version des agents utilisés
- Paramètres de l'analyse

#### 4. Mention obligatoire
- "Ce rapport a été généré automatiquement par une IA"
- Score de confiance affiché (ex: 92%)
- Ou "Validé par [Nom] le [Date]" si validation humaine

### Exemple de bloc explicabilité dans un rapport

```
┌─────────────────────────────────────────────────────────────────┐
│ 🔍 EXPLICABILITÉ DE L'ANALYSE                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ POURQUOI CE RISQUE A ÉTÉ DÉTECTÉ :                             │
│                                                                 │
│ 1. Le fournisseur AluMetal est basé en Chine                   │
│ 2. Il fournit de l'aluminium (code NC 7606)                    │
│ 3. Le règlement CBAM (UE 2023/956) s'applique aux imports      │
│    d'aluminium depuis pays hors UE                             │
│ 4. Extrait : "Les importateurs doivent déclarer les            │
│    émissions carbone incorporées..." (Art. 5, §2)              │
│                                                                 │
│ NIVEAU DE CONFIANCE : 92%                                       │
│ - Sources vérifiées : ✅                                        │
│ - Raisonnement cohérent : ✅                                    │
│ - Données entreprise correctes : ✅                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```
```

---

# 5. 🔄 PARAMÉTRAGE ET ÉVOLUTIVITÉ (À AJOUTER)

## 5.1 Sources paramétrables

**Citation du client :**
> *"La notion de risque, c'est quelque chose qui n'est pas statique. Les sources d'informations peuvent évoluer. Il faut que l'application soit juste paramétrable."*

### Section à ajouter : "Paramétrage de l'application"

```markdown
## Paramétrage de l'application

### 1. Gestion des sources de données

L'administrateur peut :
- ✅ Ajouter une nouvelle source de données
- ✅ Modifier les paramètres d'une source existante
- ✅ Activer/désactiver une source
- ✅ Définir la fréquence de synchronisation

#### Structure d'une source

| Champ | Type | Description | Exemple |
|-------|------|-------------|---------|
| id | string | Identifiant unique | src_eurlex_01 |
| name | string | Nom affiché | EUR-Lex |
| type | enum | Type de risque associé | REGULATORY |
| api_url | string | URL de l'API | https://eur-lex... |
| api_type | enum | REST ou SOAP | SOAP |
| auth_required | bool | Authentification requise | false |
| sync_frequency | cron | Fréquence de sync | 0 6 * * * |
| is_active | bool | Source active | true |
| parameters | json | Paramètres spécifiques | {"language": "FR"} |

### 2. Gestion des catégories de risques

L'administrateur peut :
- ✅ Ajouter une nouvelle catégorie de risque
- ✅ Associer des sources à une catégorie
- ✅ Définir les prompts LLM spécifiques
- ✅ Configurer les seuils de criticité

#### Structure d'une catégorie

| Champ | Type | Description | Exemple |
|-------|------|-------------|---------|
| id | string | Identifiant unique | risk_regulatory |
| name | string | Nom affiché | Réglementaire |
| icon | string | Icône | 📋 |
| color | string | Couleur | #3B82F6 |
| sources | array | Sources associées | [src_eurlex_01] |
| prompt_template | text | Prompt LLM | "Analyse ce texte..." |
| thresholds | json | Seuils | {"critical": 80, "high": 60} |

### 3. Exemple : Ajout d'un nouveau type de risque

**Scénario** : Ajouter les risques sanitaires (COVID, épidémies)

1. Créer la catégorie :
   ```json
   {
     "id": "risk_sanitary",
     "name": "Sanitaire",
     "icon": "🏥",
     "color": "#10B981"
   }
   ```

2. Ajouter la source :
   ```json
   {
     "id": "src_oms_01",
     "name": "OMS - Alertes épidémies",
     "type": "SANITARY",
     "api_url": "https://www.who.int/...",
     "is_active": true
   }
   ```

3. Associer au workflow existant :
   - Les agents analysent automatiquement
   - Les rapports incluent la nouvelle catégorie
   - Le dashboard affiche les risques sanitaires
```

---

# 6. 🔔 NOTIFICATIONS ET WORKFLOW (V2)

## 6.1 Système de notifications

**Citation du client :**
> *"Le rapport est validé et une notification est envoyée aux équipes à charge."*

### Section à ajouter : "Notifications"

```markdown
## Système de notifications

### 1. Types de notifications

| Type | Déclencheur | Canal | Destinataires |
|------|-------------|-------|---------------|
| Nouveau risque critique | Score risque > 80 | Email + App | Équipe concernée |
| Rapport à valider | Score confiance 7-8.5 | Email + App | Validateurs |
| Relance validation | J+1 sans action | Email | Validateur assigné |
| Analyse terminée | Fin batch quotidien | App | Tous utilisateurs |
| Erreur système | Échec analyse | Email | Administrateurs |

### 2. Paramétrage par utilisateur

Chaque utilisateur peut configurer :
- ☑ Recevoir les notifications par email
- ☑ Recevoir les notifications dans l'app
- ☑ Fréquence : Temps réel / Résumé quotidien
- ☑ Filtrer par type de risque
- ☑ Filtrer par périmètre (région, matière, etc.)

### 3. Template email

```
Objet: [PING] 🔴 Nouveau risque critique détecté - CBAM

Bonjour [Prénom],

Un nouveau risque critique a été détecté par PING :

📋 Type : Réglementaire
🎯 Risque : CBAM - Taxe carbone aux frontières
📊 Score : 85/100 (CRITIQUE)
🏭 Entités impactées : 12 fournisseurs, 3 sites

👉 Voir le rapport complet : [Lien]

---
Cet email a été envoyé automatiquement par PING.
Pour modifier vos préférences : [Lien paramètres]
```
```

## 6.2 Workflow de validation détaillé

**Citation du client :**
> *"Tant que vous mettez le losange 'validation humaine', il faut matérialiser dans l'application le workflow."*

### Section à ajouter : "Workflow de validation"

```markdown
## Workflow de validation humaine

### 1. Statuts des rapports

| Statut | Description | Actions possibles |
|--------|-------------|-------------------|
| DRAFT | En cours de génération | - |
| PENDING_REVIEW | En attente de validation (score 7-8.5) | Approuver, Rejeter |
| APPROVED | Validé par un humain | Publier, Archiver |
| AUTO_PUBLISHED | Publié automatiquement (score > 8.5) | Archiver |
| REJECTED | Rejeté par validateur | Archiver |
| ARCHIVED | Archivé (obsolète) | - |

### 2. Diagramme de flux

```
                    ┌─────────────┐
                    │   DRAFT     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  LLM Judge  │
                    │  Score 0-10 │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
   ┌──────────┐    ┌──────────────┐   ┌──────────────┐
   │ Score<7  │    │ Score 7-8.5  │   │ Score>8.5    │
   │ REJECTED │    │PENDING_REVIEW│   │AUTO_PUBLISHED│
   └──────────┘    └──────┬───────┘   └──────────────┘
                          │
                    ┌─────┴─────┐
                    │ Validateur│
                    │ intervient│
                    └─────┬─────┘
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
       ┌──────────┐           ┌──────────┐
       │ APPROVED │           │ REJECTED │
       └──────────┘           └──────────┘
```

### 3. Règles de gestion

| Règle | Description |
|-------|-------------|
| R1 | Un rapport PENDING_REVIEW doit être traité sous 48h |
| R2 | Si non traité après 24h, une relance email est envoyée |
| R3 | Si non traité après 48h, escalade au manager |
| R4 | Si une nouvelle analyse est lancée, l'ancienne passe en ARCHIVED |
| R5 | Un rapport APPROVED affiche "Validé par [Nom] le [Date]" |
| R6 | Un rapport AUTO_PUBLISHED affiche "Généré par IA (92%)" |

### 4. Écran de validation

```
┌─────────────────────────────────────────────────────────────────┐
│ 📋 RAPPORTS À VALIDER (5)                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 🟠 CBAM - Impact fournisseurs Chine                         ││
│ │ Score confiance : 7.8/10 | Généré le 03/02 06:15           ││
│ │                                                             ││
│ │ [👁️ Voir le rapport] [✅ Approuver] [❌ Rejeter]            ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 🟠 Alerte météo Chennai                                     ││
│ │ Score confiance : 7.2/10 | Généré le 03/02 06:18           ││
│ │ ⚠️ Relance : En attente depuis 36h                         ││
│ │                                                             ││
│ │ [👁️ Voir le rapport] [✅ Approuver] [❌ Rejeter]            ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```
```

---

# 7. 📊 MÉTRIQUES ET KPIs (À AJOUTER)

**Citation du client :**
> *"28% de risque détecté ce mois"* (vu sur le dashboard)

### Section à ajouter : "Indicateurs de performance"

```markdown
## Indicateurs de performance (KPIs)

### 1. KPIs opérationnels

| KPI | Description | Cible |
|-----|-------------|-------|
| Nb analyses/jour | Nombre d'analyses automatiques | 100% périmètre |
| Temps moyen analyse | Durée d'une analyse complète | < 5 min |
| Taux de disponibilité | Uptime de l'application | > 99% |
| Taux d'erreur | Analyses en échec | < 1% |

### 2. KPIs qualité IA

| KPI | Description | Cible |
|-----|-------------|-------|
| Score confiance moyen | Moyenne des scores LLM Judge | > 8/10 |
| Taux validation auto | Rapports publiés sans validation humaine | > 70% |
| Taux de rejet | Rapports rejetés par validateurs | < 10% |
| Précision détection | Risques confirmés / Risques détectés | > 85% |

### 3. KPIs métier

| KPI | Description | Mesure |
|-----|-------------|--------|
| Risques critiques détectés | Nb de risques score > 80 | Par semaine |
| Couverture fournisseurs | % fournisseurs analysés | Cible 100% |
| Couverture sites | % sites analysés | Cible 100% |
| Temps de réaction | Délai entre alerte et action | Objectif < 24h |
```

---

# 8. 🏗️ ARCHITECTURE - MISE À JOUR SCHÉMA

**Citation du client :**
> *"Dans les priorités, c'est de mettre à jour ce schéma d'architecture avec les choses en mettant en évidence ce qui est implémenté d'ici jeudi, ce qui reste à implémenter dans une phase 2."*

### Section à modifier : "Architecture technique"

```markdown
## Architecture technique

### Légende

| Symbole | Signification |
|---------|---------------|
| ✅ | Implémenté et fonctionnel |
| 🚧 | En cours de développement |
| ⏳ | Planifié Phase 2 |
| ❌ | Non prévu |

### Schéma avec statut d'implémentation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SOURCES EXTERNES                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ ✅ EUR-Lex  │  │ ✅ OpenMeteo│  │ ⏳ Géopol.  │  │ ⏳ Nouvelles│        │
│  │   (Lois EU) │  │   (Météo)   │  │   (ACLED)   │  │   sources   │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         └────────────────┴────────────────┴────────────────┘               │
│                                    ↓                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    🚧 ORCHESTRATEUR (CRON)                           │   │
│  │           Fréquence paramétrable : 1x/jour, 2x/jour, etc.           │   │
│  └─────────────────────────────────┬───────────────────────────────────┘   │
│                                    ↓                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      ✅ AGENT 1A                                     │   │
│  │                   Collecte des documents                             │   │
│  └─────────────────────────────────┬───────────────────────────────────┘   │
│                                    ↓                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      ✅ AGENT 1B                                     │   │
│  │              Analyse de pertinence (30%+30%+40% LLM)                 │   │
│  └─────────────────────────────────┬───────────────────────────────────┘   │
│                                    ↓                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      ✅ AGENT 2                                      │   │
│  │         Analyse d'impact + Projection sur sites/fournisseurs         │   │
│  └─────────────────────────────────┬───────────────────────────────────┘   │
│                                    ↓                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      ✅ LLM JUDGE                                    │   │
│  │                    Score de confiance 0-10                           │   │
│  └─────────────────────────────────┬───────────────────────────────────┘   │
│                                    ↓                                        │
│         ┌──────────────────────────┼──────────────────────────┐            │
│         ↓                          ↓                          ↓            │
│   ┌──────────┐            ┌──────────────┐            ┌──────────┐         │
│   │ Score<7  │            │ Score 7-8.5  │            │Score>8.5 │         │
│   │ ✅ REJET │            │ ⏳ VALIDATION│            │ 🚧 AUTO  │         │
│   │          │            │    HUMAINE   │            │ PUBLIÉ   │         │
│   └──────────┘            └──────────────┘            └──────────┘         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    ✅ BASE DE DONNÉES                                │   │
│  │               Rapports stockés avec timestamp                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    ⏳ NOTIFICATIONS                                  │   │
│  │                Email + Cloche dans l'appli                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    🚧 INTERFACE UTILISATEUR                          │   │
│  │   ✅ Analyse à la demande | 🚧 Dashboard | ⏳ Admin                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```
```

---

# 9. 📋 CHECKLIST RÉCAPITULATIVE

## Éléments à ajouter au CDC

| Section | Élément | Priorité | Statut |
|---------|---------|----------|--------|
| Sources | Documentation EUR-Lex | 🔴 Obligatoire | ☐ |
| Sources | Documentation OpenMeteo | 🔴 Obligatoire | ☐ |
| Sources | Justification des choix | 🔴 Obligatoire | ☐ |
| Budget | Jours-hommes par profil | 🔴 Obligatoire | ☐ |
| Budget | Coûts infrastructure | 🟡 Recommandé | ☐ |
| Budget | Sources payantes potentielles | 🟡 Recommandé | ☐ |
| Planning | Dates concrètes par sprint | 🔴 Obligatoire | ☐ |
| Planning | Jalons avec critères | 🔴 Obligatoire | ☐ |
| Tests | Scénarios UAT | 🔴 Obligatoire | ☐ |
| Tests | Checklist validation métier | 🔴 Obligatoire | ☐ |
| Qualité | Explicabilité IA | 🔴 Obligatoire | ☐ |
| Qualité | Mécanismes de traçabilité | 🔴 Obligatoire | ☐ |
| Paramétrage | Gestion des sources | 🟡 Recommandé | ☐ |
| Paramétrage | Gestion des catégories | 🟡 Recommandé | ☐ |
| Notifications | Types et canaux | ⚪ Phase 2 | ☐ |
| Workflow | Statuts et transitions | ⚪ Phase 2 | ☐ |
| Architecture | Schéma avec statuts | 🔴 Obligatoire | ☐ |
| KPIs | Indicateurs de suivi | 🟡 Recommandé | ☐ |

---

*Document généré le 03/02/2026*
*À intégrer dans le Cahier des Charges existant*
