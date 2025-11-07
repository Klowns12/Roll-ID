#!/usr/bin/env python3
"""
Import Master Data from MasterDATA.csv
Extracts roll data and imports into the system
"""

import pandas as pd
import sys
import os
from storage import StorageManager, Roll
from datetime import datetime

def import_master_data(csv_file):
    """Import master data from CSV file"""
    
    # Initialize storage with data directory
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    storage = StorageManager(data_dir)
    
    # Read CSV
    df = pd.read_csv(csv_file)
    
    # Normalize column names
    df.columns = df.columns.str.lower().str.strip()
    
    print(f"Total rows: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")
    
    success_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Extract data
            # Column 1 (pdt_code) contains roll_id like RM2061406001
            roll_id = str(row.get('pdt_code', '')).strip()
            
            # Column 2 (pdt_name) contains description
            description = str(row.get('pdt_name', '')).strip()
            
            # Skip if roll_id is empty or starts with ###
            if not roll_id or roll_id == '###':
                error_count += 1
                continue
            
            # Extract SKU from description or use pdt_code
            sku = str(row.get('spl_part_code', '')).strip()
            if not sku:
                # Try to extract from description
                parts = description.split('#')
                if len(parts) > 1:
                    sku = parts[1].split()[0]
                else:
                    sku = roll_id[:10]  # Use first 10 chars of roll_id
            
            # Get LOT from Lot_of_SPL or generate
            lot = str(row.get('lot_of_spl', '')).strip()
            if not lot:
                lot = "DEFAULT"
            
            # Get length - ใช้ RollQTY หรือ availableqty
            length = 100.0  # Default length
            try:
                # ลองใช้ rollqty ก่อน
                if 'rollqty' in df.columns:
                    val = row.get('rollqty', '')
                    if val and str(val).strip() and str(val).strip() not in ['', 'nan', 'NaN']:
                        length = float(val)
                # ถ้าไม่มี ลอง availableqty
                elif 'availableqty' in df.columns:
                    val = row.get('availableqty', '')
                    if val and str(val).strip() and str(val).strip() not in ['', 'nan', 'NaN']:
                        length = float(val)
            except (ValueError, TypeError):
                length = 100.0  # Default length
            
            # Get other attributes
            grade = str(row.get('pdt_status', 'A')).strip()
            if not grade or grade == '':
                grade = 'A'
            
            location = str(row.get('location', '')).strip()
            
            # Get date received
            date_received = str(row.get('create_date', datetime.now().strftime("%Y-%m-%d"))).strip()
            
            # Get additional fields
            spl_name = str(row.get('spl_name', '')).strip()
            unit_type = str(row.get('unit_type', 'MTS')).strip()
            
            # Create roll object with all required fields
            roll = Roll(
                roll_id=roll_id,
                sku=sku,
                lot=lot,
                current_length=length,
                original_length=length,
                location=location,
                grade=grade,
                date_received=date_received,
                marks_no="",
                status='active',
                invoice_number="",
                po_number="",
                spl_name=spl_name,
                type_of_roll="",
                unit_type=unit_type,
                scrap_qty=0.0,
                specification=description[:100] if description else "",  # ใช้ description บางส่วน
                colour=str(row.get('pdt_color', '')).strip(),
                packing_unit=str(length)
            )
            
            # Add to storage
            if storage.add_roll(roll):
                success_count += 1
                print(f"✓ {idx+1}: {roll_id} - {description[:50]}")
            else:
                error_count += 1
                print(f"✗ {idx+1}: {roll_id} - Already exists")
        
        except Exception as e:
            error_count += 1
            print(f"✗ {idx+1}: Error - {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"Import Complete!")
    print(f"Success: {success_count}")
    print(f"Failed: {error_count}")
    print(f"Total: {success_count + error_count}")

if __name__ == "__main__":
    csv_file = "MasterDATA.csv"
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    
    import_master_data(csv_file)
