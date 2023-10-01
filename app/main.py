from services.database import Database
from services.web_scraper import WebScraper


def scrape_and_write_flights(origin: str, destination: str, date: str, budget: int, stops: int):
    db = Database()
    flights = WebScraper(
        departure_station=origin,
        arrival_station=destination,
        when=date,
        budget=budget,
        stops=stops
    ).round_trip()

    db.insert_flights(flights)
    return flights


