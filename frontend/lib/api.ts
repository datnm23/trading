/**
 * Env-driven API client for VN Stock Advisory backend.
 * Reads NEXT_PUBLIC_API_URL (default: http://localhost:8090).
 */

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') ?? 'http://localhost:8090';

// ── Types (mirrored from backend/api/models.py) ──────────────────────────────

export interface CriterionDetail {
  key: string;
  label: string;
  passed: boolean;
  value: number | null;
  weight: number;
}

export interface ScreenerItem {
  ticker: string;
  score: number;
  rank: number;
  passed_count: number;
  criteria: CriterionDetail[];
}

export interface ScreenerResponse {
  items: ScreenerItem[];
  count: number;
  disclaimer: string;
}

export interface PriceSummary {
  current_price: number;
  market_cap: number;
  issue_share: number;
  free_float_pct: number | null;
  foreigner_pct: number | null;
}

export interface FinancialSummary {
  pe_ratio: number | null;
  pb_ratio: number | null;
  roe: number | null;
  net_margin: number | null;
  debt_to_equity: number | null;
  eps: number | null;
}

export interface CompanySummary {
  name: string;
  short_name: string;
  sector: string;
  is_bank: boolean;
  listing_date: string;
}

export interface StockDetail {
  ticker: string;
  company: CompanySummary;
  price: PriceSummary;
  financials: FinancialSummary;
  disclaimer: string;
}

export interface ValuationResponse {
  ticker: string;
  current_price: number;
  target_price: number | null;
  intrinsic_value: number | null;
  upside_pct: number | null;
  score: number;
  recommendation: string;
  f_score: number | null;
  f_score_applicable: number;
  z_score: number | null;
  dcf_applicable: boolean;
  reasons: string[];
  disclaimer: string;
}

// ── Internal ─────────────────────────────────────────────────────────────────

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function apiFetch<T>(path: string): Promise<T> {
  const url = `${BASE_URL}${path}`;
  let res: Response;
  try {
    res = await fetch(url, { cache: 'no-store' });
  } catch (err) {
    throw new Error(`Network error fetching ${url}: ${String(err)}`);
  }
  if (!res.ok) {
    throw new ApiError(res.status, `HTTP ${res.status} from ${url}`);
  }
  return res.json() as Promise<T>;
}

// ── Public helpers ────────────────────────────────────────────────────────────

export function getBaseUrl(): string {
  return BASE_URL;
}

export async function getScreener(): Promise<ScreenerResponse> {
  return apiFetch<ScreenerResponse>('/api/v1/screener');
}

export async function getStock(ticker: string): Promise<StockDetail> {
  return apiFetch<StockDetail>(`/api/v1/stock/${encodeURIComponent(ticker)}`);
}

export async function getValuation(ticker: string): Promise<ValuationResponse> {
  return apiFetch<ValuationResponse>(`/api/v1/valuation/${encodeURIComponent(ticker)}`);
}

// ── Market overview ───────────────────────────────────────────────────────────

export interface MarketIndex {
  symbol: string;
  value: number;
  change_pct: number | null;
  series: number[];
}

export interface MarketStock {
  ticker: string;
  name: string;
  sector: string;
  price: number;
  change_pct: number | null;
}

export interface MarketOverviewResponse {
  index: MarketIndex | null;
  stocks: MarketStock[];
  disclaimer: string;
}

export async function getMarketOverview(): Promise<MarketOverviewResponse> {
  return apiFetch<MarketOverviewResponse>('/api/v1/market/overview');
}

// ── Recommendations ────────────────────────────────────────────────────────────

export interface RecommendationItem {
  id: number;
  ticker: string;
  date: string;
  recommendation: 'BUY' | 'SELL' | 'HOLD' | 'INSUFFICIENT';
  target_price: number | null;
  current_price: number | null;
  score: number | null;
  upside_pct: number | null;
  reasons: string[];
  created_at: string;
}

export interface RecommendationsResponse {
  items: RecommendationItem[];
  count: number;
  disclaimer: string;
}

export async function getRecommendations(limit = 100): Promise<RecommendationsResponse> {
  return apiFetch<RecommendationsResponse>(`/api/v1/recommendations?limit=${limit}`);
}

// ── Unified signals (source-of-truth: tech × valuation matrix) ───────────────

export type SignalAction = 'BUY' | 'HOLD' | 'SELL' | 'INSUFFICIENT';

export interface SignalItem {
  ticker: string;
  name: string;
  sector: string;
  action: SignalAction;
  score: number;          // 0-100, higher = better
  tech_score: number | null;
  val_upside: number | null; // fraction e.g. -0.208; null if not reliable
  reliable: boolean;
  current_price: number | null;
  target_price: number | null;
  reasons: string[];
}

export interface SignalsResponse {
  items: SignalItem[];
  count: number;
  disclaimer: string;
}

/** Fetch all VN30 signals sorted by score desc */
export async function getSignals(): Promise<SignalsResponse> {
  return apiFetch<SignalsResponse>('/api/v1/signals');
}

/** Fetch signal for a single ticker; returns null if not found */
export async function getSignal(ticker: string): Promise<SignalItem | null> {
  const resp = await apiFetch<SignalsResponse>(`/api/v1/signal/${encodeURIComponent(ticker)}`);
  return resp.items[0] ?? null;
}

// ── Knowledge base (RAG) ────────────────────────────────────────────────────────

export interface WikiResult {
  id: string;
  title: string;
  content: string;
  score: number;
  source_url: string;
}

export interface WikiSearchResponse {
  query: string;
  results: WikiResult[];
  count: number;
}

export async function searchWiki(query: string): Promise<WikiSearchResponse> {
  return apiFetch<WikiSearchResponse>(`/api/v1/wiki/search?q=${encodeURIComponent(query)}`);
}

// ── Financial statements (BCTC) ─────────────────────────────────────────────

export interface FinancialLineItem {
  item_id: string;
  label: string;
  values: Record<string, number | null>;
}

export interface FinancialStatementView {
  statement_type: string;
  periods: string[];
  rows: FinancialLineItem[];
}

export interface FinancialsResponse {
  ticker: string;
  period_type: string;
  statements: FinancialStatementView[];
  disclaimer: string;
}

export type PeriodType = 'year' | 'quarter';

export async function getFinancials(
  ticker: string,
  periodType: PeriodType = 'year',
): Promise<FinancialsResponse> {
  return apiFetch<FinancialsResponse>(
    `/api/v1/stock/${encodeURIComponent(ticker)}/financials?period_type=${periodType}`,
  );
}
