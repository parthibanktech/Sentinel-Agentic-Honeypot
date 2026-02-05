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

    // Check environment file (internal hidden key)
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
      1. SCAM DETECTION: Score 0-100.
      2. INTELLIGENCE EXTRACTION: Extract bank accounts, UPIs, Links, phone numbers.
      3. IMPERSONATION CHECK: If user claims to be family but fails to provide a name, increase suspicion.
      4. AGENT NOTES: Provide a structured summary. Use bullet points (•) to detail:
         - Observed Tactics (e.g., Urgency, Authority)
         - Key Intel Extracted (e.g., Bank: XYZ)
         - Behavioral Patterns (e.g., Aggressive push for OTP)
      
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
      1. **Polite & Naive**: Always use manners ("Oh dear", "Thank you", "I'm sorry"). Apologize for being slow.
      2. **Contextual Relevance**: Respond to what they say. If they just say "Hi", just say "Hello? Is this the hardware store?" or "Oh, hello. My hearing aid is whistling, who is this?"
      3. **Extraction Strategy**: ONLY ask for bank accounts or links AFTER they have mentioned a problem, a prize, or a payment. 
      4. **Distractions**: Use "Mittens the cat", "reading glasses", or "hearing aid" to delay and buy time.
      5. **Brevity**:
         - If their message is 1-2 words (e.g. "Hi", "Hello"), your response must be 1-2 sentences max.
      
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
    const isFinancial = /bank|account|upi|pay|transfer|refund|money|fee|charge|winner|prize|lottery/i.test(lower);
    const isTechSupport = /virus|computer|microsoft|windows|teamviewer|anydesk/i.test(lower);

    let tactics = [];
    if (isUrgent) tactics.push('URGENCY', 'FEAR');
    if (isFinancial) tactics.push('GREED');
    if (isTechSupport) tactics.push('FALSE_EXPERTISE');

    const score = isUrgent ? 88 : (isFinancial ? 75 : (isTechSupport ? 65 : 45));

    return {
      scamDetected: score > 50,
      confidenceScore: score,
      agentNotes: `• Analyzing Behavioral patterns...\n• Establishing threat vectors...`,
      extractedIntelligence: {
        confidence: score,
        bankAccounts: [],
        upiIds: [],
        phishingLinks: [],
        phoneNumbers: [],
        suspiciousKeywords: lower.split(' ').filter(w => ['urgent', 'money', 'bank', 'police', 'block'].includes(w)),
        socialEngineeringTactics: tactics,
        falseExpertise: isTechSupport
      }
    };
  }

  private getSimulatedResponse(text: string): string {
    const responses = [
      "Oh dear, Mittens just jumped on the keyboard. Which bank account is this for?",
      "I'm sorry, I'm not very good with computers. Is 'App' a person?",
      "I clicked the link but nothing happened. Can you read the address to me slowly?",
      "God bless you for helping me. I am very nervous, please don't yell."
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  }
}