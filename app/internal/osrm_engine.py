# Dans app/internal/osrm_engine.py

# 1. On importe l'instance de la configuration
from app.core.config import settings 

import requests
# 2. On utilise l'adresse
OSRM_URL = settings.OSRM_BASE_URL 
# OSRM_URL vaudra alors "http://127.0.0.1:5000" (si vous l'avez mis à jour)


# --- 1. Récupération des Configurations ---
# On utilise les variables pour l'URL, le timeout et le profil
OSRM_URL = settings.OSRM_BASE_URL
OSRM_TIMEOUT = settings.OSRM_TIMEOUT
OSRM_PROFILE = settings.OSRM_PROFILE

# --- 2. Fonction Principale ---
def get_cost_matrix(points: list[tuple[float, float]]) -> list[list[float]]:
    """
    Génère une matrice de coûts (temps de trajet) entre tous les points 
    en interrogeant le service OSRM /table.

    :param points: Liste de coordonnées [(lon1, lat1), (lon2, lat2), ...]
    :return: Matrice carrée des temps de trajet en secondes, ou une liste vide.
    """
    
    if not points:
        return []

    # Formatage des coordonnées OSRM : lon1,lat1;lon2,lat2;...
    # Attention : OSRM utilise Longitude, Latitude (et non Latitude, Longitude)
    coordinates_str = ";".join([f"{lon},{lat}" for lon, lat in points])
    
    # Construction de l'URL pour le service /table
    # annotations=duration demande les temps de trajet en secondes.
    url = f"{OSRM_URL}/table/v1/{OSRM_PROFILE}/{coordinates_str}?annotations=duration"
    
    try:
        # Envoi de la requête HTTP au serveur OSRM local
        response = requests.get(url, timeout=OSRM_TIMEOUT)
        response.raise_for_status() # Lève une erreur si la réponse est 4xx ou 5xx
        
        data = response.json()
        
        # Extraction de la matrice : 'durations' contient la matrice des temps
        if 'durations' in data:
            return data['durations']
        else:
            # Cas où OSRM renvoie un statut OK, mais la matrice est absente
            print(f"Erreur OSRM: La clé 'durations' est manquante dans la réponse OSRM. Code: {data.get('code')}")
            return []

    except requests.exceptions.RequestException as e:
        # Gère les erreurs de connexion (Timeout, serveur non joignable, etc.)
        print(f"Erreur de connexion OSRM: {e}. Vérifiez que le conteneur est lancé (docker ps).")
        return []

# --- 3. Exemple de Test ---
# Pour tester (décommenter et exécuter le fichier si vous le souhaitez)
if __name__ == '__main__':
     # Deux points de test à Marrakech (lon, lat)
     points_test = [
         (-8.0084, 31.6372),
         (-8.0305, 31.6256)
    ]
     matrix = get_cost_matrix(points_test)
     print("\nMatrice de Coûts (Temps en secondes) :")
     print(matrix)