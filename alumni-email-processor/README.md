# Alumni Email Processor

Automated system to process alumni emails, analyze sentiment, check Raiser's Edge data, and update Google Sheets.

## Features

- **Email Processing**: Reads emails from Gmail inbox using Gmail API
- **Raiser's Edge Integration**: Checks if alumni exist in the database and retrieves staff assignments
- **AI Analysis**: Uses AI to analyze sentiment (positive/negative) and intent (positive, negative, donate, withdrawal)
- **Email Summarization**: Generates concise summaries of each email
- **Google Sheets Integration**: Automatically updates spreadsheet with processed data
- **Automated Scheduling**: Runs on a configurable schedule

## Setup Instructions

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Credentials

#### Gmail API Setup:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials and run the authentication script

#### Google Sheets API Setup:
1. Place your service account JSON file in `credentials/service-account.json`
2. Share your Google Sheet with the service account email: `id-project-iam-gserviceaccount@alumni-feedback-sorter.iam.gserviceaccount.com`

#### Raiser's Edge SKY API:
1. Contact Blackbaud to get SKY API subscription key
2. Add the API key to your `.env` file
3. Note: SFTP credentials cannot be used for REST API access

#### OpenAI API:
1. Get API key from [OpenAI Platform](https://platform.openai.com/)
2. Add to `.env` file

### 3. Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

### 4. Authenticate Gmail

Run the Gmail authentication script to generate a refresh token:

```bash
node src/utils/gmailAuth.js
```

### 5. Run the Processor

**Manual Run:**
```bash
npm run process
```

**Automated Scheduling:**
```bash
npm start
```

## Configuration

Edit `.env` to customize:
- `PROCESS_INTERVAL_MINUTES`: How often to check for new emails (default: 30 minutes)
- `MAX_EMAILS_PER_RUN`: Maximum number of emails to process per run (default: 50)

## Google Sheet Columns

The system updates the following columns:
- **Date**: Email received date
- **Alum Name**: Sender's name
- **Alum Email**: Sender's email address
- **Sentiment**: positive/negative
- **Assigned Staff**: Staff member from Raiser's Edge (if exists)
- **Summary**: AI-generated email summary

## Architecture

```
alumni-email-processor/
├── src/
│   ├── index.js              # Main entry point with scheduler
│   ├── processEmails.js      # Email processing workflow
│   ├── services/
│   │   ├── gmailService.js   # Gmail API integration
│   │   ├── sheetsService.js  # Google Sheets API integration
│   │   ├── raisersEdgeService.js  # Raiser's Edge API integration
│   │   └── aiService.js      # AI sentiment analysis & summarization
│   ├── utils/
│   │   ├── gmailAuth.js      # Gmail OAuth authentication
│   │   ├── logger.js         # Logging utility
│   │   └── config.js         # Configuration loader
│   └── models/
│       └── emailData.js      # Data models
├── credentials/
│   └── service-account.json  # Google service account (not in git)
├── .env                      # Environment variables (not in git)
├── .env.example              # Example environment variables
└── package.json
```

## Important Notes

- The Raiser's Edge SFTP credentials you have are for file transfers only
- You need **Blackbaud SKY API** credentials to query the database
- The system will still work without Raiser's Edge integration (staff assignment will be empty)
- Ensure your Google Sheet is shared with the service account email
- Keep your `.env` file secure and never commit it to version control

## Troubleshooting

1. **Gmail Authentication Issues**: Make sure you've enabled Gmail API in Google Cloud Console
2. **Sheets Access Denied**: Verify the sheet is shared with the service account email
3. **Raiser's Edge Connection**: Ensure you have SKY API credentials, not just SFTP

## Support

For issues or questions, check the logs in the console output.
