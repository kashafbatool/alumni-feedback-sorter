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
    "Withdrawn or Unhappy",
    "Website Issue",
    "Complaint",
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

    # BOOLEAN APPROACH: Set threshold for "Yes" (e.g., > 30% confidence = Yes)
    THRESHOLD = 0.30

    # Sentiment Booleans
    pos_sentiment = "Yes" if sent_result['label'] == "POSITIVE" and sent_result['score'] > 0.6 else "No"
    neg_sentiment = "Yes" if sent_result['label'] == "NEGATIVE" and sent_result['score'] > 0.6 else "No"

    # If neither is confident, mark as Null
    if sent_result['score'] <= 0.6:
        pos_sentiment = "Null"
        neg_sentiment = "Null"

    # Intent Booleans - check each category independently
    donate_intent = "Yes" if intent_scores.get("Donation Inquiry", 0) > THRESHOLD else "No"
    withdrawn_intent = "Yes" if intent_scores.get("Withdrawn or Unhappy", 0) > THRESHOLD else "No"

    # Organize the Output as Booleans
    return {
        "Pos_sentiment": pos_sentiment,
        "Neg_sentiment": neg_sentiment,
        "Donate_Intent": donate_intent,
        "Withdrawn_Intent": withdrawn_intent
    }

# --- TEST ZONE ---
# Try it with a fake donor email
fake_email = "I've been trying to donate on your website for 20 minutes but it keeps crashing. Can someone call me?"

results = analyze_email(fake_email)
print("-" * 30)
print(results)