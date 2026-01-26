# Agent 2 - Analyse d'impact

**Responsable** : Dev 4

## Mission

Analyser l'impact des lois validees (analyses approuvees) sur l'entreprise et
produire des metriques d'impact exploitables.

## Workflow

```
Input: Analyses avec validation_status="approved"
   |
1. Charger l'analyse et le document
   |
2. Charger les donnees entreprise (company_processes)
   |
3. Faire le matching loi <-> donnees entreprise
   |
4. Produire les metriques d'impact
   |
5. Creer ImpactAssessment
   |
Output: ImpactAssessment (1 ligne par loi)
```

## Base de donnees

### Input (lecture)
- `analyses` (validation_status="approved")
- `documents` (workflow_status="validated")
- `company_processes`

### Output (ecriture)
- `impact_assessments` (nouvelle entree)

## Metriques d'impact (sans score chiffre)

- `risk_main` (choix predefini)
- `impact_level` (faible | moyen | eleve)
- `risk_details` (texte libre)
- `modality` (choix predefini)
- `deadline` (format MM-YYYY)
- `recommendation` (texte libre)

## Fichiers a implementer

### 1. `agent.py`
Classe principale `Agent2` avec :
- `__init__()` : Initialisation LLM + outils
- `run()` : Pipeline principal
- `analyze_impact(analysis_id)` : Analyse une regulation validee

### 2. `tools/impact_analyzer.py`
Outil pour produire les metriques d'impact.

### 3. `tools/action_recommender.py`
Outil pour proposer une recommendation textuelle.

### 4. `prompts/agent_2_prompt.py`
Prompt principal oriente metriques d'impact.

## Modeles SQLAlchemy

- `ImpactAssessment` (metriques d'impact)
- `Analysis` (lien loi validee)
- `CompanyProcess` (donnees entreprise)

## Tests (a creer)

- `tests/test_agent_2.py`
- Test `analyze_impact()`
- Test `generate_recommendations()`
- Test creation `ImpactAssessment`

## Exemple d'output

```json
{
  "analysis_id": "analysis_456",
  "regulation_type": "CBAM",
  "risk_main": "fiscal",
  "impact_level": "eleve",
  "risk_details": "Taxes carbone sur imports acier",
  "modality": "certificat",
  "deadline": "12-2025",
  "recommendation": "Prioriser transport bas-carbone et preparer les certificats CO2."
}
```
