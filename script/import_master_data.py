#!/usr/bin/env python3
"""
Import Master Data from MasterDATA.csv
Extracts roll data and imports into the system
"""

import pandas as pd
import sys
import os

# Add root directory to path
sys.path.append(os.getcwd())

from core.storage import StorageManager, Roll
from datetime import datetime

def import_master_data(csv_file):
    """Import master data from CSV file"""
    
    # Initialize storage with data directory
    storage = StorageManager(os.path.join(os.getcwd(), "data"))
    
    # Read CSV
    try:
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
    except:
        df = pd.read_csv(csv_file, encoding='windows-1252')
    
    # Normalize column names
    df.columns = df.columns.str.lower().str.strip()
    
    print(f"Total rows: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")
    
    success_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Extract data
            roll_id = str(row.get('pdt_code', '')).strip()
            description = str(row.get('pdt_name', '')).strip()
            
            if not roll_id or roll_id == '###':
                error_count += 1
                continue
            
            sku = str(row.get('spl_part_code', '')).strip()
            if not sku or sku == 'nan':
                sku = roll_id[:10]
            
            lot = str(row.get('lot_of_spl', 'DEFAULT')).strip()
            
            length = 100.0
            try:
                if 'rollqty' in df.columns:
                    val = row.get('rollqty', '')
                    if val and str(val).strip() not in ['', 'nan', 'NaN']:
                        length = float(val)
                elif 'availableqty' in df.columns:
                    val = row.get('availableqty', '')
                    if val and str(val).strip() not in ['', 'nan', 'NaN']:
                        length = float(val)
            except:
                length = 100.0
            
            grade = str(row.get('pdt_status', 'A')).strip()
            location = str(row.get('location', '')).strip()
            date_received = str(row.get('create_date', datetime.now().strftime("%Y-%m-%d"))).strip()
            
            roll = Roll(
                roll_id=roll_id,
                code=sku,
                lot_no=lot,
                length=length,
                location=location,
                status='active',
                supplier_name=str(row.get('spl_name', '')).strip(),
                description=description[:100] if description else "",
                unit=str(row.get('unit_type', 'MTS')).strip()
            )
            
            if storage.add_roll(roll):
                success_count += 1
                if (idx + 1) % 50 == 0:
                    print(f"✓ {idx+1}: {roll_id}")
            else:
                error_count += 1
        
        except Exception as e:
            error_count += 1
            print(f"✗ {idx+1}: Error - {str(e)}")
    
    print(f"\nImport Complete! Success: {success_count}, Failed: {error_count}")

if __name__ == "__main__":
    csv_file = "MasterDATA.csv"
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    
    if os.path.exists(csv_file):
        import_master_data(csv_file)
    else:
        print(f"Error: {csv_file} not found")
