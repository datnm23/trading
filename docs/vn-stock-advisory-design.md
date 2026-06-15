# Thiết kế hệ thống — Nền tảng Phân tích & Tư vấn Chứng khoán VN

> **Ngày:** 2026-06-15 · **Trạng thái:** Design approved (brainstorm) · **Bước sau:** /ck:plan cho MVP-1
> **Định vị:** Pivot từ crypto trading bot → **nền tảng advisory** cho chứng khoán Việt Nam (screening + định giá + tin tức + AI analyst). **Advisory-only, không tự đặt lệnh.**

---

## 1. Tầm nhìn sản phẩm

Hệ thống hỗ trợ nhà đầu tư cá nhân ra quyết định trên TTCK VN qua 4 năng lực:
1. **Rà soát thị trường** — lọc tự động tìm mã tiềm năng (screener FA + TA).
2. **Phân tích & định giá mã** — DCF/P-E/P-B relative, F-score/Z-score → điểm + target price + khuyến nghị BUY/SELL/HOLD.
3. **Tổng hợp tin tức** — crawl tin trong + ngoài nước → LLM sentiment → bổ sung tín hiệu.
4. **AI Analyst** — LLM đọc BCTC + tin tức + wiki → luận điểm khuyến nghị có giải thích.

**Không làm (YAGNI):** tự đặt lệnh, execution engine, broker order API, margin/short logic. Người dùng tự đặt lệnh trên app môi giới của họ.

## 2. Quyết định nền tảng (từ brainstorm)

| Quyết định | Lựa chọn | Hệ quả |
|-----------|----------|--------|
| Quan hệ repo | **Pivot hoàn toàn**, tái dùng core | Bỏ crypto execution, giữ backend/frontend/journal/RAG/wiki |
| Mô hình | **Advisory-only** | Xóa toàn bộ rủi ro money-safety (Nhóm A audit); không cần broker order API |
| Nguồn data | **vnstock (free)** trước → TCBS/DNSE bổ sung | Bắt đầu không cần đăng ký; mở rộng sau |
| Vai trò AI | **LLM analyst** (đọc BCTC + tin) | Tái dùng RAG infra; không dùng ML dự báo giá (đã chứng minh thất bại ở crypto) |
| MVP-1 | **Data + Screener + Định giá** | Lõi deterministic, backtest-able, rẻ; nền cho News+AI |
| Phạm vi MVP | **VN30 (30 mã)** | Data sạch, LLM rẻ, làm chuẩn rồi mở rộng HOSE → 3 sàn |

## 3. Kiến trúc mục tiêu

```
FRONTEND (Next.js, tái dùng skeleton)
  Screener │ Stock Detail │ Watchlist │ News Radar │ AI Report
        │
BACKEND API (FastAPI, tái dùng)
  /screener  /stock/{ticker}  /valuation/{ticker}  /news  /report/{ticker}  /watchlist
        │
  ┌─────┴───────┬──────────────────┬──────────────────┐
SCREENER   ANALYSIS+VALUATION    NEWS+SENTIMENT      AI ANALYST
(FA+TA →   (DCF/PE/PB/Fscore →   (crawl + LLM        (LLM+RAG đọc
 watchlist) điểm+target+reco)     sentiment)          BCTC+tin → luận điểm)
  └─────────────┴────────┬─────────┴──────────────────┘
                         │
DATA LAYER (build mới)
  vnstock adapter (OHLCV + BCTC + ratios + company)  │  TCBS/DNSE adapter
  cache + normalize 3 sàn (HOSE/HNX/UPCOM)
        │
NỀN (tái dùng concept): Backtest (validate screener/reco) │ Journal (track khuyến nghị + paper portfolio) │ Wiki anchor │ Telegram alerts
```

## 4. Bản đồ tái sử dụng từ code crypto

| Tái dùng (giữ + sửa) | Vứt bỏ | Build mới |
|---|---|---|
| `backend/api/` (FastAPI + Socket.IO) | `execution/` (toàn bộ — CCXT, live/paper trading, order manager) | `data/vn/` adapter (vnstock, TCBS, DNSE) |
| `frontend/` (skeleton, đổi pages) | `strategies/ensemble/regime_ensemble.py` (tuned crypto) | `screener/` engine |
| `journal/` (đổi schema: log khuyến nghị thay vì trade) | `risk/manager.py` execution-coupled parts | `valuation/` (DCF, relative, scoring) |
| `knowledge_engine/` RAG (đổi nguồn: BCTC+tin thay wiki-only) | crypto data feeds (`data/feed.py`, `free_apis.py`) | `news/` crawler + sentiment |
| `crawl-wiki/` (giữ wiki value-investing tiếng Việt làm anchor) | `monitoring/comparison_engine.py` crypto | `ai_analyst/` (LLM report generator) |
| `monitoring/telegram.py`, `health_server.py` | frontend `arbitrage`, `live` pages | |
| `backtest/engine.py` (concept, sửa cho daily VN) | | |

## 5. Chi tiết 4 sub-system

### 5.1 Data Layer (MVP-1)
- **Primary:** `vnstock` (free, wrap VCI/TCBS). Cung cấp: lịch sử giá (OHLCV daily), BCTC (balance sheet / income statement / cash flow), chỉ số tài chính (P/E, P/B, ROE, EPS...), company overview, ngành.
- **Bổ sung:** TCBS / DNSE Entrade adapter (data phong phú hơn; KHÔNG dùng order API).
- Chuẩn hóa ticker theo sàn (HOSE/HNX/UPCOM), cache (parquet/SQLite), refresh schedule (EOD daily, BCTC theo quý).
- **Rủi ro & spike:** Phase 0 cần verify vnstock thực tế trả gì cho VN30 (độ đầy đủ BCTC, lịch sử, rate limit).

### 5.2 Screener (MVP-1)
- Lọc theo bộ tiêu chí cấu hình YAML (config-driven, giữ nguyên triết lý cũ):
  - **FA:** ROE > x, P/E < trung vị ngành, tăng trưởng doanh thu/EPS, nợ/vốn, biên LN.
  - **TA:** xu hướng (MA), relative strength vs VN-Index, thanh khoản (GTGD trung bình), breakout.
- Output: watchlist xếp hạng (composite score) → "mã tiềm năng".
- Backtest-able: chạy screener trên data lịch sử, đo hiệu quả top-N.

### 5.3 Analysis + Valuation (MVP-1)
- **Định giá:** DCF (anchor wiki `dinh_gia_dcf`), P/E relative (so ngành + lịch sử), P/B, dividend yield.
- **Chất lượng:** Piotroski F-score, Altman Z-score (cảnh báo phá sản).
- **Tổng hợp:** điểm 0–100 + target price + khuyến nghị BUY/SELL/HOLD + mức rủi ro.
- Anchor vào wiki value-investing (`dau_tu_gia_tri`, `ao_anh_gia_tri`) để tránh bẫy giá trị.

### 5.4 News + AI Analyst (MVP-2, sau MVP-1)
- **News crawler:** trong nước (cafef, vietstock, fireant, vnexpress kinh doanh); quốc tế (macro: Fed, hàng hóa, chỉ số toàn cầu).
- **LLM sentiment:** phân loại sentiment theo mã/ngành; trích sự kiện (cổ tức, phát hành, kết quả KD).
- **AI Analyst:** RAG over BCTC + tin + wiki → sinh báo cáo luận điểm (định giá + rủi ro + khuyến nghị có giải thích). Tái dùng `knowledge_engine` RAG. Giới hạn LLM trong VN30 để kiểm soát chi phí.

## 6. MVP-1 — Phạm vi chốt (Data + Screener + Định giá, VN30)

**Deliverable:**
```
- Data adapter vnstock cho 30 mã VN30 (OHLCV + BCTC + ratios), có cache
- Screener engine config-driven → watchlist xếp hạng
- Valuation engine → điểm + target + reco cho từng mã
- Backend endpoints: /screener, /stock/{ticker}, /valuation/{ticker}
- Frontend: trang Screener + Stock Detail
- Journal: lưu khuyến nghị + paper portfolio để track outcome
- Backtest screener trên lịch sử VN30 (validate edge)
```
**Tiêu chí hoàn thành:** screener chạy được trên VN30 với data thật vnstock; mỗi mã có định giá + khuyến nghị giải thích được; backtest cho thấy top-N screener vượt VN-Index.

## 7. Roadmap (phases)

| Phase | Nội dung | Phụ thuộc |
|-------|----------|-----------|
| **P0** | Spike vnstock (verify data VN30) + dọn repo (gỡ execution crypto) | — |
| **P1 (MVP-1)** | Data + Screener + Valuation (VN30) + endpoints + 2 trang FE + journal khuyến nghị | P0 |
| **P2** | News crawler + LLM sentiment (VN30) | P1 |
| **P3** | AI Analyst (LLM report) + RAG repurpose | P1, P2 |
| **P4** | Mở rộng HOSE (~400 mã) + tối ưu cache/chi phí | P1–P3 |
| **P5** | Telegram alerts khuyến nghị + backtest/paper-portfolio tracking đầy đủ | P1–P4 |
| **P6** | (tùy chọn) 3 sàn + ML định lượng secondary | P4 |

## 8. Thay đổi tech stack

| Bỏ | Thêm |
|----|------|
| ccxt, websockets (crypto exchange) | vnstock |
| (giữ) | beautifulsoup4 / httpx (news crawl) |
| (giữ openai) | (giữ) chromadb, sentence-transformers cho RAG |
| (giữ) pandas, fastapi, next.js, postgresql | tcbs/dnse client (Phase sau) |

## 9. Rủi ro & giảm thiểu

| Rủi ro | Mức | Giảm thiểu |
|--------|-----|-----------|
| vnstock data thiếu/chậm/đổi API | Cao | Spike P0; adapter abstraction để swap nguồn (TCBS/DNSE) |
| Định giá DCF nhạy giả định → sai lệch | Cao | Sensitivity analysis; ưu tiên relative valuation; anchor wiki tránh value trap |
| LLM bịa số liệu (hallucination) khi đọc BCTC | Cao | RAG strict context; bắt LLM trích nguồn; số liệu lấy từ data layer, LLM chỉ luận giải |
| Chi phí LLM khi mở rộng nhiều mã | TB | Giới hạn VN30 trước; cache report; chỉ chạy khi có sự kiện/news |
| Khuyến nghị sai gây thua lỗ cho user | Cao | Disclaimer rõ "tham khảo, không phải lời khuyên đầu tư"; track & hiển thị hiệu quả lịch sử khuyến nghị |
| Pivot làm hỏng phần tái dùng | TB | Dọn repo có kiểm soát (P0); giữ git history |

## 10. Câu hỏi chưa giải quyết

1. **Tần suất cập nhật:** EOD (cuối ngày) đủ chưa, hay cần intraday? (advisory thường EOD là đủ, rẻ hơn nhiều).
2. **LLM provider:** OpenAI (đã có dep) hay model local/Vietnamese-tuned? (ảnh hưởng chi phí + chất lượng tiếng Việt).
3. **Wiki anchor:** giữ wiki Turtle Trading hiện tại hay cần crawl thêm nguồn tri thức đầu tư giá trị VN?
4. **Paper portfolio:** có muốn track danh mục ảo theo khuyến nghị để đo hiệu quả thực tế không? (đề xuất: có, dùng journal).
5. **Persist:** giữ PostgreSQL hay chuyển SQLite cho đơn giản (advisory cá nhân)?
