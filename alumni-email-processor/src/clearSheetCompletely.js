import { google } from 'googleapis';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { config } from './utils/config.js';
import { Logger } from './utils/logger.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function clearSheetCompletely() {
  try {
    Logger.info('Clearing entire spreadsheet...');

    const credentialsPath = join(__dirname, '../credentials/service-account.json');
    const credentials = JSON.parse(readFileSync(credentialsPath, 'utf8'));
    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });

    const sheets = google.sheets({ version: 'v4', auth });
    const spreadsheetId = config.sheets.spreadsheetId;

    // Get sheet ID
    const sheetInfo = await sheets.spreadsheets.get({
      spreadsheetId,
    });

    const sheetId = sheetInfo.data.sheets[0].properties.sheetId;

    Logger.info(`Sheet ID: ${sheetId}`);

    // Delete all rows except the first one (which we'll use for headers)
    await sheets.spreadsheets.batchUpdate({
      spreadsheetId,
      requestBody: {
        requests: [
          {
            deleteDimension: {
              range: {
                sheetId,
                dimension: 'ROWS',
                startIndex: 1, // Start from row 2 (0-indexed)
                endIndex: 1000, // Delete up to row 1000
              },
            },
          },
        ],
      },
    });

    Logger.success('✓ All data rows deleted');

    // Clear the first row
    await sheets.spreadsheets.values.clear({
      spreadsheetId,
      range: 'Sheet1!A1:F1',
    });

    Logger.success('✓ Header row cleared');

    // Add fresh headers
    await sheets.spreadsheets.values.update({
      spreadsheetId,
      range: 'Sheet1!A1:F1',
      valueInputOption: 'RAW',
      requestBody: {
        values: [['Date', 'Alum Name', 'Alum Email', 'Sentiment', 'Assigned Staff', 'Summary']],
      },
    });

    Logger.success('✓ Fresh headers added');

    // Verify
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: 'Sheet1!A:F',
    });

    Logger.success(`✓ Sheet now has ${response.data.values?.length || 0} rows (should be 1)`);
    Logger.success(`View: https://docs.google.com/spreadsheets/d/${spreadsheetId}/edit`);

  } catch (error) {
    Logger.error('Failed to clear sheet', error);
    throw error;
  }
}

clearSheetCompletely()
  .then(() => process.exit(0))
  .catch(() => process.exit(1));
