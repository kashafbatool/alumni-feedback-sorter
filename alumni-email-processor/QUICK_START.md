# Quick Start Guide

Get up and running in 5 minutes (assuming you have credentials ready).

## 1. Install

```bash
cd alumni-email-processor
npm install
```

## 2. Add Credentials

Place your Google service account JSON file here:
```
credentials/service-account.json
```

## 3. Configure Environment

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
GOOGLE_SHEETS_ID=...
OPENAI_API_KEY=...  # Optional but recommended
```

## 4. Authenticate Gmail

```bash
node src/utils/gmailAuth.js
```

Follow the prompts, then add the refresh token to `.env`

## 5. Share Your Spreadsheet

Share your Google Sheet with:
```
id-project-iam-gserviceaccount@alumni-feedback-sorter.iam.gserviceaccount.com
```

## 6. Test It

```bash
npm run process
```

## 7. Run Continuously

```bash
npm start
```

Done! The system will now process emails every 30 minutes.

---

For detailed setup instructions, see [SETUP_GUIDE.md](./SETUP_GUIDE.md)
