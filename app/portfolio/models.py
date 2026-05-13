from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, computed_field


class HoldingOut(BaseModel):
    rank: int
    ticker: Optional[str]
    company_name: str
    cusip: str
    value_millions: float
    pct_of_portfolio: float
    shares: int
    put_call: Optional[str] = None


class SnapshotOut(BaseModel):
    investor_name: str
    period_of_report: str
    filing_date: str
    total_aum_billions: float
    holding_count: int
    top_holdings: list[HoldingOut]


class HoldingChange(BaseModel):
    cusip: str
    company_name: str
    ticker: Optional[str]
    action: Literal["NEW", "INCREASED", "DECREASED", "EXITED", "UNCHANGED"]
    prev_shares: Optional[int] = None
    curr_shares: Optional[int] = None
    shares_change_pct: Optional[float] = None
    prev_value_thousands: Optional[int] = None
    curr_value_thousands: Optional[int] = None
    value_change_pct: Optional[float] = None
    curr_pct_of_portfolio: Optional[float] = None
    prev_pct_of_portfolio: Optional[float] = None

    @computed_field
    @property
    def current_value_millions(self) -> Optional[float]:
        return round(self.curr_value_thousands / 1000, 2) if self.curr_value_thousands else None


class DiffSummary(BaseModel):
    new_positions: int
    exited_positions: int
    increased_positions: int
    decreased_positions: int
    unchanged_positions: int


class DiffOut(BaseModel):
    investor_name: str
    current_period: str
    previous_period: str
    total_value_change_pct: float
    summary: DiffSummary
    changes: list[HoldingChange]


class TradingSignal(BaseModel):
    ticker: str
    company_name: str
    action: Literal["BUY", "ADD", "HOLD", "TRIM", "SELL"]
    confidence: float  # 0–1
    rationale: str
    sentiment_alignment: Literal["SUPPORTS", "NEUTRAL", "CONTRADICTS"] = "NEUTRAL"
    institutional_conviction: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"


class PortfolioAnalysis(BaseModel):
    investor_name: str
    period: str
    executive_summary: str
    strategy_style: str
    key_themes: list[str]
    signals: list[TradingSignal]
    risk_factors: list[str]
    model_used: str = "claude-sonnet-4-6"


class CloneAllocation(BaseModel):
    ticker: Optional[str]
    company_name: str
    allocation_pct: float
    allocation_usd: float
    institutional_value_millions: float


class CloneOut(BaseModel):
    investor_name: str
    period_of_report: str
    total_capital_usd: float
    strategy: str
    allocations: list[CloneAllocation]
