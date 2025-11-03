import sqlite3

DB_FILE = None

def set_db_file(file_path):
    global DB_FILE
    DB_FILE = file_path


def get_connection():
    if not DB_FILE:
        raise ValueError("Database wrong")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def setup_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript('''
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS customers;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS orderlines;
        DROP TABLE IF EXISTS sessions;
        DROP TABLE IF EXISTS viewedProduct;
        DROP TABLE IF EXISTS search;
        DROP TABLE IF EXISTS cart;

        CREATE TABLE users (
            uid TEXT PRIMARY KEY,
            pwd TEXT NOT NULL,
            role TEXT CHECK(role IN ('customer', 'sales')) NOT NULL
        );

        CREATE TABLE customers (
            cid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        );

        CREATE TABLE products (
            pid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            price REAL NOT NULL,
            stock_count INTEGER NOT NULL,
            descr TEXT
        );

        CREATE TABLE orders (
            ono INTEGER PRIMARY KEY AUTOINCREMENT,
            cid TEXT NOT NULL,
            sessionNo TEXT,
            odate TEXT,
            shipping_address TEXT,
            FOREIGN KEY (cid) REFERENCES customers(cid)
        );

        CREATE TABLE orderlines (
            ono INTEGER,
            lineNo INTEGER,
            pid TEXT,
            qty INTEGER,
            uprice REAL,
            PRIMARY KEY (ono, lineNo),
            FOREIGN KEY (ono) REFERENCES orders(ono),
            FOREIGN KEY (pid) REFERENCES products(pid)
        );

        CREATE TABLE sessions (
            cid TEXT,
            sessionNo TEXT,
            start_time TEXT,
            end_time TEXT,
            PRIMARY KEY (cid, sessionNo)
        );

        CREATE TABLE viewedProduct (
            cid TEXT,
            sessionNo TEXT,
            ts TEXT,
            pid TEXT,
            FOREIGN KEY (cid) REFERENCES customers(cid),
            FOREIGN KEY (pid) REFERENCES products(pid)
        );

        CREATE TABLE search (
            cid TEXT,
            sessionNo TEXT,
            ts TEXT,
            query TEXT,
            FOREIGN KEY (cid) REFERENCES customers(cid)
        );

        CREATE TABLE cart (
            cid TEXT,
            sessionNo TEXT,
            pid TEXT,
            qty INTEGER,
            PRIMARY KEY (cid, sessionNo, pid),
            FOREIGN KEY (cid) REFERENCES customers(cid),
            FOREIGN KEY (pid) REFERENCES products(pid)
        );
    ''')

    conn.commit()
    conn.close()


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
    return cursor.lastrowid
