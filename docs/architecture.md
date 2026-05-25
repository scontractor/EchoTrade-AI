# EchoTrade AI — System Architecture (current state)

> **Living document.** Reflects what's actually built today. Update in the same PR
> whenever a component or data flow changes. Renders automatically on GitHub.
> Nodes marked **(planned)** are on the roadmap but not built.

## How to read this
Boxes are components; arrows show what data flows. Solid = built and working today.
Dashed/**(planned)** = roadmap, not yet built.

```mermaid
flowchart TD
    User([User in browser])

    subgraph Frontend["Frontend — React 18 + Vite + Tailwind + TypeScript (local :5173)"]
        UI[Bloomberg-style terminal UI<br/>Portfolio · Diff · Clone · Form 4 · AI Signals tabs]
        TopBar["Ticker tape + status pills<br/>(DEMO PRICES — static, clearly labelled)"]
    end

    subgraph Backend["Backend — FastAPI + httpx + SQLAlchemy (local :8000)"]
        API[main.py — 8 HTTP routes]
        Edgar[edgar/ — SEC scraper<br/>13F holdings + CUSIP→ticker resolver]
        Portfolio[portfolio/ — diff engine + clone allocator]
        Insiders[insiders/ — Form 4 parser + scorer]
        Sentiment[sentiment/ — Yahoo RSS + TextBlob<br/>crude polarity]
        Signals[signals/ — bundles diff+sentiment → LLM → BUY/HOLD/SELL]
    end

    DB[("SQLite — echotrade.db<br/>Form 4 trades + 13F snapshots")]

    subgraph External["External services"]
        SEC["SEC EDGAR<br/>13F + Form 4 filings"]
        Yahoo["Yahoo Finance RSS<br/>headlines"]
        LLM["Configurable OSS LLM backend<br/>Groq (hosted) · Ollama (local)<br/>OpenAI-compatible API"]
    end

    User -->|interacts| UI
    UI -->|Vite proxies /api → :8000| API
    API --> Edgar
    API --> Portfolio
    API --> Insiders
    API --> Signals
    Edgar -->|checks cache first; fetches XML on miss| SEC
    Insiders -->|fetches + persists| SEC
    Insiders -->|read/write| DB
    Edgar -->|read/write| DB
    Sentiment -->|scrapes headlines| Yahoo
    Signals -->|inference via LLM_BASE_URL| LLM
    Signals --> Sentiment

    Auth["Auth + user accounts (planned, Phase 4)"]
    Prices["Real-time price feed (planned, Phase 2)"]
    Deploy["Deployment + CI/CD (planned)"]

    API -.->|planned| Auth
    TopBar -.->|planned: replace mock| Prices
    Frontend -.->|planned| Deploy

    classDef planned fill:#eee,stroke:#999,color:#666,stroke-dasharray: 5 5;
    classDef mock fill:#fff3e0,stroke:#e69138,color:#7f6000;
    class Auth,Prices,Deploy planned;
    class TopBar,Sentiment mock;
```

## What's real vs not (today)
- **Real & working:** live SEC 13F ingestion, diff engine, clone allocator, Form 4
  parser + scorer (role/value-weighted, cluster detection), full React UI wired
  across all 5 tabs, SQLite cache for Form 4.
- **Real but crude:** sentiment (TextBlob is keyword-based, not finance-aware).
- **AI Signals:** verified end-to-end via Groq (`llama-3.3-70b-versatile`). Configure
  via `.env` — see `.env.example` for Groq and Ollama options.
- **Static / labelled:** ticker tape shows demo prices, clearly marked "DEMO PRICES"; status pills say DEMO + AI (not LIVE/OLLAMA).
- **Not present:** auth, user persistence, real-time prices, deployment.

## Stack (actual)
- **Backend:** Python 3.13, FastAPI, httpx (async), SQLAlchemy 2.0, SQLite,
  openai-sdk (OpenAI-compatible, pointed at any backend via env vars).
- **Frontend:** React 18, Vite, Tailwind 3, TypeScript.
- **LLM:** configurable — default Ollama local (`llama3.1:8b`), recommended hosted
  Groq (`llama-3.3-70b-versatile`, free tier). All open-source, per CLAUDE.md.
- **Persistence:** ~5MB SQLite file (gitignored). **Deployment:** none yet.
- **Tests:** pytest, `tests/test_parse_response.py` (6 cases, passing).

_Last updated: 13F snapshot cache added (filing_snapshots table, transparent read-through)._
