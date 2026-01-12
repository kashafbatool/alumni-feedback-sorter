import pandas as pd
import re
from transformers import pipeline

print("Loading models... (This might take a minute the first time)")

# Load the Intent Classifier (Smaller & Faster for CPU)
# Using DistilBART instead of BART-large for better performance
intent_classifier = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli")

# Define feedback-focused intent labels
FEEDBACK_LABELS = [
    "Substantive Feedback or Concern",
    "Address or Contact Update",
    "General Question or Inquiry",
    "Administrative Notification",
    "Link Sharing or Article"
]

# Define fund-related intent labels
FUND_LABELS = [
    "give_funds",
    "withdraw_funds"
]

# Keywords that indicate NON-FEEDBACK emails (auto-filter these)
FILTER_KEYWORDS = {
    "address_updates": [
        "update my address", "change my address", "new address", "moved to",
        "update contact", "change email", "new email address", "update my info",
        "change my phone", "new phone number", "mailing address"
    ],
    "admin_updates": [
        "unsubscribe", "remove me", "opt out", "stop sending",
        "automatic reply", "out of office", "auto-reply", "autoreply",
        "vacation message", "away from", "do not reply"
    ],
    "forwarded_chains": [
        "forwarded message", "fwd:", "fw:", "begin forwarded message",
        "original message", "---------- forwarded", "from:", "sent:",
        "subject:", "to:", "cc:"
    ],
    "generic_acknowledgments": [
        "thanks for the update", "noted", "thank you for letting",
        "acknowledged", "got it", "received", "will do"
    ]
}

# Keywords that indicate REAL FEEDBACK (boost these)
FEEDBACK_KEYWORDS = [
    "concern", "worried", "disappointed", "frustrated", "upset",
    "suggest", "recommendation", "should consider", "improvement",
    "issue with", "problem with", "broken", "not working", "error",
    "disagree", "oppose", "against", "don't support", "unhappy",
    "love", "appreciate", "excellent", "wonderful", "impressed",
    "complaint", "feedback", "experience with", "opinion on"
]

# Keywords that indicate FUND-RELATED emails
GIVE_FUNDS_KEYWORDS = [
    "donate", "donation", "contribute", "contribution", "giving",
    "pledge", "support financially", "make a gift", "give money",
    "want to donate", "would like to contribute", "send money"
]

WITHDRAW_FUNDS_KEYWORDS = [
    "refund", "cancel donation", "stop donation", "withdraw",
    "return my money", "get my money back", "cancel my pledge",
    "stop my contribution", "discontinue support"
]

def is_email_chain(text):
    """Detect if email is part of a forwarded chain or thread"""
    chain_patterns = [
        r'From:.*\n.*Sent:.*\n.*To:',
        r'Begin forwarded message',
        r'---------- Forwarded message',
        r'On .* wrote:',
        r'From:.*<.*@.*>',
    ]

    for pattern in chain_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    # Check if multiple "From:" or "Sent:" lines exist
    from_count = len(re.findall(r'^From:', text, re.MULTILINE | re.IGNORECASE))
    sent_count = len(re.findall(r'^Sent:', text, re.MULTILINE | re.IGNORECASE))

    return from_count > 1 or sent_count > 1

def is_link_only(text):
    """Detect if email is just links with no substantive content"""
    # Remove URLs from text
    text_without_urls = re.sub(r'http[s]?://\S+', '', text)
    text_without_urls = re.sub(r'www\.\S+', '', text_without_urls)

    # Clean up whitespace
    cleaned = text_without_urls.strip()

    # If what's left is less than 50 characters, it's likely link-only
    return len(cleaned) < 50

def is_empty_or_minimal(text):
    """Check if email body is essentially empty"""
    # Remove whitespace, newlines, and common email signatures
    cleaned = re.sub(r'\s+', '', text)
    cleaned = re.sub(r'(Sent from my|Sent via|Get Outlook)', '', cleaned, flags=re.IGNORECASE)

    return len(cleaned) < 20

def check_filter_keywords(text):
    """Check if text contains keywords that indicate non-feedback"""
    text_lower = text.lower()

    matches = {}
    for category, keywords in FILTER_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matches[category] = matches.get(category, 0) + 1

    return matches

def check_feedback_keywords(text):
    """Check if text contains keywords that indicate real feedback"""
    text_lower = text.lower()
    count = 0

    for keyword in FEEDBACK_KEYWORDS:
        if keyword.lower() in text_lower:
            count += 1

    return count

def check_fund_keywords(text):
    """Check if text contains keywords that indicate fund-related emails"""
    text_lower = text.lower()

    give_count = 0
    withdraw_count = 0

    for keyword in GIVE_FUNDS_KEYWORDS:
        if keyword.lower() in text_lower:
            give_count += 1

    for keyword in WITHDRAW_FUNDS_KEYWORDS:
        if keyword.lower() in text_lower:
            withdraw_count += 1

    return give_count, withdraw_count

def filter_email(text, subject=""):
    """
    Main filtration function

    Returns 5 values:
    1. is_feedback - True if this is real feedback that should be kept
    2. is_address_update - True if this is just an address/contact update
    3. is_email_chain - True if this is a forwarded chain or thread
    4. is_admin_auto - True if this is an admin notification or auto-reply
    5. fund_intent - True if give_funds, False if withdraw_funds, None if not fund-related
    """

    # Combine subject and body for analysis
    full_text = f"{subject} {text}" if subject else text

    # Print for debugging (will remove later)
    # Commented out for cleaner output
    # print(f"\n{'='*60}")
    # print(f"Analyzing email...")
    # print(f"Preview: {full_text[:100]}...")

    # Initialize booleans
    is_feedback = False
    is_address_update = False
    is_email_chain_flag = False
    is_admin_auto = False
    fund_intent = None

    # Quick checks
    if is_empty_or_minimal(full_text):
        # print("❌ FILTERED: Empty or minimal content")
        return False, False, False, True, None

    if is_link_only(full_text):
        # print("❌ FILTERED: Link-only email")
        return False, False, False, False, None

    if is_email_chain(full_text):
        # print("❌ FILTERED: Email chain/forward detected")
        is_email_chain_flag = True
        return False, False, True, False, None

    # Check for filter keywords
    filter_matches = check_filter_keywords(full_text)

    if filter_matches:
        if "admin_updates" in filter_matches and filter_matches["admin_updates"] >= 1:
            # print(f"❌ FILTERED: Admin update detected")
            is_admin_auto = True
            return False, False, False, True, None

        if "address_updates" in filter_matches and filter_matches["address_updates"] >= 1:
            # print(f"❌ FILTERED: Address update detected")
            is_address_update = True
            return False, True, False, False, None

        if "forwarded_chains" in filter_matches and filter_matches["forwarded_chains"] >= 3:
            # print(f"❌ FILTERED: Forwarded chain detected")
            is_email_chain_flag = True
            return False, False, True, False, None

    # Check for feedback keywords (positive signal)
    feedback_keyword_count = check_feedback_keywords(full_text)

    # Check for fund-related keywords
    give_count, withdraw_count = check_fund_keywords(full_text)

    # Run AI Intent Classification for feedback
    intent_result = intent_classifier(full_text[:512], candidate_labels=FEEDBACK_LABELS)
    top_intent = intent_result['labels'][0]
    intent_score = intent_result['scores'][0]

    # Run AI Intent Classification for funds (only if fund keywords detected)
    if give_count > 0 or withdraw_count > 0:
        fund_result = intent_classifier(full_text[:512], candidate_labels=FUND_LABELS)
        top_fund_intent = fund_result['labels'][0]
        fund_score = fund_result['scores'][0]

        if fund_score > 0.5:
            if top_fund_intent == "give_funds":
                fund_intent = True
                # print(f"💰 FUND INTENT: give_funds (confidence: {fund_score:.3f})")
            elif top_fund_intent == "withdraw_funds":
                fund_intent = False
                # print(f"💸 FUND INTENT: withdraw_funds (confidence: {fund_score:.3f})")
        # else:
            # print(f"🤷 FUND INTENT: Uncertain (confidence too low)")

    # print(f"Top Intent: {top_intent} (confidence: {intent_score:.3f})")
    # print(f"Feedback keywords found: {feedback_keyword_count}")

    # Decision logic
    if top_intent == "Substantive Feedback or Concern" and intent_score > 0.35:
        is_feedback = True
        # print(f"✅ KEEP: AI classified as feedback")
    elif feedback_keyword_count >= 2:
        is_feedback = True
        # print(f"✅ KEEP: Multiple feedback keywords ({feedback_keyword_count})")
    elif top_intent == "Address or Contact Update" and intent_score > 0.5:
        is_address_update = True
        # print(f"❌ FILTER: AI classified as address update")
    elif top_intent == "Administrative Notification" and intent_score > 0.5:
        is_admin_auto = True
        # print(f"❌ FILTER: AI classified as admin notification")
    elif top_intent == "General Question or Inquiry" and intent_score > 0.6 and feedback_keyword_count == 0:
        pass  # print(f"❌ FILTER: Generic question without feedback")
    elif top_intent == "Link Sharing or Article" and intent_score > 0.5:
        pass  # print(f"❌ FILTER: Link sharing")
    else:
        # Default to keeping if uncertain and has some feedback signals
        if feedback_keyword_count >= 1:
            is_feedback = True
            # print(f"✅ KEEP: Uncertain but has feedback signals")
        # else:
            # print(f"❌ FILTER: No clear feedback indicators")

    return is_feedback, is_address_update, is_email_chain_flag, is_admin_auto, fund_intent

def analyze_emails_batch(emails):
    """
    Process a batch of emails and return results as a DataFrame

    Args:
        emails: List of dicts with 'subject' and 'body' keys

    Returns:
        pandas DataFrame with analysis results
    """
    results = []

    for i, email in enumerate(emails, 1):
        print(f"Processing email {i}/{len(emails)}...")
        subject = email.get("subject", "")
        body = email.get("body", "")

        # Get full analysis
        is_feedback, is_address_update, is_email_chain_flag, is_admin_auto, fund_intent = filter_email(body, subject)

        # Combine for intent classification to get sentiment
        full_text = f"{subject} {body}" if subject else body

        # Run AI Intent Classification for detailed results
        if not is_empty_or_minimal(full_text) and not is_link_only(full_text):
            intent_result = intent_classifier(full_text[:512], candidate_labels=FEEDBACK_LABELS)
            top_intent = intent_result['labels'][0]
            intent_score = round(intent_result['scores'][0], 3)
        else:
            top_intent = "Empty/Minimal"
            intent_score = 1.0

        # Determine sentiment based on feedback keywords
        feedback_kw_count = check_feedback_keywords(full_text)
        if feedback_kw_count > 0:
            sentiment = "Concerned/Engaged"
        elif is_admin_auto or is_empty_or_minimal(full_text):
            sentiment = "Neutral"
        else:
            sentiment = "Neutral"

        # Convert fund_intent to readable format
        if fund_intent is True:
            fund_status = "give_funds"
        elif fund_intent is False:
            fund_status = "withdraw_funds"
        else:
            fund_status = None

        results.append({
            "Email_Number": i,
            "Subject": subject[:50] + "..." if len(subject) > 50 else subject,
            "Body_Preview": body[:50] + "..." if len(body) > 50 else body,
            "Sentiment": sentiment,
            "Top_Intent": top_intent,
            "Intent_Score": intent_score,
            "Is_Feedback": is_feedback,
            "Is_Address_Update": is_address_update,
            "Is_Email_Chain": is_email_chain_flag,
            "Is_Admin_Auto": is_admin_auto,
            "Fund_Intent": fund_status
        })

    return pd.DataFrame(results)

# --- TEST ZONE ---
if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTING EMAIL FILTRATION SYSTEM")
    print("="*60)

    # Starting with 5 test emails for faster processing - you can add more later
    test_emails = [
        {
            "subject": "Unhappy with recent changes",
            "body": "I'm very upset about the new scholarship requirements. This is going to hurt students from low-income families. Please reconsider this decision."
        },
        {
            "subject": "New phone number",
            "body": "Please update my phone number in your system. My new number is 555-123-4567. Thank you!"
        },
        {
            "subject": "Portal login not working",
            "body": "I've been trying to log into the alumni portal for three days now and keep getting error 500. This is really frustrating because I need to access my transcripts urgently."
        },
        {
            "subject": "Making a contribution",
            "body": "I'd like to contribute $1000 to the scholarship fund. What's the best way to make this donation? I want to support students in the engineering program."
        },
        {
            "subject": "Unsubscribe",
            "body": "Please remove me from your mailing list. I do not wish to receive further emails."
        }
    ]

    # Process all emails and get tabular results
    print("\nProcessing emails...")
    df = analyze_emails_batch(test_emails)

    # Save to CSV
    output_file = "email_analysis_results.csv"
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")

    print("\n" + "="*80)
    print("TABULAR RESULTS")
    print("="*80)
    print("\n")

    # Display with better formatting
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 50)
    print(df.to_string(index=False))

    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print(f"Total Emails Analyzed: {len(df)}")
    print(f"Feedback Emails: {df['Is_Feedback'].sum()}")
    print(f"Address Updates: {df['Is_Address_Update'].sum()}")
    print(f"Email Chains: {df['Is_Email_Chain'].sum()}")
    print(f"Admin/Auto Replies: {df['Is_Admin_Auto'].sum()}")
    print(f"Give Funds: {(df['Fund_Intent'] == 'give_funds').sum()}")
    print(f"Withdraw Funds: {(df['Fund_Intent'] == 'withdraw_funds').sum()}")
    print(f"No Fund Intent: {df['Fund_Intent'].isna().sum()}")
    print("="*80)

    print(f"\nFull results available in: {output_file}")
