"""거울 작업대 순수 커널 : 엔진 자기서술을 반사해 이질 반환을 단일 tidy 롱으로 접는다 (L1.5 reference).

Capabilities:
    - reflectAxes: loadCapabilities() 소비로 축 카탈로그 + declared 필드를 얻는다 (raw 레지스트리
      재반사 금지 = 둘째 반사점 안 생김). 작업대측 손 축목록 0.
    - laneOf: 레인을 declared(returnType/listFn) 순수함수로. 없으면 shape morphology fallback +
      AMBIGUOUS 표면화 (조용한 확정 금지).
    - foldToCanonical: wide(KR 한글열/US 영문열)/dict/scoreDict/scalar 이질 반환을 shape family(~6)
      어댑터로 단일 정규 롱에 접는다. 접기 분기가 축 수(125)가 아니라 형태 수라 축이 늘어도 불변.
    - 접히지 않는 것(graph/note/nested)·역할불명 컬럼·계약위반은 조용히 삼키지 않고 gap 행 방출.

AIContext:
    개념 #1 데이터 작업대의 순수 계산 핵. 값 물질화(엔진 실호출)는 상위 L2.5 드라이버가 담당하고,
    본 모듈은 엔진 데이터를 부르지 않는 순수함수만 둔다 (메모리 가드: Company 루프 0). declared 는
    capability SSOT 가 이미 싣는다 (builder._injectAxisRegistriesLive, 2026-07-07). lane/universeScope
    같은 파생 의미는 저장하지 않고 여기서 계산한다.

Guide:
    reflectAxes() 로 축과 declared 를 얻고, 엔진이 반환한 raw 프레임을 foldToCanonical(raw, engine,
    axis, item, declared) 로 접는다. gap 리스트를 함께 받아 coverage 원장에 먹인다.

When:
    작업대가 여러 엔진 축을 하나의 (entity, period, item, value) 격자로 세울 때. 새 축은 declared 를
    싣기만 하면 코드 수정 0 으로 흡수된다.

Requires:
    reference.capability.loadCapabilities (축 카탈로그 + declared). polars. 엔진 데이터 접근 0.

How:
    shape family 판정(구조만, 값 무지) -> declared 우선 lane 판정 -> family 별 melt/평탄화 어댑터 ->
    정규 스키마 CANON 으로 select. entity 키는 구조 동의어 튜플 ENTITY_KEYS(종목코드/stockCode/
    code/ticker)로 식별, 실패면 unknownColumnRole gap. (capability evidenceSchema.targetKeys 는 8
    엔트리에만 있고 그 키가 이미 ENTITY_KEYS 에 포함돼 배선 이득 0 = 미배선.)

Raises:
    없음. 실패는 예외가 아니라 gap 행으로 방출한다 (결손 0 대체 금지).

SeeAlso:
    - mainPlan/scenario-simulator/18-workbench-mirror-design.md (설계·판정)
    - reference.capability.builder._injectAxisRegistriesLive (declared 원천)
    - tests/reference/capability/test_mirrorFold.py (7 shape 접기 + gap 방출)

Layer: L1.5 reference. polars 만 의존 (하향). 순수함수, 엔진 데이터 접근 0.
"""

from __future__ import annotations

import re
from typing import Any

import polars as pl

# entity/period 구조 동의어 = 전 축 entity 키 식별의 정본. O(시장 spelling) 상수지 O(축) 아님.
ENTITY_KEYS: tuple[str, ...] = ("종목코드", "stockCode", "code", "ticker")
ENTITY_NAME_KEYS: tuple[str, ...] = ("종목명", "corpName", "name")
_PERIOD_RE = re.compile(r"^\d{4}(Q[1-4]|\d{2})?$")  # 2025 / 2025Q3 / 202503, 국가 무관

CANON: tuple[str, ...] = (
    "engine",
    "axis",
    "item",
    "entity",
    "entityName",
    "period",
    "value",
    "valueText",
    "lane",
    "status",
    "gapReason",
)
_CANON_SCHEMA: dict[str, Any] = {
    "engine": pl.Utf8,
    "axis": pl.Utf8,
    "item": pl.Utf8,
    "entity": pl.Utf8,
    "entityName": pl.Utf8,
    "period": pl.Utf8,
    "value": pl.Float64,
    "valueText": pl.Utf8,
    "lane": pl.Utf8,
    "status": pl.Utf8,
    "gapReason": pl.Utf8,
}


def reflectAxes() -> pl.DataFrame:
    """축 카탈로그 반사 → (engine, axis, declared[struct]). loadCapabilities 소비, raw 재반사 0.

    Returns:
        pl.DataFrame - engine·axis·summary + declared dict(축 엔트리가 선언한 returnType/listFn/
        stockRequired 등, capability SSOT 가 이미 실은 것). 작업대측 손 축목록 0. 새 축은 다음
        반사에서 자동 등장.

    Example:
        >>> cat = reflectAxes()
        >>> cat.filter(pl.col("axis") == "account")["declared"][0]["listFn"]
        'scanAccountList'

    Raises:
        없음. loadCapabilities 부재 시에도 빈 카탈로그가 아니라 정상 카탈로그를 반환한다.
    """
    from dartlab.reference.capability import loadCapabilities

    rows = [
        {
            "engine": key.split(".", 1)[0],
            "axis": key.split(".", 1)[1],
            "summary": entry.get("summary"),
            "declared": entry.get("declared") or {},
        }
        for key, entry in loadCapabilities().items()
        if isinstance(entry, dict) and str(entry.get("kind", "")).endswith("_axis") and "." in key
    ]
    return pl.DataFrame(rows).sort(["engine", "axis"])


def universeScopeOf(declared: dict) -> str:
    """declared 로 per-company 여부 판정. quant.stockRequired 가 이미 선언한다 (universeScope 발명 불요).

    Args:
        declared: 축 엔트리 선언 dict (stockRequired·multiStock 등).

    Returns:
        "perCompany" (단일 종목 필요 = 벌크 작업대 배제) 또는 "bulk" (전종목 벌크 안전).

    Example:
        >>> universeScopeOf({"stockRequired": True, "multiStock": False})
        'perCompany'

    Raises:
        없음. 빈 dict 는 "bulk" (선언 부재 = 벌크 가정, 실패는 물질화 단계 gap 으로).
    """
    if declared.get("stockRequired") is True and not declared.get("multiStock"):
        return "perCompany"
    return "bulk"


def _entityCol(cols: list[str]) -> str | None:
    return next((c for c in cols if c in ENTITY_KEYS), None)


def _periodCols(cols: list[str]) -> list[str]:
    return [c for c in cols if _PERIOD_RE.match(str(c))]


def classifyShape(raw: Any) -> str:
    """반환 형태 → shape family. 값의 의미를 보지 않고 구조만 본다 (계약 무지).

    Args:
        raw: 엔진 축의 반환 (pl.DataFrame / dict / 스칼라).

    Returns:
        shape family: yearWide·entityMetric·envFrame·envDict·scoreDict·scalar·nested·unclassified.

    Example:
        >>> classifyShape({"scores": {"005930": 7.4}})
        'scoreDict'

    Raises:
        없음. 미지 형태는 예외 대신 "unclassified" 를 반환해 상위가 gap 으로 처리한다.
    """
    if isinstance(raw, bool):
        return "unclassified"
    if isinstance(raw, (int, float, str)):
        return "scalar"
    if isinstance(raw, dict):
        if "scores" in raw and isinstance(raw["scores"], dict):
            return "scoreDict"
        if any(isinstance(v, (dict, list)) for v in raw.values()):
            return "nested"
        return "envDict"
    if isinstance(raw, pl.DataFrame):
        cols = raw.columns
        ent, pers = _entityCol(cols), _periodCols(cols)
        if ent and pers:
            return "yearWide"
        if ent and not pers:
            return "entityMetric"
        if not ent and pers:
            return "envFrame"
        return "unclassified"
    return "unclassified"


def laneOf(family: str, raw: Any, declared: dict | None = None) -> tuple[str, str]:
    """(lane, status). declared(returnType/listFn) 우선. 없으면 morphology + AMBIGUOUS 표면화.

    listFn 보유 DataFrame = 카탈로그 원자(account/ratio/note) = 척추. declared 가 없거나 애매하면
    조용히 확정하지 않고 status 로 드러낸다.

    Args:
        family: classifyShape 산출. raw: 반환 프레임 (entityMetric fallback 시 dtype 검사용).
            declared: 축 엔트리 선언 (returnType·listFn).

    Returns:
        (lane, status). lane: spine·crossSection·env·envScalar·static·quarantine.
        status: declared(선언 근거) · inferred(형태 근거) · ambiguous(확정 보류) · unclassified.

    Example:
        >>> laneOf("yearWide", None, {"returnType": "DataFrame", "listFn": "scanAccountList"})
        ('spine', 'declared')

    Raises:
        없음. 판정 불가는 ("quarantine", "unclassified") 로 표면화한다.
    """
    declared = declared or {}
    rt, lf = declared.get("returnType"), declared.get("listFn")
    if rt == "DataFrame":
        return ("spine" if lf else "crossSection"), "declared"
    inferred = {
        "yearWide": "spine",
        "envFrame": "env",
        "envDict": "env",
        "scoreDict": "crossSection",
        "scalar": "envScalar",
    }
    if family in inferred:
        return inferred[family], "inferred"
    if family == "entityMetric":
        vals = [c for c in raw.columns if c not in ENTITY_KEYS + ENTITY_NAME_KEYS]
        textish = sum(1 for c in vals if raw.schema[c] == pl.Utf8)
        return ("static" if vals and textish > len(vals) / 2 else "crossSection"), "ambiguous"
    return "quarantine", "unclassified"


def emitGap(engine: str, axis: str, reason: str, observed: str) -> dict:
    """갭 1행. 결손을 0 으로 대체하지 않고 원장에 적는다 (조용한 삼킴 금지).

    Args:
        engine: 엔진 이름. axis: 축 이름. reason: gapReason(nonTabular·unknownColumnRole 등).
            observed: 관측된 형태/컬럼 지문 (valueText 에 실림).

    Returns:
        정규 스키마 CANON 을 따르는 gap 행 dict (status="gap", lane="quarantine", value=None).

    Example:
        >>> emitGap("industry", "edges", "nonTabular", "['edges', 'nodes']")["status"]
        'gap'

    Raises:
        없음.
    """
    return {
        "engine": engine,
        "axis": axis,
        "item": None,
        "entity": None,
        "entityName": None,
        "period": None,
        "value": None,
        "valueText": observed,
        "lane": "quarantine",
        "status": "gap",
        "gapReason": reason,
    }


def foldToCanonical(
    raw: Any, *, engine: str, axis: str, item: str | None = None, declared: dict | None = None, asOf: str = "latest"
) -> tuple[pl.DataFrame, list[dict]]:
    """이질 반환 → 단일 정규 롱. shape family 별 어댑터(~6). 접기 분기는 축 수와 무관.

    Args:
        item: 카탈로그 축(account/ratio 등)의 요청 항목. wide 반환은 항목이 열에 없으므로 이 인자가
            없으면 roe 와 debtRatio 가 둘 다 item=axis 로 찍혀 구분 불능이 된다 (2026-07-07 실측 결함).
        declared: 축 엔트리 선언 (lane 판정 입력).

    Returns:
        (canonical long df, gap rows). 접히지 않는 형태(graph/note/nested)는 df 없이 gap 만.

    Example:
        >>> df, gaps = foldToCanonical({"scores": {"005930": 7.4}}, engine="quant", axis="altman")
        >>> df["lane"][0]
        'crossSection'

    Raises:
        없음. 접기 불가(nonTabular)·역할불명 컬럼(unknownColumnRole)·빈 반환(emptyReturn)은 예외
        대신 gap 행으로 방출한다. 비수치 값(None·문자)은 valueText 로 접어 float 크래시를 내지 않는다.
    """
    label = item or axis
    fam = classifyShape(raw)
    lane, status = laneOf(fam, raw, declared)
    gaps: list[dict] = []

    if fam in ("nested", "unclassified"):
        obs = str(sorted(raw.keys()))[:80] if isinstance(raw, dict) else type(raw).__name__
        gaps.append(emitGap(engine, axis, "nonTabular" if fam == "nested" else "unclassifiedShape", obs))
        return pl.DataFrame(schema=_CANON_SCHEMA), gaps

    if fam == "scalar":
        num = isinstance(raw, (int, float)) and not isinstance(raw, bool)
        rows = [
            {
                "item": label,
                "entity": None,
                "entityName": None,
                "period": asOf,
                "value": float(raw) if num else None,
                "valueText": None if num else str(raw),
            }
        ]
    elif fam == "envDict":
        rows = [
            {
                "item": k,
                "entity": None,
                "entityName": None,
                "period": asOf,
                "value": float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None,
                "valueText": None if isinstance(v, (int, float)) and not isinstance(v, bool) else str(v),
            }
            for k, v in raw.items()
        ]
    elif fam == "scoreDict":
        # 점수는 무가드 float 금지: None·비수치(N/A 등)면 valueText 로 (다른 분기와 동일, 크래시 금지)
        rows = []
        for c, v in raw["scores"].items():
            num = isinstance(v, (int, float)) and not isinstance(v, bool)
            rows.append(
                {
                    "item": label,
                    "entity": c,
                    "entityName": None,
                    "period": asOf,
                    "value": float(v) if num else None,
                    "valueText": None if num or v is None else str(v),
                }
            )
    elif fam == "envFrame":
        # entity 없음, period 열 있음(macro 류): 비-period 열 = item 라벨, period 열 -> period.
        # yearWide 로직으로 접으면 period 가 item 으로 새고 period 가 asOf 로 소실되므로 별도 분기.
        cols = raw.columns
        pers = _periodCols(cols)
        labelCols = [c for c in cols if c not in pers]
        long = raw.unpivot(index=labelCols, on=pers, variable_name="_k", value_name="_v")
        rows = []
        for r in long.iter_rows(named=True):
            v = r["_v"]
            num = isinstance(v, (int, float)) and not isinstance(v, bool)
            lbl = " / ".join(str(r[c]) for c in labelCols) if labelCols else label
            rows.append(
                {
                    "item": lbl,
                    "entity": None,
                    "entityName": None,
                    "period": str(r["_k"]),
                    "value": float(v) if num else None,
                    "valueText": None if num or v is None else str(v),
                }
            )
    else:  # yearWide / entityMetric (entity 보유 DataFrame)
        cols = raw.columns
        ent = _entityCol(cols)
        nameCol = next((c for c in cols if c in ENTITY_NAME_KEYS), None)
        pers = _periodCols(cols)
        valueCols = pers if fam == "yearWide" else [c for c in cols if c not in (ent, nameCol)]
        itemIsAxis = fam == "yearWide"
        unknown = [c for c in cols if c not in valueCols and c not in (ent, nameCol)]
        if unknown:
            gaps.append(emitGap(engine, axis, "unknownColumnRole", ",".join(map(str, unknown))[:80]))
        idx = [c for c in (ent, nameCol) if c]
        long = raw.unpivot(index=idx, on=valueCols, variable_name="_k", value_name="_v")
        rows = []
        for r in long.iter_rows(named=True):
            v = r["_v"]
            num = isinstance(v, (int, float)) and not isinstance(v, bool)
            rows.append(
                {
                    "item": label if itemIsAxis else str(r["_k"]),
                    "entity": r.get(ent) if ent else None,
                    "entityName": r.get(nameCol) if nameCol else None,
                    "period": str(r["_k"]) if itemIsAxis else asOf,
                    "value": float(v) if num else None,
                    "valueText": None if num or v is None else str(v),
                }
            )

    if not rows and not gaps:  # 빈 반환(envDict={}·scoreDict{scores:{}}·빈 프레임)도 gap 으로 계상 (도태 사각 방지)
        gaps.append(emitGap(engine, axis, "emptyReturn", fam))

    partial = {
        k: v for k, v in _CANON_SCHEMA.items() if k in ("item", "entity", "entityName", "period", "value", "valueText")
    }
    df = (
        pl.DataFrame(rows, schema=partial)
        .with_columns(
            engine=pl.lit(engine, dtype=pl.Utf8),
            axis=pl.lit(axis, dtype=pl.Utf8),
            lane=pl.lit(lane, dtype=pl.Utf8),
            status=pl.lit(status, dtype=pl.Utf8),
            gapReason=pl.lit(None, dtype=pl.Utf8),
        )
        .select(CANON)
    )
    return df, gaps
