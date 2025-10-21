from flask import Flask, request, jsonify, render_template, redirect, url_for
import os
import mysql.connector
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# ---------------- DATABASE CONNECTION ----------------
db = mysql.connector.connect(
    host=os.getenv("host"),
    user=os.getenv("user"),
    password=os.getenv("password"),
    database=os.getenv("database")
)
cursor = db.cursor(dictionary=True)


# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return redirect(url_for("login"))

# Login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return redirect(url_for("dashboard"))
    return render_template("login.html")

# Dashboard page
@app.route("/dashboard")
def dashboard():
    cursor.execute("SELECT * FROM tasks WHERE status='todo'")
    todo = cursor.fetchall()
    cursor.execute("SELECT * FROM tasks WHERE status='in_progress'")
    in_progress = cursor.fetchall()
    cursor.execute("SELECT * FROM tasks WHERE status='completed'")
    completed = cursor.fetchall()

    return render_template(
        "StudentTaskTracker.html",
        todo=todo,
        in_progress=in_progress,
        completed=completed,
        board_id=1
    )

# Archive page
@app.route("/archive")
def archive():
    cursor.execute("SELECT DISTINCT board_id FROM archived_tasks ORDER BY board_id DESC")
    boards = cursor.fetchall()
    return render_template("archive.html", boards=boards)

# Trash, About, Contact pages
@app.route("/trash")
def trash():
    return render_template("trash.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

# ---------------- TASK MANAGEMENT ----------------

@app.route("/add_task", methods=["POST"])
def add_task():
    data = request.get_json()
    description = data.get("description")
    status = data.get("status", "todo")
    board_id = data.get("board_id", 1)

    cursor.execute(
        "INSERT INTO tasks (title, description, status, board_id) VALUES (%s,%s,%s,%s)",
        (description, description, status, board_id)
    )
    db.commit()
    inserted_id = cursor.lastrowid
    return jsonify({"message": "Task added", "inserted_id": inserted_id})

@app.route("/move_task", methods=["POST"])
def move_task():
    data = request.get_json()
    task_id = data.get("id")
    to_status = data.get("to")
    cursor.execute("UPDATE tasks SET status=%s WHERE id=%s", (to_status, task_id))
    db.commit()
    return jsonify({"message": "Task moved successfully"})

@app.route("/delete_task", methods=["POST"])
def delete_task():
    data = request.get_json()
    task_id = data.get("id")
    cursor.execute("DELETE FROM tasks WHERE id=%s", (task_id,))
    db.commit()
    return jsonify({"message": "Task deleted"})

# ---------------- NEW BOARD ----------------
@app.route("/new_board", methods=["POST"])
def new_board():
    # Get next archive board_id
    cursor.execute("SELECT IFNULL(MAX(board_id),0)+1 AS new_board_id FROM archived_tasks")
    new_board_id = cursor.fetchone()['new_board_id']

    # Archive current tasks
    cursor.execute("SELECT title, description, status FROM tasks")
    tasks = cursor.fetchall()
    for task in tasks:
        cursor.execute(
            "INSERT INTO archived_tasks (title, description, status, board_id) VALUES (%s,%s,%s,%s)",
            (task['title'], task['description'], task['status'], new_board_id)
        )

    # Clear tasks from dashboard
    cursor.execute("DELETE FROM tasks")
    db.commit()

    return jsonify({"message": "New board created and archived!", "board_id": new_board_id})

# ---------------- ARCHIVED TASKS ----------------

@app.route("/archived_board/<int:board_id>")
def archived_board(board_id):
    cursor.execute("SELECT * FROM archived_tasks WHERE board_id=%s", (board_id,))
    tasks = cursor.fetchall()
    todo = [t for t in tasks if t['status'] == 'todo']
    in_progress = [t for t in tasks if t['status'] == 'in_progress']
    completed = [t for t in tasks if t['status'] == 'completed']

    return render_template(
        "archived_board.html",
        todo=todo,
        in_progress=in_progress,
        completed=completed,
        board_id=board_id
    )

@app.route("/add_archived_task", methods=["POST"])
def add_archived_task():
    data = request.get_json()
    description = data.get("description")
    status = data.get("status", "todo")
    board_id = data.get("board_id")

    cursor.execute(
        "INSERT INTO archived_tasks (title, description, status, board_id) VALUES (%s,%s,%s,%s)",
        (description, description, status, board_id)
    )
    db.commit()
    inserted_id = cursor.lastrowid
    return jsonify({"message": "Task added", "inserted_id": inserted_id})

@app.route("/update_archived_task", methods=["POST"])
def update_archived_task():
    data = request.get_json()
    task_id = data.get("id")
    new_status = data.get("status")
    new_desc = data.get("description")

    cursor.execute(
        "UPDATE archived_tasks SET status=%s, description=%s WHERE id=%s",
        (new_status, new_desc, task_id)
    )
    db.commit()
    return jsonify({"message": "Task updated"})

@app.route("/delete_archived_task", methods=["POST"])
def delete_archived_task():
    data = request.get_json()
    task_id = data.get("id")
    cursor.execute("DELETE FROM archived_tasks WHERE id=%s", (task_id,))
    db.commit()
    return jsonify({"message": "Task deleted"})

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
