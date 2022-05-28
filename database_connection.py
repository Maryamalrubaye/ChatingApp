import sqlite3


class DatabaseConnected:
    def __init__(self):
        self.database = "chatapp.db"

    def __enter__(self):
        self.connection = sqlite3.connect(self.database)
        self.cursor = self.connection.cursor()
        return self.cursor

    def __exit__(self, exc_class, exc, traceback):
        self.connection.commit()
        self.connection.close()