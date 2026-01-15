# Quick Start Guide - Gmail Integration

## First Time Setup

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

This will install:
- Gmail API libraries
- Pandas for data processing
- ML models for sentiment analysis
- Google Sheets integration

### 2. First Authentication

Run this to authenticate with Gmail for the first time:

```bash
python3 gmail_fetcher.py
```

**What happens:**
1. A browser window will open automatically
2. Sign in to **inboxtest33@gmail.com**
3. Grant permission to read emails
4. The authentication token will be saved to `credentials/token.json`
5. Sample emails will be fetched and saved to `fetched_emails.csv`

**Important:** Keep the browser window open until you see the success message!

---

## Daily Usage

### Option 1: Process Gmail Emails (No Upload)

Fetch and analyze emails from Gmail:

```bash
python3 data_processor_gmail.py
```

**Output:** `Alumni_Feedback_Report_Gmail.xlsx`

**Customization:**
```bash
# Fetch 200 emails from last 60 days
python3 data_processor_gmail.py 200 60

# Fetch only unread emails
python3 data_processor_gmail.py 100 30 "is:unread"
```

---

### Option 2: Process + Upload to Google Sheets (One Command)

```bash
./process_gmail_and_upload.sh "YOUR_GOOGLE_SHEETS_URL"
```

**Example:**
```bash
./process_gmail_and_upload.sh "https://docs.google.com/spreadsheets/d/1ABC123.../edit"
```

**This does everything:**
1. Fetches emails from Gmail
2. Filters out administrative emails
3. Runs sentiment & intent analysis
4. Uploads results to Google Sheets

**Advanced:**
```bash
# Fetch 200 emails, last 60 days
./process_gmail_and_upload.sh "SHEET_URL" 200 60

# Only unread emails
./process_gmail_and_upload.sh "SHEET_URL" 100 30 "is:unread"
```

---

## What Gets Analyzed

### Pre-Filtering (Automatic)
The system automatically removes:
- Administrative emails (unsubscribe, out-of-office)
- Address updates ("please update my email")
- Forwarded email chains
- Empty or link-only emails

### Analysis Output
For each email:
- **Pos_sentiment**: Positive sentiment (gratitude, happiness)
- **Neg_sentiment**: Negative sentiment (complaints, disappointment)
- **Donate_Intent**: Donation inquiry or interest
- **Withdrawn_Intent**: Ending support or withdrawing donations

---

## Troubleshooting

### "Token expired" Error

**Solution:**
```bash
rm credentials/token.json
python3 gmail_fetcher.py  # Re-authenticate
```

### "No emails found"

**Check:**
- Are there emails in the inbox from the last 30 days?
- Try increasing the time range: `python3 data_processor_gmail.py 100 60`

### Browser doesn't open for authentication

**Solution:**
- The terminal will print a URL
- Copy and paste it into your browser manually

### Service account error (for Google Sheets upload)

**Make sure:**
1. `credentials/service-account.json` exists
2. The Google Sheet is shared with the service account email

**Find your service account email:**
```bash
python3 sheets_uploader.py --show-email
```

---

## File Locations

**Input:**
- `credentials/client_secret.json` - OAuth credentials (already set up)
- `credentials/token.json` - Auto-generated on first auth
- `credentials/service-account.json` - For Google Sheets upload

**Output:**
- `Alumni_Feedback_Report_Gmail.xlsx` - Analysis results
- `fetched_emails.csv` - Raw email data (when testing fetcher)

---

## Advanced Gmail Queries

You can use Gmail's search syntax:

```bash
# Unread only
python3 data_processor_gmail.py 100 30 "is:unread"

# Specific sender
python3 data_processor_gmail.py 100 30 "from:alumni@university.edu"

# Subject contains
python3 data_processor_gmail.py 100 30 "subject:donation"

# Exclude automated emails
python3 data_processor_gmail.py 100 30 "-from:noreply"

# Combination
python3 data_processor_gmail.py 100 30 "is:unread from:alumni.edu"
```

See [Gmail search operators](https://support.google.com/mail/answer/7190) for more options.

---

## Comparison: Old vs New Workflow

### Old Workflow (CSV-based)
```bash
# Manual steps:
# 1. Export emails to CSV manually
# 2. Save as test_emails.csv
python3 data_processor_with_filter.py
python3 sheets_uploader.py "SHEET_URL"
```

### New Workflow (Gmail-based)
```bash
# Fully automated:
./process_gmail_and_upload.sh "SHEET_URL"
```

**Time saved:** ~10 minutes per run!

---

## Need Help?

**Test the Gmail connection:**
```bash
python3 gmail_fetcher.py
```

**Test without uploading:**
```bash
python3 data_processor_gmail.py 10 7  # 10 emails, last 7 days
```

**Check service account email:**
```bash
python3 sheets_uploader.py --show-email
```

For detailed information, see [README_GMAIL.md](README_GMAIL.md)
