from database_connection import DatabaseConnected
from chat_helper import MessageHandler, DatabaseHandler


class GroupCreator:
    def __init__(self, members: list, group_name: str, username: str):
        self.members = members
        self.group_name = group_name
        self.username = username
        self.members_id = None

    def __check_if_group_exist(self) -> bool:
        public_channels = MessageHandler.get_public_channels()
        if self.group_name not in public_channels:
            return True

    def __set_members_id(self) -> list:
        user_id = DatabaseHandler.get_id(self.username)
        self.members_id = [int(DatabaseHandler.get_id(self.members[i])) for i in range(len(self.members))]
        self.members_id.append(user_id)
        return self.members_id

    def __add_group_to_database(self):
        with DatabaseConnected() as cursor:
            cursor.execute('INSERT INTO group_table VALUES(?,?)', (None, self.group_name))

    def add_group_members(self):
        group_id = DatabaseHandler.get_id(self.group_name)
        members = self.__set_members_id()
        for member in range(len(members)):
            with DatabaseConnected() as cursor:
                cursor.execute('INSERT INTO group_members VALUES(?,?)', (members[member], group_id))

    def start(self):
        MessageHandler.init()
        if self.__check_if_group_exist():
            self.__add_group_to_database()
            self.__set_members_id()
            self.add_group_members()


class GroupHandler:
    def __init__(self, username: str, group_name: str):
        self.username = username
        self.group_name = group_name
        self.group_id = DatabaseHandler.get_id(group_name)
        self.start()

    def __check_group_membership(self) -> bool:
        """ returns true if the user is a member of the group
               """
        user_id = DatabaseHandler.get_id(self.username)
        recipient_id = DatabaseHandler.get_id(self.group_name)
        with DatabaseConnected() as cursor:
            existed_membership = cursor.execute(
                "SELECT user_id FROM group_members WHERE user_id ='" + user_id + "'  AND group_id ='" + recipient_id + "' ").fetchone()
            existed_membership = str(existed_membership).strip("('',)'")
            if existed_membership == user_id:
                return True

    def group_membership_controller(self) -> bool:
        if self.__check_group_membership():
            print(f'you have joined {self.group_name} group chat!')
            choice = input('1- to chat  \n'
                           '2- to add new user to the group \n'
                           '3- to remove user from the group: ')
            if choice == '1':
                return True
            elif choice == '2':
                self.__add_new_member()
            elif choice == '3':
                self.__get_group_member()
                self.__remove_group_members()
            else:
                print('wrong number please choose again :) ')
            self.group_membership_controller()
        else:
            print(f'you are not a member in {self.group_name} please ask to join.')
            exit(0)

    def __add_new_member(self) -> None:
        username = input('enter username: ')
        user_id = DatabaseHandler.get_id(username)
        with DatabaseConnected() as cursor:
            cursor.execute('INSERT INTO group_members VALUES(?,?)', (user_id, self.group_id))

    def __remove_group_members(self):
        member_username = input(f' please {self.username} choose a member to be removed from {self.group_name}: ')
        member_id = DatabaseHandler.get_id(member_username)
        with DatabaseConnected() as cursor:
            cursor.execute(
                "DELETE FROM group_members WHERE group_id='" + self.group_id + "' and user_id = '" + member_id + "'")

    def __get_group_member(self) -> None:
        with DatabaseConnected() as cursor:
            group_members = cursor.execute(
                "SELECT u.name from users u ,group_members g  WHERE g.group_id='" + self.group_id + "' and g.user_id= u.id ").fetchall()
        self.__display_group_members(group_members)

    @staticmethod
    def __display_group_members(group_members) -> None:
        for x in range(len(group_members)):
            print(group_members[x][0])

    def start(self):
        self.group_membership_controller()
