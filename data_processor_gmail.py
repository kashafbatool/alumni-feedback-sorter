"""
Alumni Feedback Data Processor with Gmail Integration
Fetches emails from Gmail and processes them with sentiment and intent analysis
"""

import pandas as pd
from gmail_fetcher import authenticate_gmail, fetch_emails
from only_filter import should_filter
from email_brain import analyze_email

def process_gmail_emails(max_results=100, days_back=30, query=None):
    """
    Fetch and process emails from Gmail

    Args:
        max_results: Maximum number of emails to fetch
        days_back: Number of days to look back for emails
        query: Gmail search query (optional)
    """
    print("=" * 60)
    print("ALUMNI FEEDBACK PROCESSOR - GMAIL INTEGRATION")
    print("=" * 60)

    # Step 1: Authenticate and fetch emails
    print("\n[Step 1/4] Authenticating with Gmail...")
    service = authenticate_gmail()

    print(f"\n[Step 2/4] Fetching emails from inboxtest33@gmail.com...")
    print(f"  - Max results: {max_results}")
    print(f"  - Days back: {days_back}")
    if query:
        print(f"  - Query filter: {query}")

    df = fetch_emails(service, max_results=max_results, days_back=days_back, query=query)

    if df.empty:
        print("\n[ERROR] No emails found. Exiting...")
        return None

    print(f"\n[SUCCESS] Fetched {len(df)} emails")

    # Step 2: Pre-filter emails
    print(f"\n[Step 3/4] Pre-filtering emails...")
    print("  - Removing administrative emails")
    print("  - Removing address updates")
    print("  - Removing forwarded chains")
    print("  - Removing empty/link-only emails")

    df['Should_Filter'] = df.apply(
        lambda row: should_filter(row['Body'], row.get('Subject', '')),
        axis=1
    )

    filtered_out = df[df['Should_Filter'] == True]
    emails_to_process = df[df['Should_Filter'] == False].copy()

    print(f"  - Filtered out: {len(filtered_out)} emails")
    print(f"  - Processing: {len(emails_to_process)} emails")

    if emails_to_process.empty:
        print("\n[WARNING] No emails to process after filtering. Exiting...")
        return None

    # Step 3: Analyze emails
    print(f"\n[Step 4/4] Analyzing {len(emails_to_process)} emails...")
    print("  - Running sentiment analysis")
    print("  - Running intent classification")

    # Analyze each email
    results = emails_to_process['Body'].apply(analyze_email).apply(pd.Series)

    # Combine with original data
    final_df = pd.concat([
        emails_to_process.reset_index(drop=True),
        results
    ], axis=1)

    # Drop the filter column
    final_df = final_df.drop('Should_Filter', axis=1)

    # Reorder columns to match expected output format
    column_order = [
        'First Name',
        'Last Name',
        'Email Address',
        'Body',
        'Subject',
        'Date Received',
        'Received By',
        'Contact Method',
        'Constituent?',
        'Assigned To',
        'Pos_sentiment',
        'Neg_sentiment',
        'Donate_Intent',
        'Withdrawn_Intent'
    ]

    # Only include columns that exist
    final_columns = [col for col in column_order if col in final_df.columns]
    final_df = final_df[final_columns]

    # Step 4: Save results
    output_file = 'Alumni_Feedback_Report_Gmail.xlsx'
    print(f"\n[SAVING] Writing results to {output_file}...")

    final_df.to_excel(output_file, index=False)

    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - Total emails fetched: {len(df)}")
    print(f"  - Emails filtered out: {len(filtered_out)}")
    print(f"  - Emails processed: {len(final_df)}")
    print(f"  - Positive sentiment: {(final_df['Pos_sentiment'] == 'Yes').sum()}")
    print(f"  - Negative sentiment: {(final_df['Neg_sentiment'] == 'Yes').sum()}")
    print(f"  - Donation intent: {(final_df['Donate_Intent'] == 'Yes').sum()}")
    print(f"  - Withdrawal intent: {(final_df['Withdrawn_Intent'] == 'Yes').sum()}")
    print(f"\n[OUTPUT] {output_file}")

    return final_df


if __name__ == "__main__":
    import sys

    # Parse command line arguments
    max_results = 100
    days_back = 30
    query = None

    if len(sys.argv) > 1:
        max_results = int(sys.argv[1])
    if len(sys.argv) > 2:
        days_back = int(sys.argv[2])
    if len(sys.argv) > 3:
        query = sys.argv[3]

    # Process emails
    process_gmail_emails(max_results=max_results, days_back=days_back, query=query)
