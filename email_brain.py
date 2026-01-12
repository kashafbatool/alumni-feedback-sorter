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
    
    # Organize the Output
    return {
        "Sentiment": sent_result['label'],       # POSITIVE / NEGATIVE
        "Sentiment_Score": round(sent_result['score'], 3),
        "Top_Intent": intent_result['labels'][0], # The winner
        "Intent_Score": round(intent_result['scores'][0], 3)
    }

# --- TEST ZONE ---
# Try it with a fake donor email
fake_email = "Your new policy regarding sharing of data with the state authorities really concerns me. I do not want my donaitons going to suveil and reoprt students to this government."

results = analyze_email(fake_email)
print("-" * 30)
print(results)