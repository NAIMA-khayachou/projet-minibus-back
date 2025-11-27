# database/test.py
import sys
import os

# Ajouter le chemin parent
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from database import *
    from database.init_database import init_database
    
    print(" Test du module database")
    
    # D'abord initialiser la base
    print(" Initialisation de la base de données...")
    if init_database():
        print(" Base initialisée avec le fichier SQL")
    else:
        print(" Échec de l'initialisation")
        exit(1)
    
    # Attendre un peu pour être sûr que les tables sont créées
    import time
    time.sleep(1)
    
    # Maintenant tester les fonctions
    print("\n Test des fonctions...")
    
    stations = get_all_stations()
    print(f" Stations: {len(stations)} trouvées")
    
    minibus = get_all_minibus()
    print(f" Minibus: {len(minibus)} trouvés")
    
    reservations = get_all_reservations()
    print(f" Réservations: {len(reservations)} trouvées")
    
    # Afficher quelques données
    if stations:
        print("\n Exemple de stations:")
        for station in stations[:3]:
            print(f"   - {station[1]} (Lat: {station[2]}, Lng: {station[3]})")
    
    if minibus:
        print("\n Exemple de minibus:")
        for bus in minibus[:2]:
            print(f"   - {bus[2]} (Capacité: {bus[1]} personnes)")
    
    if reservations:
        print("\n Exemple de réservations:")
        for res in reservations[:2]:
            print(f"   - Client {res[1]} → {res[2]} ({res[5]} personnes à {res[6]})")
            
    print("\n Module database fonctionne parfaitement!")
    
except ImportError as e:
    print(f" Erreur d'import: {e}")
except Exception as e:
    print(f"❌ Erreur: {e}")