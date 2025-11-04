import hashlib
from db import get_connection, execute_query, execute_command
import getpass

def hash_password(password):
    """Return SHA-256 hash of the password."""
    alg = hashlib.sha256()
    alg.update(password.encode("utf-8"))
    return alg.hexdigest()


def login():
    """Login a user by verifying password hash."""
    uid = input("Enter user ID: ").strip()
    pwd = getpass.getpass("Password: ")

    hashed = hash_password(pwd)

    conn = get_connection()  

    result= execute_query(
        conn,
        "SELECT * FROM users WHERE uid = ? AND pwd = ?",
        (uid, hashed),
        fetch=True
    )

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

    exists = execute_query(conn, "SELECT * FROM customers WHERE email = ?", (email,), fetch=True)
    if exists:
        print("Email already registered.")
        conn.close()
        return

    new_uid = generate_new_id(conn, "users", "uid", "U")
    new_cid = generate_new_id(conn, "customers", "cid", "C")

    hashed = hash_password(pwd)

    execute_command(conn, "INSERT INTO users(uid, pwd, role) VALUES (?, ?, ?)",
                    (new_uid, hashed, "customer"))
    execute_command(conn, "INSERT INTO customers(cid, name, email) VALUES (?, ?, ?)",
                    (new_cid, name, email))

    conn.close()  

    print(f"Registration successful! Your user ID is {new_uid}")


def generate_new_id(conn, table, column, prefix="X"):
    """Generate a new ID with prefix and 3-digit number (e.g., U001)."""
    # Get all existing IDs from the table
    result = execute_query(conn, f"SELECT {column} FROM {table}", fetch=True)
    # Extract numeric parts of IDs that start with the prefix
    existing = []
    for r in result:
        if r[column].startswith(prefix):
            num_part = r[column][len(prefix):]
            existing.append(int(num_part))
    # Find the maximum number or use 0 if none exist
    if existing:
        max_num = max(existing)
    else:
        max_num = 0
    # Return new ID with prefix and 3 digits
    new_id = f"{prefix}{max_num + 1:03d}"
    return new_id

