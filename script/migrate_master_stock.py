import pandas as pd
import sqlite3
import os
import sys
from pathlib import Path

def migrate_master_stock_full():
    # Setup paths
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(root_dir, "data", "unused", "Master_Stock.csv")
    db_path = os.path.join(root_dir, "data", "storage.db")
    
    if not os.path.exists(csv_path):
        print(f"Error: File not found at {csv_path}")
        return

    print(f"Reading {csv_path}...")
    try:
        # Read CSV with encoding handling
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
        except:
            df = pd.read_csv(csv_path, encoding='windows-1252')
            
        print(f"Loaded {len(df)} rows and {len(df.columns)} columns from CSV.")
        
        # Ensure 'pdt_code' exists as it's our primary key
        if 'pdt_code' not in df.columns:
            print("Error: 'pdt_code' column not found in CSV. Migration aborted.")
            return

        # Connect to DB
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        print("Recreating master_products table with all columns...")
        cur.execute("DROP TABLE IF EXISTS master_products")
        
        # Build CREATE TABLE statement dynamically
        # We'll treat pdt_code as PRIMARY KEY and everything else as TEXT/REAL
        col_definitions = []
        for col in df.columns:
            col_sanitized = col.strip()
            if col_sanitized == 'pdt_code':
                col_definitions.append(f'"{col_sanitized}" TEXT PRIMARY KEY')
            else:
                # Check data type for better schema (optional, but good)
                if pd.api.types.is_numeric_dtype(df[col]):
                    col_definitions.append(f'"{col_sanitized}" REAL')
                else:
                    col_definitions.append(f'"{col_sanitized}" TEXT')
        
        create_query = f"CREATE TABLE master_products ({', '.join(col_definitions)})"
        cur.execute(create_query)
        
        # Insert data
        print("Inserting all data into database...")
        # We can use pandas to_sql for simplicity as we just recreated the table exactly as the df
        df.to_sql('master_products', conn, if_exists='append', index=False)
        
        conn.commit()
        conn.close()
        
        print(f"Migration completed! Migrated {len(df)} products with {len(df.columns)} attributes.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate_master_stock_full()
