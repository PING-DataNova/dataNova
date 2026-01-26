"""Script pour générer le contrat OpenAPI au format JSON et YAML"""

import json
import sys
from pathlib import Path

# Ajouter le projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.main import app

# Générer le schéma OpenAPI
openapi_schema = app.openapi()

# Sauvegarder en JSON
json_path = Path(__file__).parent.parent / "docs" / "openapi.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

print(f"✅ Contrat OpenAPI généré: {json_path}")
print(f"📊 {len(openapi_schema.get('paths', {}))} endpoints documentés")

# Essayer de générer aussi en YAML
try:
    import yaml
    yaml_path = Path(__file__).parent.parent / "docs" / "openapi.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(openapi_schema, f, default_flow_style=False, allow_unicode=True)
    print(f"✅ Contrat OpenAPI YAML généré: {yaml_path}")
except ImportError:
    print("ℹ️  PyYAML non installé, contrat YAML non généré")
    print("   Pour générer le YAML: pip install pyyaml")
