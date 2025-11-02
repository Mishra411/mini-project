import sqlite3
import hashlib
from getpass import getpass


def get_connection(db_name="ecommerce.db"):
    """Return a SQLite connection with Row factory enabled."""
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn


def execute_query(conn, query, params=(), fetch=False, fetchone=False):
    """Executes a query safely and optionally returns results."""
    cur = conn.cursor()
    cur.execute(query, params)
    if fetch:
        return cur.fetchall()
    if fetchone:
        return cur.fetchone()
    conn.commit()
    return None


def hash_password(password: str) -> str:
    """Hashes a password with SHA256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def input_password(prompt="Password: "):
    """Secure password input."""
    return getpass(prompt)


def print_rows(rows):
    """Helper to print sqlite3.Row results as readable dicts."""
    for row in rows:
        print(dict(row))
