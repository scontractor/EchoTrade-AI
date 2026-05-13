"""
cli_test.py — Quick smoke test for the Form 4 insider ingestion pipeline.

Usage:
    python cli_test.py              # tests NVDA (default)
    python cli_test.py PLTR         # tests Palantir
    python cli_test.py NVDA --days 30
"""

import argparse
import json
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="EchoTrade AI — insider trade CLI test")
    parser.add_argument("ticker", nargs="?", default="NVDA", help="Stock ticker (default: NVDA)")
    parser.add_argument("--days", type=int, default=60, help="Days of history to fetch (default: 60)")
    parser.add_argument("--db", default="echotrade_test.db", help="SQLite DB path")
    args = parser.parse_args()

    ticker = args.ticker.upper()
    logger.info("=" * 60)
    logger.info("EchoTrade AI — Form 4 Insider Test")
    logger.info("Ticker: %s | Days back: %d | DB: %s", ticker, args.days, args.db)
    logger.info("=" * 60)

    # ── Step 1: Ingest ────────────────────────────────────────────────────────
    from app.insiders.ingestion_service import Form4Client
    client = Form4Client(db_url=f"sqlite:///{args.db}")

    logger.info("\n[1/3] Ingesting Form 4 filings from SEC EDGAR...")
    result = client.ingest_ticker(ticker, days_back=args.days)
    print(json.dumps(result, indent=2))

    if result["trades_inserted"] == 0 and result["filings_processed"] == 0:
        logger.warning("No filings found. Check ticker spelling or try a larger --days window.")
        sys.exit(0)

    # ── Step 2: Retrieve ──────────────────────────────────────────────────────
    logger.info("\n[2/3] Retrieving stored trades...")
    trades = client.get_recent_trades(ticker, limit=20)

    if not trades:
        logger.warning("No trades in DB for %s yet.", ticker)
        sys.exit(0)

    for t in trades[:10]:
        plan_flag = " [10b5-1]" if t.is_10b51_plan else " [open market]"
        print(
            f"  {t.transaction_date}  {t.owner_name:<30}  "
            f"{t.transaction_code_label or t.transaction_code:<25}  "
            f"${(t.total_value or 0):>12,.0f}{plan_flag}"
        )

    # ── Step 3: Score ─────────────────────────────────────────────────────────
    logger.info("\n[3/3] Scoring signal...")
    from app.insiders.scorer import score_trades
    signal = score_trades(trades)

    print(f"\n{'='*60}")
    print(f"  TICKER:    {signal.ticker}")
    print(f"  SIGNAL:    {signal.signal_type}")
    print(f"  CONVICTION: {signal.conviction_score:.1f} / 10")
    print(f"  CLUSTER:   {'YES — ' + signal.cluster_description if signal.cluster_detected else 'No'}")
    print(f"  RATIONALE: {signal.rationale[:200]}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
