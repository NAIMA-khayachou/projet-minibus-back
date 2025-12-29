from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database.connection import db
from .routers import auth, stations, drivers, optimization, metrics, buses
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Création de l'application FastAPI
app = FastAPI(
    title="Minibus Transport API",
    description="API pour le système de transport par minibus à Marrakech",
    version="1.0.0"
)

# Configuration CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(stations.router, tags=["Stations"])
app.include_router(drivers.router, tags=["Drivers"])
app.include_router(optimization.router, tags=["Optimization"])
app.include_router(metrics.router, tags=["Metrics"])
app.include_router(buses.router, tags=["Buses"])

@app.on_event("startup")
async def startup_event():
    """Test de la connexion à la base de données au démarrage"""
    logger.info("🚀 Démarrage de l'application...")
    if db.test_connection():
        logger.info("✅ Connexion à la base de données réussie")
    else:
        logger.error("❌ Échec de la connexion à la base de données")

@app.on_event("shutdown")
async def shutdown_event():
    """Fermeture des connexions à la base de données"""
    logger.info("🛑 Arrêt de l'application...")
    db.close_all_connections()

@app.get("/")
async def root():
    """Point d'entrée de l'API"""
    return {
        "message": "API Minibus Transport - Marrakech",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Vérification de l'état de l'API"""
    db_status = db.test_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected"
    }
