# PLAN — Neobrutalism Dashboard for Hybrid Trading System

## Overview
Build a Next.js frontend with Neobrutalism design + FastAPI/Socket.IO backend gateway for real-time trading dashboard.

## Architecture

```
trading/
├── backend/api/              # FastAPI + Socket.IO gateway (port 8090)
│   ├── main.py
│   ├── socket_manager.py
│   ├── aggregator.py
│   └── models.py
├── frontend/                 # Next.js 14 App Router
│   ├── app/                  # Pages
│   ├── components/ui/        # Neobrutalism components
│   ├── components/layout/    # Sidebar, Header
│   ├── components/charts/    # Recharts wrappers
│   ├── hooks/useSocketIO.ts  # Socket.IO client
│   ├── lib/api.ts            # REST fetcher
│   └── styles/neo-theme.css  # CSS variables
```

## Design Tokens (Neobrutalism)

| Token | Light | Dark | Usage |
|---|---|---|---|
| Background | `#F4F4F0` | `#1C293C` | Page bg |
| Surface | `#FFFFFF` | `#000000` | Cards |
| Stroke | `#000000` | `#F4F4F0` | Borders, text |
| Primary | `#FDC800` | `#FDC800` | Buttons, highlights |
| Bullish | `#B9FF66` | `#B9FF66` | Profit, buy |
| Bearish | `#FF6B6B` | `#FF6B6B` | Loss, sell |
| Font Body | Inter | Inter | Text |
| Font Mono | JetBrains Mono | JetBrains Mono | Numbers |
| Border Width | 3px | 3px | All cards/buttons |
| Shadow | `4px 4px 0 #000` | `4px 4px 0 #F4F4F0` | Offset shadow |

## Tech Stack

### Backend
- FastAPI (REST + Socket.IO)
- python-socketio (async)
- uvicorn
- httpx (async polling)

### Frontend
- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS
- socket.io-client
- recharts
- lucide-react
- next-themes

## Phases

### Phase 1: Python Backend API (Est: 1-2h)
- [ ] Add dependencies: fastapi, python-socketio, uvicorn, httpx
- [ ] Create `backend/api/models.py` — Pydantic schemas
- [ ] Create `backend/api/aggregator.py` — Poll health endpoints 8080/8081/8082
- [ ] Create `backend/api/socket_manager.py` — Socket.IO broadcast loop
- [ ] Create `backend/api/main.py` — FastAPI app, CORS, lifespan
- [ ] Test: `uvicorn backend.api.main:app --port 8090`

### Phase 2: Next.js Scaffolding (Est: 1h)
- [ ] `mkdir frontend && cd frontend`
- [ ] `npx create-next-app@latest . --typescript --tailwind --app`
- [ ] Install: socket.io-client, recharts, lucide-react, next-themes
- [ ] Configure Tailwind with Neobrutalism tokens
- [ ] Create `styles/neo-theme.css`

### Phase 3: Neobrutalism Components (Est: 2-3h)
- [ ] `components/ui/NeoCard.tsx` — Border-3, shadow-neo, hover lift
- [ ] `components/ui/NeoButton.tsx` — Primary bg, pressed state
- [ ] `components/ui/NeoMetric.tsx` — Mono font, bullish/bearish color
- [ ] `components/ui/NeoTable.tsx` — Thick header, row separators
- [ ] `components/ui/NeoBadge.tsx` — Status badges
- [ ] `components/layout/Sidebar.tsx` — Bold nav links
- [ ] `components/layout/Header.tsx` — Logo + theme toggle
- [ ] `components/layout/ThemeProvider.tsx` — next-themes

### Phase 4: Pages + Socket.IO (Est: 2-3h)
- [ ] `hooks/useSocketIO.ts` — Socket.IO client with auto-reconnect
- [ ] `lib/api.ts` — REST fetcher
- [ ] `app/layout.tsx` — Root layout
- [ ] `app/page.tsx` — Overview dashboard (SSR + WS hydrate)
- [ ] `app/live/page.tsx` — Live status
- [ ] `app/compare/page.tsx` — Strategy comparison
- [ ] `app/risk/page.tsx` — Risk monitor
- [ ] `app/reports/page.tsx` — Daily reports
- [ ] `app/wiki/page.tsx` — Wiki chat

### Phase 5: Test & Polish (Est: 1h)
- [ ] Dark mode toggle working
- [ ] WebSocket real-time updates
- [ ] Responsive mobile
- [ ] All pages accessible

## REST API Endpoints (FastAPI)

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/strategies` | List all strategy states |
| GET | `/api/v1/strategies/{name}` | Single strategy detail |
| GET | `/api/v1/positions` | All open positions |
| GET | `/api/v1/slippage` | Slippage summary |
| GET | `/api/v1/trailing-stops` | Trailing stop status |
| GET | `/api/v1/daily-report` | Today's report |
| GET | `/health` | Gateway health |

## WebSocket Events

### Client → Server
```json
{"type": "subscribe", "channel": "strategies"}
{"type": "subscribe", "channel": "positions"}
```

### Server → Client (broadcast every 5s)
```json
{
  "type": "state_update",
  "timestamp": "2026-04-22T22:00:00Z",
  "strategies": [...],
  "positions": [...],
  "alerts": [...]
}
```

## Notes
- No authentication (public dashboard)
- Hybrid SSR: Next.js fetch initial data server-side, then hydrate with Socket.IO
- Rebalance/Drift/Sentiment/Arbitrage features are Phase 6 (future)
