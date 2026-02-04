"""
Repository pour la gestion des sources de données
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from src.storage.models import DataSource
from src.storage.database import get_session
import structlog

logger = structlog.get_logger()


class DataSourceRepository:
    """Repository pour les opérations CRUD sur DataSource"""
    
    def __init__(self, session: Session = None):
        self.session = session or get_session()
        self._owns_session = session is None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._owns_session:
            self.session.close()
    
    def get_all(self) -> List[DataSource]:
        """Récupère toutes les sources de données"""
        return self.session.query(DataSource).all()
    
    def get_active(self) -> List[DataSource]:
        """Récupère les sources actives uniquement"""
        return self.session.query(DataSource).filter(DataSource.is_active == True).all()
    
    def get_by_name(self, name: str) -> Optional[DataSource]:
        """Récupère une source par son nom"""
        return self.session.query(DataSource).filter(DataSource.name == name).first()
    
    def get_by_id(self, source_id: str) -> Optional[DataSource]:
        """Récupère une source par son ID"""
        return self.session.query(DataSource).filter(DataSource.id == source_id).first()
    
    def create(self, name: str, source_type: str, config: Dict = None, is_active: bool = True) -> DataSource:
        """Crée une nouvelle source de données"""
        source = DataSource(
            name=name,
            source_type=source_type,
            config=config or {},
            is_active=is_active
        )
        self.session.add(source)
        self.session.commit()
        self.session.refresh(source)
        return source
    
    def update(self, source_id: str, **kwargs) -> Optional[DataSource]:
        """Met à jour une source de données"""
        source = self.get_by_id(source_id)
        if not source:
            return None
        
        for key, value in kwargs.items():
            if hasattr(source, key):
                setattr(source, key, value)
        
        self.session.commit()
        self.session.refresh(source)
        return source
    
    def toggle_active(self, source_id: str) -> Optional[DataSource]:
        """Active/désactive une source"""
        source = self.get_by_id(source_id)
        if not source:
            return None
        
        source.is_active = not source.is_active
        self.session.commit()
        self.session.refresh(source)
        return source
    
    def delete(self, source_id: str) -> bool:
        """Supprime une source de données"""
        source = self.get_by_id(source_id)
        if not source:
            return False
        
        self.session.delete(source)
        self.session.commit()
        return True
    
    def is_source_active(self, name: str) -> bool:
        """Vérifie si une source est active par son nom"""
        source = self.get_by_name(name)
        if source:
            return source.is_active
        return True  # Par défaut, active si non trouvée
    
    def get_by_risk_type(self, risk_type: str) -> List[DataSource]:
        """Récupère les sources par type de risque"""
        return self.session.query(DataSource).filter(DataSource.risk_type == risk_type).all()
