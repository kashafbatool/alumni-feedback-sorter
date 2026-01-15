#!/usr/bin/env python3
"""
Send Weekly Summary Now - Manual Trigger Script

This script manually sends a weekly summary email for testing purposes.
Use this to test the email functionality without waiting for Monday morning.

Usage:
    python3 send_summary_now.py

This will send a summary for the previous 7 days immediately.
"""

import sys
from datetime import datetime, timedelta
from gmail_auth import get_gmail_service
from email_sender import send_weekly_summary
import email_config

def main():
    """Manually send weekly summary email"""

    print("\n" + "="*80)
    print("SEND WEEKLY SUMMARY NOW - MANUAL TRIGGER")
    print("="*80)

    # Get authenticated Gmail service
    print("\nAuthenticating with Gmail...")
    service = get_gmail_service()

    if not service:
        print("\n✗ Authentication failed!")
        print("Run: python3 gmail_auth.py")
        sys.exit(1)

    print("✓ Authentication successful")

    # Calculate date range (previous 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    print("\n" + "="*80)
    print("EMAIL DETAILS")
    print("="*80)
    print(f"From: {email_config.SENDER_NAME}")
    print(f"To: {email_config.RECIPIENT_EMAIL}")
    print(f"Date Range: {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}")
    print(f"Data Source: Google Sheets")

    # Confirm before sending
    response = input("\nSend this email now? (yes/no): ").strip().lower()

    if response not in ['yes', 'y']:
        print("\nCancelled. No email was sent.")
        sys.exit(0)

    # Send the email
    print("\nSending email...")
    success, message = send_weekly_summary(
        service,
        email_config.RECIPIENT_EMAIL,
        email_config.SPREADSHEET_URL,
        start_date,
        end_date
    )

    if success:
        print("\n" + "="*80)
        print("✓ SUCCESS!")
        print("="*80)
        print(f"\nWeekly summary email sent to: {email_config.RECIPIENT_EMAIL}")
        print("Check the inbox to verify it arrived correctly.")
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("✗ FAILED")
        print("="*80)
        print(f"\nError: {message}")
        print("\nTroubleshooting:")
        print("1. Make sure Gmail authentication has 'send' scope")
        print("2. Run: rm credentials/gmail_token.pickle && python3 gmail_auth.py")
        print("3. Try sending again")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
