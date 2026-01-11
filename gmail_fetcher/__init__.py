"""Gmail PDF Fetcher - Download credit card statement PDFs from Gmail."""

from .auth import get_gmail_service
from .fetcher import fetch_and_download_statements, fetch_and_upload_statements
from .pdf_parser import parse_statement_pdf, Transaction, StatementSummary
from .supabase_client import (
    get_supabase_client,
    get_statements_by_status,
    update_status,
    download_pdf,
    insert_transactions_batch,
)

__all__ = [
    "get_gmail_service",
    "fetch_and_download_statements",
    "fetch_and_upload_statements",
    "parse_statement_pdf",
    "Transaction",
    "StatementSummary",
    "get_supabase_client",
    "get_statements_by_status",
    "update_status",
    "download_pdf",
    "insert_transactions_batch",
]

