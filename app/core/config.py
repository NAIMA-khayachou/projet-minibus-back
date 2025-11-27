# app/core/config.py

class Settings:
    # Définition de la configuration OSRM
    OSRM_BASE_URL: str = "http://127.0.0.1:5000"  # L'adresse de votre serveur local Docker
    OSRM_PROFILE: str = "driving"
    # ====c'est le temp pour les requettes======
    OSRM_TIMEOUT: int = 30

# Cette ligne crée l'objet accessible par tous les autres fichiers
settings = Settings()