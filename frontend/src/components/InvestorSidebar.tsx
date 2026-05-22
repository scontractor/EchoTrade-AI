import { ChevronRight } from 'lucide-react';
import type { InvestorMeta } from '../types';

interface Props {
  investors: InvestorMeta[];
  selected: string;
  onSelect: (id: string) => void;
}

const STYLE_COLOR: Record<string, string> = {
  'Concentrated Value':    'text-t-gold',
  'Disruptive Innovation': 'text-t-cyan',
  'Concentrated Activist': 'text-t-orange',
  'Event-Driven Activist': 'text-t-orange',
  'Macro/Value':           'text-t-purple',
  'Global Macro':          'text-t-purple',
  'Deep Value':            'text-t-gold',
  'Growth Equity':         'text-t-cyan',
  'Macro/Growth':          'text-t-purple',
  'Quantitative':          'text-t-blue',
};

function shortName(full: string): string {
  return full.includes('(') ? full.split('(')[0].trim() : full;
}

export default function InvestorSidebar({ investors, selected, onSelect }: Props) {
  return (
    <div
      className="flex-shrink-0 flex flex-col overflow-y-auto bg-t-surface"
      style={{ width: 212 }}
    >
      <div className="panel-header">
        <span>TRACKED FUNDS</span>
        <span className="ml-auto text-t-dim">{investors.length}</span>
      </div>

      {investors.length === 0 && (
        <div className="flex flex-col gap-2 p-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="skeleton h-8 rounded" />
          ))}
        </div>
      )}

      {investors.map(inv => {
        const active = inv.id === selected;
        return (
          <button
            key={inv.id}
            onClick={() => onSelect(inv.id)}
            className={[
              'w-full text-left px-3 py-2.5 border-b border-t-border',
              'flex items-start gap-2 group transition-colors',
              'border-l-2',
              active
                ? 'bg-[#0f1118] border-l-t-orange'
                : 'hover:bg-t-panel border-l-transparent hover:border-l-t-dim',
            ].join(' ')}
          >
            <ChevronRight
              size={9}
              className={[
                'mt-0.5 flex-shrink-0 transition-colors',
                active ? 'text-t-orange' : 'text-t-faint group-hover:text-t-dim',
              ].join(' ')}
            />
            <div className="min-w-0">
              <div
                className={[
                  'text-2xs font-bold leading-tight',
                  active ? 'text-t-orange' : 'text-t-text',
                ].join(' ')}
              >
                {shortName(inv.name)}
              </div>
              <div className={`text-2xs mt-0.5 ${STYLE_COLOR[inv.style] ?? 'text-t-muted'}`}>
                {inv.style}
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
