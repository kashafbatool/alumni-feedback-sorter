# Weekly Email Summary - Quick Start Guide

## Overview
The system now automatically sends weekly email summaries every Monday morning at 8:00 AM from `inboxtest33@gmail.com` to `efratagetachew69@gmail.com`.

## What Was Implemented

### New Files Created:
1. **email_config.py** - Configuration settings (recipient, schedule, etc.)
2. **weekly_report_generator.py** - Generates HTML/text email reports from Google Sheets
3. **email_sender.py** - Sends emails via Gmail API
4. **weekly_scheduler.py** - Monday morning scheduler logic
5. **run_weekly_emailer.py** - Main entry point to run scheduler
6. **send_summary_now.py** - Manual trigger for testing

### Files Modified:
1. **gmail_auth.py** - Added gmail.send scope and helper function
2. **sheets_uploader.py** - Extracted reusable auth function

## How to Use

### Option 1: Automatic Weekly Emails (Recommended)

Run this command and keep it running:
```bash
python3 run_weekly_emailer.py
```

This will:
- Check every hour if it's Monday morning at 8 AM
- Automatically send weekly summary when it's time
- Track sent emails to prevent duplicates
- Run continuously until you stop it (Ctrl+C)

**To keep it running after logout:**
```bash
screen -S weekly-emailer
python3 run_weekly_emailer.py
# Press Ctrl+A then D to detach
# Reattach with: screen -r weekly-emailer
```

### Option 2: Manual Testing

Send a summary email right now (for testing):
```bash
python3 send_summary_now.py
```

This sends a report for the last 7 days immediately.

### Option 3: Test Email Only

Send a simple test email to verify sending works:
```bash
python3 -c "from email_sender import send_test_email; send_test_email()"
```

## Email Content

The weekly summary includes:
- **Summary Statistics**: Total emails, sentiment breakdown, giving status counts
- **Detailed Email Log**: Full table with date, sender, sentiment, giving status, email text
- **Color Coding**: Green (positive), Red (negative), Yellow (neutral)
- **Alerts**: Bold red highlighting for paused giving and removed bequests
- **Link**: Direct link to Google Sheets for full details

## Configuration

Edit `email_config.py` to change:
- **Recipient email**: Change `RECIPIENT_EMAIL`
- **Send time**: Change `SEND_HOUR` (default: 8 = 8 AM)
- **Send day**: Change `SEND_DAY` (default: 0 = Monday)
- **Spreadsheet URL**: Change `SPREADSHEET_URL`

## Troubleshooting

### Email not sending?
1. Check Gmail authentication:
   ```bash
   python3 gmail_auth.py
   ```
2. Make sure you granted "send" permission in the browser

### Wrong recipient?
- Edit `email_config.py` and change `RECIPIENT_EMAIL`

### Wrong schedule?
- Edit `email_config.py` and change `SEND_HOUR` or `SEND_DAY`

### Test if it's working?
```bash
python3 send_summary_now.py
```

## System Architecture

```
gmail_auto_processor.py (continuous)     run_weekly_emailer.py (continuous)
        ↓                                           ↓
Processes emails every 5 min            Checks every hour if Monday 8 AM
        ↓                                           ↓
Uploads to Google Sheets     ←──── Reads from ──── Fetches weekly data
        ↓                                           ↓
   (Data Storage)                          Generates HTML report
                                                    ↓
                                           Sends email via Gmail API
                                                    ↓
                                         efratagetachew69@gmail.com
```

## Files Overview

| File | Purpose |
|------|---------|
| `email_config.py` | Configuration settings |
| `weekly_report_generator.py` | Generate HTML/text reports from sheets |
| `email_sender.py` | Send emails via Gmail API |
| `weekly_scheduler.py` | Schedule Monday morning sends |
| `run_weekly_emailer.py` | Main script (run this!) |
| `send_summary_now.py` | Manual trigger for testing |
| `sent_summaries.json` | Track sent emails (auto-created) |

## Next Steps

1. ✅ **Authentication complete** - Gmail has send permission
2. ✅ **Test email sent** - Verified sending works
3. ✅ **Weekly summary sent** - Full report tested (48 emails)
4. **Run scheduler**: `python3 run_weekly_emailer.py`
5. **Keep it running** - Use `screen` or run in background

## Success!

The weekly email summary feature is fully implemented and tested. You can now:
- Send weekly summaries automatically every Monday at 8 AM
- Test anytime with `send_summary_now.py`
- Change settings easily in `email_config.py`
- View beautiful HTML emails with full alumni feedback details

Check `efratagetachew69@gmail.com` inbox to see the test emails that were just sent!
