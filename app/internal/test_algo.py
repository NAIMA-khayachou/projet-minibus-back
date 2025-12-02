# app/internal/test_algo.py - VERSION CORRIGÉE FINALE

from app.database.crud import get_all_stations, get_all_reservations, get_all_minibus
from app.internal.osrm_engine import get_cost_matrices
from app.Algorithme.genetic_algoritme import GeneticAlgorithm
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # ========================================
    # 1️⃣ CHARGER LES DONNÉES
    # ========================================
    logger.info("📊 Chargement des données...")
    
    stations_raw = get_all_stations()  # [(id, name, lat, lon), ...]
    reservations_raw = get_all_reservations()  # ✅ Retourne déjà des objets Reservation
    minibus_raw = get_all_minibus()  # ✅ Retourne déjà des objets Minibus
    
    if not stations_raw:
        logger.error("❌ Aucune station trouvée")
        return
    
    if not reservations_raw:
        logger.error("❌ Aucune réservation trouvée")
        return
    
    logger.info(f"✅ {len(stations_raw)} stations, {len(reservations_raw)} réservations, {len(minibus_raw)} minibus")
    
    # ========================================
    # 2️⃣ CONSTRUIRE stations_dict DANS LE BON ORDRE
    # ========================================
    stations_dict = {}
    for (station_id, name, lat, lon) in stations_raw:
        stations_dict[station_id] = {
            'name': name,
            'latitude': lat,
            'longitude': lon
        }
    
    logger.info(f"📍 Stations: {list(stations_dict.keys())}")
    
    # ========================================
    # 3️⃣ CONSTRUIRE LES MATRICES AVEC OSRM
    # ========================================
    logger.info("🗺️ Construction des matrices de distances/durées avec OSRM...")
    
    # ✅ ATTENTION: OSRM attend (longitude, latitude)
    points = [(lon, lat) for (station_id, name, lat, lon) in stations_raw]
    
    logger.info(f"📍 Points OSRM (lon, lat): {points[:3]}...")
    
    matrice_durees, matrice_distances = get_cost_matrices(points)
    
    if matrice_distances is None or matrice_durees is None:
        logger.error("❌ Échec de la récupération des matrices OSRM")
        logger.error("⚠️ Vérifiez que le serveur OSRM est démarré sur http://localhost:5000")
        return
    
    # ✅ AFFICHER QUELQUES DISTANCES POUR VÉRIFICATION
    logger.info("\n🔍 VÉRIFICATION DES MATRICES:")
    for i in range(min(3, len(stations_raw))):
        for j in range(min(3, len(stations_raw))):
            if i != j:
                dist_m = matrice_distances[i][j]
                dist_km = dist_m / 1000
                duree_s = matrice_durees[i][j]
                duree_min = duree_s / 60
                
                station_i = stations_raw[i][1]
                station_j = stations_raw[j][1]
                
                logger.info(f"   {station_i} → {station_j}: {dist_km:.2f} km, {duree_min:.1f} min")
    
    # ========================================
    # 4️⃣ LES RÉSERVATIONS SONT DÉJÀ DES OBJETS
    # ========================================
    reservations = reservations_raw  # ✅ Pas besoin de recréer
    
    logger.info(f"\n📋 {len(reservations)} Réservations chargées:")
    for res in reservations[:3]:  # Afficher les 3 premières
        logger.info(f"   #{res.id}: {res.client_name} | Station {res.pickup_station_id} → {res.dropoff_station_id} | {res.number_of_people} pers")
    
    # ========================================
    # 5️⃣ LES MINIBUS SONT DÉJÀ DES OBJETS
    # ========================================
    minibus = minibus_raw  # ✅ Pas besoin de recréer
    
    logger.info(f"\n🚌 {len(minibus)} Minibus chargés:")
    for bus in minibus[:3]:
        logger.info(f"   #{bus.id}: {bus.license_plate} (capacité {bus.capacity})")
    
    # ========================================
    # 6️⃣ DÉFINIR LE DÉPÔT
    # ========================================
    # ✅ OPTION 1: Choisir manuellement (ex: Gare Marrakech = ID 2)
    DEPOT_STATION_ID = 2
    
    # ✅ OPTION 2: Demander à l'utilisateur
    # print("\n🏢 Stations disponibles:")
    # for sid, sdata in stations_dict.items():
    #     print(f"   {sid}: {sdata['name']}")
    # DEPOT_STATION_ID = int(input("Choisissez l'ID du dépôt: "))
    
    logger.info(f"🏢 Dépôt: Station {DEPOT_STATION_ID} ({stations_dict[DEPOT_STATION_ID]['name']})")
    
    # ========================================
    # 7️⃣ LANCER L'ALGORITHME GÉNÉTIQUE
    # ========================================
    logger.info("\n🧬 Lancement de l'algorithme génétique...")
    
    ga = GeneticAlgorithm(
        reservations=reservations,
        minibus=minibus,
        stations_dict=stations_dict,
        matrice_distances=matrice_distances,
        matrice_durees=matrice_durees,
        depot_station_id=DEPOT_STATION_ID,
        use_osrm=True,  # ✅ IMPORTANT !
        population_size=50,   # ✅ Augmenté
        generations=100,      # ✅ Augmenté
        prob_croisement=0.8,
        prob_mutation=0.2
    )
    
    best_solution, best_details = ga.run()
    
    if best_solution is None:
        logger.error("❌ Aucune solution trouvée")
        return
    
    # ========================================
    # 8️⃣ AFFICHER LES RÉSULTATS
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
    # 9️⃣ AFFICHER LES ITINÉRAIRES
    # ========================================
    print("\n" + "="*60)
    print("🗺️  ITINÉRAIRES DÉTAILLÉS")
    print("="*60)
    
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