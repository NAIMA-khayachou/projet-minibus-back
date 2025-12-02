from math import radians, sin, cos, sqrt, atan2 
from app.database.crud import get_all_minibus, get_all_reservations, get_all_stations
from app.Algorithme.genetic_algoritme import GeneticAlgorithm


# -------------------------
# Haversine pour calcul distance
# -------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Rayon de la Terre en km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c


# -------------------------
# Matrice des distances / durées
# -------------------------
def compute_cost_matrices(points):
    n = len(points)
    matrice_distances = [[0 for _ in range(n)] for _ in range(n)]
    matrice_durees = [[0 for _ in range(n)] for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i == j:
                matrice_distances[i][j] = 0
                matrice_durees[i][j] = 0
            else:
                lon1, lat1 = points[i]
                lon2, lat2 = points[j]

                dist_km = haversine(lat1, lon1, lat2, lon2)

                matrice_distances[i][j] = dist_km
                matrice_durees[i][j] = (dist_km / 40) * 60  # durée estimée min

    return matrice_durees, matrice_distances


# -------------------------
# MAIN : optimisation
# -------------------------
def run_optimization():

    stations = get_all_stations()
    points = [(s[3], s[2]) for s in stations]  # (lon, lat)

    # On calcule la matrice avec Haversine
    matrice_durees, matrice_distances = compute_cost_matrices(points)

    stations_dict = {
    s[0]: {  # nouvelle version : clé = nom de la station
        "id": s[0],
        "name": s[1],
        "latitude": s[2],
        "longitude": s[3]
    }
    for s in stations
}


    reservations = get_all_reservations()
    minibus = get_all_minibus()

    ga = GeneticAlgorithm(
        reservations=reservations,
        minibus=minibus,
        stations_dict=stations_dict,
        matrice_distances=matrice_distances,
        matrice_durees=matrice_durees,
        population_size=10,
        generations=10
    )

    best_solution, best_details = ga.run()

    return best_solution, best_details
if __name__ == "__main__":
    best_solution, best_details = run_optimization()
    print("==== BEST SOLUTION ====")
    print(best_solution)
    print("==== DETAILS ====")
    print(best_details)
