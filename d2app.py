from flask import Flask, request, redirect, url_for, session, render_template
from pymongo import MongoClient


class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

class Account(User):
    users = {}

    def __init__(self, username, password):
        super().__init__(username, password)

    @classmethod
    def signup(cls, username, password):
        if username in cls.users:
            return False
        cls.users[username] = password
        return True

    @classmethod
    def login(cls, username, password):
        return username in cls.users and cls.users[username] == password


app = Flask(__name__)
app.secret_key = "your_secret_key"


client = MongoClient("mongodb+srv://shakti4052_db_user:shakti1707@cluster0.dmyk79s.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["flaskdb"]
users_collection = db["users"]


@app.route("/")
def home():
    return redirect(url_for("signup"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    message = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not password or not confirm_password:
            message = "Please fill all fields."
        elif password != confirm_password:
            message = "Passwords do not match!"
        elif users_collection.find_one({"username": username}):
            message = "Username already exists!"
        else:
            users_collection.insert_one({"username": username, "password": password})
            return redirect(url_for("login"))

    return render_template("signup.html", message=message)

@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = users_collection.find_one({"username": username, "password": password})

        if user:
            session["username"] = username
            return redirect(url_for("chat"))
        else:
            message = "Invalid username or password!"

    return render_template("login.html", message=message)

@app.route("/chat")
def chat():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("chat.html", username=session["username"])

if __name__ == "__main__":
    app.run(debug=True)
