import requests
from app.core.config import settings
from typing import Tuple, List, Optional

# Utilisation des variables de configuration
OSRM_URL = settings.OSRM_BASE_URL 
OSRM_TIMEOUT = settings.OSRM_TIMEOUT
OSRM_PROFILE = settings.OSRM_PROFILE

# Définition des types pour la matrice
Matrix = List[List[float]]

def get_cost_matrices(
    points: List[Tuple[float, float]]
) -> Tuple[Optional[Matrix], Optional[Matrix]]:
    """
    Génère les matrices de temps de trajet (durations) et de distance (distances)
    entre tous les points en interrogeant le service OSRM /table.

    :param points: Liste de coordonnées [(lon1, lat1), (lon2, lat2), ...]
    :return: Tuple (matrice_temps, matrice_distance), ou (None, None) en cas d'erreur.
    """
    
    if not points:
        return ([], [])

    # 1. Formatage des coordonnées OSRM : lon1,lat1;lon2,lat2;...
    # Attention : OSRM utilise Longitude, Latitude
    coordinates_str = ";".join([f"{lon},{lat}" for lon, lat in points])
    
    # 2. Construction de l'URL pour le service /table
    # annotations=duration,distance demande les deux matrices.
    # durations = temps en secondes
    # distances = distances en mètres
    url = f"{OSRM_URL}/table/v1/{OSRM_PROFILE}/{coordinates_str}?annotations=duration,distance"
    
    try:
        # Envoi de la requête HTTP au serveur OSRM local
        response = requests.get(url, timeout=OSRM_TIMEOUT)
        response.raise_for_status() # Lève une erreur si le statut est 4xx ou 5xx
        
        # la réponse json 
        data = response.json()
        
        # 3. Extraction des matrices
        matrice_temps = data.get('durations')
        matrice_distance = data.get('distances')
        
        if matrice_temps is not None and matrice_distance is not None:
            # Succès : retourne le tuple (temps, distance)
            return (matrice_temps, matrice_distance)
        else:
            # Cas où OSRM renvoie un statut OK, mais une des matrices est absente
            print(f"Erreur OSRM: Les clés 'durations' ou 'distances' sont manquantes dans la réponse OSRM. Code: {data.get('code')}")
            return (None, None)

    except requests.exceptions.RequestException as e:
        # Gère les erreurs de connexion (serveur non démarré, Timeout, etc.)
        print(f"Erreur de connexion OSRM: {e}. L'URL était: {url}")
        return (None, None)
"""
# --- 4. Exemple de Test Mis à Jour ---
if __name__ == '__main__':
    # Deux points de test à Marrakech (lon, lat)
    points_test = [
        (-8.0084, 31.6372), # Point A
        (-8.0305, 31.6256), # Point B
        (-8.0190, 31.6300)  # Point C
    ]
    
    temps_matrix, distance_matrix = get_cost_matrices(points_test)
    
    print("\n=============================================")
    print("Matrice de Coûts (Temps en secondes) :")
    print(temps_matrix)
    
    if temps_matrix and distance_matrix:
        print("\nTemps de A à B (secondes):", temps_matrix[0][1])
        print("Temps de B à A (secondes):", temps_matrix[1][0])

        print("\n=============================================")
        print("Matrice des Distances (en mètres) :")
        print(distance_matrix)
        
        print("\nDistance de A à B (mètres):", distance_matrix[0][1])
        print("Distance de B à A (mètres):", distance_matrix[1][0])
    
    print("=============================================")
    """