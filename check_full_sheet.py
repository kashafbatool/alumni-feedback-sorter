#!/usr/bin/env python3
"""
Check ALL rows in the sheet to find the new data
"""

from sheets_uploader import get_sheets_service
import sys

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1R6H2gC-lazqw0dvlBdAonqinnw7QlKLe_1uFfSqBL08/edit"

client = get_sheets_service()
if not client:
    sys.exit(1)

sheet = client.open_by_url(SPREADSHEET_URL)
jan_ws = sheet.worksheet("jan 2026")

# Get ALL values (not just records)
all_values = jan_ws.get_all_values()
print(f"Total rows in sheet (including header): {len(all_values)}")

if len(all_values) > 0:
    headers = all_values[0]
    print(f"\nHeaders: {headers[:5]}...")  # First 5 headers

    # Find the index of the "Making gift" column
    target_col = "Making gift, resuming giving, or revising their will to add the College"
    try:
        col_idx = headers.index(target_col)
        print(f"\n'Making gift...' column is at index {col_idx}")
    except ValueError:
        print(f"\n⚠ Column '{target_col}' not found!")
        print(f"Available columns: {headers}")
        sys.exit(1)

# Check for the test email about Polly (last email processed)
print("\n" + "="*80)
print("SEARCHING FOR POLLY (the test email with 'make a gift and add you in my will')")
print("="*80)

found = False
for i, row in enumerate(all_values[1:], start=1):  # Skip header
    if len(row) > 0 and 'polly' in str(row[0]).lower() + str(row[1]).lower():
        print(f"\nFound Polly at row {i}:")
        print(f"  Name: {row[0]} {row[1]}")
        if len(row) > col_idx:
            giving_status = row[col_idx]
            print(f"  Positive Giving Status: '{giving_status}'")

            if "," in giving_status:
                print("  ✓ MULTI-VALUE DETECTED!")
            elif giving_status and giving_status != "No":
                print("  ⚠ Single value detected")
            else:
                print("  ✗ No positive giving status")
        found = True

if not found:
    print("\n⚠ Polly not found in the sheet")
    print("Checking last 10 rows...")
    for i in range(max(1, len(all_values) - 10), len(all_values)):
        row = all_values[i]
        if len(row) > 2:
            name = f"{row[0]} {row[1]}" if len(row) > 1 else row[0]
            date = row[4] if len(row) > 4 else 'N/A'
            giving = row[col_idx] if len(row) > col_idx else 'N/A'
            print(f"Row {i}: {name} | Date: {date} | Giving: '{giving}'")

# Count rows by date
print("\n" + "="*80)
print("ROWS BY DATE:")
print("="*80)
from collections import Counter
date_col_idx = 4  # "Date Received" is typically column 4
dates = [row[date_col_idx] if len(row) > date_col_idx else 'N/A' for row in all_values[1:]]
date_counts = Counter(dates)
for date, count in sorted(date_counts.items(), reverse=True)[:10]:
    print(f"  {date}: {count} rows")

# Check for multi-value in ANY row
print("\n" + "="*80)
print("CHECKING FOR MULTI-VALUE DETECTION:")
print("="*80)
multi_value_rows = []
for i, row in enumerate(all_values[1:], start=1):
    if len(row) > col_idx:
        giving_status = row[col_idx]
        if "," in giving_status:
            multi_value_rows.append((i, row[0], row[1], giving_status))

if multi_value_rows:
    print(f"\n✓ Found {len(multi_value_rows)} rows with multi-value detection!")
    print("\nExamples:")
    for row_num, first, last, status in multi_value_rows[:5]:
        print(f"  Row {row_num}: {first} {last} → '{status}'")
else:
    print("\n✗ NO multi-value detection found in any row")
    print("This suggests the new data wasn't uploaded or the old data is still there")
