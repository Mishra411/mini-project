import sqlite3

DB_FILE = None

def set_db_file(file_path):
    global DB_FILE
    DB_FILE = file_path

# Connects to the SQLite database and sets up row access by column name.
def get_connection():
    if not DB_FILE:
        raise ValueError("Error: No database file set. Call set_db_file() first.")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# Runs a SELECT query safely and returns results depending on fetch mode.
def execute_query(conn, sql, params=(), fetch=False, fetchone=False):
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        if fetchone:
            return cursor.fetchone()
        elif fetch:
            return cursor.fetchall()
        else:
            conn.commit()
            return None
    except sqlite3.Error as e:
        print("An error occurred:", e)
        conn.rollback()
        return None

# Executes INSERT, UPDATE, or DELETE commands and commits changes.
def execute_command(conn, sql, params=()):
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        conn.commit()
    except sqlite3.Error as e:
        print("An error occurred:", e)
        conn.rollback()
    
# Utility to check if a given SQL statement is complete (mainly for debugging)
def is_complete_sql(text):
    return sqlite3.complete_statement(text)

def close(conn):
    if conn:
        conn.close()
