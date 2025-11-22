import sqlite3
from flask import Flask, request, redirect
from datetime import date

app = Flask(__name__)

DB = "expenses.db"

# ---------- Helper: Ensure date column exists ----------
def ensure_date_column():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(expenses)")
    cols = [r[1] for r in cur.fetchall()]  # column names
    if "date" not in cols:
        # safe ALTER TABLE to add a date TEXT column
        cur.execute("ALTER TABLE expenses ADD COLUMN date TEXT")
        conn.commit()
    conn.close()

# ---------- Helper: Render a Page ----------
def render_page(page_file, content=""):
    # start / page / end files are expected under pages/
    with open("pages/layout_start.html") as f:
        start = f.read()

    with open(f"pages/{page_file}") as f:
        page = f.read()

    with open("pages/layout_end.html") as f:
        end = f.read()

    # We replace "{{content}}" inside the page file with content HTML
    return start + page.replace("{{content}}", content) + end

# Ensure DB has date column when app starts
ensure_date_column()

# ---------- HOME ----------
@app.route("/")
def home():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # total expenses
    cur.execute("SELECT SUM(CAST(amount AS REAL)) FROM expenses")
    s = cur.fetchone()[0]
    total = float(s) if s is not None else 0.0

    conn.close()

    summary_html = f"""
    <div class="home-summary">
        <h3>Total Spending: ₹{total:.2f}</h3>
    </div>
    """

    return render_page("home.html", summary_html)

# ---------- ADD PAGE ----------
@app.route("/add")
def add_page():
    return render_page("add.html")

# ---------- SAVE EXPENSE ----------
@app.route("/save", methods=["POST"])
def save_expense():
    amount = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    custom = request.form.get("custom_category", "").strip()

    if category == "Other" and custom:
        category = custom

    note = request.form.get("note", "").strip()
    # date input (format YYYY-MM-DD). If empty, use today's date.
    expense_date = request.form.get("date", "").strip()
    if not expense_date:
        expense_date = date.today().isoformat()

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO expenses (amount, category, note, date) VALUES (?, ?, ?, ?)",
        (amount, category, note, expense_date),
    )
    conn.commit()
    conn.close()

    return redirect("/view")

# ---------- VIEW PAGE ----------
@app.route("/view")
def view_page():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, amount, category, note, date FROM expenses")
    rows = cursor.fetchall()
    conn.close()

    table = """
    <h2>All Expenses</h2>
    <table class='styled-table'>
        <thead>
        <tr>
            <th>ID</th>
            <th>Amount</th>
            <th>Category</th>
            <th>Note</th>
            <th>Date</th>
            <th>Actions</th>
        </tr>
        </thead>
        <tbody>
    """

    for r in rows:
        # r = (id, amount, category, note, date)
        dt = r[4] if r[4] else "-"
        table += f"""
        <tr>
            <td>{r[0]}</td>
            <td>{r[1]}</td>
            <td>{r[2]}</td>
            <td>{r[3]}</td>
            <td>{dt}</td>
            <td>
                <a class='action-link' href='/edit/{r[0]}'>Edit</a> |
                <a class='action-link' href='/delete/{r[0]}'>Delete</a>
            </td>
        </tr>
        """

    table += "</tbody></table>"

    return render_page("view.html", table)

# ---------- EDIT PAGE ----------
@app.route("/edit/<int:id>")
def edit_expense(id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, amount, category, note, date FROM expenses WHERE id=?", (id,))
    row = cur.fetchone()
    conn.close()

    # default values if something missing
    amount = row[1] if row and len(row) > 1 else ""
    category = row[2] if row and len(row) > 2 else ""
    note = row[3] if row and len(row) > 3 else ""
    expense_date = row[4] if row and len(row) > 4 and row[4] else date.today().isoformat()

    html = f"""
    <h2>Edit Expense</h2>

    <div class="form-container">
    <form action="/update/{id}" method="POST" class="form-box">

        <label>Amount:</label>
        <input type="number" step="0.01" name="amount" value="{amount}">

        <label>Category:</label>
        <select name="category">
            <option {'selected' if category=='Food' else ''}>Food</option>
            <option {'selected' if category=='Travel' else ''}>Travel</option>
            <option {'selected' if category=='Shopping' else ''}>Shopping</option>
            <option {'selected' if category=='Bills' else ''}>Bills</option>
            <option {'selected' if category=='Health' else ''}>Health</option>
            <option {'selected' if category=='Other' else ''}>Other</option>
        </select>

        <label>Note:</label>
        <input type="text" name="note" value="{note}">

        <label>Date:</label>
        <input type="date" name="date" value="{expense_date}">

        <button type="submit">Update</button>
    </form>
    </div>
    """

    return render_page("view.html", html)

# ---------- UPDATE EXPENSE ----------
@app.route("/update/<int:id>", methods=["POST"])
def update_expense(id):
    amount = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    note = request.form.get("note", "").strip()
    expense_date = request.form.get("date", "").strip()
    if not expense_date:
        expense_date = date.today().isoformat()

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "UPDATE expenses SET amount=?, category=?, note=?, date=? WHERE id=?",
        (amount, category, note, expense_date, id)
    )
    conn.commit()
    conn.close()

    return redirect("/view")

# ---------- DELETE ----------
@app.route("/delete/<int:id>")
def delete_expense(id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/view")

if __name__ == "__main__":
    app.run(debug=True)
