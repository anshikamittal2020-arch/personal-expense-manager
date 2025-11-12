from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
from datetime import date, timedelta
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
app.secret_key = "secret123"


# -------------------- DATABASE --------------------
def connect_db():
    return sqlite3.connect("expenses.db")

def init_db():
    db = connect_db()
    
    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT,
        amount REAL,
        spent_on TEXT,
        note TEXT
    )
    """)

    db.commit()
    db.close()

init_db()


# -------------------- LOGIN --------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        pwd = request.form["password"]

        db = connect_db()
        user = db.execute(
            "SELECT id FROM users WHERE username=? AND password=?",
            (username, pwd)
        ).fetchone()
        db.close()

        if user:
            session["user_id"] = user[0]
            return redirect("/dashboard")
        return "Invalid login"

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        pwd = request.form["password"]

        try:
            db = connect_db()
            db.execute("INSERT INTO users(username, password) VALUES(?,?)",
                       (username, pwd))
            db.commit()
            db.close()
            return redirect("/")
        except:
            return "User already exists."

    return render_template("register.html")


# -------------------- DASHBOARD --------------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":
        category = request.form["category"]
        amount = float(request.form["amount"])
        spent_on = request.form["spent_on"]
        note = request.form["note"]

        db = connect_db()
        db.execute("""
            INSERT INTO expenses (user_id, category, amount, spent_on, note)
            VALUES (?, ?, ?, ?, ?)
        """, (session["user_id"], category, amount, spent_on, note))
        db.commit()
        db.close()

        return redirect("/dashboard")

    db = connect_db()
    expenses = db.execute("""
        SELECT id, category, amount, spent_on, note
        FROM expenses WHERE user_id=?
        ORDER BY spent_on DESC
    """, (session["user_id"],)).fetchall()
    db.close()

    return render_template("dashboard.html", expenses=expenses)


# -------------------- DELETE EXPENSE --------------------
@app.route("/delete/<int:id>")
def delete_expense(id):
    db = connect_db()
    db.execute("DELETE FROM expenses WHERE id=?", (id,))
    db.commit()
    db.close()
    return redirect("/dashboard")


# ----------------- DAILY / WEEKLY / MONTHLY FILTER -----------------
def get_period_start(period):
    today = date.today()
    if period == "daily":
        return today
    elif period == "weekly":
        return today - timedelta(days=today.weekday())
    elif period == "monthly":
        return today.replace(day=1)
    return today


@app.route("/summary/<period>")
def summary(period):
    start_date = get_period_start(period)

    db = connect_db()
    rows = db.execute("""
        SELECT category, amount, spent_on
        FROM expenses
        WHERE user_id=? AND date(spent_on) >= date(?)
    """, (session["user_id"], start_date)).fetchall()
    db.close()

    totals = {}
    for cat, amt, _ in rows:
        totals[cat] = totals.get(cat, 0) + amt

    return render_template("summary.html", period=period, totals=totals)


# -------------------- CATEGORY GRAPH --------------------
@app.route("/graph/<period>")
def graph(period):
    start_date = get_period_start(period)

    db = connect_db()
    rows = db.execute("""
        SELECT category, amount FROM expenses
        WHERE user_id=? AND date(spent_on) >= date(?)
    """, (session["user_id"], start_date)).fetchall()
    db.close()

    totals = {}
    for cat, amt in rows:
        totals[cat] = totals.get(cat, 0) + amt

    # matplotlib graph
    plt.figure(figsize=(6,4))
    plt.bar(totals.keys(), totals.values())
    plt.title(f"{period.capitalize()} Expenses")
    plt.xlabel("Category")
    plt.ylabel("Amount")
    plt.tight_layout()

    graph_path = "static/graph.png"
    plt.savefig(graph_path)
    plt.close()

    return send_file(graph_path, mimetype="image/png")


if __name__ == "__main__":
    app.run(debug=True)
