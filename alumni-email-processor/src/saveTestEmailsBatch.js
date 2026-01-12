import { google } from 'googleapis';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { config } from './utils/config.js';
import { Logger } from './utils/logger.js';
import { AIService } from './services/aiService.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const testEmails = [
  { name: 'Jennifer Martinez', email: 'jennifer.martinez@gmail.com', subject: 'Website donation issue', body: "I've been trying to donate on your website for 20 minutes but it keeps crashing. Can someone call me?", date: '2026-01-12' },
  { name: 'David Chen', email: 'dchen@outlook.com', subject: 'Thank you for scholarship', body: "Thank you so much for the scholarship! It changed my life and I'm forever grateful.", date: '2026-01-12' },
  { name: 'Amanda Foster', email: 'amanda.foster@business.com', subject: 'Partnership meeting request', body: 'Can we schedule a meeting next week to discuss partnership opportunities?', date: '2026-01-13' },
  { name: 'Marcus Thompson', email: 'mthompson78@yahoo.com', subject: 'Address update needed', body: 'I need to update my mailing address in your system. My new address is 123 Main St.', date: '2026-01-13' },
  { name: 'Patricia Rodriguez', email: 'p.rodriguez@email.com', subject: 'Complaint about staff', body: 'Your staff was incredibly rude when I called yesterday. This is unacceptable.', date: '2026-01-13' },
  { name: 'Kevin Liu', email: 'kevin.liu@alumni.edu', subject: 'Monthly donation inquiry', body: "I'm interested in making a monthly donation. What are my options?", date: '2026-01-13' },
  { name: 'Rachel Green', email: 'rachelg@hotmail.com', subject: 'Thank you', body: 'Just wanted to say thank you for all the amazing work you do in the community!', date: '2026-01-14' },
  { name: 'Brandon Mitchell', email: 'b.mitchell@domain.com', subject: 'Event feedback', body: "The event last week was poorly organized. The venue was too small and there wasn't enough food.", date: '2026-01-14' },
  { name: 'Lisa Anderson', email: 'lisa.anderson@gmail.com', subject: 'Donation receipt request', body: 'How do I access my donation receipt for tax purposes?', date: '2026-01-14' },
  { name: 'Christopher Davis', email: 'c.davis@example.com', subject: 'Volunteer interest', body: 'I would love to volunteer. Can someone contact me about opportunities?', date: '2026-01-14' },
  { name: 'Michelle Parker', email: 'mparker@mail.com', subject: 'Cancel monthly donation', body: 'Please cancel my monthly donation effective immediately.', date: '2026-01-15' },
  { name: 'James Wilson', email: 'jwilson@provider.net', subject: 'Unsubscribe', body: "I'm done with this organization. Remove me from all mailing lists.", date: '2026-01-15' },
  { name: 'Nicole Stevens', email: 'nicole.stevens@email.org', subject: 'No longer supporting', body: 'After this experience, I will no longer be supporting the alumni association.', date: '2026-01-15' },
  { name: 'Robert Taylor', email: 'rtaylor@university.edu', subject: 'Mixed feelings', body: "I'm unhappy with the direction you're taking, but I'll continue my monthly donation.", date: '2026-01-15' },
  { name: 'Samantha Brooks', email: 'sbrooks@company.com', subject: 'Increase donation', body: 'Can you help me increase my donation to $100 per month?', date: '2026-01-15' },
];

async function saveAllTestEmails() {
  try {
    Logger.info('=== Saving All 15 Test Emails (Batch Mode) ===');

    // Initialize Google Sheets
    const credentialsPath = join(__dirname, '../credentials/service-account.json');
    const credentials = JSON.parse(readFileSync(credentialsPath, 'utf8'));
    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });
    const sheets = google.sheets({ version: 'v4', auth });
    const spreadsheetId = config.sheets.spreadsheetId;

    // Initialize AI service
    const aiService = new AIService();

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

    // Process all emails and collect data
    Logger.info(`Step 3: Analyzing ${testEmails.length} emails...`);
    const allRows = [];

    for (let i = 0; i < testEmails.length; i++) {
      const email = testEmails[i];
      Logger.info(`  [${i + 1}/${testEmails.length}] Analyzing: ${email.name}`);

      const analysis = await aiService.analyzeSentimentAndIntent(email.body, email.subject);

      allRows.push([
        email.date,
        email.name,
        email.email,
        analysis.sentiment,
        '', // Assigned staff (empty for now)
        analysis.summary,
      ]);
    }

    // Add all rows at once
    Logger.info('Step 4: Adding all rows to sheet in one batch...');
    await sheets.spreadsheets.values.append({
      spreadsheetId,
      range: 'Sheet1!A2:F',
      valueInputOption: 'RAW',
      requestBody: {
        values: allRows,
      },
    });

    Logger.success(`✓ Successfully added ${allRows.length} emails to Google Sheets!`);

    // Verify
    Logger.info('Step 5: Verifying...');
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: 'Sheet1!A:F',
    });

    const rows = response.data.values || [];
    Logger.success(`Verified: Found ${rows.length} total rows (${rows.length - 1} emails + 1 header)`);

    Logger.success(`\nView your sheet: https://docs.google.com/spreadsheets/d/${spreadsheetId}/edit`);

  } catch (error) {
    Logger.error('Failed to save test emails', error);
    throw error;
  }
}

saveAllTestEmails()
  .then(() => {
    process.exit(0);
  })
  .catch((error) => {
    process.exit(1);
  });
