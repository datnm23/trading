'use client';

import { useMemo } from 'react';
import {
  ComposedChart,
  Line,
  Area,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface MarketPriceChartProps {
  data: Candle[];
}

export function MarketPriceChart({ data }: MarketPriceChartProps) {
  const chartData = useMemo(() => {
    return data.map((d) => ({
      ...d,
      avg: (d.high + d.low) / 2,
      range: d.high - d.low,
      color: d.close >= d.open ? '#B9FF66' : '#FF6B6B',
    }));
  }, [data]);

  const yDomain = useMemo(() => {
    if (chartData.length === 0) return ['auto', 'auto'] as [string, string];
    const minLow = Math.min(...chartData.map((d) => d.low));
    const maxHigh = Math.max(...chartData.map((d) => d.high));
    const padding = (maxHigh - minLow) * 0.05;
    return [Math.floor(minLow - padding), Math.ceil(maxHigh + padding)] as [number, number];
  }, [chartData]);

  if (chartData.length === 0) {
    return (
      <div className="w-full h-[400px] flex items-center justify-center text-neo-muted font-bold">
        No data
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Price Area Chart */}
      <div className="w-full h-[350px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#00000022" />
            <XAxis
              dataKey="timestamp"
              tick={{ fontSize: 11, fontFamily: 'JetBrains Mono' }}
              tickFormatter={(val) => {
                const date = new Date(val);
                return `${date.getMonth() + 1}/${date.getDate()}`;
              }}
              interval="preserveStartEnd"
              minTickGap={30}
            />
            <YAxis
              domain={yDomain}
              tick={{ fontSize: 11, fontFamily: 'JetBrains Mono' }}
              tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
              orientation="right"
            />
            <Tooltip
              contentStyle={{
                background: '#fff',
                border: '3px solid #000',
                boxShadow: '4px 4px 0 #000',
                fontFamily: 'JetBrains Mono',
                fontSize: 12,
              }}
              formatter={(value, name) => {
                const label = String(name);
                if (label === 'close') return [`$${Number(value).toLocaleString()}`, 'Close'];
                if (label === 'high') return [`$${Number(value).toLocaleString()}`, 'High'];
                if (label === 'low') return [`$${Number(value).toLocaleString()}`, 'Low'];
                return [value, label];
              }}
              labelFormatter={(label) => new Date(label).toLocaleString()}
            />
            <Area
              type="monotone"
              dataKey="close"
              stroke="#FDC800"
              strokeWidth={2}
              fill="#FDC80022"
              dot={false}
              activeDot={{ r: 5, strokeWidth: 2, stroke: '#000' }}
            />
            <Line
              type="monotone"
              dataKey="high"
              stroke="#B9FF66"
              strokeWidth={1}
              strokeDasharray="4 4"
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="low"
              stroke="#FF6B6B"
              strokeWidth={1}
              strokeDasharray="4 4"
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Volume Bar Chart */}
      <div className="w-full h-[120px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData}>
            <XAxis dataKey="timestamp" hide />
            <YAxis hide />
            <Tooltip
              contentStyle={{
                background: '#fff',
                border: '3px solid #000',
                boxShadow: '4px 4px 0 #000',
                fontFamily: 'JetBrains Mono',
                fontSize: 12,
              }}
              formatter={(value) => [`${(Number(value) / 1e9).toFixed(2)}B`, 'Volume']}
            />
            <Bar dataKey="volume" fill="#00000033" stroke="#000" strokeWidth={1} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
