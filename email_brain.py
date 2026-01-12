import pandas as pd
from transformers import pipeline

print("Loading models... (This might take a minute the first time)")

# 1. Load the Sentiment Brain (Fast & Light)
# "distilbert" is a smaller, faster version of BERT
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# 2. Load the Intent Brain (Smart & Flexible)
# "bart-large-mnli" is great for Zero-Shot classification
intent_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Define the buckets you care about (Change these to match your Non-Profit's needs!)
INTENT_LABELS = [
    "Donation Inquiry",
    "Website Issue",
    "Urgent Request",
    "Complaint",
    "Meeting Request",
    "Thank You",
    "Update Info",
    "General Question"
]

def analyze_email(text):
    print(f"\nAnalyzing: '{text}'")

    # Run Sentiment
    # We truncate to 512 chars because BERT has a length limit
    sent_result = sentiment_analyzer(text[:512])[0]

    # Run Intent
    intent_result = intent_classifier(text, candidate_labels=INTENT_LABELS)

    top_intent = intent_result['labels'][0]
    sentiment = sent_result['label']
    sentiment_score = sent_result['score']

    # Fix for neutral intents being misclassified as negative
    # If the intent is clearly neutral/informational, override sentiment
    neutral_intents = ["Meeting Request", "Update Info", "General Question", "Donation Inquiry"]

    if top_intent in neutral_intents and sentiment == "NEGATIVE":
        sentiment = "NEUTRAL"

    # Organize the Output
    return {
        "Sentiment": sentiment,
        "Sentiment_Score": round(sentiment_score, 3),
        "Top_Intent": top_intent,
        "Intent_Score": round(intent_result['scores'][0], 3)
    }

# --- TEST ZONE ---
# Try it with a fake donor email
fake_email = "I've been trying to donate on your website for 20 minutes but it keeps crashing. Can someone call me?"

results = analyze_email(fake_email)
print("-" * 30)
print(results)