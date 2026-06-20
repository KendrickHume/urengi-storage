from flask import Flask, redirect, url_for, render_template, request, session, flash
import socket, sqlite3, os, psycopg2

# Socket IPv4
# hostname = socket.gethostname()
# ipaddress = socket.gethostbyname(hostname)

# Global Vars
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))  # Doesn't actually send data
ipaddress = s.getsockname()[0]
s.close()

# Flask Setup
app = Flask(__name__)
app.secret_key = "**90##!!??"

# Data setup
BASEDIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASEDIR, "data", "inventory.db")

def getdbpath():
    dburl = os.environ.get("DATABASE_URL")
    return psycopg2.connect(dburl)

# data = sqlite3.connect(DATABASE)
# cursor = data.cursor()

# # inventory
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS inventory (
#     itemid INTEGER PRIMARY KEY AUTOINCREMENT,
#     name TEXT NOT NULL,
#     category TEXT NOT NULL,  
#     qty INTEGER NOT NULL
# )
# """)

# # login credentials
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS logincreds (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         Username TEXT NOT NULL,
#         Password TEXT NOT NULL,
#         AccountFor TEXT NOT NULL
#     )
# """)

# data.commit()
# data.close()

# Login
@app.route("/", methods=["POST", "GET"])
def login():
    data = getdbpath()
    if request.method == "POST":
        action = request.form["action"]
        if action == "login":
            username = request.form["username"]
            password = request.form["password"]
            cursor = data.cursor()
            cursor.execute("SELECT * FROM logincreds WHERE Username = %s AND Password = %s", (username, password))
            user = cursor.fetchone()
            if user[3] == "inventory":
                session["user"] = user
                return redirect(url_for("inventoryhome"))
            elif user[3] == "admin":
                session["user"] = user
                return redirect(url_for("admin"))
            else:
                flash("Incorect Username or Password")
                return redirect(url_for("login"))
    return render_template("login.html")

# admin
@app.route("/admin", methods=["POST", "GET"])
def admin():
    if "user" not in session:
        flash("Not logged in")
        return redirect(url_for("login"))
    data = getdbpath()
    cursor = data.cursor()
    cursor.execute("SELECT * FROM logincreds")
    logins = cursor.fetchall()
    if request.method == "POST":
        action = request.form["action"]
        if action == "addaccount":
            username = request.form["username"]
            password = request.form["password"]
            accountfor = request.form["accountfor"]
            cursor.execute("SELECT * FROM logincreds WHERE username = %s AND password = %s", (username, password))
            account = cursor.fetchone()
            if account:
                flash("Account Exists")
            else:
                cursor.execute("INSERT INTO logincreds (Username, Password, AccountFor) VALUES (%s, %s, %s)", (username, password, accountfor))
                data.commit()
                data.close()
                flash("Account Created")
                return redirect(url_for("admin"))
        elif action == "deleteaccount":
            id = request.form["id"]
            cursor.execute("SELECT * FROM logincreds WHERE id = %s", (id,))
            account = cursor.fetchone()
            if account:
                cursor.execute("DELETE FROM logincreds WHERE id = %s", (id,))
                data.commit()
                data.close()
                flash("Account Deleted")
                return redirect(url_for("admin"))
            else:
                flash("Account id doesn't exist")
                return redirect(url_for("admin"))
    return render_template("admin.html", logins=logins)

# Inventory Home
@app.route("/inventoryhome", methods=["POST", "GET"])
def inventoryhome():
    if "user" not in session:
        flash("Not logged in")
        return redirect(url_for("login"))
    data = getdbpath()
    cursor = data.cursor()
    cursor.execute("SELECT * FROM inventory")
    items = cursor.fetchall()
    totalincategory = len(items)
    category = "All"
    if request.method == "POST":
        action = request.form["action"]
        if action == "search":
            category = request.form["category"]
            if category == "":
                cursor.execute("SELECT * FROM inventory")
                items = cursor.fetchall()
                return redirect(url_for("inventoryhome"))
            else:
                cursor.execute("SELECT * FROM inventory WHERE category = %s", (category,))
                items = cursor.fetchall()
                totalincategory = len(items)
                return render_template("inventoryhome.html", items=items, totalincategory=totalincategory, category=category)
        elif action == "update":
            itemid = request.form["item"]
            return redirect(url_for("updateitem", itemid=itemid))
    return render_template("inventoryhome.html", items=items, category=category, totalincategory=totalincategory)
    
# Add Item
@app.route("/additem", methods=["POST", "GET"])
def additem():
    if "user" not in session:
        flash("Not logged in")
        return redirect(url_for("login"))
    data = getdbpath()
    cursor = data.cursor()
    if request.method == "POST":
        item = request.form["item"]
        category = request.form["category"]
        qty = request.form["qty"]
        if item == "" or category == "" or qty == "":
            flash("all fields required")
            return redirect(url_for("additem"))
        else:
            cursor.execute("INSERT INTO inventory (name, category, qty) VALUES(%s, %s, %s)", (item, category, qty))
            data.commit()
            data.close()
            flash("Item successfully added")
            return redirect(url_for("additem"))
    return render_template("additem.html")

# Update and Delete Item
@app.route("/updateitem/<itemid>", methods=["POST", "GET"])
def updateitem(itemid):
    if "user" not in session:
        flash("Not logged in")
        return redirect(url_for("login"))
    data = getdbpath()
    cursor = data.cursor()
    cursor.execute("SELECT * FROM inventory WHERE itemid = ?", (itemid,))
    item = cursor.fetchone()
    if request.method == "POST":
        action = request.form["action"]
        if action == "Update":
            item = request.form["item"]
            category = request.form["category"]
            qty = request.form["qty"]
            cursor.execute("UPDATE inventory SET name = %s, category = %s, qty = %s WHERE itemid = %s", (item, category, qty, itemid))
            data.commit()
            data.close()
            flash("Item id, " + itemid + ", successfully updated")
            return redirect(url_for("inventoryhome"))
        elif action == "Delete":
            delitemid = request.form["delitemid"]
            cursor.execute("SELECT * FROM inventory WHERE itemid = %s", (delitemid,))
            exists = cursor.fetchone()
            if exists:
                cursor.execute("DELETE FROM inventory WHERE itemid = %s", (delitemid,))
                data.commit()
                data.close()
                flash("Item id, " + delitemid + " deletion success")
                return redirect(url_for("inventoryhome"))
            else:
                flash("Item id, " + delitemid + " not found")
                return redirect(url_for("updateitem"), itemid)
        elif action == "Add stock":
            qty = request.form["qty"]
            qty = int(qty) + 1
            return render_template("updateitem.html", vitemid=item[0], vitem=item[1], vcategory=item[2], vqty=qty)
        elif action == "Take out":
            qty = request.form["qty"]
            qty = int(qty) - 1
            return render_template("updateitem.html", vitemid=item[0], vitem=item[1], vcategory=item[2], vqty=qty)
    return render_template("updateitem.html", vitemid=item[0], vitem=item[1], vcategory=item[2], vqty=item[3])

# exit
@app.route("/exit", methods=["POST", "GET"])
def exit():
    session.pop("user", None)
    flash("Logged out")
    return redirect(url_for("login"))

if __name__ == "__main__":
    # app.run(debug=True)
    app.run(ipaddress, 5555)
