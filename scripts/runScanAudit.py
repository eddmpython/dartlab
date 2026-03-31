"""Scan 전축 audit — 축별 분리 실행.

Usage:
    uv run python -X utf8 scripts/runScanAudit.py <axis>
    uv run python -X utf8 scripts/runScanAudit.py all   # 모든 축 순차
    uv run python -X utf8 scripts/runScanAudit.py summary  # 저장된 결과 요약
"""
from __future__ import annotations

import gc
import json
import sys
import time
from pathlib import Path

OUT_DIR = Path("data/dart/auditScan")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 실행 가능 축 (target 불필요)
AXES = [
    "governance", "workforce", "capital", "debt",
    "cashflow", "profitability", "growth", "quality",
    "liquidity", "insider", "audit", "efficiency",
    "dividendTrend", "valuation", "macroBeta", "screen",
]


def audit_one(axis: str) -> dict:
    """한 축 실행 → 통계 dict 반환."""
    import polars as pl

    print(f"\n{'='*60}")
    print(f"[AUDIT] {axis} 시작")
    print(f"{'='*60}")

    t0 = time.time()
    try:
        import dartlab
        if axis == "screen":
            # screen은 target 없이 호출하면 프리셋 목록
            result = dartlab.scan("screen", "value")
        else:
            result = dartlab.scan(axis)
    except Exception as e:
        elapsed = time.time() - t0
        print(f"[ERROR] {axis}: {e}")
        return {
            "axis": axis,
            "status": "ERROR",
            "error": str(e),
            "elapsed_sec": round(elapsed, 1),
        }

    elapsed = time.time() - t0

    if not isinstance(result, pl.DataFrame):
        print(f"[SKIP] {axis}: 반환 타입 {type(result).__name__}")
        return {
            "axis": axis,
            "status": "SKIP",
            "returnType": type(result).__name__,
            "elapsed_sec": round(elapsed, 1),
        }

    nrows = result.height
    ncols = result.width
    columns = result.columns

    # NaN 분석
    nan_stats = {}
    for col in columns:
        dtype = str(result[col].dtype)
        null_count = result[col].null_count()
        null_pct = round(null_count / nrows * 100, 1) if nrows > 0 else 0
        nan_stats[col] = {
            "dtype": dtype,
            "null_count": int(null_count),
            "null_pct": null_pct,
        }

    # 최다 NaN 컬럼
    worst_col = max(nan_stats, key=lambda c: nan_stats[c]["null_pct"]) if nan_stats else None
    worst_pct = nan_stats[worst_col]["null_pct"] if worst_col else 0

    # 등급/분류 컬럼 분포
    grade_dist = {}
    for col in columns:
        if any(kw in col.lower() for kw in ["등급", "grade", "rank", "분류", "pattern", "패턴", "type", "class", "signal", "risk"]):
            try:
                vc = result[col].value_counts().sort("count", descending=True)
                grade_dist[col] = {
                    row[col]: int(row["count"])
                    for row in vc.head(10).to_dicts()
                    if row[col] is not None
                }
            except Exception:
                pass

    # 수치 컬럼 기초통계
    numeric_summary = {}
    for col in columns:
        dtype_str = str(result[col].dtype)
        if any(t in dtype_str for t in ["Float", "Int", "UInt"]):
            try:
                series = result[col].drop_nulls()
                if series.len() > 0:
                    numeric_summary[col] = {
                        "min": round(float(series.min()), 4),
                        "max": round(float(series.max()), 4),
                        "mean": round(float(series.mean()), 4),
                        "median": round(float(series.median()), 4),
                        "std": round(float(series.std()), 4) if series.len() > 1 else 0,
                        "count": int(series.len()),
                    }
            except Exception:
                pass

    info = {
        "axis": axis,
        "status": "OK",
        "rows": nrows,
        "cols": ncols,
        "columns": columns,
        "elapsed_sec": round(elapsed, 1),
        "worst_nan_col": worst_col,
        "worst_nan_pct": worst_pct,
        "nan_stats": nan_stats,
        "grade_distributions": grade_dist,
        "numeric_summary": numeric_summary,
    }

    print(f"[OK] {axis}: {nrows} rows, {ncols} cols, worst NaN: {worst_col}={worst_pct}%, {elapsed:.1f}s")

    # 메모리 해제
    del result
    gc.collect()

    return info


def run_all():
    """전 축 순차 실행."""
    results = []
    for axis in AXES:
        info = audit_one(axis)
        results.append(info)
        gc.collect()

    # 저장
    out_path = OUT_DIR / "scan_audit_2026-03-31.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[SAVED] {out_path}")
    return results


def print_summary(results: list[dict] | None = None):
    """결과 요약 출력."""
    if results is None:
        p = OUT_DIR / "scan_audit_2026-03-31.json"
        if not p.exists():
            print("결과 파일 없음. 먼저 'all'로 실행하세요.")
            return
        results = json.loads(p.read_text(encoding="utf-8"))

    print(f"\n{'='*80}")
    print(f"Scan Audit Summary — 2026-03-31")
    print(f"{'='*80}")
    print(f"{'축':<16} {'상태':<8} {'종목수':>8} {'컬럼':>6} {'최악NaN컬럼':<20} {'NaN%':>6} {'시간':>6}")
    print("-" * 80)
    for r in results:
        axis = r["axis"]
        status = r["status"]
        rows = r.get("rows", "-")
        cols = r.get("cols", "-")
        worst = r.get("worst_nan_col", "-") or "-"
        pct = r.get("worst_nan_pct", "-")
        elapsed = r.get("elapsed_sec", "-")
        print(f"{axis:<16} {status:<8} {rows:>8} {cols:>6} {worst:<20} {pct:>6} {elapsed:>6}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"

    if arg == "all":
        results = run_all()
        print_summary(results)
    elif arg == "summary":
        print_summary()
    elif arg in AXES:
        info = audit_one(arg)
        out_path = OUT_DIR / f"scan_audit_{arg}_2026-03-31.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        print(f"\n[SAVED] {out_path}")
    else:
        print(f"Unknown axis: {arg}")
        print(f"Available: {', '.join(AXES)}")
        sys.exit(1)
