# Google Sheets Integration Setup Guide

This guide will help you automatically upload your analyzed alumni feedback to Google Sheets using Python.

## Quick Overview

1. Install Python packages
2. Create Google Service Account
3. Download credentials JSON file
4. Share your Google Sheet with the service account
5. Run the uploader script

---

## Step 1: Install Required Packages

```bash
pip3 install gspread google-auth google-auth-oauthlib google-auth-httplib2
```

---

## Step 2: Create Google Service Account

### 2.1 Go to Google Cloud Console

Visit: https://console.cloud.google.com/

### 2.2 Create or Select a Project

- Click on the project dropdown at the top
- Create a new project or select your existing "Alumni Feedback Sorter" project

### 2.3 Enable Google Sheets API

1. In the left sidebar, go to **"APIs & Services"** > **"Library"**
2. Search for **"Google Sheets API"**
3. Click on it and press **"Enable"**

### 2.4 Create Service Account

1. Go to **"IAM & Admin"** > **"Service Accounts"**
2. Click **"Create Service Account"**
3. Fill in details:
   - **Name**: `alumni-feedback-uploader`
   - **Description**: `Service account for uploading alumni feedback to Google Sheets`
4. Click **"Create and Continue"**
5. Skip the optional permissions (click "Continue")
6. Click **"Done"**

### 2.5 Create and Download JSON Key

1. Find your newly created service account in the list
2. Click on it
3. Go to the **"Keys"** tab
4. Click **"Add Key"** > **"Create new key"**
5. Choose **"JSON"** format
6. Click **"Create"**
7. The JSON file will download automatically

### 2.6 Save the Credentials File

1. Create a folder called `credentials` in your project:
   ```bash
   mkdir credentials
   ```

2. Move the downloaded JSON file to `credentials/service-account.json`:
   ```bash
   mv ~/Downloads/alumni-feedback-sorter-*.json credentials/service-account.json
   ```

---

## Step 3: Get Your Service Account Email

Run this command to see your service account email:

```bash
python3 sheets_uploader.py --show-email
```

You'll see something like:
```
alumni-feedback-uploader@alumni-feedback-sorter-123456.iam.gserviceaccount.com
```

Copy this email address - you'll need it in the next step.

---

## Step 4: Share Your Google Sheet

1. Open your Google Spreadsheet in your browser
2. Click the **"Share"** button (top right)
3. Paste the service account email address
4. Make sure the permission is set to **"Editor"**
5. **Uncheck** "Notify people" (it's a bot, not a person)
6. Click **"Share"** or **"Send"**

Your Google Sheet is now accessible to the Python script!

---

## Step 5: Upload Your Data

### First, generate the analyzed report:

```bash
python3 data_processor_with_filter.py
```

This creates `Alumni_Feedback_Report_Filtered.xlsx`

### Then, upload to Google Sheets:

```bash
python3 sheets_uploader.py "YOUR_GOOGLE_SHEET_URL"
```

Replace `YOUR_GOOGLE_SHEET_URL` with your actual Google Sheets URL (the one you see in your browser).

**Example:**
```bash
python3 sheets_uploader.py "https://docs.google.com/spreadsheets/d/1ABCxyz123.../edit"
```

### If you want to upload to a specific worksheet tab:

```bash
python3 sheets_uploader.py "YOUR_GOOGLE_SHEET_URL" "Sheet2"
```

---

## What Happens When You Run the Uploader?

1. ✅ Loads your analyzed Excel file (`Alumni_Feedback_Report_Filtered.xlsx`)
2. ✅ Authenticates with Google using the service account
3. ✅ Opens your Google Spreadsheet
4. ✅ Clears existing content (optional)
5. ✅ Uploads all rows and columns
6. ✅ Formats the header row (bold, gray background)
7. ✅ Freezes the header row

The spreadsheet will contain all 14 columns:
- First Name
- Last Name
- Email Address
- Positive or Negative?
- Received By
- Date Received
- Received by Email, Phone, or in Person?
- Email Text/Synopsis of Conversation/Notes
- Paused Giving OR Changed bequest intent?
- Constituent?
- RM or team member assigned for Response
- Response Complete?
- Date of Response
- Imported in RE? (Grace will update this column)

---

## Complete Workflow

```bash
# 1. Process emails (with filtering and sentiment analysis)
python3 data_processor_with_filter.py

# 2. Upload results to Google Sheets
python3 sheets_uploader.py "https://docs.google.com/spreadsheets/d/YOUR_ID/edit"
```

---

## Troubleshooting

### Error: "Spreadsheet not found"
- Make sure you shared the sheet with the service account email
- Check that you're using the correct spreadsheet URL

### Error: "credentials/service-account.json not found"
- Make sure you created the `credentials` folder
- Check that the JSON file is named exactly `service-account.json`

### Error: "Worksheet 'Sheet1' not found"
- Your sheet tab might have a different name
- Specify the correct tab name: `python3 sheets_uploader.py "URL" "YourTabName"`

### Error: "Permission denied"
- Make sure the service account has "Editor" permissions on the sheet
- Re-share the sheet if needed

---

## Security Notes

⚠️ **IMPORTANT:**

1. **Never commit** `credentials/service-account.json` to Git
2. The `.gitignore` file already excludes `credentials/` folder
3. Keep your service account JSON file secure
4. Only share your Google Sheet with this specific service account (not publicly)

---

## Next Steps

Once everything is working:

1. Run the processor + uploader whenever you receive new alumni emails
2. Your team can view real-time updates in the Google Sheet
3. Consider automating this with a scheduled task (cron job)

---

## Questions?

If you encounter issues:
1. Check that Google Sheets API is enabled in Cloud Console
2. Verify the service account email has access to your sheet
3. Make sure all Python packages are installed
4. Check the console output for specific error messages

Good luck! 🚀
