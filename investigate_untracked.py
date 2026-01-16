"""
Investigate Untracked Label Status

This script checks:
1. Which emails currently have the Untracked label
2. Recent read emails to see if they were labeled then unlabeled
3. Sample of emails to identify filtering patterns
"""

import pickle
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

def get_gmail_service():
    """Get authenticated Gmail service"""
    token_file = 'credentials/gmail_token.pickle'

    with open(token_file, 'rb') as token:
        creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

def main():
    print("=" * 80)
    print("INVESTIGATING UNTRACKED LABEL")
    print("=" * 80)

    service = get_gmail_service()

    # 1. Get the Untracked label ID
    print("\n1. Finding Untracked label...")
    labels = service.users().labels().list(userId='me').execute()
    untracked_label = None

    for label in labels.get('labels', []):
        if label['name'].lower() == 'untracked':
            untracked_label = label
            print(f"   ✓ Found: {label['name']} (ID: {label['id']})")
            break

    if not untracked_label:
        print("   ✗ Untracked label not found!")
        return

    # 2. Check emails with Untracked label
    print("\n2. Checking emails with Untracked label...")
    try:
        results = service.users().messages().list(
            userId='me',
            labelIds=[untracked_label['id']],
            maxResults=100
        ).execute()

        messages = results.get('messages', [])
        print(f"   Found {len(messages)} emails with Untracked label")

        if messages:
            # Show first 5 as sample
            print("\n   Sample emails with Untracked label:")
            for i, msg in enumerate(messages[:5]):
                message = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()

                headers = message['payload']['headers']
                from_addr = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No subject')
                date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown')

                print(f"\n   Email {i+1}:")
                print(f"     From: {from_addr}")
                print(f"     Subject: {subject}")
                print(f"     Date: {date}")
                print(f"     Labels: {message.get('labelIds', [])}")

    except Exception as e:
        print(f"   ✗ Error: {e}")

    # 3. Check recent unread emails to see what's currently in inbox
    print("\n3. Checking current unread emails...")
    try:
        results = service.users().messages().list(
            userId='me',
            q='is:unread',
            maxResults=10
        ).execute()

        messages = results.get('messages', [])
        print(f"   Found {len(messages)} unread emails currently")

        if messages:
            print("\n   Sample current unread emails:")
            for i, msg in enumerate(messages[:3]):
                message = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject']
                ).execute()

                headers = message['payload']['headers']
                from_addr = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No subject')
                labels = message.get('labelIds', [])

                has_untracked = untracked_label['id'] in labels

                print(f"\n   Email {i+1}:")
                print(f"     From: {from_addr}")
                print(f"     Subject: {subject}")
                print(f"     Has Untracked: {has_untracked}")
                print(f"     Labels: {labels}")

    except Exception as e:
        print(f"   ✗ Error: {e}")

    # 4. Check all read emails from last 24 hours
    print("\n4. Checking recently read emails (last 24 hours)...")
    try:
        results = service.users().messages().list(
            userId='me',
            q='is:read newer_than:1d',
            maxResults=100
        ).execute()

        messages = results.get('messages', [])
        print(f"   Found {len(messages)} recently read emails")

        # Count how many have Untracked label
        untracked_count = 0
        for msg in messages:
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='minimal'
            ).execute()

            if untracked_label['id'] in message.get('labelIds', []):
                untracked_count += 1

        print(f"   {untracked_count} of them have Untracked label ({untracked_count/len(messages)*100:.1f}%)")

    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n" + "=" * 80)
    print("INVESTIGATION COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
