"""
Gmail Label Manager for Filtered Emails

This script adds a "Filtered Out" label to emails that are identified
as administrative/irrelevant by the filtering system.

Usage:
    python3 gmail_label_filtered.py
"""

import os
import pickle
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

def get_gmail_service():
    """Authenticate and return Gmail service with modify permissions"""
    token_file = 'credentials/gmail_token_modify.pickle'

    if not os.path.exists(token_file):
        print("✗ Error: Not authenticated with Gmail modify permissions!")
        print("Run: python3 gmail_auth_modify.py")
        return None

    with open(token_file, 'rb') as token:
        creds = pickle.load(token)

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

def get_or_create_label(service, label_name):
    """
    Get existing label ID or create new label

    Args:
        service: Gmail API service instance
        label_name: Name of the label to get/create

    Returns:
        Label ID string
    """
    try:
        # Get all labels
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        # Check if label already exists
        for label in labels:
            if label['name'] == label_name:
                print(f"   ✓ Found existing label: '{label_name}'")
                return label['id']

        # Create new label if it doesn't exist
        print(f"   → Creating new label: '{label_name}'")
        label_object = {
            'name': label_name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }

        created_label = service.users().labels().create(
            userId='me',
            body=label_object
        ).execute()

        print(f"   ✓ Label created successfully")
        return created_label['id']

    except Exception as e:
        print(f"   ✗ Error with label: {e}")
        return None

def add_label_to_messages(service, message_ids, label_id):
    """
    Add label to multiple messages

    Args:
        service: Gmail API service instance
        message_ids: List of message IDs
        label_id: Label ID to add
    """
    if not message_ids:
        return

    try:
        service.users().messages().batchModify(
            userId='me',
            body={
                'ids': message_ids,
                'addLabelIds': [label_id]
            }
        ).execute()
        print(f"   ✓ Labeled {len(message_ids)} emails as 'Filtered Out'")
    except Exception as e:
        print(f"   ✗ Error adding labels: {e}")

if __name__ == '__main__':
    print("="*80)
    print("GMAIL LABEL MANAGER")
    print("="*80)
    print("\nThis script requires gmail.modify permissions.")
    print("Make sure you've run gmail_auth_modify.py first!")
    print("="*80)
