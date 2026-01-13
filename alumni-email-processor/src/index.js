import cron from 'node-cron';
import { config, validateConfig } from './utils/config.js';
import { Logger } from './utils/logger.js';
import { processEmails } from './processEmails.js';

async function startScheduler() {
  Logger.info('=== Alumni Email Processor Started ===');
  Logger.info(`Process interval: ${config.processing.intervalMinutes} minutes`);
  Logger.info(`Max emails per run: ${config.processing.maxEmailsPerRun}`);

  try {
    // Validate configuration on startup
    validateConfig();

    // Run immediately on startup
    Logger.info('Running initial email processing...');
    await processEmails();

    // Schedule recurring processing
    const cronExpression = `*/${config.processing.intervalMinutes} * * * *`;
    Logger.info(`Scheduled to run every ${config.processing.intervalMinutes} minutes`);

    cron.schedule(cronExpression, async () => {
      try {
        await processEmails();
      } catch (error) {
        Logger.error('Scheduled processing failed', error);
      }
    });

    Logger.success('Scheduler is running. Press Ctrl+C to stop.');
  } catch (error) {
    Logger.error('Failed to start scheduler', error);
    process.exit(1);
  }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  Logger.info('Shutting down scheduler...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  Logger.info('Shutting down scheduler...');
  process.exit(0);
});

// Start the scheduler
startScheduler();
