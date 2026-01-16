"""
Check Untracked Label in Inbox

This script specifically checks what emails are visible in the inbox
with the Untracked label, matching what you see in Gmail UI.
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
    print("CHECKING UNTRACKED EMAILS IN INBOX")
    print("=" * 80)

    service = get_gmail_service()

    # Get the Untracked label ID
    labels = service.users().labels().list(userId='me').execute()
    untracked_label = None

    for label in labels.get('labels', []):
        if label['name'].lower() == 'untracked':
            untracked_label = label
            break

    if not untracked_label:
        print("✗ Untracked label not found!")
        return

    print(f"\n✓ Found Untracked label (ID: {untracked_label['id']})")

    # Check 1: All emails with Untracked label (regardless of read/unread)
    print("\n" + "="*80)
    print("CHECK 1: ALL EMAILS WITH UNTRACKED LABEL")
    print("="*80)

    results = service.users().messages().list(
        userId='me',
        labelIds=[untracked_label['id']],
        maxResults=500
    ).execute()

    all_untracked = results.get('messages', [])
    print(f"\nTotal emails with Untracked label: {len(all_untracked)}")

    # Check 2: Untracked emails that are UNREAD
    print("\n" + "="*80)
    print("CHECK 2: UNREAD EMAILS WITH UNTRACKED LABEL")
    print("="*80)

    results = service.users().messages().list(
        userId='me',
        q=f'label:{untracked_label["id"]} is:unread',
        maxResults=500
    ).execute()

    unread_untracked = results.get('messages', [])
    print(f"\nUnread emails with Untracked: {len(unread_untracked)}")

    # Check 3: Untracked emails in INBOX
    print("\n" + "="*80)
    print("CHECK 3: UNTRACKED EMAILS IN INBOX (what you see in Gmail)")
    print("="*80)

    results = service.users().messages().list(
        userId='me',
        q=f'label:{untracked_label["id"]} in:inbox',
        maxResults=500
    ).execute()

    inbox_untracked = results.get('messages', [])
    print(f"\nUntracked emails visible in inbox: {len(inbox_untracked)}")

    if inbox_untracked:
        print("\nList of emails visible in inbox with Untracked label:")
        print("-" * 80)
        for i, msg in enumerate(inbox_untracked, 1):
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
            labels = message.get('labelIds', [])

            is_unread = 'UNREAD' in labels
            status = "UNREAD" if is_unread else "READ"

            print(f"\n{i}. [{status}]")
            print(f"   From: {from_addr}")
            print(f"   Subject: {subject}")
            print(f"   Date: {date}")

    # Check 4: Where are the other emails?
    print("\n" + "="*80)
    print("CHECK 4: WHERE ARE THE OTHER UNTRACKED EMAILS?")
    print("="*80)

    # Check archived emails with Untracked
    results = service.users().messages().list(
        userId='me',
        q=f'label:{untracked_label["id"]} -in:inbox',
        maxResults=500
    ).execute()

    archived_untracked = results.get('messages', [])
    print(f"\nUntracked emails NOT in inbox (archived/deleted): {len(archived_untracked)}")

    if archived_untracked:
        print("\nSample of archived Untracked emails:")
        for i, msg in enumerate(archived_untracked[:5], 1):
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject']
            ).execute()

            headers = message['payload']['headers']
            from_addr = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No subject')

            print(f"\n   {i}. From: {from_addr}")
            print(f"      Subject: {subject}")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\nTotal Untracked emails: {len(all_untracked)}")
    print(f"  - In inbox (visible): {len(inbox_untracked)}")
    print(f"  - Archived/elsewhere: {len(archived_untracked)}")
    print(f"  - Unread: {len(unread_untracked)}")
    print(f"  - Read: {len(all_untracked) - len(unread_untracked)}")

if __name__ == '__main__':
    main()
