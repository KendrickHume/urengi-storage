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

# Home
@app.route("/", methods=["POST", "GET"])
def home():
    data = getdbpath()
    cursor = data.cursor()
    cursor.execute("SELECT * FROM inventory")
    items = cursor.fetchall()
    lenofitems = len(items)
    totalincategory = 0
    category = ""
    if request.method == "POST":
        action = request.form["action"]
        if action == "search":
            category = request.form["category"]
            if category == "":
                cursor.execute("SELECT * FROM inventory")
                items = cursor.fetchall()
            else:
                cursor.execute("SELECT * FROM inventory WHERE category = ?", (category,))
                items = cursor.fetchall()
                totalincategory = len(items)
        elif action == "update":
            itemid = request.form["item"]
            return redirect(url_for("updateitem", itemid=itemid))
    return render_template("index.html", items=items, lenofitems=lenofitems, category=category, totalincategory=totalincategory)
    
# Add Item
@app.route("/additem", methods=["POST", "GET"])
def additem():
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
            cursor.execute("INSERT INTO inventory (name, category, qty) VALUES(?, ?, ?)", (item, category, qty))
            data.commit()
            data.close()
            flash("Item successfully added")
            return redirect(url_for("additem"))
    return render_template("additem.html")

# Update and Delete Item
@app.route("/updateitem/<itemid>", methods=["POST", "GET"])
def updateitem(itemid):
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
            cursor.execute("UPDATE inventory SET name = ?, category = ?, qty = ? WHERE itemid = ?", (item, category, qty, itemid))
            data.commit()
            data.close()
            flash("Item id, " + itemid + ", successfully updated")
            return redirect(url_for("home"))
        elif action == "Delete":
            delitemid = request.form["delitemid"]
            cursor.execute("SELECT * FROM inventory WHERE itemid = ?", (delitemid,))
            exists = cursor.fetchone()
            if exists:
                cursor.execute("DELETE FROM inventory WHERE itemid = ?", (delitemid,))
                data.commit()
                data.close()
                flash("Item id, " + delitemid + " deletion success")
                return redirect(url_for("home"))
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


if __name__ == "__main__":
    # app.run(debug=True)
    app.run(ipaddress, 5555)
