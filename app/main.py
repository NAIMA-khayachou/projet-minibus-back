# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database.connection import db
from .routers import auth, stations, drivers, optimization, metrics, buses
import logging
from app.routers import buses

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Minibus Transport API",
    description="API pour le système de transport par minibus à Marrakech",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routers
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(stations.router, prefix="/api", tags=["Stations"])  # ✅ Important
app.include_router(drivers.router, prefix="/api", tags=["Drivers"])
app.include_router(buses.router, prefix="/api/minibus", tags=["buses"])
app.include_router(optimization.router, prefix="/api", tags=["Optimization"])
app.include_router(metrics.router, prefix="/api", tags=["Metrics"])

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Démarrage de l'application...")
    if db.test_connection():
        logger.info("✅ Connexion à la base de données réussie")
    else:
        logger.error("❌ Échec de la connexion à la base de données")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Arrêt de l'application...")
    db.close_all_connections()

@app.get("/")
async def root():
    return {
        "message": "API Minibus Transport - Marrakech",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    db_status = db.test_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected"
    }