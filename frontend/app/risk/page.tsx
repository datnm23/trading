'use client';

import { useSocketIO, Position, TrailingStop, PartialExit, SlippageItem } from '@/hooks/useSocketIO';
import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { NeoMetric } from '@/components/ui/NeoMetric';
import { t } from '@/lib/i18n';
import { Shield, AlertTriangle, CheckCircle, TrendingDown, Lock, Activity } from 'lucide-react';

export default function RiskPage() {
  const { state } = useSocketIO();
  const { lang } = useLang();

  const trailingStops = state?.trailing_stops || [];
  const slippage = state?.slippage || [];
  const partialExits = state?.partial_exits || [];
  const positions = state?.positions || [];
  const equityHistory = state?.equity_history || [];

  // Calculate max drawdown from equity history
  const maxDrawdown = (() => {
    if (equityHistory.length < 2) return 0;
    let peak = equityHistory[0]?.equity || 0;
    let maxDD = 0;
    for (const point of equityHistory) {
      if (point.equity > peak) peak = point.equity;
      const dd = peak > 0 ? (peak - point.equity) / peak : 0;
      if (dd > maxDD) maxDD = dd;
    }
    return maxDD;
  })();

  // Calculate VaR 95% (simplified historical simulation)
  const var95 = (() => {
    if (equityHistory.length < 10) return 0;
    const returns = [];
    for (let i = 1; i < equityHistory.length; i++) {
      const prev = equityHistory[i - 1]?.equity || 1;
      const curr = equityHistory[i]?.equity || 1;
      if (prev > 0) returns.push((curr - prev) / prev);
    }
    if (returns.length < 5) return 0;
    returns.sort((a, b) => a - b);
    const idx = Math.floor(returns.length * 0.05);
    return returns[idx] || 0;
  })();

  // Total open exposure
  const openExposure = positions.reduce((sum: number, p: Position) => {
    return sum + (p.size || 0) * (p.entry_price || 0);
  }, 0);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-black uppercase tracking-wider">{t('riskMonitor', lang)}</h2>

      {/* Risk Overview Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <NeoCard>
          <NeoMetric
            label="Max Drawdown"
            value={`${(maxDrawdown * 100).toFixed(2)}%`}
            variant={maxDrawdown > 0.15 ? 'bearish' : maxDrawdown > 0.10 ? 'warning' : 'bullish'}
            prefix=""
          />
        </NeoCard>
        <NeoCard>
          <NeoMetric
            label="VaR 95%"
            value={`${(Math.abs(var95) * 100).toFixed(2)}%`}
            variant={Math.abs(var95) > 0.02 ? 'bearish' : 'neutral'}
            prefix=""
          />
        </NeoCard>
        <NeoCard>
          <NeoMetric
            label="Open Exposure"
            value={openExposure.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            prefix="$"
            variant="neutral"
          />
        </NeoCard>
        <NeoCard>
          <NeoMetric
            label="Open Positions"
            value={positions.length}
            variant={positions.length > 3 ? 'warning' : 'neutral'}
          />
        </NeoCard>
      </div>

      {/* Trailing Stops */}
      <NeoCard title="Trailing Stops">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="flex items-center gap-2">
            <Activity size={20} className="text-neo-bullish" />
            <span className="font-bold">{t('running', lang)}:</span>
            <span className="font-mono font-bold ml-auto">{trailingStops.length}</span>
          </div>
          <div className="flex items-center gap-2">
            <TrendingDown size={20} className="text-neo-bearish" />
            <span className="font-bold">Hit Today:</span>
            <span className="font-mono font-bold ml-auto text-neo-bearish">0</span>
          </div>
          <div className="flex items-center gap-2">
            <Lock size={20} className="text-neo-accent" />
            <span className="font-bold">Activated:</span>
            <span className="font-mono font-bold ml-auto text-neo-bullish">
              {trailingStops.filter((s: TrailingStop) => s.activated).length}
            </span>
          </div>
        </div>
        {trailingStops.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="neo-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Entry</th>
                  <th>Peak</th>
                  <th>Current Stop</th>
                  <th>Activated</th>
                  <th>Profit %</th>
                </tr>
              </thead>
              <tbody>
                {trailingStops.map((stop: TrailingStop, i: number) => (
                  <tr key={`${stop.symbol}-${i}`}>
                    <td className="font-mono font-bold">{stop.symbol}</td>
                    <td className="font-mono">${stop.entry_price?.toLocaleString()}</td>
                    <td className="font-mono">${stop.peak_price?.toLocaleString()}</td>
                    <td className="font-mono text-neo-bearish">${stop.current_stop?.toLocaleString()}</td>
                    <td>
                      <span className={stop.activated ? 'text-neo-bullish font-bold' : 'text-neo-muted'}>
                        {stop.activated ? 'YES' : 'NO'}
                      </span>
                    </td>
                    <td className={`font-mono ${stop.profit_pct >= 0 ? 'text-neo-bullish' : 'text-neo-bearish'}`}>
                      {(stop.profit_pct * 100).toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-neo-muted text-center py-4">No trailing stops active</p>
        )}
      </NeoCard>

      {/* Partial Exits */}
      <NeoCard title="Partial Exits">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="flex items-center gap-2">
            <AlertTriangle size={20} className="text-neo-primary" />
            <span className="font-bold">Tracking:</span>
            <span className="font-mono font-bold ml-auto">{partialExits.length}</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle size={20} className="text-neo-bullish" />
            <span className="font-bold">Triggered:</span>
            <span className="font-mono font-bold ml-auto">
              {partialExits.reduce((sum: number, p: PartialExit) => sum + (p.executed_count || 0), 0)}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Lock size={20} className="text-neo-accent" />
            <span className="font-bold">Profit Locked:</span>
            <span className="font-mono font-bold ml-auto text-neo-bullish">$0.00</span>
          </div>
        </div>
        {partialExits.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="neo-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Entry</th>
                  <th>Initial Size</th>
                  <th>Remaining</th>
                  <th>Executed</th>
                </tr>
              </thead>
              <tbody>
                {partialExits.map((exit: PartialExit, i: number) => (
                  <tr key={`${exit.symbol}-${i}`}>
                    <td className="font-mono font-bold">{exit.symbol}</td>
                    <td className="font-mono">${exit.entry?.toLocaleString()}</td>
                    <td className="font-mono">{exit.initial_size?.toFixed(4)}</td>
                    <td className="font-mono">{exit.remaining?.toFixed(4)}</td>
                    <td className="font-mono">{exit.executed_count || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-neo-muted text-center py-4">No partial exits tracking</p>
        )}
      </NeoCard>

      {/* Slippage */}
      <NeoCard title="Slippage">
        {slippage.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="neo-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Trades</th>
                  <th>Avg Slippage</th>
                  <th>Max Slippage</th>
                  <th>Total Cost</th>
                </tr>
              </thead>
              <tbody>
                {slippage.map((s: SlippageItem, i: number) => (
                  <tr key={`${s.symbol}-${i}`}>
                    <td className="font-mono font-bold">{s.symbol}</td>
                    <td className="font-mono">{s.trades}</td>
                    <td className="font-mono">{(s.avg_slippage_pct * 100).toFixed(4)}%</td>
                    <td className="font-mono text-neo-bearish">{(s.max_slippage_pct * 100).toFixed(4)}%</td>
                    <td className="font-mono text-neo-bearish">${s.total_cost?.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-neo-muted text-center py-4">No slippage data yet</p>
        )}
      </NeoCard>

      {/* Open Positions Risk */}
      {positions.length > 0 && (
        <NeoCard title={`Positions at Risk (${positions.length})`}>
          <div className="overflow-x-auto">
            <table className="neo-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Entry</th>
                  <th>Stop</th>
                  <th>Size</th>
                  <th>Unrealized P&L</th>
                  <th>Risk/Reward</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((pos: Position, i: number) => {
                  const risk = (pos.entry_price || 0) - (pos.stop_price || 0);
                  const reward = pos.unrealized_pnl || 0;
                  const rr = risk > 0 ? reward / risk : 0;
                  return (
                    <tr key={`${pos.symbol}-${i}`}>
                      <td className="font-mono font-bold">{pos.symbol}</td>
                      <td className="font-mono">${pos.entry_price?.toLocaleString()}</td>
                      <td className="font-mono text-neo-bearish">${pos.stop_price?.toLocaleString()}</td>
                      <td className="font-mono">{pos.size?.toFixed(4)}</td>
                      <td className={`font-mono ${(pos.unrealized_pnl || 0) >= 0 ? 'text-neo-bullish' : 'text-neo-bearish'}`}>
                        ${(pos.unrealized_pnl || 0).toFixed(2)}
                      </td>
                      <td className={`font-mono ${rr >= 1 ? 'text-neo-bullish' : 'text-neo-warning'}`}>
                        {rr.toFixed(2)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </NeoCard>
      )}
    </div>
  );
}
