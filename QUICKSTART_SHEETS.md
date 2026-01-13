# Quick Start: Upload to Google Sheets

Follow these 5 simple steps to get your alumni feedback automatically uploaded to Google Sheets.

## Step 1: Install Python Package

```bash
pip3 install gspread google-auth
```

## Step 2: Create Google Service Account

1. Go to: https://console.cloud.google.com/
2. Create a new project (or use existing)
3. Enable **Google Sheets API**
4. Create a **Service Account**
5. Download the JSON key file
6. Save it as `credentials/service-account.json`

**Detailed instructions:** See [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)

## Step 3: Get Service Account Email

```bash
python3 sheets_uploader.py --show-email
```

Copy the email that's displayed (looks like `something@project-name.iam.gserviceaccount.com`)

## Step 4: Share Your Google Sheet

1. Open your Google Sheet
2. Click **Share**
3. Paste the service account email
4. Set permission to **Editor**
5. Click **Share**

## Step 5: Run the Uploader

### Option A: One-step command (process + upload)

```bash
./process_and_upload.sh "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
```

This will:
1. Process and analyze all emails
2. Upload results to Google Sheets

### Option B: Two separate commands

```bash
# 1. Process emails
python3 data_processor_with_filter.py

# 2. Upload to Google Sheets
python3 sheets_uploader.py "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
```

## Done! 🎉

Your analyzed alumni feedback is now in Google Sheets and ready for your team to review.

---

## Troubleshooting

**"Spreadsheet not found"**
→ Make sure you shared the sheet with the service account email

**"credentials/service-account.json not found"**
→ Create the `credentials` folder and put your JSON file there

**"Module not found: gspread"**
→ Run: `pip3 install gspread google-auth`

---

For detailed setup instructions, see: [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)
