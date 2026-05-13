"""
SQLAlchemy + Pydantic models for SEC Form 4 insider trades.

Schema covers the 2023 SEC amendments requiring mandatory Rule 10b5-1
plan disclosure and cooling-off period data on every Form 4 submission.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, computed_field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Session

# Transaction code → human label (SEC Form 4 codes)
TRANSACTION_CODES: dict[str, str] = {
    "P": "Open Market Purchase",
    "S": "Open Market Sale",
    "A": "Grant / Award",
    "D": "Disposition to Issuer",
    "F": "Tax Withholding",
    "G": "Gift",
    "I": "Discretionary Transaction",
    "J": "Other Acquisition / Disposition",
    "M": "Option / Warrant Exercise",
    "C": "Conversion of Derivative",
    "E": "Expiration of Derivative",
    "H": "Expiration of Out-of-Money Derivative",
    "O": "Exercise of Out-of-Money Derivative",
    "X": "Exercise / Conversion of Derivative",
    "Z": "Deposit into Voting Trust",
    "W": "Acquisition by Will / Inheritance",
    "K": "Equity Swap or Instrument",
    "U": "Tender of Shares",
    "L": "Small Acquisition (Rule 16a-6)",
    "V": "Voluntarily Reported",
}


class Base(DeclarativeBase):
    pass


class InsiderTrade(Base):
    """One non-derivative transaction from a Form 4 filing."""

    __tablename__ = "insider_trades"
    __table_args__ = (
        UniqueConstraint("accession_number", "transaction_sequence", name="uq_trade"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    accession_number = Column(String(25), nullable=False, index=True)
    filing_date = Column(String(10), nullable=False)

    # Issuer
    issuer_cik = Column(String(12), nullable=False)
    issuer_ticker = Column(String(10), nullable=False, index=True)
    issuer_name = Column(String(200), nullable=False)

    # Reporting owner
    owner_cik = Column(String(12))
    owner_name = Column(String(200), nullable=False)
    owner_is_director = Column(Boolean, default=False)
    owner_is_officer = Column(Boolean, default=False)
    owner_is_ten_pct = Column(Boolean, default=False)
    officer_title = Column(String(100))

    # Transaction
    transaction_sequence = Column(Integer, default=0)
    transaction_date = Column(String(10), nullable=False)
    security_title = Column(String(100))
    transaction_code = Column(String(2), nullable=False)
    transaction_code_label = Column(String(80))
    acquired_or_disposed = Column(String(1))     # A or D
    shares = Column(Float)
    price_per_share = Column(Float)
    total_value = Column(Float)                  # shares × price
    shares_owned_after = Column(Float)

    # Rule 10b5-1 plan (mandatory since Feb 2023 amendments)
    is_10b51_plan = Column(Boolean, default=False)
    plan_adoption_date = Column(String(10))      # YYYY-MM-DD if disclosed

    ingested_at = Column(DateTime, default=datetime.utcnow)


def get_engine(db_url: str = "sqlite:///echotrade.db"):
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    return engine


# ── Pydantic output schemas ───────────────────────────────────────────────────

class InsiderTradeOut(BaseModel):
    id: Optional[int] = None
    accession_number: str
    filing_date: str
    issuer_ticker: str
    issuer_name: str
    owner_name: str
    officer_title: Optional[str]
    transaction_date: str
    transaction_code: str
    transaction_code_label: Optional[str]
    acquired_or_disposed: Optional[str]
    shares: Optional[float]
    price_per_share: Optional[float]
    total_value: Optional[float]
    shares_owned_after: Optional[float]
    is_10b51_plan: bool
    plan_adoption_date: Optional[str]

    @computed_field
    @property
    def is_open_market_buy(self) -> bool:
        return self.transaction_code == "P" and not self.is_10b51_plan

    class Config:
        from_attributes = True


class InsiderSignal(BaseModel):
    ticker: str
    signal_type: Literal["STRONG_BUY", "BUY", "NEUTRAL", "SELL", "STRONG_SELL"]
    conviction_score: float               # 0–10
    rationale: str
    trades: list[InsiderTradeOut]
    cluster_detected: bool = False
    cluster_description: Optional[str] = None
    ai_commentary: Optional[str] = None
