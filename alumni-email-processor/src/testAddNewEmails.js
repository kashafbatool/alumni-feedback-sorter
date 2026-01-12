import { SheetsService } from './services/sheetsService.js';
import { AIService } from './services/aiService.js';
import { Logger } from './utils/logger.js';

// New test emails to add to existing data
const newTestEmails = [
  {
    name: 'Alex Johnson',
    email: 'alex.j@test.com',
    subject: 'Question about event',
    body: "Hi, I have a question about the upcoming alumni networking event. What time does it start and is there a dress code? Looking forward to attending!",
    date: '2026-01-16',
  },
  {
    name: 'Maria Garcia',
    email: 'm.garcia@email.com',
    subject: 'Donation confirmation',
    body: "I just made a donation of $500 through your website. Can you please send me a confirmation receipt for my tax records? Thank you!",
    date: '2026-01-16',
  },
  {
    name: 'Tom Williams',
    email: 'twilliams@company.net',
    subject: 'Very disappointed',
    body: "I attended your fundraising gala last night and I have to say I'm extremely disappointed. The food was cold, the music was too loud, and the program ran two hours late. This is not acceptable for the ticket price we paid.",
    date: '2026-01-16',
  },
];

async function testAddNewEmails() {
  try {
    Logger.info('=== Testing: Add New Emails WITHOUT Deleting Existing Data ===');

    const sheetsService = new SheetsService();
    const aiService = new AIService();

    await sheetsService.initialize();

    // Check existing data
    Logger.info('Step 1: Checking existing data...');
    const existingResponse = await sheetsService.sheets.spreadsheets.values.get({
      spreadsheetId: sheetsService.spreadsheetId,
      range: 'Sheet1!A:F',
    });

    const existingRows = existingResponse.data.values || [];
    Logger.info(`Found ${existingRows.length} existing rows (including header)`);

    // Make sure headers exist
    await sheetsService.setupHeaders();

    // Process and add new emails
    Logger.info(`\nStep 2: Adding ${newTestEmails.length} new emails...`);

    for (let i = 0; i < newTestEmails.length; i++) {
      const email = newTestEmails[i];

      Logger.info(`  [${i + 1}/${newTestEmails.length}] Processing: ${email.name}`);

      // Analyze sentiment
      const analysis = await aiService.analyzeSentimentAndIntent(email.body, email.subject);

      Logger.info(`    → Sentiment: ${analysis.sentiment}, Summary: "${analysis.summary}"`);

      // Add to sheet
      const rowData = {
        date: new Date(email.date),
        alumName: email.name,
        alumEmail: email.email,
        sentiment: analysis.sentiment,
        assignedStaff: '',
        summary: analysis.summary,
      };

      await sheetsService.appendRow(rowData);

      // Small delay
      await new Promise(resolve => setTimeout(resolve, 300));
    }

    // Verify final count
    Logger.info('\nStep 3: Verifying...');
    const finalResponse = await sheetsService.sheets.spreadsheets.values.get({
      spreadsheetId: sheetsService.spreadsheetId,
      range: 'Sheet1!A:F',
    });

    const finalRows = finalResponse.data.values || [];
    const newRowCount = finalRows.length - existingRows.length;

    Logger.success(`\n✓ Success!`);
    Logger.success(`  Before: ${existingRows.length} rows`);
    Logger.success(`  After: ${finalRows.length} rows`);
    Logger.success(`  Added: ${newRowCount} new rows`);
    Logger.success(`\nView your sheet: https://docs.google.com/spreadsheets/d/${sheetsService.spreadsheetId}/edit`);

    // Show the new summaries
    Logger.info('\nNew email summaries:');
    for (let i = existingRows.length; i < finalRows.length; i++) {
      const row = finalRows[i];
      Logger.info(`  ${row[1]}: "${row[5]}"`);
    }

  } catch (error) {
    Logger.error('Failed to add new emails', error);
    throw error;
  }
}

testAddNewEmails()
  .then(() => {
    process.exit(0);
  })
  .catch((error) => {
    process.exit(1);
  });
