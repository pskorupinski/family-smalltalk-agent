import sqlite3

def create_database(db_file: str):
    """
    Creates the state.db SQLite database and initializes the schema.
    """
    # Connect to the SQLite database (will create if it doesn't exist)
    conn = sqlite3.connect(db_file)
    
    # Create a cursor to execute SQL commands
    cursor = conn.cursor()
    
    # Create the Human table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Human (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        phone TEXT,
        name TEXT
    );
    """)
    
    # Create the ContactEvent table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ContactEvent (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        human_id INTEGER,
        datetime TEXT,
        response_received INTEGER,
        FOREIGN KEY (human_id) REFERENCES Human(id)
    );
    """)
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database("state.db")
    print("Database created with tables Human and ContactEvent.")
    