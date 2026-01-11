#!/usr/bin/env python3
"""Debug script to inspect Supabase statements table and storage."""

from gmail_fetcher.supabase_client import get_supabase_client, STORAGE_BUCKET
from gmail_fetcher.config import SUPABASE_URL

def debug_supabase():
    """Inspect Supabase configuration and data."""
    
    print("=" * 60)
    print("SUPABASE DEBUG INFO")
    print("=" * 60)
    
    # Show config
    print(f"\nSupabase URL: {SUPABASE_URL}")
    print(f"Storage Bucket: {STORAGE_BUCKET}")
    
    # Connect
    client = get_supabase_client()
    print("\n✓ Connected to Supabase")
    
    # Get all statements (not just unparsed)
    print("\n" + "=" * 60)
    print("STATEMENTS TABLE")
    print("=" * 60)
    
    result = client.table("statements").select("*").limit(3).execute()
    statements = result.data
    
    print(f"Sample records (showing 3):\n")
    
    for stmt in statements:
        print(f"ID: {stmt.get('id')}")
        print(f"  filename: {stmt.get('filename')}")
        print(f"  storage_path: {stmt.get('storage_path')}")
        print(f"  status: {stmt.get('status')}")
        print(f"  email_date: {stmt.get('email_date')}")
        print()
    
    # List storage bucket contents
    print("=" * 60)
    print("STORAGE BUCKET CONTENTS")
    print("=" * 60)
    
    try:
        files = client.storage.from_(STORAGE_BUCKET).list()
        print(f"\nRoot level ({len(files)} items):")
        for f in files[:10]:
            print(f"  {f.get('name')} (id: {f.get('id')})")
        
        # Check for zolve folder
        zolve_files = client.storage.from_(STORAGE_BUCKET).list(path="zolve")
        print(f"\n/zolve folder ({len(zolve_files)} items):")
        for f in zolve_files[:5]:
            print(f"  {f.get('name')}")
            
    except Exception as e:
        print(f"Error listing storage: {e}")
    
    # Try to download one file
    print("\n" + "=" * 60)
    print("DOWNLOAD TEST")
    print("=" * 60)
    
    if statements:
        storage_path = statements[0].get('storage_path')
        print(f"\nTrying to download: {storage_path}")
        
        try:
            data = client.storage.from_(STORAGE_BUCKET).download(storage_path)
            print(f"✓ Success! Downloaded {len(data)} bytes")
        except Exception as e:
            print(f"✗ Error: {e}")
            
            # Try without the prefix
            if storage_path and storage_path.startswith("zolve/"):
                alt_path = storage_path[6:]  # Remove "zolve/"
                print(f"\nTrying alternate path: {alt_path}")
                try:
                    data = client.storage.from_(STORAGE_BUCKET).download(alt_path)
                    print(f"✓ Success! Downloaded {len(data)} bytes")
                except Exception as e2:
                    print(f"✗ Error: {e2}")

if __name__ == "__main__":
    debug_supabase()
