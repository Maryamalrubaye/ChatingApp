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
    def get_username_input(cls) -> str:
        username: str = str(input("Enter your username: "))
        return username

    @classmethod
    def get_password_input(cls) -> str:
        password: str = str(input("Enter your password: "))
        return password


class UserSession:
    username: str = None


class Registration(UserSession):
    def __init__(self):
        self.username = None
        self.password = None
        self.email = None
        self.password_confirmation = None
        self.LoginHandler = LoginHandler()

    def register(self) -> None:
        self.__set_username()
        self.__set_email()
        self.__set_passwords()
        self.__confirm_password()
        self.__register_to_database()
        print('You are now registered.')
        Login().login(self.username, self.password)

    def __set_passwords(self) -> None:
        self.password = self.LoginHandler.get_password_input()
        self.password_confirmation = self.LoginHandler.get_password_input()

    def __confirm_password(self) -> bool:
        if self.password == self.password_confirmation:
            return True
        print('password did not match! try again')
        self.__set_passwords()
        self.__confirm_password()

    def __set_email(self) -> bool:
        self.email = input(" Enter your email:")
        if not self.LoginHandler.check_email_existing(self.email):
            return True
        print('That email is already in our database,enter another one!')
        self.__set_email()

    def __set_username(self) -> bool:
        self.username = self.LoginHandler.get_username_input()
        if not self.LoginHandler.check_username_existing(self.username):
            return True
        print('That username already exists, try another one!')
        self.__set_username()

    def __register_to_database(self) -> bool:
        with DatabaseConnected() as cursor:
            cursor.execute('INSERT INTO users VALUES(?,?,?,?)', (None, self.username, self.email, self.password))
            return True


class Login(UserSession):
    def __init__(self):
        self.password = None
        self.username = None

    def set_username(self, user=None) -> None:
        self.username = user or LoginHandler.get_username_input()

    def set_password(self, password=None) -> None:
        self.password = password or LoginHandler.get_password_input()

    def login(self, username=None, password=None) -> None:
        self.set_username(username)
        self.set_password(password)
        if LoginHandler.check_username_existing(self.username) and self.__check_password():
            print('Successfully logged-in :)')
        else:
            print('wrong username or password please try again!')
            self.login()

        UserSession.username = self.username

    def __check_password(self) -> bool:
        with DatabaseConnected() as cursor:
            db_password = cursor.execute(
                "SELECT password from users WHERE password='" + self.password + "'").fetchone()
            db_password = str(db_password).strip("('',)'")
            if db_password == self.password:
                return True


if __name__ == '__main__':
    Registration().register()
