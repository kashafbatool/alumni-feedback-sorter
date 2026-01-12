import { SheetsService } from './services/sheetsService.js';
import { Logger } from './utils/logger.js';

async function clearSheet() {
  try {
    const sheetsService = new SheetsService();
    await sheetsService.initialize();

    Logger.info('Clearing all data from Google Sheet...');

    // Clear all data
    await sheetsService.sheets.spreadsheets.values.clear({
      spreadsheetId: sheetsService.spreadsheetId,
      range: 'Sheet1!A:F',
    });

    Logger.success('Sheet cleared successfully');

  } catch (error) {
    Logger.error('Error clearing sheet', error);
    throw error;
  }
}

clearSheet()
  .then(() => {
    Logger.success('Done! Now run: npm test');
    process.exit(0);
  })
  .catch((error) => {
    Logger.error('Failed to clear sheet', error);
    process.exit(1);
  });
