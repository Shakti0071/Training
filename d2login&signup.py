
users = {}

def signup():
    username = input("Enter a new username: ")
    if username in users:
        print("Username already exists!")
    else:
        password = input("Enter a new password: ")
        users[username] = password   
        print("Signup successful!")

def login():
    username = input("Enter your username: ")
    password = input("Enter your password: ")

    if username in users:  
        if users[username] == password:
            print("Login successful! Welcome,", username)
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
        signup()
    elif choice == "2":
        login()
    elif choice == "3":
        print("Goodbye!")
        break
    else:
        print("Invalid choice!")
