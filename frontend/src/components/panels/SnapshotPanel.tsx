import React from 'react';
import { RefreshCw } from 'lucide-react';
import { useApi } from '../../hooks/useApi';
import type { SnapshotOut } from '../../types';

interface Props { investorId: string }

function Th({ children, right }: { children: React.ReactNode; right?: boolean }) {
  return (
    <th className={`px-3 py-1.5 text-t-muted tracking-wider font-bold text-2xs ${right ? 'text-right' : 'text-left'}`}>
      {children}
    </th>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-2xs text-t-muted uppercase tracking-widest">{label}</span>
      <span className="text-t-orange font-bold text-xs mt-0.5">{value}</span>
    </div>
  );
}

function LoadingRows() {
  return (
    <>
      {Array.from({ length: 10 }).map((_, i) => (
        <tr key={i} className="trow">
          {[40, 60, 140, 55, 90, 80, 40].map((w, j) => (
            <td key={j} className="px-3 py-2">
              <div className="skeleton h-3 rounded" style={{ width: w }} />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

export default function SnapshotPanel({ investorId }: Props) {
  const { data, loading, error, refetch } = useApi<SnapshotOut>(
    `/api/investors/${investorId}/snapshot`
  );

  return (
    <div className="flex flex-col h-full animate-fade-up">
      <div className="panel-header">
        <span>13F HOLDINGS — LATEST SNAPSHOT</span>
        <button
          onClick={refetch}
          disabled={loading}
          className="ml-auto text-t-muted hover:text-t-orange transition-colors disabled:opacity-40"
          title="Refresh"
        >
          <RefreshCw size={10} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {error && (
        <div className="m-4 p-3 bg-[rgba(240,60,60,0.08)] border border-t-red text-t-red text-2xs rounded">
          {error}
        </div>
      )}

      {data && (
        <div className="flex gap-6 px-4 py-2.5 border-b border-t-border flex-shrink-0 flex-wrap bg-t-panel">
          <Stat label="AUM" value={`$${data.total_aum_billions.toFixed(2)}B`} />
          <Stat label="Holdings" value={String(data.holding_count)} />
          <Stat label="Period" value={data.period_of_report} />
          <Stat label="Filed" value={data.filing_date} />
          <Stat label="Investor" value={data.investor_name} />
        </div>
      )}

      <div className="flex-1 overflow-auto">
        <table className="w-full text-2xs border-collapse">
          <thead className="sticky top-0 z-10">
            <tr className="border-b border-t-border bg-[#0a0b0e]">
              <Th>#</Th>
              <Th>Ticker</Th>
              <Th>Company</Th>
              <Th right>Value $M</Th>
              <Th right>% Port</Th>
              <Th right>Shares</Th>
              <Th>Type</Th>
            </tr>
          </thead>
          <tbody>
            {loading && <LoadingRows />}
            {data?.top_holdings.map(h => (
              <tr key={h.cusip} className="trow">
                <td className="px-3 py-1.5 num text-t-dim w-8">{h.rank}</td>
                <td className="px-3 py-1.5 w-20">
                  <span className="text-t-orange font-bold glow-orange">
                    {h.ticker ?? '—'}
                  </span>
                </td>
                <td className="px-3 py-1.5 text-t-text max-w-[200px] truncate">
                  {h.company_name}
                </td>
                <td className="px-3 py-1.5 num text-t-text text-right">
                  {h.value_millions.toFixed(1)}
                </td>
                <td className="px-3 py-1.5 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <div className="bar-track w-16">
                      <div
                        className="bar-fill bg-t-orange"
                        style={{ width: `${Math.min(h.pct_of_portfolio * 4, 100)}%` }}
                      />
                    </div>
                    <span className="num text-t-text w-10 text-right">
                      {h.pct_of_portfolio.toFixed(1)}%
                    </span>
                  </div>
                </td>
                <td className="px-3 py-1.5 num text-t-muted text-right">
                  {h.shares.toLocaleString()}
                </td>
                <td className="px-3 py-1.5">
                  {h.put_call ? (
                    <span className={`badge ${h.put_call.toLowerCase() === 'put' ? 'action-sell' : 'action-buy'}`}>
                      {h.put_call}
                    </span>
                  ) : (
                    <span className="badge signal-new">EQ</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
