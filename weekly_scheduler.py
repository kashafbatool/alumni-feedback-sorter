"""
Weekly Scheduler Module

This module handles scheduling and triggering weekly email sends every Monday morning.
It tracks sent emails to prevent duplicates and includes retry logic.
"""

import json
import time
from datetime import datetime, timedelta
import os
import email_config
from email_sender import send_weekly_summary

# File to track sent summaries
SENT_SUMMARIES_FILE = "sent_summaries.json"

def get_previous_week_range():
    """
    Calculate the previous week's date range (Sunday to Saturday)

    Returns:
        Tuple of (start_date, end_date) as datetime objects
    """
    today = datetime.now()

    # Get last Sunday
    days_since_sunday = (today.weekday() + 1) % 7  # Monday = 0, Sunday = 6
    last_sunday = today - timedelta(days=days_since_sunday + 7)  # Go back to previous week's Sunday
    last_sunday = last_sunday.replace(hour=0, minute=0, second=0, microsecond=0)

    # Get last Saturday (6 days after Sunday)
    last_saturday = last_sunday + timedelta(days=6)
    last_saturday = last_saturday.replace(hour=23, minute=59, second=59, microsecond=999999)

    return last_sunday, last_saturday

def is_monday_morning():
    """
    Check if current time is Monday morning at the configured send time

    Returns:
        Boolean indicating if it's time to send weekly summary
    """
    now = datetime.now()

    # Check if it's Monday (weekday 0)
    if now.weekday() != email_config.SEND_DAY:
        return False

    # Check if it's the right hour
    if now.hour != email_config.SEND_HOUR:
        return False

    # Check if we're within the first few minutes of the hour
    # (Allow 10 minute window to account for scheduling delays)
    if now.minute > 10:
        return False

    return True

def load_sent_summaries():
    """
    Load the record of previously sent summaries

    Returns:
        Dictionary of sent summaries {week_key: timestamp}
    """
    if not os.path.exists(SENT_SUMMARIES_FILE):
        return {}

    try:
        with open(SENT_SUMMARIES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load sent summaries file: {e}")
        return {}

def save_sent_summaries(sent_summaries):
    """
    Save the record of sent summaries

    Args:
        sent_summaries: Dictionary of sent summaries to save
    """
    try:
        with open(SENT_SUMMARIES_FILE, 'w') as f:
            json.dump(sent_summaries, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save sent summaries file: {e}")

def mark_email_sent(week_start_date):
    """
    Mark that an email was sent for a specific week

    Args:
        week_start_date: datetime object for the start of the week
    """
    # Create unique key for the week (e.g., "2026-01-05")
    week_key = week_start_date.strftime('%Y-%m-%d')

    # Load existing records
    sent_summaries = load_sent_summaries()

    # Add new record
    sent_summaries[week_key] = datetime.now().isoformat()

    # Save updated records
    save_sent_summaries(sent_summaries)

    print(f"  ✓ Marked week {week_key} as sent")

def was_email_sent_this_week(week_start_date):
    """
    Check if email was already sent for a specific week

    Args:
        week_start_date: datetime object for the start of the week

    Returns:
        Boolean indicating if email was already sent
    """
    week_key = week_start_date.strftime('%Y-%m-%d')
    sent_summaries = load_sent_summaries()
    return week_key in sent_summaries

def run_weekly_scheduler(service, spreadsheet_url, recipient_email):
    """
    Run the weekly email scheduler (continuous loop)

    This function runs continuously, checking every hour if it's Monday morning
    and time to send the weekly summary. If so, it sends the email and marks it as sent.

    Args:
        service: Authenticated Gmail API service object
        spreadsheet_url: URL of Google Spreadsheet with data
        recipient_email: Email address to send summaries to
    """
    print("\n" + "="*80)
    print("WEEKLY EMAIL SCHEDULER STARTED")
    print("="*80)
    print(f"Schedule: Every {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][email_config.SEND_DAY]} at {email_config.SEND_HOUR}:00 AM")
    print(f"Recipient: {recipient_email}")
    print(f"Check interval: Every {email_config.SCHEDULER_CHECK_INTERVAL} seconds")
    print(f"Press Ctrl+C to stop")
    print("="*80)

    try:
        while True:
            now = datetime.now()
            print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] Checking schedule...")

            # Check if it's Monday morning
            if is_monday_morning():
                print("  ✓ It's Monday morning!")

                # Get previous week's date range
                start_date, end_date = get_previous_week_range()
                print(f"  Previous week: {start_date.date()} to {end_date.date()}")

                # Check if we already sent email for this week
                if was_email_sent_this_week(start_date):
                    print(f"  ⚠ Email already sent for week of {start_date.date()}")
                    print("  Skipping to avoid duplicate...")
                else:
                    print(f"  → Sending weekly summary for {start_date.date()} - {end_date.date()}")

                    # Send weekly summary
                    success, message = send_weekly_summary(
                        service,
                        recipient_email,
                        spreadsheet_url,
                        start_date,
                        end_date
                    )

                    if success:
                        # Mark as sent
                        mark_email_sent(start_date)
                        print("\n  ✓ Weekly summary sent and logged successfully!")
                    else:
                        print(f"\n  ✗ Failed to send weekly summary: {message}")
                        print("  Will retry next check...")

            else:
                is_monday = now.weekday() == email_config.SEND_DAY
                is_right_hour = now.hour == email_config.SEND_HOUR

                if is_monday:
                    print(f"  It's Monday, but not the right time yet (current hour: {now.hour}, target: {email_config.SEND_HOUR})")
                else:
                    day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][now.weekday()]
                    print(f"  Not Monday (today is {day_name})")

            # Sleep until next check
            print(f"\n  Sleeping for {email_config.SCHEDULER_CHECK_INTERVAL} seconds until next check...")
            time.sleep(email_config.SCHEDULER_CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("SCHEDULER STOPPED")
        print("="*80)
        print("Weekly email scheduler has been stopped by user (Ctrl+C)")
    except Exception as e:
        print("\n\n" + "="*80)
        print("SCHEDULER ERROR")
        print("="*80)
        print(f"An error occurred: {e}")
        print("Scheduler has stopped. Please restart it.")

if __name__ == "__main__":
    # Test the scheduler functions
    print("Testing scheduler functions...\n")

    print("Current time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("Is Monday morning?", is_monday_morning())

    start, end = get_previous_week_range()
    print(f"\nPrevious week range:")
    print(f"  Start: {start}")
    print(f"  End: {end}")

    print(f"\nWas email sent for this week? {was_email_sent_this_week(start)}")
