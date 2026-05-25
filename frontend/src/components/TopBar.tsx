import { useEffect, useState } from 'react';
import { Activity, Cpu, TrendingUp } from 'lucide-react';
import type { InvestorMeta } from '../types';

interface Props {
  investors: InvestorMeta[];
}

function Clock() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return (
    <span className="text-t-muted text-2xs font-mono">
      {time.toUTCString().slice(17, 25)}{' '}
      <span className="animate-blink">UTC</span>
    </span>
  );
}

const TAPE_ITEMS = [
  { sym: 'AAPL',  base: 225, chg:  0.34 },
  { sym: 'MSFT',  base: 414, chg: -0.12 },
  { sym: 'NVDA',  base: 138, chg:  1.87 },
  { sym: 'AMZN',  base: 198, chg:  0.56 },
  { sym: 'META',  base: 585, chg:  0.91 },
  { sym: 'GOOGL', base: 177, chg: -0.23 },
  { sym: 'BRK.B', base: 457, chg:  0.08 },
  { sym: 'TSM',   base: 175, chg:  2.14 },
  { sym: 'TSLA',  base: 176, chg: -1.42 },
  { sym: 'JPM',   base: 246, chg:  0.33 },
  { sym: 'V',     base: 338, chg:  0.17 },
  { sym: 'UNH',   base: 298, chg: -0.77 },
  { sym: 'XOM',   base: 108, chg:  0.49 },
  { sym: 'BAC',   base: 43,  chg:  0.22 },
  { sym: 'WMT',   base: 97,  chg:  0.05 },
  { sym: 'HD',    base: 342, chg: -0.38 },
  { sym: 'CVX',   base: 155, chg:  0.61 },
  { sym: 'MRK',   base: 95,  chg: -0.54 },
];

export default function TopBar({ investors }: Props) {
  return (
    <div
      className="flex-shrink-0 border-b border-t-border bg-[#07080b] flex items-center"
      style={{ height: 36 }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2 px-3 border-r border-t-border flex-shrink-0">
        <TrendingUp size={12} className="text-t-orange" />
        <span className="text-t-orange font-bold text-2xs tracking-widest glow-orange">
          ECHOTRADE AI
        </span>
      </div>

      {/* Status indicators */}
      <div className="flex items-center gap-3 px-3 border-r border-t-border flex-shrink-0">
        <span className="flex items-center gap-1.5">
          <Activity size={9} className="text-t-orange" />
          <span className="text-t-orange text-2xs font-bold tracking-wider">DEMO</span>
        </span>
        <span className="flex items-center gap-1.5">
          <Cpu size={9} className="text-t-muted" />
          <span className="text-t-muted text-2xs tracking-wider">AI</span>
        </span>
      </div>

      {/* Ticker tape — static demo prices, not a live feed */}
      <div className="ticker-wrap flex-1 mx-2 overflow-hidden">
        <div className="ticker-inner">
          <span className="inline-flex items-center mr-6 text-2xs text-t-muted tracking-wider flex-shrink-0">
            DEMO PRICES
          </span>
          {[...TAPE_ITEMS, ...TAPE_ITEMS].map((t, i) => (
            <span key={i} className="inline-flex items-center gap-1.5 mr-8 text-2xs">
              <span className="text-t-orange font-bold tracking-wide">{t.sym}</span>
              <span className="num text-t-text">{t.base.toFixed(2)}</span>
              <span className={t.chg >= 0 ? 'text-t-green' : 'text-t-red'}>
                {t.chg >= 0 ? '+' : ''}{t.chg.toFixed(2)}%
              </span>
            </span>
          ))}
        </div>
      </div>

      {/* Right: fund count + clock */}
      <div className="flex items-center gap-4 px-3 border-l border-t-border flex-shrink-0">
        {investors.length > 0 && (
          <span className="text-t-muted text-2xs tracking-wider">
            {investors.length} FUNDS
          </span>
        )}
        <Clock />
      </div>
    </div>
  );
}
