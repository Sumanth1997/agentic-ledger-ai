"""PDF parser module for extracting transaction data from Zolve credit card statements."""

import io
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

import pikepdf
import pdfplumber


@dataclass
class Transaction:
    """Represents a single transaction from a credit card statement."""
    posted_date: datetime
    transaction_date: datetime
    description: str
    amount: float
    transaction_type: str  # 'credit' or 'debit'


@dataclass
class StatementSummary:
    """Summary information from the statement."""
    bill_period_start: Optional[datetime] = None
    bill_period_end: Optional[datetime] = None
    previous_balance: Optional[float] = None
    new_balance: Optional[float] = None
    payment_due_date: Optional[datetime] = None
    minimum_payment: Optional[float] = None
    payments: Optional[float] = None
    purchases: Optional[float] = None


def decrypt_pdf(pdf_bytes: bytes, password: str) -> bytes:
    """
    Decrypt a password-protected PDF.
    
    Args:
        pdf_bytes: Raw PDF bytes
        password: PDF password
        
    Returns:
        Decrypted PDF bytes
    """
    input_buffer = io.BytesIO(pdf_bytes)
    output_buffer = io.BytesIO()
    
    with pikepdf.open(input_buffer, password=password) as pdf:
        pdf.save(output_buffer)
    
    output_buffer.seek(0)
    return output_buffer.read()


def extract_text_from_pdf(pdf_bytes: bytes) -> List[str]:
    """
    Extract text from each page of a PDF.
    
    Args:
        pdf_bytes: Decrypted PDF bytes
        
    Returns:
        List of text content per page
    """
    buffer = io.BytesIO(pdf_bytes)
    pages_text = []
    
    with pdfplumber.open(buffer) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_text.append(text)
    
    return pages_text


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string in MM/DD/YYYY format."""
    try:
        return datetime.strptime(date_str.strip(), "%m/%d/%Y")
    except ValueError:
        return None


def parse_amount(amount_str: str) -> float:
    """Parse amount string, removing $ and handling negative values."""
    # Remove $ and any whitespace
    cleaned = amount_str.replace("$", "").replace(",", "").strip()
    # Handle parentheses for negative numbers
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    return float(cleaned)


def parse_transactions(pages_text: List[str]) -> Tuple[List[Transaction], StatementSummary]:
    """
    Parse transactions from statement text.
    
    Args:
        pages_text: List of text content per page
        
    Returns:
        Tuple of (list of transactions, statement summary)
    """
    transactions = []
    summary = StatementSummary()
    
    # Parse first page for summary info
    if pages_text:
        first_page = pages_text[0]
        
        # Extract bill period
        bill_period_match = re.search(r"Bill Period:\s*(\d{2}-\d{2}-\d{4})\s*-\s*(\d{2}-\d{2}-\d{4})", first_page)
        if bill_period_match:
            try:
                summary.bill_period_start = datetime.strptime(bill_period_match.group(1), "%d-%m-%Y")
                summary.bill_period_end = datetime.strptime(bill_period_match.group(2), "%d-%m-%Y")
            except ValueError:
                pass
        
        # Extract balances
        prev_balance_match = re.search(r"Previous Balance\s*\$?([\d,.]+)", first_page)
        if prev_balance_match:
            summary.previous_balance = parse_amount(prev_balance_match.group(1))
        
        new_balance_match = re.search(r"New Balance[^\$]*\$?([\d,.]+)", first_page)
        if new_balance_match:
            summary.new_balance = parse_amount(new_balance_match.group(1))
    
    # Parse transaction pages (typically page 2+)
    for page_text in pages_text:
        if "Account Activity" not in page_text:
            continue
            
        lines = page_text.split("\n")
        current_section = None  # 'credits' or 'debits'
        
        for line in lines:
            line = line.strip()
            
            # Detect section headers
            if "Payments and Other Credits" in line:
                current_section = "credit"
                continue
            elif "Purchases and Cash Advances" in line:
                current_section = "debit"
                continue
            elif "Fees and Interest Charged" in line:
                current_section = "fees"
                continue
            elif "Sub Total" in line or "No transaction available" in line:
                continue
            
            # Skip non-transaction lines
            if not current_section or current_section == "fees":
                continue
            
            # Try to parse transaction line
            # Format: MM/DD/YYYY MM/DD/YYYY Description $Amount
            # Pattern matches: date date description amount
            tx_match = re.match(
                r"(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(.+?)\s+\$?([\d,.]+)\s*$",
                line
            )
            
            if tx_match:
                posted_date = parse_date(tx_match.group(1))
                transaction_date = parse_date(tx_match.group(2))
                description = tx_match.group(3).strip()
                amount = parse_amount(tx_match.group(4))
                
                if posted_date and transaction_date:
                    transactions.append(Transaction(
                        posted_date=posted_date,
                        transaction_date=transaction_date,
                        description=description,
                        amount=amount,
                        transaction_type=current_section
                    ))
    
    return transactions, summary


def parse_statement_pdf(pdf_bytes: bytes, password: str) -> Tuple[List[Transaction], StatementSummary]:
    """
    Main entry point: decrypt PDF and extract all transactions.
    
    Args:
        pdf_bytes: Raw password-protected PDF bytes
        password: PDF password
        
    Returns:
        Tuple of (list of transactions, statement summary)
    """
    decrypted = decrypt_pdf(pdf_bytes, password)
    pages_text = extract_text_from_pdf(decrypted)
    return parse_transactions(pages_text)
