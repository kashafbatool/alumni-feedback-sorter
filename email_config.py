"""
Email Configuration for Weekly Summary

This file contains all configuration settings for the weekly email summary feature.
Update these values as needed.
"""

# Recipient email address for weekly summaries
RECIPIENT_EMAIL = "efratagetachew69@gmail.com"

# Google Sheets URL where alumni feedback data is stored
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1R6H2gC-lazqw0dvlBdAonqinnw7QlKLe_1uFfSqBL08/edit?gid=1043602809#gid=1043602809"

# Sender display name
SENDER_NAME = "Alumni Feedback System"

# Send time configuration
SEND_HOUR = 8  # 8 AM Monday morning
SEND_MINUTE = 0  # At the top of the hour
SEND_DAY = 0  # 0 = Monday (Python's weekday numbering)

# Email subject template
EMAIL_SUBJECT_TEMPLATE = "Weekly Alumni Feedback Summary - {date_range}"

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 60

# Scheduler check interval (in seconds)
SCHEDULER_CHECK_INTERVAL = 3600  # Check every hour
