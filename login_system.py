import sqlite3
import sys
import itertools


class LoginHandler:
    connection = sqlite3.connect("login.db", check_same_thread=False)
    cursor = connection.cursor()
    connection.commit()

    usernames = cursor.execute("SELECT name FROM login").fetchall()
    username_list = list(itertools.chain(*[username for username in usernames]))

    groups = cursor.execute("SELECT group_name FROM group_table").fetchall()
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
