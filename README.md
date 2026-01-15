# Alumni Feedback Sorter

An AI-powered email sentiment and intent analyzer for processing TCNJ alumni feedback automatically. This tool fetches emails from Gmail, categorizes them by sentiment (Positive/Negative/Neutral) and giving status changes, and uploads results directly to Google Sheets.

## Overview

**Problem:** The alumni relations inbox receives high volumes of feedback ranging from very negative to very supportive. Manually categorizing and logging these emails in a spreadsheet is extremely time-intensive, especially during peak periods.

**Solution:** An automated email analysis system that fetches emails from Gmail, filters out administrative emails, analyzes sentiment and giving intent, and uploads results to Google Sheets - all automatically.

## Features

- Fetches unread emails directly from Gmail inbox
- Filters out non-relevant emails (administrative updates, technical support, event inquiries)
- Analyzes sentiment with 3 categories: Positive, Negative, Neutral
- Detects giving status changes: Paused giving, Resumed giving, Removed bequest, Added bequest, No
- Prioritizes negative sentiment for giving changes (even with polite language)
- Uploads results to Google Sheets with monthly worksheet tracking
- Marks processed emails as read to prevent duplicates
- Sorts emails chronologically (oldest first, newest last)
- Runs continuously with 5-minute automation option
- Fast processing with M-series Mac GPU acceleration (MPS)

## Output Categories

Each email is analyzed and tagged with:

| Category | Values | Description |
|----------|--------|-------------|
| **Positive or Negative?** | Positive/Negative/Neutral | Overall sentiment classification |
| **Paused Giving OR Changed bequest intent?** | Paused giving, Resumed giving, Removed bequest, Added bequest, No | Giving status changes |

**Important:** Emails with "Paused giving" or "Removed bequest" are ALWAYS classified as Negative, regardless of polite language used.

## Installation

### Prerequisites
- Python 3.9+
- Mac (M1/M2/M3) recommended for GPU acceleration

### Install Dependencies

```bash
pip install transformers torch pandas openpyxl gspread google-auth google-auth-oauthlib google-auth-httplib2 googleapiclient
```

**Library Versions (tested):**
- transformers: 4.57.3
- torch: 2.8.0
- pandas: 2.3.3
- openpyxl: 3.1.5
- gspread: 6.1.4
- google-auth: 2.37.0

## Setup

### 1. Gmail API Authentication (One-time)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Gmail API**
4. Create **OAuth 2.0 credentials** (Desktop app)
5. Download credentials and save as `credentials/gmail_credentials.json`
6. Run authentication:

```bash
python3 gmail_auth.py
```

This will open a browser window to sign in and grant permissions. A token file will be saved for future use.

### 2. Google Sheets Service Account Setup (One-time)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable **Google Sheets API**
3. Create a **Service Account**:
   - Name: `alumni-feedback-uploader`
   - Description: `Service account for uploading alumni feedback to Google Sheets`
4. Create and download JSON key
5. Save as `credentials/service-account.json`

6. Get your service account email:

```bash
python3 sheets_uploader.py --show-email
```

7. Share your Google Spreadsheet with this email address (Editor permissions)

## Usage

### Manual Processing

Process unread Gmail emails and upload to Google Sheets:

```bash
python3 gmail_to_sheets.py "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
```

This will:
1. Fetch all unread emails from Gmail inbox
2. Filter out administrative emails
3. Analyze sentiment and giving status
4. Upload results to Google Sheets (worksheet: "jan 2026")
5. Mark processed emails as read

### Automated Processing (Continuous)

Run the processor continuously every 5 minutes:

```bash
python3 gmail_auto_processor.py "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit" 5
```

Press Ctrl+C to stop.

### CSV Input Option (For Testing)

If you want to test with a CSV file instead of Gmail:

```bash
python3 data_processor_with_filter.py
python3 sheets_uploader.py "YOUR_SHEET_URL"
```

## File Structure

```
alumni-feedback-sorter/
├── gmail_auth.py              # Gmail OAuth authentication (one-time setup)
├── gmail_to_sheets.py         # Main processor: Gmail → Analysis → Sheets
├── gmail_auto_processor.py    # Continuous 5-minute automation wrapper
├── email_brain.py             # Core ML models and analysis logic
├── only_filter.py             # Pre-filtering logic for administrative emails
├── sheets_uploader.py         # Google Sheets upload handler
├── data_processor_with_filter.py  # CSV input option (for testing)
├── credentials/
│   ├── gmail_credentials.json     # Gmail OAuth credentials
│   ├── gmail_token.pickle         # Gmail authentication token (auto-generated)
│   └── service-account.json       # Google Sheets service account key
├── Alumni_Feedback_Report_Filtered.xlsx    # Output from CSV processor
├── Alumni_Feedback_Report_Gmail.xlsx       # Output from Gmail processor
└── README.md
```

## How It Works

### Email Filtering (Pre-analysis)

The system filters out:
- **Address updates**: "update my address", "change my email"
- **Administrative notifications**: "out of office", "automatic reply"
- **Email chains**: forwarded messages with multiple headers
- **Link-only emails**: emails containing only URLs
- **Parent positive-only emails**: thank-yous from parents (alumni tracking only)
- **Technical support**: password resets, login issues
- **Event inquiries**: reunion schedules, ticket prices

Real feedback is kept based on keywords like: "concern", "disappointed", "suggest", "bequest", "will", "estate", "infuriating", "eroded", "betrayed"

### Sentiment Analysis

Uses zero-shot classification to independently detect:
- **Positive signals**: "expressing gratitude or happiness"
- **Negative signals**: "expressing complaint or disappointment"
- **Neutral signals**: No strong emotional valence

**Priority Rule:** Emails with "Paused giving" or "Removed bequest" are ALWAYS classified as Negative sentiment, even if they use polite or appreciative language.

### Giving Status Detection

Keyword-based detection with AI fallback:

**Paused giving**: "paused", "suspend", "stop giving", "step back", "discontinue"
**Resumed giving**: "resumed", "restart", "continue giving"
**Removed bequest**: "remove", "revoke", "changed my will", "no longer in my will"
**Added bequest**: "added to will", "bequest", "estate plan", "legacy gift"

If no keywords match, AI scoring determines if withdrawal/bequest language is present.

## Output Format

The Google Sheets output includes 14 columns:
1. First Name
2. Last Name
3. Email Address
4. Positive or Negative? (Positive/Negative/Neutral)
5. Received By (blank for staff to fill)
6. Date Received
7. Received by Email, Phone, or in Person? (blank for staff to fill)
8. Email Text/Synopsis of Conversation/Notes
9. Paused Giving OR Changed bequest intent? (5 options)
10. Constituent? (blank for staff to fill)
11. RM or team member assigned for Response (blank for staff to fill)
12. Response Complete? (blank for staff to fill)
13. Date of Response (blank for staff to fill)
14. Imported in RE? (Grace will update this column)

## Models Used

1. **Sentiment Analysis**: DistilBERT (distilbert-base-uncased-finetuned-sst-2-english)
   - Fast, lightweight BERT variant
   - Pre-trained on sentiment classification

2. **Intent Classification**:
   - BART-Large-MNLI (facebook/bart-large-mnli) for giving status detection
   - DistilBERT-MNLI (typeform/distilbert-base-uncased-mnli) for pre-filtering
   - Zero-shot classification allows custom categories without retraining

## Performance

**Processing Speed:**
- 3-5 seconds per email (first run, model loading)
- 1-2 seconds per email (subsequent runs)
- Processes 10 emails in ~15-20 seconds

**Accuracy:**
- High accuracy on giving status detection with comprehensive keyword lists
- 90%+ on sentiment classification
- Handles edge cases and contradictions

## Troubleshooting

### Gmail Authentication Issues

**"Not authenticated with Gmail"**
→ Run: `python3 gmail_auth.py`

**"gmail_credentials.json not found"**
→ Download OAuth credentials from Google Cloud Console

**"The credentials do not contain the necessary fields"**
→ Delete `credentials/gmail_token.pickle` and re-run `gmail_auth.py`

### Google Sheets Issues

**"Spreadsheet not found"**
→ Share the sheet with the service account email (run `python3 sheets_uploader.py --show-email` to see it)

**"credentials/service-account.json not found"**
→ Create `credentials` folder and download service account JSON key

**"Worksheet 'jan 2026' not found"**
→ Create a worksheet tab named "jan 2026" in your spreadsheet

### Processing Issues

**"No unread emails found"**
→ Send test emails to your Gmail account

**Emails not being marked as read**
→ This is expected - the Gmail API scope is read-only, so emails remain unread (they are still processed correctly)

**Old emails reappearing**
→ Manually mark emails as read in Gmail, or they will be reprocessed each time

## Security Notes

- Never commit `gmail_token.pickle` to Git (it's in .gitignore)
- Never commit `gmail_credentials.json` to Git (it's in .gitignore)
- Never commit `service-account.json` to Git (it's in .gitignore)
- The Gmail script only has READ access (cannot delete or modify emails)
- Only share your Google Sheet with the specific service account email

## Customization

### Adjusting Detection Thresholds

Edit `email_brain.py` lines 42-44:

```python
INTENT_THRESHOLD = 0.20        # Donation/intent detection
WITHDRAWN_THRESHOLD = 0.18     # Withdrawal detection
SENTIMENT_THRESHOLD = 0.25     # Positive/negative detection
```

Lower values = more sensitive (catches more, may have false positives)
Higher values = more conservative (fewer false positives, may miss some)

### Adding New Filter Keywords

Edit `only_filter.py` FILTER_KEYWORDS or FEEDBACK_KEYWORDS dictionaries to customize what gets filtered out vs. kept.

### Changing Worksheet Name

Edit `gmail_to_sheets.py` line 302 to change the worksheet name (currently "jan 2026" for monthly tracking).

## Credits

**Project:** Alumni Feedback Sorter (TCNJ Data Science Capstone)
**Models:** Hugging Face Transformers (DistilBERT, BART)
**Built with:** Python, PyTorch, Pandas, Gmail API, Google Sheets API

## License

Educational project - TCNJ Data Science Program
