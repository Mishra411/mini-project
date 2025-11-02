import hashlib
from db import execute_query, execute_command

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
    res = execute_query(
        "SELECT * FROM users WHERE uid = ? AND pwd = ?", (uid, hashed)
    )

    if not res:
        print("Invalid user ID or password.")
        return None

    return dict(res[0])


def register():
    """Register a new customer with hashed password."""
    print("\n=== New Customer Registration ===")
    name = input("Full name: ").strip()
    email = input("Email: ").strip()
    pwd = input("Password: ") 

    exists = execute_query("SELECT * FROM customers WHERE email = ?", (email,))
    if exists:
        print(" Email already registered.")
        return

    new_uid = generate_new_id("users", "uid", "U")
    new_cid = generate_new_id("customers", "cid", "C")

    hashed = hash_password(pwd)
    
    execute_command(
        "INSERT INTO users(uid, pwd, role) VALUES (?, ?, ?)",
        (new_uid, hashed, "customer")
    )
    execute_command(
        "INSERT INTO customers(cid, name, email) VALUES (?, ?, ?)",
        (new_cid, name, email)
    )

    print(f"Registration successful! Your user ID is {new_uid}")

//////
def generate_new_id(table, column, prefix="X"):
    """Generate a new ID with prefix and 3-digit number (e.g., U001)."""
    res = execute_query(f"SELECT {column} FROM {table}")
    existing = [r[column] for r in res if r[column].startswith(prefix)]
    nums = [int(x[len(prefix):]) for x in existing] if existing else [0]
    return f"{prefix}{max(nums)+1:03d}"
