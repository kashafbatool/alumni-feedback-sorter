import { SheetsService } from './services/sheetsService.js';
import { AIService } from './services/aiService.js';
import { Logger } from './utils/logger.js';

// Generate 50 diverse test emails
const mockEmails = [
  { name: 'Alice Thompson', email: 'alice.t@gmail.com', subject: 'Donation inquiry', body: 'I would like to set up a recurring monthly donation of $250. What are my payment options?', date: '2026-01-13' },
  { name: 'Bob Martinez', email: 'bob.m@yahoo.com', subject: 'Website broken', body: 'Your donation page has been down for 3 days. I tried to give but cannot complete the transaction. Very frustrating!', date: '2026-01-13' },
  { name: 'Carol White', email: 'cwhite@outlook.com', subject: 'Thank you!', body: 'I just wanted to thank you for the scholarship I received. It made all the difference in my education!', date: '2026-01-13' },
  { name: 'David Lee', email: 'd.lee@university.edu', subject: 'Unsubscribe please', body: 'Please remove me from all your mailing lists. I no longer wish to receive emails.', date: '2026-01-13' },
  { name: 'Emma Rodriguez', email: 'emma.r@company.com', subject: 'Event registration', body: 'Can you send me the link to register for the alumni networking event next month?', date: '2026-01-14' },
  { name: 'Frank Chen', email: 'frankc@email.net', subject: 'Terrible experience', body: 'The gala last night was a disaster. Poor planning, terrible food, and the speaker was 2 hours late. Unacceptable.', date: '2026-01-14' },
  { name: 'Grace Kim', email: 'grace.kim@alumni.org', subject: 'Volunteer opportunity', body: 'I would love to volunteer for the mentorship program. How can I get involved?', date: '2026-01-14' },
  { name: 'Henry Brown', email: 'hbrown@mail.com', subject: 'Donation receipt', body: 'I donated $1000 last month but never received a tax receipt. Can you resend it?', date: '2026-01-14' },
  { name: 'Iris Wang', email: 'iris.wang@tech.io', subject: 'Partnership proposal', body: 'Our company would like to discuss a corporate partnership with the alumni association. Can we schedule a meeting?', date: '2026-01-15' },
  { name: 'Jack Wilson', email: 'jwilson99@gmail.com', subject: 'Cancel my membership', body: 'Please cancel my alumni membership immediately. I am done with this organization after how I was treated.', date: '2026-01-15' },
  { name: 'Kate Johnson', email: 'kate.j@provider.net', subject: 'Amazing event!', body: 'The career fair you organized was fantastic! I connected with 3 potential employers. Thank you so much!', date: '2026-01-15' },
  { name: 'Liam Anderson', email: 'liam.a@email.com', subject: 'Question about dues', body: 'What are the annual membership dues and what benefits do members receive?', date: '2026-01-15' },
  { name: 'Maya Patel', email: 'maya.patel@business.com', subject: 'Increase donation', body: 'I currently donate $50 monthly. I would like to increase it to $100 per month.', date: '2026-01-16' },
  { name: 'Noah Davis', email: 'noah.d@alumni.edu', subject: 'Address change', body: 'Please update my mailing address to 456 Oak Street, Boston, MA 02101.', date: '2026-01-16' },
  { name: 'Olivia Garcia', email: 'olivia.g@yahoo.com', subject: 'Disappointed member', body: 'I have been a member for 10 years but the quality of events has declined significantly. Very disappointed.', date: '2026-01-16' },
  { name: 'Peter Miller', email: 'peter.m@company.org', subject: 'Mentorship interest', body: 'I am interested in being a mentor for current students. What is the time commitment?', date: '2026-01-16' },
  { name: 'Quinn Taylor', email: 'q.taylor@mail.net', subject: 'Website feedback', body: 'Your new website looks great! Much easier to navigate than the old one. Nice job!', date: '2026-01-17' },
  { name: 'Rachel Moore', email: 'rachel.moore@outlook.com', subject: 'Stop calling me', body: 'I have asked 5 times to be removed from your calling list but you keep calling. This is harassment!', date: '2026-01-17' },
  { name: 'Sam Jackson', email: 'sam.j@gmail.com', subject: 'Reunion question', body: 'Is there a 20-year reunion being planned? I would love to attend if there is one.', date: '2026-01-17' },
  { name: 'Tina Liu', email: 'tina.liu@tech.com', subject: 'Grateful alumni', body: 'The alumni network helped me land my dream job. I am so grateful for this community!', date: '2026-01-17' },
  { name: 'Uma Singh', email: 'uma.singh@provider.io', subject: 'Event was too expensive', body: 'The ticket price for the gala was way too high. Many alumni cannot afford $500 per ticket.', date: '2026-01-18' },
  { name: 'Victor Cruz', email: 'v.cruz@email.com', subject: 'Job posting request', body: 'Can I post a job opening on the alumni job board? My company is hiring.', date: '2026-01-18' },
  { name: 'Wendy Park', email: 'wendy.p@company.net', subject: 'Outstanding service', body: 'Your staff member Jennifer was so helpful when I called. Outstanding customer service!', date: '2026-01-18' },
  { name: 'Xavier Green', email: 'xavier.g@alumni.org', subject: 'No longer supporting', body: 'After the recent changes in leadership, I will no longer be supporting the alumni association.', date: '2026-01-18' },
  { name: 'Yuki Tanaka', email: 'yuki.t@mail.com', subject: 'Scholarship application', body: 'How can my daughter apply for the alumni scholarship? She is a high school senior.', date: '2026-01-19' },
  { name: 'Zoe Adams', email: 'zoe.adams@gmail.com', subject: 'Love the newsletter!', body: 'I love reading the monthly alumni newsletter. It keeps me connected to the university. Thank you!', date: '2026-01-19' },
  { name: 'Aaron Bell', email: 'aaron.bell@yahoo.com', subject: 'Privacy concern', body: 'How is my personal data being used? I want to make sure my information is protected.', date: '2026-01-19' },
  { name: 'Bella Hayes', email: 'bella.h@outlook.com', subject: 'Pledge fulfillment', body: 'I pledged $5000 last year. Please send me the payment schedule and instructions.', date: '2026-01-19' },
  { name: 'Chris Murphy', email: 'chris.m@business.com', subject: 'Rude staff member', body: 'The person who answered the phone yesterday was incredibly rude and unprofessional. I demand an apology.', date: '2026-01-20' },
  { name: 'Diana Foster', email: 'd.foster@tech.io', subject: 'Directory access', body: 'How do I access the online alumni directory? I want to reconnect with old classmates.', date: '2026-01-20' },
  { name: 'Ethan Price', email: 'ethan.p@email.net', subject: 'Fantastic program', body: 'The young alumni program has been fantastic! Great events and networking opportunities. Keep it up!', date: '2026-01-20' },
  { name: 'Fiona Ward', email: 'fiona.w@alumni.edu', subject: 'Billing error', body: 'I was charged twice for my membership. Please refund the duplicate charge immediately.', date: '2026-01-20' },
  { name: 'George Turner', email: 'g.turner@company.org', subject: 'Legacy gift', body: 'I would like to include the university in my will. Who should I contact about planned giving?', date: '2026-01-21' },
  { name: 'Hannah Scott', email: 'hannah.s@mail.com', subject: 'Event conflict', body: 'The homecoming date conflicts with another major event. Can you consider changing it?', date: '2026-01-21' },
  { name: 'Ian Cooper', email: 'ian.c@provider.net', subject: 'Thank you for everything', body: 'As I retire, I want to thank the alumni office for decades of wonderful events and connections. You made a difference!', date: '2026-01-21' },
  { name: 'Julia Rivera', email: 'julia.r@gmail.com', subject: 'Update credit card', body: 'I need to update my credit card information for my monthly donation. How do I do that?', date: '2026-01-21' },
  { name: 'Kevin Zhang', email: 'kevin.z@yahoo.com', subject: 'Worst event ever', body: 'The networking event was the worst I have ever attended. Disorganized, crowded, and waste of time.', date: '2026-01-22' },
  { name: 'Laura Bennett', email: 'laura.b@outlook.com', subject: 'Speaking opportunity', body: 'I would be interested in speaking at an alumni event about entrepreneurship. Are there opportunities?', date: '2026-01-22' },
  { name: 'Mark Phillips', email: 'mark.p@business.net', subject: 'Exceeded expectations', body: 'The alumni weekend exceeded all my expectations. Every detail was perfect. Congratulations!', date: '2026-01-22' },
  { name: 'Nina Coleman', email: 'nina.c@tech.com', subject: 'Stop sending mail', body: 'Please stop sending physical mail to my address. I only want electronic communications.', date: '2026-01-22' },
  { name: 'Oscar Reed', email: 'oscar.r@email.io', subject: 'Class gift campaign', body: 'I want to organize a class gift campaign for our 25th reunion. Can you help?', date: '2026-01-23' },
  { name: 'Penny Brooks', email: 'penny.b@alumni.org', subject: 'Confused about benefits', body: 'I am confused about what benefits come with membership. Can you send me a list?', date: '2026-01-23' },
  { name: 'Quincy Howard', email: 'q.howard@company.com', subject: 'Horrible communication', body: 'Your communication has been horrible. I sent 3 emails with no response. Completely unprofessional.', date: '2026-01-23' },
  { name: 'Rosa Flores', email: 'rosa.f@mail.net', subject: 'Regional chapter', body: 'Is there a regional alumni chapter in Seattle? I recently moved here.', date: '2026-01-23' },
  { name: 'Steve Morgan', email: 'steve.m@provider.com', subject: 'Inspired by speaker', body: 'I was so inspired by the keynote speaker at the conference. Thank you for bringing such great talent!', date: '2026-01-24' },
  { name: 'Tracy Butler', email: 'tracy.b@gmail.com', subject: 'Duplicate mailings', body: 'I am receiving duplicate mailings at my address. Please fix your mailing list.', date: '2026-01-24' },
  { name: 'Ulysses Gray', email: 'ulysses.g@yahoo.com', subject: 'Cancel recurring donation', body: 'Please cancel my recurring monthly donation effective immediately. Do not charge my card again.', date: '2026-01-24' },
  { name: 'Vera Hughes', email: 'vera.h@outlook.com', subject: 'Networking success', body: 'Thanks to the alumni network, I found my co-founder and we just launched our startup!', date: '2026-01-24' },
  { name: 'Wade Russell', email: 'wade.r@business.io', subject: 'Data breach concern', body: 'I heard there was a data breach. Was my personal information compromised? This is very concerning.', date: '2026-01-25' },
  { name: 'Xena Powell', email: 'xena.p@tech.net', subject: 'Great app!', body: 'The new alumni mobile app is fantastic! So easy to find events and connect with people.', date: '2026-01-25' },
];

async function test50Emails() {
  const startTime = Date.now();

  try {
    Logger.info('=== TESTING 50 EMAILS ===\n');

    const sheetsService = new SheetsService();
    const aiService = new AIService();

    await sheetsService.initialize();

    // Get initial count
    const beforeResponse = await sheetsService.sheets.spreadsheets.values.get({
      spreadsheetId: sheetsService.spreadsheetId,
      range: 'Sheet1!A:F',
    });
    const beforeCount = beforeResponse.data.values?.length || 0;

    Logger.info(`Starting row count: ${beforeCount}`);
    Logger.info(`Processing ${mockEmails.length} emails...\n`);

    let processedCount = 0;
    let positiveCount = 0;
    let negativeCount = 0;
    let donateIntentCount = 0;
    let withdrawalIntentCount = 0;

    // Process all emails
    for (let i = 0; i < mockEmails.length; i++) {
      const email = mockEmails[i];

      if (i % 10 === 0) {
        Logger.info(`Progress: ${i}/${mockEmails.length} emails processed...`);
      }

      // Analyze
      const analysis = await aiService.analyzeSentimentAndIntent(email.body, email.subject);

      // Track stats
      if (analysis.sentiment === 'positive') positiveCount++;
      if (analysis.sentiment === 'negative') negativeCount++;
      if (analysis.intent === 'donate_intent') donateIntentCount++;
      if (analysis.intent === 'withdrawal_intent') withdrawalIntentCount++;

      // Add to sheet
      await sheetsService.appendRow({
        date: new Date(email.date),
        alumName: email.name,
        alumEmail: email.email,
        sentiment: analysis.sentiment,
        assignedStaff: '',
        summary: analysis.summary,
      });

      processedCount++;

      // Small delay to avoid overwhelming the system
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    // Get final count
    const afterResponse = await sheetsService.sheets.spreadsheets.values.get({
      spreadsheetId: sheetsService.spreadsheetId,
      range: 'Sheet1!A:F',
    });
    const afterCount = afterResponse.data.values?.length || 0;

    const duration = ((Date.now() - startTime) / 1000).toFixed(2);

    Logger.success('\n=== TEST COMPLETE ===');
    Logger.success(`✓ Processed: ${processedCount} emails`);
    Logger.success(`✓ Duration: ${duration} seconds`);
    Logger.success(`✓ Rows before: ${beforeCount}`);
    Logger.success(`✓ Rows after: ${afterCount}`);
    Logger.success(`✓ New rows added: ${afterCount - beforeCount}`);

    Logger.info('\n=== SENTIMENT BREAKDOWN ===');
    Logger.info(`Positive: ${positiveCount} (${((positiveCount/processedCount)*100).toFixed(1)}%)`);
    Logger.info(`Negative: ${negativeCount} (${((negativeCount/processedCount)*100).toFixed(1)}%)`);

    Logger.info('\n=== INTENT BREAKDOWN ===');
    Logger.info(`Donate Intent: ${donateIntentCount} (${((donateIntentCount/processedCount)*100).toFixed(1)}%)`);
    Logger.info(`Withdrawal Intent: ${withdrawalIntentCount} (${((withdrawalIntentCount/processedCount)*100).toFixed(1)}%)`);

    Logger.success(`\n✓✓✓ View your sheet:\nhttps://docs.google.com/spreadsheets/d/${sheetsService.spreadsheetId}/edit`);

    // Show sample of summaries
    Logger.info('\n=== SAMPLE SUMMARIES (First 5) ===');
    const finalRows = afterResponse.data.values;
    for (let i = Math.max(1, afterCount - 5); i < afterCount; i++) {
      const row = finalRows[i];
      Logger.info(`${row[1]}: "${row[5]}"`);
    }

  } catch (error) {
    Logger.error('Test failed', error);
    throw error;
  }
}

test50Emails()
  .then(() => {
    Logger.success('\n✓ All 50 emails processed successfully!');
    process.exit(0);
  })
  .catch((error) => {
    process.exit(1);
  });
