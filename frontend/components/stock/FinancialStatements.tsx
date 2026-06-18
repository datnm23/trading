'use client';

import { useState, useEffect } from 'react';
import { NeoCard } from '@/components/ui/NeoCard';
import { getFinancials, type FinancialStatementView, type PeriodType } from '@/lib/api';

const STMT_TITLE: Record<string, string> = {
  balance_sheet: 'Cân đối kế toán (BCĐKT)',
  income_statement: 'Kết quả kinh doanh (KQKD)',
  cash_flow: 'Lưu chuyển tiền tệ (LCTT)',
};

// Format VND absolute → tỷ đồng (billions), 1 decimal. null → "—".
function fmtBil(v: number | null): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  return (v / 1e9).toLocaleString('vi-VN', { maximumFractionDigits: 1 });
}

function StatementTable({ stmt }: { stmt: FinancialStatementView }) {
  return (
    <NeoCard title={`${STMT_TITLE[stmt.statement_type] ?? stmt.statement_type} — đơn vị: tỷ VND`}>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b-[3px] border-neo-stroke">
              <th className="text-left py-2 px-2 font-black uppercase tracking-wide">Khoản mục</th>
              {stmt.periods.map((p) => (
                <th key={p} className="text-right py-2 px-2 font-black font-mono">{p}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {stmt.rows.map((row) => (
              <tr key={row.item_id} className="border-b border-neo-stroke/30 hover:bg-neo-surface">
                <td className="py-1.5 px-2 text-neo-text">{row.label}</td>
                {stmt.periods.map((p) => (
                  <td key={p} className="text-right py-1.5 px-2 font-mono text-neo-muted">
                    {fmtBil(row.values[p] ?? null)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </NeoCard>
  );
}

function PeriodToggle({ value, onChange }: { value: PeriodType; onChange: (p: PeriodType) => void }) {
  const opts: { key: PeriodType; label: string }[] = [
    { key: 'year', label: 'Năm' },
    { key: 'quarter', label: 'Quý' },
  ];
  return (
    <div className="flex gap-2 mb-4">
      {opts.map((o) => (
        <button
          key={o.key}
          onClick={() => onChange(o.key)}
          className={`px-4 py-1.5 font-black uppercase text-sm border-[3px] border-neo-stroke transition-colors ${
            value === o.key ? 'bg-neo-stroke text-neo-bg' : 'bg-neo-bg text-neo-text hover:bg-neo-surface'
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

/**
 * `period` is controlled by the parent (StockDetailPage) so the selection
 * survives the page's loading→loaded branch swap, which remounts this component.
 */
export function FinancialStatements({
  ticker,
  period,
  onPeriodChange,
}: {
  ticker: string;
  period: PeriodType;
  onPeriodChange: (p: PeriodType) => void;
}) {
  const [statements, setStatements] = useState<FinancialStatementView[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    getFinancials(ticker, period)
      .then((r) => { if (active) { setStatements(r.statements); setError(null); } })
      .catch((e) => { if (active) setError(e?.message ?? 'Lỗi tải BCTC'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [ticker, period]);

  return (
    <div className="space-y-6">
      <PeriodToggle value={period} onChange={onPeriodChange} />
      {loading && <NeoCard title="Báo cáo tài chính (BCTC)"><p className="text-neo-muted py-4">Đang tải…</p></NeoCard>}
      {!loading && error && (
        <NeoCard title="Báo cáo tài chính (BCTC)"><p className="text-neo-bearish py-4">{error}</p></NeoCard>
      )}
      {!loading && !error && statements.length === 0 && (
        <NeoCard title="Báo cáo tài chính (BCTC)">
          <p className="text-neo-muted py-4">Chưa có dữ liệu BCTC cho mã này (chạy scripts/collect_vn30_financials.py).</p>
        </NeoCard>
      )}
      {!loading && !error && statements.map((s) => (
        <StatementTable key={s.statement_type} stmt={s} />
      ))}
    </div>
  );
}
