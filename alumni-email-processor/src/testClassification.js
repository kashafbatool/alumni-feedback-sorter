import { AIService } from './services/aiService.js';
import { Logger } from './utils/logger.js';
import { SheetsService } from './services/sheetsService.js';
import { config } from './utils/config.js';

const testEmails = [
  {
    name: 'Jennifer Martinez',
    email: 'jennifer.martinez@gmail.com',
    subject: 'Website donation issue',
    body: "I've been trying to donate on your website for 20 minutes but it keeps crashing. Can someone call me?",
    date: '2026-01-12',
  },
  {
    name: 'David Chen',
    email: 'dchen@outlook.com',
    subject: 'Thank you for scholarship',
    body: "Thank you so much for the scholarship! It changed my life and I'm forever grateful.",
    date: '2026-01-12',
  },
  {
    name: 'Amanda Foster',
    email: 'amanda.foster@business.com',
    subject: 'Partnership meeting request',
    body: 'Can we schedule a meeting next week to discuss partnership opportunities?',
    date: '2026-01-13',
  },
  {
    name: 'Marcus Thompson',
    email: 'mthompson78@yahoo.com',
    subject: 'Address update needed',
    body: 'I need to update my mailing address in your system. My new address is 123 Main St.',
    date: '2026-01-13',
  },
  {
    name: 'Patricia Rodriguez',
    email: 'p.rodriguez@email.com',
    subject: 'Complaint about staff',
    body: 'Your staff was incredibly rude when I called yesterday. This is unacceptable.',
    date: '2026-01-13',
  },
  {
    name: 'Kevin Liu',
    email: 'kevin.liu@alumni.edu',
    subject: 'Monthly donation inquiry',
    body: "I'm interested in making a monthly donation. What are my options?",
    date: '2026-01-13',
  },
  {
    name: 'Rachel Green',
    email: 'rachelg@hotmail.com',
    subject: 'Thank you',
    body: 'Just wanted to say thank you for all the amazing work you do in the community!',
    date: '2026-01-14',
  },
  {
    name: 'Brandon Mitchell',
    email: 'b.mitchell@domain.com',
    subject: 'Event feedback',
    body: "The event last week was poorly organized. The venue was too small and there wasn't enough food.",
    date: '2026-01-14',
  },
  {
    name: 'Lisa Anderson',
    email: 'lisa.anderson@gmail.com',
    subject: 'Donation receipt request',
    body: 'How do I access my donation receipt for tax purposes?',
    date: '2026-01-14',
  },
  {
    name: 'Christopher Davis',
    email: 'c.davis@example.com',
    subject: 'Volunteer interest',
    body: 'I would love to volunteer. Can someone contact me about opportunities?',
    date: '2026-01-14',
  },
  {
    name: 'Michelle Parker',
    email: 'mparker@mail.com',
    subject: 'Cancel monthly donation',
    body: 'Please cancel my monthly donation effective immediately.',
    date: '2026-01-15',
  },
  {
    name: 'James Wilson',
    email: 'jwilson@provider.net',
    subject: 'Unsubscribe',
    body: "I'm done with this organization. Remove me from all mailing lists.",
    date: '2026-01-15',
  },
  {
    name: 'Nicole Stevens',
    email: 'nicole.stevens@email.org',
    subject: 'No longer supporting',
    body: 'After this experience, I will no longer be supporting the alumni association.',
    date: '2026-01-15',
  },
  {
    name: 'Robert Taylor',
    email: 'rtaylor@university.edu',
    subject: 'Mixed feelings',
    body: "I'm unhappy with the direction you're taking, but I'll continue my monthly donation.",
    date: '2026-01-15',
  },
  {
    name: 'Samantha Brooks',
    email: 'sbrooks@company.com',
    subject: 'Increase donation',
    body: 'Can you help me increase my donation to $100 per month?',
    date: '2026-01-15',
  },
];

async function testClassification() {
  console.log('\n=== EMAIL CLASSIFICATION TEST ===\n');
  console.log('Testing how the system classifies different types of emails...\n');

  const aiService = new AIService();
  const results = [];

  for (let i = 0; i < testEmails.length; i++) {
    const email = testEmails[i];

    console.log(`\n[${i + 1}/${testEmails.length}] Processing: ${email.name}`);
    console.log(`Subject: ${email.subject}`);
    console.log(`Body: "${email.body}"`);

    const analysis = await aiService.analyzeSentimentAndIntent(email.body, email.subject);

    console.log(`→ Sentiment: ${analysis.sentiment.toUpperCase()}`);
    console.log(`→ Intent: ${analysis.intent}`);
    console.log(`→ Summary: ${analysis.summary.substring(0, 80)}...`);

    results.push({
      name: email.name,
      email: email.email,
      sentiment: analysis.sentiment,
      intent: analysis.intent,
      summary: analysis.summary,
    });
  }

  // Summary table
  console.log('\n\n=== CLASSIFICATION SUMMARY ===\n');
  console.log('%-25s %-35s %-12s %-20s', 'Name', 'Email', 'Sentiment', 'Intent');
  console.log('-'.repeat(100));

  results.forEach(r => {
    console.log('%-25s %-35s %-12s %-20s',
      r.name.substring(0, 24),
      r.email.substring(0, 34),
      r.sentiment,
      r.intent
    );
  });

  // Statistics
  const positive = results.filter(r => r.sentiment === 'positive').length;
  const negative = results.filter(r => r.sentiment === 'negative').length;
  const donateIntent = results.filter(r => r.intent === 'donate_intent').length;
  const withdrawalIntent = results.filter(r => r.intent === 'withdrawal_intent').length;
  const positiveIntent = results.filter(r => r.intent === 'positive_intent').length;
  const negativeIntent = results.filter(r => r.intent === 'negative_intent').length;

  console.log('\n=== STATISTICS ===');
  console.log(`Total emails: ${results.length}`);
  console.log(`\nSentiment breakdown:`);
  console.log(`  Positive: ${positive} (${((positive/results.length)*100).toFixed(1)}%)`);
  console.log(`  Negative: ${negative} (${((negative/results.length)*100).toFixed(1)}%)`);
  console.log(`\nIntent breakdown:`);
  console.log(`  Donate Intent: ${donateIntent} (${((donateIntent/results.length)*100).toFixed(1)}%)`);
  console.log(`  Withdrawal Intent: ${withdrawalIntent} (${((withdrawalIntent/results.length)*100).toFixed(1)}%)`);
  console.log(`  Positive Intent: ${positiveIntent} (${((positiveIntent/results.length)*100).toFixed(1)}%)`);
  console.log(`  Negative Intent: ${negativeIntent} (${((negativeIntent/results.length)*100).toFixed(1)}%)`);

  // Ask if user wants to save to sheet
  console.log('\n\n=== SAVE TO GOOGLE SHEETS? ===');
  console.log('Would you like to save these results to your Google Sheet?');
  console.log('Run: node src/saveClassificationTest.js');

  return results;
}

testClassification()
  .then(() => {
    console.log('\n✓ Classification test complete!\n');
    process.exit(0);
  })
  .catch((error) => {
    Logger.error('Test failed', error);
    process.exit(1);
  });
