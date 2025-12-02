# app/database/test_final.py
import sys
import os
import uuid
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import crud
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

def test_simple():
    print("=== TEST SIMPLIFIÉ ===")
    
    # Test 1: Utilisateurs
    print("\n1. Test utilisateurs...")
    crud.initialize_default_users()
    admin = crud.authenticate_user('admin@test.com', 'admin123')
    print(f"   ✅ Admin: {admin['email'] if admin else '❌'}")
    
    # Test 2: Client avec email unique
    print("\n2. Test création client...")
    unique_email = f"test.{uuid.uuid4().hex[:6]}@test.com"
    client_id = crud.create_client("Test", "User", unique_email, "+212600000000")
    print(f"   ✅ Client créé: ID={client_id}, Email={unique_email}")
    
    # Test 3: Stations
    print("\n3. Test stations...")
    stations = crud.get_all_stations()
    print(f"   ✅ Stations: {len(stations)}")
    
    # Test 4: Minibus
    print("\n4. Test minibus...")
    minibus = crud.get_all_minibus()
    print(f"   ✅ Minibus: {len(minibus)}")
    
    # Test 5: Réservations
    print("\n5. Test réservations...")
    reservations = crud.get_all_reservations()
    print(f"   ✅ Réservations: {len(reservations)}")
    
    # Test 6: Routes optimisées - CORRECTION
   # test_final.py - dans la section des tests

print("\n6. Test routes optimisées...")
minibus_list = crud.get_all_minibus()
if minibus_list:
    try:
        # Option 1: Envoyer une liste Python (recommandé)
        route_id = crud.save_optimized_route(
            minibus_id=minibus_list[0][0],
            station_sequence=[1, 3, 5, 2],  # ✅ Liste Python
            total_distance=15.5,
            total_passengers=8
        )
        
        # Option 2: Envoyer du JSON (fonctionnera aussi)
        # route_id = crud.save_optimized_route(
        #     minibus_id=minibus_list[0][0],
        #     station_sequence=json.dumps([1, 3, 5, 2]),  # ✅ JSON
        #     total_distance=15.5,
        #     total_passengers=8
        # )
        
        # Option 3: Envoyer la chaîne originale (fonctionnera aussi)
        # route_id = crud.save_optimized_route(
        #     minibus_id=minibus_list[0][0],
        #     station_sequence="1,3,5,2",  # ✅ Chaîne
        #     total_distance=15.5,
        #     total_passengers=8
        # )
        
        if route_id:
            print(f"   ✅ Route créée: ID={route_id}")
        else:
            print("   ❌ Échec création route")
    except Exception as e:
        print(f"   ⚠️  Erreur route: {str(e)[:100]}")
    
    # Test 7: Statistiques
    print("\n7. Test statistiques...")
    stats = crud.get_database_stats()
    print(f"   ✅ Stats: {stats.get('clients_count', 0)} clients, {stats.get('users_by_role', {})}")
    
    print("\n✅ Tests terminés!")

if __name__ == "__main__":
    test_simple()