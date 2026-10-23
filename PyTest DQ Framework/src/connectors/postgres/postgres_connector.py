import psycopg2
import pandas as pd


class PostgresConnectorContextManager:
    def __init__(self, db_user, db_password, db_host="localhost", db_name="mydatabase", db_port="5434"):
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_name = db_name
        self.db_port = db_port
        self.connection = None

    def __enter__(self):
        self.connection = psycopg2.connect(
            user=self.db_user,
            password=self.db_password,
            host=self.db_host,
            database=self.db_name,
            port=self.db_port,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection and not self.connection.closed:
            self.connection.close()

    def get_data_sql(self, query: str) -> pd.DataFrame:
        """Executes a SQL query and returns the result as a pandas DataFrame."""
        if not self.connection or self.connection.closed:
            raise ConnectionError("PostgreSQL connection is not open.")
        return pd.read_sql_query(query, self.connection)