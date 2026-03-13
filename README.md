# Compete Pulse: Strategic AI & Agentic Intelligence ⚔️

[![Compete Pulse Actions](https://github.com/enriquekalven/compete-pulse/actions/workflows/pulse.yml/badge.svg)](https://github.com/enriquekalven/compete-pulse/actions)
[![Standard: Vertex AI ADK](https://img.shields.io/badge/Standard-Vertex%20AI%20ADK-blue)](https://github.com/google/adk-python)
[![Intelligence: Gemini 2.5 Pro](https://img.shields.io/badge/Intelligence-Gemini%202.5%20Pro-purple)](https://cloud.google.com/vertex-ai)

**Compete Pulse** is a high-fidelity intelligence engine designed to track, analyze, and neutralize competitor AI "Launch Theater." It bridges the gap between raw technical updates (LLM benchmarks, SDK releases) and **Enterprise-Ready Sales Plays** for Google Cloud field teams.

---

## 🏗️ Intelligence Architecture

```mermaid
graph TD
    subgraph "External Signals (The Noise)"
        C1[Competitor Previews: O1/GPT-5/Claude 3.7]
        C2[Rival SDKs: AutoGen/LangGraph/OpenAI SDK]
        C3[Market Trends: SiliconAngle/SemiAnalysis]
    end

    subgraph "Compete Pulse Brain (Gemini 2.5 Hub)"
        W[Watcher: Feed Ingestion]
        R[Ranker: Impact Scoring /2.5 Flash/]
        S[Scribe: Hybrid Synthesis /2.5 Pro/]
        GA[Gap Analyst: Strategic Battlecards]
        
        W --> R
        R --> S
        S --> GA
    end

    subgraph "Field Promotion (The Signal)"
        EM[Premium HTML Email Pulse]
        GH[Searchable Pulse History /Issues/]
        GC[Real-time GChat Alerts]
        IG[Strategic Infographics /Imagen 3/]
    end

    C1 --> W
    C2 --> W
    C3 --> W
    
    GA --> EM
    GA --> GH
    S --> IG
    IG --> EM
```

---

## 🎯 Core Intelligence Moats

- **The "Context Moat"**: Automatically identifies opportunities to pitch Gemini's **2M token context window** against competitor context drowning.
- **GA vs. Theater**: Differentiates between competitor "Research Previews" and Google's **General Availability** (GA) stability.
- **Agentic Trinity Integration**: Connects **Vertex AI Models**, **Agent Builder**, and the **ADK** into a unified "Production-Ready" narrative.
- **Grounding Validation**: Highlights Google Search-grade grounding as the ultimate cure for competitor hallucinations.

---

## 🚀 How it Works (The Lifecycle)

### 1. Automated Scrutiny
The **Watcher** scans official release feeds (Vertex AI, Anthropic, OpenAI) and code movements (ADK, A2UI, Genkit) **every day at 8:00 AM PST**.

### 2. Impact Ranking (Flash Engine)
Uses **Gemini 2.5 Flash** to assign a **Strategic Impact Score (1-100)**. This ensures major launches like Gemini 2.5 or Sovereign AI updates are prioritized over minor SDK patches.

### 3. Executive Synthesis (Pro Engine)
Uses **Gemini 2.5 Pro** to distill technical changes into three actionable talk tracks:
*   **Key Feature**: The technical "What."
*   **Customer Value**: The business "Why."
*   **Compete Play**: The tactical "How" to win against the rival solution.

---

## 📂 Strategic Assets
The agent maintains a suite of high-signal documents for the field:
*   [**Key Differentiators**](compete-docs/key_differentiators.md): Strategic breakdown of Google Cloud vs. Competitor Previews.
*   [**Email Pulse Draft**](compete-docs/email_pulse_draft.md): Pre-formatted executive updates for distribution lists.

---

## 🛠️ Field Usage

### Installation
```bash
pip install .
```

### Local Intelligence Report
```bash
compete-pulse report --days 2
```

### Strategic Email Broadcast
```bash
compete-pulse email "field-team@google.com" --infographic
```

### RAG Intelligence Query
```bash
# Query the historical knowledge base for past competitor moves
compete-pulse query "How did we respond to Claude 3.5 Sonnet launch?"
```

### Rapid Response Battlecard
```bash
# Generate a high-fidelity 'Rapid Response' battlecard for a competitor product
compete-pulse response "Claude CoWork" --raw
```

**🛡️ GitHub Action Trigger**: You can trigger this analysis on-demand via the **Actions** tab in GitHub using the **"Competitive Rapid Response"** workflow. It renders the battlecard directly into the workflow summary for quick executive sharing.

---

## 🔐 Environment Configuration
To run the agent locally or in CI/CD, configure the following:

| `GOOGLE_API_KEY` | API Key for Gemini 2.5 Flash/Pro access. |
| `COMPETE_PULSE_SENDER_EMAIL` | Sender address for automated pulses. |
| `COMPETE_PULSE_SENDER_PASSWORD` | Google **App Password** for secure delivery. |
| `RECIPIENT_EMAIL` | Comma-separated list of target emails (optional fallback). |
| `GCHAT_WEBHOOK_URL` | Webhook for real-time corridor alerts. |
| `GITHUB_TOKEN` | Required for dispatching reports to GitHub Issues. |

---

## 📊 Competitive Intelligence Targets
*   **LLM Model Competes**: Gemini vs. GPT-4o, Claude 3.5/3.7, and Llama 4 benchmarks.
*   **Enterprise Resilience**: GA stability vs. competitor "Waitlist" theater.
*   **Agentic Orchestration**: Vertex AI Agent Builder vs. standalone "Toy" GUI builders.
*   **Sovereignty & Security**: VPC-SC and Data Residency as regional deal-closers.

---

## 🗺️ Roadmap
Check [**ROADMAP.md**](ROADMAP.md) for upcoming RAG enhancements, automated battlecard generation, and internal CRM integration milestones.

---

*Generated & Maintained by the Compete Pulse Agent*
