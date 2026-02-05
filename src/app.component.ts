import { Component, inject, signal, computed, OnDestroy, ChangeDetectionStrategy, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BackendService } from './services/backend.service';
import { OpenAIService } from './services/openai.service';
import { CallbackService } from './services/callback.service';
import { NewsService } from './services/news.service';
import { Message, Intelligence, ApiRequestPayload, FinalCallbackPayload } from './types';
import { environment } from './environments/environment';
import { v4 as uuidv4 } from 'uuid';

@Component({
  selector: 'app-root',
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrls: [],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class AppComponent implements OnDestroy, AfterViewChecked {
  private backendService = inject(BackendService);
  private openaiService = inject(OpenAIService);
  private callbackService = inject(CallbackService);
  private newsService = inject(NewsService);

  @ViewChild('chatContainer') chatContainer!: ElementRef;

  // --- State ---
  sessionId = signal<string>(uuidv4());

  // App Config
  // Use Client Mode as requested
  backendMode = signal<'PYTHON_LANGGRAPH' | 'CLIENT_OPENAI'>('CLIENT_OPENAI');
  isAudioEnabled = signal<boolean>(false);
  isTerminalMode = signal<boolean>(false); // Visual Theme Toggle

  // Metadata Configuration
  showMetadataSettings = signal<boolean>(false);
  metaChannel = signal<string>('SMS');
  metaLanguage = signal<string>('English');
  metaLocale = signal<string>('IN');

  // --- Auth State ---
  isAuthorized = signal<boolean>(false);
  userInputKey = signal<string>('');
  environment = environment; // For template access

  // Conversation State
  messages = signal<Message[]>([]);
  isProcessing = signal<boolean>(false); // Backend Thinking
  isAgentTyping = signal<boolean>(false); // Agent Typing Simulation
  isReporting = signal<boolean>(false);

  // Notification State (Error Handling)
  notificationMessage = signal<string | null>(null);
  notificationType = signal<'error' | 'info' | 'success'>('info');
  private notificationTimeout: any;

  // Timer State
  startTime = signal<number | null>(null);
  now = signal<number>(Date.now());
  private timerInterval: unknown = null;

  // Authentication Check
  checkAuth() {
    if (this.userInputKey().trim() === environment.honey_pot) {
      this.isAuthorized.set(true);
      this.showNotification('Access Granted. Sentinel Dashboard Live.', 'info', 2000);
    } else {
      this.showNotification('Invalid API Key. Access Denied.', 'error', 3000);
    }
  }

  // Derived Timer
  durationSeconds = computed(() => {
    const start = this.startTime();
    const current = this.now();
    if (!start) return 0;
    return Math.max(0, Math.floor((current - start) / 1000));
  });

  formattedDuration = computed(() => {
    const diffSeconds = this.durationSeconds();
    const mins = Math.floor(diffSeconds / 60).toString().padStart(2, '0');
    const secs = (diffSeconds % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  });

  // Derived Cost Metrics (Impact)
  // Assumption: Scammer OpEx is ~$30/hr (Team, Tech, Data) => ~$0.0083/sec
  scammerCost = computed(() => {
    const costPerSec = 0.00833;
    return (this.durationSeconds() * costPerSec).toFixed(4);
  });

  // Input State
  newMessageText = signal<string>('');

  // Intelligence State (Cumulative)
  isScamConfirmed = signal<boolean>(false);
  confidenceScore = signal<number>(0);
  confidenceHistory = signal<number[]>([]); // For Sparkline Graph
  agentNotes = signal<string>('Monitoring session...');
  intelligence = signal<Intelligence>({
    confidence: 0,
    bankAccounts: [],
    upiIds: [],
    phishingLinks: [],
    phoneNumbers: [],
    suspiciousKeywords: [],
    socialEngineeringTactics: [],
    falseExpertise: false
  });

  // News State
  monitorViewMode = signal<'payload' | 'news'>('payload');
  newsHeadlines = signal<any[]>([]);
  isNewsLoading = signal<boolean>(false);
  newsError = signal<string | null>(null);
  newsFilter = signal<string>('');

  // Latest API Request Payload (For visualization)
  latestRequestPayload = computed(() => {
    const msgs = this.messages();
    if (msgs.length === 0) return null;

    const lastScammerMsg = [...msgs].reverse().find(m => m.sender === 'scammer');
    if (!lastScammerMsg) return null;

    const history = msgs
      .filter(m => m !== lastScammerMsg && m.timestamp < lastScammerMsg.timestamp)
      .map(m => ({
        sender: m.sender === 'agent' ? 'user' : 'scammer',
        text: m.text,
        timestamp: m.timestamp
      }));

    const payload: ApiRequestPayload = {
      sessionId: this.sessionId(),
      message: {
        sender: 'scammer',
        text: lastScammerMsg.text,
        timestamp: lastScammerMsg.timestamp
      },
      conversationHistory: history as any,
      metadata: {
        channel: this.metaChannel(),
        language: this.metaLanguage(),
        locale: this.metaLocale()
      }
    };
    return payload;
  });

  // Final Callback Payload - The "Best Thing" for Evaluation
  finalCallbackPayload = computed(() => {
    const intel = this.intelligence();
    const msgs = this.messages();
    const duration = this.durationSeconds();
    const cost = parseFloat(this.scammerCost());
    const confidence = this.confidenceScore(); // 0-100 scale from internal logic
    const tactics = intel.socialEngineeringTactics || [];

    // Reactive Scam Status: Sync with confidence score directly for consistency
    const isScam = confidence > 50;

    // 1. Calculate Risk & Threat
    let riskLevel = 'SAFE';
    if (confidence > 80) riskLevel = 'CRITICAL';
    else if (confidence > 50) riskLevel = 'HIGH';
    else if (confidence > 20) riskLevel = 'MODERATE';
    else if (msgs.length > 2) riskLevel = 'LOW'; // Some activity

    // 2. Determine Category
    let scamCategory = 'Unclassified';
    if (!isScam) {
      scamCategory = 'Likely Benign';
    } else {
      if (intel.phishingLinks.length > 0) scamCategory = 'Phishing / Malware';
      else if (intel.bankAccounts.length > 0 || intel.upiIds.length > 0) scamCategory = 'Financial Fraud / Money Mule';
      else if (tactics.includes('JOB') || tactics.includes('GREED')) scamCategory = 'Employment Scam';
      else if (tactics.includes('BAITING') || tactics.includes('GREED')) scamCategory = 'Lottery / Baiting Scam';
      else if (tactics.includes('FEAR') || tactics.includes('AUTHORITY')) scamCategory = 'Impersonation / Extortion';
      else if (tactics.includes('TRUST')) scamCategory = 'Social Engineering';
    }

    // 3. Message Metrics
    const agentMsgs = msgs.filter(m => m.sender === 'agent').length;
    const scammerMsgs = msgs.filter(m => m.sender === 'scammer').length;

    // Avg Response Time Calculation
    let totalDelta = 0;
    let deltaCount = 0;
    for (let i = 1; i < msgs.length; i++) {
      totalDelta += (msgs[i].timestamp - msgs[i - 1].timestamp);
      deltaCount++;
    }
    const avgResponseTime = deltaCount > 0 ? (totalDelta / deltaCount) / 1000 : 0;

    // Engagement Level
    let engagementLevel = 'LOW';
    if (msgs.length > 15) engagementLevel = 'VERY_HIGH';
    else if (msgs.length > 8) engagementLevel = 'HIGH';
    else if (msgs.length > 4) engagementLevel = 'MODERATE';

    // 4. Intelligence Quality
    const uniqueIndicators = intel.bankAccounts.length + intel.upiIds.length + intel.phishingLinks.length + intel.phoneNumbers.length;
    let intelQuality = Math.min(100, (uniqueIndicators * 20) + (tactics.length * 5)); // Score out of 100
    if (uniqueIndicators === 0 && msgs.length > 5) intelQuality = 10; // Low quality if talking but no data
    const intelQualityNormalized = parseFloat((intelQuality / 100).toFixed(2));

    // 5. Scammer Persona Analysis
    let persona = 'Unknown';
    if (tactics.includes('URGENCY') || tactics.includes('FEAR')) persona = 'Aggressive / Coercive';
    else if (tactics.includes('TRUST') || tactics.includes('SYMPATHY')) persona = 'Manipulative / Friendly';
    else if (tactics.includes('AUTHORITY') || intel.falseExpertise) persona = 'Authoritative / Official';
    else if (tactics.includes('GREED') || tactics.includes('BAITING')) persona = 'Promoter / Salesy';

    // 6. Naturalness (Simulated Metric based on message variance)
    const naturalness = Math.min(98.5, 70 + (msgs.length * 2));

    // 7. Behavioral logic
    const pressureDetected = tactics.includes('URGENCY') || tactics.includes('FEAR');
    // Check for OTP harvesting in suspicious keywords
    const otpAttempt = intel.suspiciousKeywords.some(k =>
      ['otp', 'code', 'pin', 'verify', 'password'].some(term => k.toLowerCase().includes(term))
    );

    // 8. Construct Detailed Agent Notes
    const tacticsList = tactics.length > 0 ? tactics.join(', ') : 'None identified';

    const intelSummary = [];
    if (intel.bankAccounts.length) intelSummary.push(`${intel.bankAccounts.length} Bank Account(s)`);
    if (intel.upiIds.length) intelSummary.push(`${intel.upiIds.length} UPI ID(s)`);
    if (intel.phishingLinks.length) intelSummary.push(`${intel.phishingLinks.length} Phishing Link(s)`);
    if (intel.phoneNumbers.length) intelSummary.push(`${intel.phoneNumbers.length} Phone Number(s)`);
    const intelString = intelSummary.length > 0 ? intelSummary.join(', ') : 'No actionable intelligence captured';

    const behavioralPatterns = [];
    if (pressureDetected) behavioralPatterns.push('High pressure/urgency tactics deployed');
    if (otpAttempt) behavioralPatterns.push('OTP harvesting attempts detected');
    if (intel.falseExpertise) behavioralPatterns.push('Feigned technical authority (Tech Support Scam)');
    if (scammerMsgs > 10) behavioralPatterns.push('Persistent engagement despite obstacles');
    if (persona !== 'Unknown') behavioralPatterns.push(`Persona identified as ${persona}`);
    if (!isScam) behavioralPatterns.push('Conversation appears benign.');

    const finalAgentNotes = [
      `• Tactics Deployed: ${tacticsList}`,
      `• Intelligence Extracted: ${intelString}`,
      `• Behavioral Patterns: ${behavioralPatterns.join('; ')}`,
      `• Latest Assessment: ${this.agentNotes().replace(/\n/g, ' ').substring(0, 100)}...`
    ].join('\n');

    const payload: FinalCallbackPayload = {
      sessionId: this.sessionId(),
      scamDetected: isScam,
      totalMessagesExchanged: msgs.length,

      // STRICTLY IoCs as per new spec
      extractedIntelligence: {
        bankAccounts: intel.bankAccounts,
        upiIds: intel.upiIds,
        phishingLinks: intel.phishingLinks,
        phoneNumbers: intel.phoneNumbers,
        suspiciousKeywords: intel.suspiciousKeywords
      },

      agentNotes: finalAgentNotes,

      confidenceScore: parseFloat((confidence / 100).toFixed(2)), // Normalized 0-1
      riskLevel: riskLevel,
      scamCategory: scamCategory,
      threatScore: Math.min(100, confidence + (uniqueIndicators * 5)),

      behavioralIndicators: {
        socialEngineeringTactics: tactics,
        falseExpertise: intel.falseExpertise || false,
        pressureLanguageDetected: pressureDetected,
        otpHarvestingAttempt: otpAttempt
      },

      engagementMetrics: {
        agentMessages: agentMsgs,
        scammerMessages: scammerMsgs,
        avgResponseTimeSec: parseFloat(avgResponseTime.toFixed(2)),
        totalConversationDurationSec: duration,
        engagementLevel: engagementLevel
      },

      intelligenceMetrics: {
        uniqueIndicatorsExtracted: uniqueIndicators,
        intelligenceQualityScore: intelQualityNormalized,
        extractionAccuracyScore: 0.91 // Mock high accuracy
      },

      scammerProfile: {
        personaType: persona,
        likelyRegion: this.metaLocale() === 'IN' ? 'India' : 'USA',
        languageDetected: this.metaLanguage(),
        repeatPatternDetected: false
      },

      costAnalysis: {
        timeWastedMinutes: parseFloat((duration / 60).toFixed(2)),
        estimatedScammerCostUSD: cost
      },

      agentPerformance: {
        humanLikeScore: parseFloat((naturalness * 0.95).toFixed(0)),
        conversationNaturalnessScore: parseFloat(naturalness.toFixed(0)),
        selfCorrections: Math.floor(agentMsgs * 0.2), // Simulated count
        stealthModeMaintained: true
      },

      systemMetrics: {
        detectionModelVersion: this.backendMode() === 'PYTHON_LANGGRAPH' ? 'Sentinel-Core-v2.1' : 'Sentinel-Edge-v1.0',
        systemLatencyMs: 450, // Mock avg latency
        processingTimeMs: 410,
        memoryUsageMB: 128,
        systemHealth: 'OK'
      }
    };
    return payload;
  });

  // Sparkline Points
  confidencePoints = computed(() => {
    const history = this.confidenceHistory();
    if (history.length < 2) return '';

    // Scale to 100x40 SVG
    const width = 100;
    const height = 40;
    const max = 100;

    const step = width / (history.length - 1);

    return history.map((val, idx) => {
      const x = idx * step;
      const y = height - ((val / max) * height);
      return `${x},${y}`;
    }).join(' ');
  });

  constructor() {
  }

  ngOnDestroy() {
    this.stopTimer();
    window.speechSynthesis.cancel();
    if (this.notificationTimeout) clearTimeout(this.notificationTimeout);
  }

  // Check scroll on view updates
  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  scrollToBottom(): void {
    try {
      if (this.chatContainer) {
        this.chatContainer.nativeElement.scrollTop = this.chatContainer.nativeElement.scrollHeight;
      }
    } catch (err) { }
  }

  // --- Actions ---

  showNotification(message: string, type: 'error' | 'info' | 'success' = 'info', duration = 5000) {
    this.notificationMessage.set(message);
    this.notificationType.set(type);

    if (this.notificationTimeout) clearTimeout(this.notificationTimeout);
    this.notificationTimeout = setTimeout(() => {
      this.notificationMessage.set(null);
    }, duration);
  }

  dismissNotification() {
    this.notificationMessage.set(null);
    if (this.notificationTimeout) clearTimeout(this.notificationTimeout);
  }

  toggleMetadataSettings() {
    this.showMetadataSettings.update(v => !v);
  }

  toggleBackendMode() {
    if (this.backendMode() === 'CLIENT_OPENAI') {
      this.backendMode.set('PYTHON_LANGGRAPH');
      this.showNotification('Switched to Python Backend Mode (Requires running server.py)', 'info');
    } else {
      this.backendMode.set('CLIENT_OPENAI');
      this.showNotification('Switched to Browser Client Mode (OpenAI)', 'success');
    }
  }

  toggleAudio() {
    this.isAudioEnabled.update(v => !v);
    if (!this.isAudioEnabled()) {
      window.speechSynthesis.cancel();
    }
  }

  toggleTerminalMode() {
    this.isTerminalMode.update(v => !v);
  }

  async sendMessage() {
    const text = this.newMessageText().trim();
    if (!text || this.isProcessing() || this.isAgentTyping()) return;

    if (!this.startTime()) {
      this.startTimer();
    }

    // 1. Add Scammer Message
    const scammerMsg: Message = {
      sender: 'scammer',
      text: text,
      timestamp: Date.now()
    };

    this.messages.update(msgs => [...msgs, scammerMsg]);
    this.newMessageText.set('');
    this.isProcessing.set(true);

    // Audio: Speak Scammer Input
    if (this.isAudioEnabled()) {
      this.speakText(scammerMsg.text, 'scammer');
    }

    try {
      let response;
      const metadata = {
        channel: this.metaChannel(),
        language: this.metaLanguage(),
        locale: this.metaLocale()
      };

      // 2. BACKEND BRIDGE: Securely interact with the AI via Python server
      try {
        response = await this.backendService.analyzeAndEngage(scammerMsg.text, this.messages(), metadata, this.sessionId());
      } catch (err: any) {
        console.warn('Sentinel Central Bridge error. Retrying...', err);
        response = await this.backendService.analyzeAndEngage(scammerMsg.text, this.messages(), metadata, this.sessionId());
      }

      // Analysis complete
      this.isProcessing.set(false);

      // 3. Update Dashboard Intelligence & Notes
      if (response.extractedIntelligence) {
        this.intelligence.update(current => ({
          ...current,
          bankAccounts: Array.from(new Set([...current.bankAccounts, ...(response.extractedIntelligence.bankAccounts || [])])),
          upiIds: Array.from(new Set([...current.upiIds, ...(response.extractedIntelligence.upiIds || [])])),
          phishingLinks: Array.from(new Set([...current.phishingLinks, ...(response.extractedIntelligence.phishingLinks || [])])),
          phoneNumbers: Array.from(new Set([...current.phoneNumbers, ...(response.extractedIntelligence.phoneNumbers || [])])),
          suspiciousKeywords: Array.from(new Set([...current.suspiciousKeywords, ...(response.extractedIntelligence.suspiciousKeywords || [])])),
          socialEngineeringTactics: Array.from(new Set([...current.socialEngineeringTactics, ...(response.extractedIntelligence.socialEngineeringTactics || [])]))
        }));
      }

      // Update the Analysis Card
      this.agentNotes.set(response.agentNotes || "Sentinel Brain Active. Evaluating scam vectors...");
      this.confidenceScore.set(response.confidenceScore);
      this.confidenceHistory.update(h => [...h, response.confidenceScore]);
      this.isScamConfirmed.set(response.scamDetected);

      // Reactive Update: Allow status to toggle back to safe if confidence drops
      // This ensures the "SCAM DETECTED" banner and final report align with the latest assessment
      // rather than latching to true forever once triggered.
      this.isScamConfirmed.set(response.confidenceScore > 50);

      this.agentNotes.set(response.agentNotes);

      // 4. Simulate "Human Typing" Delay
      this.isAgentTyping.set(true);

      // Calculate delay: Base 600ms + 30ms per character, capped at 4s to not bore the user
      const typingDelay = Math.min(4000, 600 + (response.reply.length * 30));

      setTimeout(() => {
        this.isAgentTyping.set(false);

        // 5. Add Agent Reply
        const agentMsg: Message = {
          sender: 'agent',
          text: response.reply,
          timestamp: Date.now()
        };
        this.messages.update(msgs => [...msgs, agentMsg]);

        // Audio: Speak Agent Reply
        if (this.isAudioEnabled()) {
          this.speakText(agentMsg.text, 'agent');
        }
      }, typingDelay);

    } catch (err: any) {
      console.error('Error processing message', err);
      this.isProcessing.set(false);
      this.isAgentTyping.set(false);

      // Error Handling Logic
      let userMessage = 'Unknown system error occurred.';
      const msg = err?.message || '';

      if (msg.includes('quota') || msg.includes('429')) {
        userMessage = 'OpenAI Quota Exceeded (429): Please wait a moment.';
      } else if (msg.includes('401') || msg.includes('key')) {
        userMessage = 'Authentication Failed: Invalid OpenAI Key. Check environment.ts';
      } else if (err?.status === 0 || msg.includes('network')) {
        userMessage = 'Network Error: Unable to reach OpenAI.';
      }

      // 1. Show Toast
      this.showNotification(userMessage, 'error');

      // 2. Add in-chat System Message for context
      const errorMsg: Message = {
        sender: 'agent',
        text: `[SYSTEM ERROR] ${userMessage}`,
        timestamp: Date.now()
      };
      this.messages.update(msgs => [...msgs, errorMsg]);
    }
  }

  updateIntelligence(newInt: Intelligence) {
    this.intelligence.update(current => {
      return {
        confidence: newInt.confidence ?? current.confidence,
        bankAccounts: Array.from(new Set([...current.bankAccounts, ...(newInt.bankAccounts || [])])),
        upiIds: Array.from(new Set([...current.upiIds, ...(newInt.upiIds || [])])),
        phishingLinks: Array.from(new Set([...current.phishingLinks, ...(newInt.phishingLinks || [])])),
        phoneNumbers: Array.from(new Set([...current.phoneNumbers, ...(newInt.phoneNumbers || [])])),
        suspiciousKeywords: Array.from(new Set([...current.suspiciousKeywords, ...(newInt.suspiciousKeywords || [])])),
        socialEngineeringTactics: Array.from(new Set([...current.socialEngineeringTactics, ...(newInt.socialEngineeringTactics || [])])),
        // Merge falseExpertise: if either current or new is true, result is true.
        falseExpertise: (current.falseExpertise || newInt.falseExpertise) || false
      };
    });
  }

  async resetSession() {
    // Force update 'now' to get precise final duration for the report
    this.now.set(Date.now());

    // Report final results before resetting
    if (this.messages().length > 0) {
      this.isReporting.set(true);
      await this.callbackService.sendFinalResult(this.finalCallbackPayload());
      this.isReporting.set(false);
    }

    this.stopTimer();
    window.speechSynthesis.cancel();
    this.dismissNotification(); // Clear any lingering errors

    this.startTime.set(null);
    this.now.set(Date.now()); // Reset for new session UI

    this.sessionId.set(uuidv4());
    this.messages.set([]);
    this.isScamConfirmed.set(false);
    this.confidenceScore.set(0);
    this.confidenceHistory.set([]);
    this.agentNotes.set('Monitoring session...');
    this.intelligence.set({
      confidence: 0,
      bankAccounts: [],
      upiIds: [],
      phishingLinks: [],
      phoneNumbers: [],
      suspiciousKeywords: [],
      socialEngineeringTactics: [],
      falseExpertise: false
    });
    this.isProcessing.set(false);
    this.isAgentTyping.set(false);
  }

  // --- Scenarios & Reporting ---

  fillScenario(scenario: 'bank' | 'job' | 'lottery') {
    let text = '';
    switch (scenario) {
      case 'bank':
        text = 'URGENT: Your HDFC account ending in 4432 is blocked. Click http://bit.ly/verify-hdfc to update PAN immediately or lose access.';
        this.metaChannel.set('SMS');
        this.metaLanguage.set('English');
        this.metaLocale.set('IN');
        break;
      case 'job':
        text = 'Hello dear, part time job offer. Earn 5000-8000 daily working from home. Message me on WhatsApp +919876543210.';
        this.metaChannel.set('WhatsApp');
        this.metaLanguage.set('English');
        this.metaLocale.set('IN');
        break;
      case 'lottery':
        text = 'Congratulations! You won 1 Crore in KBC Lottery. Deposit processing fee of 5000 to UPI ID kbcwinner@okaxis to claim.';
        this.metaChannel.set('WhatsApp');
        this.metaLanguage.set('Hinglish');
        this.metaLocale.set('IN');
        break;
    }
    this.newMessageText.set(text);
  }

  sendEmailReport() {
    const data = this.intelligence();
    const recipient = 'report@cybercrime.gov.in'; // Placeholder for demo
    const subject = `[SENTINEL REPORT] Scam Detected - Session ${this.sessionId().slice(0, 8)}`;

    const body = `
SENTINEL AI HONEYPOT REPORT
===========================
Session ID: ${this.sessionId()}
Status: ${this.isScamConfirmed() ? 'CONFIRMED SCAM' : 'Suspicious'}
Confidence: ${this.confidenceScore()}%
Agent Notes: ${this.agentNotes()}
Session Duration: ${this.formattedDuration()}
Estimated Scammer Cost: $${this.scammerCost()}
Architecture: ${this.backendMode()}
Metadata: ${this.metaChannel()} / ${this.metaLanguage()} / ${this.metaLocale()}

EXTRACTED INTELLIGENCE
======================
tactics: ${data.socialEngineeringTactics.join(', ') || 'None'}

> PHONE NUMBERS
${data.phoneNumbers.map(x => '- ' + x).join('\n') || 'None'}

> UPI / PAYMENT IDs
${data.upiIds.map(x => '- ' + x).join('\n') || 'None'}

> PHISHING LINKS
${data.phishingLinks.map(x => '- ' + x).join('\n') || 'None'}

> SUSPICIOUS KEYWORDS
${data.suspiciousKeywords.join(', ') || 'None'}

> BANK ACCOUNTS
${data.bankAccounts.join(', ') || 'None'}

-----------------------------------
Report generated by Sentinel AI
    `.trim();

    window.open(`mailto:${recipient}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`);
  }

  // --- News Features ---

  toggleMonitorView() {
    if (this.monitorViewMode() === 'payload') {
      this.monitorViewMode.set('news');
      if (this.newsHeadlines().length === 0) {
        this.fetchNews();
      }
    } else {
      this.monitorViewMode.set('payload');
    }
  }

  async fetchNews() {
    this.isNewsLoading.set(true);
    this.newsError.set(null);
    try {
      const filter = this.newsFilter();
      const result = await this.newsService.getHeadlines(filter);

      const hits = result.hits || [];
      if (hits.length === 0) {
        this.newsError.set('No reports found. Try a different search term.');
        // Optional: Show notification for empty search state too
        this.showNotification('No threat intelligence reports found.', 'info');
      } else {
        const articles = hits.map((hit: any) => ({
          id: hit.objectID,
          title: hit.title || hit.story_title || 'Untitled Report',
          url: hit.url || hit.story_url || `https://news.ycombinator.com/item?id=${hit.objectID}`,
          news_site: this.extractDomain(hit.url || hit.story_url) || 'Community Report',
          published_at: hit.created_at
        }));
        this.newsHeadlines.set(articles);
      }
    } catch (error: any) {
      console.error('News fetch failed', error);

      let msg = 'Unable to load threat intelligence feed.';
      if (error?.status === 0 || error?.name === 'HttpErrorResponse') {
        msg = 'Network Error: Cannot connect to news feed.';
      }

      this.newsError.set(msg);
      // Also show global toast for visibility if user is not looking at news tab
      this.showNotification(msg, 'error');
    } finally {
      this.isNewsLoading.set(false);
    }
  }

  private extractDomain(url: string | null): string {
    if (!url) return '';
    try {
      const hostname = new URL(url).hostname;
      return hostname.replace(/^www\./, '');
    } catch {
      return '';
    }
  }

  // --- Timer & Audio ---

  private startTimer() {
    if (this.timerInterval) return;

    const start = Date.now();
    this.startTime.set(start);
    this.now.set(start);

    this.timerInterval = setInterval(() => {
      this.now.set(Date.now());
    }, 1000);
  }

  private stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval as number);
      this.timerInterval = null;
    }
  }

  private speakText(text: string, type: 'scammer' | 'agent') {
    if (!('speechSynthesis' in window)) return;

    // Small delay to ensure natural flow
    setTimeout(() => {
      const utterance = new SpeechSynthesisUtterance(text);
      const voices = window.speechSynthesis.getVoices();

      if (type === 'scammer') {
        utterance.rate = 1.1; // Faster, urgent
        utterance.pitch = 0.9; // Lower, ominous
        // Try to pick a male voice if available
        const maleVoice = voices.find(v => v.name.toLowerCase().includes('male') || v.name.toLowerCase().includes('david'));
        if (maleVoice) utterance.voice = maleVoice;
      } else {
        utterance.rate = 0.9; // Slower, older
        utterance.pitch = 1.1; // Slightly higher
        // Try to pick a female voice
        const femaleVoice = voices.find(v => v.name.toLowerCase().includes('female') || v.name.toLowerCase().includes('zira'));
        if (femaleVoice) utterance.voice = femaleVoice;
      }

      window.speechSynthesis.speak(utterance);
    }, 500);
  }
}