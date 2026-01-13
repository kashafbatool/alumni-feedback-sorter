import pandas as pd
from datetime import datetime
from email_brain import analyze_email
from only_filter import should_filter

print("="*80)
print("ALUMNI FEEDBACK PROCESSOR WITH PRE-FILTERING")
print("="*80)

# 1. Load your data
df = pd.read_csv("test_emails.csv")

print(f"\nTotal emails loaded: {len(df)}")

# 2. Apply pre-filter to remove administrative emails
print("\nStep 1: Filtering out administrative emails...")
df['Should_Filter'] = df['Body'].apply(lambda x: should_filter(x, subject=""))

# Separate filtered vs kept emails
filtered_out = df[df['Should_Filter'] == True]
emails_to_process = df[df['Should_Filter'] == False]

print(f"  - Filtered out (admin/irrelevant): {len(filtered_out)}")
print(f"  - Kept for analysis (real feedback): {len(emails_to_process)}")

if len(filtered_out) > 0:
    print("\nFiltered out emails:")
    for idx, row in filtered_out.iterrows():
        preview = row['Body'][:60] + "..." if len(row['Body']) > 60 else row['Body']
        print(f"  - {preview}")

# 3. Run sentiment/intent analysis ONLY on emails that passed the filter
print(f"\nStep 2: Analyzing {len(emails_to_process)} emails for sentiment and intent...")
if len(emails_to_process) > 0:
    results = emails_to_process['Body'].apply(analyze_email).apply(pd.Series)

    # 4. Create formatted output matching Google Sheet
    formatted_df = pd.DataFrame()

    # Map to Google Sheet columns
    formatted_df['First Name'] = emails_to_process.get('First Name', '')
    formatted_df['Last Name'] = emails_to_process.get('Last Name', '')
    formatted_df['Email Address'] = emails_to_process.get('Email Address', '')

    # Map sentiment to Positive/Negative (only 2 options)
    def determine_sentiment(row):
        # If any positive signal, mark as Positive
        if row['Pos_sentiment'] == 'Yes':
            return 'Positive'
        # If any negative signal, mark as Negative
        elif row['Neg_sentiment'] == 'Yes':
            return 'Negative'
        # Default to Negative for uncertain cases (staff will review)
        else:
            return 'Negative'

    formatted_df['Positive or Negative?'] = results.apply(determine_sentiment, axis=1)
    formatted_df['Received By'] = emails_to_process.get('Received By', '')
    formatted_df['Date Received'] = emails_to_process.get('Date Received', datetime.today().strftime('%Y-%m-%d'))
    formatted_df['Received by Email, Phone, or in Person?'] = emails_to_process.get('Contact Method', 'Email')
    formatted_df['Email Text/Synopsis of Conversation/Notes'] = emails_to_process['Body'].values
    formatted_df['Paused Giving OR Changed bequest intent?'] = results['Withdrawn_Intent'].values
    formatted_df['Constituent?'] = emails_to_process.get('Constituent?', '')
    formatted_df['RM or team member assigned for Response'] = emails_to_process.get('Assigned To', '')
    formatted_df['Response Complete?'] = 'No'
    formatted_df['Date of Response'] = ''
    formatted_df['Imported in RE? (Grace will update this column)'] = ''

    # 5. Save to Excel
    formatted_df.to_excel("Alumni_Feedback_Report_Filtered.xlsx", index=False)

    print("\n" + "="*80)
    print("PROCESSING COMPLETE")
    print("="*80)
    print(f"\nOutput saved to: Alumni_Feedback_Report_Filtered.xlsx")
    print(f"Total emails in report: {len(formatted_df)}")
    print(f"Emails excluded: {len(filtered_out)}")

    # Show sentiment breakdown
    print("\nSentiment Breakdown:")
    print(formatted_df['Positive or Negative?'].value_counts().to_string())

    print("\nWithdrawal Intent:")
    print(formatted_df['Paused Giving OR Changed bequest intent?'].value_counts().to_string())
else:
    print("\nNo emails passed the filter. All emails were administrative/irrelevant.")
