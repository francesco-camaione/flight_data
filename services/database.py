import psycopg2
from decouple import config
from typing import List, Tuple
from model.flight import Flight


class Database:
    def __init__(self):
        self.dbname = config('DB_NAME')
        self.user = config("USER")
        self.password = config('DB_PW')
        self.host = "localhost"
        self.port = config('PORT')
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

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Connection closed")

    def execute_query(self, q):
        self.connect()
        try:
            # use parameretized queries
            self.cursor.execute(q)
            self.close()
            return self.cursor.fetchall()
        except psycopg2.Error as e:
            print("Error during query execution: ", e)
            self.close()
            return None

    def execute_parameretized_query(self, q: str, parameters):
        self.connect()
        try:
            # use parameretized queries
            self.cursor.execute(q, parameters)
            self.conn.commit()
            self.close()
            return
        except psycopg2.Error as e:
            print("Error during query execution: ", e)
            self.close()
            return None

    def select_one_way_flights(self):
        q = "SELECT * FROM OneWayFlights;"
        res: List[Tuple[Flight]] = self.execute_query(q)
        return res

    def insert_flights(self, flights_data: List[Flight]):
        if flights_data is not None:
            for flight in flights_data:
                print(flight)
                q = "INSERT INTO OneWayFlights (flightid, departure_station, arrival_station, departure_time, "\
                    "arrival_time, duration_time, price, stops, date) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s,"\
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

