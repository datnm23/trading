'use client';

import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface PnLBarChartProps {
  data: { strategy: string; pnl: number }[];
}

export function PnLBarChart({ data }: PnLBarChartProps) {
  const chartData = useMemo(() => {
    return data.map((d) => ({
      ...d,
      color: d.pnl >= 0 ? '#B9FF66' : '#FF6B6B',
    }));
  }, [data]);

  return (
    <div className="w-full h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#00000022" />
          <XAxis 
            dataKey="strategy" 
            tick={{ fontSize: 12, fontFamily: 'JetBrains Mono', fontWeight: 700 }}
          />
          <YAxis 
            tick={{ fontSize: 12, fontFamily: 'JetBrains Mono' }}
            tickFormatter={(val) => `$${val}`}
          />
          <Tooltip
            contentStyle={{
              background: '#fff',
              border: '3px solid #000',
              boxShadow: '4px 4px 0 #000',
              fontFamily: 'JetBrains Mono',
            }}
                formatter={(value: unknown) => [`$${Number(value).toFixed(2)}`, 'P&L']}
          />
          <Bar dataKey="pnl" radius={[0, 0, 0, 0]} stroke="#000" strokeWidth={2}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
