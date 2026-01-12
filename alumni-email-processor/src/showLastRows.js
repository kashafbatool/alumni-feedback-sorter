import { SheetsService } from './services/sheetsService.js';
import { Logger } from './utils/logger.js';

async function showLastRows() {
  const sheetsService = new SheetsService();
  await sheetsService.initialize();

  const response = await sheetsService.sheets.spreadsheets.values.get({
    spreadsheetId: sheetsService.spreadsheetId,
    range: 'Sheet1!A:F',
  });

  const rows = response.data.values || [];

  console.log(`\nTotal rows: ${rows.length}\n`);
  console.log('Last 5 rows:');
  console.log('='.repeat(120));

  for (let i = Math.max(0, rows.length - 5); i < rows.length; i++) {
    const row = rows[i];
    console.log(`\nRow ${i + 1}:`);
    console.log(`  Date: ${row[0]}`);
    console.log(`  Name: ${row[1]}`);
    console.log(`  Email: ${row[2]}`);
    console.log(`  Sentiment: ${row[3]}`);
    console.log(`  Staff: ${row[4] || '(none)'}`);
    console.log(`  Summary: ${row[5]}`);
  }
}

showLastRows();
