"""scan 4축 시장 스냅샷 — 전종목 지표 사전 계산 + percentile 즉시 조회.

rank 엔진의 buildSnapshot/getRank 패턴과 동일.
첫 호출 시 전종목 scan 실행 (~4분) → JSON 저장 → 이후 즉시 조회.

사용법::

    from dartlab.engines.dart.scan.snapshot import buildScanSnapshot, getScanPosition

    buildScanSnapshot()  # 최초 1회
    pos = getScanPosition("005930")
    # → {governance: {value, percentile, ...}, workforce: ..., capital: ..., debt: ...}
"""

from __future__ import annotations

import bisect
import json
import threading
from pathlib import Path


def _cacheDir() -> Path:
    from dartlab import config

    return Path(config.dataDir) / "_cache"


def _cachePath() -> Path:
    return _cacheDir() / "scan_snapshot.json"


def buildScanSnapshot(*, verbose: bool = True) -> dict[str, dict]:
    """전종목 scan 4축 핵심 지표 스냅샷 생성.

    기존 scan 함수를 그대로 호출하여 종목별 핵심 지표를 추출한다.
    결과를 JSON으로 저장하여 이후 조회는 즉시 가능.

    Returns:
        {stockCode: {governance_score, rev_per_employee, capital_class, icr, debt_risk}}
    """
    if verbose:
        print("[scan] 전종목 스냅샷 빌드 시작...")

    # ── governance: 총점 ──
    if verbose:
        print("  [1/4] governance 스캔...")
    from dartlab.engines.dart.scan.governance.scanner import (
        scan_audit_opinion,
        scan_major_holder_pct,
        scan_outside_directors,
        scan_pay_ratio,
    )
    from dartlab.engines.dart.scan.governance.scorer import (
        grade,
        score_audit,
        score_outside_ratio,
        score_ownership,
        score_pay_ratio,
    )

    holder_pct = scan_major_holder_pct()
    outside_ratio = scan_outside_directors()
    pay_ratio = scan_pay_ratio()
    audit_opinion = scan_audit_opinion()

    all_codes = set(holder_pct) | set(outside_ratio) | set(pay_ratio) | set(audit_opinion)
    governance_scores: dict[str, float] = {}
    governance_grades: dict[str, str] = {}
    for code in all_codes:
        s = (
            score_ownership(holder_pct.get(code))
            + score_outside_ratio(outside_ratio.get(code))
            + score_pay_ratio(pay_ratio.get(code))
            + score_audit(audit_opinion.get(code))
        )
        governance_scores[code] = s
        governance_grades[code] = grade(s)

    if verbose:
        print(f"    governance: {len(governance_scores)}종목")

    # ── workforce: 직원당매출 ──
    if verbose:
        print("  [2/4] workforce 스캔...")
    from dartlab.engines.dart.scan.workforce.scanner import scan_revenue_per_employee

    rev_per_emp = scan_revenue_per_employee()
    if verbose:
        print(f"    workforce: {len(rev_per_emp)}종목")

    # ── capital: 분류 ──
    if verbose:
        print("  [3/4] capital 스캔...")
    from dartlab.engines.dart.scan.capital.classifier import classify_return
    from dartlab.engines.dart.scan.capital.scanner import (
        scan_capital_change,
        scan_dividend,
        scan_treasury_stock,
    )

    dividends = scan_dividend()
    treasury = scan_treasury_stock()
    cap_changes = scan_capital_change()

    capital_classes: dict[str, str] = {}
    all_cap_codes = set(dividends) | set(treasury) | set(cap_changes)
    for code in all_cap_codes:
        div_info = dividends.get(code, {})
        trs_info = treasury.get(code, {})
        chg_info = cap_changes.get(code, {})

        has_div = div_info.get("배당여부", False)
        has_buyback = trs_info.get("당기취득", False)
        recent_inc = chg_info.get("최근증자", False)

        cls, _ = classify_return(has_div, has_buyback, recent_inc)
        capital_classes[code] = cls

    if verbose:
        print(f"    capital: {len(capital_classes)}종목")

    # ── debt: ICR + 위험등급 ──
    if verbose:
        print("  [4/4] debt 스캔...")
    from dartlab.engines.dart.scan.debt.risk import classify_risk, scan_icr
    from dartlab.engines.dart.scan.debt.scanner import scan_bonds

    icr_map = scan_icr()
    bonds_map = scan_bonds()

    debt_risk: dict[str, str] = {}
    debt_icr: dict[str, float] = {}
    all_debt_codes = set(icr_map) | set(bonds_map)
    for code in all_debt_codes:
        icr_val = icr_map.get(code)
        bond_info = bonds_map.get(code, {})
        short_pct = bond_info.get("단기비중")
        debt_risk[code] = classify_risk(icr_val, short_pct)
        if icr_val is not None:
            debt_icr[code] = icr_val

    if verbose:
        print(f"    debt: {len(debt_risk)}종목 (ICR {len(debt_icr)}종목)")

    # ── 통합 ──
    all_known = set(governance_scores) | set(rev_per_emp) | set(capital_classes) | set(debt_risk)

    snapshot: dict[str, dict] = {}
    for code in all_known:
        snapshot[code] = {
            "governance_score": governance_scores.get(code),
            "governance_grade": governance_grades.get(code),
            "rev_per_employee": rev_per_emp.get(code),
            "capital_class": capital_classes.get(code),
            "icr": debt_icr.get(code),
            "debt_risk": debt_risk.get(code),
        }

    # ── 분포 통계 (percentile 계산용 정렬 배열) ──
    gov_sorted = sorted(v for v in governance_scores.values() if v is not None)
    rpe_sorted = sorted(v for v in rev_per_emp.values() if v is not None)
    icr_sorted = sorted(v for v in debt_icr.values() if v is not None)

    cap_dist = {}
    for cls in capital_classes.values():
        cap_dist[cls] = cap_dist.get(cls, 0) + 1

    distributions = {
        "governance_score": gov_sorted,
        "rev_per_employee": rpe_sorted,
        "icr": icr_sorted,
        "capital_class_dist": cap_dist,
    }

    # ── 저장 ──
    cache_dir = _cacheDir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    payload = {"snapshot": snapshot, "distributions": distributions}
    _cachePath().write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    if verbose:
        print(f"  [scan] {len(snapshot)}종목 스냅샷 저장: {_cachePath()}")

    return snapshot


# ── 조회 ──

_CACHE: dict | None = None
_CACHE_LOCK = threading.Lock()


def _ensureCache() -> dict | None:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    with _CACHE_LOCK:
        if _CACHE is not None:
            return _CACHE
        path = _cachePath()
        if not path.exists():
            return None
        _CACHE = json.loads(path.read_text(encoding="utf-8"))
    return _CACHE


def _percentile(sorted_arr: list[float], value: float) -> float:
    """정렬 배열에서 percentile rank 산출 (0~100)."""
    if not sorted_arr:
        return 0.0
    pos = bisect.bisect_right(sorted_arr, value)
    return round(pos / len(sorted_arr) * 100, 1)


def getScanPosition(stockCode: str) -> dict | None:
    """종목의 scan 4축 시장 내 위치 조회.

    스냅샷이 없으면 None. buildScanSnapshot() 선행 필요.

    Returns:
        {governance: {value, percentile, grade, total},
         workforce: {value, percentile, total},
         capital: {class, distribution},
         debt: {icr, percentile, risk, total}}
    """
    cache = _ensureCache()
    if cache is None:
        return None

    snapshot = cache.get("snapshot", {})
    dist = cache.get("distributions", {})
    company = snapshot.get(stockCode)
    if company is None:
        return None

    result: dict[str, dict | None] = {}

    # governance
    gov_score = company.get("governance_score")
    gov_sorted = dist.get("governance_score", [])
    if gov_score is not None:
        result["governance"] = {
            "value": gov_score,
            "percentile": _percentile(gov_sorted, gov_score),
            "grade": company.get("governance_grade"),
            "total": len(gov_sorted),
        }
    else:
        result["governance"] = None

    # workforce
    rpe = company.get("rev_per_employee")
    rpe_sorted = dist.get("rev_per_employee", [])
    if rpe is not None:
        result["workforce"] = {
            "value": rpe,
            "percentile": _percentile(rpe_sorted, rpe),
            "total": len(rpe_sorted),
        }
    else:
        result["workforce"] = None

    # capital (이산 → percentile 대신 분류 분포)
    cap_cls = company.get("capital_class")
    cap_dist = dist.get("capital_class_dist", {})
    if cap_cls is not None:
        result["capital"] = {
            "class": cap_cls,
            "distribution": cap_dist,
        }
    else:
        result["capital"] = None

    # debt
    icr = company.get("icr")
    icr_sorted = dist.get("icr", [])
    if icr is not None:
        result["debt"] = {
            "icr": icr,
            "percentile": _percentile(icr_sorted, icr),
            "risk": company.get("debt_risk"),
            "total": len(icr_sorted),
        }
    else:
        debt_risk = company.get("debt_risk")
        if debt_risk:
            result["debt"] = {"icr": None, "percentile": None, "risk": debt_risk, "total": len(icr_sorted)}
        else:
            result["debt"] = None

    return result
