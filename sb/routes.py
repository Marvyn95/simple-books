from sb import app, db, bcrypt
from flask import render_template, request, session, flash, redirect, url_for

@app.route("/register_owner", methods=["GET", "POST"])
def register_owner():
    if request.method == "POST":
        owner_info = request.form
        # checking if owner name is already registered
        if db.Users.find_one({"user_name": owner_info["username"]}) is None:
            # checking if business name is already registered
            if db.Organizations.find_one({"org_name": owner_info["organization"]}) is None:
                # registering business
                db.Organizations.insert_one({
                    "org_name": owner_info["organization"],
                    "locations": request.form.getlist("locations"),
                    "income_categories": [],
                    "expense_categories": []
                })

                # registering owner
                org = db.Organizations.find_one({"org_name": owner_info["organization"]})
                db.Users.insert_one({
                    "user_name": owner_info["username"],
                    "email": owner_info["email"],
                    "password": bcrypt.generate_password_hash(owner_info["password"]).decode("utf-8"),
                    "role": "Owner",
                    "organization": org["_id"],
                    "locations": org["locations"]
                })
                flash(f"You have been registered successfully!", "success")
                return redirect(url_for("login"))
            else:
                flash("That business name is already registered, use another!", "error")
                return redirect(url_for("register_owner"))
        else:
            flash("That user name is already registered, use another!", "error")
            return redirect(url_for("register_owner"))
    return render_template("register_owner.html")


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        #getting form info
        credentials = request.form
        #authenticating
        user = db.Users.find_one({"user_name": credentials["username"]})
        if user:
            if bcrypt.check_password_hash(user["password"], credentials["password"]):
                session["username"] = user["user_name"]
                flash("you have been logged in successfully!", "success")
                return redirect(url_for('home'))
            else:
                flash("Incorrect password!", "error")
                return redirect(url_for('login'))
        else:
            flash("That user name is not registered, try again!", "error")
        return redirect(url_for('login'))   
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("You have been logged out successfully!", "info")
    return redirect(url_for("login"))

@app.route("/register_emp", methods=["GET", "POST"])
def register_emp():
    user_data = db.Users.find_one({"user_name": session.get("username")})
    if request.method == "POST":
        employee_info = request.form
        #checking if employee name is registered
        if db.Users.find_one({"user_name": employee_info["username"]}) is None:
            # registering employee
            db.Users.insert_one({
                "user_name": employee_info["username"],
                "email": "",
                "password": bcrypt.generate_password_hash(employee_info["password"]).decode("utf-8"),
                "role": "Employee",
                "organization": user_data["organization"],
                "locations": [employee_info["location"]]
            })
            flash(f"Your employee {employee_info["username"]} has been registered successfully!", "success")
            return redirect(url_for("home"))
        else:
            flash("That user name is already registered, use another!", "error")
            return redirect(url_for("register_emp"))
    return render_template("register_emp.html", locations = user_data["locations"])


@app.route("/home", methods=["GET", "POST"])
def home():
    user = db.Users.find_one({"user_name": session.get("username")})
    org = db.Organizations.find_one({"_id": user["organization"]})
    return render_template("home.html", user = user, org = org)

@app.route("/add_income_category", methods=["POST"])
def add_income_category():
    if request.method == "POST":
        form_data = request.form
        user = db.Users.find_one({"user_name": session.get("username")})
        if form_data["income_category"] not in db.Organizations.find_one({"_id": user["organization"]})["income_categories"]
            db.Organizations.update_one({ "_id": user["organization"] },{ "$push": { "income_categories": form_data["income_category"] }})
            flash("Income Category has been added successfully!", "Error")
        else:
            flash("Income category already exists!", "Error")
            return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))
        




