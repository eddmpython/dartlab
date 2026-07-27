"""Unified Data Workbench 팩터 투영 순수 커널.

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
    - tests/dataHub/test_factor_kernel.py (7 shape 접기 + gap 방출)

Layer: L2.5 dataHub. capability metadata와 polars만 소비하는 순수 투영 커널.
"""

from __future__ import annotations

import re
from typing import Any

import polars as pl

# entity/period 구조 동의어 = 전 축 entity 키 식별의 정본. O(시장 spelling) 상수지 O(축) 아님.
ENTITY_KEYS: tuple[str, ...] = ("종목코드", "stockCode", "code", "ticker")
ENTITY_NAME_KEYS: tuple[str, ...] = ("종목명", "corpName", "name")
# 달력 연도(19xx/20xx) + 선택 분기(Q1~4) 또는 월(01~12). ASCII 숫자만(전각 배제). 종목코드(005930)·
# 계정코드(1000)·무효월(202599)을 period 로 오탐하지 않게 조인다. \Z (파이썬 $ 는 끝개행 앞도 매칭).
_PERIOD_RE = re.compile(r"^(19|20)\d{2}(Q[1-4]|(0[1-9]|1[0-2]))?\Z", re.ASCII)

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


def emptyCanonical() -> pl.DataFrame:
    """빈 정규 롱 (CANON 11열, 올바른 dtype). 성패와 무관하게 스키마 불변식을 지키는 표준 빈 프레임.

    Returns:
        0행 x CANON 스키마 DataFrame. 전 축 실패 등 결과가 없을 때도 이걸 반환해야 소비자가 value/lane
        열을 안전히 참조하고 성공분과 concat 할 수 있다.

    Example:
        >>> list(emptyCanonical().columns) == list(CANON)
        True

    Raises:
        없음.
    """
    return pl.DataFrame(schema=_CANON_SCHEMA)


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
            "declared": dict(entry.get("declared") or {}),
        }
        for key, entry in loadCapabilities().items()
        if isinstance(entry, dict) and str(entry.get("kind", "")).endswith("_axis") and "." in key
    ]
    if not rows:
        return pl.DataFrame(schema={"engine": pl.Utf8, "axis": pl.Utf8, "summary": pl.Utf8, "declared": pl.Object})
    declared = pl.Series("declared", [row.pop("declared") for row in rows], dtype=pl.Object)
    return pl.DataFrame(rows).with_columns(declared).sort(["engine", "axis"])


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


def _isNumericDtype(dt: Any) -> bool:
    """수치 컬럼 판정 (Boolean 제외). polars unpivot 후가 아니라 원본 dtype 로 판정해야 정확."""
    try:
        return bool(dt.is_numeric()) and dt != pl.Boolean
    except AttributeError:
        return dt in (pl.Float64, pl.Float32, pl.Int64, pl.Int32, pl.Int16, pl.Int8, pl.UInt64, pl.UInt32)


def _foldFrameRows(raw: pl.DataFrame, idx: list[str], valueCols: list[str], rowFn) -> list[dict]:
    """value 열을 dtype 로 분리 unpivot 해 rows 생성. 혼합 dtype String 승격의 숫자 소실 방지.

    polars unpivot 은 on 열들을 공통 상위형으로 승격한다. 숫자+문자 혼합 프레임을 한 번에 unpivot 하면
    Float64 가 String 이 돼 숫자가 valueText 로 강등된다(2026-07-11 실측: scan.profitability 272K 값
    소실). 숫자군·문자군을 나눠 각각 unpivot 해 dtype 를 보존한다. rowFn(r) 는 item/entity/entityName/
    period 를 담은 base dict 를 반환한다 (value/valueText 는 여기서 채운다).
    """
    numCols = [c for c in valueCols if _isNumericDtype(raw.schema[c])]
    txtCols = [c for c in valueCols if c not in numCols]
    rows: list[dict] = []
    for group, isNum in ((numCols, True), (txtCols, False)):
        if not group:
            continue
        for r in raw.unpivot(index=idx, on=group, variable_name="_k", value_name="_v").iter_rows(named=True):
            v = r["_v"]
            base = rowFn(r)
            base["value"] = float(v) if isNum and v is not None else None
            base["valueText"] = None if isNum or v is None else str(v)
            rows.append(base)
    return rows


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


def _numericSplit(value: Any) -> tuple[float | None, str | None]:
    """값을 (수치, 문자) 로 가른다. 무가드 float 은 금지다.

    None 이나 "N/A" 같은 값에 그대로 float 을 씌우면 접기 전체가 죽는다. 수치가 아니면
    valueText 로 남겨 무엇이 들어왔는지 보이게 한다.
    """
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value), None
    return None, str(value)


def _foldScalar(raw: Any, *, label: str, asOf: str) -> list[dict]:
    """단일 값을 한 행으로."""
    value, text = _numericSplit(raw)
    return [{"item": label, "entity": None, "entityName": None, "period": asOf, "value": value, "valueText": text}]


def _foldEnvDict(raw: dict, *, asOf: str) -> list[dict]:
    """지표 이름이 키인 dict. 키가 곧 item 이라 label 을 쓰지 않는다."""
    rows = []
    for key, value in raw.items():
        numeric, text = _numericSplit(value)
        rows.append(
            {"item": key, "entity": None, "entityName": None, "period": asOf, "value": numeric, "valueText": text}
        )
    return rows


def _foldScoreDict(raw: dict, *, label: str, asOf: str) -> list[dict]:
    """종목별 점수 dict. None 은 valueText 도 비워 둔다. 값이 없는 것과 문자인 것은 다르다."""
    rows = []
    for entity, value in raw["scores"].items():
        numeric, text = _numericSplit(value)
        rows.append(
            {
                "item": label,
                "entity": entity,
                "entityName": None,
                "period": asOf,
                "value": numeric,
                "valueText": None if value is None else text,
            }
        )
    return rows


def _foldEnvFrame(raw: pl.DataFrame, *, label: str) -> list[dict]:
    """entity 가 없고 기간 열이 있는 표(macro 류).

    yearWide 로직으로 접으면 기간이 item 으로 새고 period 가 asOf 로 소실되므로 따로 둔다.
    """
    pers = _periodCols(raw.columns)
    labelCols = [c for c in raw.columns if c not in pers]
    return _foldFrameRows(
        raw,
        labelCols,
        pers,
        lambda r: {
            "item": " / ".join(str(r[c]) for c in labelCols) if labelCols else label,
            "entity": None,
            "entityName": None,
            "period": str(r["_k"]),
        },
    )


def _foldEntityFrame(
    raw: pl.DataFrame, *, fam: str, label: str, asOf: str, engine: str, axis: str, gaps: list[dict]
) -> list[dict]:
    """entity 를 가진 표. yearWide 는 기간이 열이고 entityMetric 은 지표가 열이다.

    역할을 못 정한 열은 조용히 버리지 않고 gap 으로 적는다. 버리면 그 열이 원래 없었는지
    해석에 실패했는지 결과만 봐서는 알 수 없다.
    """
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
    return _foldFrameRows(
        raw,
        idx,
        valueCols,
        lambda r: {
            "item": label if itemIsAxis else str(r["_k"]),
            "entity": r.get(ent) if ent else None,
            "entityName": r.get(nameCol) if nameCol else None,
            "period": str(r["_k"]) if itemIsAxis else asOf,
        },
    )


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
        obs = str(sorted(map(str, raw.keys())))[:80] if isinstance(raw, dict) else type(raw).__name__
        gaps.append(emitGap(engine, axis, "nonTabular" if fam == "nested" else "unclassifiedShape", obs))
        return emptyCanonical(), gaps

    if fam == "scalar":
        rows = _foldScalar(raw, label=label, asOf=asOf)
    elif fam == "envDict":
        rows = _foldEnvDict(raw, asOf=asOf)
    elif fam == "scoreDict":
        rows = _foldScoreDict(raw, label=label, asOf=asOf)
    elif fam == "envFrame":
        rows = _foldEnvFrame(raw, label=label)
    else:  # yearWide / entityMetric (entity 보유 DataFrame)
        rows = _foldEntityFrame(raw, fam=fam, label=label, asOf=asOf, engine=engine, axis=axis, gaps=gaps)

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
