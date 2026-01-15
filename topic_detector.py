"""
Topic Detection and Clustering for Email Batches

This module identifies major topics/events in email batches and clusters
related emails together for topic-specific sheet creation.

Example: If 5+ emails mention "President Raymond retiring", they get
grouped into a "President Raymond - Jan 2026" topic cluster.
"""

import pandas as pd
from transformers import pipeline
from collections import Counter
import re

print("Loading topic detection models...")
# Use zero-shot classification for topic identification
topic_classifier = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli")

# Common topic categories for alumni feedback
TOPIC_CATEGORIES = [
    "Leadership change or resignation",
    "Tuition or financial policy change",
    "Campus safety or security issue",
    "Academic program change",
    "Diversity or inclusion concern",
    "Facility or infrastructure issue",
    "Student support services",
    "General donation or giving",
    "Other feedback"
]

def extract_key_entities(text):
    """
    Extract key people, places, and topics from text
    Simple regex-based extraction for names and institutions
    """
    entities = []

    # Extract capitalized names (likely people or places)
    # Pattern: Two or more capitalized words together
    cap_entities = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', text)
    entities.extend(cap_entities)

    # Common role titles that might be mentioned (case insensitive)
    # Pattern: "president raymond", "President Raymond", etc.
    role_patterns = [
        r'\b(president|dean|provost|chancellor|director|coach|dr\.?|prof\.?)\s+([A-Za-z]+)',
        r'\b([A-Za-z]+)\s+(president|dean|provost|chancellor)',
    ]

    for pattern in role_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # Normalize to title case
            entity = f"{match[0].title()} {match[1].title()}"
            entities.append(entity)

    # Remove duplicates and normalize
    normalized = []
    for entity in entities:
        # Normalize spacing and case
        normalized_entity = ' '.join(entity.split()).title()
        if normalized_entity not in normalized:
            normalized.append(normalized_entity)

    return normalized

def detect_major_topics(emails, min_cluster_size=5):
    """
    Detect major topics in a batch of emails

    Args:
        emails: List of dicts with 'Subject' and 'Body' keys
        min_cluster_size: Minimum number of emails to form a topic cluster

    Returns:
        dict: {
            'topics': [{'name': str, 'emails': [indices], 'size': int}],
            'topic_assignments': [topic_index or -1 for each email]
        }
    """
    if len(emails) < min_cluster_size:
        return {'topics': [], 'topic_assignments': [-1] * len(emails)}

    # Combine subject and body for analysis
    texts = [f"{email.get('Subject', '')} {email.get('Body', '')}" for email in emails]

    # Step 1: Extract entities from all emails
    all_entities = []
    for text in texts:
        entities = extract_key_entities(text)
        all_entities.append(entities)

    # Step 2: Normalize and find common entities
    # Normalize similar entities (e.g., "President Raymond" and "President Raymonds")
    def normalize_entity(entity):
        # Remove trailing 's' for possessive/plural
        normalized = entity.rstrip('s').rstrip("'").strip()
        # Filter out generic entities like "See President", "To President"
        words = normalized.split()
        if len(words) == 2 and words[0] in ['See', 'To', 'Is', 'Appreciated', 'While', 'Because']:
            return None
        return normalized

    # Group similar entities
    entity_groups = {}  # normalized_entity -> [original entities]
    for entities in all_entities:
        for entity in entities:
            norm = normalize_entity(entity)
            if norm:
                if norm not in entity_groups:
                    entity_groups[norm] = []
                entity_groups[norm].append(entity)

    # Count occurrences of normalized entities
    entity_counter = Counter()
    for norm_entity, originals in entity_groups.items():
        entity_counter[norm_entity] = len(originals)

    # Entities mentioned in at least min_cluster_size emails are candidates for topics
    common_entities = {entity: count for entity, count in entity_counter.items()
                      if count >= min_cluster_size}

    # Step 3: Classify emails by topic category
    topic_classifications = []
    for text in texts:
        # Limit text length for classification
        result = topic_classifier(text[:512], candidate_labels=TOPIC_CATEGORIES)
        topic_classifications.append({
            'category': result['labels'][0],
            'score': result['scores'][0]
        })

    # Step 4: Group emails by common entity + topic category
    topics = []
    topic_assignments = [-1] * len(emails)  # -1 means "no specific topic"

    for norm_entity, count in common_entities.items():
        # Find all emails mentioning this normalized entity
        entity_emails = []
        for idx, entities in enumerate(all_entities):
            # Check if any entity in this email normalizes to our target
            matched = False
            for entity in entities:
                if normalize_entity(entity) == norm_entity:
                    entity_emails.append(idx)
                    matched = True
                    break

            # Fallback: also check if the normalized entity appears anywhere in text (case insensitive)
            # This catches typos like "oresident Raymond" or different capitalizations
            if not matched:
                text_lower = texts[idx].lower()
                norm_entity_lower = norm_entity.lower()
                # Check each word of the entity
                entity_words = norm_entity_lower.split()
                if all(word in text_lower for word in entity_words):
                    entity_emails.append(idx)

        if len(entity_emails) >= min_cluster_size:
            # Determine the dominant topic category for this cluster
            cluster_categories = [topic_classifications[idx]['category'] for idx in entity_emails]
            dominant_category = Counter(cluster_categories).most_common(1)[0][0]

            # Create topic name
            topic_name = f"{entity} - {dominant_category}"

            topics.append({
                'name': topic_name,
                'entity': entity,
                'category': dominant_category,
                'emails': entity_emails,
                'size': len(entity_emails)
            })

            # Assign topic index to these emails
            topic_idx = len(topics) - 1
            for email_idx in entity_emails:
                topic_assignments[email_idx] = topic_idx

    return {
        'topics': topics,
        'topic_assignments': topic_assignments
    }

def generate_sheet_name(topic, date_str):
    """
    Generate a clean sheet name for a topic

    Args:
        topic: dict with 'entity' and 'category' keys
        date_str: date string like "Jan 2026"

    Returns:
        str: Sheet name like "President Raymond - Jan 2026"
    """
    # Use entity as primary identifier
    entity = topic['entity']

    # Keep it short (Google Sheets has 100 char limit)
    sheet_name = f"{entity} - {date_str}"

    # Truncate if too long
    if len(sheet_name) > 50:
        sheet_name = sheet_name[:47] + "..."

    return sheet_name

# --- TEST ZONE ---
if __name__ == "__main__":
    import json

    print("\n" + "="*80)
    print("TOPIC DETECTION TEST")
    print("="*80)

    # Load test emails
    with open('test_emails.json', 'r') as f:
        emails = json.load(f)

    print(f"\nAnalyzing {len(emails)} emails for topics...")

    # Detect topics (using threshold of 4 for testing)
    result = detect_major_topics(emails, min_cluster_size=4)

    print(f"\n{'='*80}")
    print(f"FOUND {len(result['topics'])} MAJOR TOPICS")
    print(f"{'='*80}\n")

    for i, topic in enumerate(result['topics'], 1):
        print(f"Topic {i}: {topic['name']}")
        print(f"  Entity: {topic['entity']}")
        print(f"  Category: {topic['category']}")
        print(f"  Size: {topic['size']} emails")
        print(f"  Email indices: {topic['emails']}")

        # Show sample emails
        print(f"\n  Sample emails:")
        for idx in topic['emails'][:2]:
            email = emails[idx]
            print(f"    - {email['Subject'] or '(no subject)'}: {email['Body'][:100]}...")
        print()

    # Show topic assignments
    print(f"{'='*80}")
    print("TOPIC ASSIGNMENTS")
    print(f"{'='*80}\n")
    for idx, topic_idx in enumerate(result['topic_assignments']):
        email = emails[idx]
        if topic_idx >= 0:
            topic_name = result['topics'][topic_idx]['name']
            print(f"Email {idx+1}: {email['Subject'] or '(no subject)'} → {topic_name}")
        else:
            print(f"Email {idx+1}: {email['Subject'] or '(no subject)'} → Main feedback sheet")
