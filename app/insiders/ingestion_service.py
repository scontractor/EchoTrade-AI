"""
SEC Form 4 ingestion service.

Flow per ticker:
  1. Resolve ticker → company CIK via SEC company_tickers.json
  2. Search EDGAR for recent Form 4 filings that reference that ticker
  3. For each filing, fetch and parse the ownership XML
  4. Upsert InsiderTrade rows (skip duplicates via accession_number unique constraint)

References:
  - https://www.sec.gov/developer  (rate limit: ≤10 req/sec)
  - https://efts.sec.gov/LATEST/search-index  (full-text search)
  - SEC Form 4 XML spec (2023 amendments add rule10b51TranFlag + plan adoption date)
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.insiders.models import InsiderTrade, TRANSACTION_CODES, get_engine
from sqlalchemy.orm import Session
from sqlalchemy import select

logger = logging.getLogger(__name__)

EDGAR_HEADERS = {
    "User-Agent": "EchoTrade-AI research@echotrade.ai",
    "Accept-Encoding": "gzip, deflate",
}
EFTS_SEARCH = "https://efts.sec.gov/LATEST/search-index"
ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
TICKERS_JSON = "https://www.sec.gov/files/company_tickers.json"


@dataclass
class _ParsedTrade:
    accession_number: str
    filing_date: str
    issuer_cik: str
    issuer_ticker: str
    issuer_name: str
    owner_cik: str
    owner_name: str
    owner_is_director: bool
    owner_is_officer: bool
    owner_is_ten_pct: bool
    officer_title: Optional[str]
    transactions: list[dict] = field(default_factory=list)


def _xml_text(elem: ET.Element, *tags: str) -> str:
    """Walk a chain of tag names and return the leaf text, or ''."""
    cur = elem
    for tag in tags:
        nxt = cur.find(f"{{*}}{tag}") or cur.find(tag)
        if nxt is None:
            return ""
        cur = nxt
    return cur.text.strip() if cur.text else ""


def _parse_form4_xml(xml_text: str, accession_number: str, filing_date: str) -> Optional[_ParsedTrade]:
    try:
        root = ET.fromstring(xml_text.strip())
    except ET.ParseError as exc:
        logger.warning("Form4 XML parse error %s: %s", accession_number, exc)
        return None

    issuer_cik = _xml_text(root, "issuer", "issuerCik")
    issuer_ticker = _xml_text(root, "issuer", "issuerTradingSymbol").upper()
    issuer_name = _xml_text(root, "issuer", "issuerName")

    owner_cik = _xml_text(root, "reportingOwner", "reportingOwnerId", "rptOwnerCik")
    owner_name = _xml_text(root, "reportingOwner", "reportingOwnerId", "rptOwnerName")

    rel = root.find("{*}reportingOwner/{*}reportingOwnerRelationship") or \
          root.find("reportingOwner/reportingOwnerRelationship")
    is_director = _xml_text(rel, "isDirector") == "1" if rel is not None else False
    is_officer = _xml_text(rel, "isOfficer") == "1" if rel is not None else False
    is_ten_pct = _xml_text(rel, "isTenPercentOwner") == "1" if rel is not None else False
    officer_title = _xml_text(rel, "officerTitle") if rel is not None else None

    parsed = _ParsedTrade(
        accession_number=accession_number,
        filing_date=filing_date,
        issuer_cik=issuer_cik,
        issuer_ticker=issuer_ticker,
        issuer_name=issuer_name,
        owner_cik=owner_cik,
        owner_name=owner_name,
        owner_is_director=is_director,
        owner_is_officer=is_officer,
        owner_is_ten_pct=is_ten_pct,
        officer_title=officer_title or None,
    )

    # Parse non-derivative transactions (actual share purchases/sales)
    table = root.find("{*}nonDerivativeTable") or root.find("nonDerivativeTable")
    if table is None:
        return parsed

    for seq, txn in enumerate(table):
        if not (txn.tag.endswith("nonDerivativeTransaction") or txn.tag == "nonDerivativeTransaction"):
            continue

        txn_date = _xml_text(txn, "transactionDate", "value") or _xml_text(txn, "transactionDate")
        security = _xml_text(txn, "securityTitle", "value") or _xml_text(txn, "securityTitle")

        coding = txn.find("{*}transactionCoding") or txn.find("transactionCoding")
        code = _xml_text(coding, "transactionCode") if coding is not None else ""
        # 10b5-1 plan flag (introduced in 2023 amendments)
        is_plan = _xml_text(coding, "rule10b51TranFlag") == "1" if coding is not None else False
        plan_date = _xml_text(coding, "rule10b51AdoptionDateFlag") if coding is not None else None

        amounts = txn.find("{*}transactionAmounts") or txn.find("transactionAmounts")
        shares_str = _xml_text(amounts, "transactionShares", "value") if amounts is not None else ""
        price_str = _xml_text(amounts, "transactionPricePerShare", "value") if amounts is not None else ""
        acq_disp = _xml_text(amounts, "transactionAcquiredDisposedCode", "value") if amounts is not None else ""

        post = txn.find("{*}postTransactionAmounts") or txn.find("postTransactionAmounts")
        owned_after_str = _xml_text(post, "sharesOwnedFollowingTransaction", "value") if post is not None else ""

        try:
            shares = float(re.sub(r"[^\d.]", "", shares_str)) if shares_str else None
            price = float(re.sub(r"[^\d.]", "", price_str)) if price_str else None
            owned_after = float(re.sub(r"[^\d.]", "", owned_after_str)) if owned_after_str else None
        except ValueError:
            shares, price, owned_after = None, None, None

        parsed.transactions.append({
            "sequence": seq,
            "transaction_date": txn_date,
            "security_title": security,
            "transaction_code": code,
            "acquired_or_disposed": acq_disp,
            "shares": shares,
            "price_per_share": price,
            "total_value": round(shares * price, 2) if shares and price else None,
            "shares_owned_after": owned_after,
            "is_10b51_plan": is_plan,
            "plan_adoption_date": plan_date or None,
        })

    return parsed


class Form4Client:
    def __init__(self, db_url: str = "sqlite:///echotrade.db"):
        self._http = httpx.Client(headers=EDGAR_HEADERS, timeout=20, follow_redirects=True)
        self._engine = get_engine(db_url)
        self._ticker_cik_cache: dict[str, str] = {}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def _get(self, url: str) -> httpx.Response:
        resp = self._http.get(url)
        resp.raise_for_status()
        return resp

    def _resolve_company_cik(self, ticker: str) -> Optional[str]:
        if ticker in self._ticker_cik_cache:
            return self._ticker_cik_cache[ticker]
        try:
            data = self._get(TICKERS_JSON).json()
            for entry in data.values():
                if entry.get("ticker", "").upper() == ticker.upper():
                    cik = str(entry["cik_str"])
                    self._ticker_cik_cache[ticker] = cik
                    return cik
        except Exception as exc:
            logger.warning("CIK lookup failed for %s: %s", ticker, exc)
        return None

    def _search_form4_filings(
        self, ticker: str, days_back: int = 90
    ) -> list[dict]:
        """Return recent Form 4 filing metadata for a ticker via EDGAR full-text search."""
        start = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        end = datetime.utcnow().strftime("%Y-%m-%d")

        # Search for Form 4 filings mentioning this ticker in issuerTradingSymbol
        params = {
            "q": f'"{ticker}"',
            "forms": "4",
            "dateRange": "custom",
            "startdt": start,
            "enddt": end,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{EFTS_SEARCH}?{query}"

        try:
            data = self._get(url).json()
            hits = data.get("hits", {}).get("hits", [])
            results = []
            for hit in hits[:50]:  # Cap at 50 most recent
                src = hit.get("_source", {})
                # EFTS uses "adsh" (not "accession_no") and "ciks" list (not "entity_id")
                ciks = src.get("ciks", [])
                results.append({
                    "accession_number": src.get("adsh", ""),
                    "filing_date": src.get("file_date", ""),
                    "entity_name": src.get("display_names", [""])[0],
                    "cik": ciks[0].lstrip("0") if ciks else "",
                })
            return results
        except Exception as exc:
            logger.error("EDGAR search failed for %s: %s", ticker, exc)
            return []

    def _fetch_form4_xml(self, cik: str, accession_number: str) -> Optional[str]:
        import re as _re
        cik_int = int(cik) if cik.isdigit() else cik
        acc_clean = accession_number.replace("-", "")
        base = f"{ARCHIVES}/{cik_int}/{acc_clean}"

        # Parse the HTML index — SEC no longer exposes a JSON index for recent filings.
        index_url = f"{base}/{accession_number}-index.html"
        try:
            resp = self._http.get(index_url, timeout=8)
            if resp.status_code == 200:
                rows = _re.findall(r"<tr[^>]*>(.*?)</tr>", resp.text, _re.S | _re.I)
                for row in rows:
                    cells = _re.findall(r"<td[^>]*>(.*?)</td>", row, _re.S | _re.I)
                    if len(cells) >= 4:
                        doc_type = _re.sub(r"<[^>]+>", "", cells[3]).strip().upper()
                        fname = _re.sub(r"<[^>]+>", "", cells[2]).strip()
                        if doc_type in ("4", "4/A") and fname.endswith(".xml"):
                            r = self._http.get(f"{base}/{fname}", timeout=10)
                            if r.status_code == 200:
                                return r.text
        except Exception as exc:
            logger.debug("Form4 HTML index fetch failed %s: %s", accession_number, exc)

        # Fallback: try common filename patterns
        for fname in ("form4.xml", f"{accession_number}.xml", "primary-document.xml"):
            try:
                r = self._http.get(f"{base}/{fname}", timeout=8)
                if r.status_code == 200:
                    return r.text
            except Exception:
                continue
        return None

    def _upsert_trades(self, parsed: _ParsedTrade) -> int:
        """Insert trades, skipping rows that violate the accession_number unique constraint."""
        inserted = 0
        with Session(self._engine) as session:
            for txn in parsed.transactions:
                # Check for duplicate
                exists = session.execute(
                    select(InsiderTrade.id).where(
                        InsiderTrade.accession_number == parsed.accession_number,
                        InsiderTrade.transaction_sequence == txn["sequence"],
                    )
                ).scalar_one_or_none()

                if exists:
                    continue

                code = txn["transaction_code"]
                session.add(InsiderTrade(
                    accession_number=parsed.accession_number,
                    filing_date=parsed.filing_date,
                    issuer_cik=parsed.issuer_cik,
                    issuer_ticker=parsed.issuer_ticker,
                    issuer_name=parsed.issuer_name,
                    owner_cik=parsed.owner_cik,
                    owner_name=parsed.owner_name,
                    owner_is_director=parsed.owner_is_director,
                    owner_is_officer=parsed.owner_is_officer,
                    owner_is_ten_pct=parsed.owner_is_ten_pct,
                    officer_title=parsed.officer_title,
                    transaction_sequence=txn["sequence"],
                    transaction_date=txn["transaction_date"],
                    security_title=txn["security_title"],
                    transaction_code=code,
                    transaction_code_label=TRANSACTION_CODES.get(code, code),
                    acquired_or_disposed=txn["acquired_or_disposed"],
                    shares=txn["shares"],
                    price_per_share=txn["price_per_share"],
                    total_value=txn["total_value"],
                    shares_owned_after=txn["shares_owned_after"],
                    is_10b51_plan=txn["is_10b51_plan"],
                    plan_adoption_date=txn["plan_adoption_date"],
                ))
                inserted += 1

            session.commit()
        return inserted

    def ingest_ticker(self, ticker: str, days_back: int = 90) -> dict:
        """Main entry point. Fetch + parse + store all Form 4 filings for a ticker."""
        ticker = ticker.upper()
        logger.info("Ingesting Form 4 filings for %s (last %d days)", ticker, days_back)

        filings = self._search_form4_filings(ticker, days_back)
        logger.info("Found %d Form 4 filings for %s", len(filings), ticker)

        total_inserted = 0
        errors = 0

        for f in filings:
            acc = f["accession_number"]
            cik = f["cik"]
            if not acc or not cik:
                continue

            xml_text = self._fetch_form4_xml(cik, acc)
            if not xml_text:
                errors += 1
                continue

            parsed = _parse_form4_xml(xml_text, acc, f["filing_date"])
            if not parsed:
                errors += 1
                continue

            # Only keep filings that actually mention this ticker
            if parsed.issuer_ticker and parsed.issuer_ticker != ticker:
                continue

            inserted = self._upsert_trades(parsed)
            total_inserted += inserted

        return {
            "ticker": ticker,
            "filings_processed": len(filings),
            "trades_inserted": total_inserted,
            "parse_errors": errors,
        }

    def get_recent_trades(self, ticker: str, limit: int = 50) -> list[InsiderTrade]:
        """Retrieve stored trades for a ticker, newest first."""
        with Session(self._engine) as session:
            rows = session.execute(
                select(InsiderTrade)
                .where(InsiderTrade.issuer_ticker == ticker.upper())
                .order_by(InsiderTrade.transaction_date.desc())
                .limit(limit)
            ).scalars().all()
            session.expunge_all()
            return list(rows)
