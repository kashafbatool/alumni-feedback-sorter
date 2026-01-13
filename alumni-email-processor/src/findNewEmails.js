import { SheetsService } from './services/sheetsService.js';

async function findNewEmails() {
  const sheetsService = new SheetsService();
  await sheetsService.initialize();

  const response = await sheetsService.sheets.spreadsheets.values.get({
    spreadsheetId: sheetsService.spreadsheetId,
    range: 'Sheet1!A:F',
  });

  const rows = response.data.values || [];

  console.log(`\nSearching in ${rows.length} total rows...\n`);

  const newEmails = ['alex.j@test.com', 'm.garcia@email.com', 'twilliams@company.net'];

  newEmails.forEach(email => {
    const row = rows.find(r => r[2] === email);
    if (row) {
      const rowIndex = rows.indexOf(row) + 1;
      console.log(`✓ Found ${email} at row ${rowIndex}`);
      console.log(`  Name: ${row[1]}`);
      console.log(`  Summary: "${row[5]}"`);
      console.log();
    } else {
      console.log(`✗ NOT FOUND: ${email}`);
    }
  });
}

findNewEmails();
