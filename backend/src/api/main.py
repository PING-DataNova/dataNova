"""
Point d'entrée de l'API FastAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import analyses, impacts, auth, pipeline, supplier
from src.storage.database import init_db

# Initialiser la base de données (créer les tables si nécessaire)
init_db()

# Créer l'application FastAPI
app = FastAPI(
    title="DataNova API",
    description="API de veille réglementaire pour Hutchinson SA",
    version="1.0.0"
)

# Configuration CORS pour le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
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