import pandas as pd
from datetime import datetime
from email_brain import analyze_email

# 1. Load your data (CSV should have columns: Body, First Name, Last Name, Email Address, Date Received, etc.)
df = pd.read_csv("test_emails.csv")

# 2. Run the analysis on every row
results = df['Body'].apply(analyze_email).apply(pd.Series)

# 3. Create the formatted output matching the Google Sheet structure
formatted_df = pd.DataFrame()

# Map to Google Sheet columns
formatted_df['First Name'] = df.get('First Name', '')  # If you have this in CSV
formatted_df['Last Name'] = df.get('Last Name', '')  # If you have this in CSV
formatted_df['Email Address'] = df.get('Email Address', '')  # If you have this in CSV

# Map sentiment analysis to "Positive or Negative?"
def determine_sentiment(row):
    if row['Pos_sentiment'] == 'Yes' and row['Neg_sentiment'] == 'No':
        return 'Positive'
    elif row['Neg_sentiment'] == 'Yes' and row['Pos_sentiment'] == 'No':
        return 'Negative'
    elif row['Pos_sentiment'] == 'Yes' and row['Neg_sentiment'] == 'Yes':
        return 'Mixed'
    else:
        return 'Neutral'

formatted_df['Positive or Negative?'] = results.apply(determine_sentiment, axis=1)

formatted_df['Received By'] = df.get('Received By', '')  # If you have this in CSV
formatted_df['Date Received'] = df.get('Date Received', datetime.today().strftime('%Y-%m-%d'))  # Default to today
formatted_df['Received by Email, Phone, or in Person?'] = df.get('Contact Method', 'Email')  # Default to Email
formatted_df['Email Text/Synopsis of Conversation/Notes'] = df['Body']  # The actual email content

# Map Withdrawn_Intent to "Paused Giving OR Changed bequest intent?"
formatted_df['Paused Giving OR Changed bequest intent?'] = results['Withdrawn_Intent']

formatted_df['Constituent?'] = df.get('Constituent?', '')  # If you have this in CSV
formatted_df['RM or team member assigned for Response'] = df.get('Assigned To', '')  # If you have this in CSV
formatted_df['Response Complete?'] = 'No'  # Default to No
formatted_df['Date of Response'] = ''  # Empty for now
formatted_df['Imported in RE? (Grace will update this column)'] = ''  # Empty for Grace

# 4. Save to Excel matching Google Sheet format
formatted_df.to_excel("Alumni_Feedback_Report.xlsx", index=False)
print("Done! Formatted report generated.")
print("\nColumns in output:")
for col in formatted_df.columns:
    print(f"  - {col}")
