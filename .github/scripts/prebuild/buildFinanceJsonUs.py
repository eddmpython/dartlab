"""edgar/scan/finance.parquet (다년 패널) → landing/static/dashboards/finance-us.json.

US(EDGAR) 터미널 게이트용 경량 5Y 재무 집계. KR ``buildFinanceJson`` 의 US 대칭 —
KR 은 ``dart/scan/finance.parquet``(long, account_id_std) 을 읽고, US 는
``edgar/scan/finance.parquet``(wide 다년 패널, std 컬럼) 을 읽는다. buildAnnual 회사별
재호출이 아니라 scan 집계 SSOT 단일 소스를 reshape — ``별도빌드 금지`` 준수.

출력 shape = ``finance.json`` 동형 + currency='USD' (조 USD = ÷1e12)::

    {
      "version": "v16-us",
      "years": ["2021", ..., "2025"],
      "companies": {
        "AAPL": {
          "currency": "USD",
          "is":  {"sales": [...5], "op": [...5], "net": [...5], "opMargin": [...5]},
          "bs":  {"assets": {...}, "liab": {...}, "equity": {...}, "totals": {...6×5}},
          "cf":  {"op", "inv", "fin", "opening", "closing", "fx"},  # 최신연도 단일값
          "ratios": {"roe": [...5], "debtRatio": [...5]},
          "macroExposure": null
        }, ...
      }
    }

실행::

    uv run python -X utf8 .github/scripts/prebuild/buildFinanceJsonUs.py [--src PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "data" / "edgar" / "scan" / "finance.parquet"
OUT = ROOT / "landing" / "static" / "dashboards" / "finance-us.json"

YEARS = ["2021", "2022", "2023", "2024", "2025"]

# wide std 컬럼 → 출력 필드 (edgar scan finance schema = buildEdgarFinance targetAccounts)
IS_MAP = {"sales": "sales", "operating_profit": "op", "net_profit": "net"}
BS_ASSETS = {
    "cash_and_cash_equivalents": "cash",
    "trade_and_other_receivables": "recv",
    "inventories": "inv",
    "property_plant_and_equipment": "tang",
    "intangible_assets": "intan",
}
BS_LIAB = {
    "trade_and_other_payables": "pay",
    "shortterm_borrowings": "shortDebt",
    "longterm_borrowings": "longDebt",
}
BS_EQUITY = {"retained_earnings": "retained", "treasury_stock": "treasury"}
BS_TOTALS = {
    "total_assets": "totalAsset",
    "total_liabilities": "totalLiab",
    "total_stockholders_equity": "totalEquity",
    "current_assets": "currAsset",
    "current_liabilities": "currLiab",
}
CF_MAP = {"operating_cashflow": "op", "investing_cashflow": "inv", "financing_cash_flow": "fin"}


def _tril(v) -> float | None:
    """USD 금액 → 조 USD (÷1e12, 4 자리). None/비유한은 None."""
    if v is None:
        return None
    try:
        x = float(v)
    except (ValueError, TypeError):
        return None
    if x != x:  # NaN
        return None
    return round(x / 1_000_000_000_000, 4)


def _extractCompany(byYear: dict[str, dict]) -> dict:
    """{fy: row} → finance.json 동형 회사 dict (5Y is/bs/cf/ratios, USD 조)."""
    result: dict = {
        "currency": "USD",
        "is": {k: [None] * 5 for k in IS_MAP.values()},
        "bs": {
            "assets": {k: [None] * 5 for k in BS_ASSETS.values()},
            "liab": {k: [None] * 5 for k in BS_LIAB.values()},
            "equity": {k: [None] * 5 for k in BS_EQUITY.values()},
            "totals": {k: [None] * 5 for k in BS_TOTALS.values()},
        },
        "cf": {k: None for k in CF_MAP.values()},
    }
    for i, year in enumerate(YEARS):
        row = byYear.get(year)
        if not row:
            continue
        for col, out in IS_MAP.items():
            result["is"][out][i] = _tril(row.get(col))
        for col, out in BS_ASSETS.items():
            result["bs"]["assets"][out][i] = _tril(row.get(col))
        for col, out in BS_LIAB.items():
            result["bs"]["liab"][out][i] = _tril(row.get(col))
        for col, out in BS_EQUITY.items():
            result["bs"]["equity"][out][i] = _tril(row.get(col))
        for col, out in BS_TOTALS.items():
            result["bs"]["totals"][out][i] = _tril(row.get(col))
    # CF — 최신연도(2025) 단일값 (finance.json 규약과 동일)
    lastRow = byYear.get(YEARS[-1])
    if lastRow:
        for col, out in CF_MAP.items():
            result["cf"][out] = _tril(lastRow.get(col))
    result["cf"]["opening"] = None
    result["cf"]["closing"] = None
    result["cf"]["fx"] = 0.0

    # opMargin = op / sales * 100
    result["is"]["opMargin"] = []
    for i in range(5):
        op, sales = result["is"]["op"][i], result["is"]["sales"][i]
        result["is"]["opMargin"].append(
            round(op / sales * 100, 1) if (op is not None and sales and sales > 0) else None
        )

    # ratios — ROE = net / equity * 100, debtRatio = liab / equity * 100
    result["ratios"] = {"roe": [], "debtRatio": []}
    for i in range(5):
        net = result["is"]["net"][i]
        equity = result["bs"]["totals"]["totalEquity"][i]
        liab = result["bs"]["totals"]["totalLiab"][i]
        result["ratios"]["roe"].append(
            round(net / equity * 100, 1) if (net is not None and equity and equity > 0) else None
        )
        result["ratios"]["debtRatio"].append(
            round(liab / equity * 100, 1) if (liab is not None and equity and equity > 0) else None
        )

    result["macroExposure"] = None
    return result


def build(src: Path, out: Path) -> int:
    """edgar scan finance(다년 wide) → finance-us.json. 반환=회사 수."""
    if not src.exists():
        print(f"[finance-us] 소스 없음: {src} — edgar scan 빌드 필요(buildEdgarFinance)", flush=True)
        return 0
    t0 = time.time()
    df = pl.read_parquet(src)
    if "fy" not in df.columns or "stockCode" not in df.columns:
        print(f"[finance-us] 스키마 부적합(fy/stockCode 부재): {df.columns}", flush=True)
        return 0
    df = df.with_columns(pl.col("fy").cast(pl.Utf8).alias("_fy")).filter(pl.col("_fy").is_in(YEARS))
    companies: dict[str, dict] = {}
    for ticker, grp in df.group_by("stockCode"):
        tk = ticker[0] if isinstance(ticker, tuple) else ticker
        tk = str(tk).strip().upper()
        if not tk:
            continue
        byYear = {str(r["_fy"]): r for r in grp.iter_rows(named=True)}
        data = _extractCompany(byYear)
        # 전 연도 매출 전무면 게이트 무의미 — skip
        if any(v is not None for v in data["is"]["sales"]):
            companies[tk] = data
    output = {"version": "v16-us", "years": YEARS, "companies": companies}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    sizeMb = out.stat().st_size / 1024 / 1024
    print(f"[finance-us] 완료: {len(companies)}사, {sizeMb:.2f}MB, {time.time() - t0:.0f}초 → {out}", flush=True)
    return len(companies)


def main() -> int:
    """CLI 진입 — edgar scan finance → finance-us.json."""
    # prebuild = offline only.
    from dartlab.core.offlineGuard import enforceOffline

    enforceOffline()

    parser = argparse.ArgumentParser()
    parser.add_argument("--src", default=str(SRC), help="edgar scan finance parquet 경로(테스트용 override)")
    parser.add_argument("--out", default=str(OUT), help="출력 finance-us.json 경로")
    args = parser.parse_args()
    n = build(Path(args.src), Path(args.out))
    return 0 if n > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
