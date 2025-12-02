from dataclasses import dataclass
import datetime

@dataclass
class Minibus:
    id: int
    capacity: int
    license_plate: str
    current_passengers: int
    status: str
    last_maintenance: datetime.date
