import logging
from contextlib import contextmanager
from typing import List, Tuple

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
from tenacity import retry, stop_after_attempt, wait_exponential

from config import DB_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.db_config = DB_CONFIG
        self.pool = MySQLConnectionPool(
            pool_name="mypool", pool_size=5, pool_reset_session=True, **self.db_config
        )

    @contextmanager
    def get_connection(self):
        conn = self.pool.get_connection()
        try:
            yield conn
        except mysql.connector.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            conn.close()

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def save(self, data_list: List[Tuple]):
        query = "INSERT INTO data (id, name, timestamp, data) VALUES (%s, %s, %s, %s)"
        with self.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.executemany(query, data_list)
                conn.commit()
                logger.info(f"Successfully saved {len(data_list)} records.")
            except mysql.connector.Error as e:
                logger.error(f"Error saving data: {e}")
                conn.rollback()
                raise

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def get_last(self, name: str):
        query = "SELECT * FROM data WHERE name = %s ORDER BY id DESC LIMIT 1"
        with self.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, (name,))
                    return cursor.fetchone()
            except mysql.connector.Error as e:
                logger.error(f"Error fetching last record for {name}: {e}")
                raise
