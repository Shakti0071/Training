
class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

class Account(User):
    users = {}  

    def __init__(self, username, password):
        super().__init__(username, password)  
        Account.users[username] = password    

    @classmethod
    def signup(cls):
        username = input("Enter a new username: ")
        if username in cls.users:
            print("Username already exists!")
        else:
            password = input("Enter a new password: ")
            cls(username, password)  
            print("Signup successful!")

    @classmethod
    def login(cls):
        username = input("Enter your username: ")
        password = input("Enter your password: ")

        if username in cls.users:
            if cls.users[username] == password:
                print(f"Login successful! Welcome, {username}")
            else:
                print("Wrong password!")
        else:
            print("Username not found! Please signup first.")

while True:
    print("\n1. Signup")
    print("2. Login")
    print("3. Exit")

    choice = input("Enter choice: ")

    if choice == "1":
        Account.signup()
    elif choice == "2":
        Account.login()
    elif choice == "3":
        print("Goodbye!")
        break
    else:
        print("Invalid choice!")
