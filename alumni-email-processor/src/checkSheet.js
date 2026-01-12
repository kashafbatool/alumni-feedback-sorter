import { SheetsService } from './services/sheetsService.js';
import { Logger } from './utils/logger.js';

async function checkSheetContents() {
  try {
    const sheetsService = new SheetsService();
    await sheetsService.initialize();

    Logger.info('Reading all data from Google Sheet...');

    const response = await sheetsService.sheets.spreadsheets.values.get({
      spreadsheetId: sheetsService.spreadsheetId,
      range: 'Sheet1!A:F',
    });

    const rows = response.data.values || [];

    Logger.info(`Found ${rows.length} rows in the sheet`);

    rows.forEach((row, index) => {
      console.log(`Row ${index + 1}:`, row);
    });

  } catch (error) {
    Logger.error('Error reading sheet', error);
  }
}

checkSheetContents();
