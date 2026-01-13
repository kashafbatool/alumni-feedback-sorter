import { config, validateConfig } from './utils/config.js';
import { Logger } from './utils/logger.js';
import { SheetsService } from './services/sheetsService.js';
import { RaisersEdgeService } from './services/raisersEdgeService.js';
import { AIService } from './services/aiService.js';
import { EmailData } from './models/emailData.js';

// Mock email data for testing
const mockEmails = [
  {
    id: 'mock-1',
    from: 'john.smith@alumni.example.com',
    name: 'John Smith',
    subject: 'Thank you for the wonderful reunion event!',
    body: 'I wanted to reach out and express my gratitude for organizing such a fantastic alumni reunion last weekend. It was incredible to reconnect with old classmates and see how the campus has evolved. The presentations were informative and inspiring. Thank you to the entire team for putting this together!',
    date: new Date('2026-01-10'),
  },
  {
    id: 'mock-2',
    from: 'sarah.johnson@gmail.com',
    name: 'Sarah Johnson',
    subject: 'Interested in making a donation',
    body: 'Hello, I graduated in 2010 and have been following the university\'s progress over the years. I would like to make a contribution to the scholarship fund to help support current students. Could you please send me information about how to proceed with a donation? I\'m particularly interested in supporting students in the Computer Science department.',
    date: new Date('2026-01-11'),
  },
  {
    id: 'mock-3',
    from: 'mike.brown@yahoo.com',
    name: 'Mike Brown',
    subject: 'Complaint about fundraising calls',
    body: 'I have received three phone calls this week from your fundraising team despite previously asking to be removed from the call list. This is very frustrating and unprofessional. Please ensure that I am removed from all calling lists immediately. I should not have to keep repeating this request.',
    date: new Date('2026-01-11'),
  },
  {
    id: 'mock-4',
    from: 'emily.davis@outlook.com',
    name: 'Emily Davis',
    subject: 'Please unsubscribe me',
    body: 'Hi, I would like to unsubscribe from all alumni emails and mailings. Please remove me from your mailing list and stop sending me newsletters. Thank you.',
    date: new Date('2026-01-12'),
  },
  {
    id: 'mock-5',
    from: 'robert.wilson@alumni.edu',
    name: 'Robert Wilson',
    subject: 'Update on my career',
    body: 'Hello! I wanted to share some exciting news with the alumni office. I recently got promoted to Senior Director at my company and will be speaking at a major industry conference next month. I\'d love to stay connected and potentially mentor current students interested in my field. Looking forward to hearing from you!',
    date: new Date('2026-01-12'),
  },
];

async function testWithMockData() {
  const startTime = Date.now();
  Logger.info('=== Starting Mock Email Processing Test ===');

  try {
    // Check for required configurations (skip Gmail validation)
    const requiredVars = ['GOOGLE_SHEETS_ID', 'GOOGLE_SERVICE_ACCOUNT_EMAIL'];
    const missing = requiredVars.filter(key => !process.env[key]);

    if (missing.length > 0) {
      throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
    }

    // Initialize services (no Gmail needed)
    const sheetsService = new SheetsService();
    const raisersEdgeService = new RaisersEdgeService();
    const aiService = new AIService();

    Logger.info('Services initialized successfully');

    // Setup Google Sheets headers if needed
    Logger.info('Setting up Google Sheets headers...');
    await sheetsService.setupHeaders();
    Logger.success('Google Sheets headers configured');

    Logger.info(`Processing ${mockEmails.length} mock emails`);

    let processedCount = 0;
    let errorCount = 0;

    // Process each mock email
    for (const email of mockEmails) {
      try {
        Logger.info(`Processing mock email from: ${email.from}`);

        // Get staff assignment from Raiser's Edge (if configured)
        let assignedStaff = null;
        if (raisersEdgeService.isConfigured) {
          Logger.info('Raiser\'s Edge is configured, attempting staff lookup...');
          assignedStaff = await raisersEdgeService.getAssignedStaff(email.from);
        } else {
          Logger.info('Raiser\'s Edge not configured, skipping staff lookup');
        }

        // Analyze sentiment and generate summary using AI
        Logger.info('Analyzing sentiment and generating summary...');
        const analysis = await aiService.analyzeSentimentAndIntent(email.body, email.subject);
        Logger.info('Analysis complete', {
          sentiment: analysis.sentiment,
          intent: analysis.intent,
        });

        // Create email data object
        const emailData = EmailData.fromGmailAndAnalysis(email, analysis, assignedStaff);

        // Append to Google Sheets
        Logger.info('Writing to Google Sheets...');
        await sheetsService.appendRow(emailData.toSheetRow());

        processedCount++;
        Logger.success(`Successfully processed email from ${email.from}`, {
          sentiment: analysis.sentiment,
          intent: analysis.intent,
          assignedStaff: assignedStaff || 'None',
        });

        // Small delay between emails to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 500));

      } catch (error) {
        errorCount++;
        Logger.error(`Error processing email from ${email.from}`, error);
      }
    }

    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    Logger.info('=== Mock Email Processing Test Complete ===', {
      total: mockEmails.length,
      processed: processedCount,
      errors: errorCount,
      duration: `${duration}s`,
    });

    if (processedCount > 0) {
      Logger.success(`\n✓ Test successful! Check your Google Sheet:\nhttps://docs.google.com/spreadsheets/d/${config.sheets.spreadsheetId}/edit`);
    }

  } catch (error) {
    Logger.error('Fatal error in mock email processing test', error);
    throw error;
  }
}

// Run the test
testWithMockData()
  .then(() => {
    Logger.success('Test completed successfully');
    process.exit(0);
  })
  .catch((error) => {
    Logger.error('Test failed', error);
    process.exit(1);
  });
