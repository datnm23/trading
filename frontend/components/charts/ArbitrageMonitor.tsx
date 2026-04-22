'use client';

import { NeoCard } from '@/components/ui/NeoCard';
import { NeoBadge } from '@/components/ui/NeoBadge';
import { ArrowRightLeft, TrendingUp, AlertTriangle } from 'lucide-react';

interface ExchangePrice {
  exchange: string;
  symbol: string;
  bid: number;
  ask: number;
  spread: number;
  fees: number;
}

const mockPrices: ExchangePrice[] = [
  { exchange: 'Binance', symbol: 'BTC/USDT', bid: 78820.50, ask: 78850.00, spread: 0.037, fees: 0.10 },
  { exchange: 'Bybit', symbol: 'BTC/USDT', bid: 78810.20, ask: 78860.50, spread: 0.064, fees: 0.10 },
  { exchange: 'OKX', symbol: 'BTC/USDT', bid: 78830.00, ask: 78845.00, spread: 0.019, fees: 0.08 },
  { exchange: 'Kraken', symbol: 'BTC/USDT', bid: 78805.00, ask: 78870.00, spread: 0.083, fees: 0.16 },
];

export function ArbitrageMonitor() {
  // Find best arbitrage opportunity
  const bestBid = Math.max(...mockPrices.map((p) => p.bid));
  const bestAsk = Math.min(...mockPrices.map((p) => p.ask));
  const arbitragePct = ((bestBid - bestAsk) / bestAsk) * 100;
  const isProfitable = arbitragePct > 0.05; // > 0.05% after fees estimate

  return (
    <div className="space-y-6">
      {/* Opportunity Card */}
      <NeoCard>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ArrowRightLeft size={24} className={isProfitable ? 'text-neo-bullish' : 'text-neo-muted'} />
            <div>
              <h3 className="text-lg font-black uppercase">Arbitrage Opportunity</h3>
              <p className="text-sm text-neo-muted">
                {isProfitable 
                  ? `Potential profit: ${arbitragePct.toFixed(3)}%` 
                  : 'No profitable opportunities'}
              </p>
            </div>
          </div>
          <NeoBadge status={isProfitable ? 'running' : 'halted'}>
            {isProfitable ? 'OPPORTUNITY' : 'NO ARB'}
          </NeoBadge>
        </div>
      </NeoCard>

      {/* Best Pair */}
      {isProfitable && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <NeoCard title="Buy At" className="border-neo-bullish">
            <div className="text-center">
              <div className="text-sm text-neo-muted uppercase">Lowest Ask</div>
              <div className="text-3xl font-black font-mono my-2">
                ${bestAsk.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </div>
              <div className="text-lg font-bold text-neo-bullish">
                {mockPrices.find((p) => p.ask === bestAsk)?.exchange}
              </div>
            </div>
          </NeoCard>
          <NeoCard title="Sell At" className="border-neo-primary">
            <div className="text-center">
              <div className="text-sm text-neo-muted uppercase">Highest Bid</div>
              <div className="text-3xl font-black font-mono my-2">
                ${bestBid.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </div>
              <div className="text-lg font-bold text-neo-primary">
                {mockPrices.find((p) => p.bid === bestBid)?.exchange}
              </div>
            </div>
          </NeoCard>
        </div>
      )}

      {/* Price Comparison Table */}
      <NeoCard title="Exchange Price Comparison">
        <div className="overflow-x-auto">
          <table className="neo-table">
            <thead>
              <tr>
                <th>Exchange</th>
                <th>Bid</th>
                <th>Ask</th>
                <th>Spread %</th>
                <th>Fees %</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {mockPrices.map((price) => (
                <tr key={price.exchange}>
                  <td className="font-bold">{price.exchange}</td>
                  <td className="font-mono">${price.bid.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                  <td className="font-mono">${price.ask.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                  <td className="font-mono">{price.spread.toFixed(3)}%</td>
                  <td className="font-mono">{price.fees}%</td>
                  <td>
                    {price.bid === bestBid ? (
                      <NeoBadge status="running">Best Bid</NeoBadge>
                    ) : price.ask === bestAsk ? (
                      <NeoBadge status="paper">Best Ask</NeoBadge>
                    ) : (
                      <span className="text-neo-muted">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </NeoCard>

      {/* Warnings */}
      <NeoCard>
        <div className="flex items-start gap-3">
          <AlertTriangle size={20} className="text-neo-primary mt-1" />
          <div>
            <h4 className="font-bold uppercase">Arbitrage Risks</h4>
            <ul className="text-sm text-neo-muted mt-2 space-y-1">
              <li>• Transfer fees between exchanges (0.1-0.5%)</li>
              <li>• Withdrawal processing time (10-30 min)</li>
              <li>• Price movement during transfer</li>
              <li>• Minimum order size requirements</li>
            </ul>
          </div>
        </div>
      </NeoCard>
    </div>
  );
}
