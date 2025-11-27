from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Dict, Any
from models.bus import Bus

Base = declarative_base()

class Reservation(Base):
    __tablename__ = 'reservations'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    pickup_station_id = Column(Integer, ForeignKey('stations.id'))
    dropoff_station_id = Column(Integer, ForeignKey('stations.id'))
    number_of_people = Column(Integer, nullable=False)
    desired_time = Column(DateTime)
    status = Column(String(20), default='pending')
    
    # Relations
    pickup_station = relationship("Station", foreign_keys=[pickup_station_id])
    dropoff_station = relationship("Station", foreign_keys=[dropoff_station_id])

class OptimizedRoute(Base):
    __tablename__ = 'optimized_routes'
    
    id = Column(Integer, primary_key=True, index=True)
    minibus_id = Column(Integer, ForeignKey('minibus.id'))
    station_sequence = Column(JSON)  
    total_distance = Column(Float)  
    total_passengers = Column(Integer)
    calculation_time = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    bus = relationship("Bus", back_populates="optimized_routes")

class RouteSolution:#Classe utilitaire pour représenter une solution de route optimisée Utilisée par l'algorithme génétique
    def __init__(self, bus: Bus, station_sequence: List[Dict], total_distance: float = 0.0):
        self.bus = bus
        self.station_sequence = station_sequence  
        self.total_distance = total_distance
        self.total_passengers = 0
        self.fitness_score = 0.0
    
    def calculate_total_passengers(self):
        self.total_passengers = sum(
            stop.get('passengers', 0) 
            for stop in self.station_sequence 
            if stop.get('action') == 'pickup'
        )
        return self.total_passengers
    
    def validate_capacity_constraints(self) -> bool:
        current_passengers = 0
        
        for stop in self.station_sequence:
            if stop['action'] == 'pickup':
                current_passengers += stop.get('passengers', 0)
            elif stop['action'] == 'dropoff':
                current_passengers -= stop.get('passengers', 0)
            
            if current_passengers > self.bus.capacity:
                return False
        
        return True
    
    def to_optimized_route(self) -> OptimizedRoute:
        return OptimizedRoute(
            minibus_id=self.bus.id,
            station_sequence=self.station_sequence,
            total_distance=self.total_distance,
            total_passengers=self.calculate_total_passengers()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'bus': self.bus.to_dict(),
            'station_sequence': self.station_sequence,
            'total_distance': self.total_distance,
            'total_passengers': self.total_passengers,
            'fitness_score': self.fitness_score
        }

class RouteManager:
    
    def __init__(self, db_session):
        self.db_session = db_session
    
    def get_pending_reservations(self):
        return self.db_session.query(Reservation).filter(
            Reservation.status == 'pending'
        ).all()
    
    def save_optimized_route(self, route_solution: RouteSolution):
        optimized_route = route_solution.to_optimized_route()
        self.db_session.add(optimized_route)
        self.db_session.commit()
        return optimized_route.id
    
    def get_recent_optimized_routes(self, limit: int = 10):
        return self.db_session.query(OptimizedRoute).order_by(
            OptimizedRoute.calculation_time.desc()
        ).limit(limit).all()