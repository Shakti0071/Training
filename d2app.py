from flask import Flask, render_template_string, request, redirect, url_for


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


# ----- Flask app -----
app = Flask(__name__)

# --- HTML Templates ---
signup_page = """
<!doctype html>
<html>
<head>
    <title>Signup</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: #f0f2f5;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-image: linear-gradient(135deg, #74ebd5 0%, #9face6 100%);
        }
        .signup-container {
            background: rgba(255, 255, 255, 0.9);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            text-align: center;
            width: 350px;
            animation: slideIn 1s ease-out;
        }
        h2 {
            color: #333;
            margin-bottom: 25px;
            font-size: 2.2em;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
        }
        form {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 1px solid #ccc;
            border-radius: 10px;
            font-size: 1em;
            transition: all 0.3s ease;
        }
        input[type="text"]:focus, input[type="password"]:focus {
            border-color: #667eea;
            box-shadow: 0 0 8px rgba(102, 126, 234, 0.6);
            outline: none;
        }
        button {
            background-image: linear-gradient(to right, #74ebd5 0%, #9face6 100%);
            color: white;
            padding: 15px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1.1em;
            font-weight: bold;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            box-shadow: 0 5px 15px rgba(118, 75, 162, 0.4);
        }
        button:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(118, 75, 162, 0.6);
        }
        .message {
            color: #d9534f;
            margin-top: 15px;
            font-weight: bold;
        }
        a {
            color: #667eea;
            text-decoration: none;
            margin-top: 20px;
            font-size: 1em;
            transition: color 0.3s ease;
        }
        a:hover {
            color: #764ba2;
            text-decoration: underline;
        }
        @keyframes slideIn {
            from {
                transform: translateY(-50px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
    </style>
</head>
<body>
    <div class="signup-container">
        <h2>Signup</h2>
        <form method="post">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Create Account</button>
        </form>
        <p class="message">{{ message }}</p>
        <a href="{{ url_for('login') }}">Already have an account? Login here.</a>
    </div>
</body>
</html>
"""

login_page = """
<!doctype html>
<html>
<head>
    <title>Login</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: #f0f2f5;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-image: linear-gradient(135deg, #74ebd5 0%, #9face6 100%);
        }
        .login-container {
            background: rgba(255, 255, 255, 0.9);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            text-align: center;
            width: 350px;
            animation: slideIn 1s ease-out;
        }
        h2 {
            color: #333;
            margin-bottom: 25px;
            font-size: 2.2em;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
        }
        form {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 1px solid #ccc;
            border-radius: 10px;
            font-size: 1em;
            transition: all 0.3s ease;
        }
        input[type="text"]:focus, input[type="password"]:focus {
            border-color: #74ebd5;
            box-shadow: 0 0 8px rgba(116, 235, 213, 0.6);
            outline: none;
        }
        button {
            background-image: linear-gradient(to right, #74ebd5 0%, #9face6 100%);
            color: white;
            padding: 15px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1.1em;
            font-weight: bold;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            box-shadow: 0 5px 15px rgba(145, 172, 230, 0.4);
        }
        button:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(145, 172, 230, 0.6);
        }
        .message {
            color: #5cb85c;
            margin-top: 15px;
            font-weight: bold;
        }
        a {
            color: #74ebd5;
            text-decoration: none;
            margin-top: 20px;
            font-size: 1em;
            transition: color 0.3s ease;
        }
        a:hover {
            color: #9face6;
            text-decoration: underline;
        }
        @keyframes slideIn {
            from {
                transform: translateY(-50px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>Login</h2>
        <form method="post">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Log In</button>
        </form>
        <p class="message">{{ message }}</p>
        <a href="{{ url_for('signup') }}">Don't have an account? Sign up here.</a>
    </div>
</body>
</html>
"""

# --- Routes ---
@app.route("/")
def home():
    return redirect(url_for("signup"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    message = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            message = "Please fill both fields."
        elif Account.signup(username, password):
            print(f"New user created: {username}")
            print(f"Current users dictionary: {Account.users}")
            return redirect(url_for("login"))
        else:
            print(f"Attempted to create existing user: {username}")
            print(f"Current users dictionary: {Account.users}")
            message = "Username already exists!"

    return render_template_string(signup_page, message=message)

@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if Account.login(username, password):
            message = f"Login successful! Welcome, {username}"
        else:
            message = "Invalid username or password!"

    return render_template_string(login_page, message=message)

if __name__ == "__main__":
    app.run(debug=True)

