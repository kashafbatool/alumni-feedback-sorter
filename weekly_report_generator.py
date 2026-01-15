"""
Weekly Report Generator

This module generates HTML and plain text email reports from Google Sheets data.
It fetches weekly alumni feedback data and formats it into a comprehensive report.
"""

import pandas as pd
from datetime import datetime, timedelta
from sheets_uploader import get_sheets_service
import email_config
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
from collections import Counter
import re

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

def generate_pie_chart(positive_count, negative_count, neutral_count, paused_giving, removed_bequest):
    """
    Generate a pie chart as base64-encoded image

    Args:
        positive_count: Number of positive emails
        negative_count: Number of negative emails
        neutral_count: Number of neutral emails
        paused_giving: Number of paused giving
        removed_bequest: Number of removed bequests

    Returns:
        Base64-encoded PNG image string
    """
    # Prepare data for pie chart
    labels = []
    sizes = []
    colors = []

    if positive_count > 0:
        labels.append(f'Positive ({positive_count})')
        sizes.append(positive_count)
        colors.append('#28a745')  # Green

    if negative_count > 0:
        labels.append(f'Negative ({negative_count})')
        sizes.append(negative_count)
        colors.append('#dc3545')  # Red

    if neutral_count > 0:
        labels.append(f'Neutral ({neutral_count})')
        sizes.append(neutral_count)
        colors.append('#6c757d')  # Gray

    if paused_giving > 0:
        labels.append(f'Paused Giving ({paused_giving})')
        sizes.append(paused_giving)
        colors.append('#fd7e14')  # Orange

    if removed_bequest > 0:
        labels.append(f'Removed Bequest ({removed_bequest})')
        sizes.append(removed_bequest)
        colors.append('#e83e8c')  # Pink

    # Create pie chart
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.title('Email Distribution Overview', fontsize=14, fontweight='bold', pad=20)

    # Save to bytes buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)

    # Encode to base64
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close(fig)

    return image_base64

def analyze_themes(weekly_data):
    """
    Analyze email text to identify common themes

    Args:
        weekly_data: pandas DataFrame with email data

    Returns:
        List of theme strings
    """
    if weekly_data is None or len(weekly_data) == 0:
        return []

    # Combine all email text
    all_text = ' '.join(weekly_data['Email Text/Synopsis of Conversation/Notes'].astype(str).tolist())
    all_text = all_text.lower()

    # Define theme keywords
    theme_keywords = {
        'Donations & Giving': ['donat', 'giv', 'contribut', 'pledge', 'fund', 'support', 'financial'],
        'Events & Reunions': ['event', 'reunion', 'homecoming', 'gathering', 'celebration', 'anniversary'],
        'Campus Changes': ['campus', 'building', 'construction', 'facility', 'renovation', 'new'],
        'Administration & Leadership': ['president', 'administration', 'leadership', 'board', 'decision', 'policy'],
        'Student Experience': ['student', 'education', 'academ', 'program', 'curriculum', 'class'],
        'Alumni Engagement': ['network', 'connect', 'alumni', 'community', 'relationship', 'engagement'],
        'Recognition & Thanks': ['thank', 'appreciat', 'grateful', 'recognition', 'honor', 'acknowledge'],
        'Concerns & Complaints': ['concern', 'disappoint', 'upset', 'frustrat', 'worry', 'issue', 'problem'],
        'Career & Mentorship': ['career', 'job', 'mentor', 'professional', 'network', 'internship'],
        'Legacy & Bequests': ['will', 'estate', 'bequest', 'legacy', 'planned', 'endow']
    }

    # Count theme mentions
    theme_counts = {}
    for theme, keywords in theme_keywords.items():
        count = sum(all_text.count(keyword) for keyword in keywords)
        if count > 0:
            theme_counts[theme] = count

    # Get top 3-5 themes
    sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
    top_themes = [theme for theme, count in sorted_themes[:5]]

    # Generate theme descriptions
    theme_descriptions = []

    for theme in top_themes:
        if theme == 'Donations & Giving':
            theme_descriptions.append("**Donations & Giving** - Alumni discussing their financial support and contributions to the college")
        elif theme == 'Events & Reunions':
            theme_descriptions.append("**Events & Reunions** - Feedback about alumni events, reunions, and campus gatherings")
        elif theme == 'Campus Changes':
            theme_descriptions.append("**Campus Changes** - Reactions to new buildings, facilities, or campus developments")
        elif theme == 'Administration & Leadership':
            theme_descriptions.append("**Administration & Leadership** - Opinions about college leadership and institutional decisions")
        elif theme == 'Student Experience':
            theme_descriptions.append("**Student Experience** - Comments about academic programs and current student life")
        elif theme == 'Alumni Engagement':
            theme_descriptions.append("**Alumni Engagement** - Discussions about staying connected with the alumni community")
        elif theme == 'Recognition & Thanks':
            theme_descriptions.append("**Recognition & Thanks** - Alumni expressing gratitude and appreciation")
        elif theme == 'Concerns & Complaints':
            theme_descriptions.append("**Concerns & Complaints** - Alumni raising issues or expressing dissatisfaction")
        elif theme == 'Career & Mentorship':
            theme_descriptions.append("**Career & Mentorship** - Professional networking and career guidance discussions")
        elif theme == 'Legacy & Bequests':
            theme_descriptions.append("**Legacy & Bequests** - Conversations about planned giving and estate planning")

    return theme_descriptions if theme_descriptions else ["**General Alumni Communication** - Standard updates and routine correspondence"]

def generate_briefing(weekly_data, positive_count, negative_count, neutral_count,
                      paused_giving, removed_bequest, total_emails, themes):
    """
    Generate an overall briefing paragraph summarizing the week

    Args:
        weekly_data: pandas DataFrame with email data
        positive_count: Number of positive emails
        negative_count: Number of negative emails
        neutral_count: Number of neutral emails
        paused_giving: Number of paused giving
        removed_bequest: Number of removed bequests
        total_emails: Total number of emails
        themes: List of theme descriptions

    Returns:
        String with briefing paragraph
    """
    # Calculate percentages
    positive_pct = (positive_count / total_emails * 100) if total_emails > 0 else 0
    negative_pct = (negative_count / total_emails * 100) if total_emails > 0 else 0

    # Determine overall sentiment tone
    if positive_pct > 60:
        sentiment_tone = "predominantly positive"
        outlook = "The strong positive sentiment reflects healthy alumni relations and active engagement."
    elif positive_pct > 40:
        sentiment_tone = "generally balanced with a positive lean"
        outlook = "Overall engagement remains healthy with manageable concerns."
    elif negative_pct > 50:
        sentiment_tone = "notably negative"
        outlook = "The elevated negative sentiment warrants immediate attention from leadership."
    elif negative_pct > 30:
        sentiment_tone = "mixed with significant concerns"
        outlook = "While not critical, the level of negative feedback suggests areas needing attention."
    else:
        sentiment_tone = "primarily neutral"
        outlook = "Standard communication patterns with routine inquiries and updates."

    # Build briefing
    briefing = f"This week's alumni inbox reflects {sentiment_tone} engagement, with {total_emails} messages received. "

    # Add critical concerns if present
    if paused_giving > 0 or removed_bequest > 0:
        concerns = []
        if paused_giving > 0:
            concerns.append(f"{paused_giving} paused giving notification{'s' if paused_giving > 1 else ''}")
        if removed_bequest > 0:
            concerns.append(f"{removed_bequest} removed bequest{'s' if removed_bequest > 1 else ''}")

        briefing += f"Critically, there {'are' if len(concerns) > 1 or (paused_giving + removed_bequest) > 1 else 'is'} {' and '.join(concerns)}, requiring urgent follow-up. "

    # Extract first theme if available
    if themes:
        # Get just the theme name from the first theme (before the dash)
        first_theme = themes[0].split('**')[1] if '**' in themes[0] else themes[0]
        briefing += f"The primary conversation themes center around {first_theme.lower()}"
        if len(themes) > 1:
            briefing += f", along with discussions about {themes[1].split('**')[1].lower() if '**' in themes[1] else themes[1].lower()}"
        briefing += ". "

    # Add outlook
    briefing += outlook

    return briefing

def generate_html_report(weekly_data, start_date, end_date):
    """
    Generate HTML email report from weekly data with pie chart and themes

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

    # Generate pie chart
    pie_chart_base64 = generate_pie_chart(positive_count, negative_count, neutral_count, paused_giving, removed_bequest)

    # Analyze themes
    themes = analyze_themes(weekly_data)

    # Generate overall briefing
    briefing = generate_briefing(weekly_data, positive_count, negative_count, neutral_count,
                                  paused_giving, removed_bequest, total_emails, themes)

    # Build HTML
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #34495e; margin-top: 30px; border-bottom: 2px solid #bdc3c7; padding-bottom: 5px; }}
            .section {{ background-color: #ecf0f1; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .overview {{ background-color: #e8f4f8; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .chart-container {{ text-align: center; margin: 20px 0; }}
            .metric {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
            .alert {{ background-color: #f8d7da; padding: 15px; border-left: 4px solid #e74c3c; margin: 15px 0; border-radius: 5px; }}
            .positive {{ background-color: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 15px 0; border-radius: 5px; }}
            .theme-item {{ padding: 10px 0; border-bottom: 1px solid #ddd; }}
            .theme-item:last-child {{ border-bottom: none; }}
            .link {{ margin-top: 30px; padding: 15px; background-color: #e8f4f8; border-radius: 8px; text-align: center; }}
            ul {{ line-height: 1.8; }}
        </style>
    </head>
    <body>
        <h1>📊 Weekly Alumni Inbox Summary</h1>
        <p><strong>Reporting Period:</strong> {date_range}</p>

        <h2>📈 Overview</h2>
        <div class="overview">
            <p class="metric">Total Emails: {total_emails}</p>
            <p style="margin-top: 15px;">Summary of this week's alumni inbox:</p>
            <ul>
                <li><strong>Positive:</strong> {positive_count} emails ({(positive_count/total_emails*100):.1f}%)</li>
                <li><strong>Negative:</strong> {negative_count} emails ({(negative_count/total_emails*100):.1f}%)</li>
                <li><strong>Neutral:</strong> {neutral_count} emails ({(neutral_count/total_emails*100):.1f}%)</li>
                <li><strong>Paused Giving:</strong> {paused_giving}</li>
                <li><strong>Removed Bequests:</strong> {removed_bequest}</li>
            </ul>
        </div>

        <div class="chart-container">
            <img src="data:image/png;base64,{pie_chart_base64}" alt="Email Distribution Pie Chart" style="max-width: 100%; height: auto;" />
        </div>

        <h2>📝 Overall Briefing</h2>
        <div class="section" style="background-color: #fff3cd; border-left: 4px solid #ffc107;">
            <p style="font-size: 16px; line-height: 1.8;">{briefing}</p>
        </div>
    """

    # Add critical alerts if any
    if paused_giving > 0 or removed_bequest > 0:
        html += """
            <div class="alert">
                <p><strong>⚠ Critical Alerts:</strong></p>
                <ul>
        """
        if paused_giving > 0:
            html += f"<li><strong>{paused_giving} alumni</strong> paused their giving</li>"
        if removed_bequest > 0:
            html += f"<li><strong>{removed_bequest} alumni</strong> removed bequest intentions</li>"
        html += """
                </ul>
                <p style="color: #721c24; margin-top: 10px;">These require immediate follow-up.</p>
            </div>
        """

    # Add positive developments if any
    if resumed_giving > 0 or added_bequest > 0:
        html += """
            <div class="positive">
                <p><strong>✓ Positive Developments:</strong></p>
                <ul>
        """
        if resumed_giving > 0:
            html += f"<li><strong>{resumed_giving} alumni</strong> resumed giving</li>"
        if added_bequest > 0:
            html += f"<li><strong>{added_bequest} alumni</strong> added bequest intentions</li>"
        html += """
                </ul>
            </div>
        """

    # Themes observed section
    html += """
        <h2>💡 Themes Observed</h2>
        <div class="section">
            <p>Based on analysis of this week's correspondence, the following themes emerged:</p>
    """

    for theme in themes:
        html += f'<div class="theme-item">{theme}</div>'

    html += """
        </div>
    """

    # Link to full data
    html += f"""
        <div class="link">
            <p><strong>📋 <a href="{email_config.SPREADSHEET_URL}">View Full Details in Google Sheets</a></strong></p>
            <p style="font-size: 14px; color: #555;">Access complete email log with names, dates, and full text</p>
        </div>

        <hr style="margin-top: 40px; border: none; border-top: 1px solid #ccc;">
        <p style="color: #7f8c8d; font-size: 12px; text-align: center;">
            Automated weekly summary from Alumni Feedback System<br>
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
