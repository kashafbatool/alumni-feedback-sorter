import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: join(__dirname, '../../.env') });

export const config = {
  gmail: {
    clientId: process.env.GMAIL_CLIENT_ID,
    clientSecret: process.env.GMAIL_CLIENT_SECRET,
    redirectUri: process.env.GMAIL_REDIRECT_URI || 'http://localhost:3000/oauth2callback',
    refreshToken: process.env.GMAIL_REFRESH_TOKEN,
  },
  sheets: {
    spreadsheetId: process.env.GOOGLE_SHEETS_ID,
    serviceAccountEmail: process.env.GOOGLE_SERVICE_ACCOUNT_EMAIL,
    range: 'Sheet1!A:F', // Date, Alum Name, Alum Email, Sentiment, Assigned Staff, Summary
  },
  raisersEdge: {
    apiKey: process.env.RAISERS_EDGE_API_KEY,
    tenantId: process.env.RAISERS_EDGE_TENANT_ID,
    baseUrl: 'https://api.sky.blackbaud.com',
  },
  ai: {
    openaiApiKey: process.env.OPENAI_API_KEY,
    anthropicApiKey: process.env.ANTHROPIC_API_KEY,
  },
  processing: {
    alumniEmailAddress: process.env.ALUMNI_EMAIL_ADDRESS,
    intervalMinutes: parseInt(process.env.PROCESS_INTERVAL_MINUTES) || 30,
    maxEmailsPerRun: parseInt(process.env.MAX_EMAILS_PER_RUN) || 50,
  },
};

export function validateConfig() {
  const required = [
    'GMAIL_CLIENT_ID',
    'GMAIL_CLIENT_SECRET',
    'GMAIL_REFRESH_TOKEN',
    'GOOGLE_SHEETS_ID',
    'GOOGLE_SERVICE_ACCOUNT_EMAIL',
  ];

  const missing = required.filter(key => !process.env[key]);

  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
  }

  if (!process.env.OPENAI_API_KEY && !process.env.ANTHROPIC_API_KEY) {
    console.warn('Warning: No AI API key configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY');
  }

  if (!process.env.RAISERS_EDGE_API_KEY) {
    console.warn('Warning: RAISERS_EDGE_API_KEY not set. Staff assignments will be empty.');
  }
}
