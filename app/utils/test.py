from app.internal.test_algo import run_algorithm
from .geo import MapVisualizer

# Lancer l'algorithme et récupérer la solution
best_solution, best_details, minibus_list, stations_dict = run_algorithm()
if best_solution:
    # Créer la carte
    visualizer = MapVisualizer(center_lat=31.6295, center_lon=-7.9811)
    visualizer.create_base_map()

    # Ajouter les itinéraires
    visualizer.visualize_solution(best_solution, stations_dict)

    # Ajouter la légende
    visualizer.add_legend(minibus_list)

    # Sauvegarder
    visualizer.save_map("map_minibus.html")
    print("Carte générée : map_minibus.html")
