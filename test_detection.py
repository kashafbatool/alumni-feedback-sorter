#!/usr/bin/env python3
"""
Test script to verify keyword detection on the specific email from row 50
"""

from email_brain import analyze_email

# This is the exact email text from row 50 in your Google Sheet
test_email = """Dear Alumni Office,

I really want to contribute to Haverford College. I would like to make a
gift and add you in my will. How would I do that? Can you put me in contact
to someone who can help me?

Best,
Polly"""

print("="*80)
print("TESTING KEYWORD DETECTION")
print("="*80)
print("\nEmail text:")
print(test_email)
print("\n" + "="*80)
print("ANALYSIS RESULT:")
print("="*80)

result = analyze_email(test_email)

print(f"\nPositive Sentiment: {result['Pos_sentiment']}")
print(f"Negative Sentiment: {result['Neg_sentiment']}")
print(f"Donate Intent: {result['Donate_Intent']}")
print(f"Giving Status (Negative): {result['Giving_Status']}")
print(f"Positive Giving Status: {result['Positive_Giving_Status']}")

print("\n" + "="*80)
if result['Positive_Giving_Status'] == "Added bequest, Making gift":
    print("✓ SUCCESS: Detection is working correctly!")
    print("  The code correctly detected BOTH 'Making gift' AND 'Added bequest'")
elif "Making gift" in result['Positive_Giving_Status']:
    print("⚠ PARTIAL: Detected 'Making gift' but might be missing other keywords")
elif "Added bequest" in result['Positive_Giving_Status']:
    print("⚠ PARTIAL: Detected 'Added bequest' but might be missing other keywords")
else:
    print("✗ FAILED: Detection not working")
    print("  Expected: 'Added bequest, Making gift'")
    print(f"  Got: '{result['Positive_Giving_Status']}'")
print("="*80)
