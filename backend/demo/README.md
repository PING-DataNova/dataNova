# Démonstrations des Agents

Scripts de démonstration pour tester manuellement les agents.

## 📋 Scripts disponibles

### 1. **Agent 1A - Collecte de documents**
```bash
python demo/demo_agent_1a.py
```
- Collecte depuis EUR-Lex (lois CBAM)
- Collecte depuis CBAM Guidance (documents officiels)
- Télécharge les PDFs
- Extrait le contenu
- Sauvegarde en BDD avec `workflow_status = "raw"`

### 2. **Agent 1B - Analyse de documents**
```bash
python demo/demo_agent_1b.py
```
- Charge les documents CBAM de la BDD
- Analyse avec 3 niveaux (mots-clés, codes NC, sémantique LLM)
- Calcule le score de pertinence
- Affiche les résultats avec Rich
- Sauvegarde les analyses en BDD

### 3. **Pipeline complet - Agent 1A → 1B**
```bash
python demo/demo_pipeline_complete.py
```
- Exécute Agent 1A (collecte)
- Puis Agent 1B (analyse des documents `workflow_status = "raw"`)
- Affiche les statistiques complètes
- Met à jour `workflow_status = "analyzed"` après analyse

## ⚙️ Configuration requise

1. **Variables d'environnement** (`.env`)
   ```bash
   ANTHROPIC_API_KEY=sk-ant-xxx
   DATABASE_URL=sqlite:///data/agent1.db
   ```

2. **Base de données initialisée**
   ```bash
   python scripts/init_db.py
   ```

3. **Profil entreprise**
   - `data/company_profiles/Hutchinson_SA.json`

## 🧪 Tests unitaires (pytest)

Pour les tests automatisés, utilisez :
```bash
pytest tests/orchestration/test_pipeline.py
```

## 📝 Notes

- Les scripts de démo font de **vrais appels API** et écrivent en BDD
- Agent 1B nécessite une **clé API Anthropic** valide
- Les documents déjà analysés ne sont **pas re-analysés** (vérification via `workflow_status`)
