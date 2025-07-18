from sb import app, db, bcrypt
from flask import render_template, request, session, flash, redirect, url_for
import datetime, json
from bson.objectid import ObjectId
from collections import Counter


@app.route("/register_owner", methods=["GET", "POST"])
def register_owner():

    with open("../config.json") as config_file:
        config = json.load(config_file)

    if request.method == "POST":
        owner_info = request.form
        if owner_info["admin_password"] == config.get("ADMIN_PASSWORD"):
            # checking if owner name is already registered
            if db.Users.find_one({"user_name": owner_info["username"]}) is None:
                # checking if business name is already registered
                if db.Organizations.find_one({"org_name": owner_info["organization"]}) is None:
                    # registering business
                    db.Organizations.insert_one({
                        "org_name": owner_info["organization"],
                        "locations": [loc for loc in request.form.getlist("locations") if loc!= ""],
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
                        "locations": [loc for loc in org["locations"] if loc != ""]
                    })
                    flash(f"You have been registered successfully!", "success")
                    return redirect(url_for("login"))
                else:
                    flash("That business name is already registered, use another!", "error")
                    return redirect(url_for("register_owner"))
            else:
                flash("That user name is already registered, use another!", "error")
                return redirect(url_for("register_owner"))
        else:
            flash("Incorrect admin password!", "error")
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
        #updating employee name
        if employee_new_info["name"] != employee_old_info["user_name"]:
            if db.Users.find_one({"user_name": employee_new_info["name"]}) is None:
                db.Users.update_one({"_id": ObjectId(employee_new_info["emp_id"])}, {"$set":{"user_name": employee_new_info["name"]}})
                flash("Employee name has been updated successfully!", "success")
                if employee_old_info["role"] != "Owner":
                    session.pop(employee_old_info["user_name"], None)
                else:
                    session.pop(employee_old_info["user_name"], None)
                    session["username"] = employee_new_info["name"]
            else:
                flash("That user name is already registered, use another!", "error")

        #updating employee location
        if employee_new_info["location"] != employee_old_info["locations"][0]:
            db.Users.update_one({"_id": ObjectId(employee_new_info["emp_id"])}, {"$set":{"locations": [employee_new_info["location"]]}})
            flash("Employee date has been updated successfully!", "success")
        return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))
    
@app.route('/update_password', methods=['POST'])
def update_password():
    if request.method == "POST":
        form_data = request.form
        employee_info = db.Users.find_one({"_id": ObjectId(form_data["user_id"])})
        if form_data["new_password"] != form_data["confirm_password"]:
            flash("Passwords do not match!", "danger")
            return redirect(request.referrer)
        else:
            db.Users.update_one({"_id": ObjectId(form_data["user_id"])},{"$set": {
                "password": bcrypt.generate_password_hash(form_data["new_password"]).decode("utf-8")
            }})
            flash("Password updated successfully", "success")
            # session.pop(employee_info["username"], None)
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))
    
@app.route("/delete_sales_category", methods=["POST"])
def delete_sales_category():
    form_data = request.form
    user = db.Users.find_one({"user_name": session.get("username")})
    db.Organizations.update_one(
        {"_id": user["organization"]},
        {"$pull": {"income_categories": {"category_name": form_data["category"]}}}
    )
    flash("Category deleted successfuly", "success")
    return redirect(url_for("home"))

@app.route("/delete_expense_category", methods=["POST"])
def delete_expense_category():
    form_data = request.form
    user = db.Users.find_one({"user_name": session.get("username")})
    db.Organizations.update_one(
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

    if session.get("username") is None:
        return redirect(url_for("login"))

    if request.method == "GET":
        selected_location = user["locations"][0]
        # summaries
        if user["role"] == "Employee":
            sales = list(db.Sales.find({"organization_id": user["organization"], "logger_id": user["_id"]}))
            expenses = list(db.Expenses.find({"organization_id": user["organization"], "logger_id": user["_id"]}))
            org_sales = db.Sales.find({"organization_id": user["organization"], "type": "cash", "logger_id": user["_id"]})
            org_pending_sales = db.Sales.find({"organization_id": user["organization"], "type": "debt", "logger_id": user["_id"]})
            org_expenses = db.Expenses.find({"organization_id": user["organization"], "type": "cash", "logger_id": user["_id"]})
            org_pending_expenses = db.Expenses.find({"organization_id": user["organization"], "type": "debt", "logger_id": user["_id"]})
        else:
            sales = list(db.Sales.find({"organization_id": user["organization"], "location": selected_location}))
            expenses = list(db.Expenses.find({"organization_id": user["organization"], "location": selected_location}))
            org_sales = db.Sales.find({"organization_id": user["organization"], "type": "cash", "location": selected_location})
            org_pending_sales = db.Sales.find({"organization_id": user["organization"], "type": "debt", "location": selected_location})
            org_expenses = db.Expenses.find({"organization_id": user["organization"], "type": "cash", "location": selected_location})
            org_pending_expenses = db.Expenses.find({"organization_id": user["organization"], "type": "debt", "location": selected_location})
    elif request.method == "POST":
        selected_location = user["locations"][0]
        if user["role"] == "Employee":
            sales = list(db.Sales.find({"organization_id": user["organization"], "logger_id": user["_id"], "location": selected_location}))
            expenses = list(db.Expenses.find({"organization_id": user["organization"], "logger_id": user["_id"], "location": selected_location}))
            org_sales = db.Sales.find({"organization_id": user["organization"], "type": "cash", "logger_id": user["_id"], "location": selected_location})
            org_pending_sales = db.Sales.find({"organization_id": user["organization"], "type": "debt", "logger_id": user["_id"], "location": selected_location})
            org_expenses = db.Expenses.find({"organization_id": user["organization"], "type": "cash", "logger_id": user["_id"], "location": selected_location})
            org_pending_expenses = db.Expenses.find({"organization_id": user["organization"], "type": "debt", "logger_id": user["_id"], "location": selected_location})
        else:
            selected_location = request.form["selected_location"]
            #reshuffing user/owner's locations
            org_location_list = list(org["locations"])
            org_location_list.remove(selected_location)
            org_location_list.insert(0, selected_location)
            db.Users.update_one({"_id": ObjectId(user["_id"])},{"$set": {"locations": org_location_list}})

            sales = list(db.Sales.find({"organization_id": user["organization"], "location": selected_location}))
            expenses = list(db.Expenses.find({"organization_id": user["organization"], "location": selected_location}))
            org_sales = db.Sales.find({"organization_id": user["organization"], "type": "cash", "location": selected_location})
            org_pending_sales = db.Sales.find({"organization_id": user["organization"], "type": "debt", "location": selected_location})
            org_expenses = db.Expenses.find({"organization_id": user["organization"], "type": "cash", "location": selected_location})
            org_pending_expenses = db.Expenses.find({"organization_id": user["organization"], "type": "debt", "location": selected_location})

    total_income = sum(sale.get("amount", 0) for sale in sales)
    total_expenses = sum(exp.get("amount", 0) for exp in expenses)

    #net profit
    net_profit = total_income - total_expenses

    # Profit Margin
    if total_expenses != 0:
        profit_margin = f"{round((net_profit / total_income) * 100, 2)}%"
    else:
        profit_margin = "N/A"

    # Expense-to-Income Ratio
    if total_income != 0:
        exp_to_inc_ratio = f"{round((total_expenses / total_income) * 100, 2)}%"
    else:
        exp_to_inc_ratio = "N/A"
    
    # average daily income
    dates_1 = [datetime.datetime.strptime(sale["date"], "%B %d, %Y") for sale in sales]
    dates_2 = [datetime.datetime.strptime(exp["date"], "%B %d, %Y") for exp in expenses]
    days_between_1 = (max(dates_1) - min(dates_1)).days + 1 if dates_1 else 0
    days_between_2 = (max(dates_2) - min(dates_2)).days + 1 if dates_2 else 0

    if dates_1:
        if dates_1 > dates_2:
            average_daily_income = round((total_income/days_between_1), 2) if days_between_1 else "N/A"
        else:
            average_daily_income = round((total_income/days_between_2), 2) if days_between_2 else "N/A"
    else:
        average_daily_income = "N/A"

    # average daily expense
    if dates_2:
        if days_between_2 > days_between_1:
            average_daily_expense = round((total_expenses/days_between_2), 2) if days_between_2 else "N/A"
        else:
            average_daily_expense = round((total_expenses/days_between_1), 2) if days_between_1 else "N/A"
    else:
        average_daily_expense = "N/A"

    # working on sale sectors metricss
    sale_sectors = {}
    for sale in sales:
        category = sale["income_source"]
        amount = sale["amount"]
        if category in sale_sectors:
            sale_sectors[category] += amount
        else:
            sale_sectors[category] = amount
    sorted_sale_sectors = sorted(sale_sectors.items(), key=lambda x: x[1], reverse=True)

    # best sale sector
    best_sector = sorted_sale_sectors[0][0] if sorted_sale_sectors else "N/A"
    # worst sale sector
    worst_sector = []
    for i in org_income_categories:
        if i not in list(sale_sectors.keys()):
            worst_sector.append(i)
    if len(worst_sector) == 0:
         worst_sector = sorted_sale_sectors[-1][0] if sorted_sale_sectors else "N/A"
    else:
        worst_sector = ", ".join(worst_sector)
    top_sectors = ", ".join([sector[0] for sector  in sorted_sale_sectors[:3]]) if sorted_sale_sectors else "N/A"

    # for most active sales
    categories = [sale.get("income_source") for sale in sales if "income_source" in sale]
    if len(categories) != 0:
        category_counts = Counter(categories)
        sorted_category_list = sorted(
            [{"category": cat, "count": count} for cat, count in category_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )
        # most active sale sector
        most_active_sector = sorted_category_list[0]["category"] if sorted_category_list else "N/A"
        #least active sale sector
        least_active_sector = sorted_category_list[-1] if sorted_category_list else "N/A"
    else:
        most_active_sector = "N/A"
        least_active_sector = "N/A"

    # dealing with the expense metrics
    expense_groups = {}
    for exp in expenses:
        category = exp["expense_source"]
        amount = exp["amount"]
        if category in expense_groups:
            expense_groups[category] += amount
        else:
            expense_groups[category] = amount
    sorted_expense_groups = sorted(expense_groups.items(), key=lambda x: x[1], reverse=True)

    # biggest expense
    biggest_expense = sorted_expense_groups[0] if sorted_expense_groups else "N/A"
    
    # obtaining most common expense
    exp_categories = [exp.get("expense_source") for exp in expenses if "expense_source" in exp]
    exp_category_counts = Counter(exp_categories)
    sorted_exp_category_list = sorted(
        [{"category": cat, "count": count} for cat, count in exp_category_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )
    # most common expense
    most_common_expense = sorted_exp_category_list[0] if sorted_exp_category_list else "N/A"

    # for clients metrics
    client_categories = [sale.get("client_name") for sale in sales if "client_name" in sale]
    client_counts = Counter(client_categories)
    sorted_client_list = sorted(
        [{"category": cat, "count": count} for cat, count in client_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )

    #biggest client
    biggest_client = sorted_client_list[0] if sorted_client_list else "N/A"

    #biggest 3 client
    top_3_clients = ', '.join(client['category'] for client in sorted_client_list[:3]) if sorted_client_list else "N/A"

    # working on daily metrics
    daily_sales_info = {}
    for sale in sales:
        day = sale["date"]
        amount = sale["amount"]
        if day in daily_sales_info:
            daily_sales_info[day] += amount
        else:
            daily_sales_info[day] = amount

    daily_exp_info = {}
    for exp in expenses:
        day = exp["date"]
        amount = exp["amount"]
        if day in daily_exp_info:
            daily_exp_info[day] += amount
        else:
            daily_exp_info[day] = amount
    
    # computing profit for each day
    daily_profit_info = {}
    for d, p in daily_sales_info.items():
        day = d
        profit = (p - daily_exp_info[d]) if d in daily_exp_info else p
        if day in daily_profit_info:
            daily_profit_info[day] += profit
        else:
            daily_profit_info[day] = profit


    sorted_daily_profit_info = sorted(daily_profit_info.items(), key=lambda x: x[1], reverse=True)
    #most profitable table
    most_profitable_day = sorted_daily_profit_info[0] if sorted_daily_profit_info else "N/A"

    # least profitable day
    least_profitable_day = sorted_daily_profit_info[-1] if sorted_daily_profit_info else "N/A"

    # working on most active day
    active_days = [sale.get("date") for sale in sales if "date" in sale]
    active_day_counts = Counter(active_days)
    sorted_active_day_counts = sorted(
        [{"day": cat, "count": count} for cat, count in active_day_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )
    most_active_day = sorted_active_day_counts[0] if sorted_active_day_counts else "N/A"

    summary_info = {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "profit_margin": profit_margin,
        "exp_to_inc_ratio": exp_to_inc_ratio,
        "average_daily_income": average_daily_income,
        "average_daily_expense": average_daily_expense,
        "best_sector": best_sector,
        "worst_sector": worst_sector,
        "top_sectors": top_sectors,
        "most_active_sector": most_active_sector,
        "least_active_sector": least_active_sector,
        "biggest_expense": biggest_expense,
        "most_common_expense": most_common_expense,
        "biggest_client": biggest_client,
        "top_3_clients": top_3_clients,
        "most_profitable_day": most_profitable_day,
        "least_profitable_day": least_profitable_day,
        "most_active_day": most_active_day
        }
    
    return render_template("home.html",
                            year = datetime.datetime.today().year,
                            user = user,
                            org = org,
                            selected_location = selected_location,
                            org_employees = org_employees,
                            org_income_categories = org_income_categories, 
                            org_expense_categories = org_expense_categories,
                            org_sales = org_sales,
                            org_pending_sales = org_pending_sales,
                            org_expenses = org_expenses,
                            org_pending_expenses = org_pending_expenses,
                            summary_info = summary_info)



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
            "logger_name": user["user_name"],
            "organization_id": user["organization"],
            "income_source": form_data["income_source"],
            "amount": int(form_data["amount"]),
            "amount_left": int(form_data["amount"]) if form_data["type"] == "debt" else 0,
            "type": form_data["type"],
            "client_name": form_data["client_name"],
            "date": datetime.datetime.today().strftime("%B %d, %Y"),
            "location": user["locations"][0],
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
            "logger_name": user["user_name"],
            "organization_id": user["organization"],
            "expense_source": form_data["expense_source"],
            "amount": int(form_data["amount"]),
            "amount_left": int(form_data["amount"]) if form_data["type"] == "debt" else 0,
            "type": form_data["type"],
            "service_provider": form_data["recipient"],
            "source_of_funds": form_data["payment_method"],
            "date": datetime.datetime.today().strftime("%B %d, %Y"),
            "location": user["locations"][0],
            "comments": form_data["comments"],
            "payment_history": []
        })
        flash("Your expense has been recorded successfully!", "success")
        return redirect(url_for("home"))
    else:
        redirect(url_for("home"))


@app.route("/clear_income_debt", methods=["POST"])
def clear_income_debt():
    if request.method == "POST":
        form_data = request.form
        user = db.Users.find_one({"user_name": session.get("username")})

        db.Sales.update_one({"_id": ObjectId(form_data["sale_id"])}, {"$push": {"payment_history": {
            "date": datetime.datetime.today().strftime("%B %d, %Y"),
            "logger_name": user["user_name"],
            "amount": int(form_data["amount"])
            }}})
        
        sale_info = db.Sales.find_one({"_id": ObjectId(form_data["sale_id"])})

        amount_paid = 0
        for k in sale_info["payment_history"]:
            amount_paid = amount_paid + int(k["amount"])

        amount_left = int(sale_info["amount"]) - amount_paid
        db.Sales.update_one({"_id": ObjectId(form_data["sale_id"])}, {"$set": {"amount_left": amount_left}})

        if amount_left <= 0:
            db.Sales.update_one({"_id": ObjectId(form_data["sale_id"])}, {"$set": {"type": "cash"}})
        
        flash("Payment has been recorded successfully!", "success")
        return redirect(url_for("home"))
    else:
        redirect(url_for("home"))


@app.route("/clear_expense_debt", methods=["POST"])
def clear_expense_debt():
    if request.method == "POST":
        form_data = request.form
        user = db.Users.find_one({"user_name": session.get("username")})

        db.Expenses.update_one({"_id": ObjectId(form_data["expense_id"])}, {"$push": {"payment_history": {
            "date": datetime.datetime.today().strftime("%B %d, %Y"),
            "logger_name": user["user_name"],
            "amount": int(form_data["amount"])
            }}})
        
        expense_info = db.Expenses.find_one({"_id": ObjectId(form_data["expense_id"])})

        amount_paid = 0
        for k in expense_info["payment_history"]:
            amount_paid = amount_paid + int(k["amount"])

        amount_left = int(expense_info["amount"]) - amount_paid
        db.Expenses.update_one({"_id": ObjectId(form_data["expense_id"])}, {"$set": {"amount_left": amount_left}})

        if amount_left <= 0:
            db.Expenses.update_one({"_id": ObjectId(form_data["expense_id"])}, {"$set": {"type": "cash"}})
        
        flash("Payment has been recorded successfully!", "success")
        return redirect(url_for("home"))
    else:
        redirect(url_for("home"))


@app.route("/update_sale", methods=["POST"])
def update_sale():
    if request.method == "POST":
        form_data = request.form
        user = db.Users.find_one({"user_name": session.get("username")})
        db.Sales.update_one({"_id": ObjectId(form_data["sale_id"])}, {"$set": {
            "income_source": form_data["source"],
            "amount": int(form_data["amount"]),
            "client_name": form_data["client"],
            "comments": form_data["comments"]
        }})
        flash("Your sale has been updated successfully!", "success")
        return redirect(url_for("home"))
    else:
        redirect(url_for("home"))


@app.route("/update_expense", methods=["POST"])
def update_expense():
    if request.method == "POST":
        form_data = request.form
        user = db.Users.find_one({"user_name": session.get("username")})
        db.Expenses.update_one({"_id": ObjectId(form_data["expense_id"])}, {"$set": {
            "expense_source": form_data["category"],
            "amount": int(form_data["amount"]),
            "service_provider": form_data["payee"],
            "comments": form_data["comments"]
        }})
        flash("Your expense has been updated successfully!", "success")
        return redirect(url_for("home"))
    else:
        redirect(url_for("home"))