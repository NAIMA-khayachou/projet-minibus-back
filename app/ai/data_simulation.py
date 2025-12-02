"""
Génération de données fictives pour tester l'algorithme génétique
Basé sur la structure de la BD Marrakech avec stations réelles
"""

import random
import json
from datetime import datetime, timedelta
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Stations de Marrakech (depuis la BD)
STATIONS_MARRAKECH = [
    {"id": 1, "name": "Jamaâ El Fna", "latitude": 31.6258, "longitude": -7.9891},
    {"id": 2, "name": "Gare Marrakech", "latitude": 31.6308, "longitude": -8.0027},
    {"id": 3, "name": "Ménara", "latitude": 31.6111, "longitude": -8.0292},
    {"id": 4, "name": "Gueliz", "latitude": 31.6364, "longitude": -8.0103},
    {"id": 5, "name": "Palmeraie", "latitude": 31.6708, "longitude": -7.9736},
    {"id": 6, "name": "Médina", "latitude": 31.6250, "longitude": -7.9914},
    {"id": 7, "name": "Aéroport Marrakech", "latitude": 31.6069, "longitude": -8.0363},
    {"id": 8, "name": "Université Cadi Ayyad", "latitude": 31.6417, "longitude": -8.0089}
]

def generer_reservations_depuis_bd(nb_reservations):
    """
    Génère des réservations au format compatible avec la BD
    Correspond à la table 'reservations'
    """
    reservations = []
    
    for i in range(nb_reservations):
        pickup_station = random.choice(STATIONS_MARRAKECH)
        dropoff_station = random.choice(STATIONS_MARRAKECH)
        
        # Assurer que pickup != dropoff
        while dropoff_station['id'] == pickup_station['id']:
            dropoff_station = random.choice(STATIONS_MARRAKECH)
        
        reservations.append({
            "id": i + 1,
            "client_id": random.randint(1, 6),  # Clients existants dans la BD
            "pickup_station_id": pickup_station['id'],
            "pickup_station_name": pickup_station['name'],
            "pickup_location": {
                "lat": pickup_station['latitude'],
                "lon": pickup_station['longitude']
            },
            "dropoff_station_id": dropoff_station['id'],
            "dropoff_station_name": dropoff_station['name'],
            "dropoff_location": {
                "lat": dropoff_station['latitude'],
                "lon": dropoff_station['longitude']
            },
            "number_of_people": random.randint(1, 4),
            "desired_time": generer_heure_aleatoire(),
            "status": "pending"
        })
    
    return reservations

def generer_heure_aleatoire():
    """Génère une heure aléatoire entre 7h et 22h"""
    heure = random.randint(7, 21)
    minute = random.randint(0, 59)
    return f"{heure:02d}:{minute:02d}:00"

def generer_minibus_depuis_bd(nb_minibus=None):
    """
    Génère la flotte de minibus depuis la BD
    Correspond à la table 'minibus'
    """
    # Minibus existants dans la BD
    minibus_db = [
        {"id": 1, "capacity": 20, "license_plate": "M-1234-AB"},
        {"id": 2, "capacity": 18, "license_plate": "M-5678-CD"},
        {"id": 3, "capacity": 22, "license_plate": "M-9012-EF"},
        {"id": 4, "capacity": 16, "license_plate": "M-3456-GH"},
        {"id": 5, "capacity": 20, "license_plate": "M-7890-IJ"}
    ]
    
    if nb_minibus:
        minibus_db = minibus_db[:nb_minibus]
    
    # Ajouter position initiale aléatoire (garage central)
    for bus in minibus_db:
        station = random.choice(STATIONS_MARRAKECH)
        bus['position_initiale'] = {
            "lat": station['latitude'],
            "lon": station['longitude']
        }
        bus['current_passengers'] = 0
        bus['status'] = 'available'
    
    return minibus_db

def generer_scenario_test(nom_scenario):
    """
    Génère différents scénarios de test basés sur la BD Marrakech
    
    Scénarios disponibles:
    - 'petit': 6 réservations (comme dans la BD), 2 bus
    - 'moyen': 20 réservations, 3 bus
    - 'grand': 50 réservations, 5 bus
    - 'rush': 30 réservations concentrées, 4 bus
    """
    
    scenarios = {
        'petit': {'reservations': 6, 'bus': 2},
        'moyen': {'reservations': 20, 'bus': 3},
        'grand': {'reservations': 50, 'bus': 5},
        'rush': {'reservations': 30, 'bus': 4}
    }
    
    if nom_scenario not in scenarios:
        nom_scenario = 'moyen'
    
    config = scenarios[nom_scenario]
    
    reservations = generer_reservations_depuis_bd(config['reservations'])
    minibus = generer_minibus_depuis_bd(config['bus'])
    
    return {
        "scenario": nom_scenario,
        "timestamp": datetime.now().isoformat(),
        "ville": "Marrakech",
        "stations": STATIONS_MARRAKECH,
        "reservations": reservations,
        "minibus": minibus,
        "contraintes": {
            "temps_max_trajet_min": 60,  # minutes
            "distance_max_detour_km": 3.0,  # km
            "temps_attente_max_min": 20  # minutes
        }
    }

def generer_depuis_bd_reelle():
    """
    Génère un scénario exactement comme dans la BD
    (6 réservations réelles + 5 minibus réels)
    """
    
    # Réservations exactes de la BD
    reservations_bd = [
        {
            "id": 1, "client_id": 1,
            "pickup_station_id": 1, "pickup_station_name": "Jamaâ El Fna",
            "pickup_location": {"lat": 31.6258, "lon": -7.9891},
            "dropoff_station_id": 7, "dropoff_station_name": "Aéroport Marrakech",
            "dropoff_location": {"lat": 31.6069, "lon": -8.0363},
            "number_of_people": 3, "desired_time": "08:00:00", "status": "pending"
        },
        {
            "id": 2, "client_id": 2,
            "pickup_station_id": 2, "pickup_station_name": "Gare Marrakech",
            "pickup_location": {"lat": 31.6308, "lon": -8.0027},
            "dropoff_station_id": 7, "dropoff_station_name": "Aéroport Marrakech",
            "dropoff_location": {"lat": 31.6069, "lon": -8.0363},
            "number_of_people": 2, "desired_time": "08:30:00", "status": "pending"
        },
        {
            "id": 3, "client_id": 3,
            "pickup_station_id": 8, "pickup_station_name": "Université Cadi Ayyad",
            "pickup_location": {"lat": 31.6417, "lon": -8.0089},
            "dropoff_station_id": 4, "dropoff_station_name": "Gueliz",
            "dropoff_location": {"lat": 31.6364, "lon": -8.0103},
            "number_of_people": 4, "desired_time": "09:00:00", "status": "pending"
        },
        {
            "id": 4, "client_id": 4,
            "pickup_station_id": 8, "pickup_station_name": "Université Cadi Ayyad",
            "pickup_location": {"lat": 31.6417, "lon": -8.0089},
            "dropoff_station_id": 1, "dropoff_station_name": "Jamaâ El Fna",
            "dropoff_location": {"lat": 31.6258, "lon": -7.9891},
            "number_of_people": 2, "desired_time": "09:15:00", "status": "pending"
        },
        {
            "id": 5, "client_id": 5,
            "pickup_station_id": 4, "pickup_station_name": "Gueliz",
            "pickup_location": {"lat": 31.6364, "lon": -8.0103},
            "dropoff_station_id": 2, "dropoff_station_name": "Gare Marrakech",
            "dropoff_location": {"lat": 31.6308, "lon": -8.0027},
            "number_of_people": 1, "desired_time": "17:00:00", "status": "pending"
        },
        {
            "id": 6, "client_id": 6,
            "pickup_station_id": 3, "pickup_station_name": "Ménara",
            "pickup_location": {"lat": 31.6111, "lon": -8.0292},
            "dropoff_station_id": 5, "dropoff_station_name": "Palmeraie",
            "dropoff_location": {"lat": 31.6708, "lon": -7.9736},
            "number_of_people": 2, "desired_time": "17:30:00", "status": "pending"
        }
    ]
    
    minibus = generer_minibus_depuis_bd()
    
    return {
        "scenario": "bd_reelle",
        "timestamp": datetime.now().isoformat(),
        "ville": "Marrakech",
        "source": "Base de données réelle",
        "stations": STATIONS_MARRAKECH,
        "reservations": reservations_bd,
        "minibus": minibus,
        "contraintes": {
            "temps_max_trajet_min": 60,
            "distance_max_detour_km": 3.0,
            "temps_attente_max_min": 20
        }
    }

def sauvegarder_scenario(scenario, nom_fichier="test_data.json"):
    """Sauvegarde un scénario dans un fichier JSON"""
    with open(nom_fichier, 'w', encoding='utf-8') as f:
        json.dump(scenario, f, indent=2, ensure_ascii=False)
    print(f"✅ Scénario '{scenario['scenario']}' sauvegardé dans {nom_fichier}")
    print(f"   - {len(scenario['reservations'])} réservations")
    print(f"   - {len(scenario['minibus'])} minibus")
    print(f"   - {len(scenario['stations'])} stations")

def charger_scenario(nom_fichier="test_data.json"):
    """Charge un scénario depuis un fichier JSON"""
    with open(nom_fichier, 'r', encoding='utf-8') as f:
        return json.load(f)

# Tests et génération de données
if __name__ == "__main__":
    print("🚀 Génération de données de test - Marrakech")
    print("=" * 50)
    print()
    
    # 1. Générer le scénario de la BD réelle
    print("📊 Génération du scénario BD réelle...")
    scenario_bd = generer_depuis_bd_reelle()
    sauvegarder_scenario(scenario_bd, "test_data_bd_reelle.json")
    print()
    
    # 2. Générer les autres scénarios
    scenarios = ['petit', 'moyen', 'grand', 'rush']
    
    for nom in scenarios:
        print(f"📊 Génération du scénario '{nom}'...")
        scenario = generer_scenario_test(nom)
        nom_fichier = f"test_data_{nom}.json"
        sauvegarder_scenario(scenario, nom_fichier)
        print()
    
    print("=" * 50)
    print("✨ Tous les scénarios ont été générés !")
    print()
    print("Fichiers créés:")
    print("  - test_data_bd_reelle.json (données exactes de la BD)")
    for nom in scenarios:
        print(f"  - test_data_{nom}.json")
    print()
    print("🗺️  Stations disponibles:")
    for station in STATIONS_MARRAKECH:
        print(f"   {station['id']}. {station['name']}")