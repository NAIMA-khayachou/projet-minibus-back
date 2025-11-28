# database/crud.py
from .connection import db
import logging

logger = logging.getLogger(__name__)

# ==================== STATIONS ====================
def get_all_stations():
    """Récupère toutes les stations"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, latitude, longitude FROM stations ORDER BY id;")
        stations = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Récupéré {len(stations)} stations")
        return stations
    except Exception as e:
        logger.error(f" Erreur get_all_stations: {e}")
        return []

def get_station_by_id(station_id):
    """Récupère une station par son ID"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, latitude, longitude FROM stations WHERE id = %s;", (station_id,))
        station = cursor.fetchone()
        cursor.close()
        db.release_connection(conn)
        return station
    except Exception as e:
        logger.error(f" Erreur get_station_by_id: {e}")
        return None

# ==================== MINIBUS ====================
def get_all_minibus():
    """Récupère tous les minibus"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, capacity, license_plate, current_passengers, status, 
                   last_maintenance, limite_distance, limite_duree 
            FROM minibus ORDER BY id;
        """)
        minibus = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Récupéré {len(minibus)} minibus")
        return minibus
    except Exception as e:
        logger.error(f" Erreur get_all_minibus: {e}")
        return []

def get_available_minibus():
    """Récupère les minibus disponibles"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, capacity, license_plate, current_passengers 
            FROM minibus 
            WHERE status = 'available' AND current_passengers < capacity
            ORDER BY capacity DESC;
        """)
        available_minibus = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        return available_minibus
    except Exception as e:
        logger.error(f" Erreur get_available_minibus: {e}")
        return []

# ==================== CLIENTS ====================
def get_all_clients():
    """Récupère tous les clients"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, first_name, last_name, email, phone FROM clients ORDER BY id;")
        clients = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        return clients
    except Exception as e:
        logger.error(f" Erreur get_all_clients: {e}")
        return []

def create_client(first_name, last_name, email=None, phone=None):
    """Crée un nouveau client"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clients (first_name, last_name, email, phone) 
            VALUES (%s, %s, %s, %s) RETURNING id;
        """, (first_name, last_name, email, phone))
        client_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Client créé avec ID: {client_id}")
        return client_id
    except Exception as e:
        logger.error(f" Erreur create_client: {e}")
        return None

# ==================== RÉSERVATIONS ====================
def get_all_reservations():
    """Récupère toutes les réservations avec détails"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                r.id, 
                c.first_name || ' ' || c.last_name as client_name,
                s1.name as pickup_station, 
                s2.name as dropoff_station,
                r.number_of_people,
                r.desired_time,
                r.status
            FROM reservations r
            JOIN clients c ON r.client_id = c.id
            JOIN stations s1 ON r.pickup_station_id = s1.id
            JOIN stations s2 ON r.dropoff_station_id = s2.id
            ORDER BY r.desired_time;
        """)
        reservations = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Récupéré {len(reservations)} réservations")
        return reservations
    except Exception as e:
        logger.error(f" Erreur get_all_reservations: {e}")
        return []

def create_reservation(client_id, pickup_station_id, dropoff_station_id, number_of_people, desired_time):
    """Crée une nouvelle réservation"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reservations 
            (client_id, pickup_station_id, dropoff_station_id, number_of_people, desired_time) 
            VALUES (%s, %s, %s, %s, %s) RETURNING id;
        """, (client_id, pickup_station_id, dropoff_station_id, number_of_people, desired_time))
        reservation_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Réservation créée avec ID: {reservation_id}")
        return reservation_id
    except Exception as e:
        logger.error(f" Erreur create_reservation: {e}")
        return None

def get_pending_reservations():
    """Récupère les réservations en attente pour l'optimisation"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                r.id,
                r.client_id,
                r.pickup_station_id,
                r.dropoff_station_id,
                r.number_of_people,
                r.desired_time
            FROM reservations r
            WHERE r.status = 'pending'
            ORDER BY r.desired_time;
        """)
        pending_reservations = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        return pending_reservations
    except Exception as e:
        logger.error(f" Erreur get_pending_reservations: {e}")
        return []

def get_all_reservations_for_algo():
    """Récupère toutes les réservations avec coordonnées des stations pour l'algorithme"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                r.id,
                r.client_id,
                r.pickup_station_id,
                r.dropoff_station_id,
                r.number_of_people,
                r.desired_time,
                s1.latitude as pickup_lat,
                s1.longitude as pickup_lon,
                s2.latitude as dropoff_lat,
                s2.longitude as dropoff_lon
            FROM reservations r
            JOIN stations s1 ON r.pickup_station_id = s1.id
            JOIN stations s2 ON r.dropoff_station_id = s2.id
            WHERE r.status = 'pending'
            ORDER BY r.desired_time;
        """)
        reservations = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Récupéré {len(reservations)} réservations pour algo")
        return reservations
    except Exception as e:
        logger.error(f" Erreur get_all_reservations_for_algo: {e}")
        return []
# ==================== OPTIMIZED ROUTES ====================
def save_optimized_route(minibus_id, station_sequence, total_distance, total_passengers):
    """Sauvegarde une route optimisée trouvée par l'algorithme"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO optimized_routes 
            (minibus_id, station_sequence, total_distance, total_passengers) 
            VALUES (%s, %s, %s, %s) RETURNING id;
        """, (minibus_id, station_sequence, total_distance, total_passengers))
        route_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Route optimisée sauvegardée avec ID: {route_id}")
        return route_id
    except Exception as e:
        logger.error(f" Erreur save_optimized_route: {e}")
        return None

def get_optimized_routes():
    """Récupère toutes les routes optimisées"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                or.id,
                m.license_plate,
                or.station_sequence,
                or.total_distance,
                or.total_passengers,
                or.calculation_time
            FROM optimized_routes or
            JOIN minibus m ON or.minibus_id = m.id
            ORDER BY or.calculation_time DESC;
        """)
        routes = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        return routes
    except Exception as e:
        logger.error(f" Erreur get_optimized_routes: {e}")
        return []

# ==================== STATISTIQUES ====================
def get_database_stats():
    """Récupère les statistiques de la base"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Nombre de stations
        cursor.execute("SELECT COUNT(*) FROM stations;")
        stats['stations_count'] = cursor.fetchone()[0]
        
        # Nombre de minibus
        cursor.execute("SELECT COUNT(*) FROM minibus;")
        stats['minibus_count'] = cursor.fetchone()[0]
        
        # Nombre de clients
        cursor.execute("SELECT COUNT(*) FROM clients;")
        stats['clients_count'] = cursor.fetchone()[0]
        
        # Nombre de réservations par statut
        cursor.execute("SELECT status, COUNT(*) FROM reservations GROUP BY status;")
        stats['reservations_by_status'] = dict(cursor.fetchall())
        
        cursor.close()
        db.release_connection(conn)
        
        logger.info(" Statistiques récupérées")
        return stats
    except Exception as e:
        logger.error(f" Erreur get_database_stats: {e}")
        return {}