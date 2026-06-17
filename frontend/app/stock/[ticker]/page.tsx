'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { NeoMetric } from '@/components/ui/NeoMetric';
import { NeoBadge } from '@/components/ui/NeoBadge';
import { FinancialStatements } from '@/components/stock/FinancialStatements';
import { t } from '@/lib/i18n';
import {
  getStock,
  getValuation,
  type StockDetail,
  type ValuationResponse,
} from '@/lib/api';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ArrowLeft,
} from 'lucide-react';

// ── helpers ───────────────────────────────────────────────────────────────────

function fmtVND(value: number | null): string {
  if (value === null || value === undefined) return '—';
  return value.toLocaleString('vi-VN') + ' ₫';
}

function fmtPct(value: number | null): string {
  if (value === null || value === undefined) return '—';
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
}

function fmtNum(value: number | null, decimals = 2): string {
  if (value === null || value === undefined) return '—';
  return value.toFixed(decimals);
}

function recoVariant(reco: string): 'bullish' | 'bearish' | 'neutral' {
  if (reco === 'BUY') return 'bullish';
  if (reco === 'SELL') return 'bearish';
  return 'neutral';
}

function RecoIcon({ reco }: { reco: string }) {
  if (reco === 'BUY') return <TrendingUp size={16} className="inline mr-1 text-neo-bullish" />;
  if (reco === 'SELL') return <TrendingDown size={16} className="inline mr-1 text-neo-bearish" />;
  return <Minus size={16} className="inline mr-1 text-neo-muted" />;
}

// Simple bar: score 0-10 rendered as a progress bar
function ScoreBar({ score, max = 10 }: { score: number; max?: number }) {
  const pct = Math.min((score / max) * 100, 100);
  const color = pct >= 60 ? 'bg-neo-bullish' : pct >= 40 ? 'bg-neo-warning' : 'bg-neo-bearish';
  return (
    <div className="h-4 bg-neo-bg border-2 border-neo-stroke w-full">
      <div className={`h-full ${color} transition-all`} style={{ width: `${pct}%` }} />
    </div>
  );
}

// ── component ─────────────────────────────────────────────────────────────────

export default function StockDetailPage() {
  const { lang } = useLang();
  const params = useParams();
  const ticker = typeof params?.ticker === 'string' ? params.ticker.toUpperCase() : '';

  const [stock, setStock] = useState<StockDetail | null>(null);
  const [valuation, setValuation] = useState<ValuationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!ticker) return;
    setLoading(true);
    setError(null);
    try {
      const [stockData, valData] = await Promise.all([
        getStock(ticker),
        getValuation(ticker),
      ]);
      setStock(stockData);
      setValuation(valData);
    } catch (e) {
      setError(e instanceof Error ? e.message : t('error', lang));
    } finally {
      setLoading(false);
    }
  }, [ticker, lang]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // ── render states ─────────────────────────────────────────────────────────

  if (loading && !stock) {
    // BCTC reads from the fast DB — show it without waiting on slow live price/valuation.
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center py-12 text-neo-muted font-bold animate-pulse text-xl uppercase">
          {t('loading', lang)} — {ticker}
        </div>
        <FinancialStatements ticker={ticker} />
      </div>
    );
  }

  if (error && !stock) {
    return (
      <div className="space-y-4">
        <Link href="/screener" className="flex items-center gap-2 text-sm font-bold hover:underline">
          <ArrowLeft size={16} /> {t('screener', lang)}
        </Link>
        <NeoCard>
          <div className="text-neo-bearish font-bold py-8 text-center">
            {t('error', lang)}: {error}
          </div>
        </NeoCard>
        <FinancialStatements ticker={ticker} />
      </div>
    );
  }

  const disclaimer =
    stock?.disclaimer ??
    valuation?.disclaimer ??
    'Chỉ mang tính tham khảo, không phải lời khuyên đầu tư.';

  const reco = valuation?.recommendation ?? 'HOLD';
  const variant = recoVariant(reco);
  const upside = valuation?.upside_pct ?? null;

  return (
    <div className="space-y-6">
      {/* Back + header */}
      <div className="flex items-center gap-4 flex-wrap">
        <Link
          href="/screener"
          className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider hover:underline text-neo-muted"
        >
          <ArrowLeft size={16} /> {t('screener', lang)}
        </Link>
        <h2 className="text-2xl font-black uppercase tracking-wider flex items-center gap-3">
          {ticker}
          {stock?.company.short_name && (
            <span className="text-neo-muted text-base font-bold">{stock.company.short_name}</span>
          )}
        </h2>
        {stock?.company.sector && (
          <span className="text-xs font-bold font-mono text-neo-muted border-[2px] border-neo-muted px-2 py-0.5 uppercase">
            {stock.company.sector}
          </span>
        )}
      </div>

      {/* Disclaimer */}
      <div className="flex items-start gap-3 border-[3px] border-neo-warning bg-neo-warning/10 px-4 py-3">
        <AlertTriangle size={18} className="text-neo-warning mt-0.5 shrink-0" />
        <p className="text-sm font-bold text-neo-text">{disclaimer}</p>
      </div>

      {/* Price summary */}
      {stock && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <NeoCard>
            <NeoMetric
              label={t('close', lang)}
              value={fmtVND(stock.price.current_price)}
              variant="neutral"
            />
          </NeoCard>
          <NeoCard>
            <NeoMetric
              label="Market Cap"
              value={fmtVND(stock.price.market_cap)}
              variant="neutral"
            />
          </NeoCard>
          <NeoCard>
            <NeoMetric
              label="Free Float"
              value={stock.price.free_float_pct != null ? `${stock.price.free_float_pct.toFixed(1)}%` : '—'}
              variant="neutral"
            />
          </NeoCard>
          <NeoCard>
            <NeoMetric
              label="Foreign Room"
              value={stock.price.foreigner_pct != null ? `${stock.price.foreigner_pct.toFixed(1)}%` : '—'}
              variant="neutral"
            />
          </NeoCard>
        </div>
      )}

      {/* Valuation + Recommendation */}
      {valuation && (
        <NeoCard title="Định giá & Khuyến nghị">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
            <NeoMetric
              label="Giá hiện tại"
              value={fmtVND(valuation.current_price)}
              variant="neutral"
            />
            <NeoMetric
              label="Target Price"
              value={fmtVND(valuation.target_price)}
              variant={variant}
            />
            <NeoMetric
              label="Upside"
              value={fmtPct(upside)}
              variant={upside != null && upside >= 0 ? 'bullish' : 'bearish'}
            />
            <NeoMetric
              label="Score"
              value={`${valuation.score}/10`}
              variant={variant}
            />
          </div>

          {/* Score bar */}
          <div className="mb-4 space-y-1">
            <div className="flex justify-between text-xs font-mono text-neo-muted">
              <span>Composite Score</span>
              <span>{valuation.score}/10</span>
            </div>
            <ScoreBar score={valuation.score} />
          </div>

          {/* Recommendation badge */}
          <div className="flex items-center gap-4 mb-6">
            <span className="text-sm font-bold uppercase tracking-wider text-neo-muted">Recommendation</span>
            <NeoBadge
              status={reco === 'BUY' ? 'running' : reco === 'SELL' ? 'halted' : 'paper'}
              className="text-base px-4 py-1"
            >
              <RecoIcon reco={reco} />
              {reco}
            </NeoBadge>
          </div>

          {/* Extra valuation fields */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-6">
            {valuation.intrinsic_value != null && (
              <div>
                <div className="text-neo-muted font-bold uppercase text-xs tracking-wider mb-1">Intrinsic Value</div>
                <div className="font-mono font-bold">{fmtVND(valuation.intrinsic_value)}</div>
              </div>
            )}
            {valuation.f_score != null && (
              <div>
                <div className="text-neo-muted font-bold uppercase text-xs tracking-wider mb-1">
                  F-Score /{valuation.f_score_applicable}
                </div>
                <div className="font-mono font-bold">{valuation.f_score}</div>
              </div>
            )}
            {valuation.z_score != null && (
              <div>
                <div className="text-neo-muted font-bold uppercase text-xs tracking-wider mb-1">Z-Score</div>
                <div className="font-mono font-bold">{fmtNum(valuation.z_score)}</div>
              </div>
            )}
            <div>
              <div className="text-neo-muted font-bold uppercase text-xs tracking-wider mb-1">DCF</div>
              <div className={`font-mono font-bold ${valuation.dcf_applicable ? 'text-neo-bullish' : 'text-neo-muted'}`}>
                {valuation.dcf_applicable ? 'Applicable' : 'N/A'}
              </div>
            </div>
          </div>

          {/* Reasons list */}
          {valuation.reasons.length > 0 && (
            <div>
              <h4 className="text-sm font-black uppercase tracking-wider mb-3 text-neo-muted">
                Analysis Reasons
              </h4>
              <ul className="space-y-2">
                {valuation.reasons.map((reason, idx) => {
                  const positive = /tốt|cao|pass|buy|strong|đạt|vượt/i.test(reason);
                  const negative = /yếu|thấp|fail|sell|debt|âm|không đạt/i.test(reason);
                  return (
                    <li key={idx} className="flex items-start gap-2 text-sm">
                      {positive ? (
                        <CheckCircle size={16} className="text-neo-bullish mt-0.5 shrink-0" />
                      ) : negative ? (
                        <XCircle size={16} className="text-neo-bearish mt-0.5 shrink-0" />
                      ) : (
                        <Minus size={16} className="text-neo-muted mt-0.5 shrink-0" />
                      )}
                      <span className="font-mono">{reason}</span>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </NeoCard>
      )}

      {/* Financial ratios (BCTC) */}
      {stock && (
        <NeoCard title="Chỉ số tài chính (BCTC)">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            <NeoMetric label="P/E" value={fmtNum(stock.financials.pe_ratio)} variant="neutral" />
            <NeoMetric label="P/B" value={fmtNum(stock.financials.pb_ratio)} variant="neutral" />
            <NeoMetric
              label="ROE"
              value={stock.financials.roe != null ? fmtPct(stock.financials.roe * 100) : '—'}
              variant={stock.financials.roe != null && stock.financials.roe > 0 ? 'bullish' : 'bearish'}
            />
            <NeoMetric
              label="Net Margin"
              value={stock.financials.net_margin != null ? fmtPct(stock.financials.net_margin * 100) : '—'}
              variant={stock.financials.net_margin != null && stock.financials.net_margin > 0 ? 'bullish' : 'bearish'}
            />
            <NeoMetric
              label="D/E"
              value={fmtNum(stock.financials.debt_to_equity)}
              variant={
                stock.financials.debt_to_equity != null
                  ? stock.financials.debt_to_equity < 1 ? 'bullish' : 'bearish'
                  : 'neutral'
              }
            />
            <NeoMetric label="EPS" value={fmtNum(stock.financials.eps)} variant="neutral" />
          </div>
        </NeoCard>
      )}

      {/* Company info */}
      {stock && (
        <NeoCard title="Thông tin công ty">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-4 text-sm">
            <div>
              <div className="text-neo-muted font-bold uppercase text-xs tracking-wider mb-1">Tên đầy đủ</div>
              <div className="font-bold">{stock.company.name}</div>
            </div>
            <div>
              <div className="text-neo-muted font-bold uppercase text-xs tracking-wider mb-1">Ngành</div>
              <div className="font-bold">{stock.company.sector}</div>
            </div>
            <div>
              <div className="text-neo-muted font-bold uppercase text-xs tracking-wider mb-1">Ngày niêm yết</div>
              <div className="font-mono">{stock.company.listing_date}</div>
            </div>
            <div>
              <div className="text-neo-muted font-bold uppercase text-xs tracking-wider mb-1">Loại</div>
              <div>{stock.company.is_bank ? 'Ngân hàng' : 'Doanh nghiệp'}</div>
            </div>
            <div>
              <div className="text-neo-muted font-bold uppercase text-xs tracking-wider mb-1">CP phát hành</div>
              <div className="font-mono">{stock.price.issue_share.toLocaleString('vi-VN')}</div>
            </div>
          </div>
        </NeoCard>
      )}

      {/* Full financial statements (BS/IS/CF) from collected DB */}
      <FinancialStatements ticker={ticker} />
    </div>
  );
}
