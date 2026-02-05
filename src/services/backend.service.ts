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

  // Use relative path if apiUrl is not set (best for Docker/Monoliths)
  private apiUrl = environment.apiUrl
    ? `${environment.apiUrl}/api/message`
    : '/api/message';

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
            return {
              reply: response.reply,
              scamDetected: response.scamDetected ?? true,
              confidenceScore: response.confidenceScore ?? 100,
              agentNotes: response.agentNotes ?? "• Monitoring via Python API",
              extractedIntelligence: response.extractedIntelligence ?? {
                confidence: 100,
                bankAccounts: [],
                upiIds: [],
                phishingLinks: [],
                phoneNumbers: [],
                suspiciousKeywords: [],
                socialEngineeringTactics: [],
                falseExpertise: false
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