import datetime

import mysql.connector

db_config = {
    "host": "43.202.228.198",
    "port": 3306,
    "database": "goat",
    "user": "root",
    "password": "tkrhk0123!!",
}


class Database:
    def __init__(self):
        self.connect()

    def connect(self):
        try:
            self.conn = mysql.connector.connect(**db_config)
            if self.conn.is_connected():
                self.cursor = self.conn.cursor()
                self.conn.autocommit = True
                print("MySQL connected.")
        except mysql.connector.Error as e:
            print(f"Error connecting to MySQL: {e}")

    def saver(self, queue):
        buffer = []
        while True:
            if not queue.empty():
                queue_data = queue.get()
                buffer.append(
                    (
                        0,
                        queue_data[0],
                        datetime.datetime.now().time(),
                        str(queue_data[1]),
                    )
                )
                if len(buffer) >= 30:
                    self.save(buffer)
                    buffer = []

    def save(self, data_list):
        try:
            query = (
                "INSERT INTO data (id, name, timestamp, data) VALUES (%s, %s, %s, %s)"
            )
            # query = "INSERT INTO sensor (id, sensor_type, timestamp, data) VALUES (%s, %s, %s, %s)"

            self.cursor.executemany(query, data_list)
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"{name} Error inserting data into MySQL: {e}")

    def get_last(self, name):
        try:
            query = "SELECT * FROM data WHERE name = %s ORDER BY id DESC LIMIT 1"
            self.cursor.execute(query, (name,))
            result = self.cursor.fetchone()
            if result:
                return result[1]
            return None
        except mysql.connector.Error as e:
            print(f"Error fetching data from MySQL: {e}")
            return None
