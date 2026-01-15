"""
Gmail to Google Sheets - Automated Email Processor

This script:
1. Fetches unread emails from your Gmail inbox
2. Filters out administrative emails
3. Analyzes sentiment and intent
4. Uploads results to Google Sheets
5. Marks processed emails as read

Usage:
    python3 gmail_to_sheets.py SPREADSHEET_URL
"""

import os
import sys
import pickle
import base64
import re
from datetime import datetime
from email.utils import parseaddr
import pandas as pd
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Import your existing modules
from email_brain import analyze_email
from only_filter import should_filter

def get_gmail_service():
    """Authenticate and return Gmail service"""
    token_file = 'credentials/gmail_token.pickle'

    if not os.path.exists(token_file):
        print("✗ Error: Not authenticated with Gmail!")
        print("Run: python3 gmail_auth.py")
        return None

    with open(token_file, 'rb') as token:
        creds = pickle.load(token)

    # Check if credentials are valid
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Try to refresh the token
            try:
                print("   ↻ Refreshing expired Gmail token...")
                creds.refresh(Request())
                with open(token_file, 'wb') as token:
                    pickle.dump(creds, token)
                print("   ✓ Token refreshed successfully")
            except Exception as e:
                print(f"   ✗ Token refresh failed: {e}")
                print("   Please re-authenticate by running: python3 gmail_auth.py")
                return None
        else:
            # No refresh token available - need to re-authenticate
            print("✗ Error: Gmail token is invalid and cannot be refreshed!")
            print("Run: python3 gmail_auth.py")
            return None

    return build('gmail', 'v1', credentials=creds)

def extract_name_from_email(email_string):
    """Extract name and email from 'Name <email@domain.com>' format"""
    name, email = parseaddr(email_string)

    if name:
        # Split name into first and last
        parts = name.split()
        first_name = parts[0] if parts else ""
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
    else:
        # If no name, try to extract from email
        first_name = email.split('@')[0] if '@' in email else ""
        last_name = ""

    return first_name, last_name, email

def get_email_body(payload):
    """Extract email body from Gmail message payload"""
    if 'parts' in payload:
        # Multi-part message
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    else:
        # Simple message
        data = payload['body'].get('data', '')
        if data:
            return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

    return ""

def fetch_unread_emails(service, max_results=500):
    """Fetch unread emails from Gmail inbox with pagination"""
    print("\n1. Fetching unread emails from Gmail...")

    try:
        # Get list of unread messages with pagination
        messages = []
        page_token = None

        while True:
            results = service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=100,  # Fetch 100 at a time
                pageToken=page_token
            ).execute()

            batch_messages = results.get('messages', [])
            messages.extend(batch_messages)

            # Check if there are more pages
            page_token = results.get('nextPageToken')
            if not page_token:
                break  # No more pages

            # Stop if we've reached max_results
            if len(messages) >= max_results:
                messages = messages[:max_results]
                break

        if not messages:
            print("   ✓ No unread emails found")
            return []

        print(f"   ✓ Found {len(messages)} unread emails")

        # Fetch full details for each message
        emails = []
        for msg in messages:
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()

            # Extract headers
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            from_addr = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')

            # Extract name and email
            first_name, last_name, email_addr = extract_name_from_email(from_addr)

            # Skip system emails (service accounts, no-reply, etc.)
            if any(skip in email_addr.lower() for skip in ['gserviceaccount.com', 'noreply', 'no-reply', 'donotreply']):
                continue

            # Extract body
            body = get_email_body(message['payload'])

            # Skip emails with no meaningful content (too short or empty)
            if not body or len(body.strip()) < 20:
                continue

            # Parse date (keep full datetime for sorting, then format)
            try:
                # Parse the full date to get accurate timestamp
                from email.utils import parsedate_to_datetime
                date_obj = parsedate_to_datetime(date_str)
                date_received = date_obj.strftime('%Y-%m-%d')
                timestamp = date_obj.timestamp()
            except:
                date_received = datetime.today().strftime('%Y-%m-%d')
                timestamp = datetime.today().timestamp()

            emails.append({
                'id': msg['id'],
                'First Name': first_name,
                'Last Name': last_name,
                'Email Address': email_addr,
                'Subject': subject,
                'Body': body,
                'Date Received': date_received,
                'timestamp': timestamp
            })

        # Sort by timestamp (oldest first)
        emails.sort(key=lambda x: x.get('timestamp', 0))

        # Remove timestamp before returning (not needed in final output)
        for email in emails:
            email.pop('timestamp', None)

        return emails

    except Exception as e:
        print(f"   ✗ Error fetching emails: {e}")
        return []

def mark_as_read(service, message_ids):
    """Mark messages as read"""
    if not message_ids:
        return

    try:
        service.users().messages().batchModify(
            userId='me',
            body={
                'ids': message_ids,
                'removeLabelIds': ['UNREAD']
            }
        ).execute()
        print(f"   ✓ Marked {len(message_ids)} emails as read")
    except Exception as e:
        print(f"   ⚠ Warning: Could not mark emails as read: {e}")

def apply_filtered_label(service, message_ids):
    """Apply 'Untracked' label to messages"""
    if not message_ids:
        return

    try:
        # Get all labels to find the 'Untracked' label ID
        labels = service.users().labels().list(userId='me').execute()
        label_id = None

        for label in labels.get('labels', []):
            if label['name'].lower() == 'untracked':
                label_id = label['id']
                break

        if not label_id:
            print(f"   ⚠ Warning: 'Untracked' label not found in Gmail")
            return

        # Apply the label to all filtered messages AND remove from inbox
        service.users().messages().batchModify(
            userId='me',
            body={
                'ids': message_ids,
                'addLabelIds': [label_id],
                'removeLabelIds': ['INBOX']  # Move emails out of inbox
            }
        ).execute()
        print(f"   ✓ Applied 'Untracked' label and moved {len(message_ids)} emails out of inbox")
    except Exception as e:
        print(f"   ⚠ Warning: Could not apply label: {e}")

def process_and_upload(spreadsheet_url):
    """Main processing pipeline"""
    print("="*80)
    print("GMAIL TO GOOGLE SHEETS - AUTOMATED EMAIL PROCESSOR")
    print("="*80)

    # Get Gmail service
    service = get_gmail_service()
    if not service:
        return

    # Fetch unread emails
    emails = fetch_unread_emails(service)

    if not emails:
        print("\n✓ No emails to process")
        return

    # Convert to DataFrame
    df = pd.DataFrame(emails)
    message_ids = df['id'].tolist()

    print(f"\n2. Pre-filtering emails...")
    df['Should_Filter'] = df['Body'].apply(lambda x: should_filter(x, subject=""))

    filtered_out = df[df['Should_Filter'] == True]
    emails_to_process = df[df['Should_Filter'] == False]

    # Get message IDs for filtered emails
    filtered_message_ids = filtered_out['id'].tolist() if len(filtered_out) > 0 else []

    # Now drop the id column for processing
    df = df.drop('id', axis=1)
    filtered_out = filtered_out.drop('id', axis=1) if len(filtered_out) > 0 else filtered_out
    emails_to_process = emails_to_process.drop('id', axis=1) if len(emails_to_process) > 0 else emails_to_process

    print(f"   - Filtered out (admin/irrelevant): {len(filtered_out)}")
    print(f"   - Kept for analysis (real feedback): {len(emails_to_process)}")

    # Apply 'Untracked' label to filtered emails
    if len(filtered_message_ids) > 0:
        print(f"\n   Applying 'Untracked' label to {len(filtered_message_ids)} emails...")
        apply_filtered_label(service, filtered_message_ids)

    if len(emails_to_process) == 0:
        print("\n✓ All emails were administrative/irrelevant")
        return

    # Analyze sentiment
    print(f"\n3. Analyzing {len(emails_to_process)} emails for sentiment and intent...")

    # Analyze each email and ensure we get proper results
    analyzed_results = []
    for idx, body in emails_to_process['Body'].items():
        try:
            result = analyze_email(body)
            if result is None or not isinstance(result, dict):
                # If analysis failed, provide default values
                result = {
                    'Pos_sentiment': 'No',
                    'Neg_sentiment': 'No',
                    'Donate_Intent': 'No',
                    'Giving_Status': 'No',
                    'Positive_Giving_Status': 'No'
                }
            analyzed_results.append(result)
        except Exception as e:
            print(f"   ⚠ Warning: Analysis failed for one email: {e}")
            # Default to negative sentiment for failed analysis
            analyzed_results.append({
                'Pos_sentiment': 'No',
                'Neg_sentiment': 'Yes',
                'Donate_Intent': 'No',
                'Giving_Status': 'No',
                'Positive_Giving_Status': 'No'
            })

    results = pd.DataFrame(analyzed_results)

    # Create formatted output
    formatted_df = pd.DataFrame()
    formatted_df['First Name'] = emails_to_process['First Name'].values
    formatted_df['Last Name'] = emails_to_process['Last Name'].values
    formatted_df['Email Address'] = emails_to_process['Email Address'].values

    def determine_sentiment(row):
        # Return Positive, Negative, or Neutral (never empty/null/NaN)
        try:
            pos = str(row['Pos_sentiment']).strip() if pd.notna(row.get('Pos_sentiment')) else 'No'
            neg = str(row['Neg_sentiment']).strip() if pd.notna(row.get('Neg_sentiment')) else 'No'
            giving_status = str(row.get('Giving_Status', '')).strip()
            positive_giving = str(row.get('Positive_Giving_Status', '')).strip()
        except:
            # If anything goes wrong, default to Neutral
            return 'Neutral'

        # PRIORITY 1: If they're making gifts/adding bequests, it's ALWAYS Positive
        # Check if positive_giving contains any of the positive keywords (handles comma-separated values)
        if any(status in positive_giving for status in ['Making gift', 'Resumed giving', 'Added bequest']):
            return 'Positive'

        # PRIORITY 2: If they're stopping giving or removing bequest, it's ALWAYS Negative
        # Even if they use polite/appreciative language
        if giving_status in ['Paused giving', 'Removed bequest']:
            return 'Negative'

        # If negative detected, return Negative
        if neg == 'Yes':
            return 'Negative'
        # If positive detected, return Positive
        elif pos == 'Yes':
            return 'Positive'
        # If both are Null/No, it's truly neutral
        else:
            return 'Neutral'

    formatted_df['Positive or Negative?'] = results.apply(determine_sentiment, axis=1).fillna('Neutral')
    formatted_df['Received By'] = ''
    formatted_df['Date Received'] = emails_to_process['Date Received'].values
    formatted_df['Received by Email, Phone, or in Person?'] = ''
    formatted_df['Email Text/Synopsis of Conversation/Notes'] = emails_to_process['Body'].values
    formatted_df['Paused Giving OR Changed bequest intent?'] = results['Giving_Status'].values
    formatted_df['Making gift, resuming giving, or revising their will to add the College'] = results['Positive_Giving_Status'].values
    formatted_df['Constituent?'] = ''
    formatted_df['RM or team member assigned for Response'] = ''
    formatted_df['Response Complete?'] = ''
    formatted_df['Date of Response'] = ''
    formatted_df['Imported in RE? (Grace will update this column)'] = ''

    # Save to Excel
    formatted_df.to_excel("Alumni_Feedback_Report_Gmail.xlsx", index=False)
    print(f"   ✓ Analysis complete")

    # Group emails by month/year and upload to separate tabs
    print(f"\n4. Uploading to Google Sheets...")

    # Convert Date Received to datetime and extract month/year
    formatted_df['Date Received'] = pd.to_datetime(formatted_df['Date Received'])
    formatted_df['Month_Year'] = formatted_df['Date Received'].dt.strftime('%b %Y').str.lower()

    # Group by month/year
    grouped = formatted_df.groupby('Month_Year')

    print(f"   Found emails from {len(grouped)} different months")

    import subprocess
    upload_success = True

    for month_year, group_df in grouped:
        # Convert Date Received back to date-only format (remove time)
        group_df['Date Received'] = group_df['Date Received'].dt.strftime('%Y-%m-%d')

        # Remove the helper column before uploading
        group_df = group_df.drop('Month_Year', axis=1)

        # Save to temporary Excel file for this month
        temp_file = f"Alumni_Feedback_Report_Gmail_{month_year.replace(' ', '_')}.xlsx"
        group_df.to_excel(temp_file, index=False)

        print(f"   Uploading {len(group_df)} emails to '{month_year}' tab...")

        result = subprocess.run(
            ['python3', 'sheets_uploader.py', spreadsheet_url, month_year],
            capture_output=True,
            text=True,
            env={**os.environ, 'GMAIL_UPLOAD': 'true', 'TEMP_FILE': temp_file}
        )

        if result.returncode != 0:
            upload_success = False
            print(f"   ✗ Upload failed for '{month_year}'")
            if result.stderr:
                print(f"      Error: {result.stderr}")

    if upload_success:
        print("   ✓ All uploads successful!")

        print("\n" + "="*80)
        print("✓ SUCCESS! All emails processed and uploaded to Google Sheets")
        print("="*80)
        print(f"\nProcessed: {len(emails_to_process)} emails")
        print(f"Filtered: {len(filtered_out)} emails")
        print(f"\nView sheet: {spreadsheet_url}")
    else:
        print(f"   ✗ Upload failed: {result.stderr}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("   python3 gmail_to_sheets.py YOUR_SPREADSHEET_URL")
        print("\nExample:")
        print("   python3 gmail_to_sheets.py https://docs.google.com/spreadsheets/d/ABC123.../edit")
        sys.exit(1)

    spreadsheet_url = sys.argv[1]
    process_and_upload(spreadsheet_url)
