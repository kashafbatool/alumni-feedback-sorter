"""
Gmail API Email Fetcher
Fetches emails from Gmail inbox using OAuth2 authentication
"""

import os
import base64
import json
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pandas as pd

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Credentials file paths
CLIENT_SECRET_FILE = 'credentials/client_secret.json'
TOKEN_FILE = 'credentials/token.json'


def authenticate_gmail():
    """
    Authenticate with Gmail API using OAuth2
    Returns authenticated Gmail service
    """
    creds = None

    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for future use
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    # Build Gmail service
    service = build('gmail', 'v1', credentials=creds)
    return service


def get_email_body(payload):
    """
    Extract email body from message payload
    Handles both plain text and HTML content
    """
    body = ""

    if 'parts' in payload:
        # Multi-part message
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
            elif part['mimeType'] == 'text/html' and not body:
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
    else:
        # Single part message
        if 'data' in payload['body']:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

    return body


def get_header_value(headers, name):
    """
    Extract specific header value from email headers
    """
    for header in headers:
        if header['name'].lower() == name.lower():
            return header['value']
    return ""


def fetch_emails(service, max_results=100, days_back=30, query=None):
    """
    Fetch emails from Gmail inbox

    Args:
        service: Authenticated Gmail service
        max_results: Maximum number of emails to fetch
        days_back: Number of days to look back for emails
        query: Gmail search query (optional, e.g., "is:unread" or "from:example@gmail.com")

    Returns:
        pandas DataFrame with email data
    """
    try:
        # Calculate date for query
        date_filter = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')

        # Build query
        if query:
            search_query = f"{query} after:{date_filter}"
        else:
            search_query = f"in:inbox after:{date_filter}"

        # Fetch message list
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            q=search_query
        ).execute()

        messages = results.get('messages', [])

        if not messages:
            print("No messages found.")
            return pd.DataFrame()

        print(f"Found {len(messages)} messages. Fetching details...")

        # Fetch full message details
        emails_data = []

        for i, message in enumerate(messages, 1):
            msg = service.users().messages().get(
                userId='me',
                id=message['id'],
                format='full'
            ).execute()

            # Extract headers
            headers = msg['payload']['headers']
            subject = get_header_value(headers, 'Subject')
            from_email = get_header_value(headers, 'From')
            date = get_header_value(headers, 'Date')

            # Extract body
            body = get_email_body(msg['payload'])

            # Parse sender info
            sender_name = ""
            sender_email = ""
            if '<' in from_email and '>' in from_email:
                sender_name = from_email.split('<')[0].strip().strip('"')
                sender_email = from_email.split('<')[1].split('>')[0].strip()
            else:
                sender_email = from_email

            # Parse first and last name
            first_name = ""
            last_name = ""
            if sender_name:
                name_parts = sender_name.split()
                if len(name_parts) > 0:
                    first_name = name_parts[0]
                if len(name_parts) > 1:
                    last_name = ' '.join(name_parts[1:])

            emails_data.append({
                'First Name': first_name,
                'Last Name': last_name,
                'Email Address': sender_email,
                'Body': body,
                'Subject': subject,
                'Date Received': date,
                'Received By': 'inboxtest33@gmail.com',
                'Contact Method': 'Email',
                'Constituent?': '',
                'Assigned To': ''
            })

            if i % 10 == 0:
                print(f"Processed {i}/{len(messages)} emails...")

        print(f"Successfully fetched {len(emails_data)} emails")

        # Create DataFrame
        df = pd.DataFrame(emails_data)
        return df

    except Exception as e:
        print(f"Error fetching emails: {str(e)}")
        raise


def save_emails_to_csv(df, output_file='fetched_emails.csv'):
    """
    Save fetched emails to CSV file
    """
    df.to_csv(output_file, index=False)
    print(f"Emails saved to {output_file}")


if __name__ == "__main__":
    # Test the Gmail fetcher
    print("Authenticating with Gmail...")
    service = authenticate_gmail()

    print("\nFetching emails from inbox...")
    emails_df = fetch_emails(service, max_results=50, days_back=30)

    if not emails_df.empty:
        print(f"\nFetched {len(emails_df)} emails")
        print("\nFirst few emails:")
        print(emails_df[['First Name', 'Last Name', 'Email Address', 'Subject']].head())

        # Save to CSV
        save_emails_to_csv(emails_df)
