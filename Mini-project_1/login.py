import hashlib
from db import get_connection, execute_query, execute_command
import getpass

def hash_password(password):
    """Return SHA-256 hash of the password."""
    alg = hashlib.sha256()
    alg.update(password.encode("utf-8"))
    return alg.hexdigest()


def login():
    """Login a user by verifying password hash or legacy plaintext."""
    try:
        uid = int(input("Enter user ID (integer): ").strip())
    except ValueError:
        print("User ID must be an integer.")
        return None

    pwd = getpass.getpass("Password: ")
    hashed = hash_password(pwd)

    conn = get_connection()

    # Try login with hashed password first
    result = execute_query(
        conn,
        "SELECT * FROM users WHERE uid = ? AND pwd = ?",
        (uid, hashed),
        fetch=True
    )

    # If not found, try legacy plaintext match
    if not result:
        result = execute_query(
            conn,
            "SELECT * FROM users WHERE uid = ? AND pwd = ?",
            (uid, pwd),
            fetch=True
        )

        # If found, upgrade their password to hashed
        if result:
            execute_command(
                conn,
                "UPDATE users SET pwd = ? WHERE uid = ?",
                (hashed, uid)
            )
            print("(Your password has been securely updated.)")

    conn.close()

    if not result:
        print("Invalid user ID or password.")
        return None

    return dict(result[0])

def register():
    """Register a new customer with hashed password."""
    print("\n=== New Customer Registration ===")
    name = input("Full name: ").strip()
    email = input("Email: ").strip()
    pwd = getpass.getpass("Password: ")

    conn = get_connection()

    # Check if email already exists
    exists = execute_query(conn, "SELECT * FROM customers WHERE email = ?", (email,), fetch=True)
    if exists:
        print("Email already registered.")
        conn.close()
        return

    new_uid = generate_new_id(conn, "users", "uid")
    new_cid = generate_new_id(conn, "customers", "cid")

    hashed = hash_password(pwd)

    execute_command(conn, "INSERT INTO users(uid, pwd, role) VALUES (?, ?, ?)",
                    (new_uid, hashed, "customer"))
    execute_command(conn, "INSERT INTO customers(cid, name, email) VALUES (?, ?, ?)",
                    (new_cid, name, email))

    conn.close()

    print(f"Registration successful! Your user ID is {new_uid}")


def generate_new_id(conn, table, column):
    """Generate a new integer ID by finding the max existing ID and adding 1."""
    result = execute_query(conn, f"SELECT MAX({column}) AS max_id FROM {table}", fetch=True)
    max_id = result[0]["max_id"] if result and result[0]["max_id"] is not None else 0
    return max_id + 1
