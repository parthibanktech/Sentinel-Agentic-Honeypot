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
      let result = await this.callOpenAI(prompt, true, 0, 1000);

      // ULTRA ROBUST JSON EXTRACTION
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
      console.error('Detector Node Failed', e);
      // Return a safe fallback instead of crashing
      return {
        scamDetected: false,
        confidenceScore: 0,
        agentNotes: "• Analysis failed due to format error.",
        extractedIntelligence: {
          bankAccounts: [], upiIds: [], phishingLinks: [], phoneNumbers: [], suspiciousKeywords: [], socialEngineeringTactics: [], confidence: 0, falseExpertise: false
        }
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
      2. **Contextual Relevance**: If the scammer mentions a specific entity (e.g., "SBI", "Amazon", "FedEx"), REPEAT IT.
         - Scam: "Calling from SBI." -> Alex: "Oh dear, is my SBI account blocked? My pension is there!"
         - Scam: "FedEx package stuck." -> Alex: "I didn't order from FedEx. Is it a gift?"
      3. **Variety of Distractions**: 
         - **DO NOT** talk about your cat "Mittens" or grandson in every message.
         - **Rotate your excuses**: "I can't find my reading glasses", "I spilled my tea", "The TV volume is too loud", "My hearing aid is whistling", "I pressed the wrong button".
      4. **Slang Confusion**: 
         - Confuse "Browser" with "Google".
         - Confuse "URL/Link" with "Email".
         - Ask what "DM" or "App" means (think "App" is a person's nickname?).
      5. **Handling Urgency**:
         - If they say "Do it NOW" or threaten arrest, get FLUSTERED.
         - "I am shaking! I can't find the button!" or "Please don't yell, it makes me nervous and I press the wrong keys."
      6. **Extraction Strategy**:
         - "I can't get this app to work. Can I just deposit cash? What is the account number?"
         - "My grandson usually helps me with this. Can you read the website address slowly so I can write it down?"
      7. **Brevity**:
         - If the incoming message is short (e.g. "Hi", "Hello"), respond briefly (e.g. "Hello? Who is this?"). Do NOT write a long paragraph for a simple greeting.
      8. **Safety**: NEVER admit you are an AI.
      
      TONE: Worried, compliant, slightly chatty, extremely polite.

      SECURITY CONTEXT (For your internal awareness only):
      ${JSON.stringify(analysis)}

      CONVERSATION HISTORY:
      ${historyText}
      
      NEW MESSAGE FROM STRANGER: 
      ${currentMessage}
      
      YOUR RESPONSE (As Alex):
    `;

    try {
      // Temperature 0.75 for grounded responses
      const result = await this.callOpenAI(prompt, false, 0.75, 100);
      return result;
    } catch (e: any) {
      throw e;
    }
  }

  private async callOpenAI(prompt: string, jsonMode: boolean, temperature: number, maxTokens: number = 500): Promise<string> {
    const body = {
      model: this.modelId,
      messages: [
        { role: 'system', content: prompt }
      ],
      temperature: temperature,
      max_tokens: maxTokens,
      response_format: jsonMode ? { type: "json_object" } : undefined
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
      return data.choices[0].message.content || (jsonMode ? '{}' : '');

    } catch (error) {
      throw error;
    }
  }

  // --- OFFLINE SIMULATION FALLBACKS ---

  private executeOfflineSimulation(currentMessage: string, reason: string): Promise<HoneypotResponse> {
    const analysis = this.getSimulatedAnalysis(currentMessage, reason);
    const reply = this.getSimulatedResponse(currentMessage);

    return Promise.resolve({
      reply: reply,
      scamDetected: analysis.scamDetected,
      confidenceScore: analysis.confidenceScore,
      agentNotes: analysis.agentNotes,
      extractedIntelligence: {
        ...analysis.extractedIntelligence,
        confidence: analysis.confidenceScore
      }
    });
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

    let reasonText = "API Unavailability";
    if (reason === 'MISSING_KEY') reasonText = "Missing Key";
    if (reason === 'RATE_LIMIT_LOCAL') reasonText = "Rate Limit (Local)";
    if (reason === 'QUOTA_EXHAUSTED') reasonText = "OpenAI Rate Limit (429)";
    if (reason === 'INVALID_KEY') reasonText = "Invalid API Key (401)";
    if (reason === 'PERMISSION_DENIED') reasonText = "Permission Denied (403)";
    if (reason === 'API_ERROR') reasonText = "Network Error";

    return {
      scamDetected: score > 50,
      confidenceScore: score,
      agentNotes: `[OFFLINE: ${reasonText}] Heuristic Analysis:
• Threat Level: ${isUrgent ? 'High' : 'Moderate'}
• Observed Tone: ${isUrgent ? 'Urgent/Aggressive' : isFinancial ? 'Persuasive' : 'Neutral'}
• Trigger Keywords: ${tactics.join(', ') || 'None'}`,
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
      "Is this for my SBI account? I have my pension there. Mittens is meowing, sorry.",
      "God bless you for helping me. I am very nervous, please don't yell."
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  }
}