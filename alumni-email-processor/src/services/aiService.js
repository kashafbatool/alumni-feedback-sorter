import OpenAI from 'openai';
import { config } from '../utils/config.js';
import { Logger } from '../utils/logger.js';

export class AIService {
  constructor() {
    if (config.ai.openaiApiKey) {
      this.client = new OpenAI({ apiKey: config.ai.openaiApiKey });
      this.provider = 'openai';
    } else if (config.ai.anthropicApiKey) {
      // Note: If using Anthropic, you'd need to import their SDK
      // For now, we'll focus on OpenAI implementation
      Logger.warn('Anthropic API key detected but not implemented. Using OpenAI as default.');
      this.provider = null;
    } else {
      this.provider = null;
      Logger.warn('No AI API key configured. Sentiment analysis will use fallback logic.');
    }
  }

  async analyzeSentimentAndIntent(emailBody, subject) {
    if (!this.client) {
      return this.fallbackAnalysis(emailBody, subject);
    }

    try {
      const prompt = `Analyze this alumni email and provide:
1. Sentiment (positive or negative)
2. Intent (choose one: positive_intent, negative_intent, donate_intent, withdrawal_intent)
3. A brief summary (2-3 sentences max)

Email Subject: ${subject}
Email Body: ${emailBody}

Respond in JSON format:
{
  "sentiment": "positive" or "negative",
  "intent": "positive_intent" or "negative_intent" or "donate_intent" or "withdrawal_intent",
  "summary": "your summary here"
}

Guidelines:
- positive_intent: General positive feedback, praise, gratitude
- negative_intent: Complaints, criticism, concerns
- donate_intent: Mentions of donations, giving, financial support
- withdrawal_intent: Requests to unsubscribe, remove from lists, or disconnect`;

      const response = await this.client.chat.completions.create({
        model: 'gpt-4o-mini',
        messages: [
          {
            role: 'system',
            content: 'You are an AI assistant that analyzes alumni emails for sentiment and intent. Always respond with valid JSON.',
          },
          {
            role: 'user',
            content: prompt,
          },
        ],
        temperature: 0.3,
        response_format: { type: 'json_object' },
      });

      const result = JSON.parse(response.choices[0].message.content);
      Logger.info('AI analysis completed', { sentiment: result.sentiment, intent: result.intent });

      return {
        sentiment: result.sentiment,
        intent: result.intent,
        summary: result.summary,
      };
    } catch (error) {
      Logger.error('Error in AI analysis, using fallback', error);
      return this.fallbackAnalysis(emailBody, subject);
    }
  }

  fallbackAnalysis(emailBody, subject) {
    const text = `${subject} ${emailBody}`.toLowerCase();

    // Simple keyword-based sentiment analysis
    const positiveKeywords = [
      'thank', 'great', 'wonderful', 'excellent', 'appreciate', 'grateful',
      'love', 'amazing', 'fantastic', 'outstanding', 'impressed', 'happy',
    ];

    const negativeKeywords = [
      'disappointed', 'terrible', 'horrible', 'upset', 'angry', 'frustrated',
      'complaint', 'issue', 'problem', 'concern', 'dissatisfied', 'unacceptable',
      'rude', 'poorly', 'crashing', 'done with', 'no longer',
    ];

    const donateKeywords = [
      'donate', 'donation', 'contribute', 'contribution', 'gift', 'giving',
      'pledge', 'support', 'fund', 'endowment', 'scholarship', 'increase my donation',
    ];

    const withdrawalKeywords = [
      'unsubscribe', 'remove', 'opt out', 'stop sending', 'no longer',
      'take me off', 'cancel', 'delete my',
    ];

    let positiveCount = 0;
    let negativeCount = 0;
    let donateCount = 0;
    let withdrawalCount = 0;

    positiveKeywords.forEach(keyword => {
      if (text.includes(keyword)) positiveCount++;
    });

    negativeKeywords.forEach(keyword => {
      if (text.includes(keyword)) negativeCount++;
    });

    donateKeywords.forEach(keyword => {
      if (text.includes(keyword)) donateCount++;
    });

    withdrawalKeywords.forEach(keyword => {
      if (text.includes(keyword)) withdrawalCount++;
    });

    let intent;
    if (withdrawalCount > 0) {
      intent = 'withdrawal_intent';
    } else if (donateCount > 0) {
      intent = 'donate_intent';
    } else if (negativeCount > positiveCount) {
      intent = 'negative_intent';
    } else {
      intent = 'positive_intent';
    }

    const sentiment = negativeCount > positiveCount ? 'negative' : 'positive';

    // Create a concise summary (max 100 chars)
    const summary = this.createShortSummary(emailBody, subject);

    Logger.info('Fallback analysis completed', { sentiment, intent });

    return { sentiment, intent, summary };
  }

  createShortSummary(emailBody, subject) {
    // Create a short, concise summary
    const text = emailBody.trim();

    // Extract the first sentence or key point
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
    let summary = sentences[0]?.trim() || text;

    // If still too long, extract key action/request
    if (summary.length > 100) {
      // Look for key phrases
      const keyPhrases = [
        /trying to (.*?)(?:\.|$)/i,
        /want to (.*?)(?:\.|$)/i,
        /need to (.*?)(?:\.|$)/i,
        /interested in (.*?)(?:\.|$)/i,
        /would like to (.*?)(?:\.|$)/i,
        /can you (.*?)(?:\.|$)/i,
        /please (.*?)(?:\.|$)/i,
        /how do i (.*?)(?:\.|$)/i,
      ];

      for (const pattern of keyPhrases) {
        const match = text.match(pattern);
        if (match && match[1]) {
          summary = match[0].trim();
          break;
        }
      }

      // If still too long, just truncate at word boundary
      if (summary.length > 100) {
        summary = summary.substring(0, 97);
        const lastSpace = summary.lastIndexOf(' ');
        if (lastSpace > 50) {
          summary = summary.substring(0, lastSpace) + '...';
        } else {
          summary = summary + '...';
        }
      }
    }

    return summary;
  }
}
