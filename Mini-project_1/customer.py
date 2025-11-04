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
            close_session(conn, cid, session_no)
            print("Logging out...\n")
            break
        else:
            print("Invalid choice. Try again.")

    conn.close()


def get_session_no(conn, cid):
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
    conn.commit()
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
    conn.commit()




def view_cart(conn, cid, session_no):
    while True:
        rows = execute_query(
            conn,
            """
            SELECT c.pid, p.name, p.price, c.qty, (p.price * c.qty) AS total, p.stock_count
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

        print("\nOptions:")
        print("1. Update Quantity")
        print("2. Remove Product")
        print("3. Proceed to Checkout")
        print("4. Go Back")
        choice = input("Select an option: ").strip()

        if choice == "1":
            pid = input("Enter Product ID to update: ").strip()
            product = None
            for r in rows:
                if str(r["pid"]) == pid:
                    product = r
                    break

            if not product:
                print("Invalid Product ID.")
                continue

            try:
                new_qty = int(input("Enter new quantity: ").strip())
            except ValueError:
                print("Invalid quantity.")
                continue

            if new_qty <= 0:
                print("Quantity must be greater than 0.")
                continue
            if new_qty > product["stock_count"]:
                print(f"Only {product['stock_count']} units available in stock.")
                continue

            execute_command(
                conn,
                "UPDATE cart SET qty=? WHERE cid=? AND sessionNo=? AND pid=?",
                (new_qty, cid, session_no, pid)
            )
            print("Quantity updated successfully.")

        elif choice == "2":
            pid = input("Enter Product ID to remove: ").strip()
            execute_command(
                conn,
                "DELETE FROM cart WHERE cid=? AND sessionNo=? AND pid=?",
                (cid, session_no, pid)
            )
            print("Product removed from cart.")

        elif choice == "3":
            confirm = input(f"Proceed to checkout for ${total:.2f}? (y/n): ").strip().lower()
            if confirm == "y":
                checkout(conn, cid, session_no, total)
            break

        elif choice == "4":
            break
        else:
            print("Invalid choice. Please enter valid.")

# ------------------- Checkout -------------------
def generate_new_order_no(conn):
    """Generate a new unique order number."""
    row = execute_query(conn, "SELECT MAX(ono) AS max_ono FROM orders", fetchone=True)
    max_ono = row["max_ono"] if row and row["max_ono"] else 5000  # start from 5001 if no orders
    return max_ono + 1


def checkout(conn, cid, session_no, total):
    address = input("Enter shipping address: ").strip()
    if not address:
        print("Address required.")
        return

    confirm = input(f"Confirm checkout for ${total:.2f}? (y/n): ").strip().lower()
    if confirm != "y":
        return

    # Generate unique order number manually
    ono = generate_new_order_no(conn)

    # Insert into orders table
    execute_command(
        conn,
        "INSERT INTO orders(ono, cid, sessionNo, odate, shipping_address) VALUES (?, ?, ?, ?, ?)",
        (ono, cid, session_no, datetime.now(), address)
    )

    # Get items from cart
    items = execute_query(
        conn,
        "SELECT pid, qty FROM cart WHERE cid=? AND sessionNo=?",
        (cid, session_no),
        fetch=True
    )

    line_no = 1
    for item in items:
        pid, qty = item["pid"], item["qty"]
        price_row = execute_query(conn, "SELECT price FROM products WHERE pid=?", (pid,), fetchone=True)
        price = price_row["price"] if price_row else 0

        # Insert into orderlines
        execute_command(
            conn,
            "INSERT INTO orderlines(ono, lineNo, pid, qty, uprice) VALUES (?, ?, ?, ?, ?)",
            (ono, line_no, pid, qty, price)
        )

        # Update product stock
        execute_command(
            conn,
            "UPDATE products SET stock_count = stock_count - ? WHERE pid=?",
            (qty, pid)
        )

        line_no += 1

    # Clear cart
    execute_command(conn, "DELETE FROM cart WHERE cid=? AND sessionNo=?", (cid, session_no))

    print(f"Order #{ono} placed successfully!")



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

def close_session(conn, cid, session_no):
    """Set end_time of a session when customer logs out."""
    execute_command(
        conn,
        "UPDATE sessions SET end_time=? WHERE cid=? AND sessionNo=?",
        (datetime.now(), cid, session_no)
    )
