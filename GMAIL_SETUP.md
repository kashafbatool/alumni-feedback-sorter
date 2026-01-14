# Gmail Integration Setup Guide

Automatically fetch emails from Gmail and process them!

## Quick Start

### Step 1: Authenticate Gmail (One-time setup)

```bash
python3 gmail_auth.py
```

This will:
1. Open a browser window
2. Ask you to sign in with your test Gmail account
3. Ask for permission to read emails
4. Save a token file for future use

**Important:** Sign in with the Gmail account that will receive the alumni feedback emails.

### Step 2: Send Test Emails

Send some test emails to your Gmail account (the one you just authenticated).

### Step 3: Process Emails

```bash
python3 gmail_to_sheets.py "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
```

This will:
1. ✅ Fetch all unread emails from Gmail
2. ✅ Filter out administrative emails
3. ✅ Analyze sentiment and intent
4. ✅ Upload results to Google Sheets
5. ✅ Mark processed emails as "read"

---

## Complete Workflow Example

```bash
# 1. Authenticate Gmail (only needed once)
python3 gmail_auth.py

# 2. Send test emails to your Gmail inbox

# 3. Process and upload
python3 gmail_to_sheets.py "https://docs.google.com/spreadsheets/d/1GYc5XF3ScKZmqONY3eUmzrpYnQZuu6Z-qszOTnk2AVQ/edit"
```

---

## What Happens?

### The script will:

1. **Fetch Unread Emails**
   - Connects to your Gmail inbox
   - Gets all unread emails (up to 50 at a time)
   - Extracts sender name, email, subject, body, and date

2. **Pre-Filter**
   - Removes administrative emails (address updates, auto-replies, etc.)
   - Only analyzes real feedback

3. **Sentiment Analysis**
   - Analyzes each email for positive/negative sentiment
   - Detects withdrawal intent
   - Smart contradiction detection

4. **Upload to Sheets**
   - Uploads analyzed emails to your Google Spreadsheet
   - All 14 columns filled in

5. **Mark as Read**
   - Marks processed emails as "read" in Gmail
   - Prevents duplicate processing next time

---

## Running on a Schedule

You can set this up to run automatically every hour:

### On Mac (using cron):

```bash
# Edit crontab
crontab -e

# Add this line (runs every hour):
0 * * * * cd /Users/kashafbatool/alumni-feedback-sorter && /usr/bin/python3 gmail_to_sheets.py "YOUR_SHEET_URL" >> gmail_processor.log 2>&1
```

### Manual Run:
Just run the command whenever you want to process new emails:

```bash
python3 gmail_to_sheets.py "YOUR_SHEET_URL"
```

---

## Troubleshooting

### "Not authenticated with Gmail"
→ Run: `python3 gmail_auth.py` first

### "gmail_credentials.json not found"
→ Make sure you downloaded the OAuth credentials from Google Cloud Console

### "No unread emails found"
→ Send some test emails to your Gmail account

### Emails not being fetched
→ Make sure you're signed in with the correct Gmail account when you run `gmail_auth.py`

---

## Files Created

After setup, you'll have:

```
credentials/
├── gmail_credentials.json    # OAuth credentials (from Google Cloud)
├── gmail_token.pickle         # Authentication token (auto-generated)
└── service-account.json       # Google Sheets access (already have)
```

---

## Security Notes

- ⚠️ Never commit `gmail_token.pickle` to Git (it's in .gitignore)
- ⚠️ Never commit `gmail_credentials.json` to Git (it's in .gitignore)
- ✅ The script only has READ access to Gmail (cannot delete or modify emails, only mark as read)

---

## Comparison: CSV vs Gmail

### Option 1: CSV Input (Current)
```bash
python3 data_processor_with_filter.py
python3 sheets_uploader.py "SHEET_URL"
```
- Manual: You create a CSV file with emails
- Good for testing with fake data

### Option 2: Gmail Input (New!)
```bash
python3 gmail_to_sheets.py "SHEET_URL"
```
- Automatic: Fetches emails directly from Gmail
- Good for production with real emails

Both work! Use whichever fits your workflow.

---

## Next Steps

1. ✅ You've authenticated Gmail
2. ✅ Send some test emails to your inbox
3. ✅ Run `gmail_to_sheets.py` to process them
4. 🎉 Check your Google Sheet!

Questions? Check the troubleshooting section above.
