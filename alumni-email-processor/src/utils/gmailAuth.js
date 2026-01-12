import { google } from 'googleapis';
import { createInterface } from 'readline';
import { config } from './config.js';

const oauth2Client = new google.auth.OAuth2(
  config.gmail.clientId,
  config.gmail.clientSecret,
  config.gmail.redirectUri
);

const SCOPES = ['https://www.googleapis.com/auth/gmail.readonly'];

export async function authenticateGmail() {
  if (config.gmail.refreshToken) {
    oauth2Client.setCredentials({
      refresh_token: config.gmail.refreshToken,
    });
    return oauth2Client;
  }

  const authUrl = oauth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: SCOPES,
  });

  console.log('\n=== Gmail Authentication Required ===');
  console.log('1. Visit this URL:', authUrl);
  console.log('2. Authorize the application');
  console.log('3. Copy the authorization code from the URL');
  console.log('\nNote: Save the refresh token to your .env file as GMAIL_REFRESH_TOKEN\n');

  const rl = createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve, reject) => {
    rl.question('Enter the authorization code: ', async (code) => {
      rl.close();
      try {
        const { tokens } = await oauth2Client.getToken(code);
        oauth2Client.setCredentials(tokens);

        console.log('\nAuthentication successful!');
        console.log('Add this to your .env file:');
        console.log(`GMAIL_REFRESH_TOKEN=${tokens.refresh_token}`);

        resolve(oauth2Client);
      } catch (error) {
        reject(new Error(`Authentication failed: ${error.message}`));
      }
    });
  });
}

// Run this script directly to authenticate
if (import.meta.url === `file://${process.argv[1]}`) {
  authenticateGmail()
    .then(() => {
      console.log('\nAuthentication complete. You can now run the email processor.');
      process.exit(0);
    })
    .catch((error) => {
      console.error('Authentication error:', error);
      process.exit(1);
    });
}
