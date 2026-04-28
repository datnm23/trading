'use client';

import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface EquityCurveProps {
  data: { timestamp: string; equity: number; strategy: string }[];
}

export function EquityCurveChart({ data }: EquityCurveProps) {
  const chartData = useMemo(() => {
    // Group by timestamp
    const grouped: Record<string, Record<string, number | string>> = {};
    data.forEach((d) => {
      if (!grouped[d.timestamp]) grouped[d.timestamp] = { timestamp: d.timestamp };
      grouped[d.timestamp][d.strategy] = d.equity;
    });
    return Object.values(grouped).sort((a: Record<string, number | string>, b: Record<string, number | string>) =>
      new Date(String(a.timestamp)).getTime() - new Date(String(b.timestamp)).getTime()
    );
  }, [data]);

  const strategies = useMemo(() => {
    const s = new Set<string>();
    data.forEach((d) => s.add(d.strategy));
    return Array.from(s);
  }, [data]);

  const colors = ['#FDC800', '#B9FF66', '#FF6B6B', '#432DD7'];

  return (
    <div className="w-full h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#00000022" />
          <XAxis 
            dataKey="timestamp" 
            tick={{ fontSize: 12, fontFamily: 'JetBrains Mono' }}
            tickFormatter={(val) => new Date(val).toLocaleTimeString()}
          />
          <YAxis 
            tick={{ fontSize: 12, fontFamily: 'JetBrains Mono' }}
            tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
          />
          <Tooltip 
            contentStyle={{
              background: '#fff',
              border: '3px solid #000',
              boxShadow: '4px 4px 0 #000',
              fontFamily: 'JetBrains Mono',
            }}
            formatter={(value) => [`$${Number(value).toLocaleString()}`, '']}
          />
          <Legend 
            wrapperStyle={{ fontFamily: 'Inter', fontWeight: 700 }}
          />
          {strategies.map((strategy, index) => (
            <Line
              key={strategy}
              type="monotone"
              dataKey={strategy}
              stroke={colors[index % colors.length]}
              strokeWidth={3}
              dot={false}
              activeDot={{ r: 6, strokeWidth: 2, stroke: '#000' }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
