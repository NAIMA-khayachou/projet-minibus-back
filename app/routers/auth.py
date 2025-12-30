from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
from ..database import crud
import bcrypt
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter()

# Configuration JWT
SECRET_KEY = "your-secret-key-change-in-production"  # À changer en production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Modèles Pydantic
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    user: dict
    access_token: str
    token_type: str = "bearer"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crée un token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
def get_password_hash(password):
    """Génère un hash bcrypt pour un mot de passe en clair"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')
def verify_password(plain_password, hashed_password):
    """Vérifie le mot de passe avec bcrypt"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

@router.post("/login", response_model=LoginResponse)

async def login(credentials: LoginRequest):
    """
    Authentification de l'utilisateur via la base de données
    """
    logger.info(f"Tentative de connexion pour: {credentials.email}")
    
    start_time = time.time()
    
    # Recherche de l'utilisateur dans la base de données
    db_start = time.time()
    user = crud.get_user_by_email(credentials.email)
    db_time = time.time() - db_start
    logger.info(f"⏱️ DB took: {db_time:.4f}s")
    
    if not user:
        logger.warning(f"Utilisateur non trouvé: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Vérification du mot de passe
    hash_start = time.time()
    if not verify_password(credentials.password, user["password"]):
        logger.warning(f"Mot de passe incorrect pour: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    hash_time = time.time() - hash_start
    logger.info(f"⏱️ Password hashing verify took: {hash_time:.4f}s")
    
    total_time = time.time() - start_time
    logger.info(f"⏱️ Total login time: {total_time:.4f}s")
    
    # Création du token JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"], "id": user["id"]},
        expires_delta=access_token_expires
    )
    
    # Retour de l'utilisateur sans le mot de passe
    user_data = {k: v for k, v in user.items() if k != "password"}
    
    logger.info(f"✅ Connexion réussie pour: {credentials.email} (role: {user['role']})")
    
    return {
        "user": user_data,
        "access_token": access_token,
        "token_type": "bearer"
    }
