import random
import logging
from typing import List
from datetime import datetime, timedelta
from .solution import Solution, Arret, ItineraireMinibus

logger = logging.getLogger(__name__)

class SolutionBuilder:
    """Construit des solutions avec gestion des horaires et arrêts multiples"""
    
    def __init__(self, matrice_distances, matrice_durees, stations_dict, 
                 depot_station_id=None, use_osrm=True):
        self.matrice_distances = matrice_distances
        self.matrice_durees = matrice_durees
        self.stations_dict = stations_dict
        self.depot_station_id = depot_station_id
        self.use_osrm = use_osrm
        
        self.station_ids_order = sorted(stations_dict.keys())
        self.station_id_to_index = {
            sid: idx for idx, sid in enumerate(self.station_ids_order)
        }
        
        if depot_station_id is None and stations_dict:
            self.depot_station_id = min(stations_dict.keys())
        
        logger.info(f"✅ SolutionBuilder initialisé (depot={self.depot_station_id}, OSRM={use_osrm})")
    
    def generer_population_initiale(self, reservations, minibus_list, 
                                    taille_population: int) -> List[Solution]:
        """Génère une population initiale de solutions"""
        population = []
        
        for i in range(taille_population):
            solution = Solution(minibus_list, reservations, self.stations_dict)
            
            # Stratégie 1: Assignation aléatoire (50%)
            if i < taille_population // 2:
                self._assignation_aleatoire(solution, reservations, minibus_list)
            # Stratégie 2: Assignation par proximité et horaire (30%)
            elif i < taille_population * 0.8:
                self._assignation_par_proximite_horaire(solution, reservations, minibus_list)
            # Stratégie 3: Assignation greedy avec réutilisation (20%)
            else:
                self._assignation_greedy_reutilisation(solution, reservations, minibus_list)
            
            # Construire les itinéraires
            self.construire_itineraires(solution)
            
            # Réparer si nécessaire
            self.reparer_solution(solution)
            
            population.append(solution)
        
        logger.info(f"✅ Population de {len(population)} solutions générée")
        return population
    
    def _assignation_aleatoire(self, solution: Solution, reservations, minibus_list):
        """Assignation complètement aléatoire"""
        for reservation in reservations:
            minibus = random.choice(minibus_list)
            solution.affectations[reservation.id] = minibus.id
    
    def _assignation_par_proximite_horaire(self, solution: Solution, reservations, minibus_list):
        """Assignation en tenant compte de la proximité et des horaires"""
        # Trier par heure souhaitée
        reservations_triees = sorted(reservations, key=lambda r: r.desired_time)
        
        for reservation in reservations_triees:
            # Chercher un minibus compatible
            minibus_compatible = solution.trouver_minibus_compatible(reservation)
            
            if minibus_compatible:
                solution.affectations[reservation.id] = minibus_compatible
            else:
                # Sinon, assigner à un minibus aléatoire
                minibus = random.choice(minibus_list)
                solution.affectations[reservation.id] = minibus.id
    
    def _assignation_greedy_reutilisation(self, solution: Solution, reservations, minibus_list):
        """
        ✅ NOUVELLE STRATÉGIE: Privilégie la réutilisation des routes existantes
        """
        # Trier par heure
        reservations_triees = sorted(reservations, key=lambda r: r.desired_time)
        
        for reservation in reservations_triees:
            meilleur_minibus = None
            meilleur_score = float('inf')
            
            for minibus in minibus_list:
                itineraire = solution.itineraires[minibus.id]
                
                # Si la route passe déjà par la station pickup
                if itineraire.peut_ajouter_reservation(reservation):
                    # Score basé sur la charge actuelle (favoriser les minibus peu chargés)
                    score = itineraire.charge_maximale
                    if score < meilleur_score:
                        meilleur_score = score
                        meilleur_minibus = minibus.id
            
            # Si aucun compatible, prendre le minibus le moins chargé
            if meilleur_minibus is None:
                meilleur_minibus = min(minibus_list, 
                                      key=lambda m: solution.itineraires[m.id].charge_maximale).id
            
            solution.affectations[reservation.id] = meilleur_minibus
    
    def construire_itineraires(self, solution: Solution):
        """
        ✅ NOUVELLE VERSION: Construit les itinéraires avec arrêts combinés
        """
        # Réinitialiser les itinéraires
        for minibus_id in solution.itineraires:
            solution.itineraires[minibus_id] = ItineraireMinibus(
                minibus_id=minibus_id,
                capacite=solution.itineraires[minibus_id].capacite
            )
        
        # Grouper les réservations par minibus
        for minibus_id in solution.itineraires:
            reservations = solution.get_reservations_by_minibus(minibus_id)
            
            if not reservations:
                continue
            
            # Trier par heure souhaitée
            reservations = sorted(reservations, key=lambda r: r.desired_time)
            
            # Construire l'itinéraire
            self._construire_itineraire_optimise(solution, minibus_id, reservations)
    
    def _construire_itineraire_optimise(self, solution: Solution, minibus_id: int, 
                                       reservations: List):
        """
        ✅ Construit un itinéraire en regroupant les pickups/dropoffs par station
        """
        itineraire = solution.itineraires[minibus_id]
        
       # Trouver l'heure de la première réservation
        premiere_heure = min(r.desired_time for r in reservations) if reservations else datetime.now()
        # Partir 30 minutes avant
        heure_depart = premiere_heure - timedelta(minutes=30)

        depot_arret = Arret(
        station_id=self.depot_station_id,
        station_name=self.stations_dict[self.depot_station_id]["name"],

        type="DEPOT",
        heure_arrivee=heure_depart  # ✅ BON
)
        itineraire.arrets.append(depot_arret)
        
        # Créer un dictionnaire des arrêts par station
        arrets_par_station = {}
        
        # Collecter tous les pickups et dropoffs
        for reservation in reservations:
            # Pickup
            if reservation.pickup_station_id not in arrets_par_station:
                arrets_par_station[reservation.pickup_station_id] = Arret(
                    station_id=reservation.pickup_station_id,
                    station_name=self.stations_dict[reservation.pickup_station_id]["name"],
                    type="STOP"
                )
            
            arrets_par_station[reservation.pickup_station_id].ajouter_pickup(
                reservation.id, reservation.number_of_people
            )
            
            # Dropoff
            if reservation.dropoff_station_id not in arrets_par_station:
                arrets_par_station[reservation.dropoff_station_id] = Arret(
                    station_id=reservation.dropoff_station_id,
                    station_name=self.stations_dict[reservation.dropoff_station_id]["name"],
                    type="STOP"
                )
            
            arrets_par_station[reservation.dropoff_station_id].ajouter_dropoff(
                reservation.id, reservation.number_of_people
            )
        
        # Ordonner les arrêts de manière optimale
        arrets_ordonnes = self._ordonner_arrets(arrets_par_station, reservations)
        
        # Ajouter à l'itinéraire
        itineraire.arrets.extend(arrets_ordonnes)
        
        # Retour au dépôt
        depot_retour = Arret(
            station_id=self.depot_station_id,
            station_name=self.stations_dict[self.depot_station_id]["name"],
            type="DEPOT"
        )
        itineraire.arrets.append(depot_retour)
        
        # Calculer les horaires
        self._calculer_horaires(itineraire, reservations)
        
        # Enregistrer les réservations servies
        itineraire.reservations_servies = [r.id for r in reservations]
    
    def _ordonner_arrets(self, arrets_par_station: dict, reservations: List) -> List[Arret]:
        """
        Ordonne les arrêts en respectant les contraintes:
        1. Pickup avant dropoff pour chaque réservation
        2. Respect des horaires souhaités
        3. Minimisation de la distance
        """
        arrets = list(arrets_par_station.values())
        
        # Trier par heure souhaitée la plus proche
        def calculer_heure_min(arret):
            heures = []
            for res in reservations:
                if res.id in arret.pickups:
                    heures.append(res.desired_time)
            return min(heures) if heures else datetime.max
        
        arrets.sort(key=calculer_heure_min)
        
        # Vérifier et corriger l'ordre pickup/dropoff
        arrets_corriges = []
        pickups_vus = set()
        
        for arret in arrets:
            # Ajouter d'abord tous les dropoffs possibles
            dropoffs_possibles = [d for d in arret.dropoffs if d in pickups_vus]
            pickups_possibles = arret.pickups
            
            if pickups_possibles or dropoffs_possibles:
                arret_copie = Arret(
                    station_id=arret.station_id,
                    station_name=arret.station_name,
                    type="STOP",
                    pickups=pickups_possibles,
                    dropoffs=dropoffs_possibles,
                    personnes_montantes=sum(
                        next(r.number_of_people for r in reservations if r.id == pid)
                        for pid in pickups_possibles
                    ),
                    personnes_descendantes=sum(
                        next(r.number_of_people for r in reservations if r.id == did)
                        for did in dropoffs_possibles
                    )
                )
                arrets_corriges.append(arret_copie)
                pickups_vus.update(pickups_possibles)
        
        return arrets_corriges
    
    def _calculer_horaires(self, itineraire: ItineraireMinibus, reservations: List):
   
        heure_actuelle = itineraire.arrets[0].heure_arrivee
    
       # ✅ Temps d'arrêt fixe
        TEMPS_ARRET_MINUTES = 2
    
        for i in range(1, len(itineraire.arrets)):
            arret_precedent = itineraire.arrets[i-1]
            arret_actuel = itineraire.arrets[i]
        
        # Récupérer les indices
            idx_prec = self.station_id_to_index.get(arret_precedent.station_id)
            idx_curr = self.station_id_to_index.get(arret_actuel.station_id)

            if idx_prec is not None and idx_curr is not None:
                duree_brute = self.matrice_durees[idx_prec][idx_curr]

            # ✅ CORRECTION : Conversion correcte OSRM
                if self.use_osrm:
                # OSRM retourne des SECONDES
                    duree_minutes = duree_brute / 60.0
                else:
                # Matrices déjà en minutes
                   duree_minutes = duree_brute
            
            # ✅ Ajouter le temps d'arrêt seulement pour les STOPS (pas pour le dépôt final)
                temps_arret = TEMPS_ARRET_MINUTES if arret_actuel.type == "STOP" else 0
            
            # Calculer la nouvelle heure
                heure_actuelle += timedelta(minutes=duree_minutes + temps_arret)
                arret_actuel.heure_arrivee = heure_actuelle
                logger.debug(f"🔍 Segment {arret_precedent.station_name} → {arret_actuel.station_name}")
                logger.debug(f"   Durée brute : {duree_brute}")
                logger.debug(f"   use_osrm : {self.use_osrm}")
                logger.debug(f"   Durée minutes : {duree_minutes}") 
    def reparer_solution(self, solution: Solution):
        """Répare une solution invalide"""
        for minibus_id, itineraire in solution.itineraires.items():
            self._reparer_itineraire(itineraire, solution)
    
    def _reparer_itineraire(self, itineraire: ItineraireMinibus, solution: Solution):
        """Répare un itinéraire en corrigeant les violations"""
        if len(itineraire.arrets) <= 2:
            return
        
        # Vérifier l'ordre pickup/dropoff
        pickups_vus = set()
        
        for arret in itineraire.arrets:
            # Retirer les dropoffs impossibles
            dropoffs_valides = [d for d in arret.dropoffs if d in pickups_vus]
            arret.dropoffs = dropoffs_valides
            
            # Ajouter les pickups
            pickups_vus.update(arret.pickups)