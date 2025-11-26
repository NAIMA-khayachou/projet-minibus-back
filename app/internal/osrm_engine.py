# Dans app/internal/osrm_engine.py

# 1. On importe l'instance de la configuration
from core.config import settings 

# 2. On utilise l'adresse
OSRM_URL = settings.OSRM_BASE_URL 
# OSRM_URL vaudra alors "http://127.0.0.1:5000" (si vous l'avez mis à jour)