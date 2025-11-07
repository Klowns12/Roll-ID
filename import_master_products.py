"""
Import Master Products from MasterDATA.csv
นำเข้าข้อมูลสินค้าหลัก (Master Products) จาก MasterDATA.csv
"""

import pandas as pd
import sys
import os
from storage import StorageManager, MasterProduct
from datetime import datetime

def import_master_products(csv_file):
    """Import master products from CSV file"""
    
    # Initialize storage with data directory
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    storage = StorageManager(data_dir)
    
    print(f"Reading {csv_file}...")
    
    # Read CSV
    try:
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
    except:
        df = pd.read_csv(csv_file, encoding='windows-1252')
    
    # Normalize column names
    df.columns = df.columns.str.lower().str.strip()
    
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    success_count = 0
    error_count = 0
    
    # Process each row
    for idx, row in df.iterrows():
        try:
            # Get SKU from pdt_code or spl_part_code
            sku = str(row.get('spl_part_code', '')).strip()
            if not sku or sku == 'nan':
                sku = str(row.get('pdt_code', '')).strip()
            
            if not sku or sku == 'nan':
                error_count += 1
                continue
            
            # Get description
            description = str(row.get('pdt_name', '')).strip()
            if not description or description == 'nan':
                description = str(row.get('pdt_name_en', '')).strip()
            
            if not description or description == 'nan':
                description = sku
            
            # Get default length from RollQTY or availableqty
            default_length = 100.0
            try:
                if 'rollqty' in df.columns:
                    val = row.get('rollqty', '')
                    if val and str(val).strip() and str(val).strip() not in ['', 'nan', 'NaN', 'THB']:
                        default_length = float(val)
                elif 'availableqty' in df.columns:
                    val = row.get('availableqty', '')
                    if val and str(val).strip() and str(val).strip() not in ['', 'nan', 'NaN', 'THB']:
                        default_length = float(val)
            except (ValueError, TypeError):
                default_length = 100.0
            
            # Get default grade
            default_grade = str(row.get('pdt_status', 'A')).strip()
            if not default_grade or default_grade == 'nan' or default_grade == '':
                default_grade = 'A'
            
            # Create MasterProduct object
            product = MasterProduct(
                sku=sku,
                description=description,
                default_length=default_length,
                default_grade=default_grade
            )
            
            # Add to storage
            if storage.add_master_product(product):
                success_count += 1
                if (idx + 1) % 50 == 0:
                    print(f"✓ {idx+1}: {sku} - {description[:50]}")
            else:
                # Already exists, update it
                storage._master_products[sku] = product
                storage.save_master_products()
                success_count += 1
                
        except Exception as e:
            error_count += 1
            print(f"✗ {idx+1}: Error - {str(e)}")
    
    print("\n" + "="*80)
    print("Import Complete!")
    print(f"Success: {success_count}")
    print(f"Failed: {error_count}")
    print(f"Total: {len(df)}")
    print("="*80)

if __name__ == "__main__":
    csv_file = "MasterDATA.csv"
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found!")
        sys.exit(1)
    
    import_master_products(csv_file)
