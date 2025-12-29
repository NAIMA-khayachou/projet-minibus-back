import requests
import time

AUTH_URL = "http://localhost:8000/api/login"
CREDENTIALS = {"email": "admin@test.com", "password": "admin123"}

def test_login_speed():
    print("🚀 Test de la vitesse de connexion...")
    
    start_time = time.time()
    try:
        response = requests.post(AUTH_URL, json=CREDENTIALS)
        end_time = time.time()
        
        duration = end_time - start_time
        
        if response.status_code == 200:
            print(f"✅ Connexion réussie en {duration:.4f} secondes")
            print(f"   Status Code: {response.status_code}")
        else:
            print(f"❌ Échec de la connexion (Status: {response.status_code})")
            print(f"   Durée: {duration:.4f} secondes")
            print(f"   Réponse: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la requête: {e}")

if __name__ == "__main__":
    test_login_speed()
