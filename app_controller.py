import login_system
import message_session


class AppController:
    def __init__(self):
        self.username = None
        self.recipient = None
        self.choice = None

    def get_user_info(self) -> None:
        """ check if user is registered or not and login to user account or creates new account
               """
        choice = input('for login please write 1 & for signup please write 2 : ')
        if choice == "1":
            self.username = login_system.Login().login()
            self.__get_recipient_info()
        elif choice == "2":
            username, password = login_system.Registration().register()
            self.username = login_system.Login().login(username, password)
            self.__get_recipient_info()
        else:
            print('Incorrect input! Please try again.')
            self.get_user_info()

    def __get_recipient_info(self) -> None:
        self.recipient: str = str(input("Enter your recipient: "))
        message_session.MessageSession(self.username, self.recipient)


if __name__ == '__main__':
    AppController().get_user_info()
