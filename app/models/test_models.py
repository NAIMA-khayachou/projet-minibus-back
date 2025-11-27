import unittest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.bus import Bus, BusManager, Base as BusBase
from models.station import Station, StationManager, Base as StationBase
from models.route import Reservation, OptimizedRoute, RouteSolution, RouteManager, Base as RouteBase


class TestBusModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('sqlite:///:memory:')
        BusBase.metadata.create_all(cls.engine)
        Session = sessionmaker(bind=cls.engine)
        cls.session = Session()

    def setUp(self):
        self.session.query(Bus).delete()
        self.session.commit()

    def test_bus_creation(self):
        bus = Bus(
            capacity=20,
            license_plate='M-1234-AB',
            current_passengers=5,
            status='available'
        )
        self.session.add(bus)
        self.session.commit()

        self.assertIsNotNone(bus.id)
        self.assertEqual(bus.capacity, 20)
        self.assertEqual(bus.license_plate, 'M-1234-AB')
        self.assertEqual(bus.current_passengers, 5)

    def test_get_available_capacity(self):
        bus = Bus(capacity=20, current_passengers=5)
        self.assertEqual(bus.get_available_capacity(), 15)

    def test_can_accommodate(self):
        bus = Bus(capacity=20, current_passengers=15)
        self.assertTrue(bus.can_accommodate(5))
        self.assertFalse(bus.can_accommodate(6))

    def test_bus_to_dict(self):
        bus = Bus(
            capacity=20,
            license_plate='M-1234-AB',
            current_passengers=5,
            status='available'
        )
        bus_dict = bus.to_dict()

        self.assertEqual(bus_dict['capacity'], 20)
        self.assertEqual(bus_dict['license_plate'], 'M-1234-AB')
        self.assertEqual(bus_dict['available_capacity'], 15)

    def test_bus_manager_get_available_buses(self):
        bus1 = Bus(capacity=20, license_plate='M-1111-AA', status='available', current_passengers=5)
        bus2 = Bus(capacity=18, license_plate='M-2222-BB', status='available', current_passengers=18)
        bus3 = Bus(capacity=22, license_plate='M-3333-CC', status='maintenance', current_passengers=0)

        self.session.add_all([bus1, bus2, bus3])
        self.session.commit()

        manager = BusManager(self.session)
        available = manager.get_available_buses()

        self.assertEqual(len(available), 1)
        self.assertEqual(available[0].license_plate, 'M-1111-AA')

    def test_bus_manager_assign_passengers(self):
        bus = Bus(capacity=20, license_plate='M-4444-DD', status='available', current_passengers=10)
        self.session.add(bus)
        self.session.commit()

        manager = BusManager(self.session)

        result = manager.assign_passengers(bus.id, 5)
        self.assertTrue(result)
        self.assertEqual(bus.current_passengers, 15)

        result = manager.assign_passengers(bus.id, 10)
        self.assertFalse(result)
        self.assertEqual(bus.current_passengers, 15)

    @classmethod
    def tearDownClass(cls):
        cls.session.close()


class TestStationModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('sqlite:///:memory:')
        StationBase.metadata.create_all(cls.engine)
        Session = sessionmaker(bind=cls.engine)
        cls.session = Session()

    def setUp(self):
        self.session.query(Station).delete()
        self.session.commit()

    def test_station_creation(self):
        station = Station(
            name='Jamaâ El Fna',
            latitude=31.6258,
            longitude=-7.9891
        )
        self.session.add(station)
        self.session.commit()

        self.assertIsNotNone(station.id)
        self.assertEqual(station.name, 'Jamaâ El Fna')
        self.assertEqual(station.latitude, 31.6258)
        self.assertEqual(station.longitude, -7.9891)

    def test_distance_calculation(self):
        station1 = Station(name='Station A', latitude=31.6258, longitude=-7.9891)
        station2 = Station(name='Station B', latitude=31.6308, longitude=-8.0027)

        distance = station1.distance_to(station2)

        self.assertGreater(distance, 0)
        self.assertLess(distance, 5)

    def test_station_to_dict(self):
        station = Station(
            name='Test Station',
            latitude=31.5,
            longitude=-8.0
        )
        station_dict = station.to_dict()

        self.assertEqual(station_dict['name'], 'Test Station')
        self.assertEqual(station_dict['latitude'], 31.5)
        self.assertEqual(station_dict['longitude'], -8.0)

    def test_station_manager_load_stations(self):
        station1 = Station(name='Station 1', latitude=31.6, longitude=-7.9)
        station2 = Station(name='Station 2', latitude=31.7, longitude=-8.0)

        self.session.add_all([station1, station2])
        self.session.commit()

        manager = StationManager(self.session)
        stations = manager.load_all_stations()

        self.assertEqual(len(stations), 2)
        self.assertEqual(len(manager.stations_by_id), 2)

    def test_station_manager_get_by_id(self):
        station = Station(name='Test Station', latitude=31.6, longitude=-7.9)
        self.session.add(station)
        self.session.commit()

        manager = StationManager(self.session)
        retrieved = manager.get_station_by_id(station.id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, 'Test Station')

    @classmethod
    def tearDownClass(cls):
        cls.session.close()


class TestRouteModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('sqlite:///:memory:')
        RouteBase.metadata.create_all(cls.engine)
        StationBase.metadata.create_all(cls.engine)
        BusBase.metadata.create_all(cls.engine)
        Session = sessionmaker(bind=cls.engine)
        cls.session = Session()

    def setUp(self):
        self.session.query(Reservation).delete()
        self.session.query(OptimizedRoute).delete()
        self.session.commit()

        self.station1 = Station(name='Station A', latitude=31.6, longitude=-7.9)
        self.station2 = Station(name='Station B', latitude=31.7, longitude=-8.0)
        self.session.add_all([self.station1, self.station2])
        self.session.commit()

    def test_reservation_creation(self):
        reservation = Reservation(
            client_id=1,
            pickup_station_id=self.station1.id,
            dropoff_station_id=self.station2.id,
            number_of_people=3,
            desired_time=datetime.now(),
            status='pending'
        )
        self.session.add(reservation)
        self.session.commit()

        self.assertIsNotNone(reservation.id)
        self.assertEqual(reservation.number_of_people, 3)
        self.assertEqual(reservation.status, 'pending')

    def test_route_solution_creation(self):
        bus = Bus(capacity=20, license_plate='M-1234-AB')
        self.session.add(bus)
        self.session.commit()

        station_sequence = [
            {'station_id': 1, 'action': 'pickup', 'passengers': 3},
            {'station_id': 2, 'action': 'dropoff', 'passengers': 3}
        ]

        solution = RouteSolution(bus, station_sequence, total_distance=5.5)

        self.assertEqual(solution.bus.license_plate, 'M-1234-AB')
        self.assertEqual(solution.total_distance, 5.5)
        self.assertEqual(len(solution.station_sequence), 2)

    def test_route_solution_calculate_passengers(self):
        bus = Bus(capacity=20, license_plate='M-1234-AB')

        station_sequence = [
            {'station_id': 1, 'action': 'pickup', 'passengers': 3},
            {'station_id': 2, 'action': 'pickup', 'passengers': 2},
            {'station_id': 3, 'action': 'dropoff', 'passengers': 3}
        ]

        solution = RouteSolution(bus, station_sequence)
        total = solution.calculate_total_passengers()

        self.assertEqual(total, 5)

    def test_route_solution_validate_capacity(self):
        bus = Bus(capacity=10, license_plate='M-1234-AB')

        valid_sequence = [
            {'station_id': 1, 'action': 'pickup', 'passengers': 5},
            {'station_id': 2, 'action': 'dropoff', 'passengers': 5}
        ]
        solution1 = RouteSolution(bus, valid_sequence)
        self.assertTrue(solution1.validate_capacity_constraints())

        invalid_sequence = [
            {'station_id': 1, 'action': 'pickup', 'passengers': 8},
            {'station_id': 2, 'action': 'pickup', 'passengers': 5}
        ]
        solution2 = RouteSolution(bus, invalid_sequence)
        self.assertFalse(solution2.validate_capacity_constraints())

    def test_route_solution_to_dict(self):
        bus = Bus(capacity=20, license_plate='M-1234-AB')
        station_sequence = [{'station_id': 1, 'action': 'pickup', 'passengers': 3}]
        solution = RouteSolution(bus, station_sequence, total_distance=5.5)

        solution_dict = solution.to_dict()

        self.assertIn('bus', solution_dict)
        self.assertIn('station_sequence', solution_dict)
        self.assertEqual(solution_dict['total_distance'], 5.5)

    def test_route_manager_get_pending_reservations(self):
        res1 = Reservation(
            client_id=1,
            pickup_station_id=self.station1.id,
            dropoff_station_id=self.station2.id,
            number_of_people=3,
            status='pending'
        )
        res2 = Reservation(
            client_id=2,
            pickup_station_id=self.station1.id,
            dropoff_station_id=self.station2.id,
            number_of_people=2,
            status='confirmed'
        )

        self.session.add_all([res1, res2])
        self.session.commit()

        manager = RouteManager(self.session)
        pending = manager.get_pending_reservations()

        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].status, 'pending')

    @classmethod
    def tearDownClass(cls):
        cls.session.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
