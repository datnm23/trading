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
