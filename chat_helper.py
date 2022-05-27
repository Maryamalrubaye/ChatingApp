import json
import redis
import datetime
import itertools

from typing import Tuple

from database_connection import DatabaseConnected


class RedisConnected:
    def __init__(self):
        self.port = 6379
        self.password = 'maryam21'
        self.host = 'localhost'

    def __enter__(self):
        self.redis_client = redis.StrictRedis(host=self.host, port=self.port, password=self.password)
        return self.redis_client

    def __exit__(self, exc_class, exc, traceback):
        self.redis_client.close()


class MessageHandler:
    channels = {
        'private': None,
        'public': None,
    }

    @classmethod
    def init(cls) -> None:
        with DatabaseConnected() as cursor:
            usernames = cursor.execute("SELECT name FROM users").fetchall()
            all_usernames = [username for username in usernames]
            cls.channels['private'] = list(itertools.chain(*all_usernames))

            groups = cursor.execute("SELECT group_name FROM group_table").fetchall()
            all_groups = [group for group in groups]
            cls.channels['public'] = list(itertools.chain(*all_groups))

    @classmethod
    def get_private_channels(cls) -> list:
        return cls.channels['private']

    @classmethod
    def get_public_channels(cls) -> list:
        return cls.channels['public']

    @classmethod
    def get_channels(cls) -> Tuple[list, list]:
        """ Returns private and public channels names in order.
        """
        return cls.channels['private'], cls.channels['public']

    @classmethod
    def get_all_channels(cls) -> list:
        """ Returns all channels names in one list.
        """
        private_channels, public_channels = cls.get_channels()
        # unpack the list using *
        return [*private_channels, *public_channels]


class DatabaseHandler:
    def __init__(self, recipient: str, data: dict, username: str):
        self.recipient = recipient
        self.data = data
        self.username = username
        self.__insert_messages()

    def __insert_messages(self) -> None:
        """ Listens continuously to user messages and save them to the database.
        """
        data = json.dumps(self.data)
        data = json.loads(data)
        username = self.get_id(self.username)
        message = data['message']
        recipient_type = self.__check_recipient_type()
        recipient = self.get_id(self.recipient)
        current_datetime = datetime.datetime.now()
        with DatabaseConnected() as cursor:
            cursor.execute('INSERT INTO messages VALUES(?,?,?,?,?,?)',
                           (None, username, message, recipient, recipient_type, current_datetime))

    @staticmethod
    def get_id(name) -> int:
        """ Get channel id using channel name.
               """
        private_channels = MessageHandler.get_private_channels()
        with DatabaseConnected() as cursor:
            if name in private_channels:
                user_id = cursor.execute(
                    "SELECT id from users WHERE name='" + name + "'").fetchone()
                user_id = str(user_id).strip("('',)'")
                return user_id
            else:
                user_id = cursor.execute(
                    "SELECT id from group_table WHERE group_name='" + name + "'").fetchone()
                user_id = str(user_id).strip("('',)'")
                return user_id

    def __check_recipient_type(self) -> str:
        """  check recipient type if it is group or user
        so we could save its type as a receiver type to handle the messages in the database
               """
        public_channels = MessageHandler.get_public_channels()
        private_channels = MessageHandler.get_private_channels()
        if self.recipient in public_channels:
            recipient_type = 'group'
            return recipient_type
        elif self.recipient in private_channels:
            recipient_type = 'user'
            return recipient_type
