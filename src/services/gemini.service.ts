import { Injectable } from '@angular/core';
import { HoneypotResponse, Message, Intelligence } from '../types';
import { environment } from '../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class GeminiService {
  // Frontend Gemini is disabled to focus on the Python Backend / OpenAI routing
  private hasValidKey = false;

  constructor() { }

  async analyzeAndEngage(
    currentMessage: string,
    history: Message[],
    metadata: { channel: string; language: string; locale: string }
  ): Promise<HoneypotResponse> {
    // Silently route to offline simulation if called
    return this.executeOfflineSimulation(currentMessage, 'BACKEND_ROUTING_ONLY');
  }

  private executeOfflineSimulation(currentMessage: string, reason: string): Promise<HoneypotResponse> {
    return Promise.resolve({
      reply: "I'm sorry, I'm a bit flustered. What was that?",
      scamDetected: false,
      confidenceScore: 0,
      agentNotes: "[Gemini Service: Offline - Routing to Backend]",
      extractedIntelligence: {
        confidence: 0, bankAccounts: [], upiIds: [], phishingLinks: [], phoneNumbers: [], suspiciousKeywords: [], socialEngineeringTactics: [], falseExpertise: false
      }
    });
  }
}