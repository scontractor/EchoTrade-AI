# EchoTrade AI

> Institutional-grade celebrity portfolio cloning. 13F filings + social sentiment → actionable AI trading signals.

## The Problem
Retail investors lack the tools to replicate high-performance celebrity portfolios. 13F filings are public but opaque — raw XML with no context, no diff, no signal.

## The Solution
EchoTrade AI is an AI Strategy Cloner that:
1. **Ingests** SEC EDGAR 13F filings for 10 celebrity investors (Buffett, Ackman, Cathie Wood, Druckenmiller, and more)
2. **Diffs** holdings quarter-over-quarter to surface new/exited/increased/decreased positions
3. **Scores** sentiment per position using real-time news via Yahoo Finance RSS + TextBlob
4. **Generates** institutional-quality trading signals via Claude claude-sonnet-4-6 with full rationale
5. **Clones** any portfolio: given $X capital, returns a proportional allocation table

---

## Architecture

```
app/
├── edgar/
│   ├── client.py       # Async EDGAR API client (submissions + infotable XML)
│   ├── parser.py       # 13F-HR XML parser (handles all namespace variants)
│   └── investors.py    # Celebrity investor registry (name → CIK)
├── portfolio/
│   ├── models.py       # Pydantic response schemas
│   └── diff.py         # Q/Q diff engine + clone allocator
├── sentiment/
│   └── analyzer.py     # RSS news fetch + TextBlob sentiment scoring
├── signals/
│   └── analyst.py      # Claude claude-sonnet-4-6 with prompt caching
├── config.py           # Pydantic-settings
└── main.py             # FastAPI app + all routes
```

---

## Quickstart

EchoTrade AI runs entirely on open-source models — no proprietary API keys required.

### Option A — Ollama (fully local, recommended)

```bash
# Install Ollama: https://ollama.com
ollama pull llama3.1:8b        # ~5 GB; swap for llama3.3:70b for higher quality

pip install -e .
cp .env.example .env           # defaults already point to Ollama
uvicorn app.main:app --reload
```

### Option B — Groq (hosted, free tier, no GPU needed)

```bash
pip install -e .
cp .env.example .env
# Edit .env:
#   LLM_BASE_URL=https://api.groq.com/openai/v1
#   LLM_API_KEY=gsk_<your_groq_key>   # free at console.groq.com
#   LLM_MODEL=llama-3.3-70b-versatile
uvicorn app.main:app --reload
```

### Supported backends

| Provider | `LLM_BASE_URL` | Recommended model | Cost |
|----------|---------------|-------------------|------|
| **Ollama** (default) | `http://localhost:11434/v1` | `llama3.1:8b` | Free (local) |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` | Free tier |
| Together AI | `https://api.together.xyz/v1` | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | Free tier |
| OpenRouter | `https://openrouter.ai/api/v1` | `meta-llama/llama-3.3-70b-instruct` | Pay-per-use |
| vLLM / LM Studio | `http://localhost:8000/v1` | any GGUF | Free (local) |

All backends use the same OpenAI-compatible `/v1/chat/completions` interface.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/investors` | List all tracked celebrity investors |
| `GET` | `/investors/{id}/snapshot` | Latest 13F holdings (top 25) |
| `GET` | `/investors/{id}/diff` | Q/Q portfolio changes |
| `GET` | `/investors/{id}/signals` | AI trading signals (Claude) |
| `GET` | `/investors/{id}/clone?capital=50000` | Proportional clone allocation |

**Investor IDs:** `berkshire` · `ark_invest` · `pershing_square` · `third_point` · `appaloosa` · `soros_fund` · `baupost` · `tiger_global` · `druckenmiller` · `renaissance`

---

## Example: Trading Signals

```bash
curl http://localhost:8000/investors/berkshire/signals
```

```json
{
  "investor_name": "Berkshire Hathaway (Warren Buffett)",
  "executive_summary": "Berkshire meaningfully rotated into energy and financials...",
  "strategy_style": "Concentrated Value with macro overlay",
  "key_themes": ["Energy transition", "Financial sector re-rating", "Japan conglomerate exposure"],
  "signals": [
    {
      "ticker": "OXY",
      "action": "ADD",
      "confidence": 0.88,
      "rationale": "Position increased 12% QoQ, now 5.1% of portfolio. Buffett has consistently added...",
      "institutional_conviction": "HIGH"
    }
  ],
  "risk_factors": ["Rising interest rates compress equity multiples", "Energy demand uncertainty"]
}
```

---

## Data Sources

| Source | Usage | Cost |
|--------|-------|------|
| [SEC EDGAR](https://www.sec.gov/developer) | 13F filings (XML) | Free |
| [Yahoo Finance RSS](https://finance.yahoo.com) | News headlines per ticker | Free |
| [Ollama](https://ollama.com) / any OpenAI-compatible backend | Signal generation | Free (local) |

---

## Tech Stack

- **Backend:** FastAPI + uvicorn
- **Data:** httpx (async), SEC EDGAR public API
- **AI:** Any open-source LLM via OpenAI-compatible API (Ollama · Groq · Together · vLLM)
- **Parsing:** Python stdlib xml.etree + TextBlob
- **Validation:** Pydantic v2
