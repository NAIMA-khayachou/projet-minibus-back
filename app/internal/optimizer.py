from app.database.crud import get_all_clients, get_all_stations, get_all_minibus, get_all_reservations_for_algo
from app.internal.osrm_engine import get_cost_matrices
import random
import copy

class AlgoGenetic:

    def __init__(self, population_size=20):  # ✅ CORRIGÉ : double underscore
        self.population_size = population_size
        self.population = []

    # ---------------------------------------------------------
    # HELPER: RECALCULER DISTANCES ET DURÉES
    # ---------------------------------------------------------
    def recalculate_minibus_metrics(self, minibus_data):
        """
        Recalcule distance_total et duree_total pour un minibus
        après modification de ses réservations
        """
        if not minibus_data["reservations"]:
            minibus_data["distance_total"] = 0
            minibus_data["duree_total"] = 0
            return

        # Construire la liste de points (pickup et dropoff de chaque réservation)
        points = []
        for res in minibus_data["reservations"]:
            points.append((res['pickup_lon'], res['pickup_lat']))
            points.append((res['dropoff_lon'], res['dropoff_lat']))

        try:
            # Appeler OSRM
            dist_matrix, duree_matrix = get_cost_matrices(points)
            
            # Calculer la distance et durée totale
            distance_total = sum(dist_matrix[i][i+1] for i in range(len(points)-1))
            duree_total = sum(duree_matrix[i][i+1] for i in range(len(points)-1))
            
            minibus_data["distance_total"] = distance_total
            minibus_data["duree_total"] = duree_total
        except Exception as e:
            print(f"Erreur OSRM: {e}")
            minibus_data["distance_total"] = 0
            minibus_data["duree_total"] = 0

    # ---------------------------------------------------------
    # 1. INITIALISATION DE LA POPULATION
    # ---------------------------------------------------------
    def initialize_population(self):
        """
        Initialise la population en affectant les réservations aux minibus
        selon leur capacité et en calculant les distances via OSRM
        """
        reservations = get_all_reservations_for_algo()
        minibus_list = get_all_minibus()

        if not reservations:
            print("⚠ Aucune réservation trouvée!")
            return
        
        if not minibus_list:
            print("⚠ Aucun minibus disponible!")
            return

        for _ in range(self.population_size):
            reservations_copy = list(reservations)
            random.shuffle(reservations_copy)
            solution = []

            # Pour chaque minibus disponible
            for mb in minibus_list:
                mb_reservations = []
                total_passengers = 0

                # Affecter les réservations au minibus selon la capacité
                reservations_to_remove = []
                for res in reservations_copy:
                    if total_passengers + res[4] <= mb[1]:
                        mb_reservations.append({
                            "reservation_id": res[0],
                            "client_id": res[1],
                            "pickup_station_id": res[2],
                            "dropoff_station_id": res[3],
                            "number_of_people": res[4],
                            "pickup_lat": res[6],
                            "pickup_lon": res[7],
                            "dropoff_lat": res[8],
                            "dropoff_lon": res[9]
                        })
                        total_passengers += res[4]
                        reservations_to_remove.append(res)
                
                # Retirer les réservations assignées
                for res in reservations_to_remove:
                    reservations_copy.remove(res)

                if mb_reservations:
                    # Construire la liste de points (pickup ET dropoff pour chaque réservation)
                    points = []
                    for res in mb_reservations:
                        points.append((res['pickup_lon'], res['pickup_lat']))
                        points.append((res['dropoff_lon'], res['dropoff_lat']))

                    try:
                        # Appeler OSRM
                        dist_matrix, duree_matrix = get_cost_matrices(points)
                        distance_total = sum(dist_matrix[i][i+1] for i in range(len(points)-1))
                        duree_total = sum(duree_matrix[i][i+1] for i in range(len(points)-1))
                    except Exception as e:
                        print(f"Erreur OSRM: {e}")
                        distance_total = 0
                        duree_total = 0

                    solution.append({
                        "minibus_id": mb[0],
                        "license_plate": mb[2],
                        "reservations": mb_reservations,
                        "distance_total": distance_total,
                        "duree_total": duree_total,
                        "capacity": mb[1],
                        "limite_distance": mb[6] if mb[6] else float('inf'),
                        "limite_duree": mb[7] if mb[7] else float('inf')
                    })

            if solution:
                self.population.append(solution)

        print(f"✅ Population initiale créée : {len(self.population)} solutions")

    # ---------------------------------------------------------
    # 2. FITNESS
    # ---------------------------------------------------------
    def fitness(self, population):
        """
        Calcule le score de fitness pour chaque solution
        """
        list_fit = []

        for solution in population:
            dist = sum(mb["distance_total"] for mb in solution)
            duree = sum(mb["duree_total"] for mb in solution)
            penalite = 0

            for mb in solution:
                total_passengers = sum(res["number_of_people"] for res in mb["reservations"])

                if total_passengers > mb["capacity"]:
                    penalite += 500

                if mb["limite_distance"] != float('inf') and mb["distance_total"] > mb["limite_distance"]:
                    penalite += 500

                if mb["limite_duree"] != float('inf') and mb["duree_total"] > mb["limite_duree"]:
                    penalite += 500

            score = 1 / (1 + dist + duree + penalite)
            list_fit.append((score, solution))

        return list_fit

    # ---------------------------------------------------------
    # 3. SELECTION PAR TOURNOI
    # ---------------------------------------------------------
    def selection_tournoi(self, list_fitness, tournoi=3, nb_parents=6):
        """
        Sélectionne les meilleurs parents par tournoi
        """
        parents = []
        for _ in range(nb_parents):
            groupe = random.sample(list_fitness, min(tournoi, len(list_fitness)))
            best = max(groupe, key=lambda x: x[0])
            parents.append(best[1])
        return parents

    # ---------------------------------------------------------
    # 4. CROSSOVER
    # ---------------------------------------------------------
    def crossover(self, parent1, parent2):
        """
        Crée un enfant en combinant deux parents
        ✅ CORRIGÉ : deep copy et gestion des réservations
        """
        enfant = []
        
        # Collecter toutes les réservations des deux parents
        all_reservations = []
        for mb in parent1:
            all_reservations.extend(copy.deepcopy(mb["reservations"]))
        
        # Mélanger pour la diversité
        random.shuffle(all_reservations)
        
        # Redistribuer aux minibus (utiliser la structure de parent1)
        for mb_template in parent1:
            mb_new = {
                "minibus_id": mb_template["minibus_id"],
                "license_plate": mb_template["license_plate"],
                "reservations": [],
                "distance_total": 0,
                "duree_total": 0,
                "capacity": mb_template["capacity"],
                "limite_distance": mb_template["limite_distance"],
                "limite_duree": mb_template["limite_duree"]
            }
            
            # Assigner des réservations selon la capacité
            total_passengers = 0
            reservations_to_remove = []
            for res in all_reservations:
                if total_passengers + res["number_of_people"] <= mb_new["capacity"]:
                    mb_new["reservations"].append(res)
                    total_passengers += res["number_of_people"]
                    reservations_to_remove.append(res)
            
            # Retirer les réservations assignées
            for res in reservations_to_remove:
                all_reservations.remove(res)
            
            # Recalculer les métriques
            if mb_new["reservations"]:
                self.recalculate_minibus_metrics(mb_new)
                enfant.append(mb_new)
        
        return enfant

    # ---------------------------------------------------------
    # 5. MUTATION
    # ---------------------------------------------------------
    def mutation(self, enfant):
        """
        Applique des mutations aléatoires à un enfant
        ✅ CORRIGÉ : recalcul des distances après mutation
        """
        enfant = copy.deepcopy(enfant)
        
        # Mutation 1 : mélanger l'ordre des réservations dans un minibus
        for mb in enfant:
            if random.random() < 0.2 and len(mb["reservations"]) > 1:
                random.shuffle(mb["reservations"])
                self.recalculate_minibus_metrics(mb)  # ✅ Recalculer

        # Mutation 2 : réaffecter une réservation à un autre minibus
        if random.random() < 0.3 and len(enfant) > 1:
            mb_source_list = [m for m in enfant if len(m["reservations"]) > 0]
            if mb_source_list:
                mb_source = random.choice(mb_source_list)
                if mb_source["reservations"]:
                    reservation = random.choice(mb_source["reservations"])
                    mb_source["reservations"].remove(reservation)

                    autres = [m for m in enfant if m["minibus_id"] != mb_source["minibus_id"]]
                    if autres:
                        mb_dest = random.choice(autres)
                        cap = sum(res["number_of_people"] for res in mb_dest["reservations"])
                        
                        if cap + reservation["number_of_people"] <= mb_dest["capacity"]:
                            mb_dest["reservations"].append(reservation)
                            self.recalculate_minibus_metrics(mb_dest)  # ✅ Recalculer
                        else:
                            mb_source["reservations"].append(reservation)
                    
                    self.recalculate_minibus_metrics(mb_source)  # ✅ Recalculer

        return enfant

    # ---------------------------------------------------------
    # 6. GENERATION SUIVANTE
    # ---------------------------------------------------------
    def next_generation(self):
        """
        Crée la génération suivante
        """
        fitness_vals = self.fitness(self.population)
        parents = self.selection_tournoi(fitness_vals)

        new_pop = []
        while len(new_pop) < self.population_size:
            p1 = random.choice(parents)
            p2 = random.choice(parents)
            enfant = self.crossover(p1, p2)
            enfant = self.mutation(enfant)
            new_pop.append(enfant)

        self.population = new_pop

    # ---------------------------------------------------------
    # 7. OBTENIR LA MEILLEURE SOLUTION
    # ---------------------------------------------------------
    def get_best_solution(self):
        """
        Retourne la meilleure solution
        """
        fitness_vals = self.fitness(self.population)
        best = max(fitness_vals, key=lambda x: x[0])
        return best[1], best[0]

    # ---------------------------------------------------------
    # 8. EXECUTER L'ALGORITHME
    # ---------------------------------------------------------
    def run(self, generations=100):
        """
        Execute l'algorithme génétique
        """
        print("🚀 Démarrage de l'algorithme génétique...")
        self.initialize_population()
        
        if not self.population:
            print("❌ Impossible de créer une population initiale")
            return None, 0
        
        for gen in range(generations):
            self.next_generation()
            
            if gen % 10 == 0:
                best_solution, best_score = self.get_best_solution()
                print(f"Génération {gen}: Meilleur score = {best_score:.6f}")
        
        best_solution, best_score = self.get_best_solution()
        print(f"\n✅ MEILLEURE SOLUTION FINALE")
        print(f"Score: {best_score:.6f}")
        
        return best_solution, best_score