from db import execute_query, get_connection
from datetime import datetime


def customer_menu(user):
    conn = get_connection()
    cid = user["uid"]
    print(f"\n=== Welcome, Customer {cid} ===")

    while True:
        print("\n1. Search Products")
        print("2. View Cart")
        print("3. My Orders")
        print("4. Logout")

        choice = input("Select an option: ").strip()

        if choice == "1":
            search_products(conn, cid)
        elif choice == "2":
            view_cart(conn, cid)
        elif choice == "3":
            view_orders(conn, cid)
        elif choice == "4":
            print("Logging out...\n")
            break
        else:
            print("Invalid choice. Try again.")


def search_products(conn, cid):
    keyword = input("\nEnter keyword to search: ").strip().lower()
    if not keyword:
        print("Keyword cannot be empty.")
        return

    # Record the search
    execute_query(conn, "INSERT INTO search(cid, sessionNo, ts, query) VALUES (?, ?, ?, ?)",
                  (cid, 1, datetime.now(), keyword))

    # Perform search
    rows = execute_query(conn, """
        SELECT pid, name, category, price, stock_count, descr
        FROM products
        WHERE LOWER(name) LIKE ? OR LOWER(descr) LIKE ?
        LIMIT 5
    """, (f"%{keyword}%", f"%{keyword}%"), fetch=True)

    if not rows:
        print("No products found.")
        return

    for row in rows:
        product = dict(row)
        print(f"\n{product['pid']}: {product['name']} - ${product['price']} ({product['stock_count']} in stock)")
        print(f"Description: {product['descr']}")

    pid = input("\nEnter Product ID to view details or press Enter to go back: ").strip()
    if pid:
        view_product(conn, cid, pid)


def view_product(conn, cid, pid):
    product = execute_query(conn, "SELECT * FROM products WHERE pid = ?", (pid,), fetchone=True)
    if not product:
        print("Invalid product ID.")
        return

    print(f"\n--- {product['name']} ---")
    print(f"Category: {product['category']}")
    print(f"Price: ${product['price']}")
    print(f"Stock: {product['stock_count']}")
    print(f"Description: {product['descr']}")

    # Record view
    execute_query(conn, "INSERT INTO viewedProduct(cid, sessionNo, ts, pid) VALUES (?, ?, ?, ?)",
                  (cid, 1, datetime.now(), pid))

    choice = input("\nAdd to cart? (y/n): ").strip().lower()
    if choice == "y":
        add_to_cart(conn, cid, pid)


def add_to_cart(conn, cid, pid):
    qty = int(input("Enter quantity: "))
    stock = execute_query(conn, "SELECT stock_count FROM products WHERE pid = ?", (pid,), fetchone=True)
    if not stock or qty <= 0 or qty > stock["stock_count"]:
        print("Invalid quantity.")
        return

    existing = execute_query(conn, "SELECT qty FROM cart WHERE cid=? AND sessionNo=1 AND pid=?", (cid, pid), fetchone=True)
    if existing:
        new_qty = existing["qty"] + qty
        execute_query(conn, "UPDATE cart SET qty=? WHERE cid=? AND sessionNo=1 AND pid=?",
                      (new_qty, cid, pid))
    else:
        execute_query(conn, "INSERT INTO cart(cid, sessionNo, pid, qty) VALUES (?, 1, ?, ?)",
                      (cid, pid, qty))
    print("Added to cart.")


def view_cart(conn, cid):
    rows = execute_query(conn, """
        SELECT c.pid, p.name, p.price, c.qty, (p.price * c.qty) as total
        FROM cart c JOIN products p ON c.pid = p.pid
        WHERE c.cid = ? AND c.sessionNo = 1
    """, (cid,), fetch=True)

    if not rows:
        print("Your cart is empty.")
        return

    print("\n--- Your Cart ---")
    total = 0
    for row in rows:
        r = dict(row)
        total += r["total"]
        print(f"{r['pid']} - {r['name']} | {r['qty']} x ${r['price']} = ${r['total']:.2f}")

    print(f"Total: ${total:.2f}")
    choice = input("\nProceed to checkout? (y/n): ").strip().lower()
    if choice == "y":
        checkout(conn, cid, total)


def checkout(conn, cid, total):
    address = input("Enter shipping address: ").strip()
    if not address:
        print("Address required.")
        return

    confirm = input(f"Confirm checkout for ${total:.2f}? (y/n): ").strip().lower()
    if confirm != "y":
        return

    execute_query(conn, "INSERT INTO orders(cid, sessionNo, odate, shipping_address) VALUES (?, 1, ?, ?)",
                  (cid, datetime.now(), address))
    ono = execute_query(conn, "SELECT last_insert_rowid() AS id", fetchone=True)["id"]

    items = execute_query(conn, "SELECT pid, qty FROM cart WHERE cid=? AND sessionNo=1", (cid,), fetch=True)
    for item in items:
        pid, qty = item["pid"], item["qty"]
        price = execute_query(conn, "SELECT price FROM products WHERE pid=?", (pid,), fetchone=True)["price"]
        execute_query(conn, "INSERT INTO orderlines(ono, lineNo, pid, qty, uprice) VALUES (?, ?, ?, ?, ?)",
                      (ono, 1, pid, qty, price))
        execute_query(conn, "UPDATE products SET stock_count = stock_count - ? WHERE pid=?", (qty, pid))

    execute_query(conn, "DELETE FROM cart WHERE cid=? AND sessionNo=1", (cid,))
    print("✅ Order placed successfully!")


def view_orders(conn, cid):
    orders = execute_query(conn, "SELECT * FROM orders WHERE cid=? ORDER BY odate DESC", (cid,), fetch=True)
    if not orders:
        print("No past orders found.")
        return

    for order in orders:
        print(f"\nOrder #{order['ono']} | Date: {order['odate']} | Ship to: {order['shipping_address']}")
        lines = execute_query(conn, """
            SELECT p.name, p.category, ol.qty, ol.uprice, (ol.qty*ol.uprice) as total
            FROM orderlines ol JOIN products p ON ol.pid = p.pid
            WHERE ol.ono=?
        """, (order["ono"],), fetch=True)
        grand = sum(row["total"] for row in lines)
        for row in lines:
            print(f"  - {row['name']} ({row['category']}) x{row['qty']} = ${row['total']:.2f}")
        print(f"  → Grand Total: ${grand:.2f}")
