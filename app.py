import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DB_PATH = "tasks.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            due_date TEXT,
            is_done INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_db()


@app.route("/", methods=["GET"])
def index():
    filter_status = request.args.get("status", "all")
    search_query = request.args.get("q", "").strip()

    conn = get_db_connection()
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if filter_status == "active":
        query += " AND is_done = 0"
    elif filter_status == "done":
        query += " AND is_done = 1"

    if search_query:
        query += " AND (title LIKE ? OR category LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    query += " ORDER BY is_done ASC, id DESC"
    tasks = conn.execute(query, params).fetchall()

    total_count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    done_count = conn.execute("SELECT COUNT(*) FROM tasks WHERE is_done = 1").fetchone()[0]
    conn.close()

    progress = int((done_count / total_count) * 100) if total_count > 0 else 0

    return render_template(
        "index.html",
        tasks=tasks,
        filter_status=filter_status,
        search_query=search_query,
        total_count=total_count,
        done_count=done_count,
        progress=progress,
    )


@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "一般").strip() or "一般"
    priority = request.form.get("priority", "中")
    due_date = request.form.get("due_date", "").strip()

    if title:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO tasks (title, category, priority, due_date, is_done, created_at) VALUES (?, ?, ?, ?, 0, ?)",
            (title, category, priority, due_date, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        conn.commit()
        conn.close()

    return redirect(url_for("index"))


@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle_task(task_id):
    conn = get_db_connection()
    task = conn.execute("SELECT is_done FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if task:
        new_status = 0 if task["is_done"] == 1 else 1
        conn.execute("UPDATE tasks SET is_done = ? WHERE id = ?", (new_status, task_id))
        conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)