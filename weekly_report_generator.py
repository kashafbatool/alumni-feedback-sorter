"""
Weekly Report Generator

This module generates HTML and plain text email reports from Google Sheets data.
It fetches weekly alumni feedback data and formats it into a comprehensive report.
"""

import pandas as pd
from datetime import datetime, timedelta
from sheets_uploader import get_sheets_service
import email_config

def fetch_weekly_data(spreadsheet_url, start_date, end_date):
    """
    Fetch weekly data from Google Sheets for the specified date range

    Args:
        spreadsheet_url: URL of the Google Spreadsheet
        start_date: Start date (datetime object)
        end_date: End date (datetime object)

    Returns:
        pandas DataFrame with all emails from the date range, or None if error
    """
    print(f"Fetching data from {start_date.date()} to {end_date.date()}...")

    try:
        # Get authenticated client
        client = get_sheets_service()
        if not client:
            return None

        # Open spreadsheet
        sheet = client.open_by_url(spreadsheet_url)

        # Get all worksheets (month tabs)
        worksheets = sheet.worksheets()

        # Collect all data from relevant worksheets
        all_data = []

        for worksheet in worksheets:
            # Skip worksheets that don't look like month tabs
            worksheet_name = worksheet.title.lower()
            if not any(month in worksheet_name for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                                                              'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                continue

            print(f"  Reading worksheet: {worksheet.title}")

            # Get all values from worksheet
            records = worksheet.get_all_records()

            if not records:
                continue

            # Convert to DataFrame
            df = pd.DataFrame(records)

            # Filter by date range if Date Received column exists
            if 'Date Received' in df.columns:
                df['Date Received'] = pd.to_datetime(df['Date Received'], errors='coerce')

                # Filter to date range
                mask = (df['Date Received'] >= start_date) & (df['Date Received'] <= end_date)
                filtered_df = df[mask]

                if len(filtered_df) > 0:
                    all_data.append(filtered_df)

        if not all_data:
            print("  No data found in date range")
            return pd.DataFrame()

        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True)

        # Sort by date (oldest first)
        combined_df = combined_df.sort_values('Date Received')

        print(f"  ✓ Found {len(combined_df)} emails in date range")

        return combined_df

    except Exception as e:
        print(f"  ✗ Error fetching data: {e}")
        return None

def generate_html_report(weekly_data, start_date, end_date):
    """
    Generate HTML email report from weekly data

    Args:
        weekly_data: pandas DataFrame with weekly email data
        start_date: Start date (datetime object)
        end_date: End date (datetime object)

    Returns:
        HTML string for email body
    """
    if weekly_data is None or len(weekly_data) == 0:
        return generate_empty_report_html(start_date, end_date)

    # Calculate statistics
    total_emails = len(weekly_data)
    sentiment_counts = weekly_data['Positive or Negative?'].value_counts()
    positive_count = sentiment_counts.get('Positive', 0)
    negative_count = sentiment_counts.get('Negative', 0)
    neutral_count = sentiment_counts.get('Neutral', 0)

    # Giving status counts
    giving_status_counts = weekly_data['Paused Giving OR Changed bequest intent?'].value_counts()
    paused_giving = giving_status_counts.get('Paused giving', 0)
    removed_bequest = giving_status_counts.get('Removed bequest', 0)
    resumed_giving = giving_status_counts.get('Resumed giving', 0)
    added_bequest = giving_status_counts.get('Added bequest', 0)

    # Format date range
    date_range = f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"

    # Analyze trends
    positive_pct = (positive_count / total_emails * 100) if total_emails > 0 else 0
    negative_pct = (negative_count / total_emails * 100) if total_emails > 0 else 0
    neutral_pct = (neutral_count / total_emails * 100) if total_emails > 0 else 0

    # Determine overall sentiment interpretation
    if positive_pct > 60:
        sentiment_interpretation = "This week shows a strongly positive trend with alumni expressing appreciation and satisfaction."
    elif positive_pct > 40:
        sentiment_interpretation = "This week shows a balanced mix of feedback with a slight positive lean."
    elif negative_pct > 50:
        sentiment_interpretation = "This week shows concerning feedback trends that may require attention."
    elif negative_pct > 30:
        sentiment_interpretation = "This week shows mixed feedback with notable concerns that should be addressed."
    else:
        sentiment_interpretation = "This week shows mostly neutral engagement with standard alumni communication."

    # Build HTML
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #34495e; margin-top: 30px; border-bottom: 2px solid #bdc3c7; padding-bottom: 5px; }}
            .section {{ background-color: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .trend {{ background-color: #e8f4f8; padding: 15px; border-left: 4px solid #3498db; margin: 15px 0; }}
            .alert {{ background-color: #f8d7da; padding: 15px; border-left: 4px solid #e74c3c; margin: 15px 0; }}
            .positive {{ background-color: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 15px 0; }}
            .metric {{ font-size: 18px; font-weight: bold; color: #2c3e50; }}
            .interpretation {{ font-style: italic; color: #555; margin-top: 10px; }}
            .link {{ margin-top: 30px; padding: 15px; background-color: #e8f4f8; border-radius: 5px; }}
            ul {{ line-height: 1.8; }}
        </style>
    </head>
    <body>
        <h1>📊 Weekly Alumni Feedback Summary</h1>
        <p><strong>Period:</strong> {date_range}</p>

        <h2>📈 Weekly Trends</h2>
        <div class="trend">
            <p class="metric">Total Emails: {total_emails}</p>
            <p>This week, the system processed {total_emails} alumni feedback emails. The breakdown shows:</p>
            <ul>
                <li><strong>{positive_count} Positive emails</strong> ({positive_pct:.1f}%) - Alumni expressing gratitude, satisfaction, or positive experiences</li>
                <li><strong>{negative_count} Negative emails</strong> ({negative_pct:.1f}%) - Alumni raising concerns, complaints, or dissatisfaction</li>
                <li><strong>{neutral_count} Neutral emails</strong> ({neutral_pct:.1f}%) - General inquiries and standard communication</li>
            </ul>
        </div>

        <h2>💭 Overall Sentiment</h2>
        <div class="section">
            <p class="interpretation">{sentiment_interpretation}</p>
    """

    # Add critical alerts if any
    if paused_giving > 0 or removed_bequest > 0:
        html += """
            <div class="alert">
                <p><strong>⚠️ Critical Alerts:</strong></p>
                <ul>
        """
        if paused_giving > 0:
            html += f"<li><strong>{paused_giving} alumni</strong> indicated they have paused their giving</li>"
        if removed_bequest > 0:
            html += f"<li><strong>{removed_bequest} alumni</strong> indicated they have removed bequest intentions</li>"
        html += """
                </ul>
                <p style="color: #721c24;">These cases require immediate follow-up from the relationship management team.</p>
            </div>
        """

    # Add positive developments if any
    if resumed_giving > 0 or added_bequest > 0:
        html += """
            <div class="positive">
                <p><strong>✅ Positive Developments:</strong></p>
                <ul>
        """
        if resumed_giving > 0:
            html += f"<li><strong>{resumed_giving} alumni</strong> have resumed their giving</li>"
        if added_bequest > 0:
            html += f"<li><strong>{added_bequest} alumni</strong> have added bequest intentions</li>"
        html += """
                </ul>
            </div>
        """

    html += """
        </div>
    """

    # Note about filtered emails (placeholder for future enhancement)
    html += """
        <h2>🤔 Uncertain Classifications</h2>
        <div class="section">
            <p>Some emails were filtered as administrative or unclear. These emails contained:</p>
            <ul>
                <li>Automated responses or out-of-office messages</li>
                <li>Very short messages without clear sentiment (e.g., "Thanks!" or "Ok")</li>
                <li>System notifications or forwarded administrative emails</li>
            </ul>
            <p>These filtered emails are marked as "Untracked" in Gmail and can be reviewed manually if needed.</p>
        </div>
    """

    html += f"""
        <div class="link">
            <p><strong>📋 <a href="{email_config.SPREADSHEET_URL}">View Full Details in Google Sheets</a></strong></p>
            <p style="font-size: 14px; color: #555;">Access the complete email log with names, dates, and full text for detailed review.</p>
        </div>

        <hr>
        <p style="color: #7f8c8d; font-size: 12px;">
            This is an automated weekly summary from the Alumni Feedback System.<br>
            Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        </p>
    </body>
    </html>
    """

    return html

def generate_empty_report_html(start_date, end_date):
    """Generate HTML for when there's no data"""
    date_range = f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            h1 {{ color: #2c3e50; }}
            .message {{ background-color: #e8f4f8; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h1>📊 Weekly Alumni Feedback Summary</h1>
        <p><strong>Period:</strong> {date_range}</p>

        <div class="message">
            <p>✓ No new alumni feedback emails were processed during this period.</p>
        </div>

        <hr>
        <p style="color: #7f8c8d; font-size: 12px;">
            This is an automated weekly summary from the Alumni Feedback System.<br>
            Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        </p>
    </body>
    </html>
    """

    return html

def generate_plain_text_report(weekly_data, start_date, end_date):
    """
    Generate plain text email report from weekly data

    Args:
        weekly_data: pandas DataFrame with weekly email data
        start_date: Start date (datetime object)
        end_date: End date (datetime object)

    Returns:
        Plain text string for email body
    """
    if weekly_data is None or len(weekly_data) == 0:
        date_range = f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"
        return f"""
WEEKLY ALUMNI FEEDBACK SUMMARY
Period: {date_range}

No new alumni feedback emails were processed during this period.

---
This is an automated weekly summary from the Alumni Feedback System.
Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        """

    # Calculate statistics
    total_emails = len(weekly_data)
    sentiment_counts = weekly_data['Positive or Negative?'].value_counts()
    positive_count = sentiment_counts.get('Positive', 0)
    negative_count = sentiment_counts.get('Negative', 0)
    neutral_count = sentiment_counts.get('Neutral', 0)

    giving_status_counts = weekly_data['Paused Giving OR Changed bequest intent?'].value_counts()
    paused_giving = giving_status_counts.get('Paused giving', 0)
    removed_bequest = giving_status_counts.get('Removed bequest', 0)

    date_range = f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"

    # Build text report
    text = f"""
WEEKLY ALUMNI FEEDBACK SUMMARY
Period: {date_range}

SUMMARY STATISTICS
==================
Total Emails Processed: {total_emails}
Positive: {positive_count} ({positive_count/total_emails*100:.1f}%)
Negative: {negative_count} ({negative_count/total_emails*100:.1f}%)
Neutral: {neutral_count} ({neutral_count/total_emails*100:.1f}%)
"""

    if paused_giving > 0 or removed_bequest > 0:
        text += f"""
ALERTS:
🚨 Paused Giving: {paused_giving}
🚨 Removed Bequests: {removed_bequest}
"""

    text += "\n\nDETAILED EMAIL LOG\n==================\n"

    # Add email entries
    for _, row in weekly_data.iterrows():
        date_str = row['Date Received'].strftime('%Y-%m-%d') if pd.notna(row['Date Received']) else 'N/A'
        first_name = row.get('First Name', '')
        last_name = row.get('Last Name', '')
        email_addr = row.get('Email Address', '')
        sentiment = row.get('Positive or Negative?', 'Neutral')
        giving_status = row.get('Paused Giving OR Changed bequest intent?', 'No')
        email_text = row.get('Email Text/Synopsis of Conversation/Notes', '')

        text += f"""
Date: {date_str}
From: {first_name} {last_name} ({email_addr})
Sentiment: {sentiment}
Giving Status: {giving_status}
Email Text:
{email_text}
{'-'*80}
"""

    text += f"""
View Full Report: {email_config.SPREADSHEET_URL}

---
This is an automated weekly summary from the Alumni Feedback System.
Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
    """

    return text

if __name__ == "__main__":
    # Test the report generator
    print("Testing weekly report generator...")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    data = fetch_weekly_data(email_config.SPREADSHEET_URL, start_date, end_date)

    if data is not None:
        html = generate_html_report(data, start_date, end_date)
        print("\nHTML Report Generated:")
        print(html[:500] + "..." if len(html) > 500 else html)

        text = generate_plain_text_report(data, start_date, end_date)
        print("\nPlain Text Report Generated:")
        print(text[:500] + "..." if len(text) > 500 else text)
    else:
        print("Failed to generate reports")
