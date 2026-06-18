import { useEffect, useState } from 'react';
import { Activity, Cpu, TrendingUp } from 'lucide-react';
import type { InvestorMeta } from '../types';

interface Props {
  investors: InvestorMeta[];
}

interface PriceItem {
  sym: string;
  price: number | null;
  chg_pct: number | null;
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

const FALLBACK: PriceItem[] = [
  { sym: 'AAPL',  price: null, chg_pct: null },
  { sym: 'MSFT',  price: null, chg_pct: null },
  { sym: 'NVDA',  price: null, chg_pct: null },
  { sym: 'AMZN',  price: null, chg_pct: null },
  { sym: 'META',  price: null, chg_pct: null },
  { sym: 'GOOGL', price: null, chg_pct: null },
  { sym: 'BRK.B', price: null, chg_pct: null },
  { sym: 'TSM',   price: null, chg_pct: null },
  { sym: 'TSLA',  price: null, chg_pct: null },
  { sym: 'JPM',   price: null, chg_pct: null },
  { sym: 'V',     price: null, chg_pct: null },
  { sym: 'UNH',   price: null, chg_pct: null },
  { sym: 'XOM',   price: null, chg_pct: null },
  { sym: 'BAC',   price: null, chg_pct: null },
  { sym: 'WMT',   price: null, chg_pct: null },
  { sym: 'HD',    price: null, chg_pct: null },
  { sym: 'CVX',   price: null, chg_pct: null },
  { sym: 'MRK',   price: null, chg_pct: null },
];

export default function TopBar({ investors }: Props) {
  const [prices, setPrices] = useState<PriceItem[]>(FALLBACK);

  useEffect(() => {
    const load = () => {
      fetch('/api/prices')
        .then(r => r.ok ? r.json() : Promise.reject())
        .then(setPrices)
        .catch(() => {}); // keep showing previous prices on error
    };
    load();
    const id = setInterval(load, 60_000);
    return () => clearInterval(id);
  }, []);

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

      {/* Ticker tape — ~15-min delayed prices from Yahoo Finance */}
      <div className="ticker-wrap flex-1 mx-2 overflow-hidden">
        <div className="ticker-inner">
          <span className="inline-flex items-center mr-6 text-2xs text-t-muted tracking-wider flex-shrink-0">
            DELAYED
          </span>
          {[...prices, ...prices].map((t, i) => (
            <span key={i} className="inline-flex items-center gap-1.5 mr-8 text-2xs">
              <span className="text-t-orange font-bold tracking-wide">{t.sym}</span>
              {t.price != null ? (
                <>
                  <span className="num text-t-text">{t.price.toFixed(2)}</span>
                  <span className={t.chg_pct != null && t.chg_pct >= 0 ? 'text-t-green' : 'text-t-red'}>
                    {t.chg_pct != null ? `${t.chg_pct >= 0 ? '+' : ''}${t.chg_pct.toFixed(2)}%` : ''}
                  </span>
                </>
              ) : (
                <span className="text-t-muted">---</span>
              )}
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
