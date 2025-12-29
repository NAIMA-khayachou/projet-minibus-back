
-- =============================================
-- SYSTÈME DE TRANSPORT MINIBUS - MARRAKECH
-- Création de la base de données complète
-- =============================================

-- 1. TABLE DES STATIONS
CREATE TABLE stations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL
);

-- 2. TABLE DES MINIBUS
CREATE TABLE minibus (
    id SERIAL PRIMARY KEY,
    capacity INT NOT NULL CHECK (capacity BETWEEN 10 AND 30),
    license_plate VARCHAR(20) UNIQUE,
    current_passengers INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'available',
    last_maintenance DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. TABLE DES UTILISATEURS
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    nom VARCHAR(50),
    prenom VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. TABLE DES CLIENTS
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. TABLE DES RÉSERVATIONS
CREATE TABLE reservations (
    id SERIAL PRIMARY KEY,
    client_id INT REFERENCES clients(id) ON DELETE CASCADE,
    pickup_station_id INT REFERENCES stations(id) ON DELETE CASCADE,
    dropoff_station_id INT REFERENCES stations(id) ON DELETE CASCADE,
    number_of_people INT NOT NULL CHECK (number_of_people > 0),
    desired_time TIME,
    status VARCHAR(20) DEFAULT 'pending'
);

-- 6. TABLE DES SOLUTIONS OPTIMALES
CREATE TABLE optimized_routes (
    id SERIAL PRIMARY KEY,
    minibus_id INT REFERENCES minibus(id),
    station_sequence JSONB,
    total_distance DECIMAL(10,2),
    total_passengers INT,
    calculation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- INSERTION DES DONNÉES DE TEST
-- =============================================

-- Stations de Marrakech
INSERT INTO stations (name, latitude, longitude) VALUES
('Jamaâ El Fna', 31.6258, -7.9891),
('Gare Marrakech', 31.6308, -8.0027),
('Ménara', 31.6111, -8.0292),
('Gueliz', 31.6364, -8.0103),
('Palmeraie', 31.6708, -7.9736),
('Médina', 31.6250, -7.9914),
('Aéroport Marrakech', 31.6069, -8.0363),
('Université Cadi Ayyad', 31.6417, -8.0089);

-- Minibus
INSERT INTO minibus (capacity, license_plate, last_maintenance) VALUES
(20, 'M-1234-AB', '2024-11-01'),
(18, 'M-5678-CD', '2024-10-15'),
(22, 'M-9012-EF', '2024-11-10'),
(16, 'M-3456-GH', '2024-10-25'),
(20, 'M-7890-IJ', '2024-11-05');

-- Clients
INSERT INTO clients (first_name, last_name, email, phone) VALUES
('Ahmed', 'Alaoui', 'ahmed.alaoui@email.com', '+212-600-123456'),
('Fatima', 'Benali', 'fatima.benali@email.com', '+212-600-234567'),
('Mehdi', 'Chraibi', 'mehdi.chraibi@email.com', '+212-600-345678'),
('Khadija', 'Mansouri', 'khadija.mansouri@email.com', '+212-600-456789'),
('Youssef', 'El Fassi', 'youssef.elfassi@email.com', '+212-600-567890'),
('Nadia', 'Saidi', 'nadia.saidi@email.com', '+212-600-678901');

-- Réservations
INSERT INTO reservations (client_id, pickup_station_id, dropoff_station_id, number_of_people, desired_time) VALUES
(1, 1, 7, 3, '08:00:00'),
(2, 2, 7, 2, '08:30:00'),
(3, 8, 4, 4, '09:00:00'),
(4, 8, 1, 2, '09:15:00'),
(5, 4, 2, 1, '17:00:00'),
(6, 3, 5, 2, '17:30:00');

-- =============================================
-- VÉRIFICATION DES DONNÉES
-- =============================================

-- Compte le nombre d'entrées dans chaque table
SELECT 'stations' as table_name, COUNT(*) as count FROM stations
UNION ALL
SELECT 'minibus', COUNT(*) FROM minibus
UNION ALL
SELECT 'clients', COUNT(*) FROM clients
UNION ALL
SELECT 'reservations', COUNT(*) FROM reservations;

-- Affiche les réservations avec les noms des stations
SELECT 
    c.first_name,
    c.last_name,
    s1.name as departure_station,
    s2.name as arrival_station,
    r.number_of_people,
    r.desired_time
FROM reservations r
JOIN clients c ON r.client_id = c.id
JOIN stations s1 ON r.pickup_station_id = s1.id
JOIN stations s2 ON r.dropoff_station_id = s2.id;