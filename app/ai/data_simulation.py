"""
Génération de données fictives pour tester l'algorithme génétique
Génère des demandes de trajets et une flotte de minibus
"""

import random
import json
from datetime import datetime, timedelta
import sys
sys.stdout.reconfigure(encoding='utf-8')

def generer_demandes(nb_passagers, zone_geographique):
    """
    Génère des demandes de trajets fictives dans une zone géographique
    
    Args:
        nb_passagers: Nombre de demandes à générer
        zone_geographique: Dict avec lat_min, lat_max, lon_min, lon_max
    
    Returns:
        Liste de demandes avec coordonnées GPS
    """
    demandes = []
    
    for i in range(nb_passagers):
        demandes.append({
            "id": i + 1,
            "depart": {
                "lat": round(random.uniform(zone_geographique['lat_min'], 
                                           zone_geographique['lat_max']), 6),
                "lon": round(random.uniform(zone_geographique['lon_min'], 
                                           zone_geographique['lon_max']), 6)
            },
            "arrivee": {
                "lat": round(random.uniform(zone_geographique['lat_min'], 
                                           zone_geographique['lat_max']), 6),
                "lon": round(random.uniform(zone_geographique['lon_min'], 
                                           zone_geographique['lon_max']), 6)
            },
            "nb_passagers": random.randint(1, 4),
            "heure_demande": generer_heure_aleatoire(),
            "priorite": random.choice(["normale", "normale", "normale", "urgente"])
        })
    
    return demandes

def generer_heure_aleatoire():
    """Génère une heure aléatoire entre 7h et 22h"""
    heure = random.randint(7, 21)
    minute = random.randint(0, 59)
    return f"{heure:02d}:{minute:02d}"

def generer_bus(nb_bus, zone_geographique):
    """
    Génère une flotte de minibus avec positions initiales
    
    Args:
        nb_bus: Nombre de minibus
        zone_geographique: Zone où placer les bus
    
    Returns:
        Liste de minibus
    """
    bus_list = []
    
    for i in range(nb_bus):
        bus_list.append({
            "id": i + 1,
            "capacite": random.choice([6, 8, 10]),  # Capacités variées
            "position_initiale": {
                "lat": round(random.uniform(zone_geographique['lat_min'], 
                                           zone_geographique['lat_max']), 6),
                "lon": round(random.uniform(zone_geographique['lon_min'], 
                                           zone_geographique['lon_max']), 6)
            },
            "disponible": True
        })
    
    return bus_list

def generer_scenario_test(nom_scenario):
    """
    Génère différents scénarios de test
    
    Scénarios disponibles:
    - 'petit': 10 demandes, 2 bus
    - 'moyen': 30 demandes, 5 bus
    - 'grand': 100 demandes, 15 bus
    - 'rush': 50 demandes concentrées, 8 bus
    """
    
    # Zone de Casablanca (exemple)
    zone_casa = {
        'lat_min': 33.52,
        'lat_max': 33.65,
        'lon_min': -7.70,
        'lon_max': -7.50
    }
    
    scenarios = {
        'petit': {'demandes': 10, 'bus': 2},
        'moyen': {'demandes': 30, 'bus': 5},
        'grand': {'demandes': 100, 'bus': 15},
        'rush': {'demandes': 50, 'bus': 8}
    }
    
    if nom_scenario not in scenarios:
        nom_scenario = 'moyen'
    
    config = scenarios[nom_scenario]
    
    demandes = generer_demandes(config['demandes'], zone_casa)
    bus = generer_bus(config['bus'], zone_casa)
    
    return {
        "scenario": nom_scenario,
        "timestamp": datetime.now().isoformat(),
        "zone": zone_casa,
        "demandes": demandes,
        "bus": bus,
        "contraintes": {
            "temps_max_trajet": 45,  # minutes
            "distance_max_detour": 2.0,  # km
            "temps_attente_max": 15  # minutes
        }
    }

def sauvegarder_scenario(scenario, nom_fichier="test_data.json"):
    """Sauvegarde un scénario dans un fichier JSON"""
    with open(nom_fichier, 'w', encoding='utf-8') as f:
        json.dump(scenario, f, indent=2, ensure_ascii=False)
    print(f"✅ Scénario sauvegardé dans {nom_fichier}")
    print(f"   - {len(scenario['demandes'])} demandes")
    print(f"   - {len(scenario['bus'])} minibus")

def charger_scenario(nom_fichier="test_data.json"):
    """Charge un scénario depuis un fichier JSON"""
    with open(nom_fichier, 'r', encoding='utf-8') as f:
        return json.load(f)

# Tests et génération de données
if __name__ == "__main__":
    print("🚀 Génération de données de test...")
    print()
    
    # Générer plusieurs scénarios
    scenarios = ['petit', 'moyen', 'grand', 'rush']
    
    for nom in scenarios:
        scenario = generer_scenario_test(nom)
        nom_fichier = f"test_data_{nom}.json"
        sauvegarder_scenario(scenario, nom_fichier)
        print()
    
    print("✨ Tous les scénarios ont été générés !")
    print()
    print("Fichiers créés:")
    for nom in scenarios:
        print(f"  - test_data_{nom}.json")