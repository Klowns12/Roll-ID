import os
import sys
from pathlib import Path
import pandas as pd

# Add current directory to path so we can import storage
sys.path.append(os.getcwd())

from storage import StorageManager

def verify_master_data_count():
    # Setup paths
    root_dir = os.getcwd()
    data_dir = os.path.join(root_dir, "data")
    master_csv_path = os.path.join(root_dir, "MasterDATA.csv")
    
    print(f"Root dir: {root_dir}")
    print(f"Data dir: {data_dir}")
    print(f"Master CSV path: {master_csv_path}")
    
    # Initialize storage
    storage = StorageManager(data_dir)
    
    # Get count from storage
    count_from_storage = storage.get_master_data_count()
    print(f"Count from storage: {count_from_storage}")
    
    # Verify manually
    if os.path.exists(master_csv_path):
        try:
            df = pd.read_csv(master_csv_path, encoding='utf-8-sig')
        except UnicodeDecodeError:
            df = pd.read_csv(master_csv_path, encoding='windows-1252')
        except Exception as e:
            print(f"Error reading CSV manually: {e}")
            return
            
        real_count = len(df)
        print(f"Real count from CSV: {real_count}")
        
        if count_from_storage == real_count:
            print("SUCCESS: Counts match!")
        else:
            print("FAILURE: Counts do not match!")
    else:
        print("MasterDATA.csv does not exist. Storage should return 0.")
        if count_from_storage == 0:
             print("SUCCESS: Storage returned 0 as expected.")
        else:
             print(f"FAILURE: Storage returned {count_from_storage} but file missing.")

if __name__ == "__main__":
    verify_master_data_count()
