import sqlite3

DB_FILE = None

def set_db_file(file_path):
    global DB_FILE
    DB_FILE = file_path


def get_connection():
    if not DB_FILE:
        raise ValueError("Error leading Database")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    #conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def execute_query(conn, sql, params=(), fetch=False, fetchone=False):
    """
    Execute SQL safely using an existing connection.
    Use fetch=True for multiple rows, fetchone=True for a single row.
    """
    cursor = conn.cursor()
    cursor.execute(sql, params)

    if fetchone:
        return cursor.fetchone()
    elif fetch:
        return cursor.fetchall()
    else:
        conn.commit()
        return None


def execute_command(conn, sql, params=()):
    """
    Execute INSERT/UPDATE/DELETE using an existing connection.
    Returns last inserted row ID.
    """
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    

def close(conn):
    if conn:
        conn.close()
    else:
        raise Exception("Error closing connection")