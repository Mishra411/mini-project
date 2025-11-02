import sqlite3


def setup_database():
    """Creates the employees and tasks tables."""
    conn = sqlite3.connect("company_tasks.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.executescript('''
        DROP TABLE IF EXISTS employees;
        DROP TABLE IF EXISTS tasks;
        
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            status TEXT CHECK(status IN ('Pending', 'Completed')) DEFAULT 'Pending',
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        );
    ''')
    conn.commit()
    conn.close()


def insert_employees(cursor):
    """Inserts predefined employees into the database."""
    employees_data = [
        ("Alice Johnson", "HR"),
        ("Bob Smith", "IT"),
        ("Charlie Lee", "Finance"),
        ("David Kim", "Marketing")
    ]
     # TODO: Insert employees_data into the employees table
    cursor.executemany(
        "INSERT INTO employees (name, department) VALUES (?, ?)",
        employees_data
    )
    conn.commit()
    

def insert_tasks(cursor):
    """Inserts predefined tasks into the database."""
    tasks_data = [
        {"employee_id": 1, "description": "Review resumes"},
        {"employee_id": 2, "description": "Fix server issue"},
        {"employee_id": 3, "description": "Prepare budget report"},
        {"employee_id": 4, "description": "Create marketing plan"}
    ]
     # TODO: Insert tasks_data into the tasks table using named placeholders
    cursor.executemany(
        "INSERT INTO tasks (employee_id, description) VALUES (:employee_id, :description)",
        tasks_data
    )   
    conn.commit()


def fetch_all_employees(cursor):
    """Fetch all employees from the database."""
    cursor.execute("SELECT * FROM employees")
    return cursor.fetchall()
    


def fetch_employee_by_id(cursor, emp_id):
    """Fetch a single employee by ID."""
    cursor.execute("SELECT * FROM employees WHERE id = ?", (emp_id,))
    return cursor.fetchone()


def fetch_tasks_by_employee(cursor, emp_id):
    """Fetch all tasks assigned to a given employee ID."""
    cursor.execute("SELECT * FROM tasks WHERE employee_id = ?", (emp_id,))
    return cursor.fetchall()


def update_task_status(cursor, task_id, status):
    """Update the status of a task."""
    cursor.execute(
        "UPDATE tasks SET status = ? WHERE id = ?",
        (status, task_id)
    )


def delete_task(cursor, task_id):
    """Delete a task by ID."""
    cursor.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )


def generate_summary_report(cursor):
    """Generate a summary report of employees and their tasks."""
    cursor.execute('''
        SELECT e.id, e.name, e.department, t.id as task_id, t.description, t.status
        FROM employees e, tasks t 
        WHERE e.id = t.employee_id ''')
    return cursor.fetchall()


def count_tasks_per_employee(cursor):
    """Count the number of tasks assigned to each employee."""
    cursor.execute('''
        SELECT e.id, e.name, COUNT(t.id) AS task_count
        FROM employees e, tasks t
        WHERE e.id = t.employee_id
        GROUP BY e.id, e.name
    ''')
    return cursor.fetchall()


def test_keys_function(cursor):
    """Test how to access and use .keys()."""
    cursor.execute("SELECT * FROM employees LIMIT 1")
    row = cursor.fetchone()
    if row:
        print("Column Names:", row.keys())  
        print("Value for 'name':", row["name"])  


if _name_ == "_main_":
    setup_database()
    conn = sqlite3.connect("company_tasks.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    insert_employees(cursor)
    insert_tasks(cursor)
    conn.commit()

    print("Employees:")
    for row in fetch_all_employees(cursor):
        print(dict(row))

    print("\nTasks for Employee 1:")
    for row in fetch_tasks_by_employee(cursor, 1):
        print(dict(row))

    update_task_status(cursor, 1, "Completed")
    print("\nUpdated Tasks for Employee 1:")
    for row in fetch_tasks_by_employee(cursor, 1):
        print(dict(row))

    print("\nSummary Report:")
    for row in generate_summary_report(cursor):
        print(dict(row))

    print("\nTask Counts:")
    for row in count_tasks_per_employee(cursor):
        print(dict(row))

    print("\nTesting keys() function:")
    test_keys_function(cursor)

    conn.commit()
    conn.close()
    print("\nDatabase operations complete.")