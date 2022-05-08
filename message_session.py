import json
import time
import redis
import sqlite3
import sys
from typing import Tuple
from threading import Thread
import itertools

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


class LoginHandler:
    connection = sqlite3.connect("login.db")
    cursor = connection.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS login (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL UNIQUE,email TEXT NOT NULL UNIQUE,password TEXT NOT NULL)")
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS GroupTable (name TEXT NOT NULL)")

    connection.commit()
    usernames = cursor.execute("SELECT name FROM login").fetchall()
    username_list = list(itertools.chain(*[username for username in usernames]))
    groups = cursor.execute("SELECT name FROM GroupTable").fetchall()
    group_list = list(itertools.chain(*[group for group in groups]))

    @classmethod
    def check_username_existing(cls, username) -> bool:
        existed_username = LoginHandler.cursor.execute(
            "SELECT name FROM login WHERE name='" + username + "'").fetchone()
        existed_username = str(existed_username).strip("('',)'")
        if existed_username == username:
            return True

    @classmethod
    def check_email_existing(cls, email) -> bool:
        existed_email = LoginHandler.cursor.execute("SELECT email FROM login WHERE email='" + email + "'").fetchone()
        existed_email = str(existed_email).strip("('',)'")
        if existed_email == email:
            return True


class Registration:
    def __init__(self):
        self.username = None
        self.password = None
        self.email = None
        self.rewrite_password = None
        self.start_login()

    def start_login(self) -> None:
        while True:
            self.username = input("Enter your username. ")
            if LoginHandler.check_username_existing(self.username):
                print('That username already exists,try another one!')
                continue
            else:
                while True:
                    self.email = input("Enter your email. ")
                    if LoginHandler.check_email_existing(self.email):
                        print('That email is already in our database,enter another one!')
                        continue
                    else:
                        while True:
                            self.password = input("Enter your password. ")
                            self.rewrite_password = input("Enter your password again. ")
                            if self.__check_password():
                                sys.exit()
                            continue

    def __check_password(self) -> bool:
        if self.password == self.rewrite_password:
            LoginHandler.cursor.execute('INSERT INTO login VALUES(?,?,?,?)',
                                        (None, self.username, self.email, self.password))
            LoginHandler.connection.commit()
            print('You are now registered.')
            return True

        else:
            print('Password does not match')
            return False


class Login:
    def __init__(self, username: str):
        self.password = None
        self.username = username

    def start(self) -> bool:
        cursor = LoginHandler.cursor
        check_user = False
        while True:
            password = input("Enter your password. ")
            if LoginHandler.check_username_existing(self):
                db_password = cursor.execute("SELECT password from login WHERE password='" + password + "'").fetchone()
                db_password = str(db_password).strip("('',)'")
                if db_password == password:
                    print('You are now logged in.')
                    check_user = True
                    return check_user
                else:
                    print('Wrong password.')
            else:
                print('Wrong username.')
                return check_user


class MessageHandler:
    port = 6379
    password = 'maryam21'
    redis_client = redis.Redis(host='localhost', port=port, password=password)

    channels = {
        'private': LoginHandler.username_list,
        'public': LoginHandler.group_list,
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
                    if self.__check_user_accessibility(username):
                        message = data['message']
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
                if Login.start(self.username):
                    break
            self.recipient: str = str(input("Enter your Recipient: "))
        elif query == "2":
            Registration()
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
