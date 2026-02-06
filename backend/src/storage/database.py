"""
Configuration SQLAlchemy et gestion de la base de données

Documentation: docs/DATABASE_SCHEMA.md
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from src.storage.models import Base
from src.config import settings


# Configuration du moteur de base de données
def get_database_url() -> str:
    """
    Récupère l'URL de connexion à la base de données
    
    Supporte:
    - SQLite (développement): sqlite:///data/datanova.db
    - PostgreSQL (production): postgresql://user:pass@host/db
    
    Returns:
        URL de connexion
    """
    db_url = getattr(settings, 'database_url', None)
    
    if db_url:
        return db_url
    
    # Par défaut: SQLite en développement
    data_dir = os.path.join(os.path.dirname(__file__), "../../data")
    os.makedirs(data_dir, exist_ok=True)
    
    db_path = os.path.join(data_dir, "datanova.db")
    return f"sqlite:///{db_path}"


def create_db_engine():
    """
    Crée le moteur SQLAlchemy
    
    Configuration:
    - SQLite: active les foreign keys
    - PostgreSQL: pool de connexions
    
    Returns:
        Engine SQLAlchemy
    """
    database_url = get_database_url()
    
    # Log pour savoir quelle base est utilisée
    db_type = "PostgreSQL" if database_url.startswith("postgresql") else "SQLite"
    print(f"🗄️  DATABASE: {db_type}")
    print(f"   URL: {database_url.split('@')[-1] if '@' in database_url else database_url}")
    
    if database_url.startswith("sqlite"):
        # SQLite: pool statique + echo pour debug
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False  # Mettre True pour voir les requêtes SQL
        )
        
        # Activer les foreign keys pour SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    else:
        # PostgreSQL ou autre
        engine = create_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            echo=False
        )
    
    return engine


# Lazy engine: ne se connecte qu'au premier appel
_engine = None
_SessionLocal = None


def get_engine():
    """Retourne le moteur SQLAlchemy (lazy init)"""
    global _engine
    if _engine is None:
        _engine = create_db_engine()
    return _engine


def get_session_factory():
    """Retourne le session factory (lazy init)"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


# Compatibilité: SessionLocal reste accessible mais lazy
class _LazySessionLocal:
    """Proxy pour SessionLocal avec lazy init"""
    def __call__(self, *args, **kwargs):
        return get_session_factory()(*args, **kwargs)
    def __getattr__(self, name):
        return getattr(get_session_factory(), name)

SessionLocal = _LazySessionLocal()


def get_session() -> Session:
    """
    Crée une nouvelle session de base de données
    
    Usage:
        session = get_session()
        try:
            # utiliser la session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
    
    Returns:
        Session SQLAlchemy
    """
    return SessionLocal()


def init_db():
    """
    Initialise la base de données (crée toutes les tables)
    
    Usage:
        from src.storage.database import init_db
        init_db()
    
    Note: Utilise Base.metadata.create_all() - idempotent
    """
    print("🔨 Création des tables de base de données...")
    Base.metadata.create_all(bind=get_engine())
    print("✅ Base de données initialisée avec succès!")
    
    # Afficher les tables créées
    tables = Base.metadata.tables.keys()
    print(f"📋 Tables créées: {', '.join(tables)}")


def drop_all_tables():
    """
    Supprime toutes les tables (DANGER: perte de données)
    
    Usage en développement uniquement:
        from src.storage.database import drop_all_tables
        drop_all_tables()
    """
    print("⚠️  Suppression de toutes les tables...")
    Base.metadata.drop_all(bind=get_engine())
    print("✅ Toutes les tables ont été supprimées")


def get_db_context():
    """
    Context manager pour gérer automatiquement les sessions
    
    Usage:
        with get_db_context() as session:
            repo = DocumentRepository(session)
            repo.save(document)
            # Commit automatique si pas d'exception
    
    Yields:
        Session SQLAlchemy
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
