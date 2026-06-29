"""제네릭 노트 추출기 — panel 노트 셀(NT_) → CompositionSeries(멤버/라벨 × 기간 비중).

축유형(noteShape)별 *1 엔진*으로 32 표준 IFRS 주석을 덮는다(bespoke 추출기 32개 = 덕지덕지 회피):

- ``composition`` — axisPath 멤버 피벗 (부문별/특수관계자 등 다축).
- ``lineitem`` — label 피벗 (지역별매출·판관비·종업원급여·비용성격별 등 단일축).
- ``movement``/``flat`` — 미지원(None, 정직). 변동표·잔액표는 후속.

비중(%) 출력이라 **단위-free**(분자[항목]/분모[Σ] 같은 raw scale 약분) — 단위추론 불요. shape 는
호출자가 레지스트리(`core/_entries/notes.py` DataEntry.noteShape)에서 받아 전달(추출기↔레지스트리 결합 0).
``_noteCellsFromPanel``(providers L1) 직독 — 별 bake 0(런타임-SSOT).

LLM Specifications:
    AntiPatterns:
        - 노트마다 bespoke 추출 함수 신설 금지 — shape 4종 제네릭만.
        - 절대액 단위환산 산수 금지 — 비중(%)은 약분이라 단위-free.
        - 합계/소계 행을 카테고리로 노출 금지(_isTotal 드롭) — 비중 왜곡.
    OutputSchema:
        - ``extractNoteView(...) -> {categories: list[str], points: list[CompositionPoint]} | None``
          (CompositionPoint = {period, year, quarter, total, shares: list[float]}).
    Prerequisites:
        - KR(DART) panel artifact. EDGAR(US)는 NT_ 부재 → None.
    Freshness:
        - 매 호출 (panel read-time 파생).
    Dataflow:
        - _noteCellsFromPanel(code, canonicalKey) → scope/축/연도 피벗 → 비중% → CompositionSeries.
    TargetMarkets:
        - KR (DART). XBRL 2022+ 정밀, 옛 표는 _parseOldNoteTable 위치파싱.
"""

from __future__ import annotations

import re
from typing import Any

# axisPath 멤버 토큰 — 회사 네임스페이스(entity######_XxxMember) 또는 표준(PlanAssetsMember) 멤버.
_MEMBER_RE = re.compile(r"entity\d+_([A-Za-z0-9]+?)Member", re.IGNORECASE)
_TOTAL_NAMES = ("합계", "계", "소계", "총계", "총액")
_MAX_PERIODS = 8


def _memberName(axisPath: str | None) -> str | None:
    """axisPath 마지막 멤버 토큰 → 읽기 이름. 총계축(ConsolidatedMember 단독)·축없음 = None.

    Examples:
        >>> _memberName("ConsolidatedMember|entity00164779_EssencoreLimitedMemberOfX")
        'EssencoreLimited'
        >>> _memberName("ConsolidatedMember|PlanAssetsMember")
        'PlanAssets'
        >>> _memberName("ConsolidatedMember") is None
        True
        >>> _memberName(None) is None
        True
    """
    if not axisPath:
        return None
    last = axisPath.split("|")[-1]
    m = _MEMBER_RE.search(last)
    if m:
        return m.group(1)
    if last.endswith("Member") and last not in ("ConsolidatedMember", "SeparateMember"):
        return last[: -len("Member")]
    return None


def _isTotal(name: str) -> bool:
    """라벨이 합계/소계 행인가 (비중 카테고리에서 드롭)."""
    n = name.replace(" ", "")
    return any(n == t or n.endswith(t) for t in _TOTAL_NAMES)


def _parseValue(raw: Any) -> float | None:
    """valueRaw(콤마·△·괄호) → float. build.cell._parseAmount 재사용(panel 자급 로직)."""
    from dartlab.providers.dart.panel.build.cell import _parseAmount

    return _parseAmount(str(raw or ""))


def extractNoteView(
    company: Any, canonicalKey: str, *, shape: str, maxPeriods: int = _MAX_PERIODS
) -> dict[str, Any] | None:
    """노트(canonicalKey) 셀 → CompositionSeries(멤버/라벨 × 기간 비중%). 제네릭 SSOT 추출.

    Args:
        company: Company 객체 (stockCode·market). KR 만 (EDGAR=None).
        canonicalKey: 정부 disclosureKey (NT_D######).
        shape: 축유형 — "composition"(axisPath 멤버) | "lineitem"(label). 그 외(movement/flat) = None.
        maxPeriods: 최근 기간 cap (기본 8).

    Returns:
        ``{categories, points}`` (CompositionSeries) 또는 None (데이터/지원 부재). categories =
        최신연도 비중 desc(합계행 제외), points = 연도별 {period, year, quarter, total, shares}.

    Example:
        >>> extractNoteView(c, "NT_D831150", shape="lineitem")  # doctest: +SKIP
        {'categories': ['미국', '중국', ...], 'points': [{'period': '2025Q4', 'shares': [...]}, ...]}

    Raises:
        없음 — 데이터/파싱 실패는 None.
    """
    if getattr(company, "market", "KR") != "KR":
        return None
    code = getattr(company, "stockCode", None)
    if not code or shape not in ("composition", "lineitem"):
        return None

    from dartlab.providers.dart.panel.cell import _noteCellsFromPanel

    cells = _noteCellsFromPanel(code, canonicalKey)
    if cells is None or not hasattr(cells, "is_empty") or cells.is_empty():
        return None

    perYear: dict[str, dict[str, float]] = {}
    for r in cells.iter_rows(named=True):
        if (r.get("scope") or "consolidated") != "consolidated":
            continue
        key = _memberName(r.get("axisPath")) if shape == "composition" else str(r.get("label") or "").strip()
        if not key or _isTotal(key):
            continue
        val = _parseValue(r.get("valueRaw"))
        year = r.get("ctxYear")
        if val is None or year is None:
            continue
        bucket = perYear.setdefault(str(year), {})
        bucket[key] = bucket.get(key, 0.0) + abs(val)

    if not perYear:
        return None
    years = sorted(perYear)[-maxPeriods:]
    latest = perYear[years[-1]]
    categories = [k for k, v in sorted(latest.items(), key=lambda kv: -kv[1]) if v > 0]
    if not categories:
        return None

    points: list[dict[str, Any]] = []
    for y in years:
        d = perYear[y]
        total = sum(d.get(c, 0.0) for c in categories)
        if total <= 0:
            continue
        shares = [round(100.0 * d.get(c, 0.0) / total, 2) for c in categories]
        points.append({"period": f"{y}Q4", "year": y, "quarter": "4분기", "total": total, "shares": shares})
    if not points:
        return None
    return {"categories": categories, "points": points}
