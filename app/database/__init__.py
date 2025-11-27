# database/__init__.py
"""
Module de base de données pour le système d'optimisation des transports Marrakech
"""

from .connection import db, DatabaseConnection
from .crud import (
    get_all_stations,
    get_station_by_id,
    get_all_minibus,
    get_available_minibus,
    get_all_clients,
    create_client,
    get_all_reservations,
    create_reservation,
    get_pending_reservations,
    save_optimized_route,
    get_optimized_routes,
    get_database_stats
)
from .init_database import init_database

__version__ = "1.0.0"

__all__ = [
    'db',
    'DatabaseConnection',
    'init_database',
    'get_all_stations',
    'get_station_by_id', 
    'get_all_minibus',
    'get_available_minibus',
    'get_all_clients',
    'create_client',
    'get_all_reservations',
    'create_reservation',
    'get_pending_reservations',
    'save_optimized_route',
    'get_optimized_routes',
    'get_database_stats'
]

print(f" Module database {__version__} chargé - Prêt pour l'optimisation")