from dataclasses import dataclass
import datetime

@dataclass
class Reservation:
    id: int
    client_name: str
    pickup_station: str
    dropoff_station: str
    number_of_people: int
    desired_time: datetime.datetime
    status: str
