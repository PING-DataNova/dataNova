"""
TODO: Outil calcul score final (LangChain @tool)

Tâches:
1. Décorer avec @tool
2. Agréger les 3 scores (keywords, NC, LLM)
3. Appliquer pondération (0.3 + 0.3 + 0.4)
4. Déterminer criticité (Critique/Élevé/Moyen/Faible)
5. Retourner résultat structuré

Seuils de criticité:
- CRITIQUE: score >= 0.8
- ÉLEVÉ: 0.6 <= score < 0.8
- MOYEN: 0.4 <= score < 0.6
- FAIBLE: 0.2 <= score < 0.4
- INFO: score < 0.2
"""
