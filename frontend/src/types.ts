export interface InvestorMeta {
  id: string;
  name: string;
  style: string;
  description: string;
}

export interface HoldingOut {
  rank: number;
  ticker: string | null;
  company_name: string;
  cusip: string;
  value_millions: number;
  pct_of_portfolio: number;
  shares: number;
  put_call: string | null;
}

export interface SnapshotOut {
  investor_name: string;
  period_of_report: string;
  filing_date: string;
  total_aum_billions: number;
  holding_count: number;
  top_holdings: HoldingOut[];
}

export interface HoldingChange {
  cusip: string;
  company_name: string;
  ticker: string | null;
  action: 'NEW' | 'INCREASED' | 'DECREASED' | 'EXITED' | 'UNCHANGED';
  prev_shares: number | null;
  curr_shares: number | null;
  shares_change_pct: number | null;
  prev_value_thousands: number | null;
  curr_value_thousands: number | null;
  value_change_pct: number | null;
  curr_pct_of_portfolio: number | null;
  prev_pct_of_portfolio: number | null;
  current_value_millions: number | null;
}

export interface DiffSummary {
  new_positions: number;
  exited_positions: number;
  increased_positions: number;
  decreased_positions: number;
  unchanged_positions: number;
}

export interface DiffOut {
  investor_name: string;
  current_period: string;
  previous_period: string;
  total_value_change_pct: number;
  summary: DiffSummary;
  changes: HoldingChange[];
}

export interface TradingSignal {
  ticker: string;
  company_name: string;
  action: 'BUY' | 'ADD' | 'HOLD' | 'TRIM' | 'SELL';
  confidence: number;
  rationale: string;
  sentiment_alignment: 'SUPPORTS' | 'NEUTRAL' | 'CONTRADICTS';
  institutional_conviction: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface PortfolioAnalysis {
  investor_name: string;
  period: string;
  executive_summary: string;
  strategy_style: string;
  key_themes: string[];
  signals: TradingSignal[];
  risk_factors: string[];
  model_used: string;
}

export interface CloneAllocation {
  ticker: string | null;
  company_name: string;
  allocation_pct: number;
  allocation_usd: number;
  institutional_value_millions: number;
}

export interface CloneOut {
  investor_name: string;
  period_of_report: string;
  total_capital_usd: number;
  strategy: string;
  allocations: CloneAllocation[];
}

export interface InsiderTradeOut {
  id: number | null;
  accession_number: string;
  filing_date: string;
  issuer_ticker: string;
  issuer_name: string;
  owner_name: string;
  officer_title: string | null;
  transaction_date: string;
  transaction_code: string;
  transaction_code_label: string | null;
  acquired_or_disposed: string | null;
  shares: number | null;
  price_per_share: number | null;
  total_value: number | null;
  shares_owned_after: number | null;
  is_10b51_plan: boolean;
  plan_adoption_date: string | null;
  is_open_market_buy: boolean;
}

export interface InsiderSignal {
  ticker: string;
  signal_type: 'STRONG_BUY' | 'BUY' | 'NEUTRAL' | 'SELL' | 'STRONG_SELL';
  conviction_score: number;
  rationale: string;
  trades: InsiderTradeOut[];
  cluster_detected: boolean;
  cluster_description: string | null;
  ai_commentary: string | null;
}
