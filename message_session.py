import json
import time
import redis
import datetime
import itertools

from typing import Tuple
from threading import Thread

from database_connection import DatabaseConnected

"""
private chat: 
    -publish: the other person channel
    -subscribe: the session owner (the username owner)
public chat (groups):
all people wishing to use public chat should:
    -publish: the username
    -subscribe: group channel.
"""


class RedisConnected:
    def __init__(self):
        self.port = 6379
        self.password = 'maryam21'
        self.host = 'localhost'

    def __enter__(self):
        self.redis_client = redis.Redis(host=self.host, port=self.port, password=self.password)
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


class ChatDatabaseHandler:
    def __init__(self, recipient: str, data: dict, username: str):
        self.recipient = recipient
        self.data = data
        self.username = username
        self.insert_messages()

    def insert_messages(self) -> None:
        """ Listens continuously to user messages and save them to the database.
        """
        data = json.dumps(self.data)
        data = json.loads(data)
        username = self.get_user_id(self.username)
        message = data['message']
        recipient_type = self.__check_recipient_type()
        recipient = self.get_user_id(self.recipient)
        current_datetime = datetime.datetime.now()
        with DatabaseConnected() as cursor:
            cursor.execute('INSERT INTO messages VALUES(?,?,?,?,?,?)',
                           (None, username, message, recipient, recipient_type, current_datetime))

    @staticmethod
    def get_user_id(user) -> int:
        """ Get channel id using channel name.
               """
        private_channels = MessageHandler.get_private_channels()
        with DatabaseConnected() as cursor:
            if user in private_channels:
                user_id = cursor.execute(
                    "SELECT id from users WHERE name='" + user + "'").fetchone()
                user_id = str(user_id).strip("('',)'")
                return user_id
            else:
                user_id = cursor.execute(
                    "SELECT id from group_table WHERE group_name='" + user + "'").fetchone()
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


class GroupCreator:
    def __init__(self, members: list, group_name: str):
        self.members = members
        self.group_name = group_name
        self.members_id = None
        self.start()

    def __check_if_group_exist(self) -> bool:
        public_channels = MessageHandler.get_public_channels()
        if self.group_name not in public_channels:
            return True

    def __get_members_id(self) -> list:
        self.members_id = [int(ChatDatabaseHandler.get_user_id(self.members[i])) for i in range(len(self.members))]
        return self.members_id

    def __add_group_to_database(self):
        with DatabaseConnected() as cursor:
            cursor.execute('INSERT INTO group_table VALUES(?,?)', (None, self.group_name))

    def __add_group_members(self):
        group_id = ChatDatabaseHandler.get_user_id(self.group_name)
        members = self.__get_members_id()
        for member in range(len(members)):
            with DatabaseConnected() as cursor:
                cursor.execute('INSERT INTO group_members VALUES(?,?)', (members[member], group_id))

    def start(self):
        MessageHandler.init()
        if self.__check_if_group_exist():
            self.__add_group_to_database()
            self.__get_members_id()
            self.__add_group_members()


class PrivateMessageSubscriber(Thread, MessageHandler):
    def __init__(self, user_channel: str, recipient: str):
        super().__init__()
        self.user_channel = user_channel
        self.recipient = recipient
        self._thread = None
        self.start()

    def run(self) -> None:
        with RedisConnected() as redis_client:
            redis_pubsub = redis_client.pubsub()
            redis_pubsub.subscribe(self.user_channel)
        if self._thread is not None:
            self._thread.stop()
            self._thread = redis_client.pubsub.run_in_thread()
            redis_message = redis_pubsub.get_message()
            if redis_message:
                data = redis_message["data"]
                if data and isinstance(data, bytes):
                    data = json.loads(data)
                    username = data['username']
                    message = data['message']
                    if self.__check_user_accessibility(username):
                        print(f"\n{username}: {message}\n")
                        time.sleep(0.01)

    def __check_user_accessibility(self, user) -> bool:
        """  Returns true if the the user has the accessibility to enter private chat
               """
        user_exist = True
        if self.recipient != user:
            user_exist = False
        return user_exist


class PublicMessageSubscriber(Thread, MessageHandler):
    def __init__(self, user_channel: str, recipient: str):
        super().__init__()
        self.user_channel = user_channel
        self.recipient = recipient
        self._thread = None
        self.start()

    def run(self) -> None:
        with RedisConnected() as redis_client:
            redis_pubsub = redis_client.pubsub()
            redis_pubsub.subscribe(self.recipient)
            if self._thread is not None:
                self._thread.stop()
            self._thread = redis_client.pubsub.run_in_thread()
            redis_message = redis_pubsub.get_message()
            if redis_message:
                data = redis_message["data"]
                if data and isinstance(data, bytes):
                    data = json.loads(data)
                    username = data['username']
                    message = data['message']
                    print(f"\n{username}: {message}\n")
                    time.sleep(0.01)


class MessagePublisher(Thread):
    def __init__(self, username: str, recipient: str):
        super().__init__()
        self.username = username
        self.recipient = recipient
        self.start()

    def send_message(self, data: dict, recipient: str) -> None:
        """ Prepares and publishes the message to the redis client

        Args:
            data: message to sent to redis channel.
            recipient: the message recipient.
        """
        ChatDatabaseHandler(self.recipient, data, self.username)
        json_data = json.dumps(data)
        with RedisConnected() as redis_client:
            redis_client.publish(recipient, json_data)

    def run(self) -> None:
        """ Listens continuously to user messages and send them them to the desired destination.
        """
        print("Message session has been started.")
        while True:
            message: str = str(input(f"{self.username}: "))
            data: dict = {
                'username': self.username,
                'message': message
            }
            self.send_message(data, self.recipient)


class MessagesRecovery:
    def __init__(self, username: str, recipient: str):
        self.username = username
        self.recipient = recipient

    def public_messages_recovery(self) -> None:
        recipient_id = ChatDatabaseHandler.get_user_id(self.recipient)
        with DatabaseConnected() as cursor:
            messages = cursor.execute(
                "SELECT  u.name, m.message_content from messages m, users u WHERE m.receiver_id ='" + recipient_id + "' and m.receiver_type ='group' and u.id = m.sender_id ORDER BY m.date ASC").fetchall()
        self.__print_messages(messages)

    def private_messages_recovery(self) -> None:
        recipient_id = ChatDatabaseHandler.get_user_id(self.recipient)
        user_id = ChatDatabaseHandler.get_user_id(self.username)
        with DatabaseConnected() as cursor:
            messages = cursor.execute(
                "SELECT u.name, m.message_content from messages m, users u WHERE m.sender_id ='" + user_id + "' and m.receiver_id ='" + recipient_id + "' and m.receiver_type ='user' and u.id ='" + user_id + "' or m.sender_id ='" + recipient_id + "' and m.receiver_id ='" + user_id + "' and m.receiver_type ='user' and u.id ='" + recipient_id + "' ORDER BY m.date ASC ").fetchall()
            self.__print_messages(messages)

    @staticmethod
    def __print_messages(messages) -> None:
        """ print and reformat messages history coming from the database
               """
        for x in range(len(messages)):
            print(messages[x][0] + ' : ' + messages[x][1])


class MessageSession:
    def __init__(self, username: str, recipient: str):
        self.username = username
        self.recipient = recipient
        self.start()

    def start_messaging_session(self) -> None:
        """ Starts the messaging session.
        """
        public_channels = MessageHandler.get_public_channels()
        private_channels = MessageHandler.get_private_channels()
        if self.recipient in public_channels:
            MessagesRecovery(self.username, self.recipient).public_messages_recovery()
            PublicMessageSubscriber(self.username, self.recipient)
        elif self.recipient in private_channels:
            MessagesRecovery(self.username, self.recipient).private_messages_recovery()
            PrivateMessageSubscriber(self.username, self.recipient)
        MessagePublisher(self.username, self.recipient)

    def __check_if_channel_exist(self) -> bool:
        MessageHandler.init()
        channel_exist = True
        all_channels = MessageHandler.get_all_channels()
        print(f'{all_channels = }')
        if self.recipient not in all_channels:
            print(f"Recipient '{self.recipient}' does not exist!")
            channel_exist = False
        return channel_exist

    def __check_group_membership(self) -> bool:
        """ returns true if the user is a member of the group
               """
        user_id = ChatDatabaseHandler.get_user_id(self.username)
        recipient_id = ChatDatabaseHandler.get_user_id(self.recipient)
        with DatabaseConnected() as cursor:
            existed_membership = cursor.execute(
                "SELECT user_id FROM group_members WHERE user_id ='" + user_id + "'  AND group_id ='" + recipient_id + "' ").fetchone()
            existed_membership = str(existed_membership).strip("('',)'")
            if existed_membership == user_id:
                return True

    def __group_membership_controller(self) -> None:
        public_channels = MessageHandler.get_public_channels()
        if self.recipient in public_channels:
            if self.__check_group_membership():
                print(f'you have joined {self.recipient} group chat!')
            else:
                user_id = ChatDatabaseHandler.get_user_id(self.username)
                recipient_id = ChatDatabaseHandler.get_user_id(self.recipient)
                with DatabaseConnected() as cursor:
                    cursor.execute('INSERT INTO group_members VALUES(?,?)', (user_id, recipient_id))

    def start(self) -> None:
        if self.__check_if_channel_exist():
            self.__group_membership_controller()
            self.start_messaging_session()
