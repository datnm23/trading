"""Spike vnstock 4.x (P0) — verify data đầy đủ cho VN30 trước khi build P1.

vnstock >= 4.0: class Vnstock() đã deprecated → dùng bộ `vnstock.api.*`.
Lấy OHLCV + BCTC (BS/IS/CF) + ratio + company cho 3 mã mẫu, in schema thực tế
(cột, dtype) làm input cho data models P1; sweep VN30 đo coverage + thời gian.

Chạy: python3 scripts/spike_vnstock.py
"""
from __future__ import annotations

import time
import traceback
import warnings

warnings.filterwarnings("ignore")

import pandas as pd  # noqa: E402

pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 180)

SAMPLE = ["FPT", "VNM", "HPG"]
SOURCE = "VCI"


def _q(symbol):
    from vnstock.api.quote import Quote

    return Quote(symbol=symbol, source=SOURCE)


def _fin(symbol):
    from vnstock.api.financial import Finance

    return Finance(symbol=symbol, source=SOURCE)


def _company(symbol):
    from vnstock.api.company import Company

    return Company(symbol=symbol, source=SOURCE)


def _timed(label, fn):
    t0 = time.perf_counter()
    try:
        out = fn()
        print(f"  [OK {time.perf_counter()-t0:.2f}s] {label}")
        return out
    except Exception as exc:  # noqa: BLE001
        print(f"  [ERR {time.perf_counter()-t0:.2f}s] {label}: {type(exc).__name__}: {str(exc)[:160]}")
        return None


def _describe(name, df):
    if df is None:
        print(f"    {name}: <none>")
        return
    if isinstance(df, pd.DataFrame):
        cols = list(df.columns)
        print(f"    {name}: shape={df.shape}")
        print(f"      columns({len(cols)}): {cols}")
        try:
            print(f"      head(2):\n{df.head(2).to_string()[:1500]}")
        except Exception:  # noqa: BLE001
            pass
    else:
        print(f"    {name}: type={type(df)} -> {str(df)[:300]}")


def probe(sym):
    print(f"\n=== {sym} ===")
    q, f, c = _q(sym), _fin(sym), _company(sym)
    _describe("OHLCV 3y", _timed("quote.history", lambda: q.history(start="2023-06-13", end="2026-06-13", interval="1D")))
    _describe("balance_sheet", _timed("balance_sheet year", lambda: f.balance_sheet(period="year", lang="vi")))
    _describe("income_statement", _timed("income_statement year", lambda: f.income_statement(period="year", lang="vi")))
    _describe("cash_flow", _timed("cash_flow year", lambda: f.cash_flow(period="year", lang="vi")))
    _describe("ratio", _timed("ratio year", lambda: f.ratio(period="year", lang="vi")))
    _describe("company.overview", _timed("company.overview", lambda: c.overview()))


def get_vn30():
    try:
        from vnstock.api.listing import Listing

        g = Listing(source=SOURCE).symbols_by_group("VN30")
        if isinstance(g, pd.Series):
            return list(g)
        if isinstance(g, pd.DataFrame):
            return list(g.iloc[:, 0])
        return list(g)
    except Exception as exc:  # noqa: BLE001
        print(f"VN30 listing ERR: {type(exc).__name__}: {exc}")
        return SAMPLE


def main():
    import vnstock

    print(f"vnstock version: {vnstock.__version__ if hasattr(vnstock, '__version__') else '4.x'}")
    print(f"source: {SOURCE}")

    print("\n### Sample symbols — schema sâu (input cho P1 models) ###")
    for s in SAMPLE:
        try:
            probe(s)
        except Exception:  # noqa: BLE001
            traceback.print_exc()
        time.sleep(0.8)

    print("\n### VN30 coverage sweep ###")
    vn30 = get_vn30()
    print(f"VN30 ({len(vn30)}): {vn30}")
    miss = {"ohlcv": [], "ratio": [], "bctc": []}
    t0 = time.perf_counter()
    for i, sym in enumerate(vn30):
        ok = []
        try:
            h = _q(sym).history(start="2025-01-01", end="2026-06-13", interval="1D")
            (ok.append("px") if h is not None and not h.empty else miss["ohlcv"].append(sym))
            f = _fin(sym)
            r = f.ratio(period="year", lang="vi")
            (ok.append("ratio") if r is not None and not r.empty else miss["ratio"].append(sym))
            b = f.balance_sheet(period="year", lang="vi")
            (ok.append("bctc") if b is not None and not b.empty else miss["bctc"].append(sym))
            print(f"  [{i+1}/{len(vn30)}] {sym}: {','.join(ok)}")
        except Exception as exc:  # noqa: BLE001
            print(f"  [{i+1}/{len(vn30)}] {sym} ERR: {type(exc).__name__}: {str(exc)[:120]}")
            miss["ohlcv"].append(sym)
        time.sleep(0.4)
    dt = time.perf_counter() - t0
    print(f"\nVN30 sweep {dt:.1f}s ({dt/max(len(vn30),1):.2f}s/symbol)")
    print(f"Missing OHLCV: {miss['ohlcv']}")
    print(f"Missing ratio: {miss['ratio']}")
    print(f"Missing BCTC : {miss['bctc']}")


if __name__ == "__main__":
    main()
