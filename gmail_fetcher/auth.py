"""Gmail API authentication module."""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import SCOPES, CREDENTIALS_FILE, TOKEN_FILE


def get_gmail_service():
    """
    Authenticate with Gmail API and return a service instance.
    
    On first run, opens a browser for OAuth authorization.
    Subsequent runs use the cached token.
    
    Returns:
        googleapiclient.discovery.Resource: Gmail API service instance
    """
    creds = None
    
    # Load existing token if available
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh expired token
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            # Run OAuth flow
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {CREDENTIALS_FILE}\n"
                    "Please download OAuth credentials from Google Cloud Console."
                )
            
            print("Opening browser for Google authorization...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save token for future runs
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
            print(f"Token saved to {TOKEN_FILE}")
    
    # Build and return Gmail service
    service = build("gmail", "v1", credentials=creds)
    return service
