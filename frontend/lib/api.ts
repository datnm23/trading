/** Centralized API configuration for all frontend HTTP/SocketIO calls.
 *
 * Use `NEXT_PUBLIC_API_URL` env var in production.
 * Use `NEXT_PUBLIC_API_KEY` and `NEXT_PUBLIC_ADMIN_KEY` for auth.
 */
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8090';
export const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';
export const ADMIN_KEY = process.env.NEXT_PUBLIC_ADMIN_KEY || '';

/** Default headers for read-only API calls. */
export function apiHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (API_KEY) {
    headers['X-API-Key'] = API_KEY;
  }
  return headers;
}

/** Headers for admin operations (rebalance). */
export function adminHeaders(): Record<string, string> {
  const headers = apiHeaders();
  if (ADMIN_KEY) {
    headers['X-Admin-Key'] = ADMIN_KEY;
  }
  return headers;
}
