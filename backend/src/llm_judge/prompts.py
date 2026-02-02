"""
Prompts structurés pour le LLM Judge (Anthropic Claude)
"""

JUDGE_SYSTEM_PROMPT = """Tu es un expert en évaluation de qualité pour les systèmes d'analyse de risques supply chain.

Ton rôle est d'évaluer objectivement la qualité des analyses produites par des agents IA selon des critères précis.

Tu dois :
1. Évaluer chaque critère de manière indépendante
2. Fournir un score de 0 à 10 pour chaque critère
3. Indiquer un niveau de confiance (0-1) pour chaque évaluation
4. Justifier chaque score avec des preuves concrètes
5. Identifier les faiblesses même dans les bonnes analyses

Tu es rigoureux, impartial et constructif dans tes évaluations."""


EVALUATE_PERTINENCE_CHECKER_PROMPT = """Évalue la qualité de l'analyse de pertinence (Pertinence Checker) selon 4 critères.

**DOCUMENT SOURCE** :
{document}

**RÉSULTAT DE L'ANALYSE DE PERTINENCE** :
{pertinence_result}

**CONTEXTE** :
- Nombre de sites Hutchinson : {sites_count}
- Nombre de fournisseurs : {suppliers_count}

---

**CRITÈRES À ÉVALUER** :

1. **Source Relevance** (0-10) :
   - La source citée est-elle fiable et pertinente pour Hutchinson ?
   - La source est-elle officielle, vérifiable et à jour ?
   
2. **Company Data Alignment** (0-10) :
   - Les données internes Hutchinson sont-elles correctement interprétées ?
   - Les entités affectées identifiées sont-elles cohérentes avec les données ?
   
3. **Logical Coherence** (0-10) :
   - La conclusion (OUI/NON/PARTIELLEMENT) découle-t-elle logiquement des preuves ?
   - Le raisonnement est-il structuré et sans contradictions ?
   
4. **Traceability** (0-10) :
   - Chaque affirmation est-elle tracée à une source ou une donnée ?
   - Les entités affectées sont-elles clairement identifiées ?

---

**FORMAT DE RÉPONSE REQUIS** (JSON strict) :

```json
{{
  "source_relevance": {{
    "score": <0-10>,
    "confidence": <0.0-1.0>,
    "comment": "<1-2 phrases>",
    "evidence": ["<preuve 1>", "<preuve 2>", ...],
    "weaknesses": ["<faiblesse 1>", "<faiblesse 2>", ...]
  }},
  "company_data_alignment": {{
    "score": <0-10>,
    "confidence": <0.0-1.0>,
    "comment": "<1-2 phrases>",
    "evidence": [...],
    "weaknesses": [...]
  }},
  "logical_coherence": {{
    "score": <0-10>,
    "confidence": <0.0-1.0>,
    "comment": "<1-2 phrases>",
    "evidence": [...],
    "weaknesses": [...]
  }},
  "traceability": {{
    "score": <0-10>,
    "confidence": <0.0-1.0>,
    "comment": "<1-2 phrases>",
    "evidence": [...],
    "weaknesses": [...]
  }}
}}
```

Réponds UNIQUEMENT avec le JSON, sans texte avant ou après."""


EVALUATE_RISK_ANALYZER_PROMPT = """Évalue la qualité de l'analyse de risque (Risk Analyzer) selon 8 critères.

**DOCUMENT SOURCE** :
{document}

**RÉSULTAT DE L'ANALYSE DE PERTINENCE** :
{pertinence_result}

**RÉSULTAT DE L'ANALYSE DE RISQUE** :
{risk_analysis}

**CONTEXTE** :
- Nombre de sites Hutchinson : {sites_count}
- Nombre de fournisseurs : {suppliers_count}
- Nombre de relations site-fournisseur : {relationships_count}

---

**CRITÈRES À ÉVALUER** :

1. **Source Relevance** (0-10) :
   - Les sources utilisées sont-elles fiables et pertinentes ?
   
2. **Company Data Alignment** (0-10) :
   - Les données Hutchinson sont-elles correctement utilisées ?
   - Les entités impactées sont-elles cohérentes ?
   
3. **Logical Coherence** (0-10) :
   - L'analyse en cascade est-elle logique et cohérente ?
   - Les niveaux de risque sont-ils justifiés ?
   
4. **Completeness** (0-10) :
   - Tous les aspects importants sont-ils couverts ?
   - Sites, fournisseurs, cascade, timeline, coûts ?
   
5. **Recommendation Appropriateness** (0-10) :
   - Les recommandations sont-elles concrètes et actionnables ?
   - Sont-elles priorisées et avec des timelines réalistes ?
   
6. **Traceability** (0-10) :
   - Chaque affirmation est-elle tracée à une source/donnée ?
   - Les calculs sont-ils transparents ?
   
7. **Strategic Alignment** (0-10) :
   - L'analyse est-elle alignée avec les priorités stratégiques Hutchinson ?
   - Les sites critiques sont-ils correctement priorisés ?
   
8. **Actionability Timeline** (0-10) :
   - Les timelines sont-elles réalistes et actionnables ?
   - Les actions immédiates sont-elles clairement identifiées ?

---

**FORMAT DE RÉPONSE REQUIS** (JSON strict) :

```json
{{
  "source_relevance": {{
    "score": <0-10>,
    "confidence": <0.0-1.0>,
    "comment": "<1-2 phrases>",
    "evidence": ["<preuve 1>", "<preuve 2>", ...],
    "weaknesses": ["<faiblesse 1>", "<faiblesse 2>", ...]
  }},
  "company_data_alignment": {{ ... }},
  "logical_coherence": {{ ... }},
  "completeness": {{ ... }},
  "recommendation_appropriateness": {{ ... }},
  "traceability": {{ ... }},
  "strategic_alignment": {{ ... }},
  "actionability_timeline": {{ ... }}
}}
```

Réponds UNIQUEMENT avec le JSON, sans texte avant ou après."""


FINAL_DECISION_PROMPT = """Détermine l'action recommandée basée sur les scores et la confiance.

**SCORES** :
- Pertinence Checker : {pertinence_score}/10 (confiance: {pertinence_confidence})
- Risk Analyzer : {risk_score}/10 (confiance: {risk_confidence})
- Score Global : {overall_score}/10 (confiance: {overall_confidence})

**RÈGLES DE DÉCISION** :

1. **APPROVE** (Alerte immédiate) :
   - Score global ≥ 8.5 ET confiance globale ≥ 0.85
   
2. **REVIEW** (Validation humaine) :
   - Score global ≥ 8.5 ET confiance < 0.85
   - OU score global 7.0-8.4 ET confiance ≥ 0.80
   
3. **REVIEW_PRIORITY** (Validation humaine prioritaire) :
   - Score global 7.0-8.4 ET confiance < 0.80
   
4. **REJECT** (Archiver) :
   - Score global < 7.0

---

**FORMAT DE RÉPONSE REQUIS** (JSON strict) :

```json
{{
  "action_recommended": "<APPROVE|REVIEW|REVIEW_PRIORITY|REJECT>",
  "reasoning": "<Explication en 2-3 phrases>"
}}
```

Réponds UNIQUEMENT avec le JSON, sans texte avant ou après."""
