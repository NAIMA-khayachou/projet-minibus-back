from app.database.crud import *
from .osrm_engine import get_cost_matrix
import random

class Algogenetic:
    def __init__(self, population_size=20):
        self.population = []
        self.population_size = population_size

    def initialize_population(self):
        clients_list = get_all_clients()       
        minibus_list = get_all_minibus()      
        stations_list = get_all_stations()     

        for _ in range(self.population_size):
            random.shuffle(clients_list)   
            solution = []                  

            for minibus in minibus_list:
                minibus_clients = []
                total_passengers = 0

                
                for client in clients_list:
                    if total_passengers + client.nbr_place <= minibus.capacite_max:
                        minibus_clients.append({
                            "client_id": client.name,
                            "station_depart": client.depart,
                            "station_arrivee": client.destination,
                            "nbr_places": client.nbr_place
                        })
                        total_passengers += client.nbr_place

               
                if minibus_clients:
                    distance = Distance_total(minibus_clients)
                    duree = Duree_Total(minibus_clients)

                    if distance <= minibus.limite_distance and duree <= minibus.limite_duree:
                        solution.append({
                            "minibus_id": minibus.id,
                            "clients": minibus_clients,
                            "distance_total": distance,
                            "duree_total": duree
                        })

            
            if solution:
                self.population.append(solution)

        print(f"Population initiale générée : {len(self.population)} itinéraires")
    def fitness(self, solutions):
       list_fitness=[]

       for solution in solutions:
            distance_total = 0
            temps_total = 0
            penalite = 0

            for minibus in solution:
            
               distance_total += minibus['distance_total']
               temps_total += minibus['duree_total']
               total_passagers = sum(c['nbr_places'] for c in minibus['clients'])

            
               if total_passagers > minibus['capacite_max']:
                 penalite += 100
               if distance_total > minibus['limite_distance']:
                  penalite += 100
               if temps_total > minibus['limite_duree']:
                   penalite += 100
            fitness_score = 1 / (distance_total + temps_total + penalite)
            list_fitness.append((fitness_score,solution))
       return list_fitness
    def Selection_tournoi(self,list_fitness,taille_tournoi=3,nombre_parents=5):
        parents=[]
        for _ in range(nombre_parents):
             tournoi=random.sample(list_fitness,taille_tournoi)
             meillure_score,meillure_solution=max(tournoi,key=lambda x:x[0]) 
             parents.append(meillure_solution)  
        return parents

             
             
                 
