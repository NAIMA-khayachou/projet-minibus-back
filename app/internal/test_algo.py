from app.internal.optimizer import AlgoGenetic


# Créer l'instance
algo = AlgoGenetic()

# Tester l'initialisation
print("=== TEST INITIALISATION ===")
algo.initialize_population()

# Lancer l'algorithme
print("\n=== LANCEMENT ALGORITHME ===")
best_solution, best_score = algo.run(generations=20)

# Afficher le résultat
print(f"\n=== MEILLEURE SOLUTION ===")
print(f"Score: {best_score:.6f}")
for i, mb in enumerate(best_solution):
    print(f"\nMinibus {i+1} ({mb['license_plate']}):")
    print(f"  - Réservations: {len(mb['reservations'])}")
    print(f"  - Distance: {mb['distance_total']:.2f}m")
    print(f"  - Durée: {mb['duree_total']:.2f}s")