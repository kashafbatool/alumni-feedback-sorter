#!/bin/bash

# Alumni Feedback Processor - Gmail Integration
# Fetches emails from Gmail, processes them, and uploads to Google Sheets

set -e  # Exit on error

# Check if spreadsheet URL is provided
if [ -z "$1" ]; then
    echo "Error: Please provide the Google Sheets URL"
    echo "Usage: ./process_gmail_and_upload.sh [SPREADSHEET_URL] [MAX_EMAILS] [DAYS_BACK] [QUERY]"
    echo ""
    echo "Examples:"
    echo "  ./process_gmail_and_upload.sh 'https://docs.google.com/spreadsheets/d/YOUR_ID/edit'"
    echo "  ./process_gmail_and_upload.sh 'https://docs.google.com/spreadsheets/d/YOUR_ID/edit' 200"
    echo "  ./process_gmail_and_upload.sh 'https://docs.google.com/spreadsheets/d/YOUR_ID/edit' 100 60"
    echo "  ./process_gmail_and_upload.sh 'https://docs.google.com/spreadsheets/d/YOUR_ID/edit' 100 30 'is:unread'"
    exit 1
fi

SPREADSHEET_URL="$1"
MAX_EMAILS="${2:-100}"
DAYS_BACK="${3:-30}"
QUERY="${4:-}"

echo "========================================"
echo "Alumni Feedback Processor - Gmail Mode"
echo "========================================"
echo ""
echo "Configuration:"
echo "  - Max emails: $MAX_EMAILS"
echo "  - Days back: $DAYS_BACK"
if [ -n "$QUERY" ]; then
    echo "  - Query filter: $QUERY"
fi
echo "  - Output: Alumni_Feedback_Report_Gmail.xlsx"
echo "  - Upload to: $SPREADSHEET_URL"
echo ""

# Step 1: Process emails from Gmail
echo "[Step 1/2] Fetching and processing emails from Gmail..."
echo "------------------------------------------------------"
if [ -n "$QUERY" ]; then
    python3 data_processor_gmail.py "$MAX_EMAILS" "$DAYS_BACK" "$QUERY"
else
    python3 data_processor_gmail.py "$MAX_EMAILS" "$DAYS_BACK"
fi

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Email processing failed!"
    exit 1
fi

echo ""
echo "[Step 2/2] Uploading to Google Sheets..."
echo "------------------------------------------------------"
python3 sheets_uploader.py "$SPREADSHEET_URL" Alumni_Feedback_Report_Gmail.xlsx

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Upload to Google Sheets failed!"
    exit 1
fi

echo ""
echo "========================================"
echo "SUCCESS! Processing complete."
echo "========================================"
echo ""
echo "Results uploaded to:"
echo "$SPREADSHEET_URL"
