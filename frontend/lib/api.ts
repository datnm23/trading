/** Centralized API base URL for all frontend HTTP/SocketIO calls.
 *
 * Use `NEXT_PUBLIC_API_URL` env var in production.
 * Falls back to `http://localhost:8090` for local dev.
 */
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8090';
