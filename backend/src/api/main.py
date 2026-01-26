"""
Point d'entrée de l'API FastAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import analyses, impacts

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
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative port
        "http://localhost:3001",  # Alternative port 2
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrer les routes
app.include_router(analyses.router, prefix="/api")
app.include_router(impacts.router, prefix="/api")


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