'use client';

import { useEffect, useState } from 'react';
import { getBaseUrl } from '@/lib/api';

/**
 * Poll the advisory backend's GET /health and report liveness.
 *
 * Replaces the crypto-era Socket.IO connection indicator: the advisory API is
 * request/response (no live stream), so there is no socket server to connect to.
 * This reflects the real backend state and avoids the constant failed Socket.IO
 * reconnect storm that ran on every page via the Header.
 */
export function useApiHealth(intervalMs: number = 15000) {
  const [healthy, setHealthy] = useState(false);

  useEffect(() => {
    let active = true;
    const base = getBaseUrl();

    const check = async () => {
      try {
        const res = await fetch(`${base}/health`, { cache: 'no-store' });
        if (active) setHealthy(res.ok);
      } catch {
        if (active) setHealthy(false);
      }
    };

    check();
    const id = setInterval(check, intervalMs);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [intervalMs]);

  return { healthy };
}
