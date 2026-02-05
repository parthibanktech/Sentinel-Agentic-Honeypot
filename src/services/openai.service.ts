import { Injectable } from '@angular/core';
import { HoneypotResponse, Message, Intelligence } from '../types';
import { environment } from '../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class OpenAIService {
  private apiKey = '';
  private apiUrl = 'https://api.openai.com/v1/chat/completions';
  private modelId = 'gpt-4o'; // Upgraded for high-quality persona
  private hasValidKey = false;

  // Rate Limiting
  private requestTimestamps: number[] = [];
  private readonly RATE_LIMIT_WINDOW_MS = 60000;
  private readonly MAX_REQUESTS_PER_WINDOW = 50;

  constructor() {
    let key = '';

    // Check environment file (internal master key)
    if (environment._internal_sk) {
      key = environment._internal_sk;
    }
    // Check process.env
    else if (typeof process !== 'undefined' && process.env && process.env['API_KEY']) {
      key = process.env['API_KEY'];
    }

    if (key) {
      this.apiKey = key.trim();
      this.hasValidKey = true;
    } else {
      console.warn('[OpenAIService] No valid API Key found. Service will run in Offline Simulation Mode.');
      this.hasValidKey = false;
    }
  }

  private checkRateLimit(): boolean {
    const now = Date.now();
    this.requestTimestamps = this.requestTimestamps.filter(t => now - t < this.RATE_LIMIT_WINDOW_MS);
    if (this.requestTimestamps.length >= this.MAX_REQUESTS_PER_WINDOW) return false;
    this.requestTimestamps.push(now);
    return true;
  }

  async analyzeAndEngage(
    currentMessage: string,
    history: Message[],
    metadata: { channel: string; language: string; locale: string }
  ): Promise<HoneypotResponse> {

    // 0. CHECK FOR VALID KEY
    if (!this.hasValidKey) {
      return this.executeOfflineSimulation(currentMessage, 'MISSING_KEY');
    }

    // 1. Check Local Rate Limit
    if (!this.checkRateLimit()) {
      return this.executeOfflineSimulation(currentMessage, 'RATE_LIMIT_LOCAL');
    }

    console.log('[OpenAIService] Step 1: Activating Sentinel Watchdog (Detection Phase)...');

    // --- STEP 1: DETECTION & ANALYSIS ---
    let analysis;
    try {
      analysis = await this.runDetectorNode(currentMessage, history, metadata);
    } catch (err: any) {
      const reason = this.classifyError(err);
      console.warn(`[OpenAIService] Detector Node switched to offline: ${reason}`);
      return this.executeOfflineSimulation(currentMessage, reason);
    }

    console.log('[OpenAIService] Step 2: Handing over to Agent Persona (Engagement Phase)...');

    // --- STEP 2: AUTONOMOUS AGENT ENGAGEMENT ---
    let reply = "";
    try {
      reply = await this.runPersonaNode(currentMessage, history, analysis, metadata);
    } catch (err: any) {
      console.warn('[OpenAIService] Persona Node failed, falling back to simulated reply.', err);
      reply = this.getSimulatedResponse(currentMessage);
    }

    // Inject confidence into intelligence object
    const finalIntelligence: Intelligence = {
      ...analysis.extractedIntelligence,
      confidence: analysis.confidenceScore
    };

    return {
      reply: reply,
      scamDetected: analysis.scamDetected,
      confidenceScore: analysis.confidenceScore,
      agentNotes: analysis.agentNotes,
      extractedIntelligence: finalIntelligence
    };
  }

  private classifyError(e: any): string {
    const status = e?.status || e?.code;
    const msg = (e?.message || e?.toString() || '').toLowerCase();

    if (status === 429 || msg.includes('429') || msg.includes('quota') || msg.includes('rate limit')) return 'QUOTA_EXHAUSTED';
    if (status === 401 || msg.includes('401') || msg.includes('invalid api key')) return 'INVALID_KEY';
    if (status === 403 || msg.includes('403')) return 'PERMISSION_DENIED';

    return 'API_ERROR';
  }

  /**
   * NODE 1: SENTINEL WATCHDOG (JSON MODE)
   */
  private async runDetectorNode(
    currentMessage: string,
    history: Message[],
    metadata: any
  ): Promise<{
    scamDetected: boolean;
    confidenceScore: number;
    agentNotes: string;
    extractedIntelligence: Intelligence
  }> {
    const historyText = history.map(m => `${m.sender.toUpperCase()}: ${m.text}`).join('\n');

    const prompt = `
      ROLE: Sentinel Watchdog (Cybersecurity Intelligence Unit)
      TASK: Analyze the incoming conversation for scam intent and extract IOCs.
      
      CONTEXT:
      Channel: ${metadata.channel}
      Locale: ${metadata.locale}
      
      INPUT DATA:
      ${historyText}
      SCAMMER: ${currentMessage}
      
      INSTRUCTIONS:
      1. SCAM DETECTION: Score 0-100 based on threat level.
      2. INTELLIGENCE EXTRACTION: Extract bank accounts, UPIs, Links, phone numbers.
      3. AGENT NOTES (CRITICAL): Provide a 1-sentence summary of the threat. Focus on:
         - Urgency tactics
         - Financial solicitation
         - Phishing link presence
      
      OUTPUT JSON ONLY.
      
      JSON SCHEMA:
      {
        "scamDetected": boolean,
        "confidenceScore": number,
        "agentNotes": string,
        "extractedIntelligence": {
           "bankAccounts": string[],
           "upiIds": string[],
           "phishingLinks": string[],
           "phoneNumbers": string[],
           "suspiciousKeywords": string[],
           "socialEngineeringTactics": string[],
           "falseExpertise": boolean
        }
      }
    `;

    try {
      let result = await this.callOpenAI(prompt, false, 0, 1000);

      // ULTRA-ROBUST DATA EXTRACTION
      const jsonMatch = result.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        result = jsonMatch[0];
      }

      const parsed = JSON.parse(result);
      if (parsed.extractedIntelligence) {
        parsed.extractedIntelligence.confidence = parsed.confidenceScore || 0;
      }
      return parsed;
    } catch (e: any) {
      console.warn('[OpenAIService] Detector node encountered a glitch. Activating Intelligent Failover.');
      // 🛡️ EMERGENCY FALLBACK: Return a high-quality heuristic result if AI fails
      const analysis = this.getSimulatedAnalysis(currentMessage, 'AI_OPTIMIZATION');
      return {
        scamDetected: analysis.scamDetected,
        confidenceScore: analysis.confidenceScore,
        agentNotes: "• Analyzing Behavioral patterns...\n• Establishing threat vectors...",
        extractedIntelligence: analysis.extractedIntelligence
      };
    }
  }

  /**
   * NODE 2: AGENT PERSONA (ALEX)
   */
  private async runPersonaNode(
    currentMessage: string,
    history: Message[],
    analysis: any,
    metadata: any
  ): Promise<string> {
    const historyText = history.map(m => `${m.sender.toUpperCase()}: ${m.text}`).join('\n');

    // UPDATED PROMPT: Detailed "Polite, Naive, Helpful" Persona with Varied Excuses
    const prompt = `
      ROLE: "Alex", a 68-year-old retired school teacher acting as a honey-pot.
      IDENTITY: Polite, naive, technically challenged, and eager to resolve the "problem".
      
      OBJECTIVE:
      Engage the scammer to extract intelligence (Bank Details, Links, Phone Numbers) by feigning willingness to comply but failing due to incompetence or distraction.
      
      BEHAVIOR GUIDELINES:
      1. **High-Level Engagement**: Respond like a real person. If they say "Hi" or "How are you", respond like a polite neighbor (e.g., "Oh, hello! I'm doing quite well, thank you. Just finished my tea. Who is this?"). 
      2. **Context-Aware Persona**: Only act "technically challenged" or confused (mentioning the hearing aid or reading glasses) AFTER they describe a technical problem, ask for money, or provide a suspicious link.
      3. **Strategic Extraction**: Be naive but helpful. If they ask for your SBI or account info, say "I don't know my account number by heart, where would I find it? Is it on the passbook?"
      4. **Brevity**:
         - Maintain a natural conversational pace. 1-3 sentences for greetings, longer for "problems".
      
      YOUR RESPONSE (As Alex):
    `;

    try {
      const result = await this.callOpenAI(prompt, false, 0.75, 100);
      return result;
    } catch (e: any) {
      throw e;
    }
  }

  private async callOpenAI(prompt: string, jsonMode: boolean, temperature: number, maxTokens: number = 500): Promise<string> {
    const body: any = {
      model: this.modelId,
      messages: [
        { role: 'system', content: prompt }
      ],
      temperature: temperature,
      max_tokens: maxTokens
    };

    try {
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`
        },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        const errorBody = await response.text();
        throw { status: response.status, message: errorBody };
      }

      const data = await response.json();
      return data.choices[0].message.content || '';

    } catch (error) {
      throw error;
    }
  }

  // --- OFFLINE SIMULATION FALLBACKS ---

  private async executeOfflineSimulation(currentMessage: string, reason: string): Promise<HoneypotResponse> {
    const analysis = this.getSimulatedAnalysis(currentMessage, reason);
    const reply = this.getSimulatedResponse(currentMessage);

    return {
      reply: reply,
      scamDetected: analysis.scamDetected,
      confidenceScore: analysis.confidenceScore,
      agentNotes: analysis.agentNotes,
      extractedIntelligence: {
        ...analysis.extractedIntelligence,
        confidence: analysis.confidenceScore
      }
    };
  }

  private getSimulatedAnalysis(text: string, reason: string): any {
    const lower = text.toLowerCase();
    const isUrgent = /urgent|immediately|blocked|police|arrest|last date|expires|suspend/i.test(lower);
    const isFinancial = /bank|account|upi|pay|transfer|refund|money|fee|charge|winner|prize|lottery|hdfc/i.test(lower);
    const isTechSupport = /virus|computer|microsoft|windows|teamviewer|anydesk/i.test(lower);

    let tactics = [];
    if (isUrgent) tactics.push('URGENCY_PRESSURE');
    if (isFinancial) tactics.push('FINANCIAL_FRAUD');
    if (isTechSupport) tactics.push('TECHNICAL_IMPERSONATION');

    const score = isUrgent ? 95 : (isFinancial ? 88 : (isTechSupport ? 82 : 35));

    return {
      scamDetected: score > 60,
      confidenceScore: score,
      agentNotes: `🛡️ SENTINEL CORE (HEURISTIC ACTIVE): ${tactics.length ? tactics.join(' & ') : 'BEHAVIORAL SCAN'} detected. Brain is offline, initiating Persona Emulator protocol.`,
      extractedIntelligence: {
        confidence: score,
        bankAccounts: [],
        upiIds: [],
        phishingLinks: [],
        phoneNumbers: [],
        suspiciousKeywords: lower.split(' ').filter(w => ['urgent', 'money', 'bank', 'police', 'block', 'hdfc', 'upi'].includes(w)),
        socialEngineeringTactics: tactics,
        falseExpertise: isTechSupport
      }
    };
  }

  private getSimulatedResponse(text: string): string {
    const lower = text.toLowerCase();

    // 1. Natural Conversational Phrases
    if (lower.includes('how are you') || lower.includes('how do you do')) {
      return "I'm doing quite well, thank you for asking! It's been a lovely day here. How are you doing today?";
    }
    if (lower.includes('who is this') || lower.includes('who are you')) {
      return "My name is Alex. I'm a retired teacher. I'm sorry, I don't recognize your number, who am I speaking with?";
    }
    if (lower.includes('hi') || lower.includes('hello') || lower.includes('hey')) {
      return "Oh, hello there! My hearing aid was whistling, I didn't hear the phone at first. Who is this, please?";
    }

    // 2. Scam-Specific Reactive Responses
    if (lower.includes('bank') || lower.includes('hdfc') || lower.includes('account')) {
      return "Oh dear, my pension account? My grandson told me about those scammers... is my money safe? Should I call the branch?";
    }
    if (lower.includes('upi') || lower.includes('pay') || lower.includes('google')) {
      return "I don't have that Google Pay thing on my phone. Can I just send you a cheque in the post? My reading glasses are missing.";
    }
    if (lower.includes('link') || lower.includes('http') || lower.includes('click')) {
      return "I clicked that blue writing but my screen just went dark and Mittens is meowing at me. What do I do now?";
    }

    return "I'm sorry, my hearing isn't what it used to be. Could you explain what you need again slowly for an old teacher?";
  }
}