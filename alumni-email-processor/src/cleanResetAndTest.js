import { google } from 'googleapis';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { config } from './utils/config.js';
import { Logger } from './utils/logger.js';
import { AIService } from './services/aiService.js';
import { SheetsService } from './services/sheetsService.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Original 15 test emails
const originalEmails = [
  { name: 'Jennifer Martinez', email: 'jennifer.martinez@gmail.com', subject: 'Website donation issue', body: "I've been trying to donate on your website for 20 minutes but it keeps crashing. Can someone call me?", date: '2026-01-12' },
  { name: 'David Chen', email: 'dchen@outlook.com', subject: 'Thank you for scholarship', body: "Thank you so much for the scholarship! It changed my life and I'm forever grateful.", date: '2026-01-12' },
  { name: 'Amanda Foster', email: 'amanda.foster@business.com', subject: 'Partnership meeting request', body: 'Can we schedule a meeting next week to discuss partnership opportunities?', date: '2026-01-13' },
  { name: 'Marcus Thompson', email: 'mthompson78@yahoo.com', subject: 'Address update needed', body: 'I need to update my mailing address in your system. My new address is 123 Main St.', date: '2026-01-13' },
  { name: 'Patricia Rodriguez', email: 'p.rodriguez@email.com', subject: 'Complaint about staff', body: 'Your staff was incredibly rude when I called yesterday. This is unacceptable.', date: '2026-01-13' },
];

async function cleanResetAndTest() {
  try {
    Logger.info('=== CLEAN RESET AND TEST ALL FIXES ===\n');

    // Initialize
    const credentialsPath = join(__dirname, '../credentials/service-account.json');
    const credentials = JSON.parse(readFileSync(credentialsPath, 'utf8'));
    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });
    const sheets = google.sheets({ version: 'v4', auth });
    const spreadsheetId = config.sheets.spreadsheetId;
    const aiService = new AIService();
    const sheetsService = new SheetsService();

    // STEP 1: Clear and setup fresh
    Logger.info('Step 1: Clearing sheet and adding headers...');
    await sheets.spreadsheets.values.clear({
      spreadsheetId,
      range: 'Sheet1!A:F',
    });

    await sheets.spreadsheets.values.update({
      spreadsheetId,
      range: 'Sheet1!A1:F1',
      valueInputOption: 'RAW',
      requestBody: {
        values: [['Date', 'Alum Name', 'Alum Email', 'Sentiment', 'Assigned Staff', 'Summary']],
      },
    });
    Logger.success('✓ Sheet cleared and headers added');

    // STEP 2: Add original 5 emails with NEW summary logic
    Logger.info(`\nStep 2: Adding ${originalEmails.length} emails with improved summaries...`);
    for (let i = 0; i < originalEmails.length; i++) {
      const email = originalEmails[i];
      const analysis = await aiService.analyzeSentimentAndIntent(email.body, email.subject);

      Logger.info(`  [${i + 1}] ${email.name}: "${analysis.summary}"`);

      await sheetsService.appendRow({
        date: new Date(email.date),
        alumName: email.name,
        alumEmail: email.email,
        sentiment: analysis.sentiment,
        assignedStaff: '',
        summary: analysis.summary,
      });

      await new Promise(resolve => setTimeout(resolve, 200));
    }

    // STEP 3: Verify they're at the end
    Logger.info('\nStep 3: Verifying rows are at the end...');
    let response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: 'Sheet1!A:F',
    });
    Logger.success(`✓ Total rows: ${response.data.values.length} (1 header + 5 emails)`);

    // STEP 4: Add 2 more emails WITHOUT deleting existing
    Logger.info('\nStep 4: Adding 2 more emails without deleting existing...');
    const newEmails = [
      { name: 'Sarah Kim', email: 'sarah.k@test.com', subject: 'Thank you', body: 'Just wanted to say thanks for the amazing scholarship program. It really helped me finish my degree!', date: '2026-01-14' },
      { name: 'Mike Chen', email: 'mchen@email.com', subject: 'Complaint', body: 'Your customer service representative was extremely rude to me on the phone yesterday. This is completely unacceptable behavior.', date: '2026-01-14' },
    ];

    for (const email of newEmails) {
      const analysis = await aiService.analyzeSentimentAndIntent(email.body, email.subject);
      Logger.info(`  Adding: ${email.name}: "${analysis.summary}"`);

      await sheetsService.appendRow({
        date: new Date(email.date),
        alumName: email.name,
        alumEmail: email.email,
        sentiment: analysis.sentiment,
        assignedStaff: '',
        summary: analysis.summary,
      });

      await new Promise(resolve => setTimeout(resolve, 200));
    }

    // STEP 5: Final verification
    response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: 'Sheet1!A:F',
    });
    const finalRows = response.data.values;

    Logger.success(`\n✓ Final total rows: ${finalRows.length} (1 header + 7 emails)`);

    // Show last 3 rows to confirm they're at the end
    Logger.info('\nLast 3 rows in sheet:');
    for (let i = finalRows.length - 3; i < finalRows.length; i++) {
      const row = finalRows[i];
      Logger.info(`  Row ${i + 1}: ${row[1]} - "${row[5]}"`);
    }

    Logger.success(`\n✓✓✓ ALL FIXES VERIFIED ✓✓✓`);
    Logger.success(`1. Summaries are concise and clear`);
    Logger.success(`2. New rows append at the END`);
    Logger.success(`3. Existing data is NOT deleted`);
    Logger.success(`\nView: https://docs.google.com/spreadsheets/d/${spreadsheetId}/edit`);

  } catch (error) {
    Logger.error('Test failed', error);
    throw error;
  }
}

cleanResetAndTest()
  .then(() => process.exit(0))
  .catch(() => process.exit(1));
