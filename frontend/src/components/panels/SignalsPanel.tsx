import { useState } from 'react';
import { Zap, AlertTriangle, TrendingUp, BarChart2 } from 'lucide-react';
import { useApi } from '../../hooks/useApi';
import type { PortfolioAnalysis, TradingSignal } from '../../types';

interface Props { investorId: string }

const ACTION_BADGE: Record<TradingSignal['action'], string> = {
  BUY:  'action-buy',
  ADD:  'action-add',
  HOLD: 'action-hold',
  TRIM: 'action-trim',
  SELL: 'action-sell',
};

const CONVICTION_BAR: Record<TradingSignal['institutional_conviction'], string> = {
  HIGH:   'bg-t-green',
  MEDIUM: 'bg-t-yellow',
  LOW:    'bg-t-red',
};

const SENTIMENT_BADGE: Record<TradingSignal['sentiment_alignment'], string> = {
  SUPPORTS:    'signal-inc',
  NEUTRAL:     '',
  CONTRADICTS: 'signal-exit',
};

const SENTIMENT_ICON: Record<TradingSignal['sentiment_alignment'], string> = {
  SUPPORTS:    '↑',
  NEUTRAL:     '→',
  CONTRADICTS: '↓',
};

function SignalRow({ s }: { s: TradingSignal }) {
  return (
    <tr className="trow">
      <td className="px-3 py-2 w-16">
        <span className="text-t-orange font-bold">{s.ticker}</span>
      </td>
      <td className="px-3 py-2 max-w-[140px] truncate text-t-muted">
        {s.company_name}
      </td>
      <td className="px-3 py-2 w-16">
        <span className={`badge ${ACTION_BADGE[s.action]}`}>{s.action}</span>
      </td>
      <td className="px-3 py-2 w-28">
        <div className="flex items-center gap-2">
          <div className="bar-track flex-1">
            <div
              className={`bar-fill ${CONVICTION_BAR[s.institutional_conviction]}`}
              style={{ width: `${s.confidence * 100}%` }}
            />
          </div>
          <span className="num text-t-text w-8 text-right">
            {(s.confidence * 100).toFixed(0)}%
          </span>
        </div>
      </td>
      <td className="px-3 py-2 text-t-muted max-w-xs">
        <span className="line-clamp-2 leading-snug">{s.rationale}</span>
      </td>
      <td className="px-3 py-2">
        <span className={`badge ${SENTIMENT_BADGE[s.sentiment_alignment]}`}>
          {SENTIMENT_ICON[s.sentiment_alignment]} {s.sentiment_alignment}
        </span>
      </td>
      <td className="px-3 py-2">
        <span className="badge text-t-muted bg-t-faint">{s.institutional_conviction}</span>
      </td>
    </tr>
  );
}

export default function SignalsPanel({ investorId }: Props) {
  const [triggered, setTriggered] = useState(false);
  const url = triggered ? `/api/investors/${investorId}/signals` : null;
  const { data, loading, error, refetch } = useApi<PortfolioAnalysis>(url);

  return (
    <div className="flex flex-col h-full animate-fade-up">
      <div className="panel-header">
        <Zap size={10} className="mr-1.5 text-t-orange" />
        <span>AI TRADING SIGNALS</span>
        {data && (
          <span className="ml-3 text-t-dim normal-case tracking-normal font-normal text-2xs">
            via {data.model_used}
          </span>
        )}
        {triggered && !loading && (
          <button
            onClick={refetch}
            className="ml-auto text-t-muted hover:text-t-orange transition-colors text-2xs tracking-widest"
          >
            ↺ REFRESH
          </button>
        )}
      </div>

      {/* Pre-trigger idle state */}
      {!triggered && (
        <div className="flex flex-col items-center justify-center flex-1 gap-4">
          <BarChart2 size={52} className="text-t-faint" />
          <p className="text-t-muted text-xs text-center max-w-xs">
            AI analysis calls your local Ollama instance and may take 30–90 s.
          </p>
          <button
            onClick={() => setTriggered(true)}
            className="px-6 py-2.5 bg-t-orange text-black font-bold text-2xs tracking-widest uppercase rounded hover:bg-orange-400 transition-colors"
          >
            Run Analysis
          </button>
        </div>
      )}

      {/* Loading */}
      {triggered && loading && (
        <div className="flex flex-col items-center justify-center flex-1 gap-4">
          <div className="flex gap-1.5">
            {[0, 1, 2].map(i => (
              <div
                key={i}
                className="w-2 h-2 rounded-full bg-t-orange animate-bounce-dot"
                style={{ animationDelay: `${i * 0.18}s` }}
              />
            ))}
          </div>
          <p className="text-t-muted text-2xs animate-pulse">Ollama is analysing the portfolio…</p>
        </div>
      )}

      {error && (
        <div className="m-4 p-3 bg-[rgba(240,60,60,0.08)] border border-t-red text-t-red text-2xs rounded">
          {error}
        </div>
      )}

      {data && (
        <>
          {/* Executive summary */}
          <div className="px-4 py-3 border-b border-t-border bg-t-panel flex-shrink-0">
            <p className="text-t-text text-xs leading-relaxed">{data.executive_summary}</p>
          </div>

          {/* Themes */}
          <div className="flex items-center gap-2 px-4 py-2 border-b border-t-border flex-shrink-0 flex-wrap">
            <span className="flex items-center gap-1 text-t-muted text-2xs uppercase tracking-widest mr-1">
              <TrendingUp size={9} /> Themes
            </span>
            {data.key_themes.map((t, i) => (
              <span key={i} className="badge signal-new">{t}</span>
            ))}
          </div>

          {/* Signals table */}
          <div className="flex-1 overflow-auto">
            <table className="w-full text-2xs border-collapse">
              <thead className="sticky top-0 z-10">
                <tr className="border-b border-t-border bg-[#0a0b0e]">
                  {['Ticker', 'Company', 'Action', 'Confidence', 'Rationale', 'Sentiment', 'Conviction'].map(h => (
                    <th key={h} className="px-3 py-1.5 text-t-muted tracking-wider font-bold text-left text-2xs">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.signals.map((s, i) => <SignalRow key={i} s={s} />)}
              </tbody>
            </table>
          </div>

          {/* Risk factors */}
          {data.risk_factors.length > 0 && (
            <div className="border-t border-t-border px-4 py-3 flex-shrink-0 bg-t-panel">
              <div className="flex items-center gap-1.5 mb-2">
                <AlertTriangle size={9} className="text-t-yellow" />
                <span className="text-2xs text-t-yellow font-bold uppercase tracking-widest">
                  Risk Factors
                </span>
              </div>
              <ul className="space-y-1">
                {data.risk_factors.map((r, i) => (
                  <li key={i} className="text-2xs text-t-muted flex gap-2">
                    <span className="text-t-yellow flex-shrink-0">▸</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}
