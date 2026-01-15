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

    # Build HTML
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            .stats {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .stats ul {{ list-style-type: none; padding: 0; }}
            .stats li {{ margin: 8px 0; font-size: 16px; }}
            .alert {{ color: #e74c3c; font-weight: bold; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th {{ background-color: #3498db; color: white; padding: 12px; text-align: left; }}
            td {{ padding: 10px; border-bottom: 1px solid #ddd; vertical-align: top; }}
            tr:hover {{ background-color: #f5f5f5; }}
            .positive {{ background-color: #d4edda; }}
            .negative {{ background-color: #f8d7da; }}
            .neutral {{ background-color: #fff3cd; }}
            .email-text {{ max-width: 400px; white-space: pre-wrap; font-size: 14px; }}
            .link {{ margin-top: 30px; padding: 15px; background-color: #e8f4f8; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1>📊 Weekly Alumni Feedback Summary</h1>
        <p><strong>Period:</strong> {date_range}</p>

        <div class="stats">
            <h2>Summary Statistics</h2>
            <ul>
                <li><strong>Total Emails Processed:</strong> {total_emails}</li>
                <li><strong>Positive:</strong> {positive_count} ({positive_count/total_emails*100:.1f}%)</li>
                <li><strong>Negative:</strong> {negative_count} ({negative_count/total_emails*100:.1f}%)</li>
                <li><strong>Neutral:</strong> {neutral_count} ({neutral_count/total_emails*100:.1f}%)</li>
    """

    if paused_giving > 0 or removed_bequest > 0:
        html += f"""
                <li class="alert">🚨 Paused Giving: {paused_giving}</li>
                <li class="alert">🚨 Removed Bequests: {removed_bequest}</li>
        """

    if resumed_giving > 0 or added_bequest > 0:
        html += f"""
                <li>✅ Resumed Giving: {resumed_giving}</li>
                <li>✅ Added Bequests: {added_bequest}</li>
        """

    html += """
            </ul>
        </div>

        <h2>Detailed Email Log</h2>
        <table>
            <tr>
                <th>Date</th>
                <th>From</th>
                <th>Sentiment</th>
                <th>Giving Status</th>
                <th>Email Text</th>
            </tr>
    """

    # Add email rows
    for _, row in weekly_data.iterrows():
        date_str = row['Date Received'].strftime('%Y-%m-%d') if pd.notna(row['Date Received']) else 'N/A'
        first_name = row.get('First Name', '')
        last_name = row.get('Last Name', '')
        email_addr = row.get('Email Address', '')
        sentiment = row.get('Positive or Negative?', 'Neutral')
        giving_status = row.get('Paused Giving OR Changed bequest intent?', 'No')
        email_text = row.get('Email Text/Synopsis of Conversation/Notes', '')

        # Determine row class based on sentiment
        row_class = sentiment.lower() if sentiment in ['Positive', 'Negative', 'Neutral'] else ''

        # Truncate long email text for readability
        if len(str(email_text)) > 500:
            email_text = str(email_text)[:500] + "..."

        # Highlight critical giving status
        if giving_status in ['Paused giving', 'Removed bequest']:
            giving_status = f'<span class="alert">{giving_status}</span>'

        html += f"""
            <tr class="{row_class}">
                <td>{date_str}</td>
                <td>{first_name} {last_name}<br><small>{email_addr}</small></td>
                <td>{sentiment}</td>
                <td>{giving_status}</td>
                <td class="email-text">{email_text}</td>
            </tr>
        """

    html += f"""
        </table>

        <div class="link">
            <p><strong>📋 <a href="{email_config.SPREADSHEET_URL}">View Full Report in Google Sheets</a></strong></p>
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
