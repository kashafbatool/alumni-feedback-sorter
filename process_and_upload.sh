#!/bin/bash

# Alumni Feedback Processor & Google Sheets Uploader
# This script runs the full pipeline: filter -> analyze -> upload to Google Sheets

echo "=============================================================================="
echo "ALUMNI FEEDBACK PROCESSOR & GOOGLE SHEETS UPLOADER"
echo "=============================================================================="
echo ""

# Check if spreadsheet URL was provided
if [ -z "$1" ]; then
    echo "Usage: ./process_and_upload.sh YOUR_GOOGLE_SHEET_URL [worksheet_name]"
    echo ""
    echo "Example:"
    echo "  ./process_and_upload.sh \"https://docs.google.com/spreadsheets/d/ABC123.../edit\""
    echo ""
    echo "Or with specific worksheet:"
    echo "  ./process_and_upload.sh \"https://docs.google.com/spreadsheets/d/ABC123.../edit\" \"Sheet2\""
    echo ""
    exit 1
fi

SPREADSHEET_URL="$1"
WORKSHEET_NAME="${2:-Sheet1}"

echo "Step 1/2: Processing and analyzing emails..."
echo "──────────────────────────────────────────────────────────────────────────────"
python3 data_processor_with_filter.py

if [ $? -ne 0 ]; then
    echo ""
    echo "✗ Error: Email processing failed"
    exit 1
fi

echo ""
echo "Step 2/2: Uploading to Google Sheets..."
echo "──────────────────────────────────────────────────────────────────────────────"
python3 sheets_uploader.py "$SPREADSHEET_URL" "$WORKSHEET_NAME"

if [ $? -ne 0 ]; then
    echo ""
    echo "✗ Error: Upload to Google Sheets failed"
    exit 1
fi

echo ""
echo "=============================================================================="
echo "✓ SUCCESS! All emails processed and uploaded to Google Sheets"
echo "=============================================================================="
echo ""
