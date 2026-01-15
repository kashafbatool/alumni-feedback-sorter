"""
Email Sender Module

This module handles sending emails via Gmail API.
It creates MIME messages and sends them through the authenticated Gmail service.
"""

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import time
import email_config
from weekly_report_generator import fetch_weekly_data, generate_html_report, generate_plain_text_report

def create_message(sender, to, subject, html_body, text_body):
    """
    Create a MIME message for Gmail API

    Args:
        sender: Sender email address
        to: Recipient email address
        subject: Email subject
        html_body: HTML version of email body
        text_body: Plain text version of email body

    Returns:
        Dictionary with encoded message ready for Gmail API
    """
    # Create multipart message with both HTML and plain text
    message = MIMEMultipart('alternative')
    message['To'] = to
    message['From'] = f"{email_config.SENDER_NAME} <{sender}>"
    message['Subject'] = subject

    # Attach plain text version (for email clients that don't support HTML)
    part1 = MIMEText(text_body, 'plain')
    message.attach(part1)

    # Attach HTML version (preferred)
    part2 = MIMEText(html_body, 'html')
    message.attach(part2)

    # Encode message in base64url format for Gmail API
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

    return {'raw': raw_message}

def send_email(service, message):
    """
    Send an email using Gmail API

    Args:
        service: Authenticated Gmail API service object
        message: Message dictionary created by create_message()

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        result = service.users().messages().send(
            userId='me',
            body=message
        ).execute()

        print(f"  ✓ Email sent successfully (Message ID: {result['id']})")
        return True, f"Email sent successfully (ID: {result['id']})"

    except Exception as e:
        print(f"  ✗ Error sending email: {e}")
        return False, str(e)

def send_weekly_summary(service, recipient_email, spreadsheet_url, start_date, end_date):
    """
    Send weekly summary email with full report

    Args:
        service: Authenticated Gmail API service object
        recipient_email: Email address to send summary to
        spreadsheet_url: URL of Google Sheets with data
        start_date: Start date for data range (datetime object)
        end_date: End date for data range (datetime object)

    Returns:
        Tuple of (success: bool, message: str)
    """
    print("\n" + "="*80)
    print("SENDING WEEKLY EMAIL SUMMARY")
    print("="*80)
    print(f"Recipient: {recipient_email}")
    print(f"Date Range: {start_date.date()} to {end_date.date()}")

    # Step 1: Fetch weekly data from Google Sheets
    print("\nStep 1: Fetching data from Google Sheets...")
    weekly_data = fetch_weekly_data(spreadsheet_url, start_date, end_date)

    if weekly_data is None:
        return False, "Failed to fetch data from Google Sheets"

    # Step 2: Generate reports
    print("\nStep 2: Generating email reports...")
    html_body = generate_html_report(weekly_data, start_date, end_date)
    text_body = generate_plain_text_report(weekly_data, start_date, end_date)
    print("  ✓ Reports generated")

    # Step 3: Create email message
    print("\nStep 3: Creating email message...")
    # Format: "Jan 8–14, 2026" (no leading zeros)
    start_day = str(start_date.day)
    end_day = str(end_date.day)
    start_month = start_date.strftime('%b')
    end_month = end_date.strftime('%b')

    if start_month == end_month:
        date_range = f"{start_month} {start_day}–{end_day}, {end_date.year}"
    else:
        date_range = f"{start_month} {start_day}–{end_month} {end_day}, {end_date.year}"

    subject = email_config.EMAIL_SUBJECT_TEMPLATE.format(date_range=date_range)

    # Get sender email from service
    try:
        profile = service.users().getProfile(userId='me').execute()
        sender_email = profile['emailAddress']
    except:
        sender_email = "me"  # Fallback

    message = create_message(sender_email, recipient_email, subject, html_body, text_body)
    print("  ✓ Message created")

    # Step 4: Send email with retry logic
    print("\nStep 4: Sending email...")
    max_retries = email_config.MAX_RETRIES
    retry_delay = email_config.RETRY_DELAY_SECONDS

    for attempt in range(1, max_retries + 1):
        if attempt > 1:
            print(f"  Retry attempt {attempt}/{max_retries}...")
            time.sleep(retry_delay)

        success, result_msg = send_email(service, message)

        if success:
            print("\n" + "="*80)
            print("✓ WEEKLY SUMMARY EMAIL SENT SUCCESSFULLY!")
            print("="*80)
            print(f"Sent to: {recipient_email}")
            print(f"Subject: {subject}")
            print(f"Emails in report: {len(weekly_data) if weekly_data is not None else 0}")
            return True, result_msg

    # All retries failed
    error_msg = f"Failed to send email after {max_retries} attempts"
    print("\n" + "="*80)
    print(f"✗ {error_msg}")
    print("="*80)
    return False, error_msg

def send_test_email(service=None):
    """
    Send a test email to verify email sending works

    Args:
        service: Authenticated Gmail API service object (optional, will create if not provided)

    Returns:
        Tuple of (success: bool, message: str)
    """
    print("\n" + "="*80)
    print("SENDING TEST EMAIL")
    print("="*80)

    # Get service if not provided
    if service is None:
        from gmail_auth import get_gmail_service
        service = get_gmail_service()
        if not service:
            return False, "Failed to authenticate with Gmail"

    # Get sender email
    try:
        profile = service.users().getProfile(userId='me').execute()
        sender_email = profile['emailAddress']
        print(f"Sender: {sender_email}")
    except:
        sender_email = "me"

    # Create simple test message
    subject = "Test Email from Alumni Feedback System"
    html_body = """
    <html>
    <body>
        <h1>Test Email</h1>
        <p>This is a test email from the Alumni Feedback System.</p>
        <p>If you received this, email sending is working correctly! ✓</p>
        <p><small>Sent on {}</small></p>
    </body>
    </html>
    """.format(datetime.now().strftime('%B %d, %Y at %I:%M %p'))

    text_body = f"""
TEST EMAIL

This is a test email from the Alumni Feedback System.
If you received this, email sending is working correctly!

Sent on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
    """

    recipient = email_config.RECIPIENT_EMAIL
    print(f"Recipient: {recipient}")

    # Create and send message
    message = create_message(sender_email, recipient, subject, html_body, text_body)
    success, result_msg = send_email(service, message)

    if success:
        print("\n✓ Test email sent successfully!")
        print(f"Check {recipient} inbox")
    else:
        print(f"\n✗ Test email failed: {result_msg}")

    return success, result_msg

if __name__ == "__main__":
    # Test the email sender
    print("Testing email sender module...")

    from gmail_auth import get_gmail_service

    service = get_gmail_service()
    if not service:
        print("Failed to authenticate. Run: python3 gmail_auth.py")
    else:
        # Send test email
        send_test_email(service)
