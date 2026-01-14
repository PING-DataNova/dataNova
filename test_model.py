import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Modèles à tester
models = [
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-5-sonnet-20241022",
    "claude-3-haiku-20240307",
]

print("🔍 Test des modèles Claude disponibles...\n")

for model in models:
    try:
        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Test"}]
        )
        print(f"✅ {model} → FONCTIONNE")
    except anthropic.NotFoundError:
        print(f"❌ {model} → N'existe pas")
    except Exception as e:
        print(f"⚠️ {model} → Erreur: {str(e)[:50]}")

print("\n✅ Test terminé !")