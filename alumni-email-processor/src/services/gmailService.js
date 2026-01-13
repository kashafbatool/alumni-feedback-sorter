import { google } from 'googleapis';
import { config } from '../utils/config.js';
import { Logger } from '../utils/logger.js';

export class GmailService {
  constructor(auth) {
    this.gmail = google.gmail({ version: 'v1', auth });
  }

  async getUnreadEmails(maxResults = 50) {
    try {
      Logger.info('Fetching unread emails from Gmail');

      const response = await this.gmail.users.messages.list({
        userId: 'me',
        q: 'is:unread', // Only unread emails
        maxResults,
      });

      const messages = response.data.messages || [];
      Logger.info(`Found ${messages.length} unread emails`);

      const emails = [];
      for (const message of messages) {
        const email = await this.getEmailDetails(message.id);
        if (email) {
          emails.push(email);
        }
      }

      return emails;
    } catch (error) {
      Logger.error('Error fetching emails from Gmail', error);
      throw error;
    }
  }

  async getEmailDetails(messageId) {
    try {
      const response = await this.gmail.users.messages.get({
        userId: 'me',
        id: messageId,
        format: 'full',
      });

      const message = response.data;
      const headers = message.payload.headers;

      const getHeader = (name) => {
        const header = headers.find(h => h.name.toLowerCase() === name.toLowerCase());
        return header ? header.value : '';
      };

      const fromHeader = getHeader('From');
      const emailMatch = fromHeader.match(/<(.+?)>/);
      const email = emailMatch ? emailMatch[1] : fromHeader;

      const nameMatch = fromHeader.match(/^(.+?)\s*</);
      const name = nameMatch ? nameMatch[1].replace(/"/g, '').trim() : email;

      let body = '';
      if (message.payload.body.data) {
        body = Buffer.from(message.payload.body.data, 'base64').toString('utf-8');
      } else if (message.payload.parts) {
        for (const part of message.payload.parts) {
          if (part.mimeType === 'text/plain' && part.body.data) {
            body = Buffer.from(part.body.data, 'base64').toString('utf-8');
            break;
          }
        }

        if (!body) {
          for (const part of message.payload.parts) {
            if (part.mimeType === 'text/html' && part.body.data) {
              const htmlBody = Buffer.from(part.body.data, 'base64').toString('utf-8');
              body = htmlBody.replace(/<[^>]*>/g, '');
              break;
            }
          }
        }
      }

      const dateHeader = getHeader('Date');
      const date = dateHeader ? new Date(dateHeader) : new Date();

      return {
        id: messageId,
        from: email,
        name,
        subject: getHeader('Subject'),
        body: body.trim(),
        date,
      };
    } catch (error) {
      Logger.error(`Error fetching email details for message ${messageId}`, error);
      return null;
    }
  }

  async markAsRead(messageId) {
    try {
      await this.gmail.users.messages.modify({
        userId: 'me',
        id: messageId,
        requestBody: {
          removeLabelIds: ['UNREAD'],
        },
      });
      Logger.info(`Marked email ${messageId} as read`);
    } catch (error) {
      Logger.error(`Error marking email ${messageId} as read`, error);
    }
  }
}
