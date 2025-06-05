from sb import app, db, bcrypt
from flask import render_template, request, session, flash, redirect, url_for
import datetime
from bson.objectid import ObjectId

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
            return redirect(url_for("home"))
    return redirect(url_for("home"))

@app.route("/delete_emp", methods=["POST"])
def delete_emp():
    if request.method == "POST":
        form_data = request.form
        print(type(form_data["emp_id"]))
        db.Users.delete_one({"_id": ObjectId(form_data["emp_id"])})
        flash(f"{form_data['emp_name']} has been deleted successfully!", "success")
        return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))
    
@app.route("/edit_employee", methods=["POST"])
def edit_employee():
    if request.method == "POST":
        employee_new_info = request.form
        employee_old_info = db.Users.find_one({"_id": ObjectId(employee_new_info["emp_id"])})
        db.Users.delete_one({"_id": ObjectId(employee_new_info["emp_id"])})
        if employee_new_info["name"] != employee_old_info["user_name"]:
            if db.Users.find_one({"user_name": employee_new_info["name"]}) is None:
                employee_old_info["user_name"] = employee_new_info["name"]
            else:
                flash("That user name is already registered, use another!", "error")
                db.Users.insert_one(employee_old_info)
                return redirect(url_for("home"))
        employee_old_info["locations"] = [(employee_new_info["location"])]
        db.Users.insert_one(employee_old_info)
        flash("Employee data has been updated successfully!", "success")
        return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))
    
@app.route('/update_password', methods=['POST'])
def update_password():
    if request.method == "POST":
        form_data = request.form
        if form_data["new_password"] != form_data["confirm_password"]:
            flash("Passwords do not match!", "danger")
            return redirect(request.referrer)
        else:
            db.Users.update_one({"_id": ObjectId(form_data["user_id"])},{"$set": {
                "password": bcrypt.generate_password_hash(form_data["new_password"]).decode("utf-8")
            }})
            flash("Password updated successfully", "success")
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))
    
@app.route("/delete_sales_category", methods=["POST"])
def delete_sales_category():
    form_data = request.form
    user = db.Users.find_one({"user_name": session.get("username")})
    db.Organization.update_one(
        {"_id": user["organization"]},
        {"$pull": {"income_categories": {"category_name": form_data["category"]}}}
    )
    flash("Category deleted successfuly", "success")
    return redirect(url_for("home"))

@app.route("/delete_expense_category", methods=["POST"])
def delete_expense_category():
    form_data = request.form
    user = db.Users.find_one({"user_name": session.get("username")})
    db.Organization.update_one(
        {"_id": user["organization"]},
        {"$pull": {"expense_categories": {"category_name": form_data["category"]}}}
    )
    flash("Category deleted successfuly", "success")
    return redirect(url_for("home"))


@app.route("/home", methods=["GET", "POST"])
def home():
    user = db.Users.find_one({"user_name": session.get("username")})
    org = db.Organizations.find_one({"_id": user["organization"]})
    org_employees = db.Users.find({"organization": user["organization"]})
    org_income_categories = [k["category_name"] for k in org["income_categories"]]
    org_expense_categories = [k["category_name"] for k in org["expense_categories"]]
    return render_template("home_2.html",
                            user = user,
                            org = org,
                            org_employees = org_employees,
                            org_income_categories = org_income_categories, 
                            org_expense_categories = org_expense_categories)

@app.route("/add_income_category", methods=["POST"])
def add_income_category():
    if request.method == "POST":
        form_data = request.form
        user = db.Users.find_one({"user_name": session.get("username")})
        income_categories = db.Organizations.find_one({"_id": user["organization"]})["income_categories"]
        income_category_names = []
        for k in income_categories:
            income_category_names.append(k["category_name"])

        if form_data["income_category"] not in income_category_names:
            db.Organizations.update_one({ "_id": user["organization"] },{ "$push": { "income_categories": {
                "category_name": form_data["income_category"],
                "category_description": form_data["description"]
            }}})
            flash("Income Category has been added successfully!", "Error")
            return redirect(url_for("home"))
        else:
            flash("Income category already exists!", "Error")
            return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))

@app.route("/add_expense_category", methods=["POST"])
def add_expense_category():
    if request.method == "POST":
        form_data = request.form
        user = db.Users.find_one({"user_name": session.get("username")})
        expense_categories = db.Organizations.find_one({"_id": user["organization"]})["expense_categories"]
        expense_category_names = []
        for k in expense_categories:
            expense_category_names.append(k["category_name"])

        if form_data["expense_category"] not in expense_category_names:
            db.Organizations.update_one({ "_id": user["organization"] },{ "$push": { "expense_categories": {
                "category_name": form_data["expense_category"],
                "category_description": form_data["description"]
            }}})
            flash("Expense category has been added successfully!", "Error")
            return redirect(url_for("home"))
        else:
            flash("Expense category already exists!", "Error")
            return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))


@app.route("/add_sale", methods=["POST"])
def add_sale():
    if request.method == "POST":
        form_data = request.form
        user = db.Users.find_one({"user_name": session.get("username")})
        db.Sales.insert_one({
            "logger_id": user["_id"],
            "organization_id": user["organization"],
            "income_source": form_data["income_source"],
            "amount": form_data["amount"],
            "type": form_data["type"],
            "client_name": form_data["client_name"],
            "date": datetime.datetime.today(),
            "comments": form_data["comments"],
            "payment_history": []
        })
        flash("Your sale has been recorded successfully!", "success")
        return redirect(url_for("home"))
    else:
        redirect(url_for("home"))


@app.route("/add_expense", methods=["POST"])
def add_expense():
    if request.method == "POST":
        form_data = request.form
        user = db.Users.find_one({"user_name": session.get("username")})

        db.Expenses.insert_one({
            "logger_id": user["_id"],
            "organization_id": user["organization"],
            "expense_source": form_data["expense_source"],
            "amount": form_data["amount"],
            "type": form_data["type"],
            "service_provider": form_data["recipient"],
            "source_of_funds": form_data["payment_method"],
            "date": datetime.datetime.today(),
            "comments": form_data["comments"],
            "payment_history": []
        })
        flash("Your expense has been recorded successfully!", "success")
        return redirect(url_for("home"))
    else:
        redirect(url_for("home"))
