# app/internal/test_algo.py - VERSION CORRIGÉE FINALE AVEC run_algorithm

from app.database.crud import get_all_stations, get_all_reservations, get_all_minibus
from app.internal.osrm_engine import get_cost_matrices
from app.Algorithme.genetic_algoritme import GeneticAlgorithm
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
        return None, None, None, None

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
    matrice_durees, matrice_distances = get_cost_matrices(points)
    if matrice_distances is None or matrice_durees is None:
        logger.error("❌ Échec de récupération des matrices OSRM")
        return None, None, None, None

    # 4️⃣ DÉFINIR LE DÉPÔT
    DEPOT_STATION_ID = 2

    # 5️⃣ LANCER L'ALGORITHME GÉNÉTIQUE
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
        return None, None, None, None

    return best_solution, best_details, minibus_raw, stations_dict


def main():
    """Fonction principale, conserve tout le code existant"""
    best_solution, best_details, minibus, stations_dict = run_algorithm()
    if not best_solution:
        return

    # ========================================
    # 7️⃣ AFFICHER LES RÉSULTATS
    # ========================================
    print("\n" + "="*60)
    print("🏆 MEILLEURE SOLUTION TROUVÉE")
    print("="*60)
    print(f"📏 Distance totale: {best_details['distance_totale']:.2f} km")
    print(f"⏱️  Durée totale: {best_details['duree_totale']:.1f} minutes")
    print(f"🚌 Minibus utilisés: {best_details['minibus_utilises']}")
    print(f"⚠️  Violations capacité: {best_details['violations_capacite']}")
    print(f"⚠️  Violations ordre: {best_details['violations_ordre']}")
    print(f"❌ Réservations non servies: {best_details['reservations_non_servies']}")

    # ========================================
    # 8️⃣ AFFICHER LES ITINÉRAIRES
    # ========================================
    for minibus_id, itineraire in best_solution.itineraires.items():
        if not itineraire.arrets or len(itineraire.arrets) <= 2:
            continue
        
        bus_obj = next((m for m in minibus if m.id == minibus_id), None)
        plaque = bus_obj.license_plate if bus_obj else "?"
        
        print(f"\n🚌 Minibus {minibus_id} ({plaque}) - {len(itineraire.arrets)} arrêts")
        print(f"   Distance: {itineraire.distance_totale:.2f} km")
        print(f"   Durée: {itineraire.duree_totale:.1f} min")
        print(f"   Charge max: {itineraire.charge_maximale}/{bus_obj.capacity if bus_obj else '?'}")
        
        print(f"\n   {'Type':<10} | {'Station':<25} | {'Passagers':<10} | {'Dist (km)':<10} | {'Durée (min)':<12}")
        print(f"   {'-'*85}")
        
        for arret in itineraire.arrets:
            type_emoji = "🏢" if arret.type == "DEPOT" else ("🟢" if arret.type == "PICKUP" else "🔴")
            dist_str = f"{arret.distance_depuis_precedent:.2f}" if hasattr(arret, 'distance_depuis_precedent') else "-"
            duree_str = f"{arret.duree_depuis_precedent:.1f}" if hasattr(arret, 'duree_depuis_precedent') else "-"
            passagers_str = f"{arret.passagers_a_bord if hasattr(arret, 'passagers_a_bord') else 0}"
            
            print(f"   {type_emoji} {arret.type:<8} | {arret.station_name:<25} | {passagers_str:<10} | {dist_str:<10} | {duree_str:<12}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
