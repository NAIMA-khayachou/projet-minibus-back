import joblib
import os
import pandas as pd
import math
from datetime import datetime
from app.database.connection import db

class AIService:
    def __init__(self):
        """Initialize the AI service and load the trained model."""
        self.model_path = os.path.join(
            os.path.dirname(__file__), 
            "..", "..", "..", 
            "eta_model.pkl"
        )
        self.model = None
        self.stations_cache = {}  # Cache pour éviter de requêter la DB à chaque fois
        self._load_model()
        self._load_stations()
    
    def _load_model(self):
        """Load the Random Forest model from disk."""
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file not found at {self.model_path}")
            
            self.model = joblib.load(self.model_path)
            print(f"✓ Random Forest model loaded successfully")
        except FileNotFoundError as e:
            print(f"✗ Model file not found: {e}")
            raise
        except Exception as e:
            print(f"✗ Error loading model: {e}")
            raise
    
    def _load_stations(self):
        """Load all stations from database into cache."""
        conn = None
        cursor = None
        try:
            # Obtenir une connexion du pool
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Exécuter la requête
            query = "SELECT id, name, latitude, longitude FROM stations"
            cursor.execute(query)
            
            # Récupérer tous les résultats
            rows = cursor.fetchall()
            
            # Remplir le cache (psycopg2 retourne des tuples)
            for row in rows:
                station_id, name, latitude, longitude = row
                self.stations_cache[station_id] = {
                    'name': name,
                    'latitude': latitude,
                    'longitude': longitude
                }
            
            print(f"✓ Loaded {len(self.stations_cache)} stations into cache")
            
        except Exception as e:
            print(f"✗ Error loading stations: {e}")
            raise
        finally:
            # Toujours fermer le curseur et libérer la connexion
            if cursor:
                cursor.close()
            if conn:
                db.release_connection(conn)
    
    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate distance between two GPS coordinates using Haversine formula.
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
        
        Returns:
            Distance in kilometers
        """
        R = 6371  # Rayon de la Terre en km
        
        # Conversion en radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Formule de Haversine
        a = math.sin(delta_lat / 2)**2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * \
            math.sin(delta_lon / 2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _get_station_coords(self, station_id):
        """
        Get coordinates for a station from cache.
        
        Args:
            station_id: Station ID
        
        Returns:
            tuple: (latitude, longitude)
        """
        if station_id not in self.stations_cache:
            raise ValueError(f"Station ID {station_id} not found in database")
        
        station = self.stations_cache[station_id]
        return station['latitude'], station['longitude']
    
    def _prepare_features(self, from_station_id, to_station_id, passenger_count, 
                         departure_time=None):
        """
        Prepare features in the EXACT order expected by the Random Forest model.
        
        Expected order: from_station_id, to_station_id, hour_of_day, day_of_week, 
                       passenger_count, distance_km, is_night
        
        Args:
            from_station_id: Departure station ID
            to_station_id: Arrival station ID
            passenger_count: Number of passengers
            departure_time: datetime object (if None, uses current time)
        
        Returns:
            pandas DataFrame with features in correct order
        """
        # Use current time if not provided
        if departure_time is None:
            departure_time = datetime.now()
        
        # Extract temporal features
        hour_of_day = departure_time.hour
        day_of_week = departure_time.weekday()  # 0=Lundi, 6=Dimanche
        
        # Determine if it's night time (22h-6h)
        is_night = 1 if (hour_of_day >= 22 or hour_of_day < 6) else 0
        
        # Calculate distance
        lat1, lon1 = self._get_station_coords(from_station_id)
        lat2, lon2 = self._get_station_coords(to_station_id)
        distance_km = self._haversine_distance(lat1, lon1, lat2, lon2)
        
        # Create DataFrame with EXACT column order
        features = pd.DataFrame({
            'from_station_id': [from_station_id],
            'to_station_id': [to_station_id],
            'hour_of_day': [hour_of_day],
            'day_of_week': [day_of_week],
            'passenger_count': [passenger_count],
            'distance_km': [distance_km],
            'is_night': [is_night]
        })
        
        return features
    
    def predict_eta(self, from_station_id, to_station_id, passenger_count, 
                    departure_time=None):
        """
        Predict ETA for a tramway journey.
        
        Args:
            from_station_id: Departure station ID (1-12 for Marrakech)
            to_station_id: Arrival station ID (1-12 for Marrakech)
            passenger_count: Number of passengers
            departure_time: datetime object (optional, uses current time if None)
        
        Returns:
            dict: {
                'eta_minutes': float,
                'distance_km': float,
                'is_night': bool,
                'from_station': str,
                'to_station': str
            }
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Cannot make predictions.")
        
        try:
            # Prepare features
            features_df = self._prepare_features(
                from_station_id, 
                to_station_id, 
                passenger_count,
                departure_time
            )
            
            # Make prediction
            eta_minutes = self.model.predict(features_df)[0]
            
            # Get station names for response
            from_station_name = self.stations_cache[from_station_id]['name']
            to_station_name = self.stations_cache[to_station_id]['name']
            
            return {
                'eta_minutes': round(eta_minutes, 2),
                'distance_km': round(features_df['distance_km'].values[0], 2),
                'is_night': bool(features_df['is_night'].values[0]),
                'from_station': from_station_name,
                'to_station': to_station_name,
                'hour_of_day': features_df['hour_of_day'].values[0],
                'day_of_week': features_df['day_of_week'].values[0]
            }
        
        except ValueError as e:
            print(f"Validation error: {e}")
            raise
        except Exception as e:
            print(f"Error during prediction: {e}")
            raise
    
    def predict_batch(self, journeys):
        """
        Predict ETA for multiple journeys.
        
        Args:
            journeys: list of dicts with keys: 
                     'from_station_id', 'to_station_id', 'passenger_count', 'departure_time'
        
        Returns:
            list of prediction dicts
        """
        predictions = []
        
        for journey in journeys:
            try:
                prediction = self.predict_eta(
                    journey['from_station_id'],
                    journey['to_station_id'],
                    journey['passenger_count'],
                    journey.get('departure_time')  # Optional
                )
                predictions.append(prediction)
            except Exception as e:
                predictions.append({
                    'error': str(e),
                    'from_station_id': journey['from_station_id'],
                    'to_station_id': journey['to_station_id']
                })
        
        return predictions
    
    def reload_stations(self):
        """Reload stations from database (useful if stations are updated)."""
        self.stations_cache.clear()
        self._load_stations()
    
    def get_station_info(self, station_id):
        """Get information about a specific station."""
        if station_id not in self.stations_cache:
            return None
        return self.stations_cache[station_id]
    
    def get_all_stations(self):
        """Get all stations information."""
        return self.stations_cache


# Example usage for testing:
if __name__ == "__main__":
    # Initialize service
    ai_service = AIService()
    
    # Example 1: Simple prediction (current time)
    print("\n=== Test 1: Prediction avec l'heure actuelle ===")
    try:
        result = ai_service.predict_eta(
            from_station_id=1,
            to_station_id=5,
            passenger_count=25
        )
        print(f"ETA: {result['eta_minutes']} minutes")
        print(f"Distance: {result['distance_km']} km")
        print(f"Trajet: {result['from_station']} → {result['to_station']}")
        print(f"Période nocturne: {result['is_night']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Prediction with specific time (night)
    print("\n=== Test 2: Prediction en période nocturne ===")
    try:
        night_time = datetime(2025, 1, 15, 23, 30)  # 23h30
        result = ai_service.predict_eta(
            from_station_id=3,
            to_station_id=8,
            passenger_count=10,
            departure_time=night_time
        )
        print(f"ETA: {result['eta_minutes']} minutes")
        print(f"Période nocturne: {result['is_night']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 3: Batch prediction
    print("\n=== Test 3: Batch prediction ===")
    journeys = [
        {'from_station_id': 1, 'to_station_id': 5, 'passenger_count': 30},
        {'from_station_id': 2, 'to_station_id': 7, 'passenger_count': 15},
        {'from_station_id': 4, 'to_station_id': 9, 'passenger_count': 20}
    ]
    
    results = ai_service.predict_batch(journeys)
    for i, result in enumerate(results, 1):
        if 'error' not in result:
            print(f"Trajet {i}: {result['eta_minutes']} min ({result['from_station']} → {result['to_station']})")
        else:
            print(f"Trajet {i}: Error - {result['error']}")