from dataclasses import dataclass
import datetime

@dataclass
class Reservation:
    def __init__(self, id, client_name, pickup_station_id, dropoff_station_id, 
                 number_of_people, desired_time, status):
        self.id = id
        self.client_name = client_name
        self.pickup_station_id = pickup_station_id  # ✅ INTEGER
        self.dropoff_station_id = dropoff_station_id  # ✅ INTEGER
        self.number_of_people = number_of_people
        self.desired_time = desired_time
        self.status = status
