'use client';

import { NeoCard } from '@/components/ui/NeoCard';
import { NeoBadge } from '@/components/ui/NeoBadge';
import { AlertTriangle, Newspaper, Shield, TrendingDown, Activity } from 'lucide-react';

interface NewsAlert {
  id: string;
  level: 'info' | 'warning' | 'critical';
  headline: string;
  source: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  impact: 'high' | 'medium' | 'low';
  timestamp: string;
}

const mockAlerts: NewsAlert[] = [
  {
    id: '1',
    level: 'warning',
    headline: 'SEC announces review of crypto ETF applications',
    source: 'CoinDesk',
    sentiment: 'neutral',
    impact: 'high',
    timestamp: '2h ago',
  },
  {
    id: '2',
    level: 'info',
    headline: 'Bitcoin hash rate reaches all-time high',
    source: 'CryptoPanic',
    sentiment: 'positive',
    impact: 'medium',
    timestamp: '4h ago',
  },
  {
    id: '3',
    level: 'critical',
    headline: 'Major exchange experiences withdrawal delays',
    source: 'Twitter/X',
    sentiment: 'negative',
    impact: 'high',
    timestamp: '30m ago',
  },
];

export function NewsSentimentPanel() {
  const circuitBreakerActive = mockAlerts.some((a) => a.level === 'critical');

  return (
    <div className="space-y-6">
      {/* Circuit Breaker Status */}
      <NeoCard>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield size={24} className={circuitBreakerActive ? 'text-neo-bearish' : 'text-neo-bullish'} />
            <div>
              <h3 className="text-lg font-black uppercase">Circuit Breaker</h3>
              <p className="text-sm text-neo-muted">
                {circuitBreakerActive 
                  ? 'ACTIVE — Trading paused due to critical news' 
                  : 'INACTIVE — All systems normal'}
              </p>
            </div>
          </div>
          <NeoBadge status={circuitBreakerActive ? 'halted' : 'running'}>
            {circuitBreakerActive ? 'PAUSED' : 'ACTIVE'}
          </NeoBadge>
        </div>
      </NeoCard>

      {/* Sentiment Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <NeoCard>
          <div className="flex items-center gap-3">
            <Activity size={20} className="text-neo-bullish" />
            <div>
              <div className="text-sm text-neo-muted uppercase">Market Sentiment</div>
              <div className="text-2xl font-black font-mono">Neutral</div>
            </div>
          </div>
        </NeoCard>
        <NeoCard>
          <div className="flex items-center gap-3">
            <TrendingDown size={20} className="text-neo-bearish" />
            <div>
              <div className="text-sm text-neo-muted uppercase">Fear Index</div>
              <div className="text-2xl font-black font-mono">45/100</div>
            </div>
          </div>
        </NeoCard>
        <NeoCard>
          <div className="flex items-center gap-3">
            <Newspaper size={20} className="text-neo-primary" />
            <div>
              <div className="text-sm text-neo-muted uppercase">News Count (24h)</div>
              <div className="text-2xl font-black font-mono">12</div>
            </div>
          </div>
        </NeoCard>
      </div>

      {/* News Alerts */}
      <NeoCard title="Latest News Alerts">
        <div className="space-y-4">
          {mockAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`border-[3px] p-4 ${
                alert.level === 'critical'
                  ? 'border-neo-bearish bg-neo-bearish/10'
                  : alert.level === 'warning'
                  ? 'border-neo-primary bg-neo-primary/10'
                  : 'border-neo-stroke'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  {alert.level === 'critical' && <AlertTriangle size={18} className="text-neo-bearish" />}
                  <span className="font-bold">{alert.headline}</span>
                </div>
                <div className="flex gap-2">
                  <NeoBadge status={alert.sentiment === 'positive' ? 'running' : alert.sentiment === 'negative' ? 'halted' : 'paper'}>
                    {alert.sentiment}
                  </NeoBadge>
                  <span className="text-xs font-mono text-neo-muted">{alert.impact}</span>
                </div>
              </div>
              <div className="flex justify-between text-sm text-neo-muted">
                <span>{alert.source}</span>
                <span className="font-mono">{alert.timestamp}</span>
              </div>
            </div>
          ))}
        </div>
      </NeoCard>
    </div>
  );
}
