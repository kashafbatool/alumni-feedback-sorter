import { google } from 'googleapis';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { config } from '../utils/config.js';
import { Logger } from '../utils/logger.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export class SheetsService {
  constructor() {
    this.sheets = null;
    this.spreadsheetId = config.sheets.spreadsheetId;
  }

  async initialize() {
    try {
      const credentialsPath = join(__dirname, '../../credentials/service-account.json');
      const credentials = JSON.parse(readFileSync(credentialsPath, 'utf8'));

      const auth = new google.auth.GoogleAuth({
        credentials,
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
      });

      this.sheets = google.sheets({ version: 'v4', auth });
      Logger.info('Google Sheets service initialized');
    } catch (error) {
      Logger.error('Error initializing Google Sheets service', error);
      throw error;
    }
  }

  async appendRow(data) {
    try {
      if (!this.sheets) {
        await this.initialize();
      }

      const { date, alumName, alumEmail, sentiment, assignedStaff, summary } = data;

      // Get current row count to know where to insert
      const response = await this.sheets.spreadsheets.values.get({
        spreadsheetId: this.spreadsheetId,
        range: 'Sheet1!A:F',
      });

      const currentRowCount = response.data.values?.length || 0;
      const nextRow = currentRowCount + 1;

      const values = [[
        date.toISOString().split('T')[0], // Format: YYYY-MM-DD
        alumName,
        alumEmail,
        sentiment,
        assignedStaff || '',
        summary,
      ]];

      Logger.info(`Appending row for: ${alumEmail} at row ${nextRow}`);

      // Use UPDATE with specific row number instead of APPEND
      const updateResponse = await this.sheets.spreadsheets.values.update({
        spreadsheetId: this.spreadsheetId,
        range: `Sheet1!A${nextRow}:F${nextRow}`,
        valueInputOption: 'USER_ENTERED',
        requestBody: { values },
      });

      Logger.success(`Added row to Google Sheets at row ${nextRow}`, { alumEmail, sentiment });
      return updateResponse.data;
    } catch (error) {
      Logger.error('Error appending row to Google Sheets', error);
      throw error;
    }
  }

  async checkIfEmailExists(email) {
    try {
      if (!this.sheets) {
        await this.initialize();
      }

      const response = await this.sheets.spreadsheets.values.get({
        spreadsheetId: this.spreadsheetId,
        range: 'Sheet1!C:C', // Column C contains Alum Email
      });

      const rows = response.data.values || [];
      return rows.some(row => row[0] === email);
    } catch (error) {
      Logger.error('Error checking if email exists in Google Sheets', error);
      return false;
    }
  }

  async setupHeaders() {
    try {
      if (!this.sheets) {
        await this.initialize();
      }

      const response = await this.sheets.spreadsheets.values.get({
        spreadsheetId: this.spreadsheetId,
        range: 'Sheet1!A1:F1',
      });

      const existingHeaders = response.data.values?.[0] || [];

      // Only add headers if they don't exist (first time setup)
      if (existingHeaders.length === 0) {
        const headers = [['Date', 'Alum Name', 'Alum Email', 'Sentiment', 'Assigned Staff', 'Summary']];

        await this.sheets.spreadsheets.values.update({
          spreadsheetId: this.spreadsheetId,
          range: 'Sheet1!A1:F1',
          valueInputOption: 'USER_ENTERED',
          requestBody: { values: headers },
        });

        Logger.success('Added headers to Google Sheets');
      } else {
        Logger.info('Headers already exist, skipping setup');
      }
    } catch (error) {
      Logger.error('Error setting up headers in Google Sheets', error);
      throw error;
    }
  }
}
