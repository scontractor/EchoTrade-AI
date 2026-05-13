"""
EchoTrade AI — FastAPI application

Endpoints:
  GET /investors                           List celebrity investors
  GET /investors/{id}/snapshot             Latest 13F holdings
  GET /investors/{id}/diff                 Q/Q portfolio changes
  GET /investors/{id}/signals              AI trading signals (requires ANTHROPIC_API_KEY)
  GET /investors/{id}/clone?capital=50000  Proportional clone allocation

  POST /insiders/ingest/{ticker}           Ingest Form 4 filings for a ticker
  GET  /insiders/{ticker}/trades           Recent insider trades
  GET  /insiders/{ticker}/signal           Scored insider signal (+ optional AI commentary)
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.edgar.client import EDGARClient
from app.edgar.investors import INVESTORS
from app.insiders.ingestion_service import Form4Client
from app.insiders.models import InsiderSignal, InsiderTradeOut
from app.insiders.scorer import score_trades
from app.portfolio.diff import clone_portfolio, compute_diff
from app.portfolio.models import CloneOut, DiffOut, PortfolioAnalysis, SnapshotOut, HoldingOut
from app.sentiment.analyzer import analyze_tickers
from app.signals.analyst import AIAnalyst

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger(__name__)

edgar = EDGARClient()
form4 = Form4Client()
analyst: AIAnalyst | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global analyst
    analyst = AIAnalyst()
    logger.info("AIAnalyst initialised — model=%s base_url=%s", settings.llm_model, settings.llm_base_url)
    yield


app = FastAPI(
    title="EchoTrade AI",
    description="Institutional-grade celebrity portfolio cloning engine powered by SEC 13F filings + open-source LLMs",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _require_investor(investor_id: str):
    inv = INVESTORS.get(investor_id)
    if not inv:
        raise HTTPException(404, f"Investor '{investor_id}' not found. GET /investors for valid IDs.")
    return inv


# ── routes ───────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "EchoTrade AI",
        "version": "0.1.0",
        "docs": "/docs",
        "investors": "/investors",
    }


@app.get("/investors")
async def list_investors():
    """Return all tracked celebrity investors."""
    return [
        {"id": inv.id, "name": inv.name, "style": inv.style, "description": inv.description}
        for inv in INVESTORS.values()
    ]


@app.get("/investors/{investor_id}/snapshot", response_model=SnapshotOut)
async def get_snapshot(investor_id: str):
    """Latest 13F holdings for an investor."""
    inv = _require_investor(investor_id)
    current, _ = await edgar.get_two_latest_snapshots(inv.cik, inv.name)
    if not current:
        raise HTTPException(503, "Could not retrieve filings from SEC EDGAR. Try again later.")

    total = current.total_value_thousands or 1
    top_holdings = [
        HoldingOut(
            rank=i + 1,
            ticker=h.ticker,
            company_name=h.company_name,
            cusip=h.cusip,
            value_millions=round(h.value_thousands / 1000, 2),
            pct_of_portfolio=round(h.value_thousands / total * 100, 2),
            shares=h.shares,
            put_call=h.put_call,
        )
        for i, h in enumerate(current.holdings[:25])
    ]

    return SnapshotOut(
        investor_name=current.investor_name,
        period_of_report=current.period_of_report,
        filing_date=current.filing_date,
        total_aum_billions=round(current.total_value_thousands / 1_000_000, 3),
        holding_count=current.holding_count,
        top_holdings=top_holdings,
    )


@app.get("/investors/{investor_id}/diff", response_model=DiffOut)
async def get_diff(investor_id: str):
    """Quarter-over-quarter portfolio changes (new / exited / increased / decreased)."""
    inv = _require_investor(investor_id)
    current, previous = await edgar.get_two_latest_snapshots(inv.cik, inv.name)
    if not current or not previous:
        raise HTTPException(503, "Need at least two 13F filings; data unavailable.")

    return compute_diff(current, previous)


@app.get("/investors/{investor_id}/signals", response_model=PortfolioAnalysis)
async def get_signals(investor_id: str):
    """AI-generated trading signals via the configured open-source LLM (default: Ollama llama3.1:8b)."""
    if not analyst:
        raise HTTPException(503, "AI analyst not initialised. Check LLM_BASE_URL in .env.")

    inv = _require_investor(investor_id)
    current, previous = await edgar.get_two_latest_snapshots(inv.cik, inv.name)
    if not current or not previous:
        raise HTTPException(503, "Need at least two 13F filings; data unavailable.")

    diff = compute_diff(current, previous)

    # Gather sentiment for new/increased positions above 0.5% portfolio weight
    tickers_for_sentiment = [
        c.ticker
        for c in diff.changes
        if c.ticker
        and c.action in ("NEW", "INCREASED")
        and (c.curr_pct_of_portfolio or 0) > 0.5
    ][:12]

    sentiment = analyze_tickers(tickers_for_sentiment) if tickers_for_sentiment else {}

    return analyst.analyze(diff, current, sentiment)


@app.get("/investors/{investor_id}/clone", response_model=CloneOut)
async def clone(
    investor_id: str,
    capital: float = Query(10_000, ge=100, description="Capital to allocate in USD"),
    top_n: int = Query(20, ge=5, le=50, description="Number of top holdings to replicate"),
):
    """Proportionally allocate capital to mirror the investor's top holdings."""
    inv = _require_investor(investor_id)
    current, _ = await edgar.get_two_latest_snapshots(inv.cik, inv.name)
    if not current:
        raise HTTPException(503, "Could not retrieve filings from SEC EDGAR.")

    allocations = clone_portfolio(current, capital, top_n)

    return CloneOut(
        investor_name=current.investor_name,
        period_of_report=current.period_of_report,
        total_capital_usd=capital,
        strategy=f"Proportional top-{top_n} holdings replication",
        allocations=allocations,
    )


# ── Insider trades (Form 4) ───────────────────────────────────────────────────

@app.post("/insiders/ingest/{ticker}")
async def ingest_insider_trades(
    ticker: str,
    days_back: int = Query(90, ge=7, le=365, description="How many days of filings to fetch"),
):
    """
    Fetch and store Form 4 filings for a ticker from SEC EDGAR.
    Run this first before querying /insiders/{ticker}/trades or /signal.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, form4.ingest_ticker, ticker.upper(), days_back)
    return result


@app.get("/insiders/{ticker}/trades", response_model=list[InsiderTradeOut])
async def get_insider_trades(
    ticker: str,
    limit: int = Query(50, ge=1, le=200),
):
    """Return stored Form 4 trades for a ticker, newest first."""
    import asyncio
    loop = asyncio.get_event_loop()
    trades = await loop.run_in_executor(None, form4.get_recent_trades, ticker.upper(), limit)
    return [InsiderTradeOut.model_validate(t, from_attributes=True) for t in trades]


@app.get("/insiders/{ticker}/signal", response_model=InsiderSignal)
async def get_insider_signal(
    ticker: str,
    with_ai: bool = Query(False, description="Append Claude commentary to the signal"),
):
    """
    Score insider activity for a ticker.
    Set ?with_ai=true to include LLM narrative (requires a running LLM backend).
    """
    import asyncio
    loop = asyncio.get_event_loop()
    trades = await loop.run_in_executor(None, form4.get_recent_trades, ticker.upper(), 100)

    if not trades:
        raise HTTPException(
            404,
            f"No trades found for {ticker.upper()}. "
            f"Call POST /insiders/ingest/{ticker.upper()} first.",
        )

    signal = score_trades(trades)

    if with_ai and analyst:
        prompt = (
            f"Insider trade summary for {ticker.upper()}:\n"
            f"Signal: {signal.signal_type} (conviction {signal.conviction_score}/10)\n"
            f"Rationale: {signal.rationale}\n"
            f"Cluster: {signal.cluster_description or 'None'}\n\n"
            f"Recent trades ({len(trades)}):\n"
            + "\n".join(
                f"- {t.owner_name} ({t.officer_title or 'Director'}): "
                f"{t.transaction_code_label} {t.shares or 0:,.0f} shares @ "
                f"${t.price_per_share or 0:,.2f} on {t.transaction_date}"
                + (" [10b5-1 plan]" if t.is_10b51_plan else " [open market]")
                for t in signal.trades[:10]
            )
            + "\n\nWrite a 3-sentence institutional-quality commentary on what this "
              "insider activity implies for the stock. Be specific about the 10b5-1 "
              "plan vs. discretionary distinction."
        )
        try:
            signal.ai_commentary = analyst.generate_commentary(prompt, max_tokens=512)
        except Exception as exc:
            logger.warning("AI commentary failed: %s", exc)

    return signal
