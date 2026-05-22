import React from 'react';
import { RefreshCw, ArrowRight } from 'lucide-react';
import { useApi } from '../../hooks/useApi';
import type { DiffOut, HoldingChange } from '../../types';

interface Props { investorId: string }

const ACTION_BADGE: Record<HoldingChange['action'], string> = {
  NEW:       'signal-new',
  INCREASED: 'signal-inc',
  DECREASED: 'signal-dec',
  EXITED:    'signal-exit',
  UNCHANGED: '',
};

const ACTION_TICKER_COLOR: Record<HoldingChange['action'], string> = {
  NEW:       'text-t-blue',
  INCREASED: 'text-t-green glow-green',
  DECREASED: 'text-t-yellow',
  EXITED:    'text-t-red glow-red',
  UNCHANGED: 'text-t-muted',
};

function SummaryCard({
  label, count, colorClass,
}: { label: string; count: number; colorClass: string }) {
  return (
    <div className={`flex flex-col items-center px-5 py-2 rounded border ${colorClass}`}>
      <span className="text-2xs font-bold tracking-widest uppercase opacity-80">{label}</span>
      <span className="text-2xl font-bold mt-0.5 num">{count}</span>
    </div>
  );
}

function Th({ children, right }: { children: React.ReactNode; right?: boolean }) {
  return (
    <th className={`px-3 py-1.5 text-t-muted tracking-wider font-bold text-2xs ${right ? 'text-right' : 'text-left'}`}>
      {children}
    </th>
  );
}

export default function DiffPanel({ investorId }: Props) {
  const { data, loading, error, refetch } = useApi<DiffOut>(
    `/api/investors/${investorId}/diff`
  );

  return (
    <div className="flex flex-col h-full animate-fade-up">
      <div className="panel-header">
        <span>QUARTER-OVER-QUARTER CHANGES</span>
        <button
          onClick={refetch}
          disabled={loading}
          className="ml-auto text-t-muted hover:text-t-orange transition-colors disabled:opacity-40"
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
        <>
          {/* Summary cards */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-t-border bg-t-panel flex-shrink-0 flex-wrap">
            <SummaryCard
              label="New"
              count={data.summary.new_positions}
              colorClass="text-t-blue border-t-blue-dim bg-[rgba(59,142,255,0.06)]"
            />
            <SummaryCard
              label="Increased"
              count={data.summary.increased_positions}
              colorClass="text-t-green border-t-green-dim bg-[rgba(22,201,110,0.06)]"
            />
            <SummaryCard
              label="Decreased"
              count={data.summary.decreased_positions}
              colorClass="text-t-yellow border-[#6b4800] bg-[rgba(230,184,0,0.06)]"
            />
            <SummaryCard
              label="Exited"
              count={data.summary.exited_positions}
              colorClass="text-t-red border-t-red-dim bg-[rgba(240,60,60,0.06)]"
            />

            <div className="ml-auto text-right flex flex-col">
              <span className="text-2xs text-t-muted uppercase tracking-widest">AUM Δ</span>
              <span
                className={`font-bold text-lg num mt-0.5 ${data.total_value_change_pct >= 0 ? 'text-t-green glow-green' : 'text-t-red glow-red'}`}
              >
                {data.total_value_change_pct >= 0 ? '+' : ''}
                {data.total_value_change_pct.toFixed(1)}%
              </span>
            </div>
          </div>

          {/* Period range */}
          <div className="flex items-center gap-2 px-4 py-1.5 border-b border-t-border text-2xs text-t-muted bg-t-surface flex-shrink-0">
            <span className="text-t-dim">{data.previous_period}</span>
            <ArrowRight size={10} className="text-t-orange" />
            <span className="text-t-text">{data.current_period}</span>
          </div>
        </>
      )}

      <div className="flex-1 overflow-auto">
        <table className="w-full text-2xs border-collapse">
          <thead className="sticky top-0 z-10">
            <tr className="border-b border-t-border bg-[#0a0b0e]">
              <Th>Action</Th>
              <Th>Ticker</Th>
              <Th>Company</Th>
              <Th right>Value $M</Th>
              <Th right>% Port</Th>
              <Th right>Shares Δ%</Th>
              <Th right>Value Δ%</Th>
            </tr>
          </thead>
          <tbody>
            {loading &&
              Array.from({ length: 10 }).map((_, i) => (
                <tr key={i} className="trow">
                  {[50, 60, 150, 60, 60, 60, 60].map((w, j) => (
                    <td key={j} className="px-3 py-2">
                      <div className="skeleton h-3 rounded" style={{ width: w }} />
                    </td>
                  ))}
                </tr>
              ))}
            {data?.changes
              .filter(c => c.action !== 'UNCHANGED')
              .map((c, i) => (
                <tr key={i} className="trow">
                  <td className="px-3 py-1.5">
                    <span className={`badge ${ACTION_BADGE[c.action]}`}>{c.action}</span>
                  </td>
                  <td className="px-3 py-1.5 w-20">
                    <span className={`font-bold ${ACTION_TICKER_COLOR[c.action]}`}>
                      {c.ticker ?? '—'}
                    </span>
                  </td>
                  <td className="px-3 py-1.5 text-t-text max-w-[180px] truncate">
                    {c.company_name}
                  </td>
                  <td className="px-3 py-1.5 num text-t-text text-right">
                    {c.current_value_millions != null
                      ? c.current_value_millions.toFixed(1)
                      : '—'}
                  </td>
                  <td className="px-3 py-1.5 num text-t-text text-right">
                    {c.curr_pct_of_portfolio != null
                      ? `${c.curr_pct_of_portfolio.toFixed(1)}%`
                      : '—'}
                  </td>
                  <td className="px-3 py-1.5 num text-right">
                    {c.shares_change_pct != null ? (
                      <span className={c.shares_change_pct >= 0 ? 'text-t-green' : 'text-t-red'}>
                        {c.shares_change_pct >= 0 ? '+' : ''}
                        {c.shares_change_pct.toFixed(1)}%
                      </span>
                    ) : '—'}
                  </td>
                  <td className="px-3 py-1.5 num text-right">
                    {c.value_change_pct != null ? (
                      <span className={c.value_change_pct >= 0 ? 'text-t-green' : 'text-t-red'}>
                        {c.value_change_pct >= 0 ? '+' : ''}
                        {c.value_change_pct.toFixed(1)}%
                      </span>
                    ) : '—'}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
