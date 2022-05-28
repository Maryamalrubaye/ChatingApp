import json
import time

from typing import List
from threading import Thread
from abc import ABC, abstractmethod

from database_connection import DatabaseConnected
from chat_helper import RedisConnected, MessageHandler, DatabaseHandler


"""
private chat: 
    -publish: the other person channel
    -subscribe: the session owner (the username owner)
public chat (groups):
all people wishing to use public chat should:
    -publish: the username
    -subscribe: group channel.
"""


class Subscriber(ABC):
    def __init__(self, user_channel: str, recipient: str):
        self.user_channel = user_channel
        self.recipient = recipient
        self.start()

    def start(self) -> None:
        with RedisConnected() as redis_client:
            subscribe_handler = {
                self.get_subscriber(): self.message_handler
            }
            redis_pubsub = redis_client.pubsub()
            redis_pubsub.subscribe(**subscribe_handler)
            redis_pubsub.run_in_thread(time.sleep(0.01))

    @abstractmethod
    def get_subscriber(self) -> str:
        """

        Returns:

        """
        pass

    @abstractmethod
    def message_handler(self, data: dict) -> None:
        """

        Args:
            data:

        Returns:

        """
        pass


class GroupMessageSubscriber(Subscriber):
    """ Private messages redis subscriber.
    """
    def get_subscriber(self) -> str:
        return self.user_channel

    def message_handler(self, redis_data: dict) -> None:
        json_data = redis_data['data']
        data = json.loads(json_data)
        username = data['username']
        message = data['message']
        if self.__check_user_accessibility(username):
            print(f"\n{username}: {message}\n")

    def __check_user_accessibility(self, user: str) -> bool:
        """  Returns true if the the user has the accessibility to enter private chat
        """
        user_exist = True
        if self.recipient != user:
            user_exist = False
        return user_exist


class IndividualMessageSubscriber(Subscriber):
    """ Public messages redis subscriber.
    """
    def get_subscriber(self) -> str:
        return self.recipient

    def message_handler(self, redis_data: dict) -> None:
        json_data = redis_data['data']
        data = json.loads(json_data)
        username = data['username']
        message = data['message']
        print(f"\n{username}: {message}\n")


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
        DatabaseHandler(self.recipient, data, self.username)
        json_data = json.dumps(data)
        with RedisConnected() as redis_client:
            redis_client.publish(recipient, json_data)

    def run(self) -> None:
        """ Listens continuously to user messages and send them them to the desired destination.
        """
        print("Message session has been started.")
        while True:
            message = str(input(f"{self.username}: "))
            data = {
                'username': self.username,
                'message': message
            }
            self.send_message(data, self.recipient)


class MessagesHistory:
    def __init__(self, username: str, recipient: str):
        self.username = username
        self.recipient = recipient

    def group_messages(self) -> None:
        recipient_id = DatabaseHandler.get_id(self.recipient)
        with DatabaseConnected() as cursor:
            messages = cursor.execute(
                "SELECT  u.name, m.message_content from messages m, users u WHERE m.receiver_id ='" + recipient_id + "' and m.receiver_type ='group' and u.id = m.sender_id ORDER BY m.date ASC").fetchall()
        self.__print_messages(messages)

    def individual_messages(self) -> None:
        recipient_id = DatabaseHandler.get_id(self.recipient)
        user_id = DatabaseHandler.get_id(self.username)
        with DatabaseConnected() as cursor:
            messages = cursor.execute(
                "SELECT u.name, m.message_content from messages m, users u WHERE m.sender_id ='" + user_id + "' and m.receiver_id ='" + recipient_id + "' and m.receiver_type ='user' and u.id ='" + user_id + "' or m.sender_id ='" + recipient_id + "' and m.receiver_id ='" + user_id + "' and m.receiver_type ='user' and u.id ='" + recipient_id + "' ORDER BY m.date ASC ").fetchall()
            self.__print_messages(messages)

    @staticmethod
    def __print_messages(messages: List[tuple]) -> None:
        """ print and reformat messages history coming from the database
               """
        for index in range(len(messages)):
            print(messages[index][0] + ': ' + messages[index][1])


class MessageSession:
    def __init__(self, username: str, recipient: str):
        self.username = username
        self.recipient = recipient
        self.public_channels = MessageHandler.get_public_channels()
        self.private_channels = MessageHandler.get_private_channels()
        self.start()

    def start(self) -> None:
        """ Starts the messaging session.
        """
        if self.recipient in self.public_channels:
            MessagesHistory(self.username, self.recipient).group_messages()
            IndividualMessageSubscriber(self.username, self.recipient)
        elif self.recipient in self.private_channels:
            MessagesHistory(self.username, self.recipient).individual_messages()
            GroupMessageSubscriber(self.username, self.recipient)
        MessagePublisher(self.username, self.recipient)

