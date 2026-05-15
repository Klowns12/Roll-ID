import pandas as pd
import sqlite3
import os

def migrate_master_data():
    root_dir = os.getcwd()
    csv_path = os.path.join(root_dir, "MasterDATA.csv")
    db_path = os.path.join(root_dir, "data", "storage.db")

    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    print(f"Reading data from {csv_path}...")
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding='windows-1252')
    
    # Normalize columns to lowercase and strip whitespace
    df.columns = df.columns.str.strip().str.lower()
    
    # Define the columns we want in our DB
    target_columns = [
        "pdt_code", "pdt_name", "unit_type", "spl_part_code", "scrapqty",
        "create_name", "create_date", "update_name", "update_date",
        "last_buy_date", "lastdate", "pg_name", "cate_name", "spl_name", "spl_code"
    ]
    
    # Ensure all target columns exist in DF
    for col in target_columns:
        if col not in df.columns:
            df[col] = ""
            
    # Select only the columns we need
    df_to_save = df[target_columns].copy()
    
    # Clean numeric columns
    df_to_save['scrapqty'] = pd.to_numeric(df_to_save['scrapqty'], errors='coerce').fillna(0.0)

    print(f"Connecting to database {db_path}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # ลบตารางเก่าทิ้งเพื่อให้สร้างใหม่ด้วยโครงสร้างที่ถูกต้อง
    print("Dropping old 'master_products' table if exists...")
    cur.execute("DROP TABLE IF EXISTS master_products")
    
    # สร้างตารางใหม่ด้วยโครงสร้างที่ถูกต้อง
    print("Creating new 'master_products' table...")
    cur.execute("""
    CREATE TABLE master_products (
        pdt_code TEXT PRIMARY KEY,
        pdt_name TEXT,
        unit_type TEXT,
        spl_part_code TEXT,
        scrapqty REAL,
        create_name TEXT,
        create_date TEXT,
        update_name TEXT,
        update_date TEXT,
        last_buy_date TEXT,
        lastdate TEXT,
        pg_name TEXT,
        cate_name TEXT,
        spl_name TEXT,
        spl_code TEXT
    )
    """)
    conn.commit()
    
    print(f"Migrating {len(df_to_save)} records to 'master_products' table...")
    df_to_save.to_sql('master_products', conn, if_exists='append', index=False, method='multi', chunksize=500)
    
    conn.close()
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate_master_data()
