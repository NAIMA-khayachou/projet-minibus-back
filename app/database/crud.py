# database/crud.py
from ..models.bus import Bus
from ..models.route import Reservation
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
    except Exception as e:
        logger.error(f" Erreur get_station_by_id: {e}")
        return None

def create_station(name, latitude, longitude):
    """Crée une nouvelle station"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO stations (name, latitude, longitude) 
            VALUES (%s, %s, %s) RETURNING id;
        """, (name, latitude, longitude))
        station_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Station créée avec ID: {station_id}")
        return station_id
    except Exception as e:
        logger.error(f" Erreur create_station: {e}")
        return None

def update_station(station_id, name, latitude, longitude):
    """Met à jour une station existante"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE stations 
            SET name = %s, latitude = %s, longitude = %s 
            WHERE id = %s;
        """, (name, latitude, longitude, station_id))
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Station {station_id} mise à jour")
        return True
    except Exception as e:
        logger.error(f" Erreur update_station: {e}")
        return False

def delete_station(station_id):
    """Supprime une station"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM stations WHERE id = %s;", (station_id,))
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Station {station_id} supprimée")
        return True
    except Exception as e:
        logger.error(f" Erreur delete_station: {e}")
        return False

# ==================== MINIBUS ====================

def get_all_minibus():
    try: 
        conn = db.get_connection() 
        cursor = conn.cursor() 
        cursor.execute("""
            SELECT id, capacity, license_plate, current_passengers, status, last_maintenance
            FROM minibus ORDER BY id;
        """) 
        rows = cursor.fetchall() 
        cursor.close() 
        db.release_connection(conn) 

        minibus_list = []
        for row in rows:
            bus = Bus()
            bus.id = row[0]
            bus.capacity = row[1]
            bus.license_plate = row[2]
            bus.current_passengers = row[3]
            bus.status = row[4]
            bus.last_maintenance = row[5]
            minibus_list.append(bus)

        logger.info(f"Récupéré {len(minibus_list)} minibus")
        return minibus_list
    except Exception as e: 
        logger.error(f"Erreur get_all_minibus: {e}")
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

def create_minibus(capacity, license_plate):
    """Crée un nouveau minibus"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO minibus (capacity, license_plate, current_passengers, status, last_maintenance, created_at) 
            VALUES (%s, %s, 0, 'available', CURRENT_DATE, CURRENT_TIMESTAMP) RETURNING id;
        """, (capacity, license_plate))
        minibus_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Minibus créé avec ID: {minibus_id}")
        return minibus_id
    except Exception as e:
        logger.error(f" Erreur create_minibus: {e}")
        return None

def update_minibus(minibus_id, capacity, license_plate, status='available'):
    """Met à jour un minibus existant"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE minibus 
            SET capacity = %s, license_plate = %s, status = %s 
            WHERE id = %s;
        """, (capacity, license_plate, status, minibus_id))
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Minibus {minibus_id} mis à jour")
        return True
    except Exception as e:
        logger.error(f" Erreur update_minibus: {e}")
        return False

def delete_minibus(minibus_id):
    """Supprime un minibus"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM minibus WHERE id = %s;", (minibus_id,))
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Minibus {minibus_id} supprimé")
        return True
    except Exception as e:
        logger.error(f" Erreur delete_minibus: {e}")
        return False

# ==================== CLIENTS ====================
def get_all_clients():
    """Récupère tous les clients"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, first_name, last_name, email, phone, status FROM clients ORDER BY id;")
        clients = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        return clients
    except Exception as e:
        logger.error(f" Erreur get_all_clients: {e}")
        return []

def create_client(first_name, last_name, email=None, phone=None, status='active'):
    """Crée un nouveau client"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clients (first_name, last_name, email, phone, status) 
            VALUES (%s, %s, %s, %s, %s) RETURNING id;
        """, (first_name, last_name, email, phone, status))
        client_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Client créé avec ID: {client_id}")
        return client_id
    except Exception as e:
        logger.error(f" Erreur create_client: {e}")
        return None

def update_client(client_id, first_name, last_name, email=None, phone=None, status='active'):
    """Met à jour un client existant"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE clients 
            SET first_name = %s, last_name = %s, email = %s, phone = %s, status = %s 
            WHERE id = %s;
        """, (first_name, last_name, email, phone, status, client_id))
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Client {client_id} mis à jour")
        return True
    except Exception as e:
        logger.error(f" Erreur update_client: {e}")
        return False

def delete_client(client_id):
    """Supprime un client"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clients WHERE id = %s;", (client_id,))
        conn.commit()
        cursor.close()
        db.release_connection(conn)
        logger.info(f" Client {client_id} supprimé")
        return True
    except Exception as e:
        logger.error(f" Erreur delete_client: {e}")
        return False


# ==================== RÉSERVATIONS ====================


def get_all_reservations():
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                r.id, 
                c.first_name || ' ' || c.last_name as client_name,
                r.pickup_station_id,
                r.dropoff_station_id,
                r.number_of_people,
                CURRENT_DATE + r.desired_time as desired_time,  -- ✅ Convertir TIME en DATETIME
                r.status
            FROM reservations r
            JOIN clients c ON r.client_id = c.id
            ORDER BY r.desired_time;
        """)
        rows = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        
        return [Reservation(*row) for row in rows]
    except Exception as e:
        logger.error(f"❌ Erreur get_all_reservations: {e}")
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
                c.first_name || ' ' || c.last_name as client_name, 
                r.pickup_station_id,
                r.dropoff_station_id,
                r.number_of_people,
                r.desired_time,
                'pending' as status  
            FROM reservations r
            JOIN clients c ON r.client_id = c.id  
            WHERE r.status = 'pending'
            ORDER BY r.desired_time;
        """)
        rows = cursor.fetchall()
        cursor.close()
        db.release_connection(conn)
        
        return [Reservation(*row) for row in rows]  
    except Exception as e:
        logger.error(f"❌ Erreur get_pending_reservations: {e}")
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
  # ==================== HELPER FUNCTIONS ====================
def get_stations_dict():
    """
    ✅ NOUVELLE FONCTION HELPER
    Retourne les stations sous forme de dictionnaire {id: {name, lat, lon}}
    """
    try:
        stations = get_all_stations()
        return {
            station_id: {
                "name": name,
                "latitude": lat,
                "longitude": lon
            }
            for station_id, name, lat, lon in stations
        }
    except Exception as e:
        logger.error(f"❌ Erreur get_stations_dict: {e}")
        return {}

# ==================== USERS ====================
def get_user_by_email(email):
    """Récupère un utilisateur par son email"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, password, role, nom, prenom 
            FROM users 
            WHERE email = %s;
        """, (email,))
        user = cursor.fetchone()
        cursor.close()
        db.release_connection(conn)
        
        if user:
            return {
                "id": user[0],
                "email": user[1],
                "password": user[2],
                "role": user[3],
                "nom": user[4],
                "prenom": user[5]
            }
        return None
    except Exception as e:
        logger.error(f"❌ Erreur get_user_by_email: {e}")
        return None

def create_user(email, password, role, nom, prenom):
    """Crée un nouvel utilisateur (chauffeur ou admin)"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (email, password, role, nom, prenom)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """, (email, password, role, nom, prenom))
        user_id = cursor.fetchone()[0]
        conn.commit()
        return user_id
    except Exception as e:
        logger.error(f"❌ Erreur create_user: {e}")
        return None
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): db.release_connection(conn)

def update_user(user_id, email, role, nom, prenom):
    """Met à jour un utilisateur"""
    conn = None
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET email = %s, role = %s, nom = %s, prenom = %s
            WHERE id = %s;
        """, (email, role, nom, prenom, user_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Erreur update_user: {e}")
        return False
    finally:
        if conn:
            db.release_connection(conn)

def delete_user(user_id):
    """Supprime un utilisateur"""
    conn = None
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s;", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"❌ Erreur delete_user: {e}")
        return False
    finally:
        if conn:
            db.release_connection(conn)


def get_users_by_role(role):
    """Récupère tous les utilisateurs ayant un rôle spécifique"""
    conn = None
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, password, role, nom, prenom 
            FROM users 
            WHERE role = %s;
        """, (role,))
        users = cursor.fetchall()
        cursor.close()
        return users
    except Exception as e:
        logger.error(f"❌ Erreur get_users_by_role: {e}")
        return []
    finally:
        if conn:
            db.release_connection(conn)

            