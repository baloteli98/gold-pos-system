from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import sqlite3
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

# Use cloud-safe path for SQLite
DB_FILE = os.environ.get("DB_FILE", "/tmp/gold_pos.db")

# ================= DATABASE SETUP =================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            grams REAL NOT NULL,
            percent REAL NOT NULL,
            rate REAL NOT NULL,
            pure REAL NOT NULL,
            total REAL NOT NULL,
            branch TEXT DEFAULT 'Main',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ================= ROUTES =================

# Dashboard
@app.route("/")
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# Add entry
@app.route("/add", methods=["POST"])
def add_entry():
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO sales (name, phone, grams, percent, rate, pure, total, branch)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['name'], data['phone'], data['grams'], data['percent'],
        data['rate'], data['pure'], data['total'], data.get('branch', 'Main')
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"}), 201

# Get entries
@app.route("/get", methods=["GET"])
def get_entries():
    branch = request.args.get("branch")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if branch:
        c.execute("SELECT * FROM sales WHERE branch=?", (branch,))
    else:
        c.execute("SELECT * FROM sales")
    rows = c.fetchall()
    conn.close()
    return jsonify(rows)

# Delete single entry
@app.route("/delete/<int:id>", methods=["DELETE"])
def delete_entry(id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM sales WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

# Delete all entries
@app.route("/delete_all", methods=["POST"])
def delete_all():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM sales")
    conn.commit()
    conn.close()
    return jsonify({"status": "all deleted"})

# Export Excel
@app.route("/export", methods=["GET"])
def export_excel():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM sales", conn)
    conn.close()
    excel_file = "/tmp/gold_sales.xlsx"  # cloud-safe path
    df.to_excel(excel_file, index=False)
    return send_file(excel_file, as_attachment=True)

# Reports (daily, monthly, all)
@app.route("/report/<string:period>", methods=["GET"])
def report(period):
    branch = request.args.get("branch")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    query = "SELECT id, name, phone, branch, grams, percent, pure, rate, total, timestamp FROM sales"
    params = []

    # Filter branch
    if branch:
        query += " WHERE branch=?"
        params.append(branch)

    # Filter period
    if period == "daily":
        if params:
            query += " AND date(timestamp)=date('now')"
        else:
            query += " WHERE date(timestamp)=date('now')"
    elif period == "monthly":
        if params:
            query += " AND strftime('%Y-%m', timestamp)=strftime('%Y-%m', 'now')"
        else:
            query += " WHERE strftime('%Y-%m', timestamp)=strftime('%Y-%m', 'now')"
    elif period != "all":
        conn.close()
        return jsonify({"status": "error", "message": "Invalid period"}), 400

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return jsonify(rows)

# Serve static files
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_file(os.path.join("static", filename))

# ================= RUN SERVER =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)