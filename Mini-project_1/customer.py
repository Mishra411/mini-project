from db import get_connection, execute_query, execute_command
from datetime import datetime

def customer_menu(user):
    conn = get_connection()
    cid = user["uid"]
    session_no = get_session_no(conn, cid)
    print(f"\n=== Welcome, Customer {cid} ===")

    while True:
        print("\n1. Search Products")
        print("2. View Cart")
        print("3. My Orders")
        print("4. Logout")

        choice = input("Select an option: ").strip()

        if choice == "1":
            search_products(conn, cid, session_no)
        elif choice == "2":
            view_cart(conn, cid, session_no)
        elif choice == "3":
            view_orders(conn, cid)
        elif choice == "4":
            print("Logging out...\n")
            break
        else:
            print("Invalid choice. Try again.")

    conn.close()


def get_session_no(conn, cid):
    """Reuse today's session if it exists, otherwise create a new one."""
    row = execute_query(
        conn,
        """
        SELECT sessionNo 
        FROM sessions 
        WHERE cid=? AND DATE(start_time)=DATE('now')
        ORDER BY sessionNo DESC 
        LIMIT 1
        """,
        (cid,),
        fetchone=True
    )
    if row:  
        return row["sessionNo"]
    last_row = execute_query(
        conn,
        "SELECT MAX(sessionNo) AS last_session FROM sessions WHERE cid=?",
        (cid,),
        fetchone=True
    )
    last = last_row["last_session"] if last_row and last_row["last_session"] else 0
    new_session_no = last + 1

    execute_command(
        conn,
        "INSERT INTO sessions(cid, sessionNo, start_time) VALUES (?, ?, ?)",
        (cid, new_session_no, datetime.now())
    )

    return new_session_no




def search_products(conn, cid, session_no):
    keyword = input("\nEnter keyword to search: ").strip().lower()
    if not keyword:
        print("Keyword cannot be empty.")
        return

    # Record the search
    execute_command(
        conn,
        "INSERT INTO search(cid, sessionNo, ts, query) VALUES (?, ?, ?, ?)",
        (cid, session_no, datetime.now(), keyword)
    )

    page = 0
    while True:
        rows = execute_query(
            conn,
            """
            SELECT pid, name, category, price, stock_count, descr
            FROM products
            WHERE LOWER(name) LIKE ? OR LOWER(descr) LIKE ?
            LIMIT 5 OFFSET ?
            """,
            (f"%{keyword}%", f"%{keyword}%", page*5),
            fetch=True
        )

        if not rows:
            if page == 0:
                print("No products found.")
            else:
                print("No more products.")
            break

        print(f"\n--- Page {page+1} ---")
        for row in rows:
            product = dict(row)
            print(f"{product['pid']}: {product['name']} - ${product['price']} ({product['stock_count']} in stock)")
            print(f"Description: {product['descr']}")

        nav = input("\nEnter Product ID to view, N for next, P for prev, Q to quit: ").strip().lower()
        if nav == "n":
            page += 1
        elif nav == "p" and page > 0:
            page -= 1
        elif nav == "q":
            break
        else:
            view_product(conn, cid, session_no, nav)



def view_product(conn, cid, session_no, pid):
    product = execute_query(
        conn,
        "SELECT * FROM products WHERE pid=?",
        (pid,),
        fetchone=True
    )
    if not product:
        print("Invalid product ID.")
        return

    print(f"\n--- {product['name']} ---")
    print(f"Category: {product['category']}")
    print(f"Price: ${product['price']}")
    print(f"Stock: {product['stock_count']}")
    print(f"Description: {product['descr']}")

    # Record view
    execute_command(
        conn,
        "INSERT INTO viewedProduct(cid, sessionNo, ts, pid) VALUES (?, ?, ?, ?)",
        (cid, session_no, datetime.now(), pid)
    )

    choice = input("\nAdd to cart? (y/n): ").strip().lower()
    if choice == "y":
        add_to_cart(conn, cid, session_no, pid)




def add_to_cart(conn, cid, session_no, pid):
    try:
        qty = int(input("Enter quantity: ").strip())
    except ValueError:
        print("Invalid quantity.")
        return

    stock_row = execute_query(
        conn,
        "SELECT stock_count FROM products WHERE pid=?",
        (pid,),
        fetchone=True
    )
    stock = stock_row["stock_count"] if stock_row else 0

    if qty <= 0 or qty > stock:
        print("Quantity unavailable")
        return

    existing = execute_query(
        conn,
        "SELECT qty FROM cart WHERE cid=? AND sessionNo=? AND pid=?",
        (cid, session_no, pid),
        fetchone=True
    )

    if existing:
        new_qty = existing["qty"] + qty
        execute_command(
            conn,
            "UPDATE cart SET qty=? WHERE cid=? AND sessionNo=? AND pid=?",
            (new_qty, cid, session_no, pid)
        )
    else:
        execute_command(
            conn,
            "INSERT INTO cart(cid, sessionNo, pid, qty) VALUES (?, ?, ?, ?)",
            (cid, session_no, pid, qty)
        )
    print("Added to cart.")




def view_cart(conn, cid, session_no):
    rows = execute_query(
        conn,
        """
        SELECT c.pid, p.name, p.price, c.qty, (p.price * c.qty) AS total
        FROM cart c JOIN products p ON c.pid = p.pid
        WHERE c.cid=? AND c.sessionNo=?
        """,
        (cid, session_no),
        fetch=True
    )

    if not rows:
        print("Your cart is empty.")
        return

    total = 0
    print("\n--- Your Cart ---")
    for row in rows:
        r = dict(row)
        total += r["total"]
        print(f"{r['pid']} - {r['name']} | {r['qty']} x ${r['price']} = ${r['total']:.2f}")

    print(f"Total: ${total:.2f}")
    choice = input("\nProceed to checkout? (y/n): ").strip().lower()
    if choice == "y":
        checkout(conn, cid, session_no, total)


# ------------------- Checkout -------------------
def checkout(conn, cid, session_no, total):
    address = input("Enter shipping address: ").strip()
    if not address:
        print("Address required.")
        return

    confirm = input(f"Confirm checkout for ${total:.2f}? (y/n): ").strip().lower()
    if confirm != "y":
        return

    execute_command(
        conn,
        "INSERT INTO orders(cid, sessionNo, odate, shipping_address) VALUES (?, ?, ?, ?)",
        (cid, session_no, datetime.now(), address)
    )
    ono = execute_query(conn, "SELECT last_insert_rowid() AS id", fetchone=True)["id"]

    items = execute_query(
        conn,
        "SELECT pid, qty FROM cart WHERE cid=? AND sessionNo=?",
        (cid, session_no),
        fetch=True
    )

    line_no = 1
    for item in items:
        pid, qty = item["pid"], item["qty"]
        price = execute_query(conn, "SELECT price FROM products WHERE pid=?", (pid,), fetchone=True)["price"]

        execute_command(
            conn,
            "INSERT INTO orderlines(ono, lineNo, pid, qty, uprice) VALUES (?, ?, ?, ?, ?)",
            (ono, line_no, pid, qty, price)
        )
        execute_command(
            conn,
            "UPDATE products SET stock_count = stock_count - ? WHERE pid=?",
            (qty, pid)
        )
        line_no += 1

    execute_command(conn, "DELETE FROM cart WHERE cid=? AND sessionNo=?", (cid, session_no))
    print("Order placed successfully!")


# ------------------- View Orders -------------------
def view_orders(conn, cid):
    page = 0
    while True:
        orders = execute_query(
            conn,
            "SELECT * FROM orders WHERE cid=? ORDER BY odate DESC LIMIT 5 OFFSET ?",
            (cid, page*5),
            fetch=True
        )
        if not orders:
            if page == 0:
                print("No past orders found.")
            else:
                print("No more orders.")
            break

        print(f"\n--- Page {page+1} ---")
        for order in orders:
            print(f"Order #{order['ono']} | Date: {order['odate']} | Ship to: {order['shipping_address']}")
            lines = execute_query(
                conn,
                """
                SELECT p.name, p.category, ol.qty, ol.uprice, (ol.qty*ol.uprice) AS total
                FROM orderlines ol JOIN products p ON ol.pid = p.pid
                WHERE ol.ono=?
                """,
                (order["ono"],),
                fetch=True
            )
            grand_total = sum(row["total"] for row in lines)
            for row in lines:
                print(f"  - {row['name']} ({row['category']}) x{row['qty']} = ${row['total']:.2f}")
            print(f"  → Grand Total: ${grand_total:.2f}")

        nav = input("\nN for next, P for prev, Q to quit: ").strip().lower()
        if nav == "n":
            page += 1
        elif nav == "p" and page > 0:
            page -= 1
        elif nav == "q":
            break
