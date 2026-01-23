"""
TODO: Outil analyse sémantique LLM (LangChain @tool)

Tâches:
1. Décorer avec @tool
2. Créer prompt template pour analyse
3. Découper texte si trop long (chunking)
4. Appeler Claude/GPT pour analyse
5. Parser la réponse en score 0-1

Prompt à inclure:
- Contexte entreprise
- Type de réglementation
- Question: "Ce document est-il pertinent pour l'entreprise?"

Pondération: 40% du score final
"""
