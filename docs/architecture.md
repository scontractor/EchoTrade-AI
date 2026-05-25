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
        TopBar["Ticker tape + status pills<br/>(MOCK — static prices, fake LIVE/Ollama lights)"]
    end

    subgraph Backend["Backend — FastAPI + httpx + SQLAlchemy (local :8000)"]
        API[main.py — 8 HTTP routes]
        Edgar[edgar/ — SEC scraper<br/>13F holdings + CUSIP→ticker resolver]
        Portfolio[portfolio/ — diff engine + clone allocator]
        Insiders[insiders/ — Form 4 parser + scorer]
        Sentiment[sentiment/ — Yahoo RSS + TextBlob<br/>crude polarity]
        Signals[signals/ — bundles diff+sentiment → LLM → BUY/HOLD/SELL]
    end

    DB[("SQLite — echotrade.db<br/>caches Form 4 trades only")]

    subgraph External["External services"]
        SEC["SEC EDGAR<br/>13F + Form 4 filings"]
        Yahoo["Yahoo Finance RSS<br/>headlines"]
        Ollama["Ollama local LLM :11434<br/>(assumed running — UNVERIFIED end-to-end)"]
    end

    User -->|interacts| UI
    UI -->|Vite proxies /api → :8000| API
    API --> Edgar
    API --> Portfolio
    API --> Insiders
    API --> Signals
    Edgar -->|fetches filings every request<br/>NO 13F cache| SEC
    Insiders -->|fetches + persists| SEC
    Insiders -->|read/write| DB
    Sentiment -->|scrapes headlines| Yahoo
    Signals -->|inference| Ollama
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
- **Built but unverified:** AI Signals assumes Ollama is running locally — never
  tested end-to-end. Confirm Ollama setup before relying on it.
- **Mock / cosmetic:** ticker tape (static prices), LIVE + OLLAMA status lights.
- **Not present:** auth, user persistence, real-time prices, deployment, tests,
  and 13F caching (13F is re-fetched from SEC on every request — a known gap).

## Stack (actual)
- **Backend:** Python 3.13, FastAPI, httpx (async), SQLAlchemy 2.0, SQLite,
  openai-sdk pointed at Ollama.
- **Frontend:** React 18, Vite, Tailwind 3, TypeScript.
- **LLM:** local Ollama (default llama3.1:8b) — open-source, matches CLAUDE.md.
- **Persistence:** ~5MB SQLite file (gitignored). **Deployment:** none yet.

_Last updated: reconciliation pass against real codebase. Update with each change._
