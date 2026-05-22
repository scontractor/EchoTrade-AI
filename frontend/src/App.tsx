import { useState, useEffect } from 'react';
import TopBar from './components/TopBar';
import InvestorSidebar from './components/InvestorSidebar';
import SnapshotPanel from './components/panels/SnapshotPanel';
import DiffPanel from './components/panels/DiffPanel';
import SignalsPanel from './components/panels/SignalsPanel';
import ClonePanel from './components/panels/ClonePanel';
import InsiderPanel from './components/panels/InsiderPanel';
import type { InvestorMeta } from './types';

type Tab = 'snapshot' | 'diff' | 'signals' | 'clone' | 'insider';

const TABS: { id: Tab; label: string }[] = [
  { id: 'snapshot', label: 'PORTFOLIO' },
  { id: 'diff',     label: 'Q/Q DIFF'  },
  { id: 'signals',  label: 'AI SIGNALS' },
  { id: 'clone',    label: 'CLONE'     },
  { id: 'insider',  label: 'FORM 4'    },
];

export default function App() {
  const [investors, setInvestors] = useState<InvestorMeta[]>([]);
  const [selected, setSelected] = useState<string>('berkshire');
  const [tab, setTab] = useState<Tab>('snapshot');

  useEffect(() => {
    window.fetch('/api/investors')
      .then(r => r.json())
      .then((data: InvestorMeta[]) => setInvestors(data))
      .catch(() => {/* backend not yet running */});
  }, []);

  const investor = investors.find(i => i.id === selected);

  const handleSelect = (id: string) => {
    setSelected(id);
    // Reset to portfolio view when switching investors
    if (tab !== 'insider') setTab('snapshot');
  };

  return (
    <div className="scanlines flex flex-col h-full bg-t-bg overflow-hidden font-mono">
      <TopBar investors={investors} />

      <div className="flex flex-1 overflow-hidden">
        <InvestorSidebar
          investors={investors}
          selected={selected}
          onSelect={handleSelect}
        />

        <div className="flex flex-col flex-1 overflow-hidden border-l border-t-border">
          {/* Tab bar */}
          <div className="flex items-stretch border-b border-t-border bg-t-surface flex-shrink-0" style={{ height: 30 }}>
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={[
                  'px-4 text-2xs font-bold tracking-widest uppercase border-r border-t-border transition-colors',
                  tab === t.id
                    ? 'bg-t-orange text-black'
                    : 'text-t-muted hover:text-t-orange hover:bg-t-panel',
                ].join(' ')}
              >
                {t.label}
              </button>
            ))}

            {/* Investor label on the right */}
            {investor && tab !== 'insider' && (
              <div className="ml-auto px-4 flex items-center gap-2 text-2xs text-t-dim border-l border-t-border">
                <span className="text-t-orange font-bold truncate max-w-[200px]">
                  {investor.name}
                </span>
                <span className="text-t-faint">·</span>
                <span className="text-t-muted">{investor.style}</span>
              </div>
            )}
          </div>

          {/* Panel content */}
          <div className="flex-1 overflow-hidden flex flex-col">
            {tab === 'snapshot' && <SnapshotPanel key={selected} investorId={selected} />}
            {tab === 'diff'     && <DiffPanel     key={selected} investorId={selected} />}
            {tab === 'signals'  && <SignalsPanel  key={selected} investorId={selected} />}
            {tab === 'clone'    && <ClonePanel    key={selected} investorId={selected} />}
            {tab === 'insider'  && <InsiderPanel />}
          </div>
        </div>
      </div>
    </div>
  );
}
