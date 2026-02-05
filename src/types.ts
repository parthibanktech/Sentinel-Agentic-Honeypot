
export interface Message {
  sender: 'scammer' | 'user' | 'agent';
  text: string;
  timestamp: number;
}

export interface Intelligence {
  confidence: number;
  bankAccounts: string[];
  upiIds: string[];
  phishingLinks: string[];
  phoneNumbers: string[];
  suspiciousKeywords: string[];
  socialEngineeringTactics: string[];
  falseExpertise?: boolean;
}

// Updated to be flexible enough for strict backend response AND frontend needs
export interface HoneypotResponse {
  status?: string; // Added for strict API compliance
  reply: string;
  scamDetected: boolean;
  confidenceScore: number;
  agentNotes: string;
  extractedIntelligence: Intelligence;
}

export interface ApiRequestPayload {
  sessionId: string;
  message: {
    sender: 'scammer' | 'user';
    text: string;
    timestamp: number;
  };
  conversationHistory: {
    sender: 'scammer' | 'user';
    text: string;
    timestamp: number;
  }[];
  metadata: {
    channel: string;
    language: string;
    locale: string;
  };
}

export interface FinalCallbackPayload {
  sessionId: string;
  scamDetected: boolean;
  totalMessagesExchanged: number;

  // Strictly IoCs
  extractedIntelligence: {
    bankAccounts: string[];
    upiIds: string[];
    phishingLinks: string[];
    phoneNumbers: string[];
    suspiciousKeywords: string[];
  };

  agentNotes: string;

  confidenceScore: number;
  riskLevel: string;
  scamCategory: string;
  threatScore: number;

  behavioralIndicators: {
    socialEngineeringTactics: string[];
    falseExpertise: boolean;
    pressureLanguageDetected: boolean;
    otpHarvestingAttempt: boolean;
  };

  engagementMetrics: {
    agentMessages: number;
    scammerMessages: number;
    avgResponseTimeSec: number;
    totalConversationDurationSec: number;
    engagementLevel: string;
  };

  intelligenceMetrics: {
    uniqueIndicatorsExtracted: number;
    intelligenceQualityScore: number;
    extractionAccuracyScore: number;
  };

  scammerProfile: {
    personaType: string;
    likelyRegion: string;
    languageDetected: string;
    repeatPatternDetected: boolean;
  };

  costAnalysis: {
    timeWastedMinutes: number;
    estimatedScammerCostUSD: number;
  };

  agentPerformance: {
    humanLikeScore: number;
    conversationNaturalnessScore: number;
    selfCorrections: number;
    stealthModeMaintained: boolean;
  };

  systemMetrics: {
    detectionModelVersion: string;
    systemLatencyMs: number;
    processingTimeMs: number;
    memoryUsageMB: number;
    systemHealth: string;
  };
}
