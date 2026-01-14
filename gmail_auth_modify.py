"""
Gmail Authentication Script with Modify Permissions

This script authenticates your Gmail account with permissions to:
- Read emails
- Modify labels
- Mark emails as read

Run this to enable labeling of filtered emails.
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Gmail API scope - allows reading and modifying emails
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def authenticate_gmail():
    """
    Authenticate with Gmail and create token file with modify permissions
    """
    print("="*80)
    print("GMAIL AUTHENTICATION WITH MODIFY PERMISSIONS")
    print("="*80)

    creds = None
    token_file = 'credentials/gmail_token_modify.pickle'
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
            print("\nPermissions being requested:")
            print("  - Read emails")
            print("  - Modify labels")
            print("  - Mark emails as read")
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
        print("You can now use the labeling features!")
    else:
        print("\n✓ Already authenticated with modify permissions!")
        print("You're ready to use the labeling features")

    print("\n" + "="*80)

if __name__ == '__main__':
    authenticate_gmail()
