#!/usr/bin/env python3
"""
Check how many unread emails are in Gmail
"""

from gmail_to_sheets import get_gmail_service
import sys

print("="*80)
print("CHECKING UNREAD EMAILS IN GMAIL")
print("="*80)

service = get_gmail_service()
if not service:
    print("✗ Failed to authenticate with Gmail")
    print("Run: python3 gmail_auth.py")
    sys.exit(1)

print("✓ Authenticated with Gmail")

try:
    # Get count of unread messages
    results = service.users().messages().list(
        userId='me',
        q='is:unread',
        maxResults=1
    ).execute()

    messages = results.get('messages', [])
    result_size_estimate = results.get('resultSizeEstimate', 0)

    print(f"\n✓ Found approximately {result_size_estimate} unread emails")

    if result_size_estimate == 0:
        print("\n" + "="*80)
        print("NO UNREAD EMAILS FOUND")
        print("="*80)
        print("\nThis is why you're not seeing changes in the Google Sheet!")
        print("The new code works, but there are no new emails to process.")
        print("\nOptions:")
        print("1. Send a test email to inboxtest33@gmail.com with keywords like:")
        print("   'I would like to make a gift and add you to my will'")
        print("2. Or mark some existing emails as unread in Gmail")
        print("3. Then run: python3 gmail_to_sheets.py YOUR_SHEET_URL")
    else:
        print("\n✓ There ARE unread emails to process!")
        print("\nRun this command to process them:")
        print("python3 gmail_to_sheets.py https://docs.google.com/spreadsheets/d/1R6H2gC-lazqw0dvlBdAonqinnw7QlKLe_1uFfSqBL08/edit")

    print("="*80)

except Exception as e:
    print(f"✗ Error checking emails: {e}")
    sys.exit(1)
