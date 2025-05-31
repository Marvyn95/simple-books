from sb import app
from flask import render_template


@app.route("/home", methods=["GET", "POST"])
def Home_Page():
    data=[]
    return render_template("home_page.html", Data = data)


@app.route("/sign_up", methods=["GET", "POST"])
def sign_up():
    return "login page"

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET","POST"])
def login():
    return "login"


