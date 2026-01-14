#!/usr/bin/env python3
"""
Weekly Email Summary - Main Entry Point

This script runs the weekly email scheduler that sends summary reports
every Monday morning to the configured recipient email.

Usage:
    python3 run_weekly_emailer.py

This will start a continuous process that checks every hour if it's Monday morning.
When it is, it automatically sends the weekly summary email.

Keep this script running to ensure weekly emails are sent automatically.
Press Ctrl+C to stop.
"""

import sys
from gmail_auth import get_gmail_service
from weekly_scheduler import run_weekly_scheduler
import email_config

def main():
    """Main entry point for weekly email scheduler"""

    print("\n" + "="*80)
    print("ALUMNI FEEDBACK - WEEKLY EMAIL SUMMARY")
    print("="*80)

    # Get authenticated Gmail service
    print("\nAuthenticating with Gmail...")
    service = get_gmail_service()

    if not service:
        print("\n" + "="*80)
        print("✗ AUTHENTICATION FAILED")
        print("="*80)
        print("\nCould not authenticate with Gmail.")
        print("\nTo fix this:")
        print("1. Make sure you've run: python3 gmail_auth.py")
        print("2. Complete the OAuth flow in your browser")
        print("3. Try running this script again")
        sys.exit(1)

    print("✓ Authentication successful")

    # Display configuration
    print("\n" + "="*80)
    print("CONFIGURATION")
    print("="*80)
    print(f"Recipient: {email_config.RECIPIENT_EMAIL}")
    print(f"Send Schedule: Every Monday at {email_config.SEND_HOUR}:00 AM")
    print(f"Data Source: {email_config.SPREADSHEET_URL[:80]}...")
    print(f"Sender Name: {email_config.SENDER_NAME}")

    # Confirm before starting
    print("\n" + "="*80)
    print("READY TO START")
    print("="*80)
    print("\nThe scheduler will run continuously and send weekly summaries")
    print("every Monday morning automatically.")
    print("\nPress Ctrl+C at any time to stop the scheduler.")

    input("\nPress Enter to start the scheduler (or Ctrl+C to cancel)...")

    # Run the scheduler
    run_weekly_scheduler(
        service,
        email_config.SPREADSHEET_URL,
        email_config.RECIPIENT_EMAIL
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScheduler stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(1)
