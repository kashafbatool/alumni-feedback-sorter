import { SheetsService } from './services/sheetsService.js';
import { AIService } from './services/aiService.js';
import { Logger } from './utils/logger.js';
import { google } from 'googleapis';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { config } from './utils/config.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const testEmails = [
  { name: 'Alice Test', email: 'alice@test.com', subject: 'Thank you', body: 'Thank you for the scholarship!', date: '2026-01-13' },
  { name: 'Bob Test', email: 'bob@test.com', subject: 'Complaint', body: 'Your service was terrible and rude.', date: '2026-01-13' },
  { name: 'Carol Test', email: 'carol@test.com', subject: 'Donation', body: 'I want to donate $500 monthly.', date: '2026-01-13' },
];

async function test3Emails() {
  try {
    Logger.info('=== TESTING 3 EMAILS WITH DEBUG ===\n');

    // Initialize
    const credentialsPath = join(__dirname, '../credentials/service-account.json');
    const credentials = JSON.parse(readFileSync(credentialsPath, 'utf8'));
    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });
    const sheets = google.sheets({ version: 'v4', auth });
    const spreadsheetId = config.sheets.spreadsheetId;

    // Clear sheet
    Logger.info('Step 1: Clearing sheet...');
    await sheets.spreadsheets.values.clear({
      spreadsheetId,
      range: 'Sheet1!A:F',
    });

    // Add headers
    Logger.info('Step 2: Adding headers...');
    await sheets.spreadsheets.values.update({
      spreadsheetId,
      range: 'Sheet1!A1:F1',
      valueInputOption: 'RAW',
      requestBody: {
        values: [['Date', 'Alum Name', 'Alum Email', 'Sentiment', 'Assigned Staff', 'Summary']],
      },
    });

    Logger.success('✓ Headers added\n');

    // Initialize services
    const sheetsService = new SheetsService();
    const aiService = new AIService();
    await sheetsService.initialize();

    // Process emails
    for (let i = 0; i < testEmails.length; i++) {
      const email = testEmails[i];

      Logger.info(`\nProcessing email ${i + 1}:`);
      Logger.info(`  From: ${email.name} <${email.email}>`);
      Logger.info(`  Subject: ${email.subject}`);
      Logger.info(`  Body: ${email.body}`);

      // Analyze
      const analysis = await aiService.analyzeSentimentAndIntent(email.body, email.subject);

      Logger.info(`  Analysis result:`);
      Logger.info(`    Sentiment: ${analysis.sentiment}`);
      Logger.info(`    Intent: ${analysis.intent}`);
      Logger.info(`    Summary: "${analysis.summary}"`);

      // Prepare data object
      const dataToWrite = {
        date: new Date(email.date),
        alumName: email.name,
        alumEmail: email.email,
        sentiment: analysis.sentiment,
        assignedStaff: '',
        summary: analysis.summary,
      };

      Logger.info(`  Data object to write:`);
      Logger.info(`    date: ${dataToWrite.date.toISOString().split('T')[0]}`);
      Logger.info(`    alumName: ${dataToWrite.alumName}`);
      Logger.info(`    alumEmail: ${dataToWrite.alumEmail}`);
      Logger.info(`    sentiment: ${dataToWrite.sentiment}`);
      Logger.info(`    assignedStaff: ${dataToWrite.assignedStaff}`);
      Logger.info(`    summary: ${dataToWrite.summary}`);

      // Write to sheet
      await sheetsService.appendRow(dataToWrite);

      Logger.success(`✓ Row added`);
    }

    // Verify
    Logger.info('\n=== VERIFICATION ===');
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: 'Sheet1!A:F',
    });

    const rows = response.data.values || [];
    Logger.info(`\nTotal rows: ${rows.length}`);

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      Logger.info(`\nRow ${i + 1}:`);
      Logger.info(`  A (Date): ${row[0] || '(empty)'}`);
      Logger.info(`  B (Name): ${row[1] || '(empty)'}`);
      Logger.info(`  C (Email): ${row[2] || '(empty)'}`);
      Logger.info(`  D (Sentiment): ${row[3] || '(empty)'}`);
      Logger.info(`  E (Staff): ${row[4] || '(empty)'}`);
      Logger.info(`  F (Summary): ${row[5] || '(empty)'}`);
    }

    Logger.success(`\n✓✓✓ TEST COMPLETE`);
    Logger.success(`View: https://docs.google.com/spreadsheets/d/${spreadsheetId}/edit`);

  } catch (error) {
    Logger.error('Test failed', error);
    throw error;
  }
}

test3Emails()
  .then(() => process.exit(0))
  .catch(() => process.exit(1));
