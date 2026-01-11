#!/usr/bin/env python3
"""
Categorize Transactions using Ollama LLM.

Usage:
    python categorize_transactions.py

This script:
1. Fetches transactions with category=NULL from Supabase
2. Uses Ollama (llama3.2) to categorize each transaction
3. Updates the transaction record with the assigned category
"""

import os
import json
import requests
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from gmail_fetcher import get_supabase_client

# Ollama configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

# Valid categories
VALID_CATEGORIES = [
    "Shopping",
    "Food & Dining",
    "Transportation",
    "Subscriptions",
    "Utilities",
    "Housing",
    "Entertainment",
    "Travel",
    "Healthcare",
    "Income",
    "Other",
]

SYSTEM_PROMPT = """You are a transaction categorizer. Given a credit card transaction description, respond with ONLY the category name from this list:
- Shopping (retail: Amazon, Walmart, Target, etc.)
- Food & Dining (restaurants, food delivery, groceries)
- Transportation (Uber, Lyft, gas, parking)
- Subscriptions (Netflix, Spotify, cloud services, software)
- Utilities (phone, internet, electricity)
- Housing (rent, mortgage, home services)
- Entertainment (movies, games, events, hobbies)
- Travel (hotels, flights, travel bookings)
- Healthcare (medical, pharmacy, insurance)
- Income (refunds, cashback, payments received)
- Other (anything else)

Respond with ONLY the category name, nothing else."""


def categorize_with_ollama(description: str) -> Optional[str]:
    """
    Use Ollama to categorize a transaction description.
    
    Args:
        description: Transaction description text
        
    Returns:
        Category string or None if failed
    """
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": f"{SYSTEM_PROMPT}\n\nTransaction: {description}\nCategory:",
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for consistent results
                    "num_predict": 20,   # Short response
                }
            },
            timeout=30,
        )
        
        if response.status_code != 200:
            print(f"  ✗ Ollama error: {response.status_code}")
            return None
        
        result = response.json()
        category = result.get("response", "").strip()
        
        # Validate category
        for valid_cat in VALID_CATEGORIES:
            if valid_cat.lower() in category.lower():
                return valid_cat
        
        # Fallback to Other if no match
        return "Other"
        
    except requests.exceptions.ConnectionError:
        print("  ✗ Could not connect to Ollama. Is it running?")
        return None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None


def get_uncategorized_transactions(client) -> list:
    """Fetch transactions without a category."""
    result = (
        client.table("transactions")
        .select("*")
        .is_("category", "null")
        .execute()
    )
    return result.data


def update_transaction_category(client, transaction_id: str, category: str) -> bool:
    """Update a transaction's category in the database."""
    try:
        client.table("transactions").update({"category": category}).eq("id", transaction_id).execute()
        return True
    except Exception as e:
        print(f"  ✗ Database error: {e}")
        return False


def main():
    """Main entry point."""
    print("=" * 60)
    print("Transaction Categorizer - Ollama LLM")
    print("=" * 60)
    print()
    
    # Test Ollama connection
    print(f"Connecting to Ollama ({OLLAMA_URL})...")
    try:
        test_resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if test_resp.status_code != 200:
            print("✗ Could not connect to Ollama. Please ensure it's running.")
            return 1
        print(f"✓ Connected to Ollama (using model: {OLLAMA_MODEL})")
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to Ollama. Please run: ollama serve")
        return 1
    
    print()
    
    # Connect to Supabase
    print("Connecting to Supabase...")
    try:
        client = get_supabase_client()
        print("✓ Connected to Supabase")
    except ValueError as e:
        print(f"✗ {e}")
        return 1
    
    print()
    
    # Fetch uncategorized transactions
    print("Fetching uncategorized transactions...")
    transactions = get_uncategorized_transactions(client)
    
    if not transactions:
        print("✓ All transactions are already categorized!")
        return 0
    
    print(f"Found {len(transactions)} uncategorized transaction(s)")
    print()
    
    # Categorize each transaction
    success_count = 0
    for i, tx in enumerate(transactions, 1):
        description = tx.get("description", "Unknown")
        tx_id = tx.get("id")
        
        # Truncate long descriptions for display
        display_desc = description[:50] + "..." if len(description) > 50 else description
        print(f"[{i}/{len(transactions)}] {display_desc}")
        
        # Get category from Ollama
        category = categorize_with_ollama(description)
        
        if category:
            print(f"  → {category}")
            if update_transaction_category(client, tx_id, category):
                success_count += 1
        else:
            print(f"  → Skipped (Ollama error)")
    
    # Summary
    print()
    print("=" * 60)
    print(f"✓ Categorized {success_count}/{len(transactions)} transactions")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit(main())
