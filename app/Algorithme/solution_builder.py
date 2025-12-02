# app/algorithms/solution_builder.py

import random

from typing import List, Dict, Optional
from .solution import Solution, Arret, ItineraireMinibus
from ..database.crud import get_all_reservations,get_all_minibus,get_all_stations
class SolutionBuilder:
    """Construit des solutions initiales"""
    
    def __init__(self, matrice_distances, matrice_durees, stations_dict):
        self.matrice_distances = matrice_distances
        self.matrice_durees = matrice_durees
        self.stations_dict = stations_dict
    
    def generer_population_initiale(self, reservations, minibus, taille_population: int = 100) -> List[Solution]:
        """Génère une population initiale diverse"""
        population = []
        
        for i in range(taille_population):
            # 33% aléatoire
            if i < taille_population // 3:
                solution = self.affectation_aleatoire(reservations, minibus)
            
            # 33% plus proche voisin
            elif i < 2 * taille_population // 3:
                solution = self.heuristique_plus_proche_voisin(reservations, minibus)
            
            # 34% regroupement géographique
            else:
                solution = self.regroupement_geographique(reservations, minibus)
            
            # Construire les itinéraires
            self.construire_itineraires(solution)
            
            # Réparer si nécessaire
            self.reparer_solution(solution)
            
            population.append(solution)
        
        return population
    
    def affectation_aleatoire(self, reservations, minibus) -> Solution:
        """Affecte aléatoirement les réservations aux minibus"""
        solution = Solution(minibus, reservations, self.stations_dict)
        
        for reservation in reservations:
            minibus_choisi = random.choice(minibus)
            solution.affectations[reservation.id] = minibus_choisi.id
        
        return solution
    
    def heuristique_plus_proche_voisin(self, reservations, minibus) -> Solution:
        """Construit une solution avec l'heuristique du plus proche voisin"""
        solution = Solution(minibus, reservations, self.stations_dict)
        reservations_non_assignees = list(reservations)
        
        # Dépôt (supposons ID = 0 ou le premier dans le dict)
        depot_id = 0  # Vous devez avoir un ID pour le dépôt
        
        for bus in minibus:
            capacite_restante = bus.capacity
            position_actuelle_id = depot_id
            
            while reservations_non_assignees and capacite_restante > 0:
                meilleure_reservation = None
                distance_min = float('inf')
                
                # Trouver la réservation la plus proche
                for reservation in reservations_non_assignees:
                    if reservation.number_of_people <= capacite_restante:
                        pickup_id = reservation.pickup_station_id
                        distance = self.matrice_distances[position_actuelle_id][pickup_id]
                        
                        if distance < distance_min:
                            distance_min = distance
                            meilleure_reservation = reservation
                
                # Assigner si trouvée
                if meilleure_reservation:
                    solution.affectations[meilleure_reservation.id] = bus.id
                    capacite_restante -= meilleure_reservation.number_of_people
                    position_actuelle_id = meilleure_reservation.pickup_station_id
                    reservations_non_assignees.remove(meilleure_reservation)
                else:
                    break
        
        return solution
    
    def regroupement_geographique(self, reservations, minibus) -> Solution:
        """Regroupe les réservations par zones géographiques"""
        from sklearn.cluster import KMeans
        import numpy as np
        
        solution = Solution(minibus, reservations, self.stations_dict)
        
        if len(reservations) == 0:
            return solution
        
        # Calculer les centres des réservations
        centres = []
        for reservation in reservations:
            pickup = self.stations_dict[reservation.pickup_station_id]
            dropoff = self.stations_dict[reservation.dropoff_station_id]
            
            centre_lat = (pickup.latitude + dropoff.latitude) / 2
            centre_lon = (pickup.longitude + dropoff.longitude) / 2
            centres.append([centre_lat, centre_lon])
        
        # Clustering K-Means
        n_clusters = min(len(minibus), len(reservations))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(centres)
        
        # Assigner chaque cluster à un minibus
        for cluster_id in range(n_clusters):
            if cluster_id >= len(minibus):
                break
            
            bus = minibus[cluster_id]
            capacite_restante = bus.capacity
            
            # Récupérer les réservations de ce cluster
            reservations_cluster = [
                reservations[i] for i in range(len(reservations))
                if labels[i] == cluster_id
            ]
            
            # Assigner si capacité suffisante
            for reservation in reservations_cluster:
                if reservation.number_of_people <= capacite_restante:
                    solution.affectations[reservation.id] = bus.id
                    capacite_restante -= reservation.number_of_people
        
        return solution
    
    def construire_itineraires(self, solution: Solution):
        """Construit les itinéraires détaillés pour chaque minibus"""
        depot_id = 0  # ID du dépôt
        depot_name = "Depot"
        
        for minibus in solution.minibus_list:
            minibus_id = minibus.id
            reservations_minibus = solution.get_reservations_by_minibus(minibus_id)
            
            if not reservations_minibus:
                # Minibus non utilisé
                solution.itineraires[minibus_id].arrets = []
                continue
            
            # Créer la liste des arrêts
            arrets = []
            
            # Départ du dépôt
            arrets.append(Arret(
                station_id=depot_id,
                station_name=depot_name,
                type="DEPOT"
            ))
            
            # Ajouter tous les pickups
            for reservation in reservations_minibus:
                pickup_station = self.stations_dict[reservation.pickup_station_id]
                arrets.append(Arret(
                    station_id=reservation.pickup_station_id,
                    station_name=pickup_station.name,
                    type="PICKUP",
                    reservation_id=reservation.id,
                    personnes=reservation.number_of_people
                ))
            
            # Ajouter tous les dropoffs
            for reservation in reservations_minibus:
                dropoff_station = self.stations_dict[reservation.dropoff_station_id]
                arrets.append(Arret(
                    station_id=reservation.dropoff_station_id,
                    station_name=dropoff_station.name,
                    type="DROPOFF",
                    reservation_id=reservation.id,
                    personnes=reservation.number_of_people
                ))
            
            # Retour au dépôt
            arrets.append(Arret(
                station_id=depot_id,
                station_name=depot_name,
                type="DEPOT"
            ))
            
            solution.itineraires[minibus_id].arrets = arrets
            solution.itineraires[minibus_id].reservations_servies = [r.id for r in reservations_minibus]
    
    def reparer_solution(self, solution: Solution):
        """Répare une solution pour respecter les contraintes"""
        for minibus in solution.minibus_list:
            minibus_id = minibus.id
            itineraire = solution.itineraires[minibus_id]
            
            if not itineraire.arrets:
                continue
            
            # Vérifier et corriger l'ordre pickup-dropoff
            self._corriger_ordre_pickup_dropoff(itineraire)
            
            # Vérifier la capacité
            self._verifier_capacite(solution, minibus_id, minibus.capacity)
    
    def _corriger_ordre_pickup_dropoff(self, itineraire: ItineraireMinibus):
        """S'assure que chaque pickup vient avant son dropoff"""
        reservation_pickups = {}
        arrets_a_reordonner = []
        
        for i, arret in enumerate(itineraire.arrets):
            if arret.type == "PICKUP":
                reservation_pickups[arret.reservation_id] = i
            elif arret.type == "DROPOFF":
                if arret.reservation_id in reservation_pickups:
                    pickup_index = reservation_pickups[arret.reservation_id]
                    if pickup_index >= i:
                        # Dropoff avant pickup : échanger
                        itineraire.arrets[pickup_index], itineraire.arrets[i] = \
                            itineraire.arrets[i], itineraire.arrets[pickup_index]
    
    def _verifier_capacite(self, solution: Solution, minibus_id: int, capacite: int):
   
       itineraire = solution.itineraires[minibus_id]
       charge_actuelle = 0
       reservations_a_retirer = set()  # utiliser set pour éviter doublons
    
       # 1️⃣ Identifier les réservations qui dépassent la capacité
       for arret in itineraire.arrets:
        if arret.type == "PICKUP":
            charge_actuelle += arret.personnes
            if charge_actuelle > capacite:
                reservations_a_retirer.add(arret.reservation_id)
        elif arret.type == "DROPOFF":
            charge_actuelle -= arret.personnes
    
    # 2️⃣ Retirer les réservations problématiques
       if reservations_a_retirer:
        itineraire.arrets = [
            a for a in itineraire.arrets if a.reservation_id not in reservations_a_retirer
        ]
        for res_id in reservations_a_retirer:
            if res_id in solution.affectations:
                del solution.affectations[res_id]
