import sqlite3 as sql
from contextlib import contextmanager


class DatabaseConnection:
    connection = None

    @classmethod
    @contextmanager
    def database_connection(cls) -> None:
        cls.connection = sql.connect("login.db", check_same_thread=False)
        cursor = cls.connection.cursor()
        try:
            yield cursor
        except Exception as exception:
            print(exception)
        finally:
            cls.connection.commit()
            cls.connection.close()
