"""
SQLite read-through cache for 13F filing snapshots.

Keyed on SEC accession_number, which is immutable — once a filing is accepted
by the SEC it never changes, so a cached snapshot is valid forever. New filings
are detected by always calling get_recent_filings() live (one fast request);
only the slow infotable XML fetch is cached.

Works with plain dicts rather than importing FilingSnapshot/Holding dataclasses
to avoid a circular import with client.py.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class FilingSnapshotRow(Base):
    __tablename__ = "filing_snapshots"

    accession_number = Column(String(25), primary_key=True)
    cik = Column(String(12), nullable=False, index=True)
    investor_name = Column(String(200), nullable=False)
    period_of_report = Column(String(10), nullable=False)
    filing_date = Column(String(10), nullable=False)
    holdings_json = Column(Text, nullable=False)
    cached_at = Column(DateTime, default=datetime.utcnow)


def _get_engine(db_url: str):
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    return engine


class FilingCache:
    """Read-through cache for 13F snapshots. Keyed on SEC accession_number."""

    def __init__(self, db_url: str = "sqlite:///echotrade.db"):
        self._engine = _get_engine(db_url)

    def get(self, accession_number: str) -> Optional[dict]:
        """Return cached snapshot as a plain dict, or None on miss."""
        with Session(self._engine) as session:
            row = session.get(FilingSnapshotRow, accession_number)
            if row is None:
                return None
            try:
                return {
                    "cik": row.cik,
                    "investor_name": row.investor_name,
                    "period_of_report": row.period_of_report,
                    "filing_date": row.filing_date,
                    "accession_number": row.accession_number,
                    "holdings": json.loads(row.holdings_json),
                }
            except Exception as exc:
                logger.warning("Cache deserialise error for %s: %s", accession_number, exc)
                return None

    def put(self, snapshot_dict: dict) -> None:
        """Store a snapshot dict. merge() makes this a safe upsert."""
        row = FilingSnapshotRow(
            accession_number=snapshot_dict["accession_number"],
            cik=snapshot_dict["cik"],
            investor_name=snapshot_dict["investor_name"],
            period_of_report=snapshot_dict["period_of_report"],
            filing_date=snapshot_dict["filing_date"],
            holdings_json=json.dumps(snapshot_dict["holdings"]),
        )
        with Session(self._engine) as session:
            session.merge(row)
            session.commit()
        logger.debug("Cached snapshot %s", snapshot_dict["accession_number"])
