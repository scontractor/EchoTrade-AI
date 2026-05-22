import { useState, useCallback } from 'react';
import { Search, Download, BarChart2, AlertCircle } from 'lucide-react';
import type { InsiderSignal, InsiderTradeOut } from '../../types';

const SIGNAL_STYLE: Record<InsiderSignal['signal_type'], string> = {
  STRONG_BUY:  'text-t-green glow-green',
  BUY:         'text-t-green',
  NEUTRAL:     'text-t-yellow',
  SELL:        'text-t-red',
  STRONG_SELL: 'text-t-red glow-red',
};

function TradeRow({ t }: { t: InsiderTradeOut }) {
  const isBuy = t.acquired_or_disposed === 'A';
  return (
    <tr className="trow">
      <td className="px-3 py-1.5 w-16">
        <span className="text-t-orange font-bold">{t.issuer_ticker}</span>
      </td>
      <td className="px-3 py-1.5 max-w-[150px] truncate text-t-text">{t.owner_name}</td>
      <td className="px-3 py-1.5 max-w-[100px] truncate text-t-muted">
        {t.officer_title ?? 'Director'}
      </td>
      <td className="px-3 py-1.5">
        <span className={`badge ${isBuy ? 'action-buy' : 'action-sell'}`}>
          {isBuy ? '▲ BUY' : '▼ SELL'}
        </span>
      </td>
      <td className="px-3 py-1.5 num text-t-text text-right">
        {t.shares != null ? t.shares.toLocaleString() : '—'}
      </td>
      <td className="px-3 py-1.5 num text-t-text text-right">
        {t.price_per_share != null ? `$${t.price_per_share.toFixed(2)}` : '—'}
      </td>
      <td className="px-3 py-1.5 num text-t-text text-right">
        {t.total_value != null
          ? t.total_value >= 1_000_000
            ? `$${(t.total_value / 1_000_000).toFixed(2)}M`
            : `$${(t.total_value / 1000).toFixed(0)}K`
          : '—'}
      </td>
      <td className="px-3 py-1.5">
        {t.is_10b51_plan ? (
          <span className="badge text-t-dim bg-t-faint">10b5-1</span>
        ) : (
          <span className="badge signal-inc">OPEN MKT</span>
        )}
      </td>
      <td className="px-3 py-1.5 text-t-muted">{t.transaction_date}</td>
    </tr>
  );
}

export default function InsiderPanel() {
  const [ticker, setTicker] = useState('');
  const [ingesting, setIngesting] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [signal, setSignal] = useState<InsiderSignal | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = useCallback(async () => {
    const sym = ticker.trim().toUpperCase();
    if (!sym) return;
    setError(null);
    setSignal(null);
    setIngesting(true);

    try {
      setStatusMsg(`Fetching Form 4 filings for ${sym}…`);
      const ingestRes = await window.fetch(`/api/insiders/ingest/${sym}`, { method: 'POST' });
      if (!ingestRes.ok) {
        const body = await ingestRes.json().catch(() => ({}));
        throw new Error((body as { detail?: string }).detail ?? `Ingest failed: HTTP ${ingestRes.status}`);
      }

      setStatusMsg(`Scoring insider activity for ${sym}…`);
      const sigRes = await window.fetch(`/api/insiders/${sym}/signal`);
      if (!sigRes.ok) {
        const body = await sigRes.json().catch(() => ({}));
        throw new Error((body as { detail?: string }).detail ?? `Signal failed: HTTP ${sigRes.status}`);
      }
      setSignal((await sigRes.json()) as InsiderSignal);
      setStatusMsg('');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
      setStatusMsg('');
    } finally {
      setIngesting(false);
    }
  }, [ticker]);

  const convictionPct = signal ? (signal.conviction_score / 10) * 100 : 0;

  return (
    <div className="flex flex-col h-full animate-fade-up">
      <div className="panel-header">
        <Search size={10} className="mr-1.5" />
        <span>FORM 4 INSIDER TRADES</span>
        {signal && (
          <span className="ml-3 text-t-dim normal-case tracking-normal font-normal text-2xs">
            {signal.trades.length} filings · {signal.ticker}
          </span>
        )}
      </div>

      {/* Search bar */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-t-border bg-t-panel flex-shrink-0 flex-wrap">
        <input
          type="text"
          value={ticker}
          onChange={e => setTicker(e.target.value.toUpperCase())}
          onKeyDown={e => e.key === 'Enter' && !ingesting && handleSearch()}
          placeholder="Ticker (e.g. AAPL)"
          maxLength={10}
          className="term-input w-36 uppercase"
          disabled={ingesting}
        />
        <button
          onClick={handleSearch}
          disabled={ingesting || !ticker.trim()}
          className="flex items-center gap-1.5 px-4 py-1.5 bg-t-orange text-black font-bold text-2xs tracking-widest uppercase rounded hover:bg-orange-400 transition-colors disabled:opacity-50"
        >
          <Download size={10} />
          {ingesting ? 'Fetching…' : 'Ingest + Score'}
        </button>
        {statusMsg && (
          <span className="text-t-muted text-2xs animate-pulse">{statusMsg}</span>
        )}
      </div>

      {error && (
        <div className="m-4 p-3 bg-[rgba(240,60,60,0.08)] border border-t-red text-t-red text-2xs rounded flex gap-2">
          <AlertCircle size={12} className="flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {signal && (
        <>
          {/* Signal summary header */}
          <div className="flex gap-6 px-4 py-3 border-b border-t-border flex-shrink-0 flex-wrap items-center bg-t-panel">
            <div>
              <div className="text-2xs text-t-muted uppercase tracking-widest mb-0.5">Signal</div>
              <div className={`text-xl font-bold ${SIGNAL_STYLE[signal.signal_type]}`}>
                {signal.signal_type.replace('_', ' ')}
              </div>
            </div>

            <div>
              <div className="text-2xs text-t-muted uppercase tracking-widest mb-1">Conviction</div>
              <div className="flex items-center gap-2">
                <div className="bar-track w-28">
                  <div
                    className="bar-fill transition-all"
                    style={{
                      width: `${convictionPct}%`,
                      background:
                        convictionPct >= 70
                          ? '#16c96e'
                          : convictionPct >= 40
                          ? '#e6b800'
                          : '#f03c3c',
                    }}
                  />
                </div>
                <span className="num text-t-orange font-bold">
                  {signal.conviction_score.toFixed(1)}/10
                </span>
              </div>
            </div>

            {signal.cluster_detected && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded border border-t-blue-dim bg-[rgba(59,142,255,0.08)]">
                <BarChart2 size={10} className="text-t-blue" />
                <span className="text-t-blue text-2xs font-bold">CLUSTER DETECTED</span>
                {signal.cluster_description && (
                  <span className="text-t-muted text-2xs">{signal.cluster_description}</span>
                )}
              </div>
            )}

            <div className="flex-1 min-w-[200px]">
              <div className="text-2xs text-t-muted uppercase tracking-widest mb-0.5">Rationale</div>
              <p className="text-t-text text-2xs leading-relaxed">{signal.rationale}</p>
            </div>
          </div>

          {signal.ai_commentary && (
            <div className="px-4 py-2.5 border-b border-t-border flex-shrink-0 bg-t-surface">
              <div className="text-2xs text-t-orange font-bold uppercase tracking-widest mb-1">
                AI Commentary
              </div>
              <p className="text-t-text text-xs leading-relaxed">{signal.ai_commentary}</p>
            </div>
          )}

          {/* Trades table */}
          <div className="flex-1 overflow-auto">
            <table className="w-full text-2xs border-collapse">
              <thead className="sticky top-0 z-10">
                <tr className="border-b border-t-border bg-[#0a0b0e]">
                  {['Ticker', 'Insider', 'Title', 'Txn', 'Shares', 'Price', 'Value', 'Type', 'Date'].map(h => (
                    <th
                      key={h}
                      className="px-3 py-1.5 text-t-muted tracking-wider font-bold text-left text-2xs"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {signal.trades.map((t, i) => (
                  <TradeRow key={i} t={t} />
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {!signal && !ingesting && !error && (
        <div className="flex flex-col items-center justify-center flex-1 gap-3 text-t-muted">
          <Search size={44} className="text-t-faint" />
          <p className="text-xs">Enter a ticker to fetch and score Form 4 filings</p>
          <p className="text-2xs text-t-dim">Pulls 90 days of SEC EDGAR data via edgartools</p>
        </div>
      )}
    </div>
  );
}
