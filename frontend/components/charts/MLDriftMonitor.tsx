'use client';

import { NeoCard } from '@/components/ui/NeoCard';
import { NeoMetric } from '@/components/ui/NeoMetric';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { Activity, AlertTriangle, CheckCircle } from 'lucide-react';

interface DriftData {
  timestamp: string;
  accuracy: number;
  baseline: number;
  psi: number;
}

const mockDriftData: DriftData[] = [
  { timestamp: '2026-04-15', accuracy: 0.72, baseline: 0.75, psi: 0.05 },
  { timestamp: '2026-04-16', accuracy: 0.71, baseline: 0.75, psi: 0.08 },
  { timestamp: '2026-04-17', accuracy: 0.69, baseline: 0.75, psi: 0.12 },
  { timestamp: '2026-04-18', accuracy: 0.68, baseline: 0.75, psi: 0.15 },
  { timestamp: '2026-04-19', accuracy: 0.65, baseline: 0.75, psi: 0.22 },
  { timestamp: '2026-04-20', accuracy: 0.63, baseline: 0.75, psi: 0.28 },
  { timestamp: '2026-04-21', accuracy: 0.61, baseline: 0.75, psi: 0.35 },
  { timestamp: '2026-04-22', accuracy: 0.58, baseline: 0.75, psi: 0.42 },
];

export function MLDriftMonitor() {
  const latest = mockDriftData[mockDriftData.length - 1];
  const isDrifted = latest.psi > 0.2;
  const accuracyDrop = ((latest.baseline - latest.accuracy) / latest.baseline) * 100;

  return (
    <div className="space-y-6">
      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <NeoCard>
          <div className="flex items-center gap-3">
            {isDrifted ? (
              <AlertTriangle size={24} className="text-neo-bearish" />
            ) : (
              <CheckCircle size={24} className="text-neo-bullish" />
            )}
            <NeoMetric
              label="Drift Status"
              value={isDrifted ? 'DRIFTED' : 'Stable'}
              variant={isDrifted ? 'bearish' : 'bullish'}
            />
          </div>
        </NeoCard>
        <NeoCard>
          <NeoMetric
            label="Current Accuracy"
            value={`${(latest.accuracy * 100).toFixed(1)}%`}
            delta={`-${accuracyDrop.toFixed(1)}% from baseline`}
            variant={latest.accuracy < 0.6 ? 'bearish' : 'neutral'}
          />
        </NeoCard>
        <NeoCard>
          <NeoMetric
            label="PSI Score"
            value={latest.psi.toFixed(2)}
            delta={latest.psi > 0.2 ? 'Above threshold' : 'Normal'}
            variant={latest.psi > 0.2 ? 'bearish' : 'bullish'}
          />
        </NeoCard>
      </div>

      {/* Accuracy Chart */}
      <NeoCard title="Model Accuracy Over Time">
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={mockDriftData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#00000022" />
              <XAxis
                dataKey="timestamp"
                tick={{ fontSize: 12, fontFamily: 'JetBrains Mono' }}
              />
              <YAxis
                domain={[0.5, 0.8]}
                tick={{ fontSize: 12, fontFamily: 'JetBrains Mono' }}
                tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
              />
              <Tooltip
                contentStyle={{
                  background: '#fff',
                  border: '3px solid #000',
                  boxShadow: '4px 4px 0 #000',
                  fontFamily: 'JetBrains Mono',
                }}
                formatter={(value: any) => [`${(Number(value) * 100).toFixed(1)}%`, '']}
              />
              <ReferenceLine
                y={0.6}
                stroke="#FF6B6B"
                strokeDasharray="5 5"
                strokeWidth={2}
                label={{ value: 'Retrain Threshold', position: 'right', fontWeight: 700 }}
              />
              <Line
                type="monotone"
                dataKey="accuracy"
                stroke="#FDC800"
                strokeWidth={3}
                dot={{ stroke: '#000', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, strokeWidth: 2, stroke: '#000' }}
              />
              <Line
                type="monotone"
                dataKey="baseline"
                stroke="#000"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </NeoCard>

      {/* PSI Chart */}
      <NeoCard title="Population Stability Index (PSI)">
        <div className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={mockDriftData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#00000022" />
              <XAxis
                dataKey="timestamp"
                tick={{ fontSize: 12, fontFamily: 'JetBrains Mono' }}
              />
              <YAxis
                tick={{ fontSize: 12, fontFamily: 'JetBrains Mono' }}
              />
              <Tooltip
                contentStyle={{
                  background: '#fff',
                  border: '3px solid #000',
                  boxShadow: '4px 4px 0 #000',
                  fontFamily: 'JetBrains Mono',
                }}
              />
              <ReferenceLine
                y={0.2}
                stroke="#FF6B6B"
                strokeDasharray="5 5"
                strokeWidth={2}
                label={{ value: 'Drift Threshold', position: 'right', fontWeight: 700 }}
              />
              <Line
                type="monotone"
                dataKey="psi"
                stroke="#432DD7"
                strokeWidth={3}
                dot={{ stroke: '#000', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </NeoCard>

      {/* Action Required */}
      {isDrifted && (
        <NeoCard className="border-neo-bearish">
          <div className="flex items-center gap-3">
            <Activity size={24} className="text-neo-bearish" />
            <div>
              <h4 className="font-black uppercase">Retrain Recommended</h4>
              <p className="text-sm text-neo-muted">
                Model accuracy dropped {accuracyDrop.toFixed(1)}% and PSI exceeds 0.2. 
                Schedule retraining with recent data.
              </p>
            </div>
          </div>
        </NeoCard>
      )}
    </div>
  );
}
