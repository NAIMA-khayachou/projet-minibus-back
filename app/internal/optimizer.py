from app.database.crud import get_all_clients, get_all_stations, get_all_minibus,get_all_reservations_for_algo
from app.internal.osrm_engine import get_cost_matrices
import random

class AlgoGenetic:

    def __init__(self, population_size=20):
        self.population_size = population_size
        self.population = []

    # ---------------------------------------------------------
    # 1. INITIALISATION DE LA POPULATION
    # ---------------------------------------------------------
    def initialize_population(self):
        """
        Initialise la population en affectant les réservations aux minibus
        selon leur capacité et en calculant les distances via OSRM
        """
        # Récupérer toutes les réservations depuis la DB (retourne des tuples)
        # Format: (id, client_id, pickup_station_id, dropoff_station_id, number_of_people, 
        #          desired_time, pickup_lat, pickup_lon, dropoff_lat, dropoff_lon)
        reservations = get_all_reservations_for_algo()
        
        # Récupérer tous les minibus (retourne des tuples)
        # Format: (id, capacity, license_plate, current_passengers, status, 
        #          last_maintenance, limite_distance, limite_duree)
        minibus_list = get_all_minibus()

        for _ in range(self.population_size):
            # Mélanger aléatoirement les réservations
            reservations_copy = reservations.copy()
            random.shuffle(reservations_copy)
            solution = []

            # Pour chaque minibus disponible
            for mb in minibus_list:
                mb_reservations = []
                total_passengers = 0

                # Affecter les réservations au minibus selon la capacité
                for res in reservations_copy:
                    # res[4] = number_of_people, mb[1] = capacity
                    if total_passengers + res[4] <= mb[1]:
                        mb_reservations.append({
                            "reservation_id": res[0],      # id
                            "client_id": res[1],           # client_id
                            "pickup_station_id": res[2],   # pickup_station_id
                            "dropoff_station_id": res[3],  # dropoff_station_id
                            "number_of_people": res[4],    # number_of_people
                            "pickup_lat": res[6],          # pickup_lat
                            "pickup_lon": res[7],          # pickup_lon
                            "dropoff_lat": res[8],         # dropoff_lat
                            "dropoff_lon": res[9]          # dropoff_lon
                        })
                        total_passengers += res[4]

                if mb_reservations:
                    # Construire la liste de points (lon, lat) pour OSRM
                    points = []
                    for res in mb_reservations:
                        points.append((res['pickup_lon'], res['pickup_lat']))
                    # Ajouter la dernière destination
                    points.append((mb_reservations[-1]['dropoff_lon'], mb_reservations[-1]['dropoff_lat']))

                    # Appeler OSRM pour obtenir les matrices distance et durée
                    dist_matrix, duree_matrix = get_cost_matrices(points)

                    # Calculer la distance et la durée totale
                    distance_total = sum(dist_matrix[i][i+1] for i in range(len(points)-1))
                    duree_total = sum(duree_matrix[i][i+1] for i in range(len(points)-1))

                    # Ajouter le minibus à la solution
                    # mb[0]=id, mb[2]=license_plate, mb[1]=capacity, mb[6]=limite_distance, mb[7]=limite_duree
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

        print(f"Population initiale créée : {len(self.population)} solutions")

    # ---------------------------------------------------------
    # 2. FITNESS
    # ---------------------------------------------------------
    def fitness(self, population):
        """
        Calcule le score de fitness pour chaque solution
        Score basé sur : distance totale, durée totale et pénalités
        """
        list_fit = []

        for solution in population:
            # Somme des distances et durées de tous les minibus
            dist = sum(mb["distance_total"] for mb in solution)
            duree = sum(mb["duree_total"] for mb in solution)

            penalite = 0
            for mb in solution:
                # Calculer le nombre total de passagers
                total_passengers = sum(res["number_of_people"] for res in mb["reservations"])

                # Pénalité si dépassement de capacité
                if total_passengers > mb["capacity"]:
                    penalite += 500

                # Pénalité si dépassement de limite de distance
                if mb["limite_distance"] != float('inf') and mb["distance_total"] > mb["limite_distance"]:
                    penalite += 500

                # Pénalité si dépassement de limite de durée
                if mb["limite_duree"] != float('inf') and mb["duree_total"] > mb["limite_duree"]:
                    penalite += 500

            # Score de fitness (plus élevé = meilleur)
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
            # Sélectionner un groupe aléatoire
            groupe = random.sample(list_fitness, tournoi)
            # Choisir le meilleur du groupe
            best = max(groupe, key=lambda x: x[0])
            parents.append(best[1])

        return parents

    # ---------------------------------------------------------
    # 4. CROSSOVER
    # ---------------------------------------------------------
    def crossover(self, parent1, parent2):
        """
        Crée un enfant en combinant deux parents
        """
        enfant = []
        max_len = min(len(parent1), len(parent2))

        for i in range(max_len):
            if random.random() < 0.5:
                enfant.append(parent1[i])
            else:
                enfant.append(parent2[i])

        return enfant

    # ---------------------------------------------------------
    # 5. MUTATION
    # ---------------------------------------------------------
    def mutation(self, enfant):
        """
        Applique des mutations aléatoires à un enfant
        """
        # Mutation 1 : mélanger l'ordre des réservations dans un minibus
        for mb in enfant:
            if random.random() < 0.2 and len(mb["reservations"]) > 1:
                random.shuffle(mb["reservations"])

        # Mutation 2 : réaffecter une réservation à un autre minibus
        if random.random() < 0.3:
            # Choisir un minibus source avec au moins une réservation
            mb_source_list = [m for m in enfant if len(m["reservations"]) > 0]
            if mb_source_list:
                mb_source = random.choice(mb_source_list)
                reservation = random.choice(mb_source["reservations"])
                mb_source["reservations"].remove(reservation)

                # Trouver un autre minibus de destination
                autres = [m for m in enfant if m != mb_source]
                if autres:
                    mb_dest = random.choice(autres)
                    # Vérifier si la capacité le permet
                    cap = sum(res["number_of_people"] for res in mb_dest["reservations"])
                    if cap + reservation["number_of_people"] <= mb_dest["capacity"]:
                        mb_dest["reservations"].append(reservation)
                    else:
                        # Remettre la réservation dans le minibus source
                        mb_source["reservations"].append(reservation)

        return enfant

    # ---------------------------------------------------------
    # 6. GENERATION SUIVANTE
    # ---------------------------------------------------------
    def next_generation(self):
        """
        Crée la génération suivante par sélection, crossover et mutation
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
        Retourne la meilleure solution de la population actuelle
        """
        fitness_vals = self.fitness(self.population)
        best = max(fitness_vals, key=lambda x: x[0])
        return best[1], best[0]

    # ---------------------------------------------------------
    # 8. EXECUTER L'ALGORITHME
    # ---------------------------------------------------------
    def run(self, generations=100):
        """
        Execute l'algorithme génétique sur N générations
        """
        self.initialize_population()
        
        for gen in range(generations):
            self.next_generation()
            
            if gen % 10 == 0:
                best_solution, best_score = self.get_best_solution()
                print(f"Génération {gen}: Meilleur score = {best_score:.6f}")
        
        best_solution, best_score = self.get_best_solution()
        print(f"\n=== MEILLEURE SOLUTION FINALE ===")
        print(f"Score: {best_score:.6f}")
        
        return best_solution, best_score