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

def extract_themes(weekly_data):
    """
    Extract common themes from email bodies with counts

    Args:
        weekly_data: pandas DataFrame with weekly email data

    Returns:
        Dictionary with 'major_themes' (list of tuples with theme and count),
        'minor_themes' (list of tuples), and 'total_emails' (int)
    """
    from collections import Counter
    import re

    # Common keywords for different themes
    theme_keywords = {
        'Giving & Donations': ['donation', 'donate', 'giving', 'gift', 'contribute', 'support', 'pledge', 'bequest', 'endowment'],
        'Events & Reunions': ['event', 'reunion', 'gathering', 'homecoming', 'attend', 'rsvp', 'invitation'],
        'Career & Networking': ['career', 'job', 'networking', 'mentor', 'internship', 'employment', 'hiring'],
        'Alumni Updates': ['update', 'address', 'contact', 'information', 'moved', 'married', 'changed'],
        'Gratitude & Appreciation': ['thank', 'grateful', 'appreciate', 'wonderful', 'amazing', 'love'],
        'Concerns & Complaints': ['concern', 'disappointed', 'issue', 'problem', 'complaint', 'unhappy', 'frustrated'],
        'Campus Life': ['campus', 'facilities', 'building', 'dining', 'housing', 'library'],
        'Academic Programs': ['program', 'course', 'degree', 'major', 'curriculum', 'faculty', 'professor']
    }

    theme_counts = Counter()
    total_emails = len(weekly_data)

    # Analyze each email body
    for body in weekly_data['Email Text/Synopsis of Conversation/Notes']:
        if pd.notna(body):
            body_lower = str(body).lower()
            for theme, keywords in theme_keywords.items():
                if any(keyword in body_lower for keyword in keywords):
                    theme_counts[theme] += 1

    # Separate into major (top 3) and minor themes
    all_themes = theme_counts.most_common()

    if not all_themes:
        return {
            'major_themes': [('General Alumni Correspondence', total_emails)],
            'minor_themes': [],
            'total_emails': total_emails
        }

    # Major themes: top 3 or themes with >20% of emails
    major_threshold = max(3, int(total_emails * 0.2))
    major_themes = []
    minor_themes = []

    for theme, count in all_themes[:3]:
        major_themes.append((theme, count))

    # Minor themes: everything else that has at least 1 mention
    for theme, count in all_themes[3:]:
        if count > 0:
            minor_themes.append((theme, count))

    return {
        'major_themes': major_themes,
        'minor_themes': minor_themes,
        'total_emails': total_emails
    }

def generate_summary_paragraph(weekly_data, positive_count, negative_count, neutral_count, paused_giving, removed_bequest):
    """
    Generate a brief summary paragraph about the week's emails

    Args:
        weekly_data: pandas DataFrame with weekly email data
        positive_count, negative_count, neutral_count: Sentiment counts
        paused_giving, removed_bequest: Giving status counts

    Returns:
        Summary paragraph string
    """
    total = len(weekly_data)

    # Determine overall sentiment
    if positive_count > negative_count:
        sentiment_desc = "predominantly positive"
    elif negative_count > positive_count:
        sentiment_desc = "mixed, with some concerns raised"
    else:
        sentiment_desc = "balanced"

    # Build summary
    summary = f"This week, we received {total} alumni emails with {sentiment_desc} sentiment. "

    if paused_giving > 0 or removed_bequest > 0:
        summary += f"<strong>Important:</strong> {paused_giving + removed_bequest} alumni indicated changes to their giving status, requiring follow-up. "

    if positive_count > total * 0.6:
        summary += "The majority of correspondence expressed appreciation and support for the institution. "
    elif negative_count > total * 0.3:
        summary += "Several alumni raised concerns that may need attention from the appropriate teams. "

    return summary

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

    # Extract themes
    themes = extract_themes(weekly_data)

    # Generate summary paragraph
    summary_para = generate_summary_paragraph(weekly_data, positive_count, negative_count, neutral_count, paused_giving, removed_bequest)

    # Calculate percentages for pie chart
    positive_pct = (positive_count / total_emails * 100) if total_emails > 0 else 0
    negative_pct = (negative_count / total_emails * 100) if total_emails > 0 else 0
    neutral_pct = (neutral_count / total_emails * 100) if total_emails > 0 else 0

    # Build HTML with pie chart using CSS
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #34495e; margin-top: 30px; margin-bottom: 15px; }}
            .summary-box {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3498db; }}
            .stats-container {{ display: flex; justify-content: space-around; align-items: center; margin: 30px 0; flex-wrap: wrap; }}
            .pie-chart {{ width: 200px; height: 200px; border-radius: 50%; margin: 20px; }}
            .stats-list {{ list-style: none; padding: 0; margin: 20px; }}
            .stats-list li {{ margin: 12px 0; font-size: 16px; display: flex; align-items: center; }}
            .color-box {{ width: 20px; height: 20px; display: inline-block; margin-right: 10px; border-radius: 3px; }}
            .positive-color {{ background-color: #28a745; }}
            .negative-color {{ background-color: #dc3545; }}
            .neutral-color {{ background-color: #ffc107; }}
            .themes-list {{ background-color: #e8f4f8; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .themes-list ul {{ margin: 10px 0; padding-left: 20px; }}
            .themes-list li {{ margin: 8px 0; }}
            .alert-box {{ background-color: #fff3cd; border-left: 4px solid #ff9800; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            .link-box {{ margin-top: 30px; padding: 20px; background-color: #e8f4f8; border-radius: 8px; text-align: center; }}
            .link-box a {{ color: #3498db; text-decoration: none; font-weight: bold; font-size: 18px; }}
            .link-box a:hover {{ text-decoration: underline; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; font-size: 12px; text-align: center; }}
        </style>
    </head>
    <body>
        <h1>📊 Weekly Alumni Inbox Summary</h1>

        <div class="summary-box">
            <p><strong>Week of:</strong> {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}</p>
            <p>{summary_para}</p>
        </div>

        <h2>📈 Email Breakdown</h2>
        <div class="stats-container">
            <svg width="200" height="200" viewBox="0 0 200 200" style="margin: 20px;">
                <circle r="90" cx="100" cy="100" fill="#28a745" />
                <circle r="90" cx="100" cy="100" fill="#dc3545"
                        stroke-dasharray="{positive_pct * 5.65} {100 * 5.65}"
                        stroke-dashoffset="{-25 * 5.65}"
                        stroke-width="180"
                        fill="none" />
                <circle r="90" cx="100" cy="100" fill="#ffc107"
                        stroke-dasharray="{negative_pct * 5.65} {100 * 5.65}"
                        stroke-dashoffset="{-(25 + positive_pct) * 5.65}"
                        stroke-width="180"
                        fill="none" />
                <circle r="60" cx="100" cy="100" fill="white" />
                <text x="100" y="95" text-anchor="middle" font-size="24" font-weight="bold" fill="#333">{total_emails}</text>
                <text x="100" y="115" text-anchor="middle" font-size="14" fill="#666">Total</text>
            </svg>

            <ul class="stats-list">
                <li><span class="color-box positive-color"></span><strong>Positive:</strong> {positive_count} ({positive_pct:.1f}%)</li>
                <li><span class="color-box negative-color"></span><strong>Negative:</strong> {negative_count} ({negative_pct:.1f}%)</li>
                <li><span class="color-box neutral-color"></span><strong>Neutral:</strong> {neutral_count} ({neutral_pct:.1f}%)</li>
    """

    if paused_giving > 0 or removed_bequest > 0:
        html += f"""
                <li style="margin-top: 20px;"><strong>⚠️ Paused Giving:</strong> {paused_giving}</li>
                <li><strong>⚠️ Removed Bequests:</strong> {removed_bequest}</li>
        """

    html += """
            </ul>
        </div>
    """

    # Add alert box if there are giving concerns
    if paused_giving > 0 or removed_bequest > 0:
        html += f"""
        <div class="alert-box">
            <strong>⚠️ Action Required:</strong> {paused_giving + removed_bequest} alumni have indicated changes to their giving status.
            Please review the detailed report and follow up accordingly.
        </div>
        """

    # Add themes section
    html += f"""
        <h2>🔍 Themes Observed</h2>
        <div class="themes-list">
    """

    # Add major themes
    major_themes = themes.get('major_themes', [])
    minor_themes = themes.get('minor_themes', [])

    if major_themes:
        if len(major_themes) == 1:
            html += f"<p>Most correspondence focused on <strong>{major_themes[0][0]}</strong> ({major_themes[0][1]} emails).</p>"
        else:
            theme_list = ", ".join([f"<strong>{theme}</strong> ({count} emails)" for theme, count in major_themes[:-1]])
            last_theme = f"<strong>{major_themes[-1][0]}</strong> ({major_themes[-1][1]} emails)"
            html += f"<p>Most alumni discussed {theme_list}, and {last_theme}.</p>"

    # Add minor themes if they exist
    if minor_themes:
        if len(minor_themes) == 1:
            html += f"<p>Additionally, <strong>{minor_themes[0][0]}</strong> was mentioned ({minor_themes[0][1]} {'email' if minor_themes[0][1] == 1 else 'emails'}).</p>"
        else:
            minor_list = ", ".join([f"<strong>{theme}</strong> ({count})" for theme, count in minor_themes])
            html += f"<p>Other topics mentioned include: {minor_list}.</p>"

    html += """
        </div>
    """

    # Add link to full report (no detailed email log)
    html += f"""
        <div class="link-box">
            <p>📋 <a href="{email_config.SPREADSHEET_URL}">View Detailed Email Log in Google Sheets</a></p>
            <p style="font-size: 14px; color: #666; margin-top: 10px;">Click above to see the complete list of emails with full details</p>
        </div>

        <div class="footer">
            This is an automated weekly summary from the Alumni Feedback System.<br>
            Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        </div>
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
