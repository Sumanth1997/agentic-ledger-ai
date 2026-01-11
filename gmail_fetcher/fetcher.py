"""Gmail email fetching and PDF upload module."""

import base64
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import SEARCH_QUERY, DOWNLOADS_DIR
from .supabase_client import (
    get_supabase_client,
    upload_pdf,
    create_statement_record,
    check_file_exists,
)


def fetch_and_upload_statements(service, use_supabase: bool = True) -> List[dict]:
    """
    Fetch emails matching the Zolve credit card statement query and upload PDF attachments.
    
    Args:
        service: Gmail API service instance
        use_supabase: If True, upload to Supabase. If False, save locally.
        
    Returns:
        List of uploaded file records (dicts with filename, storage_path, etc.)
    """
    uploaded_files = []
    supabase_client = None
    
    if use_supabase:
        supabase_client = get_supabase_client()
        print("✓ Connected to Supabase")
    
    print(f"Searching for emails with query: {SEARCH_QUERY}")
    
    # Search for matching emails
    results = service.users().messages().list(
        userId="me",
        q=SEARCH_QUERY
    ).execute()
    
    messages = results.get("messages", [])
    
    if not messages:
        print("No matching emails found.")
        return uploaded_files
    
    print(f"Found {len(messages)} matching email(s)")
    
    # Process each email
    for msg_info in messages:
        msg_id = msg_info["id"]
        
        # Get full message details
        message = service.users().messages().get(
            userId="me",
            id=msg_id,
            format="full"
        ).execute()
        
        # Extract email metadata
        headers = {h["name"]: h["value"] for h in message["payload"]["headers"]}
        subject = headers.get("Subject", "No Subject")
        date_str = headers.get("Date", "")
        
        # Parse email date
        email_date = None
        try:
            email_date = parsedate_to_datetime(date_str)
            date_prefix = email_date.strftime("%Y-%m-%d")
        except:
            date_prefix = datetime.now().strftime("%Y-%m-%d")
            email_date = datetime.now()
        
        print(f"\nProcessing: {subject} ({date_prefix})")
        
        # Find and download PDF attachments
        attachments = _get_pdf_attachments(service, msg_id, message["payload"])
        
        for attachment_name, attachment_data in attachments:
            # Create safe filename
            safe_name = _sanitize_filename(f"{date_prefix}_{attachment_name}")
            
            if use_supabase and supabase_client:
                # Check if file already exists
                if check_file_exists(supabase_client, safe_name):
                    print(f"  ⏭ Skipped (already exists): {safe_name}")
                    continue
                
                try:
                    # Upload to Supabase Storage
                    storage_path = upload_pdf(supabase_client, safe_name, attachment_data)
                    
                    # Create database record
                    record = create_statement_record(
                        supabase_client,
                        filename=safe_name,
                        storage_path=storage_path,
                        email_date=email_date
                    )
                    
                    print(f"  ✓ Uploaded: {safe_name}")
                    uploaded_files.append(record)
                    
                except Exception as e:
                    print(f"  ✗ Error uploading {safe_name}: {e}")
            else:
                # Fallback: save locally
                file_path = DOWNLOADS_DIR / safe_name
                
                if file_path.exists():
                    base = file_path.stem
                    ext = file_path.suffix
                    counter = 1
                    while file_path.exists():
                        file_path = DOWNLOADS_DIR / f"{base}_{counter}{ext}"
                        counter += 1
                
                with open(file_path, "wb") as f:
                    f.write(attachment_data)
                
                print(f"  ✓ Downloaded: {file_path.name}")
                uploaded_files.append({"filename": file_path.name, "path": str(file_path)})
    
    return uploaded_files


# Keep the old function for backwards compatibility
def fetch_and_download_statements(service) -> List[Path]:
    """Legacy function - downloads to local storage."""
    results = fetch_and_upload_statements(service, use_supabase=False)
    return [Path(r["path"]) for r in results if "path" in r]


def _get_pdf_attachments(service, msg_id: str, payload: Dict[str, Any]) -> List[tuple]:
    """
    Extract PDF attachments from email payload.
    
    Args:
        service: Gmail API service instance
        msg_id: Message ID
        payload: Email payload dict
        
    Returns:
        List of tuples (filename, binary_data)
    """
    attachments = []
    
    parts = payload.get("parts", [])
    
    # Handle single-part messages
    if not parts and payload.get("filename"):
        parts = [payload]
    
    for part in parts:
        # Recurse into nested parts
        if part.get("parts"):
            attachments.extend(_get_pdf_attachments(service, msg_id, part))
            continue
        
        filename = part.get("filename", "")
        mime_type = part.get("mimeType", "")
        
        # Check if this is a PDF attachment
        if filename and (mime_type == "application/pdf" or filename.lower().endswith(".pdf")):
            body = part.get("body", {})
            attachment_id = body.get("attachmentId")
            
            if attachment_id:
                # Fetch attachment data
                attachment = service.users().messages().attachments().get(
                    userId="me",
                    messageId=msg_id,
                    id=attachment_id
                ).execute()
                
                # Decode base64url data
                data = base64.urlsafe_b64decode(attachment["data"])
                attachments.append((filename, data))
            elif body.get("data"):
                # Inline attachment
                data = base64.urlsafe_b64decode(body["data"])
                attachments.append((filename, data))
    
    return attachments


def _sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Collapse multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Limit length
    if len(sanitized) > 200:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        sanitized = name[:195] + ('.' + ext if ext else '')
    return sanitized
