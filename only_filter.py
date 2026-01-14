import pandas as pd
import re
from transformers import pipeline

print("Loading models... (This might take a minute the first time)")

# Load the Intent Classifier (Smaller & Faster for CPU)
intent_classifier = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli")

# Define feedback-focused intent labels
FEEDBACK_LABELS = [
    "Substantive Feedback or Concern",
    "Address or Contact Update",
    "General Question or Inquiry",
    "Administrative Notification",
    "Link Sharing or Article"
]

# Keywords that indicate NON-FEEDBACK emails (auto-filter these)
FILTER_KEYWORDS = {
    "address_updates": [
        "update my address", "change my address", "new address", "moved to",
        "update contact", "change email", "new email address", "update my info",
        "change my phone", "new phone number", "mailing address"
    ],
    "admin_updates": [
        "automatic reply", "out of office", "auto-reply", "autoreply",
        "vacation message", "away from", "do not reply",
        "iam.gserviceaccount.com", "service account", "unique id"
    ],
    "forwarded_chains": [
        "forwarded message", "fwd:", "fw:", "begin forwarded message",
        "original message", "---------- forwarded", "from:", "sent:",
        "subject:", "to:", "cc:"
    ],
    "generic_acknowledgments": [
        "thanks for the update", "noted", "thank you for letting",
        "acknowledged", "got it", "received", "will do"
    ],
    "parent_positive_only": [
        "parent of class of", "as a parent", "proud parent", "my student",
        "our student", "my child", "our child", "my daughter", "my son"
    ],
    "technical_support": [
        "reset my password", "reset my account", "can't log in", "cannot log in",
        "login not working", "portal login", "forgot password", "password reset",
        "access my account", "unlock my account", "reset password"
    ],
    "event_inquiries": [
        "reunion schedule", "event schedule", "ticket prices", "accommodation suggestions",
        "what time", "when is the", "where is the", "how do i register", "rsvp",
        "planning to attend", "attend the reunion", "attend the event",
        "schedule for", "agenda for", "registration details"
    ]
}

# Keywords that indicate REAL FEEDBACK (boost these)
FEEDBACK_KEYWORDS = [
    "concern", "worried", "disappointed", "frustrated", "upset",
    "suggest", "recommendation", "should consider", "improvement",
    "issue with", "problem with", "broken", "not working", "error",
    "disagree", "oppose", "against", "don't support", "unhappy",
    "love", "appreciate", "excellent", "wonderful", "impressed",
    "complaint", "feedback", "experience with", "opinion on",
    "unsubscribe", "remove me", "opt out", "stop sending", "no longer want",
    # Bequest and giving-related keywords
    "will", "estate", "bequest", "planned giving", "legacy", "financial plans",
    "personal plans", "commitments", "no longer directed", "removing from",
    "update my plans", "change my plans", "trust", "confidence",
    # Strong formal negative language
    "infuriating", "infuriated", "eroded", "undermined", "betrayed",
    "outraged", "alarmed", "appalled", "disgraceful", "unacceptable",
    "course-correct", "rebuild trust", "lost confidence", "serious reflection"
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

def should_filter(text, subject=""):
    """
    Main filtration function

    Returns:
        True if email should be FILTERED OUT (removed)
        False if email should be KEPT (no_filter - it's feedback)
    """

    # Combine subject and body for analysis
    full_text = f"{subject} {text}" if subject else text

    # Quick checks - filter these out
    if is_empty_or_minimal(full_text):
        return True  # FILTER

    if is_link_only(full_text):
        return True  # FILTER

    if is_email_chain(full_text):
        return True  # FILTER

    # Check for filter keywords
    filter_matches = check_filter_keywords(full_text)

    if filter_matches:
        if "admin_updates" in filter_matches and filter_matches["admin_updates"] >= 1:
            return True  # FILTER

        if "address_updates" in filter_matches and filter_matches["address_updates"] >= 1:
            return True  # FILTER

        if "forwarded_chains" in filter_matches and filter_matches["forwarded_chains"] >= 3:
            return True  # FILTER

        if "technical_support" in filter_matches and filter_matches["technical_support"] >= 1:
            return True  # FILTER - technical support requests not relevant to alumni tracking

        if "event_inquiries" in filter_matches and filter_matches["event_inquiries"] >= 1:
            return True  # FILTER - event logistics questions not alumni feedback

    # Check for parent emails - filter if only positive thank-you with no concerns
    text_lower = full_text.lower()
    is_parent_email = "parent_positive_only" in filter_matches and filter_matches["parent_positive_only"] >= 1

    # Check for feedback keywords (positive signal)
    feedback_keyword_count = check_feedback_keywords(full_text)

    # Check for negative/concern keywords specifically
    negative_keywords = ["concern", "worried", "disappointed", "frustrated", "upset", "issue", "problem",
                        "disagree", "oppose", "unhappy", "complaint", "infuriating", "undermined",
                        "eroded", "betrayed", "outraged", "alarmed", "appalled", "unacceptable",
                        "will", "estate", "bequest", "financial plans", "no longer directed",
                        "stop giving", "pause", "suspend", "discontinue", "step back"]
    has_negative_concerns = any(kw in text_lower for kw in negative_keywords)

    # If it's a parent email with only positive feedback and no concerns, filter it out
    if is_parent_email and not has_negative_concerns:
        return True  # FILTER - parent positive thank-you not relevant to alumni tracking

    # Run AI Intent Classification for feedback
    intent_result = intent_classifier(full_text[:512], candidate_labels=FEEDBACK_LABELS)
    top_intent = intent_result['labels'][0]
    intent_score = intent_result['scores'][0]

    # Decision logic - determine if this is feedback worth keeping
    if top_intent == "Substantive Feedback or Concern" and intent_score > 0.35:
        return False  # NO_FILTER - Keep this feedback
    elif feedback_keyword_count >= 2:
        return False  # NO_FILTER - Keep this feedback
    elif top_intent == "Address or Contact Update" and intent_score > 0.5:
        return True  # FILTER
    elif top_intent == "Administrative Notification" and intent_score > 0.5:
        return True  # FILTER
    elif top_intent == "General Question or Inquiry" and intent_score > 0.6 and feedback_keyword_count == 0:
        return True  # FILTER
    elif top_intent == "Link Sharing or Article" and intent_score > 0.5:
        return True  # FILTER
    else:
        # Default to keeping if uncertain and has some feedback signals
        if feedback_keyword_count >= 1:
            return False  # NO_FILTER - Keep this
        else:
            return True  # FILTER

def analyze_emails_batch(emails):
    """
    Process a batch of emails and return results as a DataFrame

    Args:
        emails: List of dicts with 'subject' and 'body' keys

    Returns:
        pandas DataFrame with simple filter results
    """
    results = []

    for i, email in enumerate(emails, 1):
        print(f"Processing email {i}/{len(emails)}...")
        subject = email.get("subject", "")
        body = email.get("body", "")

        # Get filter decision
        should_be_filtered = should_filter(body, subject)

        # Convert to simple output
        decision = "filter" if should_be_filtered else "no_filter"

        results.append({
            "Email_Number": i,
            "Subject": subject[:60] + "..." if len(subject) > 60 else subject,
            "Body_Preview": body[:60] + "..." if len(body) > 60 else body,
            "Decision": decision
        })

    return pd.DataFrame(results)

# --- TEST ZONE ---
if __name__ == "__main__":
    print("\n" + "="*60)
    print("EMAIL FILTRATION SYSTEM - SIMPLE OUTPUT")
    print("="*60)

    # Test emails - 15 samples
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
        },
        {
            "subject": "Fwd: Article",
            "body": "Begin forwarded message\nFrom: Someone\nCheck this out: https://example.com/article"
        },
        {
            "subject": "Website broken",
            "body": "The website has been broken for days. This is a huge problem and needs to be fixed immediately. Very disappointed with the service."
        },
        {
            "subject": "Out of office",
            "body": "This is an automatic reply. I am out of office until next Monday and will respond when I return."
        },
        {
            "subject": "Poor customer service",
            "body": "I called three times about my issue and nobody helped me. Your customer service is terrible and needs major improvement."
        },
        {
            "subject": "Change my email",
            "body": "Hi, please change my email from old@example.com to new@example.com. Thanks!"
        },
        {
            "subject": "RE: RE: Meeting notes",
            "body": "From: John Smith\nSent: Tuesday\nTo: Team\n\nGreat points everyone!\n\nFrom: Jane Doe\nThanks for sharing."
        },
        {
            "subject": "Link only",
            "body": "https://news.site.com/article-12345\n\nSent from my iPhone"
        },
        {
            "subject": "Love the new program!",
            "body": "Just wanted to say the new mentorship program is excellent! I'm so impressed with how well it's organized. Thank you for creating this!"
        },
        {
            "subject": "What time is the event?",
            "body": "Quick question - what time does the alumni event start on Saturday?"
        },
        {
            "subject": "Safety issues on campus",
            "body": "I'm really concerned about safety on campus. The parking lot lighting is broken and it's dangerous at night. This needs to be fixed ASAP."
        }
    ]

    # Process all emails and get tabular results
    print("\nProcessing emails...")
    df = analyze_emails_batch(test_emails)

    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print("\n")

    # Display results
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 60)
    print(df.to_string(index=False))

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total Emails: {len(df)}")
    print(f"Filter (Remove): {(df['Decision'] == 'filter').sum()}")
    print(f"No Filter (Keep): {(df['Decision'] == 'no_filter').sum()}")
    print("="*80)
