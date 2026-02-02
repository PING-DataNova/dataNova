"""
Routes d'authentification (inscription et connexion)
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from src.storage.database import get_session
from src.storage.models import User
from src.utils.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# Schémas Pydantic
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str  # 'juridique' ou 'decisive'


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str


class LoginResponse(BaseModel):
    token: str
    user: UserResponse


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: RegisterRequest, session: Session = Depends(get_session)):
    """
    Inscription d'un nouvel utilisateur
    
    Args:
        data: Email, mot de passe, nom, rôle
        session: Session SQLAlchemy
        
    Returns:
        Informations de l'utilisateur créé
        
    Raises:
        HTTPException 400: Email déjà utilisé
        HTTPException 400: Rôle invalide
    """
    # Vérifier que le rôle est valide
    if data.role not in ['juridique', 'decisive']:
        raise HTTPException(
            status_code=400,
            detail="Le rôle doit être 'juridique' ou 'decisive'"
        )
    
    # Vérifier que l'email n'existe pas déjà
    existing_user = session.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Un compte existe déjà avec cet email"
        )
    
    # Créer l'utilisateur
    # Séparer le nom complet en prénom/nom
    name_parts = data.name.strip().split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ''
    
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=first_name,
        last_name=last_name,
        role=data.role,
        active=True
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=f"{user.first_name} {user.last_name}".strip(),
        role=user.role
    )


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, session: Session = Depends(get_session)):
    """
    Connexion d'un utilisateur existant
    
    Args:
        data: Email et mot de passe
        session: Session SQLAlchemy
        
    Returns:
        Token JWT et informations utilisateur
        
    Raises:
        HTTPException 401: Identifiants invalides
        HTTPException 403: Compte désactivé
    """
    # Récupérer l'utilisateur par email
    user = session.query(User).filter(User.email == data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Email ou mot de passe incorrect"
        )
    
    # Vérifier le mot de passe
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Email ou mot de passe incorrect"
        )
    
    # Vérifier que le compte est actif
    if not user.active:
        raise HTTPException(
            status_code=403,
            detail="Ce compte a été désactivé"
        )
    
    # Mettre à jour la date de dernière connexion
    user.last_login = datetime.utcnow()
    session.commit()
    
    # Créer le token JWT
    token_data = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role
    }
    token = create_access_token(token_data)
    
    return LoginResponse(
        token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=f"{user.first_name} {user.last_name}".strip(),
            role=user.role
        )
    )


@router.get("/me", response_model=UserResponse)
def get_current_user(token: str, session: Session = Depends(get_session)):
    """
    Récupère les informations de l'utilisateur connecté
    
    Args:
        token: Token JWT dans le header Authorization
        session: Session SQLAlchemy
        
    Returns:
        Informations de l'utilisateur
        
    Raises:
        HTTPException 401: Token invalide ou expiré
    """
    from src.utils.auth import verify_token
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Token invalide ou expiré"
        )
    
    user_id = payload.get("user_id")
    user = session.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Utilisateur introuvable"
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=f"{user.first_name} {user.last_name}".strip(),
        role=user.role
    )
