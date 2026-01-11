#!/usr/bin/env python3
"""
Parse Statement PDFs - Extract transactions from Supabase-stored PDFs.

Usage:
    python parse_statements.py

This script:
1. Fetches all statements with status='not_parsed' from Supabase
2. Downloads each PDF from Supabase storage
3. Decrypts and extracts transactions
4. Saves transactions to the 'transactions' table
5. Updates statement status to 'parsed'
"""

import os
import sys
from gmail_fetcher import (
    get_supabase_client,
    get_statements_by_status,
    update_status,
    download_pdf,
    insert_transactions_batch,
    parse_statement_pdf,
)

# PDF password for Zolve statements
PDF_PASSWORD = os.getenv("PDF_PASSWORD")


def main():
    """Main entry point."""
    print("=" * 60)
    print("Statement Parser - Extract Transactions from PDFs")
    print("=" * 60)
    print()
    
    try:
        # Connect to Supabase
        print("Connecting to Supabase...")
        client = get_supabase_client()
        print("✓ Connected to Supabase\n")
        
        # Get unparsed statements
        print("Fetching unparsed statements...")
        statements = get_statements_by_status(client, "not_parsed")
        
        if not statements:
            print("No unparsed statements found.")
            return 0
        
        print(f"Found {len(statements)} unparsed statement(s)\n")
        
        total_transactions = 0
        
        # Process each statement
        for stmt in statements:
            stmt_id = stmt["id"]
            filename = stmt.get("filename", "unknown")
            storage_path = stmt.get("storage_path", "")
            
            print(f"Processing: {filename}")
            
            if not storage_path:
                print(f"  ✗ No storage path found, skipping")
                continue
            
            try:
                # Update status to 'parsing'
                update_status(client, stmt_id, "parsing")
                
                # Download PDF from storage
                print(f"  Downloading from storage...")
                pdf_bytes = download_pdf(client, storage_path)
                
                # Parse transactions from PDF
                print(f"  Extracting transactions...")
                transactions, summary = parse_statement_pdf(pdf_bytes, PDF_PASSWORD)
                
                if transactions:
                    # Convert to dict format for insertion
                    tx_dicts = [
                        {
                            "posted_date": tx.posted_date.isoformat(),
                            "transaction_date": tx.transaction_date.isoformat(),
                            "description": tx.description,
                            "amount": tx.amount,
                            "transaction_type": tx.transaction_type,
                        }
                        for tx in transactions
                    ]
                    
                    # Insert transactions to database
                    print(f"  Inserting {len(tx_dicts)} transactions...")
                    insert_transactions_batch(client, stmt_id, tx_dicts)
                    total_transactions += len(tx_dicts)
                    
                    print(f"  ✓ Parsed {len(transactions)} transactions")
                else:
                    print(f"  ⚠ No transactions found in statement")
                
                # Update status to 'parsed'
                update_status(client, stmt_id, "parsed")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                # Update status to 'error'
                update_status(client, stmt_id, "error")
                continue
        
        # Summary
        print()
        print("=" * 60)
        print(f"✓ Processed {len(statements)} statement(s)")
        print(f"✓ Extracted {total_transactions} total transactions")
        print("=" * 60)
        
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
