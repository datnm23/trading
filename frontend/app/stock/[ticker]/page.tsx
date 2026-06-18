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
  getSignal,
  type StockDetail,
  type ValuationResponse,
  type SignalItem,
  type PeriodType,
} from '@/lib/api';
import { SignalBadge } from '@/components/stock/SignalBadge';
import {
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

// Compact VND for large aggregates (Market Cap): nghìn tỷ / tỷ, no decimal noise.
function fmtCompactVND(value: number | null): string {
  if (value === null || value === undefined || value <= 0) return '—';
  if (value >= 1e12) return `${(value / 1e12).toFixed(1)} nghìn tỷ ₫`;
  if (value >= 1e9) return `${(value / 1e9).toFixed(1)} tỷ ₫`;
  return Math.round(value).toLocaleString('vi-VN') + ' ₫';
}

function fmtPct(value: number | null): string {
  if (value === null || value === undefined) return '—';
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
}

function fmtNum(value: number | null, decimals = 2): string {
  if (value === null || value === undefined) return '—';
  return value.toFixed(decimals);
}

function actionToVariant(action: string): 'bullish' | 'bearish' | 'neutral' {
  if (action === 'BUY') return 'bullish';
  if (action === 'SELL') return 'bearish';
  return 'neutral';
}

// Simple bar: score rendered as a progress bar (valuation score is 0-100)
function ScoreBar({ score, max = 100 }: { score: number; max?: number }) {
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
  const [signal, setSignal] = useState<SignalItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // BCTC period lives here so the year/quarter choice survives the loading→loaded
  // branch swap below (which remounts FinancialStatements).
  const [finPeriod, setFinPeriod] = useState<PeriodType>('year');

  const fetchData = useCallback(async () => {
    if (!ticker) return;
    setLoading(true);
    setError(null);
    try {
      const [stockData, valData, sigData] = await Promise.all([
        getStock(ticker),
        getValuation(ticker),
        getSignal(ticker),
      ]);
      setStock(stockData);
      setValuation(valData);
      setSignal(sigData);
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
        <FinancialStatements ticker={ticker} period={finPeriod} onPeriodChange={setFinPeriod} />
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
        <FinancialStatements ticker={ticker} period={finPeriod} onPeriodChange={setFinPeriod} />
      </div>
    );
  }

  const disclaimer =
    stock?.disclaimer ??
    valuation?.disclaimer ??
    'Chỉ mang tính tham khảo, không phải lời khuyên đầu tư.';

  // Unified signal is source-of-truth for action; valuation is supplementary
  const signalAction = signal?.action ?? 'HOLD';
  const variant = actionToVariant(signalAction);
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
              value={fmtCompactVND(stock.price.market_cap)}
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

      {/* Unified signal card — source-of-truth */}
      {signal && (
        <NeoCard title={t('signalAction', lang)}>
          <div className="flex items-center gap-6 flex-wrap mb-4">
            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-neo-muted mb-1">
                {t('signalAction', lang)}
              </div>
              <SignalBadge action={signal.action} className="text-base px-4 py-1" />
            </div>
            <NeoMetric
              label={t('signalScore', lang)}
              value={`${signal.score.toFixed(1)}/100`}
              variant={variant}
            />
            {signal.current_price != null && (
              <NeoMetric
                label={t('price', lang)}
                value={fmtVND(signal.current_price)}
                variant="neutral"
              />
            )}
            {signal.target_price != null && (
              <NeoMetric
                label={t('targetPrice', lang)}
                value={fmtVND(signal.target_price)}
                variant={variant}
              />
            )}
          </div>
          {/* Score bar */}
          <div className="mb-4 space-y-1">
            <div className="flex justify-between text-xs font-mono text-neo-muted">
              <span>{t('signalScore', lang)}</span>
              <span>{signal.score.toFixed(1)}/100</span>
            </div>
            <ScoreBar score={signal.score} max={100} />
          </div>
          {/* Signal reasons */}
          {signal.reasons.length > 0 && (
            <p className="text-sm font-mono text-neo-text">{signal.reasons[0]}</p>
          )}
          {signal.action === 'INSUFFICIENT' && (
            <p className="text-xs font-bold text-neo-warning mt-2">
              {lang === 'vi'
                ? 'Thiếu định giá tin cậy — chưa đủ cơ sở khuyến nghị.'
                : 'Insufficient reliable valuation — recommendation pending.'}
            </p>
          )}
        </NeoCard>
      )}

      {/* Valuation + Supplementary details */}
      {valuation && (
        <NeoCard title="Định giá & Khuyến nghị (bổ trợ)">
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
              label="Valuation Score"
              value={`${valuation.score}/100`}
              variant={variant}
            />
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
      <FinancialStatements ticker={ticker} period={finPeriod} onPeriodChange={setFinPeriod} />
    </div>
  );
}
