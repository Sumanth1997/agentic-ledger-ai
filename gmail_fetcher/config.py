"""Configuration constants for Gmail PDF Fetcher."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Gmail API scope - readonly access to emails
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Search query to find Zolve credit card statement emails
SEARCH_QUERY = 'subject:"Zolve credit card statement"'

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Credentials and token paths
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"

# Directory to save downloaded PDFs (local fallback)
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
STORAGE_BUCKET = "statements"
