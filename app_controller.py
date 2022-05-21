import login_system
import message_session


class AppController:
    def __init__(self):
        self.username = None
        self.recipient = None

    def get_user_info(self) -> bool:
        """ check if user is registered or not and login to user account or creates new account
               """
        choice = input('for login please write 1 & for signup please write 2 : ')
        if choice == "1":
            self.username = login_system.Login().start()
            return True
        elif choice == "2":
            self.username = login_system.Registration().register()
            return True

        else:
            print('Incorrect input! Please try again.')
            self.get_user_info()

    def __get_recipient_info(self) -> None:
        self.recipient: str = str(input("Enter your recipient: "))
        message_session.MessageSession(self.username, self.recipient)

    def start(self) -> None:
        if self.get_user_info():
            self.__get_recipient_info()


if __name__ == '__main__':
    AppController().start()
