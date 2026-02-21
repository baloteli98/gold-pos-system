from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import sqlite3
import csv
import os
from datetime import datetime
import tempfile

app = Flask(__name__)
CORS(app)

# Use cloud-safe path for SQLite
DB_FILE = os.environ.get("DB_FILE", "/tmp/gold_pos.db")

# ================= DATABASE SETUP =================
def init_db():
    """Initialize the database with sales table"""
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

# Initialize database on startup
init_db()

# ================= ROUTES =================

@app.route("/")
@app.route("/dashboard")
def dashboard():
    """Render the dashboard page"""
    return render_template("dashboard.html")

@app.route("/login")
def login():
    """Render the login page"""
    return render_template("login.html")

@app.route("/print")
def print_page():
    """Render the print page"""
    return render_template("print.html")

@app.route("/reports")
def reports():
    """Render the reports page"""
    return render_template("reports.html")

@app.route("/add", methods=["POST"])
def add_entry():
    """Add a new sales entry"""
    try:
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
        return jsonify({"status": "success", "message": "Entry added successfully"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/get", methods=["GET"])
def get_entries():
    """Get all sales entries, optionally filtered by branch"""
    try:
        branch = request.args.get("branch")
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        if branch:
            c.execute("SELECT * FROM sales WHERE branch=? ORDER BY timestamp DESC", (branch,))
        else:
            c.execute("SELECT * FROM sales ORDER BY timestamp DESC")
        
        rows = c.fetchall()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/delete/<int:id>", methods=["DELETE"])
def delete_entry(id):
    """Delete a single entry by ID"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM sales WHERE id=?", (id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"Entry {id} deleted"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/delete_all", methods=["POST"])
def delete_all():
    """Delete all entries"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM sales")
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "All entries deleted"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/export", methods=["GET"])
def export_csv():
    """Export all data as CSV file"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT * FROM sales ORDER BY timestamp DESC")
        rows = c.fetchall()
        conn.close()
        
        # Create CSV file in temp directory
        csv_file = os.path.join(tempfile.gettempdir(), "gold_sales.csv")
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write headers
            writer.writerow(['ID', 'Name', 'Phone', 'Grams', 'Purity %', 'Rate', 
                           'Pure Gold', 'Total', 'Branch', 'Timestamp'])
            # Write data
            writer.writerows(rows)
        
        return send_file(
            csv_file, 
            as_attachment=True, 
            download_name=f'gold_sales_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mimetype='text/csv'
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/report/<string:period>", methods=["GET"])
def report(period):
    """Get reports for daily, monthly, or all periods"""
    try:
        branch = request.args.get("branch")
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        # Base query
        query = "SELECT id, name, phone, branch, grams, percent, pure, rate, total, timestamp FROM sales"
        params = []

        # Add WHERE clauses
        where_clauses = []
        
        if branch:
            where_clauses.append("branch=?")
            params.append(branch)

        # Filter by period
        if period == "daily":
            where_clauses.append("date(timestamp)=date('now')")
        elif period == "monthly":
            where_clauses.append("strftime('%Y-%m', timestamp)=strftime('%Y-%m', 'now')")
        elif period != "all":
            conn.close()
            return jsonify({"status": "error", "message": "Invalid period"}), 400

        # Construct final query
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += " ORDER BY timestamp DESC"

        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        
        return jsonify(rows)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Serve static files
@app.route("/static/<path:filename>")
def static_files(filename):
    """Serve static files (CSS, JS)"""
    return send_file(os.path.join("static", filename))

# ================= RUN SERVER =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)