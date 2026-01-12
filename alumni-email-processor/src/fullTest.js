import { google } from 'googleapis';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { config } from './utils/config.js';
import { Logger } from './utils/logger.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Mock email data
const mockEmails = [
  {
    date: '2026-01-10',
    name: 'John Smith',
    email: 'john.smith@alumni.example.com',
    sentiment: 'positive',
    staff: '',
    summary: 'Thank you for the wonderful reunion event! Grateful for reconnecting with classmates.',
  },
  {
    date: '2026-01-11',
    name: 'Sarah Johnson',
    email: 'sarah.johnson@gmail.com',
    sentiment: 'positive',
    staff: '',
    summary: 'Interested in making a donation to the scholarship fund, especially for CS department.',
  },
  {
    date: '2026-01-11',
    name: 'Mike Brown',
    email: 'mike.brown@yahoo.com',
    sentiment: 'negative',
    staff: '',
    summary: 'Complaint about repeated fundraising calls despite requesting to be removed from list.',
  },
  {
    date: '2026-01-12',
    name: 'Emily Davis',
    email: 'emily.davis@outlook.com',
    sentiment: 'positive',
    staff: '',
    summary: 'Requests to unsubscribe from all alumni emails and mailings.',
  },
  {
    date: '2026-01-12',
    name: 'Robert Wilson',
    email: 'robert.wilson@alumni.edu',
    sentiment: 'positive',
    staff: '',
    summary: 'Career update: promoted to Senior Director, interested in mentoring current students.',
  },
];

async function fullTest() {
  try {
    Logger.info('=== Full Test with Direct Google Sheets API ===');

    // Initialize Google Sheets
    const credentialsPath = join(__dirname, '../credentials/service-account.json');
    const credentials = JSON.parse(readFileSync(credentialsPath, 'utf8'));

    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });

    const sheets = google.sheets({ version: 'v4', auth });
    const spreadsheetId = config.sheets.spreadsheetId;

    // Step 1: Clear everything
    Logger.info('Step 1: Clearing sheet...');
    await sheets.spreadsheets.values.clear({
      spreadsheetId,
      range: 'Sheet1!A:F',
    });
    Logger.success('Sheet cleared');

    // Step 2: Add headers
    Logger.info('Step 2: Adding headers...');
    await sheets.spreadsheets.values.update({
      spreadsheetId,
      range: 'Sheet1!A1:F1',
      valueInputOption: 'RAW',
      requestBody: {
        values: [['Date', 'Alum Name', 'Alum Email', 'Sentiment', 'Assigned Staff', 'Summary']],
      },
    });
    Logger.success('Headers added');

    // Step 3: Add all data rows at once
    Logger.info('Step 3: Adding all 5 email rows...');
    const dataRows = mockEmails.map(email => [
      email.date,
      email.name,
      email.email,
      email.sentiment,
      email.staff,
      email.summary,
    ]);

    await sheets.spreadsheets.values.append({
      spreadsheetId,
      range: 'Sheet1!A2:F',
      valueInputOption: 'RAW',
      requestBody: {
        values: dataRows,
      },
    });
    Logger.success(`Added ${dataRows.length} rows`);

    // Step 4: Verify
    Logger.info('Step 4: Verifying data...');
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: 'Sheet1!A:F',
    });

    const rows = response.data.values || [];
    Logger.success(`Verification: Found ${rows.length} total rows (including header)`);

    rows.forEach((row, index) => {
      console.log(`Row ${index + 1}:`, row);
    });

    Logger.success(`\n✓ Test complete! Check your sheet:\nhttps://docs.google.com/spreadsheets/d/${spreadsheetId}/edit`);

  } catch (error) {
    Logger.error('Test failed', error);
    throw error;
  }
}

fullTest()
  .then(() => {
    process.exit(0);
  })
  .catch((error) => {
    process.exit(1);
  });
