"""
Dépendances FastAPI
"""

from typing import Generator
from src.storage.database import SessionLocal


def get_db() -> Generator:
    """
    Fournit une session de base de données.
    
    Yields:
        Session SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
