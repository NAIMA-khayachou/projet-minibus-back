from database.crud import get_clients, get_stations, get_minibus
from app.core.osrm_engine import Distance_total, Duree_Total
import random


class AlgoGenetic:

    def __init__(self, population_size=20):
        self.population_size = population_size
        self.population = []

    # ---------------------------------------------------------
    # 1. INITIALISATION DE LA POPULATION
    # ---------------------------------------------------------
    def initialize_population(self):
        clients_list = get_clients()
        minibus_list = get_minibus()

        for _ in range(self.population_size):
            random.shuffle(clients_list)
            solution = []

            for mb in minibus_list:

                mb_clients = []
                total_pass = 0

                for cl in clients_list:
                    if total_pass + cl.nbr_place <= mb.capacite_max:
                        mb_clients.append({
                            "client_id": cl.name,
                            "station_depart": cl.depart,
                            "station_arrivee": cl.destination,
                            "nbr_places": cl.nbr_place
                        })
                        total_pass += cl.nbr_place

                if mb_clients:
                    dist = Distance_total(mb_clients)
                    duree = Duree_Total(mb_clients)

                    solution.append({
                        "minibus_id": mb.id,
                        "clients": mb_clients,
                        "distance_total": dist,
                        "duree_total": duree,
                        "capacite_max": mb.capacite_max,
                        "limite_distance": mb.limite_distance,
                        "limite_duree": mb.limite_duree
                    })

            if solution:
                self.population.append(solution)

        print("Population initiale :", len(self.population))



    # ---------------------------------------------------------
    # 2. FITNESS
    # ---------------------------------------------------------
    def fitness(self, population):
        list_fit = []

        for solution in population:

            dist = sum(mb["distance_total"] for mb in solution)
            duree = sum(mb["duree_total"] for mb in solution)

            penalite = 0
            for mb in solution:
                total_places = sum(c["nbr_places"] for c in mb["clients"])

                if total_places > mb["capacite_max"]:
                    penalite += 500

                if mb["distance_total"] > mb["limite_distance"]:
                    penalite += 500

                if mb["duree_total"] > mb["limite_duree"]:
                    penalite += 500

            score = 1 / (1 + dist + duree + penalite)
            list_fit.append((score, solution))

        return list_fit



    # ---------------------------------------------------------
    # 3. SELECTION PAR TOURNOI
    # ---------------------------------------------------------
    def selection_tournoi(self, list_fitness, tournoi=3, nb_parents=6):
        parents = []

        for _ in range(nb_parents):
            groupe = random.sample(list_fitness, tournoi)
            best = max(groupe, key=lambda x: x[0])
            parents.append(best[1])

        return parents



    # ---------------------------------------------------------
    # 4. CROSSOVER
    # ---------------------------------------------------------
    def crossover(self, parent1, parent2):

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

        # ---- 1 : mélanger l’ordre des clients ----
        for mb in enfant:
            if random.random() < 0.2:
                random.shuffle(mb["clients"])

        # ---- 2 : réaffecter un client ----
        if random.random() < 0.3:

            mb_source = random.choice([m for m in enfant if len(m["clients"]) > 0])
            client = random.choice(mb_source["clients"])
            mb_source["clients"].remove(client)

            autres = [m for m in enfant if m != mb_source]
            if autres:
                mb_dest = random.choice(autres)

                cap = sum(c["nbr_places"] for c in mb_dest["clients"])
                if cap + client["nbr_places"] <= mb_dest["capacite_max"]:
                    mb_dest["clients"].append(client)
                else:
                    mb_source["clients"].append(client)

        return enfant



    # ---------------------------------------------------------
    # 6. GENERATION SUIVANTE
    # ---------------------------------------------------------
    def next_generation(self):

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
