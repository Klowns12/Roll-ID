import pandas as pd
import sqlite3
import os

def migrate_all_data():
    root_dir = os.getcwd()
    data_dir = os.path.join(root_dir, "data")
    db_path = os.path.join(data_dir, "storage.db")
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # --- 1. Migrate MasterDATA.csv ---
    csv_master = os.path.join(root_dir, "MasterDATA.csv")
    if os.path.exists(csv_master):
        print(f"Migrating {csv_master}...")
        try:
            df = pd.read_csv(csv_master, encoding='utf-8-sig')
        except:
            df = pd.read_csv(csv_master, encoding='windows-1252')
        
        df.columns = df.columns.str.strip().str.lower()
        target_cols = ["pdt_code", "pdt_name", "unit_type", "spl_part_code", "scrapqty", 
                       "create_name", "create_date", "update_name", "update_date", 
                       "last_buy_date", "lastdate", "pg_name", "cate_name", "spl_name", "spl_code"]
        for c in target_cols:
            if c not in df.columns: df[c] = ""
        
        df_save = df[target_cols].copy()
        df_save['scrapqty'] = pd.to_numeric(df_save['scrapqty'], errors='coerce').fillna(0.0)
        
        cur.execute("DROP TABLE IF EXISTS master_products")
        cur.execute("""CREATE TABLE master_products (pdt_code TEXT PRIMARY KEY, pdt_name TEXT, unit_type TEXT, spl_part_code TEXT, scrapqty REAL, create_name TEXT, create_date TEXT, update_name TEXT, update_date TEXT, last_buy_date TEXT, lastdate TEXT, pg_name TEXT, cate_name TEXT, spl_name TEXT, spl_code TEXT)""")
        df_save.to_sql('master_products', conn, if_exists='append', index=False)
        print(f"Done MasterDATA: {len(df_save)} rows")

    # --- 2. Migrate Suppliers.csv ---
    csv_suppliers = os.path.join(data_dir, "Suppliers.csv")
    if os.path.exists(csv_suppliers):
        print(f"Migrating {csv_suppliers}...")
        try:
            df = pd.read_csv(csv_suppliers, encoding='utf-8-sig')
        except:
            df = pd.read_csv(csv_suppliers, encoding='windows-1252')
        
        # คัดกรองข้อมูลตาม logic เดิมในโค้ด
        df = df[(df.iloc[:, 0] != 'Item') & (df.iloc[:, 0] != 'Suppliers') & (df.iloc[:, 0].notna())]
        if 'Unnamed: 1' in df.columns:
            df = df.rename(columns={'Unnamed: 1': 'Suppliers'})
        
        # Map columns
        mapping = {
            df.columns[0]: 'pdt_code',
            'Suppliers': 'supplier_name',
            'Location': 'location',
            'QTY': 'qty',
            'ม้วนเต็ม': 'full_rolls',
            'เศษ': 'scrap_qty'
        }
        df = df.rename(columns=mapping)
        
        target_cols = ['pdt_code', 'supplier_name', 'location', 'qty', 'full_rolls', 'scrap_qty']
        for c in target_cols:
            if c not in df.columns: df[c] = ""
            
        df_save = df[target_cols].copy()
        df_save['qty'] = pd.to_numeric(df_save['qty'], errors='coerce').fillna(0.0)
        df_save['full_rolls'] = pd.to_numeric(df_save['full_rolls'], errors='coerce').fillna(0.0)
        df_save['scrap_qty'] = pd.to_numeric(df_save['scrap_qty'], errors='coerce').fillna(0.0)
        
        cur.execute("DROP TABLE IF EXISTS supplier_stock")
        cur.execute("""CREATE TABLE supplier_stock (pdt_code TEXT, supplier_name TEXT, location TEXT, qty REAL, full_rolls REAL, scrap_qty REAL, PRIMARY KEY (pdt_code, supplier_name, location))""")
        df_save.to_sql('supplier_stock', conn, if_exists='append', index=False)
        print(f"Done Suppliers: {len(df_save)} rows")

    # --- 3. Migrate MasterDispatch.csv ---
    csv_dispatch = os.path.join(data_dir, "MasterDispatch.csv")
    if os.path.exists(csv_dispatch):
        print(f"Migrating {csv_dispatch}...")
        try:
            df = pd.read_csv(csv_dispatch, encoding='utf-8-sig')
        except:
            df = pd.read_csv(csv_dispatch, encoding='windows-1252')
        
        df.columns = df.columns.str.strip().str.lower()
        # Map columns
        mapping = {
            'code': 'pdt_code',
            'location': 'location',
            'roll_id': 'roll_id',
            'lot': 'lot',
            'spl_name': 'spl_name'
        }
        df = df.rename(columns=mapping)
        
        target_cols = ['pdt_code', 'location', 'roll_id', 'lot', 'spl_name']
        for c in target_cols:
            if c not in df.columns: df[c] = ""
            
        df_save = df[target_cols].copy()
        
        cur.execute("DROP TABLE IF EXISTS dispatch_legacy")
        cur.execute("""CREATE TABLE dispatch_legacy (pdt_code TEXT, location TEXT, roll_id TEXT, lot TEXT, spl_name TEXT)""")
        df_save.to_sql('dispatch_legacy', conn, if_exists='append', index=False)
        print(f"Done Dispatch: {len(df_save)} rows")

    conn.commit()
    conn.close()
    print("\nAll migrations completed successfully!")

if __name__ == "__main__":
    migrate_all_data()
