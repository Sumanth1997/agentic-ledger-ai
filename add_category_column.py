#!/usr/bin/env python3
"""
Add category column to transactions table.

Run this once to add the category column before running categorize_transactions.py
"""

from dotenv import load_dotenv
load_dotenv()

from gmail_fetcher import get_supabase_client

def main():
    print("Adding 'category' column to transactions table...")
    
    client = get_supabase_client()
    
    # Use raw SQL via RPC to add the column
    # Note: This requires a Supabase function or manual execution
    # We'll verify if the column exists instead
    
    # Try to select with category to see if it exists
    try:
        result = client.table("transactions").select("id, category").limit(1).execute()
        print("✓ 'category' column already exists!")
        return 0
    except Exception as e:
        if "category does not exist" in str(e):
            print("Column does not exist. Please run this SQL in Supabase Dashboard:")
            print()
            print("=" * 60)
            print("ALTER TABLE transactions ADD COLUMN category TEXT;")
            print("CREATE INDEX idx_transactions_category ON transactions(category);")
            print("=" * 60)
            print()
            print("Go to: https://supabase.com/dashboard → SQL Editor → Run this query")
            return 1
        else:
            print(f"Error: {e}")
            return 1

if __name__ == "__main__":
    exit(main())
