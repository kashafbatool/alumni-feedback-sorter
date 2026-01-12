# Setup Guide - Alumni Email Processor

Follow these steps to set up and run the automated email processing system.

## Prerequisites

- Node.js 18+ installed
- Gmail account with API access
- Google Service Account with Sheets API access
- (Optional) Blackbaud Raiser's Edge SKY API subscription key
- (Optional) OpenAI API key for AI-powered analysis

## Step 1: Install Dependencies

```bash
cd alumni-email-processor
npm install
```

## Step 2: Gmail API Setup

### 2.1 Create OAuth 2.0 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **Gmail API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Name it (e.g., "Alumni Email Processor")
   - Download the credentials

### 2.2 Configure OAuth Credentials

From the downloaded credentials file, extract:
- `client_id` → Add to `.env` as `GMAIL_CLIENT_ID`
- `client_secret` → Add to `.env` as `GMAIL_CLIENT_SECRET`

### 2.3 Authenticate and Get Refresh Token

```bash
node src/utils/gmailAuth.js
```

This will:
1. Open a URL in your console
2. You visit the URL and authorize the app
3. Copy the authorization code from the redirect URL
4. Paste it into the console
5. You'll receive a refresh token to add to your `.env` file

## Step 3: Google Sheets Setup

### 3.1 Get Service Account Credentials

1. In Google Cloud Console, go to "IAM & Admin" > "Service Accounts"
2. Find your service account: `id-project-iam-gserviceaccount@alumni-feedback-sorter.iam.gserviceaccount.com`
3. Click on it, go to "Keys" tab
4. Create a new JSON key
5. Download and save as `credentials/service-account.json`

### 3.2 Share Your Spreadsheet

1. Open your Google Spreadsheet
2. Click "Share" button
3. Add the service account email with "Editor" permissions:
   ```
   id-project-iam-gserviceaccount@alumni-feedback-sorter.iam.gserviceaccount.com
   ```

### 3.3 Get Spreadsheet ID

From your Google Sheets URL:
```
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit
```

Copy the `SPREADSHEET_ID_HERE` part and add to `.env` as `GOOGLE_SHEETS_ID`

## Step 4: Raiser's Edge SKY API (Optional)

To enable staff assignment lookups:

1. Contact Blackbaud to get SKY API access
2. Request a **subscription key** for the SKY API
3. Add the subscription key to `.env` as `RAISERS_EDGE_API_KEY`

**Note:** The SFTP credentials you have are NOT for the REST API. You need a separate SKY API subscription.

### If You Don't Have SKY API Access

The system will still work! The "Assigned Staff" column will just be empty.

## Step 5: AI Configuration (Optional but Recommended)

For better sentiment analysis and email summarization:

### Option A: OpenAI (Recommended)

1. Get an API key from [OpenAI Platform](https://platform.openai.com/)
2. Add to `.env` as `OPENAI_API_KEY`

### Option B: Fallback (No API Key)

If you don't provide an AI API key, the system will use simple keyword-based analysis. It works, but won't be as accurate.

## Step 6: Create .env File

Copy the example and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` and add all your credentials. Minimum required:

```env
# Gmail
GMAIL_CLIENT_ID=your_client_id_here
GMAIL_CLIENT_SECRET=your_client_secret_here
GMAIL_REFRESH_TOKEN=your_refresh_token_here

# Google Sheets
GOOGLE_SHEETS_ID=your_spreadsheet_id_here
GOOGLE_SERVICE_ACCOUNT_EMAIL=id-project-iam-gserviceaccount@alumni-feedback-sorter.iam.gserviceaccount.com

# Optional but recommended
OPENAI_API_KEY=your_openai_api_key_here

# Optional - for staff assignments
RAISERS_EDGE_API_KEY=your_sky_api_key_here
RAISERS_EDGE_TENANT_ID=14aedc04-bf45-43bf-8f7c-b08199425776
```

## Step 7: Test the System

Run a one-time processing:

```bash
npm run process
```

This will:
1. Fetch unread emails from Gmail
2. Check Raiser's Edge for constituent data (if configured)
3. Analyze sentiment and intent
4. Generate summaries
5. Add data to Google Sheets
6. Mark emails as read

## Step 8: Run with Scheduler

For automated processing every 30 minutes:

```bash
npm start
```

The system will:
- Process emails immediately on startup
- Then run every 30 minutes (configurable in `.env`)
- Keep running until you press Ctrl+C

## Configuration Options

Edit `.env` to customize:

```env
# How often to check for new emails (in minutes)
PROCESS_INTERVAL_MINUTES=30

# Maximum emails to process per run
MAX_EMAILS_PER_RUN=50

# Which email address to monitor (if you want to filter)
ALUMNI_EMAIL_ADDRESS=alumni@yourdomain.com
```

## Troubleshooting

### Gmail Authentication Issues

- Make sure Gmail API is enabled in Google Cloud Console
- Check that you're using the correct client_id and client_secret
- Try regenerating the refresh token with `node src/utils/gmailAuth.js`

### Google Sheets Access Denied

- Verify the sheet is shared with the service account email
- Check that `service-account.json` is in the `credentials/` folder
- Ensure the service account has "Editor" permissions

### Raiser's Edge Connection Fails

- You need SKY API credentials, not SFTP credentials
- Contact Blackbaud support to get API access
- The system works without it (staff assignment will be empty)

### AI Analysis Not Working

- Check that your OpenAI API key is valid
- Verify you have credits/billing set up
- The system will fall back to keyword analysis if AI fails

## What Happens When Processing

For each unread email:

1. Extract sender name and email address
2. Check if already processed (avoid duplicates)
3. Look up constituent in Raiser's Edge (if configured)
4. Get assigned staff member (if exists)
5. Analyze email with AI:
   - Sentiment: positive or negative
   - Intent: positive_intent, negative_intent, donate_intent, or withdrawal_intent
   - Summary: 2-3 sentence summary
6. Add row to Google Sheets with:
   - Date received
   - Alumni name
   - Alumni email
   - Sentiment
   - Assigned staff (or empty)
   - Summary
7. Mark email as read

## Security Notes

- Never commit `.env` or `credentials/` to git
- Keep your API keys secure
- The service account should only have access to the specific spreadsheet
- Consider using a dedicated Gmail account for this automation

## Support

If you encounter issues:
1. Check the console logs for error messages
2. Verify all API credentials are correct
3. Test each service independently
4. Ensure all APIs are enabled in Google Cloud Console

## Next Steps

Once everything is working:
- Set up the system to run as a background service
- Monitor the logs regularly
- Adjust the processing interval as needed
- Consider adding email notifications for errors
- Set up alerts for donation intent emails

Good luck!
