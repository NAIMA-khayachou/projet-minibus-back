from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# 1. Imports de la base de données et des routeurs
from .database.connection import db
# On importe tous les routeurs des deux branches pour ne rien perdre
from .routers import auth, stations, drivers, optimization, metrics, buses, reservations_routes 
from .ai.routers import prediction_routes

# 2. Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 3. Initialisation de l'application
app = FastAPI(
    title="Minibus Transport & Reservation API",
    description="Système complet : Gestion de flotte, Optimisation de tournée et Prédiction IA",
    version="1.0.0"
)

# 4. Configuration CORS (Indispensable pour la liaison avec React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Autorise toutes les origines pour le développement
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Inclusion de TOUTES les routes (Fusion sans répétition)

# --- Routes de Gestion ---
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(stations.router, prefix="/api", tags=["Stations"])
app.include_router(drivers.router, prefix="/api", tags=["Drivers"])
app.include_router(buses.router, prefix="/api", tags=["Buses"])
app.include_router(optimization.router, prefix="/api", tags=["Optimization"])
app.include_router(metrics.router, prefix="/api", tags=["Metrics"])

# --- Routes IA et Réservations ---
app.include_router(reservations_routes.router, prefix="/api", tags=["Reservations"])
app.include_router(prediction_routes.predict_router, prefix="/api", tags=["Prediction"])

# 6. Gestion des événements (Startup / Shutdown)
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Démarrage de l'API Minibus...")
    try:
        if db.test_connection():
            logger.info("✅ Connexion à la base de données réussie")
        else:
            logger.error("❌ Échec de la connexion à la base de données")
    except Exception as e:
        logger.error(f"❌ Erreur lors du test DB : {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Arrêt de l'application...")
    try:
        db.close_all_connections()
        logger.info("✅ Connexions DB fermées proprement")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la fermeture : {e}")

# 7. Routes de base et Santé (Health Check)
@app.get("/")
async def root():
    return {
        "message": "API Minibus Transport - Marrakech",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/api/health", tags=["health"])
async def health_check():
    db_status = db.test_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected"
    }

# 8. Gestionnaire d'erreurs global (Sécurité IA)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erreur non gérée sur {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Une erreur interne est survenue",
            "error": str(exc)
        }
    )