
import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta
from .solution import Solution, Arret, ItineraireMinibus

logger = logging.getLogger(__name__)

class ReservationIntegrator:
    """Gère l'intégration de nouvelles réservations dans des routes existantes"""
    
    def __init__(self, solution_builder, fitness_calculator):
        self.solution_builder = solution_builder
        self.fitness_calculator = fitness_calculator
    
    def integrer_nouvelle_reservation(
        self, 
        solution_actuelle: Solution, 
        nouvelle_reservation
    ) -> Tuple[bool, Optional[int], str]:
        """
        ✅ CORRIGÉ : Intègre une nouvelle réservation SANS DUPLICATION
        
        Stratégie:
        1. Chercher un minibus dont la route passe par la station pickup
        2. Si trouvé, INSÉRER la réservation dans l'itinéraire existant
        3. Sinon, assigner à un minibus peu chargé
        
        Returns:
            (succès: bool, minibus_id: int, message: str)
        """
        logger.info(f"🔍 Intégration de la réservation {nouvelle_reservation.id}")
        logger.info(f"   Pickup: Station {nouvelle_reservation.pickup_station_id}")
        logger.info(f"   Dropoff: Station {nouvelle_reservation.dropoff_station_id}")
        logger.info(f"   Personnes: {nouvelle_reservation.number_of_people}")
        logger.info(f"   Heure souhaitée: {nouvelle_reservation.desired_time}")
        
        # 1. Chercher un minibus compatible
        minibus_compatible = solution_actuelle.trouver_minibus_compatible(nouvelle_reservation)
        
        if minibus_compatible:
            logger.info(f"✅ Minibus compatible trouvé: {minibus_compatible}")
            
            # Ajouter la réservation
            solution_actuelle.affectations[nouvelle_reservation.id] = minibus_compatible
            
            # Ajouter à la liste des réservations
            if nouvelle_reservation not in solution_actuelle.reservations_list:
                solution_actuelle.reservations_list.append(nouvelle_reservation)
                solution_actuelle.reservations_by_id[nouvelle_reservation.id] = nouvelle_reservation
            
            # ✅ CORRECTION : INSÉRER intelligemment au lieu de reconstruire
            self._inserer_reservation_dans_itineraire(
                solution_actuelle, 
                minibus_compatible, 
                nouvelle_reservation
            )
            
            # Recalculer le fitness
            self.fitness_calculator.calculer_fitness(solution_actuelle)
            
            return (
                True, 
                minibus_compatible,
                f"Réservation intégrée au minibus {minibus_compatible} (route existante réutilisée)"
            )
        
        else:
            logger.info("⚠️ Aucun minibus compatible, assignation à un minibus peu chargé")
            
            # Trouver le minibus le moins chargé
            minibus_moins_charge = min(
                solution_actuelle.minibus_list,
                key=lambda m: solution_actuelle.itineraires[m.id].charge_maximale
            )
            
            # Vérifier la capacité
            capacite_disponible = (
                minibus_moins_charge.capacity - 
                solution_actuelle.itineraires[minibus_moins_charge.id].charge_maximale
            )
            
            if capacite_disponible >= nouvelle_reservation.number_of_people:
                solution_actuelle.affectations[nouvelle_reservation.id] = minibus_moins_charge.id
                
                if nouvelle_reservation not in solution_actuelle.reservations_list:
                    solution_actuelle.reservations_list.append(nouvelle_reservation)
                    solution_actuelle.reservations_by_id[nouvelle_reservation.id] = nouvelle_reservation
                
                # ✅ CORRECTION : Insérer au lieu de reconstruire
                self._inserer_reservation_dans_itineraire(
                    solution_actuelle,
                    minibus_moins_charge.id,
                    nouvelle_reservation
                )
                
                # Recalculer le fitness
                self.fitness_calculator.calculer_fitness(solution_actuelle)
                
                return (
                    True,
                    minibus_moins_charge.id,
                    f"Réservation assignée au minibus {minibus_moins_charge.id} (nouvelle route)"
                )
            else:
                logger.error("❌ Aucun minibus n'a la capacité suffisante")
                return (
                    False,
                    None,
                    f"Impossible d'intégrer: capacité insuffisante (besoin: {nouvelle_reservation.number_of_people}, dispo: {capacite_disponible})"
                )
    
    def _inserer_reservation_dans_itineraire(
        self, 
        solution: Solution, 
        minibus_id: int, 
        reservation
    ):
        """
        ✅ NOUVELLE MÉTHODE : Insère une réservation dans un itinéraire existant
        SANS le reconstruire complètement
        """
        itineraire = solution.itineraires[minibus_id]
        
        # 1. Trouver ou créer l'arrêt PICKUP
        position_pickup = self._trouver_ou_creer_arret_pickup(
            itineraire, 
            reservation,
            solution.stations_dict
        )
        
        # 2. Trouver ou créer l'arrêt DROPOFF (APRÈS le pickup)
        position_dropoff = self._trouver_ou_creer_arret_dropoff(
            itineraire,
            reservation,
            position_pickup,
            solution.stations_dict
        )
        
        # 3. Ajouter la réservation à la liste servie
        if reservation.id not in itineraire.reservations_servies:
            itineraire.reservations_servies.append(reservation.id)
        
        # 4. Recalculer les horaires de l'itinéraire
        reservations = solution.get_reservations_by_minibus(minibus_id)
        self.solution_builder._calculer_horaires(itineraire, reservations)
        
        logger.info(f"✅ Réservation {reservation.id} insérée dans l'itinéraire")
    
    def _trouver_ou_creer_arret_pickup(
        self, 
        itineraire: ItineraireMinibus, 
        reservation,
        stations_dict: dict
    ) -> int:
        """
        Trouve un arrêt existant à la station pickup OU le crée
        
        Returns: position de l'arrêt pickup
        """
        pickup_station_id = reservation.pickup_station_id
        
        # Chercher un arrêt existant à cette station
        for i, arret in enumerate(itineraire.arrets):
            if arret.station_id == pickup_station_id and arret.type == "STOP":
                # ✅ Arrêt existant : ajouter le pickup
                arret.ajouter_pickup(reservation.id, reservation.number_of_people)
                logger.info(f"   ✅ Pickup ajouté à l'arrêt existant: {arret.station_name}")
                return i
        
        # ❌ Pas d'arrêt existant : en créer un nouveau
        # Trouver la meilleure position (basée sur l'heure souhaitée)
        position_insertion = self._trouver_position_optimale(
            itineraire,
            reservation.desired_time,
            pickup_station_id
        )
        
        # Créer le nouvel arrêt
        nouvel_arret = Arret(
            station_id=pickup_station_id,
            station_name=stations_dict[pickup_station_id]["name"],
            type="STOP"
        )
        nouvel_arret.ajouter_pickup(reservation.id, reservation.number_of_people)
        
        # Insérer dans l'itinéraire
        itineraire.arrets.insert(position_insertion, nouvel_arret)
        logger.info(f"   ✅ Nouvel arrêt pickup créé à la position {position_insertion}: {nouvel_arret.station_name}")
        
        return position_insertion
    
    def _trouver_ou_creer_arret_dropoff(
        self,
        itineraire: ItineraireMinibus,
        reservation,
        position_pickup: int,
        stations_dict: dict
    ) -> int:
        """
        Trouve un arrêt existant à la station dropoff APRÈS le pickup OU le crée
        
        Returns: position de l'arrêt dropoff
        """
        dropoff_station_id = reservation.dropoff_station_id
        
        # Chercher un arrêt existant APRÈS le pickup
        for i in range(position_pickup + 1, len(itineraire.arrets)):
            arret = itineraire.arrets[i]
            if arret.station_id == dropoff_station_id and arret.type == "STOP":
                # ✅ Arrêt existant : ajouter le dropoff
                arret.ajouter_dropoff(reservation.id, reservation.number_of_people)
                logger.info(f"   ✅ Dropoff ajouté à l'arrêt existant: {arret.station_name}")
                return i
        
        # ❌ Pas d'arrêt existant : en créer un nouveau
        # Insérer avant le dépôt final
        position_insertion = len(itineraire.arrets) - 1
        
        # Créer le nouvel arrêt
        nouvel_arret = Arret(
            station_id=dropoff_station_id,
            station_name=stations_dict[dropoff_station_id]["name"],
            type="STOP"
        )
        nouvel_arret.ajouter_dropoff(reservation.id, reservation.number_of_people)
        
        # Insérer dans l'itinéraire
        itineraire.arrets.insert(position_insertion, nouvel_arret)
        logger.info(f"   ✅ Nouvel arrêt dropoff créé à la position {position_insertion}: {nouvel_arret.station_name}")
        
        return position_insertion
    
    def _trouver_position_optimale(
        self,
        itineraire: ItineraireMinibus,
        heure_souhaitee: datetime,
        station_id: int
    ) -> int:
        """
        Trouve la meilleure position pour insérer un nouvel arrêt
        basée sur l'heure souhaitée
        
        Returns: index où insérer (1 = après dépôt initial)
        """
        # Exclure les dépôts (premier et dernier)
        arrets_non_depot = [
            (i, arret) for i, arret in enumerate(itineraire.arrets)
            if arret.type == "STOP"
        ]
        
        if not arrets_non_depot:
            # Pas d'arrêts existants : insérer après le dépôt initial
            return 1
        
        # Trouver l'arrêt dont l'heure est la plus proche (mais avant)
        meilleure_position = 1
        
        for i, arret in arrets_non_depot:
            if arret.heure_arrivee and arret.heure_arrivee <= heure_souhaitee:
                meilleure_position = i + 1
            else:
                # Dès qu'on dépasse l'heure souhaitée, on s'arrête
                break
        
        return meilleure_position
    
    def analyser_impact(
        self, 
        solution_avant: Solution, 
        solution_apres: Solution
    ) -> dict:
        """
        ✅ Analyse l'impact de l'ajout d'une réservation
        """
        impact = {
            "distance_ajoutee": solution_apres.distance_totale_flotte - solution_avant.distance_totale_flotte,
            "duree_ajoutee": solution_apres.duree_totale_flotte - solution_avant.duree_totale_flotte,
            "fitness_avant": solution_avant.fitness,
            "fitness_apres": solution_apres.fitness,
            "degradation_fitness": solution_apres.fitness - solution_avant.fitness,
            "violations_ajoutees": solution_apres.violations_totales - solution_avant.violations_totales,
            "retard_ajoute": solution_apres.retard_total - solution_avant.retard_total
        }
        
        logger.info("\n📊 IMPACT DE L'INTÉGRATION:")
        logger.info(f"   Distance ajoutée: +{impact['distance_ajoutee']:.2f} km")
        logger.info(f"   Durée ajoutée: +{impact['duree_ajoutee']:.1f} min")
        logger.info(f"   Fitness: {impact['fitness_avant']:.2f} → {impact['fitness_apres']:.2f}")
        
        if impact['violations_ajoutees'] > 0:
            logger.warning(f"   ⚠️ Violations ajoutées: +{impact['violations_ajoutees']}")
        
        if impact['retard_ajoute'] > 0:
            logger.warning(f"   ⏰ Retard ajouté: +{impact['retard_ajoute']:.1f} min")
        
        return impact