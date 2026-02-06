"""
Point d'entrée de l'API FastAPI
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import analyses, impacts, auth, pipeline, supplier, admin, documents, subscriptions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application (startup/shutdown)."""
    # Startup
    print("[MAIN] Initialisation du scheduler automatique...")
    admin.init_scheduler()
    
    # Init DB + Seed en background (pour ne pas bloquer le health check)
    import os, threading
    def init_and_seed():
        try:
            from src.storage.database import init_db, get_engine, drop_all_tables
            # Si RESET_DB=true, on drop tout d'abord
            if os.environ.get("RESET_DB") == "true":
                print("[MAIN] 🔴 RESET_DB=true → DROP toutes les tables...")
                drop_all_tables()
                print("[MAIN] Tables supprimées, recréation...")
            init_db()
            print("[MAIN] Tables créées ✅")
        except Exception as e:
            print(f"[MAIN] Erreur init_db: {e}")
        try:
            import subprocess
            subprocess.run(["python", "scripts/seed_database.py"], timeout=120)
            print("[MAIN] Seed terminé ✅")
        except Exception as e:
            print(f"[SEED] Erreur: {e}")
    threading.Thread(target=init_and_seed, daemon=True).start()
    
    yield  # Application en cours d'exécution
    
    # Shutdown
    print("[MAIN] Arrêt du scheduler...")
    admin.shutdown_scheduler()


# Créer l'application FastAPI
app = FastAPI(
    title="DataNova API",
    description="API de veille réglementaire pour Hutchinson SA",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS pour le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:3005",
        "http://localhost:3006",
        "http://localhost:3007",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
        "http://127.0.0.1:3004",
        "http://127.0.0.1:3005",
        "http://127.0.0.1:3006",
        "http://127.0.0.1:3007",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=r"https://.*\.azurestaticapps\.net",  # Accepte tous les Static Web Apps
)

# Enregistrer les routes
app.include_router(auth.router)
app.include_router(analyses.router, prefix="/api")
app.include_router(impacts.router, prefix="/api")
app.include_router(pipeline.router, prefix="/api")
app.include_router(supplier.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(subscriptions.router)  # Note: prefix déjà dans le router


@app.get("/")
def root():
    """Point d'entrée racine"""
    return {
        "name": "DataNova API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check pour monitoring"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)