import { google } from 'googleapis';
import { config, validateConfig } from './utils/config.js';
import { Logger } from './utils/logger.js';
import { GmailService } from './services/gmailService.js';
import { SheetsService } from './services/sheetsService.js';
import { RaisersEdgeService } from './services/raisersEdgeService.js';
import { AIService } from './services/aiService.js';
import { EmailData } from './models/emailData.js';

export async function processEmails() {
  const startTime = Date.now();
  Logger.info('=== Starting Email Processing ===');

  try {
    // Validate configuration
    validateConfig();

    // Initialize services
    const oauth2Client = new google.auth.OAuth2(
      config.gmail.clientId,
      config.gmail.clientSecret,
      config.gmail.redirectUri
    );

    oauth2Client.setCredentials({
      refresh_token: config.gmail.refreshToken,
    });

    const gmailService = new GmailService(oauth2Client);
    const sheetsService = new SheetsService();
    const raisersEdgeService = new RaisersEdgeService();
    const aiService = new AIService();

    // Setup Google Sheets headers if needed (only first time)
    await sheetsService.setupHeaders();

    // Fetch unread emails
    const emails = await gmailService.getUnreadEmails(config.processing.maxEmailsPerRun);

    if (emails.length === 0) {
      Logger.info('No unread emails to process');
      return;
    }

    Logger.info(`Processing ${emails.length} emails`);

    let processedCount = 0;
    let errorCount = 0;

    // Process each email
    for (const email of emails) {
      try {
        Logger.info(`Processing email from: ${email.from}`);

        // Check if already processed (email exists in sheet)
        const alreadyProcessed = await sheetsService.checkIfEmailExists(email.from);
        if (alreadyProcessed) {
          Logger.info(`Email from ${email.from} already processed, marking as read`);
          await gmailService.markAsRead(email.id);
          continue;
        }

        // Get staff assignment from Raiser's Edge
        let assignedStaff = null;
        if (raisersEdgeService.isConfigured) {
          assignedStaff = await raisersEdgeService.getAssignedStaff(email.from);
        }

        // Analyze sentiment and generate summary using AI
        const analysis = await aiService.analyzeSentimentAndIntent(email.body, email.subject);

        // Create email data object
        const emailData = EmailData.fromGmailAndAnalysis(email, analysis, assignedStaff);

        // Append to Google Sheets
        await sheetsService.appendRow(emailData.toSheetRow());

        // Mark email as read
        await gmailService.markAsRead(email.id);

        processedCount++;
        Logger.success(`Successfully processed email from ${email.from}`, {
          sentiment: analysis.sentiment,
          intent: analysis.intent,
          assignedStaff: assignedStaff || 'None',
        });

      } catch (error) {
        errorCount++;
        Logger.error(`Error processing email from ${email.from}`, error);
      }
    }

    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    Logger.info('=== Email Processing Complete ===', {
      total: emails.length,
      processed: processedCount,
      errors: errorCount,
      duration: `${duration}s`,
    });

  } catch (error) {
    Logger.error('Fatal error in email processing', error);
    throw error;
  }
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  processEmails()
    .then(() => {
      Logger.success('Email processing completed successfully');
      process.exit(0);
    })
    .catch((error) => {
      Logger.error('Email processing failed', error);
      process.exit(1);
    });
}
