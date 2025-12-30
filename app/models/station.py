#\app\models\station.py
from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import math

Base = declarative_base()

class Station(Base):
    __tablename__ = 'stations'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    def distance_to(self, other: 'Station') -> float: #Calcule la distance haversine entre deux stations (en km)
        R = 6371  # Rayon de la Terre en km
        lat1_rad = math.radians(self.latitude)
        lat2_rad = math.radians(other.latitude)
        delta_lat = math.radians(other.latitude - self.latitude)
        delta_lon = math.radians(other.longitude - self.longitude)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon/2) * math.sin(delta_lon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def to_dict(self): #Convertit la station en dictionnaire"""
        return {
            'id': self.id,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude
        }

class StationManager:# Gestionnaire des stations pour préparer les données d'optimisation
    
    def __init__(self, db_session):
        self.db_session = db_session
        self.stations = []
        self.stations_by_id = {}
    
    def load_all_stations(self):#Charge toutes les stations depuis la base de données"""
        stations = self.db_session.query(Station).all()
        self.stations = stations
        self.stations_by_id = {station.id: station for station in stations}
        return stations
    
    def get_station_by_id(self, station_id: int) -> Station: #Récupère une station par son ID"""
        return self.db_session.query(Station).filter(Station.id == station_id).first()
    
    def create_station_map(self, reservations_data):#Prépare les données des stations pour la visualisation sur une carte"""
        pickup_stations = []
        dropoff_stations = []
        station_pairs = [] 
        
        for reservation in reservations_data:
            pickup_station = self.get_station_by_id(reservation.pickup_station_id)
            dropoff_station = self.get_station_by_id(reservation.dropoff_station_id)
            
            if pickup_station and dropoff_station:
                pickup_station_copy = type('TempStation', (), {
                    'id': pickup_station.id,
                    'name': pickup_station.name,
                    'latitude': pickup_station.latitude,
                    'longitude': pickup_station.longitude,
                    'passengers_count': reservation.number_of_people,
                    'reservation_id': reservation.id
                })
                
                dropoff_station_copy = type('TempStation', (), {
                    'id': dropoff_station.id,
                    'name': dropoff_station.name,
                    'latitude': dropoff_station.latitude,
                    'longitude': dropoff_station.longitude,
                    'passengers_count': reservation.number_of_people,
                    'reservation_id': reservation.id
                })
                
                pickup_stations.append(pickup_station_copy)
                dropoff_stations.append(dropoff_station_copy)
                station_pairs.append((pickup_station_copy, dropoff_station_copy))
        
        return pickup_stations, dropoff_stations, station_pairs