from db import get_connection, execute_query, execute_command, close
from datetime import datetime, timedelta

# Menu for salesperson to view/update products and access sales reports
def sales_menu(user):
    conn = get_connection()
    print(f"\nWelcome, Salesperson {user['uid']}")

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
            print("Invalid choice. Try again.")

    close(conn)

# Let salesperson update price or stock details of an existing product
def update_product(conn):
    pid = input("Enter product ID: ").strip()
    product = execute_query(conn,
                            "SELECT * FROM products WHERE pid=?",
                            (pid,),
                            fetchone=True)
    if not product:
        print("Invalid product ID.")
        return

    print(f"Current price: {product['price']}, stock: {product['stock_count']}")

    new_price = input("Enter new price (blank to skip): ").strip()
    new_stock = input("Enter new stock count (blank to skip): ").strip()
    try:
        if new_price:
            execute_command(conn,
                            "UPDATE products SET price=? WHERE pid=?",
                            (float(new_price), pid))
        if new_stock:
            execute_command(conn,
                            "UPDATE products SET stock_count=? WHERE pid=?",
                            (int(new_stock), pid))
    except ValueError:
        print("Invalid number entered. No changes made.")
        return

    print("Product information updated successfully.")

# Summarize weekly sales totals, orders, and customer activity
def weekly_sales_report(conn):
    since = datetime.now() - timedelta(days=7)
    since_str = since.strftime("%Y-%m-%d")
    print(f"\nWeekly Sales Report (Since {since_str})")

    stats = execute_query(
                            conn,
                            """
                            SELECT 
                                COUNT(DISTINCT o.ono) AS total_orders,
                                COUNT(DISTINCT ol.pid) AS products_sold,
                                COUNT(DISTINCT o.cid) AS unique_customers,
                                AVG(customer_total) AS avg_spent,
                                SUM(ol.qty * ol.uprice) AS total_sales
                            FROM orders o
                            JOIN orderlines ol ON o.ono = ol.ono
                            JOIN (
                                SELECT o.cid, SUM(ol.qty * ol.uprice) AS customer_total
                                FROM orders o
                                JOIN orderlines ol ON o.ono = ol.ono
                                WHERE o.odate >= ?
                                GROUP BY o.cid
                            ) AS customer_totals ON customer_totals.cid = o.cid
                            WHERE o.odate >= ?;
                            """,
                            (since_str, since_str),  
                            fetchone=True
                        )

    if not stats or stats["total_orders"] == 0:
        print("No sales in this period.")
        return

    print(f"Total Orders: {stats['total_orders']}")
    print(f"Distinct Products Sold: {stats['products_sold']}")
    print(f"Unique Customers: {stats['unique_customers']}")
    print(f"Average Amount per Customer: ${stats['avg_spent']:.2f}")
    print(f"Total Sales: ${stats['total_sales']:.2f}")

# Shows top-ranked products based on orders and product views
def top_selling_products(conn):
    print("\nTop Selling Products")
    print("\nBy Orders:")
    rows = execute_query(conn, """
        SELECT p.name, COUNT(DISTINCT ol.ono) AS order_count
        FROM orderlines ol
        JOIN products p ON ol.pid = p.pid
        GROUP BY p.pid
        ORDER BY order_count DESC
    """, fetch=True)

    if not rows:
        print("No orders yet.")
        return

    third_count = rows[min(2, len(rows) - 1)]['order_count']

    for row in rows:
        if row['order_count'] >= third_count:
            print(f"{row['name']} - {row['order_count']} orders")

    print("\nBy Views:")
    rows = execute_query(conn, """
        SELECT p.name, COUNT(v.pid) AS views
        FROM viewedProduct v
        JOIN products p ON v.pid = p.pid
        GROUP BY p.pid
        ORDER BY views DESC
    """, fetch=True)

    if not rows:
        print("No views yet.")
        return

    third_count = rows[min(2, len(rows) - 1)]['views']

    for row in rows:
        if row['views'] >= third_count:
            print(f"{row['name']} - {row['views']} views")

