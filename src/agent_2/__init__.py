"""
Agent 2 - Analyse d'impact et recommandations

Agent responsable de :
- Analyse d'impact des lois validees
- Matching avec donnees entreprise
- Generation des metriques d'impact
- Creation des ImpactAssessment

Workflow :
1. Recupere les analyses avec validation_status="approved"
2. Charge les donnees company_processes
3. Produit risk_main, impact_level, risk_details, modality, deadline, recommendation
4. Cree ImpactAssessment

Responsable : Dev 4
"""

from .agent import Agent2

__all__ = ["Agent2"]
