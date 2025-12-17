import sys
import os
import logging
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

from supabase import create_client

def inspect_schema():
    url = os.getenv("supabase_url")
    key = os.getenv("supabase_service_role_key")
    
    if not url or not key:
        print("Missing Supabase credentials")
        return

    client = create_client(url, key)
    
    tables = ["glossary_index", "legal_index", "financial_index", "news_index"]
    
    for table in tables:
        print(f"\n--- Inspecting {table} ---")
        try:
            # Fetch 1 row to see columns
            response = client.table(table).select("*").limit(1).execute()
            if response.data:
                print("Row keys:", response.data[0].keys())
            else:
                print(f"No data found in {table}")
        except Exception as e:
            print(f"Error selecting from {table}: {e}")

if __name__ == "__main__":
    inspect_schema()
