"""
Automated Gmail to Google Sheets Processor

This script runs continuously and automatically checks for new emails
every few minutes, processes them, and uploads to Google Sheets.

Usage:
    python3 gmail_auto_processor.py SPREADSHEET_URL [CHECK_INTERVAL_MINUTES]

Example:
    python3 gmail_auto_processor.py "https://docs.google.com/spreadsheets/d/ABC.../edit" 5
"""

import sys
import time
from datetime import datetime
from gmail_to_sheets import process_and_upload

def run_continuous(spreadsheet_url, check_interval_minutes=5):
    """
    Run the email processor continuously

    Args:
        spreadsheet_url: Google Sheets URL to upload to
        check_interval_minutes: How often to check for new emails (default: 5 minutes)
    """

    print("="*80)
    print("AUTOMATED GMAIL PROCESSOR - RUNNING CONTINUOUSLY")
    print("="*80)
    print(f"\nChecking for new emails every {check_interval_minutes} minutes")
    print(f"Uploading to: {spreadsheet_url}")
    print(f"\nPress Ctrl+C to stop\n")
    print("="*80)

    run_count = 0

    try:
        while True:
            run_count += 1
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"\n\n[Run #{run_count}] {current_time}")
            print("-"*80)

            # Process emails and upload
            try:
                process_and_upload(spreadsheet_url)
            except Exception as e:
                print(f"\n⚠ Error during processing: {e}")
                print("Will retry on next check...")

            # Wait for next check
            wait_seconds = check_interval_minutes * 60
            next_check = datetime.now()
            next_check = next_check.replace(
                minute=(next_check.minute + check_interval_minutes) % 60,
                second=0,
                microsecond=0
            )

            print(f"\n✓ Check complete. Next check at: {next_check.strftime('%H:%M:%S')}")
            print(f"Waiting {check_interval_minutes} minutes...")
            print("="*80)

            time.sleep(wait_seconds)

    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("STOPPED BY USER")
        print("="*80)
        print(f"\nTotal runs completed: {run_count}")
        print("Automated processor stopped.\n")
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("   python3 gmail_auto_processor.py SPREADSHEET_URL [CHECK_INTERVAL_MINUTES]")
        print("\nExample:")
        print("   python3 gmail_auto_processor.py \"https://docs.google.com/spreadsheets/d/ABC.../edit\" 5")
        print("\nDefault check interval: 5 minutes")
        print("\n")
        sys.exit(1)

    spreadsheet_url = sys.argv[1]
    check_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    run_continuous(spreadsheet_url, check_interval)
