import sqlite3

DB_FILE = "ecommerce.db"

def setup_database():
    """Create tables for users, customers, products, orders, etc."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
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
            ono TEXT PRIMARY KEY,
            cid TEXT NOT NULL,
            sessionNo TEXT,
            odate TEXT,
            shipping_address TEXT,
            FOREIGN KEY (cid) REFERENCES customers(cid)
        );

        CREATE TABLE orderlines (
            ono TEXT,
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


def execute_query(sql, params=()):
    """Execute a SELECT query and return results as dictionaries."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def execute_command(sql, params=()):
    """Execute INSERT/UPDATE/DELETE safely and return lastrowid."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id
