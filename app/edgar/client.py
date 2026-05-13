"""
SEC EDGAR async client.

Fetches 13F-HR filings for a given CIK and resolves CUSIP codes to
ticker symbols using SEC's free company_tickers_exchange.json lookup.
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .parser import RawHolding, parse_infotable

logger = logging.getLogger(__name__)

EDGAR_BASE = "https://data.sec.gov"
EDGAR_ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
# SEC requires a descriptive User-Agent (https://www.sec.gov/developer)
HEADERS = {
    "User-Agent": "EchoTrade-AI research@echotrade.ai",
    "Accept-Encoding": "gzip, deflate",
}


@dataclass
class FilingMeta:
    accession_number: str
    filing_date: str
    report_date: str


@dataclass
class Holding:
    cusip: str
    company_name: str
    title_of_class: str
    value_thousands: int
    shares: int
    investment_discretion: str
    ticker: Optional[str] = None
    put_call: Optional[str] = None


@dataclass
class FilingSnapshot:
    cik: str
    investor_name: str
    period_of_report: str
    filing_date: str
    accession_number: str
    holdings: list[Holding] = field(default_factory=list)

    @property
    def total_value_thousands(self) -> int:
        return sum(h.value_thousands for h in self.holdings)

    @property
    def holding_count(self) -> int:
        return len(self.holdings)


class _TickerResolver:
    """Maps EDGAR company names to ticker symbols via SEC's ticker exchange JSON."""

    def __init__(self):
        self._name_map: dict[str, str] = {}  # normalised_name → ticker
        self._loaded = False

    async def load(self, client: httpx.AsyncClient) -> None:
        if self._loaded:
            return
        try:
            resp = await client.get(
                "https://www.sec.gov/files/company_tickers_exchange.json",
                headers=HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("data", []):
                _, name, ticker, _ = item
                self._name_map[self._norm(name)] = ticker
            self._loaded = True
            logger.info("Loaded %d ticker mappings", len(self._name_map))
        except Exception as exc:
            logger.warning("Ticker mapping load failed: %s", exc)

    def resolve(self, company_name: str) -> Optional[str]:
        key = self._norm(company_name)
        if key in self._name_map:
            return self._name_map[key]
        # Strip common corporate suffixes
        for suffix in (" inc", " corp", " co", " ltd", " llc", " lp", " plc", " group", " holdings"):
            trimmed = key.removesuffix(suffix).strip()
            if trimmed in self._name_map:
                return self._name_map[trimmed]
        # First-word prefix match (only for words > 4 chars to avoid false positives)
        first = key.split()[0] if key.split() else ""
        if len(first) > 4:
            for k, ticker in self._name_map.items():
                if k.startswith(first) and abs(len(k) - len(key)) < 8:
                    return ticker
        return None

    @staticmethod
    def _norm(name: str) -> str:
        name = name.lower()
        name = re.sub(r"[^\w\s]", " ", name)
        return re.sub(r"\s+", " ", name).strip()


class EDGARClient:
    def __init__(self):
        self._http = httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=True)
        self._resolver = _TickerResolver()

    async def _ensure_resolver(self) -> None:
        await self._resolver.load(self._http)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def _get(self, url: str) -> httpx.Response:
        resp = await self._http.get(url)
        resp.raise_for_status()
        return resp

    async def get_recent_filings(self, cik: str, count: int = 4) -> list[FilingMeta]:
        """Return the most recent `count` 13F-HR filings for a CIK."""
        padded = cik.zfill(10)
        data = (await self._get(f"{EDGAR_BASE}/submissions/CIK{padded}.json")).json()

        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        results: list[FilingMeta] = []

        for i, form in enumerate(forms):
            if form in ("13F-HR", "13F-HR/A"):
                results.append(FilingMeta(
                    accession_number=recent["accessionNumber"][i],
                    filing_date=recent["filingDate"][i],
                    report_date=recent["reportDate"][i],
                ))
                if len(results) >= count:
                    break

        return results

    async def _find_infotable_url(self, cik: str, accession_number: str) -> Optional[str]:
        cik_int = int(cik)
        acc_clean = accession_number.replace("-", "")
        index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_clean}/{accession_number}-index.json"

        try:
            resp = await self._http.get(index_url, timeout=10)
            if resp.status_code == 200:
                for item in resp.json().get("directory", {}).get("item", []):
                    name: str = item.get("name", "")
                    doc_type: str = item.get("type", "").upper()
                    if "infotable" in name.lower() or doc_type == "INFORMATION TABLE":
                        return f"{EDGAR_ARCHIVES}/{cik_int}/{acc_clean}/{name}"
        except Exception as exc:
            logger.debug("Index JSON fetch failed: %s", exc)

        # Fallback: try known filenames
        for fname in ("infotable.xml", "form13fInfoTable.xml", "informationtable.xml"):
            url = f"{EDGAR_ARCHIVES}/{cik_int}/{acc_clean}/{fname}"
            try:
                head = await self._http.head(url, timeout=5)
                if head.status_code == 200:
                    return url
            except Exception:
                continue

        return None

    async def get_snapshot(self, cik: str, investor_name: str, filing: FilingMeta) -> Optional[FilingSnapshot]:
        await self._ensure_resolver()

        xml_url = await self._find_infotable_url(cik, filing.accession_number)
        if not xml_url:
            logger.error("infotable not found for CIK %s / %s", cik, filing.accession_number)
            return None

        xml_text = (await self._get(xml_url)).text
        raw_holdings = parse_infotable(xml_text)

        holdings = [
            Holding(
                cusip=r.cusip,
                company_name=r.company_name,
                title_of_class=r.title_of_class,
                value_thousands=r.value_thousands,
                shares=r.shares,
                investment_discretion=r.investment_discretion,
                ticker=self._resolver.resolve(r.company_name),
                put_call=r.put_call,
            )
            for r in raw_holdings
        ]

        return FilingSnapshot(
            cik=cik,
            investor_name=investor_name,
            period_of_report=filing.report_date,
            filing_date=filing.filing_date,
            accession_number=filing.accession_number,
            holdings=holdings,
        )

    async def get_two_latest_snapshots(
        self, cik: str, investor_name: str
    ) -> tuple[Optional[FilingSnapshot], Optional[FilingSnapshot]]:
        filings = await self.get_recent_filings(cik, count=2)
        if not filings:
            return None, None

        snapshots = await asyncio.gather(
            *[self.get_snapshot(cik, investor_name, f) for f in filings],
            return_exceptions=False,
        )
        current = snapshots[0] if len(snapshots) > 0 else None
        previous = snapshots[1] if len(snapshots) > 1 else None
        return current, previous
