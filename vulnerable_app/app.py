from pathlib import Path
import sqlite3

from flask import Flask, flash, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
DATABASE = INSTANCE_DIR / "lab2.sqlite3"

app = Flask(__name__)
app.config["SECRET_KEY"] = "local-lab-only-change-me"


def get_db():
    INSTANCE_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS posts (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   title TEXT NOT NULL,
                   body TEXT NOT NULL,
                   is_private INTEGER NOT NULL DEFAULT 0
               )"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS comments (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   author TEXT NOT NULL,
                   content TEXT NOT NULL
               )"""
        )
        count = db.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        if count == 0:
            db.executemany(
                "INSERT INTO posts (title, body, is_private) VALUES (?, ?, ?)",
                [
                    (
                        "Введение во Flask",
                        "Flask — небольшой веб-фреймворк для Python.",
                        0,
                    ),
                    (
                        "Безопасность веб-приложений",
                        "Используйте параметризованные запросы и контекстное экранирование.",
                        0,
                    ),
                    (
                        "Служебная запись для лабораторной",
                        "FLAG{SQL_INJECTION_DEMO_ONLY}",
                        1,
                    ),
                ],
            )


@app.route("/", methods=["GET"])
def index():
    with get_db() as db:
        comments = db.execute(
            "SELECT author, content FROM comments ORDER BY id DESC"
        ).fetchall()
    return render_template("index.html", comments=comments)


@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "")

    # УЯЗВИМОСТЬ №1 (SQL Injection): пользовательский ввод вставляется
    # непосредственно в SQL-строку. Не используйте такой подход в реальных системах.
    sql = (
        "SELECT title, body, is_private FROM posts "
        f"WHERE is_private = 0 AND title LIKE '%{query}%'"
    )

    with get_db() as db:
        results = db.execute(sql).fetchall()

    return render_template("search.html", query=query, results=results)


@app.route("/comment", methods=["POST"])
def add_comment():
    author = request.form.get("author", "Аноним").strip() or "Аноним"
    content = request.form.get("content", "").strip()
    if not content:
        flash("Комментарий не должен быть пустым.")
        return redirect(url_for("index"))

    with get_db() as db:
        db.execute(
            "INSERT INTO comments (author, content) VALUES (?, ?)",
            (author[:40], content[:1000]),
        )
    flash("Комментарий добавлен.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    # Доступ только с этого компьютера. Не меняйте host на 0.0.0.0.
    app.run(host="127.0.0.1", port=5000, debug=False)
