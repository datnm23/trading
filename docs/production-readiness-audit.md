# Production-Readiness Audit — Hybrid Trading System

> **Ngày:** 2026-06-15 · **Phạm vi:** toàn bộ codebase · **Mục tiêu đánh giá:** sẵn sàng **giao dịch tiền thật (live, real money)**
> **Phương pháp:** GitNexus code graph (6.389 nodes / 8.516 edges / 116 flows) + scout code thủ công + xác minh file:line
> **Phán quyết tổng thể:** 🔴 **CHƯA SẴN SÀNG TIỀN THẬT.** RegimeEnsemble có edge thật, nhưng execution layer có lỗi money-safety có thể gây mất vốn. Tiếp tục paper trading; chặn live cho đến khi nhóm Critical (A) được fix + có test.

---

## 1. Tóm tắt điều hành

| Hạng mục | Trạng thái | Mức rủi ro cho tiền thật |
|----------|-----------|--------------------------|
| Chiến lược (RegimeEnsemble) | ✅ Có alpha thật (+53.7% net WF vs +18.4% BuyHold) | Thấp |
| Risk layer (sizing/stops/psychology) | ✅ Thiết kế tốt | Thấp–TB |
| **Execution / money-safety** | 🔴 Nhiều lỗi nghiêm trọng | **CRITICAL** |
| Intelligence layer (Wiki/LLM/ML) | 🟠 Một phần trang trí | Cao (sai kỳ vọng) |
| Backend API / deploy | 🟠 Không auth, hardcode | Cao |
| Test coverage | 🟡 ~35% (mục tiêu 80%) | Trung bình |

**Kết luận:** Hệ thống là *RegimeEnsemble rule-based ensemble + 683 wiki concepts* hoạt động tốt trên backtest, nhưng lớp đưa lệnh ra sàn chưa đủ an toàn để giao tiền thật. 3 nhóm cần xử lý trước khi live: **(A) Execution money-safety**, **(B) Intelligence đúng kỳ vọng**, **(C) Backend/deploy security**.

---

## 2. Điểm mạnh (giữ nguyên, không phá)

- **Kiến trúc modular sạch:** 12 module Python tách layer rõ ràng, giao tiếp qua interface. Hub trung tâm theo graph: `journal/trade_logger.py` (out-deg 131), `execution/live_trading.py` (106), `execution/order_manager.py` (98).
- **Edge thật:** RegimeEnsemble walk-forward BTC/USDT 4h **+53.7% net / +58% gross**, vượt BuyHold (+18.4%) và ML-XGBoost (−4%). Quyết định HALT ML là đúng đắn, có dữ liệu.
- **Risk design tốt:** regime-aware position sizing, drawdown circuit breaker, psychology enforcer, correlation guard.
- **Observability:** Telegram song ngữ, health server, PostgreSQL journal, daily report.
- **Docs xuất sắc:** architecture/PDR/roadmap đầy đủ và đồng bộ với code (hiếm gặp).

---

## 3. Nhóm A — Execution Money-Safety 🔴 CRITICAL (chặn live)

> Đây là nhóm **bắt buộc fix trước khi giao tiền thật**. Mỗi lỗi đều có thể gây desync vốn hoặc mất tiền.

### A1. Partial-fill desync vốn → over-leverage
- **`execution/live_trading.py:598,608`** — `if result.success:` coi lệnh thành công = khớp **100%**; trừ vốn `self.capital -= size * price * 1.001` theo full size dù sàn chỉ khớp một phần.
- **`execution/order_manager.py`** — `success=True` được trả cả khi status là `PARTIALLY_FILLED`; trường `filled` được parse nhưng `live_trading.py` không đọc.
- **Hệ quả:** Vốn nội bộ lệch khỏi vị thế thật trên sàn → over-leverage, lệnh sau undersize/fail.
- **Khuyến nghị:** Đọc `result.order.filled` thực tế; cập nhật `position.size` và `capital` theo **filled amount + filled price thật**, không theo size yêu cầu.

### A2. Không reconcile vị thế với sàn khi khởi động lại
- **`execution/live_trading.py:599`** — `self.positions` là dict in-memory; không có bước đối soát balance/positions với sàn lúc start.
- **Hệ quả:** Bot crash/restart khi đang có lệnh mở → mất trạng thái, trailing stop/partial exit (cũng in-memory) biến mất.
- **Khuyến nghị:** Thêm bước startup reconciliation: `fetch_balance()` + `fetch_positions()` từ sàn, so khớp với state đã persist.

### A3. Order fail có thể crash trading loop
- **`execution/order_retry.py`** — `execute()` **raise** khi hết retry; **`execution/live_trading.py:596`** gọi không có try/except riêng.
- `order_retry.py` mặc định `retryable_exceptions=(Exception,)` → bắt mọi exception, che cả bug logic.
- **Hệ quả:** Một lỗi network/exchange có thể làm chết vòng giao dịch hoặc retry sai loại lỗi.
- **Khuyến nghị:** Bọc try/except quanh đưa lệnh, halt an toàn (không tiếp tục state corrupt); thu hẹp `retryable_exceptions` về network/timeout cụ thể.

### A4. Graduation Gate bypass được qua config
- **`execution/live_trading.py:162`** — `self.paper_mode = mode == "paper" or exec_cfg.get("paper", True)`.
- **Hệ quả:** Nếu `config.execution.paper: true`, cờ CLI `--mode live` bị **bỏ qua âm thầm**; ngược lại nếu config sai default, gate ở line ~293 không chặn đúng. Gate chỉ chạy 1 lần lúc start.
- **Khuyến nghị:** Tách rõ ý định live (explicit flag) khỏi gate kết quả; gate phải là điều kiện *bắt buộc đạt* mới cho live, không phụ thuộc default config.

### A5. Slippage tracking giả
- **`execution/live_trading.py:636`** — `filled_price = getattr(result, 'filled_price', price) or price`; `OrderResult` **không có** attr `filled_price` → luôn fallback về giá strategy.
- **Hệ quả:** Slippage ghi nhận luôn = 0; không phát hiện được trượt giá thật khi live.
- **Khuyến nghị:** Trả `filled/average price` thật từ order_manager và dùng nó.

### A6. Phí & precision hardcode
- **`execution/live_trading.py:608,679`** — phí hardcode `1.001` (buy) / `0.999` (sell), không lấy từ sàn.
- **`execution/order_manager.py`** — `min_order_size`, price/amount precision dùng default, không validate theo spec sàn → lệnh có thể bị sàn từ chối.
- **Khuyến nghị:** Lấy fee + precision từ `exchange.markets`; round amount/price theo spec trước khi submit.

### A7. Psychology size-multiplier áp sai thứ tự
- **`execution/live_trading.py:552–570`** — stop-loss tính trên size **gốc**, multiplier tâm lý áp **sau** → reward/risk méo (vd giảm size 50% nhưng stop giữ nguyên → effective risk gấp đôi trên size đã giảm).
- **Khuyến nghị:** Áp multiplier trước, rồi tính stop/sizing trên size cuối.

### A8. CCXT connector nuốt lỗi
- **`execution/connectors/ccxt_connector.py`** — nhiều block `except` trả `None`/`[]` âm thầm; không retry ở tầng connector.
- **Hệ quả:** Lỗi network transient bị coi như "không có dữ liệu", khó phân biệt với lỗi thật.
- **Khuyến nghị:** Log + phân loại lỗi; để tầng trên quyết định retry.

---

## 4. Nhóm B — Intelligence Layer "trang trí" 🟠 HIGH (sai kỳ vọng sản phẩm)

> Sản phẩm quảng bá "hybrid: rule + ML + knowledge anchor". Thực tế phần lớn intelligence không tác động lên quyết định live.

### B1. Wiki validation KHÔNG BAO GIỜ chặn lệnh
- **`strategies/ensemble/regime_ensemble.py:122`** — comment `# TEMPORARY: Allow signals even if wiki blocks (for testing)`; lệnh bị wiki "block" vẫn cho qua với strength hạ xuống ~0.3.
- **Hệ quả:** Wiki chỉ là bộ giảm trọng số, **không phải gate**. Tuyên bố "mọi tín hiệu được validate chống 683 concepts" gây cảm giác an toàn giả.
- **Khuyến nghị:** Quyết định rõ: bật hard-gate thật (và backtest lại) HOẶC chỉnh mô tả sản phẩm cho đúng.

### B2. LLM không bao giờ được gọi trong live path
- **`knowledge_engine/rag.py:114`** — `if not llm_client: return context`; live path không truyền `llm_client` → chỉ trả context RAG (TF-IDF + SVD), không có generation.
- **Khuyến nghị:** Hoặc wire LLM thật (OpenAI client đã có trong deps), hoặc bỏ tuyên bố "LLM" và gọi đúng là "RAG retrieval".

### B3. Feedback loop chưa đóng
- **`knowledge_engine/signal_validator.py`** — `update_min_alignment_from_feedback()` tồn tại nhưng `_recent_feedback` không bao giờ được populate; `min_alignment` thực tế tĩnh (hardcode 0.15, override 0.3).
- **Khuyến nghị:** Nối journal `wiki_feedback` → cập nhật threshold theo outcome thật, hoặc gỡ code chết.

### B4. ML là dead code + features synthetic
- ML đã HALT (đúng, −5% gross) nhưng pipeline **không wire vào live**; `ml/features/advanced.py` on-chain/sentiment/macro là **random synthetic**; `ml/drift_detection.py:248` baseline = `[0.7]*100` placeholder.
- **Khuyến nghị:** Đánh dấu rõ ML là experimental/secondary; tách khỏi đường live để không tạo overhead & nhầm lẫn. Nếu muốn ML secondary signal thật → cần data feed thật (Glassnode/Alternative.me/FRED).

---

## 5. Nhóm C — Backend API & Deploy Security 🟠 HIGH

### C1. Không có authentication
- **`backend/api/main.py`** — mọi endpoint (kể cả **POST `/api/v1/rebalance`**) không auth. Bất kỳ client nào tới được port 8090 đều đọc state/positions/trades và ghi rebalance target.
- **Khuyến nghị:** API key / token tối thiểu; bảo vệ endpoint ghi.

### C2. CORS mâu thuẫn
- **`backend/api/main.py`** allow localhost; **`backend/api/socket_manager.py:27`** allow `*`. Không nhất quán.
- **Khuyến nghị:** Thống nhất origin theo môi trường (env-driven).

### C3. Frontend hardcode localhost
- **`frontend/hooks/useSocketIO.ts:42`** và mọi `fetch` hardcode `http://localhost:8090` → không deploy khác máy/port.
- **Khuyến nghị:** Dùng `NEXT_PUBLIC_API_URL` env var.

### C4. Aggregator tổng hợp sub-strategy "giả"
- **`backend/api/aggregator.py`** — poll 1 bot `http://{BOT_HOST}:8080/health`; synthesize 3 sub-strategy từ ensemble đơn (không phải 3 bot thật); fail thì render state rỗng âm thầm, không retry.
- **Khuyến nghị:** Hiển thị rõ trạng thái "bot offline"; cân nhắc bỏ sub-strategy giả hoặc đánh dấu là derived view.

---

## 6. Nhóm D — Test Coverage & Tech Debt 🟡 MEDIUM

- **Coverage ~35%** (mục tiêu 80%). Có 9 test file (`tests/test_{risk,execution,journal,psychology,drift,knowledge,backend_api,ml_integration}.py`). Critical path live-money (partial-fill, reconciliation, graduation gate, order retry failure) **thiếu test cho chính các kịch bản lỗi ở Nhóm A**.
- **18 marker** `placeholder/synthetic/TEMPORARY` trong code (notable: `regime_ensemble.py:122`, `ml/features/advanced.py:3`, `ml/drift_detection.py:248`, `risk/manager.py:76` Kelly placeholder).
- **`config/local.yaml` đang bị track trong git** (hiện keys **rỗng**, chưa leak) — nhưng README mô tả file này phải gitignored. Rủi ro: commit nhầm key thật về sau.
  - **Khuyến nghị:** `git rm --cached config/local.yaml`, thêm vào `.gitignore`, giữ lại `config/system.yaml` làm template.

---

## 7. Ma trận ưu tiên khắc phục (severity × effort)

| # | Việc | Nhóm | Severity | Effort | Chặn live? |
|---|------|------|----------|--------|-----------|
| 1 | Partial-fill: dùng filled amount/price thật | A1 | CRITICAL | TB | ✅ |
| 2 | Startup reconciliation với sàn | A2 | CRITICAL | TB–Cao | ✅ |
| 3 | Try/except + halt an toàn quanh đưa lệnh | A3 | CRITICAL | Thấp | ✅ |
| 4 | Graduation gate: explicit live flag + enforce | A4 | CRITICAL | Thấp | ✅ |
| 5 | Fee/precision từ sàn, bỏ hardcode | A6 | High | TB | ✅ |
| 6 | Slippage dùng filled price thật | A5 | High | Thấp | ⚠️ |
| 7 | Psychology multiplier đúng thứ tự | A7 | High | Thấp | ⚠️ |
| 8 | Test cho kịch bản lỗi Nhóm A | D | High | TB | ✅ |
| 9 | Quyết định Wiki gate: bật thật / sửa mô tả | B1 | High | TB | — |
| 10 | API auth + CORS thống nhất | C1,C2 | High | Thấp–TB | — |
| 11 | Frontend env-driven URL | C3 | Med | Thấp | — |
| 12 | Gỡ `local.yaml` khỏi git | D | Med | Thấp | — |
| 13 | LLM thật / feedback loop / ML cleanup | B2–B4 | Med | Cao | — |

---

## 8. Checklist Go-Live (điều kiện tối thiểu để cho tiền thật)

- [ ] A1 Partial-fill: capital & position cập nhật theo filled thật — có test
- [ ] A2 Reconciliation với sàn lúc start — có test
- [ ] A3 Đưa lệnh được bọc try/except, lỗi → halt an toàn — có test
- [ ] A4 Graduation gate enforce, không bypass qua config — có test
- [ ] A5 Slippage tracking dùng filled price thật
- [ ] A6 Fee & precision lấy từ sàn
- [ ] D Coverage critical path execution ≥ 80%
- [ ] C1 API write endpoint có auth (nếu expose ra ngoài máy)
- [ ] Chạy paper trading ổn định ≥ 30 ngày + positive net (theo success criteria roadmap)
- [ ] Bắt đầu live với capital tối thiểu + max 1% risk/trade + max DD halt

---

## 9. Câu hỏi chưa giải quyết

1. **Wiki gate:** có muốn bật hard-block thật (cần backtest lại để xem ảnh hưởng edge), hay chấp nhận wiki là bộ giảm trọng số và sửa mô tả sản phẩm?
2. **LLM:** có thực sự cần LLM generation trong live, hay RAG retrieval là đủ? (ảnh hưởng cost + latency NF2 < 5s).
3. **Reconciliation:** state hiện chỉ in-memory — có muốn persist position state ra PostgreSQL journal để khôi phục sau crash không?
4. **Sàn mục tiêu live:** Binance spot hay futures? (ảnh hưởng fee model, precision, margin logic ở A6).
5. **Backend expose:** API có chạy ngoài localhost không? Nếu chỉ local thì C1/C2/C3 hạ ưu tiên.
