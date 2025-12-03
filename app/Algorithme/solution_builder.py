# app/algorithms/solution_builder.py - VERSION CORRIGÉE COMPLÈTE

import random
from typing import List, Dict, Optional, Tuple
from .solution import Solution, Arret, ItineraireMinibus
import logging

logger = logging.getLogger(__name__)

class SolutionBuilder:
    """Construit des solutions initiales avec gestion robuste"""
    
    def __init__(self, matrice_distances, matrice_durees, stations_dict, depot_station_id=None):
        """
        Args:
            matrice_distances: Matrice NxN des distances entre stations
            matrice_durees: Matrice NxN des durées entre stations
            stations_dict: Dict {station_id: {'name': str, 'latitude': float, 'longitude': float}}
            depot_station_id: ID de la station dépôt (si None, prend la première)
        """
        self.matrice_distances = matrice_distances
        self.matrice_durees = matrice_durees
        self.stations_dict = stations_dict
        
        # ✅ CORRECTION 1: Ordre explicite et vérifié
        self.station_ids_order = sorted(stations_dict.keys())  # Tri pour cohérence
        self.station_id_to_index = {
            sid: idx for idx, sid in enumerate(self.station_ids_order)
        }
        
        # ✅ CORRECTION 2: Dépôt explicite avec validation
        if depot_station_id is None:
            self.depot_station_id = self.station_ids_order[0]
            logger.warning(f"⚠️ Aucun dépôt défini, utilisation de la station {self.depot_station_id}")
        else:
            if depot_station_id not in self.station_id_to_index:
                raise ValueError(f"❌ Dépôt {depot_station_id} introuvable dans stations_dict")
            self.depot_station_id = depot_station_id
        
        # Log de vérification
        logger.info(f"✅ SolutionBuilder initialisé:")
        logger.info(f"   - {len(stations_dict)} stations")
        logger.info(f"   - Dépôt: Station {self.depot_station_id}")
        logger.info(f"   - Ordre stations: {self.station_ids_order[:5]}...")

    def _id_to_index(self, station_id: int) -> Optional[int]:
        """Retourne l'index de la station dans les matrices"""
        idx = self.station_id_to_index.get(station_id)
        if idx is None:
            logger.error(f"❌ Station ID {station_id} introuvable dans le mapping")
        return idx

    def _get_station_name(self, station_obj) -> str:
        """Récupère le nom d'une station (dict ou objet)"""
        if station_obj is None:
            return "Unknown"
        if isinstance(station_obj, dict):
            return station_obj.get("name") or station_obj.get("station_name") or "Unknown"
        return getattr(station_obj, "name", "Unknown")

    def _get_station_coords(self, station_obj) -> Tuple[Optional[float], Optional[float]]:
        """Retourne (latitude, longitude)"""
        if station_obj is None:
            return None, None
        if isinstance(station_obj, dict):
            return station_obj.get("latitude"), station_obj.get("longitude")
        return getattr(station_obj, "latitude", None), getattr(station_obj, "longitude", None)
    
    def _validate_reservation(self, reservation) -> bool:
        """✅ NOUVELLE: Valide qu'une réservation a des données cohérentes"""
        # ✅ CORRECTION 3: Gestion des deux formats (tuple CRUD vs objet SQLAlchemy)
        if isinstance(reservation, tuple):
            # Format: (id, client_name, pickup_station_NAME, dropoff_station_NAME, people, time, status)
            logger.error(f"❌ Réservation {reservation[0]}: Format tuple détecté, attendu objet avec pickup_station_id")
            return False
        
        # Vérifier que pickup/dropoff sont des IDs (integers)
        pickup_id = getattr(reservation, 'pickup_station_id', None) or getattr(reservation, 'pickup_station', None)
        dropoff_id = getattr(reservation, 'dropoff_station_id', None) or getattr(reservation, 'dropoff_station', None)
        
        if not isinstance(pickup_id, int) or not isinstance(dropoff_id, int):
            logger.error(f"❌ Réservation {reservation.id}: pickup={pickup_id} dropoff={dropoff_id} (doivent être des integers)")
            return False
        
        if pickup_id not in self.station_id_to_index:
            logger.error(f"❌ Réservation {reservation.id}: pickup_station_id={pickup_id} introuvable")
            return False
        
        if dropoff_id not in self.station_id_to_index:
            logger.error(f"❌ Réservation {reservation.id}: dropoff_station_id={dropoff_id} introuvable")
            return False
        
        return True
    
    def generer_population_initiale(self, reservations, minibus, taille_population: int = 50) -> List[Solution]:
        """✅ CORRECTION 4: Population initiale plus grande et avec validation"""
        
        # ✅ Filtrer les réservations invalides
        reservations_valides = [r for r in reservations if self._validate_reservation(r)]
        
        if len(reservations_valides) < len(reservations):
            logger.warning(f"⚠️ {len(reservations) - len(reservations_valides)} réservations invalides ignorées")
        
        if not reservations_valides:
            logger.error("❌ Aucune réservation valide, impossible de générer une population")
            return []
        
        population = []
        
        for i in range(taille_population):
            # 33% aléatoire
            if i < taille_population // 3:
                solution = self.affectation_aleatoire(reservations_valides, minibus)
            
            # 33% plus proche voisin
            elif i < 2 * taille_population // 3:
                solution = self.heuristique_plus_proche_voisin(reservations_valides, minibus)
            
            # 34% regroupement géographique
            else:
                solution = self.regroupement_geographique(reservations_valides, minibus)
            
            # Construire les itinéraires
            self.construire_itineraires(solution)
            
            # Réparer si nécessaire
            self.reparer_solution(solution)
            
            population.append(solution)
        
        logger.info(f"✅ Population de {len(population)} solutions générée")
        return population
    
    def affectation_aleatoire(self, reservations, minibus) -> Solution:
        """Affecte aléatoirement les réservations aux minibus"""
        solution = Solution(minibus, reservations, self.stations_dict)
        
        for reservation in reservations:
            minibus_choisi = random.choice(minibus)
            solution.affectations[reservation.id] = minibus_choisi.id
        
        return solution
    
    def heuristique_plus_proche_voisin(self, reservations, minibus) -> Solution:
        """✅ CORRECTION 5: Heuristique avec accès correct aux IDs"""
        solution = Solution(minibus, reservations, self.stations_dict)
        reservations_non_assignees = list(reservations)
        
        for bus in minibus:
            capacite_restante = bus.capacity
            position_actuelle_id = self.depot_station_id
            
            while reservations_non_assignees and capacite_restante > 0:
                meilleure_reservation = None
                distance_min = float('inf')
                
                for reservation in reservations_non_assignees:
                    if reservation.number_of_people <= capacite_restante:
                        # ✅ Accès correct selon le format
                        pickup_id = getattr(reservation, 'pickup_station_id', None) or \
                                    getattr(reservation, 'pickup_station', None)
                        
                        idx_actuel = self._id_to_index(position_actuelle_id)
                        idx_pickup = self._id_to_index(pickup_id)
                        
                        if idx_actuel is None or idx_pickup is None:
                            continue
                        
                        distance = self.matrice_distances[idx_actuel][idx_pickup]
                        
                        if distance < distance_min:
                            distance_min = distance
                            meilleure_reservation = reservation
                
                if meilleure_reservation:
                    solution.affectations[meilleure_reservation.id] = bus.id
                    capacite_restante -= meilleure_reservation.number_of_people
                    
                    pickup_id = getattr(meilleure_reservation, 'pickup_station_id', None) or \
                                getattr(meilleure_reservation, 'pickup_station', None)
                    position_actuelle_id = pickup_id
                    
                    reservations_non_assignees.remove(meilleure_reservation)
                else:
                    break
        
        return solution
    
    def regroupement_geographique(self, reservations, minibus) -> Solution:
        """✅ CORRECTION 6: Clustering avec mapping correct"""
        from sklearn.cluster import KMeans
        import numpy as np
        
        solution = Solution(minibus, reservations, self.stations_dict)
        
        if len(reservations) == 0:
            return solution
        
        # ✅ Garder un mapping index_centres → index_reservation
        centres = []
        reservation_indices = []
        
        for i, reservation in enumerate(reservations):
            # Accès correct aux IDs
            pickup_id = getattr(reservation, 'pickup_station_id', None) or \
                       getattr(reservation, 'pickup_station', None)
            dropoff_id = getattr(reservation, 'dropoff_station_id', None) or \
                        getattr(reservation, 'dropoff_station', None)
            
            pickup_obj = self.stations_dict.get(pickup_id)
            dropoff_obj = self.stations_dict.get(dropoff_id)
            
            lat1, lon1 = self._get_station_coords(pickup_obj)
            lat2, lon2 = self._get_station_coords(dropoff_obj)
            
            if lat1 is not None and lat2 is not None:
                centre_lat = (lat1 + lat2) / 2
                centre_lon = (lon1 + lon2) / 2
                centres.append([centre_lat, centre_lon])
                reservation_indices.append(i)  # ✅ Garder le lien
        
        if not centres:
            logger.warning("⚠️ Aucune coordonnée valide pour clustering, utilisation aléatoire")
            return self.affectation_aleatoire(reservations, minibus)
        
        # Clustering
        n_clusters = min(len(minibus), len(centres))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(centres)
        
        # Assigner chaque cluster à un minibus
        for cluster_id in range(n_clusters):
            if cluster_id >= len(minibus):
                break
            
            bus = minibus[cluster_id]
            capacite_restante = bus.capacity
            
            # ✅ Utiliser le mapping correct
            for idx_centre, label in enumerate(labels):
                if label == cluster_id:
                    idx_reservation = reservation_indices[idx_centre]
                    reservation = reservations[idx_reservation]
                    
                    if reservation.number_of_people <= capacite_restante:
                        solution.affectations[reservation.id] = bus.id
                        capacite_restante -= reservation.number_of_people
        
        return solution
    
    def construire_itineraires(self, solution: Solution):
        """✅ VERSION INTELLIGENTE : Construit les itinéraires avec ordre optimal pickup/dropoff"""
        depot_name = self._get_station_name(self.stations_dict.get(self.depot_station_id))
        
        for minibus in solution.minibus_list:
            minibus_id = minibus.id
            reservations_minibus = solution.get_reservations_by_minibus(minibus_id)
            
            if not reservations_minibus:
                solution.itineraires[minibus_id].arrets = []
                continue
            
            # ✅ CONSTRUCTION INTELLIGENTE DE L'ITINÉRAIRE
            arrets = self._construire_ordre_intelligent(
                reservations_minibus, 
                minibus.capacity,
                depot_name
            )
            
            solution.itineraires[minibus_id].arrets = arrets
            solution.itineraires[minibus_id].reservations_servies = [r.id for r in reservations_minibus]

    def _construire_ordre_intelligent(self, reservations, capacite_minibus, depot_name):
        """
        ✅ Construit l'ordre des arrêts en alternant pickups/dropoffs selon proximité
        
        Logique :
        1. Départ du dépôt
        2. À chaque étape, choisir le prochain arrêt le plus proche parmi :
           - Les pickups non encore faits
           - Les dropoffs des passagers déjà à bord
        3. Respecter la capacité et l'ordre pickup avant dropoff
        4. Retour au dépôt
        """
        arrets = []
        
        # 🏁 Départ du dépôt
        arrets.append(Arret(
            station_id=self.depot_station_id,
            station_name=depot_name,
            type="DEPOT"
        ))
        
        position_actuelle_id = self.depot_station_id
        
        # ✅ CORRECTION : Utiliser des LISTES au lieu de sets
        reservations_non_prises = list(reservations)  # ✅ Liste au lieu de set
        passagers_a_bord = {}  # {reservation_id: reservation_obj}
        charge_actuelle = 0
        
        # 🔄 Boucle principale : construire l'itinéraire arrêt par arrêt
        while reservations_non_prises or passagers_a_bord:
            
            meilleur_arret = None
            distance_min = float('inf')
            type_arret = None
            reservation_choisie = None
            
            # 🔍 CANDIDATS PICKUPS : Réservations pas encore prises
            for reservation in reservations_non_prises:
                # Vérifier capacité
                if charge_actuelle + reservation.number_of_people > capacite_minibus:
                    continue  # Pas assez de place
                
                pickup_id = getattr(reservation, 'pickup_station_id', None) or \
                           getattr(reservation, 'pickup_station', None)
                
                idx_actuel = self._id_to_index(position_actuelle_id)
                idx_pickup = self._id_to_index(pickup_id)
                
                if idx_actuel is None or idx_pickup is None:
                    continue
                
                distance = self.matrice_distances[idx_actuel][idx_pickup]
                
                if distance < distance_min:
                    distance_min = distance
                    meilleur_arret = pickup_id
                    type_arret = "PICKUP"
                    reservation_choisie = reservation
            
            # 🔍 CANDIDATS DROPOFFS : Passagers déjà à bord
            for reservation in passagers_a_bord.values():
                dropoff_id = getattr(reservation, 'dropoff_station_id', None) or \
                            getattr(reservation, 'dropoff_station', None)
                
                idx_actuel = self._id_to_index(position_actuelle_id)
                idx_dropoff = self._id_to_index(dropoff_id)
                
                if idx_actuel is None or idx_dropoff is None:
                    continue
                
                distance = self.matrice_distances[idx_actuel][idx_dropoff]
                
                # ✅ Priorité légère aux dropoffs (multiplier par 0.95)
                # Pour éviter de surcharger le bus inutilement
                distance_ajustee = distance * 0.95
                
                if distance_ajustee < distance_min:
                    distance_min = distance_ajustee
                    meilleur_arret = dropoff_id
                    type_arret = "DROPOFF"
                    reservation_choisie = reservation
            
            # ❌ Aucun arrêt trouvé (ne devrait pas arriver)
            if meilleur_arret is None:
                logger.warning("⚠️ Aucun arrêt trouvé, arrêt de la construction")
                break
            
            # ✅ AJOUTER L'ARRÊT CHOISI
            station_obj = self.stations_dict.get(meilleur_arret)
            station_name = self._get_station_name(station_obj)
            
            if type_arret == "PICKUP":
                arrets.append(Arret(
                    station_id=meilleur_arret,
                    station_name=station_name,
                    type="PICKUP",
                    reservation_id=reservation_choisie.id,
                    personnes=reservation_choisie.number_of_people
                ))
                
                # Mettre à jour l'état
                reservations_non_prises.remove(reservation_choisie)  # ✅ remove() marche avec liste
                passagers_a_bord[reservation_choisie.id] = reservation_choisie
                charge_actuelle += reservation_choisie.number_of_people
            
            elif type_arret == "DROPOFF":
                arrets.append(Arret(
                    station_id=meilleur_arret,
                    station_name=station_name,
                    type="DROPOFF",
                    reservation_id=reservation_choisie.id,
                    personnes=reservation_choisie.number_of_people
                ))
                
                # Mettre à jour l'état
                del passagers_a_bord[reservation_choisie.id]
                charge_actuelle -= reservation_choisie.number_of_people
            
            # Avancer à la nouvelle position
            position_actuelle_id = meilleur_arret
        
        # 🏁 Retour au dépôt
        arrets.append(Arret(
            station_id=self.depot_station_id,
            station_name=depot_name,
            type="DEPOT"
        ))
        
        return arrets
    
    def reparer_solution(self, solution: Solution):
        """✅ CORRECTION 7: Réparation avec réassignation"""
        for minibus in solution.minibus_list:
            minibus_id = minibus.id
            itineraire = solution.itineraires[minibus_id]
            
            if not itineraire.arrets:
                continue
            
            # Corriger l'ordre pickup-dropoff
            self._corriger_ordre_pickup_dropoff(itineraire)
            
            # Vérifier la capacité ET réassigner si nécessaire
            reservations_retirees = self._verifier_capacite(solution, minibus_id, minibus.capacity)
            
            # ✅ Réassigner les réservations problématiques
            if reservations_retirees:
                self._reassigner_reservations(solution, reservations_retirees)
    
    def _corriger_ordre_pickup_dropoff(self, itineraire: ItineraireMinibus):
        """Assure que chaque pickup vient avant son dropoff"""
        reservation_pickups = {}
        
        for i, arret in enumerate(itineraire.arrets):
            if arret.type == "PICKUP":
                reservation_pickups[arret.reservation_id] = i
            elif arret.type == "DROPOFF":
                if arret.reservation_id in reservation_pickups:
                    pickup_index = reservation_pickups[arret.reservation_id]
                    if pickup_index >= i:
                        itineraire.arrets[pickup_index], itineraire.arrets[i] = \
                            itineraire.arrets[i], itineraire.arrets[pickup_index]
                        reservation_pickups[arret.reservation_id] = i
    
    def _verifier_capacite(self, solution: Solution, minibus_id: int, capacite: int) -> set:
        """✅ CORRECTION 8: Retourne les réservations à réassigner"""
        itineraire = solution.itineraires[minibus_id]
        charge_actuelle = 0
        reservations_a_retirer = set()
        
        for arret in itineraire.arrets:
            if arret.type == "PICKUP":
                charge_actuelle += arret.personnes
                if charge_actuelle > capacite:
                    reservations_a_retirer.add(arret.reservation_id)
            elif arret.type == "DROPOFF":
                if arret.reservation_id not in reservations_a_retirer:
                    charge_actuelle -= arret.personnes
        
        # Retirer du minibus
        if reservations_a_retirer:
            itineraire.arrets = [
                a for a in itineraire.arrets 
                if a.reservation_id not in reservations_a_retirer
            ]
            for res_id in reservations_a_retirer:
                if res_id in solution.affectations:
                    del solution.affectations[res_id]
        
        return reservations_a_retirer
    
    def _reassigner_reservations(self, solution: Solution, reservation_ids: set):
        """✅ NOUVELLE: Réassigne les réservations retirées"""
        for res_id in reservation_ids:
            reservation = next((r for r in solution.reservations_list if r.id == res_id), None)
            if not reservation:
                continue
            
            # Trouver un minibus avec assez de capacité
            for minibus in solution.minibus_list:
                reservations_actuelles = solution.get_reservations_by_minibus(minibus.id)
                charge_actuelle = sum(r.number_of_people for r in reservations_actuelles)
                
                if charge_actuelle + reservation.number_of_people <= minibus.capacity:
                    solution.affectations[res_id] = minibus.id
                    logger.info(f"♻️ Réservation {res_id} réassignée au minibus {minibus.id}")
                    break
            else:
                logger.warning(f"⚠️ Impossible de réassigner la réservation {res_id}")