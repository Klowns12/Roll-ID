import sqlite3
import os

def migrate_to_simplified_rolls():
    db_path = os.path.join(os.getcwd(), "data", "storage.db")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}.")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    print("Recreating 'rolls' table with simplified schema...")
    
    # Drop existing table
    cur.execute("DROP TABLE IF EXISTS rolls")
    
    # Create new table with exact requested columns
    cur.execute("""
    CREATE TABLE rolls (
        roll_id TEXT PRIMARY KEY,
        code TEXT,
        sub_part_code TEXT,
        sup_code TEXT,
        supplier_name TEXT,
        description TEXT,
        lot_no TEXT,
        quantity INTEGER,
        location TEXT,
        unit TEXT,
        color TEXT,
        width TEXT,
        length REAL,
        status TEXT,
        date_received TEXT
    )
    """)
    
    # Re-create indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_rolls_code ON rolls(code)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_rolls_lot ON rolls(lot_no)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_rolls_location ON rolls(location)")

    conn.commit()
    conn.close()
    print("Database 'rolls' table has been simplified successfully!")

if __name__ == "__main__":
    migrate_to_simplified_rolls()
