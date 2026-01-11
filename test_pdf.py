#!/usr/bin/env python3
"""Test PDF parser with a local PDF file."""

import os
from pathlib import Path
from dotenv import load_dotenv
from gmail_fetcher.pdf_parser import parse_statement_pdf

# Load environment variables
load_dotenv()

PDF_PATH = Path("/Applications/All_Folders/PersonalProjects/agentic-ledger-ai/downloads/2024-03-16_ZOLVE_CREDIT_STATEMENT_03_15_2024.pdf")
PASSWORD = os.getenv("PDF_PASSWORD")

def test_parser():
    """Test transaction extraction."""
    print(f"Testing: {PDF_PATH.name}\n")
    
    # Read PDF bytes
    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()
    
    # Parse statement
    transactions, summary = parse_statement_pdf(pdf_bytes, PASSWORD)
    
    # Print summary
    print("=" * 60)
    print("STATEMENT SUMMARY")
    print("=" * 60)
    print(f"Bill Period: {summary.bill_period_start} - {summary.bill_period_end}")
    print(f"Previous Balance: ${summary.previous_balance}")
    print(f"New Balance: ${summary.new_balance}")
    print()
    
    # Print transactions
    print("=" * 60)
    print(f"TRANSACTIONS ({len(transactions)} found)")
    print("=" * 60)
    
    for tx in transactions:
        tx_type = "+" if tx.transaction_type == "credit" else "-"
        print(f"{tx.posted_date.strftime('%m/%d/%Y')} | {tx_type}${tx.amount:,.2f} | {tx.description[:50]}")
    
    print()
    print(f"Total credits: ${sum(tx.amount for tx in transactions if tx.transaction_type == 'credit'):,.2f}")
    print(f"Total debits: ${sum(tx.amount for tx in transactions if tx.transaction_type == 'debit'):,.2f}")

if __name__ == "__main__":
    test_parser()
