import pandas as pd
from email_brain import analyze_email # Import the function you just wrote!

# 1. Load your data (Save a few test emails in a CSV first)
df = pd.read_csv("test_emails.csv")

# 2. Run the analysis on every row
# This creates new columns in your data
results = df['Body'].apply(analyze_email).apply(pd.Series)

# 3. Join it back to your original data
final_df = pd.concat([df, results], axis=1)

# 4. Save to Excel for your meeting
final_df.to_excel("Analyzed_Report.xlsx", index=False)
print("Done! Report generated.")