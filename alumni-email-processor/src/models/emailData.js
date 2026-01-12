export class EmailData {
  constructor({ date, alumName, alumEmail, sentiment, assignedStaff, summary, intent }) {
    this.date = date;
    this.alumName = alumName;
    this.alumEmail = alumEmail;
    this.sentiment = sentiment;
    this.assignedStaff = assignedStaff || '';
    this.summary = summary;
    this.intent = intent;
  }

  static fromGmailAndAnalysis(gmailData, aiAnalysis, assignedStaff) {
    return new EmailData({
      date: gmailData.date,
      alumName: gmailData.name,
      alumEmail: gmailData.from,
      sentiment: aiAnalysis.sentiment,
      assignedStaff: assignedStaff,
      summary: aiAnalysis.summary,
      intent: aiAnalysis.intent,
    });
  }

  toSheetRow() {
    return {
      date: this.date,
      alumName: this.alumName,
      alumEmail: this.alumEmail,
      sentiment: this.sentiment,
      assignedStaff: this.assignedStaff,
      summary: this.summary,
    };
  }
}
