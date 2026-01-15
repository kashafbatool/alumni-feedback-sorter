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
from topic_detector import detect_major_topics, generate_sheet_name

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
    df = df.drop('id', axis=1)  # Remove id column

    # STEP 1: Detect major topics BEFORE filtering
    print(f"\n2. Detecting major topics in {len(df)} emails...")

    # Convert to list of dicts for topic detector
    all_emails_list = df.to_dict('records')
    topic_result = detect_major_topics(all_emails_list, min_cluster_size=5)

    if topic_result['topics']:
        print(f"   ✓ Found {len(topic_result['topics'])} major topic(s):")
        for topic in topic_result['topics']:
            print(f"      - {topic['entity']}: {topic['size']} emails")
    else:
        print(f"   ✓ No major topics detected (threshold: 5 emails)")

    # STEP 2: Now filter emails (but keep topic assignments)
    print(f"\n3. Pre-filtering emails...")
    df['Should_Filter'] = df['Body'].apply(lambda x: should_filter(x, subject=""))
    df['Topic_Assignment'] = topic_result['topic_assignments']

    filtered_out = df[df['Should_Filter'] == True]
    emails_to_process = df[df['Should_Filter'] == False]

    print(f"   - Filtered out (admin/irrelevant): {len(filtered_out)}")
    print(f"   - Kept for analysis (real feedback): {len(emails_to_process)}")

    # Special handling: If an email is part of a major topic, keep it even if filtered
    topic_override_count = 0
    if topic_result['topics']:
        for idx in filtered_out.index:
            topic_idx = df.loc[idx, 'Topic_Assignment']
            if topic_idx >= 0:  # Part of a major topic
                # Move from filtered to process
                emails_to_process = pd.concat([emails_to_process, df.loc[[idx]]])
                filtered_out = filtered_out.drop(idx)
                topic_override_count += 1

        if topic_override_count > 0:
            print(f"   + Kept {topic_override_count} additional emails (part of major topics)")
            print(f"   - Final kept for analysis: {len(emails_to_process)}")

    if len(emails_to_process) == 0:
        print("\n✓ All emails were administrative/irrelevant")
        print("   Marking them as read...")
        mark_as_read(service, message_ids)
        return

    # Update topic result to only include emails we're processing
    # Map old indices to new indices
    old_to_new_idx = {old_idx: new_idx for new_idx, old_idx in enumerate(emails_to_process.index)}
    new_topic_assignments = []
    for old_idx in emails_to_process.index:
        new_topic_assignments.append(emails_to_process.loc[old_idx, 'Topic_Assignment'])

    topic_result['topic_assignments'] = new_topic_assignments
    emails_to_process = emails_to_process.drop(['Should_Filter', 'Topic_Assignment'], axis=1)

    # Analyze sentiment
    print(f"\n4. Analyzing {len(emails_to_process)} emails for sentiment and intent...")

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
                    'Giving_Status': 'No'
                }
            analyzed_results.append(result)
        except Exception as e:
            print(f"   ⚠ Warning: Analysis failed for one email: {e}")
            # Default to negative sentiment for failed analysis
            analyzed_results.append({
                'Pos_sentiment': 'No',
                'Neg_sentiment': 'Yes',
                'Donate_Intent': 'No',
                'Giving_Status': 'No'
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
        except:
            # If anything goes wrong, default to Neutral
            return 'Neutral'

        # PRIORITY: If they're stopping giving or removing bequest, it's ALWAYS Negative
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
    formatted_df['Constituent?'] = ''
    formatted_df['RM or team member assigned for Response'] = ''
    formatted_df['Response Complete?'] = ''
    formatted_df['Date of Response'] = ''
    formatted_df['Imported in RE? (Grace will update this column)'] = ''

    # Save to Excel
    formatted_df.to_excel("Alumni_Feedback_Report_Gmail.xlsx", index=False)
    print(f"   ✓ Analysis complete")

    # Split data by topic for upload
    print(f"\n5. Preparing data for upload...")

    # Separate emails by topic
    topic_assignments = topic_result['topic_assignments']
    main_sheet_data = []
    topic_sheets_data = {}  # topic_index -> DataFrame

    for idx, (orig_idx, row) in enumerate(formatted_df.iterrows()):
        topic_idx = topic_assignments[idx]
        if topic_idx >= 0:
            # This email belongs to a topic-specific sheet
            if topic_idx not in topic_sheets_data:
                topic_sheets_data[topic_idx] = []
            topic_sheets_data[topic_idx].append(row)
        else:
            # This email goes to main sheet
            main_sheet_data.append(row)

    # Create DataFrames
    main_df = pd.DataFrame(main_sheet_data) if main_sheet_data else pd.DataFrame(columns=formatted_df.columns)
    topic_dfs = {idx: pd.DataFrame(data) for idx, data in topic_sheets_data.items()}

    print(f"   - Main sheet: {len(main_df)} emails")
    for topic_idx, df in topic_dfs.items():
        topic_name = topic_result['topics'][topic_idx]['entity']
        print(f"   - {topic_name} sheet: {len(df)} emails")

    # Upload to Google Sheets
    print(f"\n6. Uploading to Google Sheets...")

    # Get current month/year for sheet naming
    from datetime import datetime
    date_str = datetime.now().strftime("%b %Y")

    # Upload main sheet
    if len(main_df) > 0:
        main_df.to_excel("Alumni_Feedback_Report_Gmail.xlsx", index=False)
        import subprocess
        result = subprocess.run(
            ['python3', 'sheets_uploader.py', spreadsheet_url, f'Alumni Feedback - {date_str}'],
            capture_output=True,
            text=True,
            env={**os.environ, 'GMAIL_UPLOAD': 'true'}
        )
        if result.returncode == 0:
            print(f"   ✓ Main sheet uploaded ({len(main_df)} emails)")
        else:
            print(f"   ✗ Main sheet upload failed: {result.stderr}")

    # Upload topic-specific sheets
    for topic_idx, topic_df in topic_dfs.items():
        topic = topic_result['topics'][topic_idx]
        sheet_name = generate_sheet_name(topic, date_str)

        # Save topic data to temp Excel
        topic_df.to_excel("Alumni_Feedback_Report_Gmail.xlsx", index=False)

        result = subprocess.run(
            ['python3', 'sheets_uploader.py', spreadsheet_url, sheet_name],
            capture_output=True,
            text=True,
            env={**os.environ, 'GMAIL_UPLOAD': 'true'}
        )

        if result.returncode == 0:
            print(f"   ✓ Topic sheet '{sheet_name}' uploaded ({len(topic_df)} emails)")
        else:
            print(f"   ⚠ Topic sheet '{sheet_name}' upload warning: {result.stderr}")

    # Mark emails as read
    print(f"\n7. Marking processed emails as read...")
    mark_as_read(service, message_ids)

    print("\n" + "="*80)
    print("✓ SUCCESS! All emails processed and uploaded to Google Sheets")
    print("="*80)
    print(f"\nProcessed: {len(emails_to_process)} emails")
    print(f"  - Main sheet: {len(main_df)} emails")
    for topic_idx, topic_df in topic_dfs.items():
        topic_name = topic_result['topics'][topic_idx]['entity']
        print(f"  - {topic_name}: {len(topic_df)} emails")
    print(f"Filtered: {len(filtered_out)} emails")
    print(f"\nView sheet: {spreadsheet_url}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("   python3 gmail_to_sheets.py YOUR_SPREADSHEET_URL")
        print("\nExample:")
        print("   python3 gmail_to_sheets.py https://docs.google.com/spreadsheets/d/ABC123.../edit")
        sys.exit(1)

    spreadsheet_url = sys.argv[1]
    process_and_upload(spreadsheet_url)
