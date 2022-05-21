from typing import Tuple

from database_connection import DatabaseConnected


class LoginHandler:

    @classmethod
    def check_username_existing(cls, username) -> bool:
        with DatabaseConnected() as cursor:
            existed_username = cursor.execute(
                "SELECT name FROM users WHERE name='" + username + "'").fetchone()
            existed_username = str(existed_username).strip("('',)'")
            if existed_username == username:
                return True

    @classmethod
    def check_email_existing(cls, email) -> bool:
        with DatabaseConnected() as cursor:
            existed_email = cursor.execute("SELECT email FROM users WHERE email='" + email + "'").fetchone()
            existed_email = str(existed_email).strip("('',)'")
            if existed_email == email:
                return True

    @classmethod
    def set_username(cls) -> str:
        username: str = str(input("Enter your username: "))
        return username

    @classmethod
    def set_password(cls) -> str:
        password: str = str(input("Enter your password: "))
        return password


class Registration:
    def __init__(self):
        self.username = None
        self.password = None
        self.email = None
        self.rewrite_password = None
        self.LoginHandler = LoginHandler()

    def register(self) -> Tuple[str, str]:
        self.__set_username()
        self.__set_email()
        self.__check_password()
        self.____register_to_database()
        print('You are now registered.')
        return self.username, self.password

    def __check_password(self) -> bool:
        self.password = self.LoginHandler.set_password()
        self.rewrite_password = self.LoginHandler.set_password()
        if self.password == self.rewrite_password:
            return True
        else:
            print('password did not match! try again')
            self.__check_password()

    def __set_email(self) -> bool:
        self.email = input(" Enter your email:")
        if self.LoginHandler.check_email_existing(self.email):
            print('That email is already in our database,enter another one!')
            self.__set_email()
        else:
            return True

    def __set_username(self) -> bool:
        self.username = self.LoginHandler.set_username()
        if self.LoginHandler.check_username_existing(self.username):
            print('That username already exists, try another one!')
            self.__set_username()
        else:
            return True

    def ____register_to_database(self) -> bool:
        with DatabaseConnected() as cursor:
            cursor.execute('INSERT INTO users VALUES(?,?,?,?)', (None, self.username, self.email, self.password))
            return True


class Login:
    def __init__(self):
        self.password = None
        self.username = None

    def get_username(self, user=None) -> str:
        if user is None:
            self.username = LoginHandler.set_username()
        else:
            self.username = user

    def get_password(self, password=None) -> str:
        if password is None:
            self.password = LoginHandler.set_password()
        else:
            self.password = password

    def login(self, username=None, password=None) -> str:
        self.get_username(username)
        self.get_password(password)
        if LoginHandler.check_username_existing(self.username) and self.__check_password():
            print('Successfully logged-in :)')
            return self.username
        else:
            print('wrong username or password please try again!')
            self.login()

    def __check_password(self) -> bool:
        with DatabaseConnected() as cursor:
            db_password = cursor.execute(
                "SELECT password from users WHERE password='" + self.password + "'").fetchone()
            db_password = str(db_password).strip("('',)'")
            if db_password == self.password:
                return True


if __name__ == '__main__':
    Registration().register()
