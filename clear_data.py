#!/usr/bin/env python3
"""
Clear all data for end-to-end testing.

This script:
1. Deletes all files from the 'statements' storage bucket
2. Truncates the transactions table
3. Truncates the statements table
"""

from dotenv import load_dotenv
load_dotenv()

from gmail_fetcher import get_supabase_client
from gmail_fetcher.config import STORAGE_BUCKET


def main():
    print("=" * 60)
    print("Clear All Data - End-to-End Test Preparation")
    print("=" * 60)
    print()
    
    client = get_supabase_client()
    print("✓ Connected to Supabase")
    print()
    
    # 1. Clear storage bucket
    print("Clearing storage bucket...")
    try:
        # List all files in the bucket
        files = client.storage.from_(STORAGE_BUCKET).list("zolve")
        if files:
            file_paths = [f"zolve/{f['name']}" for f in files]
            client.storage.from_(STORAGE_BUCKET).remove(file_paths)
            print(f"  ✓ Deleted {len(file_paths)} file(s) from storage")
        else:
            print("  ✓ Storage already empty")
    except Exception as e:
        print(f"  ⚠ Storage error: {e}")
    
    # 2. Clear transactions table
    print("Clearing transactions table...")
    try:
        # Delete all records
        result = client.table("transactions").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print(f"  ✓ Transactions table cleared")
    except Exception as e:
        print(f"  ⚠ Error: {e}")
    
    # 3. Clear statements table
    print("Clearing statements table...")
    try:
        result = client.table("statements").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print(f"  ✓ Statements table cleared")
    except Exception as e:
        print(f"  ⚠ Error: {e}")
    
    print()
    print("=" * 60)
    print("✓ All data cleared. Ready for end-to-end test!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. python main.py          # Fetch from Gmail")
    print("  2. python parse_statements.py  # Parse PDFs")
    print("  3. python categorize_transactions.py  # Categorize")
    
    return 0


if __name__ == "__main__":
    exit(main())
