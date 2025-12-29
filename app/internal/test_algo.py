# app/internal/test_algo.py - VERSION COMPLÈTE AVEC ARRÊTS MULTIPLES ET HORAIRES

from app.database.crud import get_all_stations, get_all_reservations, get_all_minibus
from app.internal.osrm_engine import get_cost_matrices
from app.Algorithme.genetic_algoritme import GeneticAlgorithm
from app.Algorithme.solution_builder import SolutionBuilder
from app.Algorithme.fitness import FitnessCalculator
from app.Algorithme.reservation_integration import ReservationIntegrator
from app.models.route import Reservation
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_algorithm():
    """Exécute l'algorithme et retourne les objets principaux"""
    
    # 1️⃣ CHARGER LES DONNÉES
    logger.info("📊 Chargement des données...")

    stations_raw = get_all_stations()
    reservations_raw = get_all_reservations()
    minibus_raw = get_all_minibus()

    if not stations_raw or not reservations_raw:
        logger.error("❌ Pas de stations ou de réservations")
        return None, None, None, None, None, None

    # 2️⃣ CONSTRUIRE stations_dict
    stations_dict = {}
    for (station_id, name, lat, lon) in stations_raw:
        stations_dict[station_id] = {
            'name': name,
            'latitude': lat,
            'longitude': lon
        }

    # 3️⃣ CONSTRUIRE LES MATRICES OSRM
    points = [(lon, lat) for (station_id, name, lat, lon) in stations_raw]
    print("Première station :", points[0])
    matrice_durees,matrice_distances = get_cost_matrices(points)
    print(f"\n🔍 VÉRIFICATION MATRICES BRUTES:")
    print(f"Type matrice_distances: {type(matrice_distances)}")
    print(f"Type matrice_durees: {type(matrice_durees)}")
    print(f"\nExemple [0][1]:")
    print(f"  matrice_distances[0][1] = {matrice_distances[0][1]}")
    print(f"  matrice_durees[0][1] = {matrice_durees[0][1]}")
    print(f"\nSi distances > 100,000 → c'est des DURÉES en secondes (INVERSÉ !)")
    print(f"Si durees < 100 → c'est des DISTANCES en km (INVERSÉ !)\n")

    if matrice_distances is None or matrice_durees is None:
        logger.error("❌ Échec de récupération des matrices OSRM")
        return None, None, None, None, None, None

    # 4️⃣ DÉFINIR LE DÉPÔT
    DEPOT_STATION_ID = 2

    # 5️⃣ LANCER L'ALGORITHME GÉNÉTIQUE
    logger.info("🧬 Démarrage de l'algorithme génétique...")
    ga = GeneticAlgorithm(
        reservations=reservations_raw,
        minibus=minibus_raw,
        stations_dict=stations_dict,
        matrice_distances=matrice_distances,
        matrice_durees=matrice_durees,
        depot_station_id=DEPOT_STATION_ID,
        use_osrm=True,
        population_size=50,
        generations=100,
        prob_croisement=0.8,
        prob_mutation=0.2
    )
    
    best_solution, best_details = ga.run()
    
    if best_solution is None:
        logger.error("❌ Aucune solution trouvée")
        return None, None, None, None, None, None

    return best_solution, best_details, minibus_raw, stations_dict, matrice_distances, matrice_durees


def afficher_resume(best_solution, best_details):
    """Affiche le résumé de la solution"""
    print("\n" + "="*80)
    print("🏆 MEILLEURE SOLUTION TROUVÉE")
    print("="*80)
    print(f"📏 Distance totale flotte    : {best_details['distance_totale']:.2f} km")
    print(f"⏱️  Durée totale flotte       : {best_details['duree_totale']:.1f} minutes")
    print(f"🚌 Minibus utilisés          : {best_details['minibus_utilises']}")
    print(f"📊 Fitness score             : {best_solution.fitness:.2f}")
    print(f"\n⚠️  VIOLATIONS:")
    print(f"   - Capacité                : {best_details['violations_capacite']}")
    print(f"   - Ordre pickup/dropoff    : {best_details['violations_ordre']}")
    print(f"   - Horaires (retards)      : {best_details.get('violations_horaire', 0)}")
    print(f"⏰ Retard total              : {best_details.get('retard_total_minutes', 0):.1f} minutes")
    print(f"🎁 Bonus réutilisation       : {best_details.get('bonus_reutilisation', 0)}")
    print(f"\n📋 RÉSERVATIONS:")
    print(f"   - Total                   : {len(best_solution.reservations_list)}")
    print(f"   - Satisfaites             : {len(best_solution.affectations)}")
    print(f"   - Non servies             : {best_details['reservations_non_servies']}")
    print("="*80)


def afficher_itineraires(best_solution, minibus_list):
    """Affiche les itinéraires détaillés de tous les minibus"""
    print("\n" + "="*80)
    print("🗺️  ITINÉRAIRES DÉTAILLÉS")
    print("="*80)
    
    for minibus_id, itineraire in best_solution.itineraires.items():
        if not itineraire.arrets or len(itineraire.arrets) <= 2:
            continue
        
        bus_obj = next((m for m in minibus_list if m.id == minibus_id), None)
        plaque = bus_obj.license_plate if bus_obj else "?"
        
        print(f"\n{'='*80}")
        print(f"🚌 MINIBUS {minibus_id} ({plaque})")
        print(f"{'='*80}")
        print(f"📏 Distance totale      : {itineraire.distance_totale:.2f} km")
        print(f"⏱️  Durée totale         : {itineraire.duree_totale:.1f} minutes")
        print(f"👥 Charge maximale      : {itineraire.charge_maximale}/{bus_obj.capacity if bus_obj else '?'} personnes")
        print(f"📦 Réservations servies : {len(itineraire.reservations_servies)}")
        print(f"⚠️  Violations capacité  : {itineraire.violations_capacite}")
        print(f"⏰ Violations horaires  : {itineraire.violations_horaire}")
        
        print(f"\n{'─'*80}")
        print(f"{'Station':<30} | {'Action':<25} | {'Passagers':<12} | {'Distance':<10} | {'Durée':<10}")
        print(f"{'─'*80}")
        
        for idx, arret in enumerate(itineraire.arrets):
            # Déterminer le type d'action et l'emoji
            if arret.type == "DEPOT":
                type_emoji = "🏢"
                if idx == 0:
                    action_text = "DÉPART DÉPÔT"
                else:
                    action_text = "RETOUR DÉPÔT"
            else:  # STOP
                actions = []
                if arret.pickups:
                    actions.append(f"↑ {len(arret.pickups)} pickup(s)")
                if arret.dropoffs:
                    actions.append(f"↓ {len(arret.dropoffs)} dropoff(s)")
                
                if arret.pickups and arret.dropoffs:
                    type_emoji = "🟡"  # Pickup ET dropoff
                elif arret.pickups:
                    type_emoji = "🟢"  # Seulement pickup
                else:
                    type_emoji = "🔴"  # Seulement dropoff
                
                action_text = " + ".join(actions) if actions else "ARRÊT"
            
            # Informations de distance et durée
            dist_str = f"{arret.distance_depuis_precedent:.2f} km" if hasattr(arret, 'distance_depuis_precedent') and arret.distance_depuis_precedent > 0 else "-"
            duree_str = f"{arret.duree_depuis_precedent:.1f} min" if hasattr(arret, 'duree_depuis_precedent') and arret.duree_depuis_precedent > 0 else "-"
            passagers_str = f"{arret.passagers_a_bord if hasattr(arret, 'passagers_a_bord') else 0} à bord"
            
            # Ligne principale de l'arrêt
            print(f"{type_emoji} {arret.station_name:<28} | {action_text:<25} | {passagers_str:<12} | {dist_str:<10} | {duree_str:<10}")
            
            # Détails des réservations et horaires
            if arret.type == "STOP":
                details = []
                
                if arret.pickups:
                    details.append(f"      ↑ Pickups  : {arret.pickups} ({arret.personnes_montantes} pers.)")
                
                if arret.dropoffs:
                    details.append(f"      ↓ Dropoffs : {arret.dropoffs} ({arret.personnes_descendantes} pers.)")
                
                if hasattr(arret, 'heure_arrivee') and arret.heure_arrivee:
                    details.append(f"      🕐 Arrivée  : {arret.heure_arrivee.strftime('%H:%M:%S')}")
                
                if hasattr(arret, 'capacite_restante'):
                    details.append(f"      📊 Capacité : {arret.capacite_restante} places restantes")
                
                if details:
                    for detail in details:
                        print(detail)
                    print()  # Ligne vide pour aération
        
        print(f"{'─'*80}")


def test_nouvelle_reservation(best_solution, minibus_list, stations_dict, 
                              matrice_distances, matrice_durees, depot_station_id=2):
    """
    ✅ TEST: Intégration dynamique d'une nouvelle réservation
    """
    print("\n" + "="*80)
    print("🆕 TEST: INTÉGRATION D'UNE NOUVELLE RÉSERVATION")
    print("="*80)
    
    # Trouver une station de pickup qui existe déjà dans un itinéraire
    # pour maximiser les chances de réutilisation
    station_pickup_id = None
    station_dropoff_id = None
    
    for minibus_id, itineraire in best_solution.itineraires.items():
        if len(itineraire.arrets) > 3:
            # Prendre une station au milieu de l'itinéraire
            arret_milieu = itineraire.arrets[len(itineraire.arrets)//2]
            if arret_milieu.station_id != depot_station_id:
                station_pickup_id = arret_milieu.station_id
                # Prendre une autre station pour le dropoff
                for arret in itineraire.arrets:
                    if arret.station_id != station_pickup_id and arret.station_id != depot_station_id:
                        station_dropoff_id = arret.station_id
                        break
                break
    
    # Si pas trouvé, prendre des stations au hasard
    if not station_pickup_id:
        stations_disponibles = [sid for sid in stations_dict.keys() if sid != depot_station_id]
        if len(stations_disponibles) >= 2:
            station_pickup_id = stations_disponibles[0]
            station_dropoff_id = stations_disponibles[1]
    
    if not station_pickup_id or not station_dropoff_id:
        print("❌ Impossible de créer une réservation de test (pas assez de stations)")
        return
    
    # Créer une nouvelle réservation fictive
    nouvelle_res = Reservation(
        id=9999,
        client_name="Test Client",
        pickup_station_id=station_pickup_id,
        dropoff_station_id=station_dropoff_id,
        number_of_people=2,
        desired_time=datetime.now() + timedelta(hours=1),
        status="pending"
    )
    
    print(f"\n📋 Nouvelle réservation créée:")
    print(f"   ID              : {nouvelle_res.id}")
    print(f"   Client          : {nouvelle_res.client_name}")
    print(f"   Pickup          : Station {nouvelle_res.pickup_station_id} ({stations_dict[nouvelle_res.pickup_station_id]['name']})")
    print(f"   Dropoff         : Station {nouvelle_res.dropoff_station_id} ({stations_dict[nouvelle_res.dropoff_station_id]['name']})")
    print(f"   Personnes       : {nouvelle_res.number_of_people}")
    print(f"   Heure souhaitée : {nouvelle_res.desired_time.strftime('%H:%M')}")
    
    # Copier la solution pour ne pas modifier l'originale
    print("\n🔄 Création d'une copie de la solution...")
    solution_avant = best_solution.copy()
    solution_test = best_solution.copy()
    
    # Créer les composants nécessaires
    solution_builder = SolutionBuilder(
        matrice_distances, 
        matrice_durees, 
        stations_dict, 
        depot_station_id=depot_station_id,
        use_osrm=True
    )
    
    fitness_calculator = FitnessCalculator(
        matrice_distances,
        matrice_durees,
        stations_dict,
        use_osrm=True
    )
    
    integrator = ReservationIntegrator(solution_builder, fitness_calculator)
    
    # Tenter l'intégration
    print("\n🔍 Recherche d'un minibus compatible...")
    succes, minibus_id, message = integrator.integrer_nouvelle_reservation(
        solution_test,
        nouvelle_res
    )
    
    if succes:
        print(f"\n✅ SUCCÈS: {message}")
        
        # Analyser l'impact
        print("\n📊 ANALYSE D'IMPACT:")
        impact = integrator.analyser_impact(solution_avant, solution_test)
        
        print(f"\n   Distance ajoutée     : +{impact['distance_ajoutee']:.2f} km")
        print(f"   Durée ajoutée        : +{impact['duree_ajoutee']:.1f} minutes")
        print(f"   Fitness avant        : {impact['fitness_avant']:.2f}")
        print(f"   Fitness après        : {impact['fitness_apres']:.2f}")
        print(f"   Dégradation          : {impact['degradation_fitness']:.2f}")
        
        if impact['violations_ajoutees'] > 0:
            print(f"   ⚠️ Violations ajoutées : +{impact['violations_ajoutees']}")
        else:
            print(f"   ✅ Aucune violation ajoutée")
        
        if impact['retard_ajoute'] > 0:
            print(f"   ⏰ Retard ajouté      : +{impact['retard_ajoute']:.1f} minutes")
        else:
            print(f"   ✅ Aucun retard ajouté")
        
        # Afficher l'itinéraire modifié
        print(f"\n📍 ITINÉRAIRE MODIFIÉ DU MINIBUS {minibus_id}:")
        print(f"{'─'*80}")
        
        itineraire = solution_test.itineraires[minibus_id]
        bus_obj = next((m for m in minibus_list if m.id == minibus_id), None)
        
        print(f"   Minibus {minibus_id} ({bus_obj.license_plate if bus_obj else '?'})")
        print(f"   Distance : {itineraire.distance_totale:.2f} km")
        print(f"   Durée    : {itineraire.duree_totale:.1f} min")
        print(f"   Charge   : {itineraire.charge_maximale}/{bus_obj.capacity if bus_obj else '?'}")
        print(f"\n   Arrêts:")
        
        for arret in itineraire.arrets:
            if arret.type == "STOP":
                marqueur = ""
                if nouvelle_res.id in arret.pickups:
                    marqueur = "🆕 PICKUP nouvelle rés."
                elif nouvelle_res.id in arret.dropoffs:
                    marqueur = "🆕 DROPOFF nouvelle rés."
                
                if marqueur:
                    print(f"      🟡 {arret.station_name:<30} | {marqueur}")
                else:
                    actions = []
                    if arret.pickups:
                        actions.append(f"↑{len(arret.pickups)}")
                    if arret.dropoffs:
                        actions.append(f"↓{len(arret.dropoffs)}")
                    print(f"         {arret.station_name:<30} | {' '.join(actions)}")
        
        print(f"{'─'*80}")
        
    else:
        print(f"\n❌ ÉCHEC: {message}")
    
    print("\n" + "="*80)


def main():
    """Fonction principale avec tous les tests"""
    
    print("\n" + "🚀"*40)
    print("DÉMARRAGE DES TESTS DE L'ALGORITHME GÉNÉTIQUE")
    print("🚀"*40)
    
    # Exécuter l'algorithme
    result = run_algorithm()
    
    if result[0] is None:
        print("\n❌ Échec de l'exécution de l'algorithme")
        return
    
    best_solution, best_details, minibus_list, stations_dict, matrice_distances, matrice_durees = result
    
    # 1️⃣ Afficher le résumé
    afficher_resume(best_solution, best_details)
    
    # 2️⃣ Afficher les itinéraires détaillés
    afficher_itineraires(best_solution, minibus_list)
    
    # 3️⃣ Test d'intégration d'une nouvelle réservation
    print("\n\n")
    reponse = input("🔔 Voulez-vous tester l'ajout d'une nouvelle réservation ? (o/n): ")
    
    if reponse.lower() in ['o', 'oui', 'y', 'yes']:
        test_nouvelle_reservation(
            best_solution, 
            minibus_list, 
            stations_dict, 
            matrice_distances, 
            matrice_durees,
            depot_station_id=2
        )
    
    # 4️⃣ Conversion au format dictionnaire (pour l'API)
    print("\n" + "="*80)
    print("📦 EXPORT AU FORMAT DICTIONNAIRE (pour API)")
    print("="*80)
    
    solution_dict = best_solution.to_dict()
    
    print(f"✅ Solution exportée avec {len(solution_dict) - 1} itinéraires")
    print(f"📊 Métriques globales incluses")
    
    # Optionnel : sauvegarder dans un fichier JSON
    try:
        import json
        with open('solution_optimale.json', 'w', encoding='utf-8') as f:
            json.dump(solution_dict, f, indent=2, ensure_ascii=False, default=str)
        print(f"💾 Solution sauvegardée dans: solution_optimale.json")
    except Exception as e:
        logger.warning(f"⚠️  Impossible de sauvegarder le JSON: {e}")
    
    print("\n" + "✅"*40)
    print("TESTS TERMINÉS")
    print("✅"*40 + "\n")
   


if __name__ == "__main__":
    main()