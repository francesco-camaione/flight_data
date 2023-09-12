from dataclasses import dataclass


@dataclass
class Flight:
    url: str
    departure_station: str
    arrival_station: str
    departure_time: str
    arrival_time: str
    duration_time: str
    price: int
    direct_flight: bool
