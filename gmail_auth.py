"""
Gmail Authentication Script

This script authenticates your Gmail account and creates a token file
that allows the system to read emails from your inbox.

Run this ONCE to set up Gmail access.
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Gmail API scope - allows reading emails, modifying labels, and sending emails
SCOPES = ['https://www.googleapis.com/auth/gmail.modify',
          'https://www.googleapis.com/auth/gmail.send']

def authenticate_gmail():
    """
    Authenticate with Gmail and create token file
    """
    print("="*80)
    print("GMAIL AUTHENTICATION")
    print("="*80)

    creds = None
    token_file = 'credentials/gmail_token.pickle'
    credentials_file = 'credentials/gmail_credentials.json'

    # Check if credentials file exists
    if not os.path.exists(credentials_file):
        print("\n✗ Error: gmail_credentials.json not found!")
        print("Make sure you downloaded the OAuth credentials from Google Cloud Console")
        print("and saved it as 'credentials/gmail_credentials.json'")
        return

    # Check if we already have a token
    if os.path.exists(token_file):
        print("\n✓ Found existing token file")
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)

    # If there are no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("\n↻ Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("\n→ Starting authentication flow...")
            print("\nThis will open a browser window where you need to:")
            print("1. Sign in with your Gmail account")
            print("2. Click 'Allow' to grant access")
            print("3. The authentication will complete automatically")
            print("\nIf the browser doesn't open, copy the URL from below and paste it in your browser.")
            print("\n" + "="*80)

            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for future runs
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)

        print("\n" + "="*80)
        print("✓ AUTHENTICATION SUCCESSFUL!")
        print("="*80)
        print(f"\nToken saved to: {token_file}")
        print("You can now use gmail_to_sheets.py to fetch and process emails!")
    else:
        print("\n✓ Already authenticated!")
        print("You're ready to use gmail_to_sheets.py")

    print("\n" + "="*80)

def get_gmail_service():
    """
    Get authenticated Gmail service for API calls

    Returns:
        Gmail service object or None if authentication fails
    """
    from googleapiclient.discovery import build

    token_file = 'credentials/gmail_token.pickle'

    if not os.path.exists(token_file):
        print("✗ Error: Not authenticated with Gmail!")
        print("Run: python3 gmail_auth.py")
        return None

    with open(token_file, 'rb') as token:
        creds = pickle.load(token)

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

if __name__ == '__main__':
    authenticate_gmail()
