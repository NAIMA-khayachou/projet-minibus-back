from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from typing import Optional
from app.internal.route_service import router as route_service_router

# -------------------------------------------------
# ⚠️ FASTAPI INSTANCE (1 seule fois)
# -------------------------------------------------
app = FastAPI(title="Minibus Route Optimization API")
app.include_router(route_service_router)

# -------------------------------------------------
# CONFIG DATABASE
# -------------------------------------------------
DATABASE_URL = "postgresql://admin:admin@localhost:5432/projet_minibus"
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -------------------------------------------------
# MODEL User (correspond exactement à ta table SQL)
# -------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), default="chauffeur")
    chauffeur_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(String, default=True)

# -------------------------------------------------
# Pydantic Models
# -------------------------------------------------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    role: str

    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    token: str
    user: UserResponse

# -------------------------------------------------
# CONFIG CORS
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# PASSWORD HASHING
# -------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, stored_password: str) -> bool:
    return plain_password == stored_password

# -------------------------------------------------
# JWT TOKEN
# -------------------------------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# -------------------------------------------------
# DB Session
# -------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------------------------
# LOGIN ROUTE
# -------------------------------------------------
@app.post("/api/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == login_data.email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    if not verify_password(login_data.password, user.password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    # Generate JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )

    return LoginResponse(
        token=access_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            role=user.role
        )
    )

# -------------------------------------------------
# ROUTES IMPORT
# -------------------------------------------------
try:
    from app.routers.routes import router
    app.include_router(router)
except ImportError:
    print("Routes d'optimisation non trouvées.")

# -------------------------------------------------
# RUN SERVER
# -------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
