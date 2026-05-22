import { useState, useCallback } from 'react';
import { Copy, DollarSign, SlidersHorizontal } from 'lucide-react';
import type { CloneOut } from '../../types';

interface Props { investorId: string }

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col min-w-0">
      <span className="text-2xs text-t-muted uppercase tracking-widest">{label}</span>
      <span className="text-t-orange font-bold text-xs mt-0.5 truncate">{value}</span>
    </div>
  );
}

export default function ClonePanel({ investorId }: Props) {
  const [capital, setCapital] = useState('50000');
  const [topN, setTopN] = useState(20);
  const [data, setData] = useState<CloneOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async () => {
    const cap = parseFloat(capital);
    if (isNaN(cap) || cap < 100) return;
    setLoading(true);
    setError(null);
    try {
      const res = await window.fetch(
        `/api/investors/${investorId}/clone?capital=${cap}&top_n=${topN}`
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error((body as { detail?: string }).detail ?? `HTTP ${res.status}`);
      }
      setData((await res.json()) as CloneOut);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error');
    } finally {
      setLoading(false);
    }
  }, [investorId, capital, topN]);

  const totalAllocated = data?.allocations.reduce((s, a) => s + a.allocation_usd, 0) ?? 0;

  return (
    <div className="flex flex-col h-full animate-fade-up">
      <div className="panel-header">
        <Copy size={10} className="mr-1.5" />
        <span>PORTFOLIO CLONE CALCULATOR</span>
      </div>

      {/* Controls */}
      <div className="flex items-end gap-6 px-4 py-3 border-b border-t-border bg-t-panel flex-shrink-0 flex-wrap">
        <div className="flex flex-col gap-1">
          <label className="text-2xs text-t-muted uppercase tracking-widest">Capital (USD)</label>
          <div className="flex items-center gap-1">
            <DollarSign size={10} className="text-t-orange" />
            <input
              type="number"
              min={100}
              step={1000}
              value={capital}
              onChange={e => setCapital(e.target.value)}
              className="term-input w-32"
            />
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-2xs text-t-muted uppercase tracking-widest flex items-center gap-1">
            <SlidersHorizontal size={9} /> Top N Holdings:
            <span className="text-t-orange ml-1">{topN}</span>
          </label>
          <input
            type="range"
            min={5}
            max={50}
            value={topN}
            onChange={e => setTopN(parseInt(e.target.value))}
            className="w-32 accent-[#f56a00]"
          />
        </div>

        <button
          onClick={run}
          disabled={loading}
          className="px-5 py-2 bg-t-orange text-black font-bold text-2xs tracking-widest uppercase rounded hover:bg-orange-400 transition-colors disabled:opacity-50"
        >
          {loading ? 'Calculating…' : 'Generate Clone'}
        </button>
      </div>

      {error && (
        <div className="m-4 p-3 bg-[rgba(240,60,60,0.08)] border border-t-red text-t-red text-2xs rounded">
          {error}
        </div>
      )}

      {data && (
        <>
          <div className="flex gap-6 px-4 py-2.5 border-b border-t-border flex-shrink-0 flex-wrap items-center">
            <Stat label="Investor" value={data.investor_name} />
            <Stat label="Period" value={data.period_of_report} />
            <Stat label="Capital" value={`$${parseFloat(capital).toLocaleString()}`} />
            <Stat label="Allocated" value={`$${totalAllocated.toLocaleString(undefined, { maximumFractionDigits: 0 })}`} />
            <Stat label="Strategy" value={data.strategy} />
          </div>

          <div className="flex-1 overflow-auto">
            <table className="w-full text-2xs border-collapse">
              <thead className="sticky top-0 z-10">
                <tr className="border-b border-t-border bg-[#0a0b0e]">
                  {[
                    { label: 'Ticker', right: false },
                    { label: 'Company', right: false },
                    { label: 'Alloc %', right: true },
                    { label: 'Alloc $', right: true },
                    { label: 'Inst. Value $M', right: true },
                  ].map(({ label, right }) => (
                    <th
                      key={label}
                      className={`px-3 py-1.5 text-t-muted tracking-wider font-bold text-2xs ${right ? 'text-right' : 'text-left'}`}
                    >
                      {label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.allocations.map((a, i) => (
                  <tr key={i} className="trow">
                    <td className="px-3 py-1.5 w-20">
                      <span className="text-t-orange font-bold">{a.ticker ?? '—'}</span>
                    </td>
                    <td className="px-3 py-1.5 text-t-text max-w-[200px] truncate">
                      {a.company_name}
                    </td>
                    <td className="px-3 py-1.5 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="bar-track w-16">
                          <div
                            className="bar-fill bg-t-orange"
                            style={{ width: `${Math.min(a.allocation_pct * 4, 100)}%` }}
                          />
                        </div>
                        <span className="num text-t-text w-10 text-right">
                          {a.allocation_pct.toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-3 py-1.5 num text-t-green font-bold text-right">
                      ${a.allocation_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </td>
                    <td className="px-3 py-1.5 num text-t-muted text-right">
                      {a.institutional_value_millions.toFixed(1)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {!data && !loading && !error && (
        <div className="flex flex-col items-center justify-center flex-1 gap-3 text-t-muted">
          <Copy size={44} className="text-t-faint" />
          <p className="text-xs">Configure capital and click Generate Clone</p>
          <p className="text-2xs text-t-dim">Proportionally mirrors the investor's top holdings</p>
        </div>
      )}
    </div>
  );
}
