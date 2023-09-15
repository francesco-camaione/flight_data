import psycopg2
from decouple import config
from typing import List, Tuple
from model.db_tables import OneWayFlights
from model.flight import Flight
from services.web_scraper import WebScraper


class Database:
    def __init__(self):
        self.dbname = "find_data"
        self.user = "postgres"
        self.password = config('DB_PW')
        self.host = "localhost"
        self.port = "5432"
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            self.cursor = self.conn.cursor()
            print("Connected to db")
        except psycopg2.Error as e:
            print("Error connecting:  ", e)

    def execute_query(self, q):
        self.connect()
        try:
            # use parameretized queries
            self.cursor.execute(q)
            return self.cursor.fetchall()
        except psycopg2.Error as e:
            print("Error during query execution: ", e)
            return None

    def execute_parameretized_query(self, q: str, parameters):
        self.connect()
        try:
            # use parameretized queries
            self.cursor.execute(q, parameters)
            self.conn.commit()
            return
        except psycopg2.Error as e:
            print("Error during query execution: ", e)
            return None

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Connection closed")

    def select_one_way_flights(self):
        q = "SELECT * FROM OneWayFlights;"
        res: List[Tuple[OneWayFlights]] = self.execute_query(q)
        self.close()
        return res

    def insert_one_way_flights(self, flights_data: List[Flight]):
        if flights_data is not None:
            for flight in flights_data:
                print(flight)
                q = "INSERT INTO OneWayFlights (flightid, departure_station, arrival_station, departure_time, "\
                    "arrival_time, duration_time, price, direct_flight, date) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s,"\
                    " %s) ON CONFLICT (flightid) DO NOTHING;"
                parameters = (
                    flight.flight_id,
                    flight.departure_station,
                    flight.arrival_station,
                    flight.departure_time,
                    flight.arrival_time,
                    flight.duration_time,
                    flight.price,
                    flight.direct_flight,
                    flight.when
                )
                self.execute_parameretized_query(q, parameters)

#
# if __name__ == "__main__":
#     db = Database()
#     # scrape and add data to db
#     flights = WebScraper(
#         "ROM",
#         "LIS",
#         "2024-03-01",
#         100,
#         0
#     ).one_way_flights()
#
#     db.insert_one_way_flights(flights)
#     print(db.get_one_way_flights())
