# Gmail Integration Guide

## Overview

The Alumni Feedback Sorter now supports fetching emails directly from Gmail (inboxtest33@gmail.com) instead of using CSV files.

## Setup

### 1. Prerequisites

Install required dependencies:

```bash
pip3 install --upgrade google-auth-oauthlib google-auth-httplib2 google-api-python-client pandas openpyxl
```

### 2. Credentials Setup

The OAuth2 credentials have been placed in:
- `credentials/client_secret.json` - OAuth2 client credentials

On first run, you'll need to authenticate:
1. A browser window will open automatically
2. Sign in to the Gmail account (inboxtest33@gmail.com)
3. Grant permission to read emails
4. The token will be saved to `credentials/token.json` for future use

## Usage

### Basic Usage - Fetch and Process Emails

```bash
python3 data_processor_gmail.py
```

This will:
1. Authenticate with Gmail (opens browser on first run)
2. Fetch up to 100 emails from the last 30 days
3. Pre-filter administrative/non-feedback emails
4. Run sentiment and intent analysis
5. Generate `Alumni_Feedback_Report_Gmail.xlsx`

### Advanced Usage

**Fetch more emails:**
```bash
python3 data_processor_gmail.py 200  # Fetch up to 200 emails
```

**Change time range:**
```bash
python3 data_processor_gmail.py 100 60  # Last 60 days
```

**Add Gmail query filter:**
```bash
python3 data_processor_gmail.py 100 30 "is:unread"  # Only unread emails
python3 data_processor_gmail.py 100 30 "from:alumni.edu"  # From specific domain
```

### Test Gmail Fetcher Only

To test the Gmail connection without processing:

```bash
python3 gmail_fetcher.py
```

This will fetch emails and save to `fetched_emails.csv` without analysis.

## File Structure

```
alumni-feedback-sorter/
├── credentials/
│   ├── client_secret.json      # OAuth2 credentials (provided)
│   ├── token.json              # Auto-generated on first auth
│   └── service-account.json    # For Google Sheets upload
├── gmail_fetcher.py            # Gmail API integration
├── data_processor_gmail.py     # Full pipeline with Gmail
├── email_brain.py              # Sentiment/intent analysis
├── only_filter.py              # Email pre-filtering
└── sheets_uploader.py          # Upload results to Sheets
```

## Workflow Comparison

### Old Workflow (CSV-based)
1. Manually export emails to CSV
2. Run: `python3 data_processor_with_filter.py`
3. Upload: `python3 sheets_uploader.py [URL]`

### New Workflow (Gmail-based)
1. Run: `python3 data_processor_gmail.py`
2. Upload: `python3 sheets_uploader.py [URL]`

Or use the combined script:
```bash
./process_gmail_and_upload.sh [SPREADSHEET_URL]
```

## Email Processing Features

### Pre-filtering (Automatic)
Removes:
- Administrative notifications (unsubscribe, out-of-office)
- Address/contact updates
- Forwarded email chains
- Empty or link-only emails

### Analysis Output
For each email, generates:
- **Pos_sentiment**: Positive sentiment detected (Yes/No/Null)
- **Neg_sentiment**: Negative sentiment detected (Yes/No/Null)
- **Donate_Intent**: Donation inquiry detected (Yes/No)
- **Withdrawn_Intent**: Withdrawal of support detected (Yes/No)

## Gmail API Details

### Scopes Used
- `https://www.googleapis.com/auth/gmail.readonly` - Read-only access to Gmail

### Email Fields Extracted
- **First Name** - Parsed from sender name
- **Last Name** - Parsed from sender name
- **Email Address** - Sender email
- **Subject** - Email subject line
- **Body** - Email content (text/plain preferred, falls back to HTML)
- **Date Received** - Email timestamp
- **Received By** - inboxtest33@gmail.com
- **Contact Method** - Email

### Query Examples

The Gmail fetcher supports standard Gmail search operators:

```python
# Unread emails only
query = "is:unread"

# Specific sender
query = "from:donor@example.com"

# Subject contains
query = "subject:donation"

# Combination
query = "is:unread from:alumni.edu"

# Exclude certain senders
query = "-from:noreply@"
```

## Troubleshooting

### Authentication Issues

**Problem:** Browser doesn't open for OAuth
**Solution:** The script will print a URL - copy and paste it into your browser manually

**Problem:** "Access blocked" error
**Solution:** Ensure the OAuth consent screen is configured for the correct email address

**Problem:** Token expired
**Solution:** Delete `credentials/token.json` and re-authenticate

### Email Fetching Issues

**Problem:** No emails found
**Solution:**
- Check the date range (default: last 30 days)
- Verify the inbox has emails in that timeframe
- Try a broader search query

**Problem:** Incomplete email body
**Solution:** Some emails may only have HTML content - the fetcher extracts both text and HTML

### Processing Issues

**Problem:** All emails filtered out
**Solution:** The pre-filter may be too aggressive - check `only_filter.py` settings

**Problem:** Analysis results incorrect
**Solution:** Review thresholds in `email_brain.py`:
- `SENTIMENT_THRESHOLD = 0.25`
- `INTENT_THRESHOLD = 0.20`
- `WITHDRAWN_THRESHOLD = 0.18`

## Security Notes

1. **Never commit credentials to git**
   - `credentials/client_secret.json` should be in `.gitignore`
   - `credentials/token.json` should be in `.gitignore`

2. **Token storage**
   - The OAuth token is stored locally in `credentials/token.json`
   - It grants read-only access to Gmail
   - Delete this file to revoke access

3. **Permissions**
   - The app only requests read-only Gmail access
   - It cannot send, delete, or modify emails

## Next Steps

1. Test the Gmail integration with a small batch:
   ```bash
   python3 data_processor_gmail.py 10 7  # 10 emails, last 7 days
   ```

2. Review the filtered emails to tune the filter settings if needed

3. Set up automated processing with cron/scheduled tasks

4. Integrate with Google Sheets upload for complete automation

## Support

For issues or questions, refer to:
- Gmail API Documentation: https://developers.google.com/gmail/api
- OAuth2 Guide: https://developers.google.com/identity/protocols/oauth2
