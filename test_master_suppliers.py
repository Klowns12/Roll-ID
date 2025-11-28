import sys
import os
import pandas as pd

# Add parent directory to path
sys.path.append(os.getcwd())
from utils.master_suppliers_manager import MasterSuppliersManager

def test_master_suppliers():
    print("Initializing MasterSuppliersManager...")
    manager = MasterSuppliersManager()
    
    test_code = "RM2062212002"
    print(f"\nSearching for code: {test_code}")
    
    # Test search_combined
    results = manager.search_combined("", test_code)
    print(f"Found {len(results)} results")
    
    if results:
        # Test get_row_data
        print("\nTesting get_row_data:")
        row_data = manager.get_row_data(results[0], "all")
        
        print(f"Code: {row_data.get('Code')}")
        print(f"QTY (from CSV): {row_data.get('QTY')}")
        print(f"ม้วนเต็ม (from CSV): {row_data.get('ม้วนเต็ม')}")
        print(f"เศษ (from CSV): {row_data.get('เศษ')}")
        
        # Verify values
        qty = row_data.get('QTY')
        full = row_data.get('ม้วนเต็ม')
        scrap = row_data.get('เศษ')
        
        if str(qty) == '9.19' and str(full) == '0.0' and str(scrap) == '9.19':
            print("\nSUCCESS: Data matches expected values!")
        else:
            print("\nFAILURE: Data does not match expected values.")

if __name__ == "__main__":
    test_master_suppliers()
