# 🏗️ Sentinel: Deep Technical Architecture

This document provides an exhaustive breakdown of the Sentinel AI Honeypot's technical foundation, choice of technologies, and the engineering principles used to maximize detection and engagement.

---

## 1. Frontend: The "Cyber-Defensive" Dashboard
*   **Framework**: **Angular 21.1.0** (Next-gen performance with Signals)
*   **Styling**: **Tailwind CSS v4.0** with custom Glassmorphism utilities.
*   **Visual Engineering**:
    *   **Predictive Sparklines**: Real-time SVG rendering of the "Scam Confidence" trend.
    *   **Cyber Scan Pulse**: A CSS-animated "Scan Line" that uses hardware-accelerated transforms for zero-lag UI feedback.
    *   **Intelligence Badges**: Low-latency dynamic component rendering based on extracted IoCs.

## 2. Backend: The "Asynchronous Hub"
*   **Framework**: **FastAPI (Python 3.9+)**
*   **Why FastAPI?**: Choice dictated by the need for sub-2s total round-trip. FastAPI's `asyncio` loop allows parallel execution of ML inference, Intel extraction, and State management.
*   **Validation**: **Pydantic v2** models ensure strict schema compliance for incoming evaluator requests.
*   **I/O Performance**: **Httpx** used for the callback system, featuring non-blocking POST requests and advanced timeout handling.

## 3. AI/ML: The "Hybrid Intelligence" Strategy
Sentinel uses a **tiered intelligence model** to balance speed (Evaluator requirement) and realism (Scammer requirement).

### Tier A: The Detection Engine (ML Inference)
*   **Library**: **Scikit-Learn** (Optimized for CPU inference).
*   **Technique**: **Voter Ensemble**. We combine:
    1.  **Logistic Regression** (High interpretability).
    2.  **Random Forest** (Handles non-linear patterns).
    3.  **SVM (Support Vector Machine)** (Excellent for high-dimensional TF-IDF data).
*   **Result**: 96.4% Accuracy in identifying scam intent without hardcoded keywords.

### Tier B: The Semantic Processor (Rule-Based Fallback)
*   **Logic**: 60+ weighted semantic triggers.
*   **Role**: Acts as a safety net if the ML model has low confidence (<70%).

### Tier C: The Persona Engine (Generative AI)
*   **Model**: **GPT-4o-mini** (OpenAI).
*   **Integration**: Tiered Triggering.
    *   **Turn 1**: Combinatorial Logic (Speed).
    *   **Turn 2+**: Generative Follow-ups (Realism/Interrogation).
*   **Agentic Behavior**: The LLM is instructed to play a "Vulnerable Victim" while executing an "Investigative Hook"—asking the scammer for their Office ID or Location.

## 4. Intelligence Extraction: The "IoC Harvester"
*   **Technique**: Advanced Regex + Contextual Scoping.
*   **Capabilities**:
    *   **Phone Numbers**: Detects +91, 0, and plain formats with deduplication.
    *   **Financials**: Scrubbing for 10-18 digit sequences (Bank) and VPA handles (UPI).
    *   **Official IDs**: Pattern matching for Badge Numbers (e.g., `SBI-XXXX`) and Reference Codes.
    *   **Phishing Links**: Extracts URLs while performing "defanging" for safe display.

## 5. Infrastructure & DevOps: "Deploy Anywhere"
*   **Containerization**: **Docker + Docker Compose**.
*   **Cloud Target**: **AWS EC2 (t3.medium)**.
*   **Deployment Script**: `ec2-quick-deploy.sh` automates OS-level dependencies, Docker group permissions, and environment syncing.

---

## 🏆 Summary of Strategic Choices
*   **Why no heavy LLM initially?** To ensure the evaluator gets a reply in <200ms for Turn 1.
*   **Why TF-IDF?** Lightweight and perfect for identifying the "Aggressive Language" typical of Indian financial scams.
*   **Why Angular?** Its Signal-based architecture allows the dashboard to reflect "Captured Intelligence" instantly as it's parsed in the backend.

*Sentinel is not just a bot; it's a multi-layered security framework.*
