import sqlite3
from flask import Flask, request, redirect

app = Flask(__name__)

DB = "expenses.db"


# ---------- Helper: Render a Page ----------
def render_page(page_file, content=""):
    with open("pages/layout_start.html") as f:
        start = f.read()

    with open(f"pages/{page_file}") as f:
        page = f.read()

    with open("pages/layout_end.html") as f:
        end = f.read()

    return start + page.replace("{{content}}", content) + end


# ---------- HOME ----------
@app.route("/")
def home():
    return render_page("home.html")


# ---------- ADD PAGE ----------
@app.route("/add")
def add_page():
    return render_page("add.html")


# ---------- SAVE EXPENSE ----------
@app.route("/save", methods=["POST"])
def save_expense():
    amount = request.form["amount"]
    category = request.form["category"]
    custom = request.form.get("custom_category")

    if category == "Other" and custom:
        category = custom

    note = request.form["note"]

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO expenses (amount, category, note) VALUES (?, ?, ?)",
        (amount, category, note),
    )

    conn.commit()
    conn.close()

    return redirect("/view")
# ---------- VIEW EXPENSE ----------
@app.route("/view")
def view_page():
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, amount, category, note FROM expenses")
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
            <th>Actions</th>
        </tr>
        </thead>
        <tbody>
    """

    for r in rows:
        table += f"""
        <tr>
            <td>{r[0]}</td>
            <td>{r[1]}</td>
            <td>{r[2]}</td>
            <td>{r[3]}</td>
            <td>
                <a class='action-link' href='/edit/{r[0]}'>Edit</a> |
                <a class='action-link' href='/delete/{r[0]}'>Delete</a>
            </td>
        </tr>
        """

    table += "</tbody></table>"

    return render_page("view.html", table)

# ---------- EDIT EXPENSE ----------
@app.route("/edit/<int:id>")
def edit_expense(id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM expenses WHERE id=?", (id,))
    row = cur.fetchone()
    conn.close()

    html = f"""
    <h2>Edit Expense</h2>

    <form action="/update/{id}" method="POST" class="form-box">

        <label>Amount:</label>
        <input type="number" step="0.01" name="amount" value="{row[1]}">

        <label>Category:</label>
        <select name="category">
            <option {'selected' if row[2]=='Food' else ''}>Food</option>
            <option {'selected' if row[2]=='Travel' else ''}>Travel</option>
            <option {'selected' if row[2]=='Shopping' else ''}>Shopping</option>
            <option {'selected' if row[2]=='Bills' else ''}>Bills</option>
            <option {'selected' if row[2]=='Health' else ''}>Health</option>
            <option {'selected' if row[2]=='Other' else ''}>Other</option>
        </select>

        <label>Note:</label>
        <input type="text" name="note" value="{row[3]}">

        <button type="submit">Update</button>
    </form>
    """

    return render_page("view.html", html)

# ---------- UPDATE EXPENSE ----------
@app.route("/update/<int:id>", methods=["POST"])
def update_expense(id):
    amount = request.form["amount"]
    category = request.form["category"]
    note = request.form["note"]

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "UPDATE expenses SET amount=?, category=?, note=? WHERE id=?",
        (amount, category, note, id)
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
