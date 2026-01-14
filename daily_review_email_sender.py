import pandas as pd
from datetime import datetime
from email_brain import analyze_email
from only_filter import should_filter
from topic_filter import detect_topic
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# EMAIL CONFIGURATION
SMTP_SERVER = "smtp.gmail.com"  # Gmail SMTP server
SMTP_PORT = 587  # TLS port
SENDER_EMAIL = "pshreedika@gmail.com"  # CHANGE THIS to your Gmail
SENDER_PASSWORD = "rytp kdup jbiz kdnx"  # CHANGE THIS to your Gmail App Password
RECIPIENT_EMAIL = "jklop838@gmail.com"

print("="*80)
print("DAILY EMAIL TREND REVIEW - WITH EMAIL SENDING")
print("="*80)

# Sample emails for today
today_emails = [
    {"First Name": "John", "Last Name": "Smith", "Email Address": "john.smith@email.com",
     "Body": "I'm very disappointed with the new parking policy. This is really frustrating for alumni visiting campus.",
     "Date Received": "2026-01-14", "Received By": "Alumni Office"},
    {"First Name": "Sarah", "Last Name": "Johnson", "Email Address": "sarah.j@email.com",
     "Body": "Just wanted to say I love the new mentorship program! It's wonderful to see students getting this support.",
     "Date Received": "2026-01-14", "Received By": "Alumni Office"},
    {"First Name": "Michael", "Last Name": "Brown", "Email Address": "mbrown@email.com",
     "Body": "I wanted to share my thoughts on President Smith's retirement announcement. This is a major transition and I'm concerned about the direction.",
     "Date Received": "2026-01-14", "Received By": "Alumni Office"},
    {"First Name": "Emily", "Last Name": "Davis", "Email Address": "emily.d@email.com",
     "Body": "Please update my address. I moved to 123 Main St, Boston MA 02101.",
     "Date Received": "2026-01-14", "Received By": "Alumni Office"},
    {"First Name": "Robert", "Last Name": "Wilson", "Email Address": "rwilson@email.com",
     "Body": "Can't wait for Alumni Return Week! Just registered for homecoming weekend. See you all there!",
     "Date Received": "2026-01-14", "Received By": "Alumni Office"},
    {"First Name": "Lisa", "Last Name": "Martinez", "Email Address": "lmartinez@email.com",
     "Body": "Unsubscribe me from this mailing list immediately.",
     "Date Received": "2026-01-14", "Received By": "Alumni Office"},
    {"First Name": "David", "Last Name": "Anderson", "Email Address": "d.anderson@email.com",
     "Body": "I'm worried about the new data privacy policy. Sharing student information with state authorities is concerning.",
     "Date Received": "2026-01-14", "Received By": "Alumni Office"},
    {"First Name": "Jennifer", "Last Name": "Taylor", "Email Address": "jtaylor@email.com",
     "Body": "The website has been broken for weeks. I can't access my alumni portal and this is really problematic.",
     "Date Received": "2026-01-14", "Received By": "Alumni Office"},
    {"First Name": "James", "Last Name": "Moore", "Email Address": "jmoore@email.com",
     "Body": "I'm excited about the presidential transition. Looking forward to President Smith's retirement celebration.",
     "Date Received": "2026-01-14", "Received By": "Alumni Office"},
    {"First Name": "Patricia", "Last Name": "White", "Email Address": "pwhite@email.com",
     "Body": "Out of office: I will be away until next Monday and will respond when I return.",
     "Date Received": "2026-01-14", "Received By": "Alumni Office"},
]

yesterday_stats = {
    'total': 42,
    'admin_filtered': 18,
    'topic_specific': 16,
    'real_feedback': 8,
    'negative_sentiment': 3,
    'positive_sentiment': 5,
    'withdrawal_intent': 0,
    'president_retirement_topic': 5
}

LOW_CONFIDENCE_THRESHOLD = 0.65

# Process emails
df = pd.DataFrame(today_emails)
total_today = len(df)

print(f"\nProcessing {total_today} emails for {datetime.now().strftime('%B %d, %Y')}...")

df['Should_Filter'] = df['Body'].apply(lambda x: should_filter(x, subject=""))
filtered_out = df[df['Should_Filter'] == True].copy()
emails_remaining = df[df['Should_Filter'] == False].copy()

# Apply topic detection
topic_results = []
for idx, row in emails_remaining.iterrows():
    topic, confidence = detect_topic(row['Body'], subject="")
    topic_results.append({'index': idx, 'topic': topic, 'confidence': confidence})

topic_df = pd.DataFrame(topic_results)
emails_remaining = emails_remaining.reset_index(drop=False)
topic_df['match_index'] = range(len(topic_df))
emails_remaining['match_index'] = range(len(emails_remaining))
emails_remaining = emails_remaining.merge(topic_df[['match_index', 'topic', 'confidence']], on='match_index', how='left')

# Separate topic-specific emails from general feedback
topic_filtered = emails_remaining[emails_remaining['topic'].notna()].copy()
emails_to_process = emails_remaining[emails_remaining['topic'].isna()].copy()

withdrawal_count = 0
positive_count = 0
negative_count = 0
uncertain_sentiments = []

if len(emails_to_process) > 0:
    for idx, row in emails_to_process.iterrows():
        result = analyze_email(row['Body'])

        if result['Pos_sentiment'] == 'Null' or result['Neg_sentiment'] == 'Null':
            uncertain_sentiments.append({
                'First Name': row['First Name'],
                'Last Name': row['Last Name'],
                'Email Address': row['Email Address'],
                'Body': row['Body'],
                'Pos_sentiment': result['Pos_sentiment'],
                'Neg_sentiment': result['Neg_sentiment'],
                'Date Received': row['Date Received']
            })

        if result['Pos_sentiment'] == 'Yes':
            sentiment = 'Positive'
        elif result['Neg_sentiment'] == 'Yes':
            sentiment = 'Negative'
        else:
            sentiment = 'Negative'

        emails_to_process.loc[idx, 'Sentiment'] = sentiment
        emails_to_process.loc[idx, 'Withdrawal_Intent'] = result.get('Withdrawn_Intent', result.get('Giving_Status', 'No'))

    positive_count = (emails_to_process['Sentiment'] == 'Positive').sum()
    negative_count = (emails_to_process['Sentiment'] == 'Negative').sum()
    # Check for withdrawal - looking for Giving_Status indicating paused/removed
    withdrawal_count = sum(1 for _, row in emails_to_process.iterrows()
                          if 'Paused' in str(row.get('Withdrawal_Intent', '')) or 'Removed' in str(row.get('Withdrawal_Intent', '')))

total_change = ((total_today - yesterday_stats['total']) / yesterday_stats['total'] * 100) if yesterday_stats['total'] > 0 else 0

# BUILD EMAIL BODY
email_body = []
email_body.append("="*80)
email_body.append("DAILY EMAIL REPORT")
email_body.append(f"Date: {datetime.now().strftime('%B %d, %Y')}")
email_body.append("="*80)
email_body.append("")

email_body.append("-"*80)
email_body.append("EXECUTIVE SUMMARY")
email_body.append("-"*80)

if total_change >= 0:
    email_body.append(f"Today we processed {total_today} emails, which represents an increase of {abs(total_change):.0f}% compared to yesterday.")
else:
    email_body.append(f"Today we processed {total_today} emails, which represents a decrease of {abs(total_change):.0f}% compared to yesterday.")

if negative_count > 0:
    email_body.append(f"There are {negative_count} negative feedback items identified today.")
else:
    email_body.append(f"There are no negative feedback items today.")

if len(uncertain_sentiments) > 0:
    email_body.append(f"We have flagged {len(uncertain_sentiments)} emails for manual review due to low AI confidence in sentiment classification.")

if withdrawal_count > 0:
    email_body.append(f"ALERT: {withdrawal_count} emails indicate withdrawal intent and require immediate attention.")
else:
    email_body.append(f"No withdrawal intent was detected in today's emails.")

email_body.append("")
email_body.append("-"*80)
email_body.append("GENERAL TRENDS & INSIGHTS")
email_body.append("-"*80)

if total_change < -20:
    email_body.append(f"Email volume is significantly lower than yesterday with a {abs(total_change):.0f}% decrease. This appears to be normal daily variation and is not a cause for concern.")
elif total_change > 20:
    email_body.append(f"Email volume has increased substantially by {total_change:.0f}% compared to yesterday, indicating heightened alumni engagement.")
else:
    email_body.append(f"Email volume remains relatively stable compared to yesterday, showing consistent alumni communication patterns.")

admin_pct = (len(filtered_out)/total_today*100)
if admin_pct > 60:
    email_body.append(f"A large portion of emails received today, specifically {admin_pct:.0f}%, were administrative in nature.")
elif admin_pct > 40:
    email_body.append(f"Approximately half of today's emails were administrative. This distribution is typical for our daily email volume.")
else:
    email_body.append(f"Administrative emails were lower than usual today.")

# Mention topics if any
if len(topic_filtered) > 0:
    top_topics = topic_filtered.groupby('topic').size().sort_values(ascending=False)
    top_topic_name = top_topics.index[0]
    top_topic_count = top_topics.iloc[0]
    if top_topic_count >= 2:
        email_body.append(f"We received {top_topic_count} emails related to {top_topic_name}, which is notable.")
    else:
        email_body.append(f"Several specific topics were mentioned in alumni emails today, including {', '.join(top_topics.index[:2])}.")

if len(emails_to_process) > 0:
    sentiment_ratio = negative_count / len(emails_to_process)
    if sentiment_ratio > 0.7:
        email_body.append(f"Sentiment in real feedback today leans predominantly negative, focusing on operational concerns.")
    elif sentiment_ratio < 0.3:
        email_body.append(f"Alumni feedback today is predominantly positive.")
    else:
        email_body.append(f"Sentiment is mixed today.")

email_body.append("")
email_body.append("-"*80)
email_body.append("VOLUME BREAKDOWN")
email_body.append("-"*80)
email_body.append(f"Out of {total_today} total emails, {len(filtered_out)} were classified as administrative or irrelevant ({len(filtered_out)/total_today*100:.0f}%).")
if len(topic_filtered) > 0:
    email_body.append(f"We identified {len(topic_filtered)} emails related to specific topics ({len(topic_filtered)/total_today*100:.0f}%).")
email_body.append(f"The remaining {len(emails_to_process)} emails were categorized as general feedback from alumni ({len(emails_to_process)/total_today*100:.0f}%).")

# Add topic summary section
if len(topic_filtered) > 0:
    email_body.append("")
    email_body.append("-"*80)
    email_body.append("TOPIC-SPECIFIC EMAILS")
    email_body.append("-"*80)
    email_body.append("The following topics were identified in today's emails:")

    # Group by topic and show counts
    topic_counts = topic_filtered.groupby('topic').size().sort_values(ascending=False)
    for topic, count in topic_counts.items():
        email_body.append(f"\n{topic}: {count} email(s)")
        # Show one example
        example = topic_filtered[topic_filtered['topic'] == topic].iloc[0]
        email_body.append(f"  Example: \"{example['Body'][:80]}...\"")
        email_body.append(f"  From: {example['First Name']} {example['Last Name']}")

if len(uncertain_sentiments) > 0:
    email_body.append("")
    email_body.append("="*80)
    email_body.append("AI UNCERTAIN - NEEDS MANUAL REVIEW")
    email_body.append("="*80)
    email_body.append("")
    email_body.append("UNCERTAIN SENTIMENT CLASSIFICATIONS:")
    email_body.append("The following emails could not be reliably classified as positive or negative by the AI system.")
    for email in uncertain_sentiments:
        email_body.append(f"\nFrom: {email['First Name']} {email['Last Name']} ({email['Email Address']})")
        email_body.append(f"Date: {email['Date Received']}")
        email_body.append(f"Email: {email['Body']}")
        email_body.append(f">> Please manually classify this email's sentiment")

email_body.append("")
email_body.append("-"*80)
email_body.append("ITEMS OF NOTE")
email_body.append("-"*80)

action_num = 1
if len(uncertain_sentiments) > 0:
    email_body.append(f"{action_num}. {len(uncertain_sentiments)} emails with uncertain sentiment classifications (see section above).")
    action_num += 1

if len(emails_to_process) > 0:
    for idx, row in emails_to_process[emails_to_process['Sentiment'] == 'Negative'].iterrows():
        if row.get('Withdrawal_Intent') == 'Yes':
            email_body.append(f"{action_num}. URGENT: {row['First Name']} {row['Last Name']} - withdrawal intent detected.")
        else:
            email_body.append(f"{action_num}. {row['First Name']} {row['Last Name']} - {row['Body'][:60]}...")
        action_num += 1

if action_num == 1:
    email_body.append("No urgent items flagged today.")

email_body.append("")
email_body.append("="*80)
email_body.append("END OF DAILY REPORT")
email_body.append("="*80)

# Convert to string
email_text = "\n".join(email_body)

# Print to console
print(email_text)

# SEND EMAIL
print("\n" + "="*80)
print("SENDING EMAIL...")
print("="*80)

try:
    # Create message
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = f"Alumni Feedback Daily Report - {datetime.now().strftime('%B %d, %Y')}"

    msg.attach(MIMEText(email_text, 'plain'))

    # Connect and send
    print(f"\nConnecting to {SMTP_SERVER}:{SMTP_PORT}...")
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()

    print(f"Logging in as {SENDER_EMAIL}...")
    server.login(SENDER_EMAIL, SENDER_PASSWORD)

    print(f"Sending email to {RECIPIENT_EMAIL}...")
    server.send_message(msg)
    server.quit()

    print("\n✓ EMAIL SENT SUCCESSFULLY!")
    print(f"Recipient: {RECIPIENT_EMAIL}")

except Exception as e:
    print(f"\n✗ ERROR SENDING EMAIL: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure SENDER_EMAIL and SENDER_PASSWORD are set correctly")
    print("2. For Gmail, you need an 'App Password', not your regular password")
    print("3. Go to: https://myaccount.google.com/apppasswords")
    print("4. Generate an app password and use that in SENDER_PASSWORD")
