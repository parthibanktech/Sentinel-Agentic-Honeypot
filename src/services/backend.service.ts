import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { HoneypotResponse, Message } from '../types';
import { lastValueFrom } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class BackendService {
  private http: HttpClient = inject(HttpClient);

  // Use relative path — works for both local dev and production (served by FastAPI)
  private apiUrl = environment.apiUrl
    ? `${environment.apiUrl}/api/message`
    : 'http://localhost:8001/api/message';

  private readonly API_KEY = environment.honey_pot;

  async analyzeAndEngage(
    currentMessage: string,
    history: Message[],
    metadata: { channel: string; language: string; locale: string; },
    sessionId: string = "session-" + Date.now()
  ): Promise<HoneypotResponse> {

    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'x-api-key': this.API_KEY
    });

    const apiHistory = history.map(msg => ({
      sender: msg.sender === 'agent' ? 'user' : 'scammer',
      text: msg.text,
      timestamp: msg.timestamp
    }));

    const payload = {
      sessionId: sessionId,
      message: {
        sender: "scammer",
        text: currentMessage,
        timestamp: Date.now()
      },
      conversationHistory: apiHistory,
      metadata: metadata
    };

    try {
      return await lastValueFrom(
        this.http.post<any>(this.apiUrl, payload, { headers }).pipe(
          map((response: any) => {
            // Backend now returns lean {status, reply} 
            // Derive scam detection from keywords heuristically for dashboard display
            const lower = currentMessage.toLowerCase();
            const allText = history.map(m => m.text).join(' ').toLowerCase() + ' ' + lower;

            const scamKeywords = ['bank', 'sbi', 'hdfc', 'upi', 'kyc', 'job', 'salary', 'investment',
              'block', 'verify', 'otp', 'police', 'cbi', 'arrest', 'lottery', 'prize',
              'customs', 'cashback', 'refund', 'click', 'link', 'urgent', 'compromise'];

            const isScam = scamKeywords.some(k => allText.includes(k));
            const confidence = isScam ? 85 + Math.min(15, history.length * 2) : 15;

            // Extract phone numbers for dashboard
            const phoneMatches = allText.match(/(?:\+?91[\s\-.]?)?[6-9]\d{9}/g) || [];
            // Extract UPI IDs (not emails)
            const upiMatches = allText.match(/[\w.\-]+@(?:ok\w+|ybl|paytm|upi|apl|ibl|axl)\b/gi) || [];
            // Extract links
            const linkMatches = allText.match(/https?:\/\/[^\s<>"']+/g) || [];
            // Extract bank accounts (10-18 digit numbers)
            const accountMatches = allText.match(/\b\d{10,18}\b/g) || [];
            // Filter accounts that are also phone numbers
            const phoneDigits = new Set(phoneMatches.map(p => p.replace(/\D/g, '').slice(-10)));
            const bankAccounts = accountMatches.filter(a => !phoneDigits.has(a.slice(-10)));

            // Detect tactics
            const tactics: string[] = [];
            if (/urgent|immediate|block|suspend/i.test(allText)) tactics.push('URGENCY');
            if (/police|cbi|arrest|warrant|court/i.test(allText)) tactics.push('AUTHORITY');
            if (/otp|verify|kyc|password/i.test(allText)) tactics.push('FEAR');
            if (/job|salary|earn|prize|lottery|win/i.test(allText)) tactics.push('GREED');

            return {
              reply: response.reply || "I'm sorry, can you explain that again?",
              scamDetected: isScam,
              confidenceScore: confidence,
              agentNotes: response.agentNotes || `Sentinel AI analyzing conversation. Confidence: ${confidence}%`,
              extractedIntelligence: {
                confidence: confidence,
                bankAccounts: [...new Set(bankAccounts)],
                upiIds: [...new Set(upiMatches)],
                phishingLinks: [...new Set(linkMatches)],
                phoneNumbers: [...new Set(phoneMatches)],
                suspiciousKeywords: [...new Set(scamKeywords.filter(k => allText.includes(k)))],
                socialEngineeringTactics: tactics,
                falseExpertise: /microsoft|windows|virus|teamviewer/i.test(allText)
              }
            } as HoneypotResponse;
          })
        )
      );
    } catch (error: any) {
      console.error('Backend API Error:', error);
      if (error.status === 401) {
        throw new Error('401 Unauthorized: Invalid API Key on Backend');
      }
      throw error;
    }
  }
}