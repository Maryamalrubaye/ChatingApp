import login_system
import contact_history

from chat_helper import MessageHandler
from message_session import MessageSession
from group_chat import GroupCreator, GroupHandler


class AppController:
    def __init__(self):
        self.username = None
        self.recipient = None
        self.choice = None

    def get_user_info(self) -> None:
        """ check if user is registered or not and login to user account or creates new account
               """
        self.choice = input('for login please write 1 & for signup please write 2: ')
        if self.choice == "1":
            self.username = login_system.Login().login()
        elif self.choice == "2":
            username, password = login_system.Registration().register()
            self.username = login_system.Login().login(username, password)
        else:
            print('Incorrect input! Please try again.')
            self.get_user_info()
        self.__main_page()

    def __get_recipient_info(self) -> None:
        MessageHandler.init()
        self.recipient: str = str(input("Enter your recipient: "))
        if self.__check_if_channel_exist():
            self.__channel_type()
        else:
            self.__get_recipient_info()

    def __main_page(self):
        print(f'Welcome {self.username} you have contacted the following channels: ')
        contact_history.ContactHistory(self.username)
        self.choice = input('1- to create a new group  \n'
                            '2- to search for new user \n'
                            '3- choose any of the previously contacted channels \n'
                            '4- to exit: ')
        if self.choice == '1':
            self.__group_creator()
        elif self.choice in ['2', '3']:
            self.__get_recipient_info()
        elif self.choice == '4':
            print('bye bye sweet one :) ')
            exit()
        else:
            print('wrong number please choose again :) ')
            self.__main_page()

    def __group_creator(self) -> None:
        group_name: str = str(input("Enter a group name: "))
        members = input('Enter elements of a list separated by space ')
        print("\n")
        members_list = members.split()
        GroupCreator(members_list, group_name, self.username).start()
        self.__main_page()

    def __check_if_channel_exist(self) -> bool:
        channel_exist = True
        all_channels = MessageHandler.get_all_channels()
        if self.recipient not in all_channels:
            print(f"Recipient '{self.recipient}' does not exist! please try again.")
            channel_exist = False
        return channel_exist

    def __channel_type(self) -> None:
        public_channels = MessageHandler.get_public_channels()
        if self.recipient in public_channels:
            if GroupHandler(self.username, self.recipient):
                MessageSession(self.username, self.recipient)
        else:
            MessageSession(self.username, self.recipient)


if __name__ == '__main__':
    AppController().get_user_info()
