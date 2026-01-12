import { SheetsService } from './services/sheetsService.js';
import { AIService } from './services/aiService.js';
import { Logger } from './utils/logger.js';

async function testFinalFix() {
  const sheetsService = new SheetsService();
  const aiService = new AIService();

  await sheetsService.initialize();

  // Get current count
  const before = await sheetsService.sheets.spreadsheets.values.get({
    spreadsheetId: sheetsService.spreadsheetId,
    range: 'Sheet1!A:F',
  });
  const beforeCount = before.data.values.length;

  Logger.info(`Current row count: ${beforeCount}`);

  // Add one test email
  const testEmail = {
    name: 'Test User',
    email: 'test@final.com',
    subject: 'Final test',
    body: 'This email should appear at the END of the spreadsheet, not at the beginning.',
    date: '2026-01-16',
  };

  Logger.info(`Adding test email from: ${testEmail.name}`);

  const analysis = await aiService.analyzeSentimentAndIntent(testEmail.body, testEmail.subject);

  await sheetsService.appendRow({
    date: new Date(testEmail.date),
    alumName: testEmail.name,
    alumEmail: testEmail.email,
    sentiment: analysis.sentiment,
    assignedStaff: '',
    summary: analysis.summary,
  });

  // Check where it was added
  const after = await sheetsService.sheets.spreadsheets.values.get({
    spreadsheetId: sheetsService.spreadsheetId,
    range: 'Sheet1!A:F',
  });
  const afterCount = after.data.values.length;

  Logger.success(`New row count: ${afterCount}`);

  // Find where the email was added
  const rows = after.data.values;
  const foundIndex = rows.findIndex(r => r[2] === testEmail.email);

  if (foundIndex === afterCount - 1) {
    Logger.success(`✓ CORRECT: Email was added at the END (row ${foundIndex + 1})`);
    Logger.success(`Summary: "${rows[foundIndex][5]}"`);
  } else {
    Logger.error(`✗ WRONG: Email was added at row ${foundIndex + 1}, but should be at row ${afterCount}`);
  }
}

testFinalFix();
