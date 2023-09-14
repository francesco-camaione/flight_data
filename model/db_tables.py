from dataclasses import dataclass
from datetime import datetime


@dataclass
class OneWayFlights:
    FlightID: str
    departure_station: str
    arrival_station: str
    departure_time: datetime
    arrival_time: datetime
    duration_time: str
    price: int
    direct_flight: bool
    when: datetime
