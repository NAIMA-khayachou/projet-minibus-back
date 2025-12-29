from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Bus(Base):
    __tablename__ = 'minibus'
    
    id = Column(Integer, primary_key=True, index=True)
    capacity = Column(Integer, nullable=False)
    license_plate = Column(String(20), unique=True)
    current_passengers = Column(Integer, default=0)
    status = Column(String(20), default='available')
    last_maintenance = Column(DateTime)
    
    # Relations
    #optimized_routes = relationship("OptimizedRoute", back_populates="bus")
    
    def get_available_capacity(self) -> int: #Calcule la capacité disponible du bus"""
        return self.capacity - self.current_passengers
    
    def can_accommodate(self, passengers: int) -> bool: #Vérifie si le bus peut accueillir un nombre donné de passagers"""
        return self.get_available_capacity() >= passengers
    
    def to_dict(self):
        return {
            'id': self.id,
            'capacity': self.capacity,
            'license_plate': self.license_plate,
            'current_passengers': self.current_passengers,
            'status': self.status,
            'available_capacity': self.get_available_capacity()
        }

class BusManager:
    def __init__(self, db_session):
        self.db_session = db_session
    
    def get_available_buses(self):
        return self.db_session.query(Bus).filter(
            Bus.status == 'available',
            Bus.current_passengers < Bus.capacity
        ).all()
    
    def get_buses_by_capacity(self, min_capacity: int = 0):
        return self.db_session.query(Bus).filter(
            Bus.capacity >= min_capacity,
            Bus.status == 'available'
        ).order_by(Bus.capacity.desc()).all()
    
    def assign_passengers(self, bus_id: int, passengers: int): #Assigner des passagers à un bus"""
        bus = self.db_session.query(Bus).filter(Bus.id == bus_id).first()
        if bus and bus.can_accommodate(passengers):
            bus.current_passengers += passengers
            self.db_session.commit()
            return True
        return False