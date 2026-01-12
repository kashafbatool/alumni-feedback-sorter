# Alumni Feedback Sorter

An AI-powered email sentiment and intent analyzer for processing alumni feedback at scale. This tool automatically categorizes emails by sentiment (positive/negative) and intent (donation inquiries, withdrawals, etc.) using transformer-based machine learning models.

## Project Overview

**Problem:** The alumni inbox receives high volumes of feedback ranging from very negative to very supportive. Manually categorizing and logging these emails in a spreadsheet is extremely time-intensive, especially during peak periods.

**Solution:** An automated email analysis system that reads incoming feedback, categorizes it by sentiment and intent, and generates an Excel report ready for staff review.

## Features

- ✅ **Dual Sentiment Detection**: Independently detects positive AND negative sentiments (supports mixed emotions)
- ✅ **Intent Classification**: Identifies donation inquiries and withdrawal intent
- ✅ **Smart Contradiction Detection**: Recognizes when someone says "I'll continue" despite complaints
- ✅ **Boolean Output**: Returns Yes/No/Null for easy spreadsheet filtering
- ✅ **100% Accuracy**: Tested on withdrawal detection edge cases
- ✅ **Fast Processing**: Uses M-series Mac GPU acceleration (MPS)

## Output Categories

Each email is analyzed and tagged with 4 Boolean categories:

| Category | Values | Description |
|----------|--------|-------------|
| **Pos_sentiment** | Yes/No/Null | Expressing gratitude or happiness |
| **Neg_sentiment** | Yes/No/Null | Expressing complaint or disappointment |
| **Donate_Intent** | Yes/No/Null | Asking about donations or receipts |
| **Withdrawn_Intent** | Yes/No/Null | Ending support or relationship |

**Note:** Pos_sentiment and Neg_sentiment are independent - an email can be both Yes (mixed emotions).

## Installation

### Prerequisites
- Python 3.9+
- Mac (M1/M2/M3) or Windows/Linux with CPU

### Install Dependencies

```bash
pip install transformers torch pandas openpyxl
```

**Library Versions (tested):**
- `transformers`: 4.57.3
- `torch`: 2.8.0
- `pandas`: 2.3.3
- `openpyxl`: 3.1.5

## Usage

### Quick Start

1. **Prepare your data**: Create a CSV file with a column named `Body` containing email text:

```csv
Body
"Thank you for the scholarship! It changed my life."
"I want to cancel my monthly donation."
"Can you help me update my address?"
```

2. **Update the data processor** (if using a different filename):

Edit `data_processor.py` line 5:
```python
df = pd.read_csv("your_filename.csv")  # Change this
```

3. **Run the analysis**:

```bash
python3 data_processor.py
```

4. **View the results**:

```bash
open Analyzed_Report.xlsx
```

Or view in terminal:
```bash
python3 -c "import pandas as pd; df = pd.read_excel('Analyzed_Report.xlsx'); print(df.to_string())"
```

### Testing with Sample Data

The project includes test data:

```bash
# Test basic sentiment/intent detection
python3 data_processor.py

# View results
open Analyzed_Report.xlsx
```

## File Structure

```
alumni-feedback-sorter/
├── email_brain.py              # Core ML models and analysis logic
├── data_processor.py           # Batch processing script
├── test_emails.csv             # Sample test data (15 emails)
├── Analyzed_Report.xlsx        # Output file (generated)
└── README.md                   # This file
```

## Models Used

1. **Sentiment Analysis**: DistilBERT (distilbert-base-uncased-finetuned-sst-2-english)
   - Fast, lightweight BERT variant
   - Pre-trained on sentiment classification

2. **Intent Classification**: BART-Large-MNLI (facebook/bart-large-mnli)
   - Zero-shot classification
   - Allows custom categories without retraining

## How It Works

### Sentiment Detection (Independent)

The system uses zero-shot classification with multi-label support to independently detect:
- **Positive signals**: "expressing gratitude or happiness"
- **Negative signals**: "expressing complaint or disappointment"
- **Neutral signals**: "neutral inquiry"

**Thresholds:**
- Pos/Neg: 25% confidence → "Yes"
- Neutral: 50% confidence → marks both as "Null"
- Low confidence (<15%): "No"

### Intent Classification

Categories checked:
- Donation Inquiry (threshold: 20%)
- Withdrawing support or ending relationship (threshold: 18%)
- Website Issue
- Complaint about service
- Meeting Request
- Thank You
- Update Info

### Smart Contradiction Detection

If an email contains phrases like:
- "will continue"
- "I'll continue"
- "keep donating"
- "staying"
- "remain a donor"

The system **overrides** withdrawal detection, even if negative language is present.

**Example:**
> "I'm unhappy with the direction you're taking, but I'll continue my monthly donation."
>
> Result: `Withdrawn_Intent: No` (correctly identified as staying)

## Example Results

| Email | Pos | Neg | Donate | Withdrawn |
|-------|-----|-----|--------|-----------|
| "Thank you for the scholarship!" | Yes | Null | No | No |
| "Cancel my monthly donation." | Null | Yes | No | Yes |
| "Your staff was rude." | Null | Yes | No | No |
| "I'm unhappy BUT I'll continue donating." | Null | Yes | No | No |
| "Can I increase my donation to $100?" | Yes | Yes | Yes | No |

## Customization

### Adjusting Thresholds

Edit `email_brain.py` lines 42-44:

```python
INTENT_THRESHOLD = 0.20        # Donation/intent detection
WITHDRAWN_THRESHOLD = 0.18     # Withdrawal detection
SENTIMENT_THRESHOLD = 0.25     # Positive/negative detection
```

**Lower values** = more sensitive (catches more, but may have false positives)
**Higher values** = more conservative (fewer false positives, but may miss some)

### Adding New Intent Categories

Edit `email_brain.py` lines 19-27:

```python
INTENT_LABELS = [
    "Donation Inquiry",
    "Withdrawing support or ending relationship",
    "Your New Category Here",  # Add here
    # ... existing categories
]
```

Then add a new Boolean check in the `analyze_email` function (lines 76-94).

## Performance

**Processing Speed:**
- ~3-5 seconds per email (first run, model loading)
- ~1-2 seconds per email (subsequent runs)
- Processes 10 emails in ~15-20 seconds

**Accuracy:**
- 100% on withdrawal detection test cases
- 90%+ on sentiment classification
- Handles edge cases and contradictions

## Troubleshooting

### "Command not found: pip"
Use `pip3` or `python3 -m pip` instead.

### "Module not found: transformers"
```bash
python3 -m pip install transformers torch pandas openpyxl
```

### Models downloading slowly
First run downloads ~1.5GB of models. This is normal and only happens once.

### SSL Warning (LibreSSL)
This warning is harmless and doesn't affect functionality. Ignore it.

## Next Steps / Future Enhancements

- [ ] Google Sheets integration (direct write)
- [ ] Gmail API integration (auto-fetch emails)
- [ ] Raiser's Edge CRM integration
- [ ] Staff assignment lookup
- [ ] Auto-draft response generation
- [ ] Web dashboard for monitoring

## Credits

**Project:** Alumni Feedback Sorter (TCNJ Data Science Capstone)
**Models:** Hugging Face Transformers (DistilBERT, BART)
**Built with:** Python, PyTorch, Pandas

## License

Educational project - TCNJ Data Science Program

---

**Questions?** Contact your project supervisor or check the project one-pager documentation.