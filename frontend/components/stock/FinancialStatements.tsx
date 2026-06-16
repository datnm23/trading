'use client';

import { useState, useEffect } from 'react';
import { NeoCard } from '@/components/ui/NeoCard';
import { getFinancials, type FinancialStatementView } from '@/lib/api';

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

export function FinancialStatements({ ticker }: { ticker: string }) {
  const [statements, setStatements] = useState<FinancialStatementView[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    getFinancials(ticker)
      .then((r) => { if (active) { setStatements(r.statements); setError(null); } })
      .catch((e) => { if (active) setError(e?.message ?? 'Lỗi tải BCTC'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [ticker]);

  if (loading) return <NeoCard title="Báo cáo tài chính (BCTC)"><p className="text-neo-muted py-4">Đang tải…</p></NeoCard>;
  if (error) return <NeoCard title="Báo cáo tài chính (BCTC)"><p className="text-neo-bearish py-4">{error}</p></NeoCard>;
  if (statements.length === 0)
    return (
      <NeoCard title="Báo cáo tài chính (BCTC)">
        <p className="text-neo-muted py-4">Chưa có dữ liệu BCTC cho mã này (chạy scripts/collect_vn30_financials.py).</p>
      </NeoCard>
    );

  return (
    <div className="space-y-6">
      {statements.map((s) => (
        <StatementTable key={s.statement_type} stmt={s} />
      ))}
    </div>
  );
}
