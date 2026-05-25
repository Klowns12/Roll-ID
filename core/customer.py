import os
import requests
from zeep import Client
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

WSDL_URL = os.getenv("WSDL_URL")
LOCAL_WSDL_PATH = os.getenv("LOCAL_WSDL_PATH")

_client_instance = None

def get_soap_client() -> Optional[Client]:
    global _client_instance
    if _client_instance is not None:
        return _client_instance

    try:
        response = requests.get(WSDL_URL, timeout=5)
        response.raise_for_status()
        wsdl_content = response.text

        wsdl_content = wsdl_content.replace("e14f0d366967.sn.mynetname.net/stws", "e14f0d366967.sn.mynetname.net:82/stws")
        wsdl_content = wsdl_content.replace("e14f0d366967.sn.mynetname.net:80/stws", "e14f0d366967.sn.mynetname.net:82/stws")

        temp_dir = os.path.dirname(os.path.abspath(__file__))
        local_path = os.path.join(temp_dir, LOCAL_WSDL_PATH)
        
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(wsdl_content)

        _client_instance = Client(wsdl=local_path)
        
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
            except:
                pass
                
        return _client_instance
    except Exception as e:
        print(f"Error: {e}")
        return None

def fetch_customer_by_id(customer_id: str) -> Optional[Tuple[str, str]]:
    client = get_soap_client()
    if not client:
        return None
        
    try:
        result = client.service.Customers(CustID=customer_id)
        if result:
            result_str = str(result).strip()
            if "|" in result_str:
                parts = result_str.split("|", 1)
                return parts[0].strip(), parts[1].strip()
            else:
                return customer_id, result_str
    except Exception as e:
        print(f"Error: {e}")
    return None
