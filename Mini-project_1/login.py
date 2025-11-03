import hashlib
from db import get_connection, execute_query, execute_command

def hash_password(password):
    """Return SHA-256 hash of the password."""
    alg = hashlib.sha256()
    alg.update(password.encode("utf-8"))
    return alg.hexdigest()


def login():
    """Login a user by verifying password hash."""
    uid = input("Enter user ID: ").strip()
    pwd = input("Enter password: ")

    hashed = hash_password(pwd)

    conn = get_connection()  # ✅ open connection

    res = execute_query(
        conn,
        "SELECT * FROM users WHERE uid = ? AND pwd = ?",
        (uid, hashed),
        fetch=True
    )

    conn.close()  # ✅ close connection

    if not res:
        print("Invalid user ID or password.")
        return None

    return dict(res[0])


def register():
    """Register a new customer with hashed password."""
    print("\n=== New Customer Registration ===")
    name = input("Full name: ").strip()
    email = input("Email: ").strip()
    pwd = input("Password: ").strip()

    conn = get_connection()  # ✅ open connection

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

    conn.close()  # ✅ close connection

    print(f"Registration successful! Your user ID is {new_uid}")


def generate_new_id(conn, table, column, prefix="X"):
    """Generate a new ID with prefix and 3-digit number (e.g., U001)."""
    res = execute_query(conn, f"SELECT {column} FROM {table}", fetch=True)
    existing = [r[column] for r in res if r[column].startswith(prefix)]
    nums = [int(x[len(prefix):]) for x in existing] if existing else [0]
    return f"{prefix}{max(nums)+1:03d}"
