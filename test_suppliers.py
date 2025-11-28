import sys
import os
import pandas as pd

# Add parent directory to path
sys.path.append(os.getcwd())
from utils.suppliers_manager import SuppliersManager

def test_suppliers_manager():
    csv_path = os.path.join("data", "Suppliers.csv")
    print(f"Testing with file: {csv_path}")
    
    if not os.path.exists(csv_path):
        print("File not found!")
        return

    manager = SuppliersManager(csv_path)
    
    if manager.data is None:
        print("Failed to load data")
        return

    print(f"Loaded {len(manager.data)} rows")
    print("Columns:", manager.data.columns.tolist())
    
    # Test search
    test_code = "RM2062212002"
    print(f"\nSearching for code: {test_code}")
    result = manager.search_by_code(test_code)
    
    if result:
        print("Found result:")
        for k, v in result.items():
            print(f"  {k}: {v}")
            
        # Check specific columns we care about
        print("\nChecking target columns:")
        print(f"  QTY (Index 5): {result.get('QTY')}")
        print(f"  ม้วนเต็ม (Index 6): {result.get('ม้วนเต็ม')}")
        print(f"  เศษ (Index 7): {result.get('เศษ')}")
    else:
        print("Result not found")

if __name__ == "__main__":
    test_suppliers_manager()
