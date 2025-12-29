import requests
import json

BASE_URL = "http://localhost:8000/api"
AUTH_URL = "http://localhost:8000/api/login"

def run_tests():
    print("🚀 Démarrage des tests de vérification des mises à jour...")
    
    # 1. Login
    print("\n[1] Connexion en tant qu'admin...")
    response = requests.post(AUTH_URL, json={"email": "admin@test.com", "password": "admin123"})
    if response.status_code != 200:
        print(f"❌ Échec de la connexion: {response.text}")
        return
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Connexion réussie")

    # 2. Test Station Update
    print("\n[2] Test Mise à jour Station...")
    # Create temp station
    station_payload = {"name": "Test Station", "latitude": 31.0, "longitude": -7.0}
    res = requests.post(f"{BASE_URL}/stations", json=station_payload, headers=headers)
    if res.status_code == 201:
        station_id = res.json()["id"]
        print(f"✅ Station créée (ID: {station_id})")
        
        # Update station
        update_payload = {"name": "Station Updated", "latitude": 32.0, "longitude": -8.0}
        res = requests.put(f"{BASE_URL}/stations/{station_id}", json=update_payload, headers=headers)
        if res.status_code == 200 and res.json()["name"] == "Station Updated":
            print(f"✅ Station mise à jour avec succès!")
        else:
            print(f"❌ Échec de la mise à jour de la station: {res.text}")
    else:
        print(f"❌ Échec de la création de la station: {res.text}")

    # 3. Test Driver Update
    print("\n[3] Test Mise à jour Chauffeur...")
    driver_payload = {"nom": "Test", "prenom": "Driver", "email": "test@driver.com", "telephone": "1234567890", "status": "active"}
    res = requests.post(f"{BASE_URL}/drivers", json=driver_payload, headers=headers)
    if res.status_code == 201:
        driver_id = res.json()["id"]
        print(f"✅ Chauffeur créé (ID: {driver_id})")
        
        # Update driver
        update_payload = {"nom": "Updated", "prenom": "Driver", "email": "test@driver.com", "telephone": "0987654321", "status": "inactive"}
        res = requests.put(f"{BASE_URL}/drivers/{driver_id}", json=update_payload, headers=headers)
        if res.status_code == 200 and res.json()["nom"] == "Updated" and res.json()["telephone"] == "0987654321":
            print(f"✅ Chauffeur mis à jour avec succès!")
        else:
            print(f"❌ Échec de la mise à jour du chauffeur: {res.text}")
    else:
        print(f"❌ Échec de la création du chauffeur: {res.text}")

    # 4. Test Bus Update
    print("\n[4] Test Mise à jour Bus...")
    bus_payload = {"capacity": 20, "license_plate": "TEST-123", "status": "available"}
    res = requests.post(f"{BASE_URL}/minibus", json=bus_payload, headers=headers)
    if res.status_code == 201:
        bus_id = res.json()["id"]
        print(f"✅ Bus créé (ID: {bus_id})")
        
        # Update bus
        update_payload = {"capacity": 25, "license_plate": "TEST-UPDATED", "status": "maintenance"}
        res = requests.put(f"{BASE_URL}/minibus/{bus_id}", json=update_payload, headers=headers)
        if res.status_code == 200 and res.json()["license_plate"] == "TEST-UPDATED":
            print(f"✅ Bus mis à jour avec succès!")
        else:
            print(f"❌ Échec de la mise à jour du bus: {res.text}")
    else:
        print(f"❌ Échec de la création du bus: {res.text}")

if __name__ == "__main__":
    run_tests()
