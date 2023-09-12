import psycopg2
from decouple import config


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
            print("Connected")
        except psycopg2.Error as e:
            print("Error connecting:  ", e)

    def execute_query(self, q: str):
        try:
            self.cursor.execute(q)
            return self.cursor.fetchall()
        except psycopg2.Error as e:
            print("Error during query execution: ", e)
            return None

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Connection closed")


if __name__ == "__main__":
    db = Database()
    db.connect()

    query = "SELECT * FROM prova"
    results = db.execute_query(query)

    if results:
        for row in results:
            print(row)

    db.close()

