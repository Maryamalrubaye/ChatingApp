from chat_helper import MessageHandler
from database_connection import DatabaseConnected


class ContactHistory:
    def __init__(self, username: str):
        self.username = username
        self.start()

    def __get_previous_conversations(self):
        user_id = self.__get_user_id(self.username)
        with DatabaseConnected() as cursor:
            usernames = cursor.execute(
                "SELECT u.name  from users u, messages m  WHERE m.receiver_id ='" + user_id + "' and m.receiver_type ='user' and m.sender_id = u.id  or m.sender_id ='" + user_id + "' and m.receiver_id = u.id ").fetchall()
            self.__print_previous_chat(usernames)

    def __get_joined_groups(self):
        user_id = self.__get_user_id(self.username)
        with DatabaseConnected() as cursor:
            groups = cursor.execute(
                "SELECT group_name  from  group_table g, group_members gm WHERE gm.user_id ='" + user_id + "' and  gm.group_id = g.id  ").fetchall()
            self.__print_previous_chat(groups)

    def __print_previous_chat(self, chats) -> None:
        # TODO: make it one for loop
        non_duplicate_usernames = []
        for x in chats:
            if x not in non_duplicate_usernames:
                non_duplicate_usernames.append(x)

        for x in range(len(non_duplicate_usernames)):
            if non_duplicate_usernames[x][0] != self.username:
                print(non_duplicate_usernames[x][0])

    @staticmethod
    def __get_user_id(user) -> int:
        with DatabaseConnected() as cursor:
            user_id = cursor.execute(
                "SELECT id from users WHERE name='" + user + "'").fetchone()
            user_id = str(user_id).strip("('',)'")
            return user_id

    def start(self) -> None:
        MessageHandler.init()
        self.__get_previous_conversations()
        self.__get_joined_groups()


if __name__ == '__main__':
    ContactHistory('maryam')
