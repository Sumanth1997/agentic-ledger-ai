#!/usr/bin/env python3
"""
Gmail PDF Fetcher - Download Zolve credit card statement PDFs from Gmail.

Usage:
    python main.py              # Upload to Supabase (default)
    python main.py --local      # Save locally instead
    
First run will open a browser for Google OAuth authorization.
"""

import sys
from gmail_fetcher import get_gmail_service, fetch_and_upload_statements
from gmail_fetcher.config import DOWNLOADS_DIR


def main():
    """Main entry point."""
    print("=" * 60)
    print("Gmail PDF Fetcher - Zolve Credit Card Statements")
    print("=" * 60)
    print()
    
    # Check for --local flag
    use_supabase = "--local" not in sys.argv
    
    try:
        # Authenticate and get Gmail service
        print("Authenticating with Gmail API...")
        service = get_gmail_service()
        print("✓ Authentication successful!\n")
        
        # Fetch and upload/download PDFs
        if use_supabase:
            print("Mode: Upload to Supabase\n")
        else:
            print(f"Mode: Save locally to {DOWNLOADS_DIR}\n")
        
        uploaded = fetch_and_upload_statements(service, use_supabase=use_supabase)
        
        # Summary
        print()
        print("=" * 60)
        if uploaded:
            if use_supabase:
                print(f"✓ Uploaded {len(uploaded)} PDF(s) to Supabase")
                print()
                for record in uploaded:
                    status = record.get("status", "unknown")
                    print(f"  • {record.get('filename', 'unknown')} [{status}]")
            else:
                print(f"✓ Downloaded {len(uploaded)} PDF(s) to: {DOWNLOADS_DIR}")
                print()
                for record in uploaded:
                    print(f"  • {record.get('filename', 'unknown')}")
        else:
            print("No new PDF attachments to process.")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        raise
    
    return 0


if __name__ == "__main__":
    exit(main())
