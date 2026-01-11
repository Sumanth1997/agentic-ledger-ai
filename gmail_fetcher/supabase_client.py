"""Supabase client for storage and database operations."""

from supabase import create_client, Client
from datetime import datetime
from typing import Optional
import uuid

from .config import SUPABASE_URL, SUPABASE_KEY, STORAGE_BUCKET


def get_supabase_client() -> Client:
    """
    Initialize and return Supabase client.
    
    Returns:
        Supabase client instance
        
    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_KEY not configured
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(
            "Supabase credentials not configured.\n"
            "Please set SUPABASE_URL and SUPABASE_KEY in .env file."
        )
    
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_pdf(client: Client, filename: str, data: bytes) -> str:
    """
    Upload PDF to Supabase Storage.
    
    Args:
        client: Supabase client
        filename: Name for the file
        data: PDF binary data
        
    Returns:
        Storage path of uploaded file
    """
    # Create unique storage path
    storage_path = f"zolve/{filename}"
    
    # Upload to storage bucket
    client.storage.from_(STORAGE_BUCKET).upload(
        path=storage_path,
        file=data,
        file_options={"content-type": "application/pdf"}
    )
    
    return storage_path


def create_statement_record(
    client: Client,
    filename: str,
    storage_path: str,
    email_date: Optional[datetime] = None
) -> dict:
    """
    Create a statement record in the database.
    
    Args:
        client: Supabase client
        filename: Original filename
        storage_path: Path in Supabase Storage
        email_date: Date from the email
        
    Returns:
        Created record data
    """
    record = {
        "filename": filename,
        "storage_path": storage_path,
        "status": "not_parsed",
    }
    
    if email_date:
        record["email_date"] = email_date.isoformat()
    
    result = client.table("statements").insert(record).execute()
    return result.data[0] if result.data else {}


def get_statements_by_status(client: Client, status: str) -> list:
    """
    Get all statements with a specific status.
    
    Args:
        client: Supabase client
        status: Status to filter by ('not_parsed', 'parsing', 'parsed', 'error')
        
    Returns:
        List of statement records
    """
    result = client.table("statements").select("*").eq("status", status).execute()
    return result.data


def update_status(client: Client, statement_id: str, status: str) -> dict:
    """
    Update the status of a statement.
    
    Args:
        client: Supabase client
        statement_id: UUID of the statement
        status: New status
        
    Returns:
        Updated record data
    """
    result = (
        client.table("statements")
        .update({"status": status, "updated_at": datetime.now().isoformat()})
        .eq("id", statement_id)
        .execute()
    )
    return result.data[0] if result.data else {}


def check_file_exists(client: Client, filename: str) -> bool:
    """
    Check if a file with this filename already exists in the database.
    
    Args:
        client: Supabase client
        filename: Filename to check
        
    Returns:
        True if exists, False otherwise
    """
    result = client.table("statements").select("id").eq("filename", filename).execute()
    return len(result.data) > 0


def download_pdf(client: Client, storage_path: str) -> bytes:
    """
    Download PDF from Supabase Storage.
    
    Args:
        client: Supabase client
        storage_path: Path in Supabase Storage
        
    Returns:
        PDF binary data
    """
    response = client.storage.from_(STORAGE_BUCKET).download(storage_path)
    return response


def insert_transaction(
    client: Client,
    statement_id: str,
    posted_date: str,
    transaction_date: str,
    description: str,
    amount: float,
    transaction_type: str
) -> dict:
    """
    Insert a single transaction into the transactions table.
    
    Args:
        client: Supabase client
        statement_id: UUID of the parent statement
        posted_date: Posted date (ISO format)
        transaction_date: Transaction date (ISO format)
        description: Transaction description
        amount: Transaction amount
        transaction_type: 'credit' or 'debit'
        
    Returns:
        Created record data
    """
    record = {
        "statement_id": statement_id,
        "posted_date": posted_date,
        "transaction_date": transaction_date,
        "description": description,
        "amount": amount,
        "transaction_type": transaction_type,
    }
    
    result = client.table("transactions").insert(record).execute()
    return result.data[0] if result.data else {}


def insert_transactions_batch(client: Client, statement_id: str, transactions: list) -> list:
    """
    Insert multiple transactions in a batch.
    
    Args:
        client: Supabase client
        statement_id: UUID of the parent statement
        transactions: List of transaction dicts
        
    Returns:
        List of created records
    """
    records = [
        {
            "statement_id": statement_id,
            "posted_date": tx["posted_date"],
            "transaction_date": tx["transaction_date"],
            "description": tx["description"],
            "amount": tx["amount"],
            "transaction_type": tx["transaction_type"],
        }
        for tx in transactions
    ]
    
    if not records:
        return []
    
    result = client.table("transactions").insert(records).execute()
    return result.data if result.data else []

