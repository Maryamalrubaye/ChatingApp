import json
import time
import redis

from typing import Tuple
from threading import Thread
import login_system as lg

"""
private chat: 
    -publish: the other person channel
    -subscribe: the session owner (the username owner)
public chat (groups):
all people wishing to use public chat should:
    -publish: the username
    -subscribe: group channel.
    
    
TODO:
- filter user subscribed message to be as same as the publisher name. (for the private chat) done
- group chat done
- login/signup (id, username, password) done
- every user chat history 
"""


class MessageHandler:
    port = 6379
    password = 'maryam21'
    redis_client = redis.Redis(host='localhost', port=port, password=password)

    channels = {
        'private': lg.LoginHandler.username_list,
        'public': lg.LoginHandler.group_list,
    }

    @classmethod
    def get_private_channels(cls):
        return cls.channels['private']

    @classmethod
    def get_public_channels(cls):
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


class ChatHistoryHandler:
    def __init__(self, recipient: str, data: dict):
        self.recipient = recipient
        self.data = data
        self.database_conn()

    def database_conn(self) -> None:
        """ Listens continuously to user messages and save them  to the database.
        """

        data = json.dumps(self.data)
        data = json.loads(data)
        username = data['username']
        message = data['message']
        user_id = lg.LoginHandler.cursor.execute(
                "SELECT id from users WHERE name='" + username + "'").fetchone()
        user_id = str(user_id).strip("('',)'")
        lg.LoginHandler.cursor.execute('INSERT INTO messages VALUES(?,?,?,?,?)', (None, username, self.recipient, message, user_id))
        lg.LoginHandler.connection.commit()


class PrivateMessageSubscriber(Thread, MessageHandler):
    def __init__(self, user_channel: str, recipient: str):
        super().__init__()
        self.user_channel = user_channel
        self.recipient = recipient
        self.start()

    def run(self) -> None:
        redis_pubsub = MessageHandler.redis_client.pubsub()
        redis_pubsub.subscribe(self.user_channel)
        while True:
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
        user_exist = True
        if self.recipient != user:
            user_exist = False
        return user_exist


class PublicMessageSubscriber(Thread, MessageHandler):
    def __init__(self, user_channel: str, recipient: str):
        super().__init__()
        self.user_channel = user_channel
        self.recipient = recipient
        self.start()

    def run(self) -> None:
        redis_pubsub = MessageHandler.redis_client.pubsub()
        redis_pubsub.subscribe(self.recipient)
        while True:
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
        ChatHistoryHandler(self.recipient, data)
        json_data = json.dumps(data)
        MessageHandler.redis_client.publish(recipient, json_data)

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


class MessageSession:
    def __init__(self):
        self.username = None
        self.recipient = None

    def get_user_info(self) -> None:
        query = input('for login please write 1 & for signup please write 2')
        if query == "1":
            while True:
                self.username: str = str(input("Enter your username: "))
                if lg.Login.start(self.username):
                    break
            self.recipient: str = str(input("Enter your Recipient: "))
        elif query == "2":
            lg.Registration()
        else:
            print('Incorrect input.Run script again. ')

    def start_messaging_session(self):
        """ Starts the messaging session.
        """
        public_channels = MessageHandler.get_public_channels()
        private_channels = MessageHandler.get_private_channels()
        if self.recipient in public_channels:
            PublicMessageSubscriber(self.username, self.recipient)
        elif self.recipient in private_channels:
            PrivateMessageSubscriber(self.username, self.recipient)
        MessagePublisher(self.username, self.recipient)

    def __check_if_channel_exist(self) -> bool:
        channel_exist = True
        all_channels = MessageHandler.get_all_channels()
        print(all_channels)
        if self.recipient not in all_channels:
            print(f"Recipient '{self.recipient}' does not exist!")
            channel_exist = False
        return channel_exist

    def start(self) -> None:
        self.get_user_info()
        if self.__check_if_channel_exist():
            self.start_messaging_session()


if __name__ == '__main__':
    MessageSession().start()
