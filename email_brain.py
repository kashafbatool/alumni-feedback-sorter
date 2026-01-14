import pandas as pd
from transformers import pipeline

print("Loading models... (This might take a minute the first time)")

# 1. Load the Sentiment Brain (Fast & Light)
# "distilbert" is a smaller, faster version of BERT
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# 2. Load the Intent Brain (Smart & Flexible)
# "bart-large-mnli" is great for Zero-Shot classification
intent_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Define the categories you care about (Change these to match your Non-Profit's needs!)
# Sentiment categories
SENTIMENT_LABELS = ["Positive", "Negative"]

# Intent categories - customize these based on your supervisor's needs
INTENT_LABELS = [
    "Donation Inquiry",
    "Withdrawing support or ending relationship",
    "Website Issue",
    "Complaint about service",
    "Meeting Request",
    "Thank You",
    "Update Info"
]

def analyze_email(text):
    print(f"\nAnalyzing: '{text}'")

    # Run Sentiment Analysis
    sent_result = sentiment_analyzer(text[:512])[0]

    # Run Intent Classification - get scores for ALL categories
    intent_result = intent_classifier(text, candidate_labels=INTENT_LABELS)

    # Create a dictionary mapping each label to its score
    intent_scores = dict(zip(intent_result['labels'], intent_result['scores']))

    # BOOLEAN APPROACH: Set threshold for "Yes"
    INTENT_THRESHOLD = 0.20  # Lower threshold to catch more donation mentions
    WITHDRAWN_THRESHOLD = 0.18  # Slightly lower for catching explicit withdrawal language
    SENTIMENT_THRESHOLD = 0.25  # Threshold for detecting positive/negative independently (lowered to catch mixed)

    # INDEPENDENT SENTIMENT DETECTION - allows for mixed emotions
    # Use zero-shot classification to check for positive AND negative aspects separately
    sentiment_result = intent_classifier(
        text,
        candidate_labels=["expressing gratitude or happiness", "expressing complaint or disappointment", "neutral inquiry"],
        multi_label=True  # This allows multiple labels to be true at once
    )

    sentiment_dict = dict(zip(sentiment_result['labels'], sentiment_result['scores']))

    positive_score = sentiment_dict.get("expressing gratitude or happiness", 0)
    negative_score = sentiment_dict.get("expressing complaint or disappointment", 0)
    neutral_score = sentiment_dict.get("neutral inquiry", 0)

    # Determine Pos_sentiment independently
    if positive_score > SENTIMENT_THRESHOLD:
        pos_sentiment = "Yes"
    elif neutral_score > 0.5 or positive_score < 0.15:
        pos_sentiment = "Null"
    else:
        pos_sentiment = "No"

    # Determine Neg_sentiment independently (can be Yes even if Pos is Yes)
    if negative_score > SENTIMENT_THRESHOLD:
        neg_sentiment = "Yes"
    elif neutral_score > 0.5 or negative_score < 0.15:
        neg_sentiment = "Null"
    else:
        neg_sentiment = "No"

    # Intent Booleans - check each category independently
    donate_intent = "Yes" if intent_scores.get("Donation Inquiry", 0) > INTENT_THRESHOLD else "No"

    # Bequest/Giving Intent Detection (4 categories)
    text_lower = text.lower()

    # Keywords for each category
    paused_keywords = ["paused", "pausing", "suspend", "suspending", "stop giving", "stopped giving",
                       "halt", "halting", "temporarily stop", "hold off", "step back", "stepping back",
                       "take a step back", "taking a step back", "pause my", "pause our",
                       "discontinue", "discontinuing", "end my support", "ending my support"]
    resumed_keywords = ["resumed", "resuming", "restart", "restarting", "begin again", "start again",
                        "continue giving", "will continue", "keep giving", "keep donating"]
    removed_bequest_keywords = ["remove", "removed", "revoke", "revoked", "changed my will",
                                "updated my will", "no longer in my will", "taken out of will",
                                "eliminate", "eliminated", "withdrawn from estate"]
    added_bequest_keywords = ["added to will", "included in will", "left in will", "bequest",
                              "estate plan", "planned giving", "legacy gift", "leaving to"]

    # Check for each category (order matters - most specific first)
    if any(keyword in text_lower for keyword in removed_bequest_keywords):
        giving_status = "Removed bequest"
    elif any(keyword in text_lower for keyword in added_bequest_keywords):
        giving_status = "Added bequest"
    elif any(keyword in text_lower for keyword in resumed_keywords):
        giving_status = "Resumed giving"
    elif any(keyword in text_lower for keyword in paused_keywords):
        giving_status = "Paused giving"
    else:
        # Fall back to general withdrawal detection
        withdrawal_score = intent_scores.get("Withdrawing support or ending relationship", 0)
        if withdrawal_score > WITHDRAWN_THRESHOLD:
            # Check if it's likely about bequest or regular giving
            if any(word in text_lower for word in ["will", "estate", "bequest", "legacy", "planned"]):
                giving_status = "Removed bequest"
            else:
                giving_status = "Paused giving"
        else:
            giving_status = "No"  # No change detected - default to "No"

    # Organize the Output
    return {
        "Pos_sentiment": pos_sentiment,
        "Neg_sentiment": neg_sentiment,
        "Donate_Intent": donate_intent,
        "Giving_Status": giving_status
    }

# --- TEST ZONE ---
# Try it with a fake donor email
fake_email = "Your new policy regarding sharing of data with the state authorities really concerns me. I do not want my donaitons going to suveil and reoprt students to this government."

results = analyze_email(fake_email)
print("-" * 30)
print(results)