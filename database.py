
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE_NAME = "promptly_history.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_table():
    connection = get_connection()
    cursor = connection.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    """)

    # History table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_name TEXT NOT NULL,
            prompt TEXT NOT NULL,
            generated_content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Add user_id to an existing history table if needed
    columns = [
        column["name"]
        for column in cursor.execute("PRAGMA table_info(history)").fetchall()
    ]

    if "user_id" not in columns:
        cursor.execute("""
            ALTER TABLE history
            ADD COLUMN user_id INTEGER REFERENCES users(id)
        """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_history_user_id
        ON history(user_id)
    """)

    connection.commit()
    connection.close()


def register_user(name, email, password):
    connection = get_connection()

    try:
        password_hash = generate_password_hash(password)

        connection.execute("""
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
        """, (name, email.lower(), password_hash))

        connection.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        connection.close()


def get_user_by_email(email):
    connection = get_connection()

    user = connection.execute("""
        SELECT * FROM users WHERE email = ?
    """, (email.lower(),)).fetchone()

    connection.close()
    return user


def verify_password(user, password):
    return check_password_hash(user["password_hash"], password)


def save_history(user_id, tool_name, prompt, generated_content):
    connection = get_connection()

    connection.execute("""
        INSERT INTO history
        (user_id, tool_name, prompt, generated_content, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        tool_name,
        prompt,
        generated_content,
        datetime.now().strftime("%d-%m-%Y %I:%M %p")
    ))

    connection.commit()
    connection.close()


def get_history(user_id):
    connection = get_connection()

    records = connection.execute("""
        SELECT * FROM history
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    connection.close()
    return records


def delete_history(history_id, user_id):
    connection = get_connection()

    connection.execute("""
        DELETE FROM history
        WHERE id = ? AND user_id = ?
    """, (history_id, user_id))

    connection.commit()
    connection.close()
