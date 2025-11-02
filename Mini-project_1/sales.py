from utilities import execute_query, get_connection
from datetime import datetime, timedelta


def sales_menu(user):
    conn = get_connection()
    print(f"\n=== Welcome, Salesperson {user['uid']} ===")

    while True:
        print("\n1. View/Update Product")
        print("2. Weekly Sales Report")
        print("3. Top-Selling Products")
        print("4. Logout")

        choice = input("Select an option: ").strip()
        if choice == "1":
            update_product(conn)
        elif choice == "2":
            weekly_sales_report(conn)
        elif choice == "3":
            top_selling_products(conn)
        elif choice == "4":
            print("Logging out...\n")
            break
        else:
            print(" Invalid choice. Try again.")


def update_product(conn):
    pid = input("Enter product ID: ").strip()
    product = execute_query(conn, "SELECT * FROM products WHERE pid=?", (pid,), fetchone=True)
    if not product:
        print("Invalid product ID.")
        return

    print(f"Current price: {product['price']}, stock: {product['stock_count']}")
    new_price = input("Enter new price (blank to skip): ").strip()
    new_stock = input("Enter new stock count (blank to skip): ").strip()

    if new_price:
        execute_query(conn, "UPDATE products SET price=? WHERE pid=?", (float(new_price), pid))
    if new_stock:
        execute_query(conn, "UPDATE products SET stock_count=? WHERE pid=?", (int(new_stock), pid))
    print(" Product updated.")


def weekly_sales_report(conn):
    since = datetime.now() - timedelta(days=7)
    print(f"\n--- Weekly Sales Report (Since {since.date()}) ---")

    stats = execute_query(conn, """
        SELECT COUNT(DISTINCT o.ono) AS total_orders,
               COUNT(DISTINCT ol.pid) AS products_sold,
               COUNT(DISTINCT o.cid) AS unique_customers,
               AVG(ol.qty * ol.uprice) AS avg_spent,
               SUM(ol.qty * ol.uprice) AS total_sales
        FROM orders o
        JOIN orderlines ol ON o.ono = ol.ono
        WHERE o.odate >= ?
    """, (since,), fetchone=True)

    if not stats or stats["total_orders"] == 0:
        print("No sales in this period.")
        return

    print(f"Total Orders: {stats['total_orders']}")
    print(f"Distinct Products Sold: {stats['products_sold']}")
    print(f"Unique Customers: {stats['unique_customers']}")
    print(f"Average Amount per Customer: ${stats['avg_spent']:.2f}")
    print(f"Total Sales: ${stats['total_sales']:.2f}")


def top_selling_products(conn):
    print("\n--- Top Selling Products ---")
    top_orders = execute_query(conn, """
        SELECT p.name, COUNT(DISTINCT ol.ono) AS order_count
        FROM orderlines ol JOIN products p ON ol.pid = p.pid
        GROUP BY p.pid
        ORDER BY order_count DESC LIMIT 3
    """, fetch=True)
    print("By Orders:")
    for row in top_orders:
        print(f"{row['name']} - {row['order_count']} orders")

    print("\nBy Views:")
    top_views = execute_query(conn, """
        SELECT p.name, COUNT(v.pid) AS views
        FROM viewedProduct v JOIN products p ON v.pid = p.pid
        GROUP BY p.pid
        ORDER BY views DESC LIMIT 3
    """, fetch=True)
    for row in top_views:
        print(f"{row['name']} - {row['views']} views")
