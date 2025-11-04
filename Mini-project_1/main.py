import sys
import os
from db import set_db_file
from login import login, register
from customer import customer_menu
from sales import sales_menu

def main():
    db_file = "madcadfvadf.db"
    if len(sys.argv) > 1:
        db_file = sys.argv[1]

    set_db_file(db_file)

    print("=== Welcome to the E-Commerce System ===")

    while True:
        print("\n1. Login")
        print("2. Register")
        print("3. Exit")
        choice = input("Select an option: ").strip()

        if choice == "1":
            user = login()
            if user:
                print(f"\nLogged in as {user['uid']} ({user['role']})")
                if user['role'] == 'customer':
                    customer_menu(user)
                elif user['role'] == 'sales':
                    sales_menu(user)
        elif choice == "2":
            register()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
