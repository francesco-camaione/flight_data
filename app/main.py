from services.database import Database
from services.web_scraper import WebScraper

if __name__ == "__main__":
    db = Database()
    flights = WebScraper(
        "AMS",
        "ROM",
        "2023-12-22",
        300,
        0
    ).round_trip()

    db.insert_one_way_flights(flights)
