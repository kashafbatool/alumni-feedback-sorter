#!/usr/bin/env python3
"""
Check what's actually in the Google Sheet
"""

from sheets_uploader import get_sheets_service
import sys

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1R6H2gC-lazqw0dvlBdAonqinnw7QlKLe_1uFfSqBL08/edit"

print("="*80)
print("CHECKING GOOGLE SHEET DATA")
print("="*80)

# Get authenticated client
client = get_sheets_service()
if not client:
    print("✗ Failed to authenticate")
    sys.exit(1)

print("✓ Authenticated with Google Sheets")

# Open spreadsheet
sheet = client.open_by_url(SPREADSHEET_URL)
print(f"✓ Opened sheet: {sheet.title}")

# Get all worksheets
worksheets = sheet.worksheets()
print(f"\nFound {len(worksheets)} worksheets:")
for ws in worksheets:
    print(f"  - {ws.title}")

# Check the jan 2026 worksheet (most recent)
jan_ws = sheet.worksheet("jan 2026")
print(f"\n✓ Reading 'jan 2026' worksheet...")

# Get all records
records = jan_ws.get_all_records()
print(f"✓ Found {len(records)} rows of data")

if len(records) == 0:
    print("\n⚠ WARNING: The sheet is empty!")
    print("You need to run gmail_to_sheets.py to populate it with data.")
    sys.exit(1)

# Check specific rows
print("\n" + "="*80)
print("CHECKING SPECIFIC ROWS:")
print("="*80)

# Check row 50 (index 49 in zero-indexed array)
if len(records) >= 50:
    row_50 = records[49]
    print(f"\nRow 50:")
    print(f"  First Name: {row_50.get('First Name', 'N/A')}")
    print(f"  Last Name: {row_50.get('Last Name', 'N/A')}")
    print(f"  Positive Giving Status: '{row_50.get('Making gift, resuming giving, or revising their will to add the College', 'N/A')}'")
    email_text = row_50.get('Email Text/Synopsis of Conversation/Notes', '')
    print(f"  Email preview: {email_text[:100]}...")
else:
    print(f"\n⚠ Row 50 doesn't exist (only {len(records)} rows)")

# Check last 5 rows
print(f"\n" + "="*80)
print(f"LAST 5 ROWS (Most Recently Processed):")
print("="*80)

for i in range(max(0, len(records) - 5), len(records)):
    row = records[i]
    giving_status = row.get('Making gift, resuming giving, or revising their will to add the College', 'N/A')
    print(f"\nRow {i+1}:")
    print(f"  Name: {row.get('First Name', '')} {row.get('Last Name', '')}")
    print(f"  Date: {row.get('Date Received', 'N/A')}")
    print(f"  Positive Giving Status: '{giving_status}'")

print("\n" + "="*80)
print("SUMMARY:")
print("="*80)

# Count how many rows have the new multi-value format
multi_value_count = 0
for record in records:
    giving_status = str(record.get('Making gift, resuming giving, or revising their will to add the College', ''))
    if ',' in giving_status:  # Contains comma = multiple values
        multi_value_count += 1

print(f"\nRows with multi-value detection (comma-separated): {multi_value_count}")
print(f"Total rows: {len(records)}")

if multi_value_count == 0:
    print("\n⚠ WARNING: No rows have the new multi-value detection!")
    print("This means the emails haven't been re-analyzed with the new code.")
    print("\nTo fix this:")
    print("1. Make sure there are unread emails in inboxtest33@gmail.com")
    print("2. Run: python3 gmail_to_sheets.py https://docs.google.com/spreadsheets/d/1R6H2gC-lazqw0dvlBdAonqinnw7QlKLe_1uFfSqBL08/edit")
    print("3. Check the output to see how many emails were processed")
else:
    print(f"\n✓ Found {multi_value_count} rows with new detection!")

print("="*80)
