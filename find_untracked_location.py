"""
Find where Untracked emails actually are in Gmail
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
    print("FINDING WHERE UNTRACKED EMAILS ARE LOCATED")
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

    # Get all 29 Untracked emails
    results = service.users().messages().list(
        userId='me',
        labelIds=[untracked_label['id']],
        maxResults=500
    ).execute()

    all_untracked = results.get('messages', [])
    print(f"\nTotal Untracked emails: {len(all_untracked)}")

    # Check each email's labels to see where they are
    locations = {
        'INBOX': 0,
        'UNREAD': 0,
        'IMPORTANT': 0,
        'STARRED': 0,
        'TRASH': 0,
        'SPAM': 0,
        'SENT': 0,
        'DRAFT': 0,
        'OTHER': 0
    }

    print("\n" + "="*80)
    print("ANALYZING ALL 29 UNTRACKED EMAILS")
    print("="*80)

    for i, msg in enumerate(all_untracked, 1):
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
        label_ids = message.get('labelIds', [])

        # Check which standard labels this email has
        in_inbox = 'INBOX' in label_ids
        is_unread = 'UNREAD' in label_ids
        is_important = 'IMPORTANT' in label_ids
        is_starred = 'STARRED' in label_ids
        is_trash = 'TRASH' in label_ids
        is_spam = 'SPAM' in label_ids

        # Count locations
        if in_inbox:
            locations['INBOX'] += 1
        if is_unread:
            locations['UNREAD'] += 1
        if is_important:
            locations['IMPORTANT'] += 1
        if is_starred:
            locations['STARRED'] += 1
        if is_trash:
            locations['TRASH'] += 1
        if is_spam:
            locations['SPAM'] += 1

        # Determine primary location
        if is_trash:
            location = "TRASH"
        elif is_spam:
            location = "SPAM"
        elif in_inbox:
            if is_unread:
                location = "INBOX (UNREAD)"
            else:
                location = "INBOX (READ)"
        else:
            location = "ARCHIVED"

        print(f"\n{i}. {location}")
        print(f"   From: {from_addr}")
        print(f"   Subject: {subject}")
        print(f"   Date: {date}")
        print(f"   Labels: {', '.join([l for l in label_ids if l.startswith('Label_') or l in ['INBOX', 'UNREAD', 'IMPORTANT', 'STARRED', 'TRASH', 'SPAM']])}")

    # Summary
    print("\n" + "="*80)
    print("LOCATION SUMMARY")
    print("="*80)
    print(f"\nOut of {len(all_untracked)} Untracked emails:")
    print(f"  - In INBOX: {locations['INBOX']}")
    print(f"  - UNREAD: {locations['UNREAD']}")
    print(f"  - IMPORTANT: {locations['IMPORTANT']}")
    print(f"  - In TRASH: {locations['TRASH']}")
    print(f"  - In SPAM: {locations['SPAM']}")
    print(f"  - Archived (not in inbox): {len(all_untracked) - locations['INBOX'] - locations['TRASH'] - locations['SPAM']}")

if __name__ == '__main__':
    main()
