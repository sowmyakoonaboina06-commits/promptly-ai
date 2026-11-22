
import os
import sqlite3
from datetime import datetime

import psycopg
from psycopg.rows import dict_row
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE_NAME = "promptly_history.db"


def using_postgres():
    return bool(os.getenv("DATABASE_URL"))


def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return psycopg.connect(
            database_url,
            row_factory=dict_row
        )

    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def execute_query(connection, query, parameters=()):
    if using_postgres():
        return connection.execute(
            query.replace("?", "%s"),
            parameters
        )

    return connection.execute(query, parameters)


def create_table():
    connection = get_connection()

    try:
        if using_postgres():

            connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id SERIAL PRIMARY KEY,
                    tool_name TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    generated_content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    user_id INTEGER REFERENCES users(id)
                )
            """)

            columns = connection.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'history'
            """).fetchall()

            column_names = [column["column_name"] for column in columns]

            if "user_id" not in column_names:
                connection.execute("""
                    ALTER TABLE history
                    ADD COLUMN user_id INTEGER REFERENCES users(id)
                """)

        else:

            connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    generated_content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            columns = [
                column["name"]
                for column in connection.execute(
                    "PRAGMA table_info(history)"
                ).fetchall()
            ]

            if "user_id" not in columns:
                connection.execute("""
                    ALTER TABLE history
                    ADD COLUMN user_id INTEGER REFERENCES users(id)
                """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_user_id
            ON history(user_id)
        """)

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def register_user(name, email, password):
    connection = get_connection()

    try:
        password_hash = generate_password_hash(password)

        execute_query(connection, """
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
        """, (name, email.lower(), password_hash))

        connection.commit()
        return True

    except Exception as error:
        connection.rollback()

        if using_postgres():
            if isinstance(error, psycopg.errors.UniqueViolation):
                return False
        else:
            if isinstance(error, sqlite3.IntegrityError):
                return False

        raise

    finally:
        connection.close()


def get_user_by_email(email):
    connection = get_connection()

    try:
        user = execute_query(connection, """
            SELECT * FROM users WHERE email = ?
        """, (email.lower(),)).fetchone()

        return user

    finally:
        connection.close()


def verify_password(user, password):
    return check_password_hash(user["password_hash"], password)


def save_history(user_id, tool_name, prompt, generated_content):
    connection = get_connection()

    try:
        execute_query(connection, """
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

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_history(user_id):
    connection = get_connection()

    try:
        records = execute_query(connection, """
            SELECT * FROM history
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,)).fetchall()

        return records

    finally:
        connection.close()


def delete_history(history_id, user_id):
    connection = get_connection()

    try:
        execute_query(connection, """
            DELETE FROM history
            WHERE id = ? AND user_id = ?
        """, (history_id, user_id))

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
