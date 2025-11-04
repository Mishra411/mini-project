import hashlib
from db import get_connection, execute_query, execute_command, close
import getpass

#Lab example: using hashlib to create a SHA-256 password hash
def hash_password(password):
    alg = hashlib.sha256()
    alg.update(password.encode("utf-8"))
    return alg.hexdigest()

# Validates user credentials and returns the matching user record.
def login():
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

    # If not found, try plaintext match
    if not result:
        result = execute_query(
            conn,
            "SELECT * FROM users WHERE uid = ? AND pwd = ?",
            (uid, pwd),
            fetch=True
        )

        # If found, upgrade the password to hashed
        if result:
            execute_command(
                conn,
                "UPDATE users SET pwd = ? WHERE uid = ?",
                (hashed, uid)
            )
            print("(Your password has been securely updated.)")

    close(conn)

    if not result:
        print("Invalid user ID or password.")
        return None

    return dict(result[0])

# Handles new user registration and stores credentials in the database.
def register():
    print("\n New Customer Registration ")
    name = input("Full name: ").strip()
    email = input("Email: ").strip()
    pwd = getpass.getpass("Password: ")

    conn = get_connection()

    exists = execute_query(conn, "SELECT * FROM customers WHERE email = ?", (email,), fetch=True)
    if exists:
        print("Email already registered.")
        close(conn)
        return

    new_uid = generate_new_id(conn, "users", "uid")
    new_cid = new_uid 

    hashed = hash_password(pwd)

    execute_command(conn, "INSERT INTO users(uid, pwd, role) VALUES (?, ?, ?)",
                    (new_uid, hashed, "customer"))
    execute_command(conn, "INSERT INTO customers(cid, name, email) VALUES (?, ?, ?)",
                    (new_cid, name, email))

    close(conn)

    print(f"Registration successful! Your user ID is {new_uid}")


def generate_new_id(conn, table, column):
    result = execute_query(conn, f"SELECT MAX({column}) AS max_id FROM {table}", fetch=True)
    if result is not None and len(result) > 0 and result[0]["max_id"] is not None:
        max_id = result[0]["max_id"]
    else:
        max_id = 0
    return max_id + 1
