"""scan 필드 카탈로그와 조건형 스크리닝 실행기.

`scan("fields")` 는 AI와 사용자가 먼저 검색할 수 있는 필드 목록을 제공한다.
`scan("screen", spec=...)` 는 같은 카탈로그의 field 키를 조건으로 받아 후보
종목을 좁힌다. 공개 진입점은 계속 `dartlab.scan()` 하나다.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import polars as pl

from dartlab.scan.builders.kr.report.fieldCatalog import _COMPOSITE_AXIS_FIELDS as _COMPOSITE_AXIS_FIELDS
from dartlab.scan.builders.kr.report.fieldCatalog import _KRX_FIELDS as _KRX_FIELDS
from dartlab.scan.builders.kr.report.fieldCatalog import _NUMERIC_OPS as _NUMERIC_OPS
from dartlab.scan.builders.kr.report.fieldCatalog import _catalog as _catalog


def scanFields(query: str | None = None, source: str | None = None) -> pl.DataFrame:
    """scan 스크리닝에 사용할 수 있는 필드 카탈로그를 반환한다.

    Summary
    -------
    `finance`, `report`, `docs`, `krx`, `krxIndex` 필드를 한 표에서 검색한다.

    Description
    -----------
    이 함수는 데이터를 전부 합치지 않는다. 각 원천의 필드 이름, 단위, 허용
    연산자, 커버리지, 실행 예시를 먼저 보여주고, 실제 후보 추출은
    `scan("screen", spec=...)` 가 필요한 필드만 로드한다.

    Parameters
    ----------
    query : str | None
        field, label, notes 에서 찾을 검색어. 예: ``"roe"``, ``"매출"``,
        ``"감사의견"``, ``"rsi"``.
    source : str | None
        원천 필터. ``"finance"``, ``"report"``, ``"docs"``, ``"krx"``,
        ``"krxIndex"``, ``"valuation"`` 중 하나.

    Returns
    -------
    pl.DataFrame
        field : str - `screen` spec 에 넣는 정규 필드 키 (단위 없음).
        label : str - 사람용 한글/영문 라벨 (단위 없음).
        source : str - 데이터 원천 이름 (단위 없음).
        kind : str - ``"number"``, ``"text"``, ``"boolean"``, ``"context"``.
        unit : str - 비교 단위. 원/%/배/건/일/점/주/텍스트/없음.
        operatorSet : str - 허용 연산자 목록.
        coverage : str - 로컬 prebuild 기준 관측 범위 또는 설명.
        example : str - `scan("screen", spec=...)` 에 넣을 조건 예시.
        notes : str - 해석·성능·제약 설명.

    Raises
    ------
    ValueError
        source 값이 카탈로그에 없는 경우.

    Examples
    --------
    >>> dartlab.scan("fields")
    >>> dartlab.scan("fields", "roe")
    >>> dartlab.scan("fields", source="krx")

    Notes
    -----
    report 카탈로그는 메모리 안전을 위해 schema 기준으로 생성한다. non-null
    전수 coverage 계산은 report parquet 전체를 materialize 할 수 있어 기본 경로에서
    수행하지 않는다.

    Guide
    -----
    When: 종목을 찾기 전 어떤 데이터 필드가 있는지 먼저 확인할 때.
    How: fields 로 후보 필드를 찾고, 최소 3개 이상의 서로 다른 관점 조건을
    screen spec 으로 조합한 뒤, 남은 종목만 Company/analysis 로 심층 확인한다.
    Verified: finance/report/docs/krx/krxIndex source 가 단일 표로 노출된다.

    Capabilities:
        - 5 원천 (finance / report / docs / krx / krxIndex / valuation) 의 가용 필드를 한 표로
          노출. 각 필드의 단위·연산자·coverage·example·notes 메타로 spec 작성을 가이드.
        - 데이터 자체는 로드 안 함 - 카탈로그 검색만. 실제 scan 은 `scan("screen", spec=...)`.

    AIContext:
        Agent 가 사용자 의도 ("저PBR 종목" / "ROE 높은 회사") 를 받으면, 직접 raw 컬럼 추정
        대신 본 함수로 spec 에 들어갈 정규 필드 키 (`finance.ratio.roe` 등) 를 먼저 확인.
        잘못된 필드명 추정으로 인한 ValueError 회피.

    Requires:
        - 메모리에 보유한 카탈로그 dict (`_catalog()` 산출). 외부 의존 없음.

    See Also
    --------
    dartlab.scan : scan 단일 진입점.
    dartlab.scan("screen") : 조건형 스크리닝 실행.
    dartlab.search : docs 텍스트 조건의 검색 인덱스 기반 후보 생성.
    """
    df = _catalog()
    if source is not None:
        valid = set(df["source"].to_list())
        if source not in valid:
            raise ValueError(f"source는 {sorted(valid)} 중 하나. 받은 값: {source!r}")
        df = df.filter(pl.col("source") == source)
    if query is not None:
        q = str(query).strip().lower()
        if q:
            df = df.filter(
                pl.any_horizontal(
                    pl.col("field").str.to_lowercase().str.contains(q, literal=True),
                    pl.col("label").str.to_lowercase().str.contains(q, literal=True),
                    pl.col("notes").str.to_lowercase().str.contains(q, literal=True),
                )
            )
    return df


def executeScreenSpec(spec: dict[str, Any]) -> pl.DataFrame:
    """조건 spec 을 실행해 후보 종목 DataFrame 을 반환한다.

    Summary
    -------
    `where` 조건은 AND, `any` 조건은 OR 후보군으로 계산한다.

    Description
    -----------
    필드별 resolver 는 필요한 원천만 lazy 로 로드한다. finance/ratio/valuation/krx
    조건은 종목별 최신 값을 계산해 비교하고, report 조건은 구조화 공시 parquet 을
    필터하며, docs 조건은 검색 인덱스 hit 를 종목 단위로 요약한다.

    Parameters
    ----------
    spec : dict
        ``where``, ``any``, ``select``, ``sort``, ``limit`` 키를 가진 스크리닝
        명세. 최소 조건 형태는
        ``{"where": [{"field": "finance.ratio.roe", "op": ">", "value": 10}]}``.

    Returns
    -------
    pl.DataFrame
        stockCode : str - 후보 종목코드.
        <field> : object - where/select/sort 에서 요청한 필드 값 (필드별 단위).
        docsHitCount : int - docs 조건 hit 수 (건), docs 조건이 있을 때.
        docsBestScore : float - docs 검색 최고 점수 (점), docs 조건이 있을 때.
        docsSnippet : str - 대표 공시 snippet (텍스트), docs 조건이 있을 때.
        dartUrl : str - 대표 DART 링크 (텍스트), docs 조건이 있을 때.

    Raises
    ------
    ValueError
        spec 형식, field, op, unit 이 잘못된 경우.

    Examples
    --------
    >>> dartlab.scan("screen", spec={
    ...     "where": [
    ...         {"field": "finance.ratio.roe", "op": ">", "value": 10},
    ...         {"field": "valuation.pbr", "op": "<", "value": 1},
    ...     ],
    ...     "select": ["krx.marketCap"],
    ...     "sort": {"field": "finance.ratio.roe", "desc": True},
    ...     "limit": 30,
    ... })

    Notes
    -----
    docs 조건은 검색 인덱스 기반 후보 생성이다. 원문 전체에 대한 완전한
    boolean scan 으로 해석하지 않는다.

    Guide
    -----
    When: 넓은 시장에서 후보군을 줄일 때.
    How: 가치·성장·품질·가격·공시 중 최소 3축을 조합하고, 결과 종목은
    Company/analysis 로 원문과 재무제표를 재검증한다.
    Verified: 기존 preset 호출과 독립적으로 spec 경로만 실행된다.

    Capabilities:
        - spec 의 ``where`` (AND) / ``any`` (OR) / ``select`` / ``sort`` / ``limit`` 을 해석해
          필요한 원천만 lazy 로 로드 후 후보 종목 DataFrame 반환. finance/ratio/valuation/krx/
          report/docs 필드를 동일 spec 안에서 자유 조합.
        - 필드별 resolver 가 단위·연산자 검증 - 잘못된 spec 은 즉시 ValueError.

    AIContext:
        Agent 가 ``dartlab.scan("screen", spec={...})`` 호출 시 본 함수가 router 진입점.
        AI 가 spec 을 직접 만들 때 ``scanFields`` 로 필드 가용성 + 단위·연산자를 먼저 확인하면
        ValueError 회피.

    Requires:
        - 필요시 lazy 로드: scan/finance.parquet (finance/ratio), scan/report/{apiType}.parquet,
          docs 검색 인덱스 (`dartlab.search`), valuation.parquet, krx listing.
        - 외부 호출 없음 - 모든 데이터 로컬 prebuild 자산.

    See Also
    --------
    scanFields : 사용 가능한 필드 검색.
    dartlab.search : docs 조건 후보 생성.
    """
    return _executeScreenSpec(spec, applyLimit=True)


def _executeScreenSpec(spec: dict[str, Any], *, applyLimit: bool) -> pl.DataFrame:
    """screen spec을 실행하고 필요할 때만 반환 행 제한을 적용한다.

    공개 경로는 항상 ``applyLimit=True``다. 설명 경로는 같은 실행 결과 전체에서
    실제 멤버 수를 센 뒤 공개 ``limit``만큼만 payload에 싣는다.
    """
    _validateScreenScope(spec)

    where = _ensureConditionList(spec.get("where", []), key="where")
    any_conditions = _ensureConditionList(spec.get("any", []), key="any")
    select = _ensureStrList(spec.get("select", []), key="select")
    sort = spec.get("sort")
    limit = int(spec.get("limit", 50))
    if limit <= 0:
        raise ValueError("limit 은 1 이상이어야 합니다.")

    # 복합축 캐시(축 스캐너 1회 재사용) + 파생 필드(spec.define) 위상순 계산 후 spec 사본에 stash.
    # where/select/sort 가 @name(파생)·axis.*(복합축) 참조.
    spec = {**spec, "_axisCache": {}}
    derivedValues, derivedUnits = _computeDerived(spec)
    if derivedValues:
        spec["_derivedValues"] = derivedValues
        spec["_derivedUnits"] = derivedUnits

    frames: list[pl.DataFrame] = []
    for cond in where:
        frames.append(_conditionFrame(cond, spec))

    if any_conditions:
        any_frames = [_conditionFrame(cond, spec) for cond in any_conditions]
        any_frames = [f for f in any_frames if not f.is_empty()]
        if any_frames:
            frames.append(_unionOnStock(any_frames))
        else:
            return pl.DataFrame({"stockCode": []})

    result = _innerJoinOnStock(frames)

    requested = list(dict.fromkeys(select))
    if sort:
        if not isinstance(sort, dict) or "field" not in sort:
            raise ValueError('sort 는 {"field": "...", "desc": true} 형태여야 합니다.')
        requested.append(str(sort["field"]))

    if result.is_empty() and not frames and requested:
        first = requested[0]
        result = _loadFieldValues(first, spec)
        requested = requested[1:]

    for field in requested:
        if _isContextField(field):
            continue
        if field in result.columns:
            continue
        values = _loadFieldValues(field, spec)
        result = (
            values
            if result.is_empty() and "stockCode" not in result.columns
            else result.join(values, on="stockCode", how="left")
        )

    if result.is_empty() and not frames:
        result = pl.DataFrame({"stockCode": []})

    result = _attachContextFields(result, select + ([str(sort["field"])] if sort else []), spec)

    if sort:
        sort_field = str(sort["field"])
        if sort_field in result.columns:
            result = result.sort(sort_field, descending=bool(sort.get("desc", False)), nulls_last=True)

    return result.head(limit) if applyLimit else result


def executeScreenSpecDetailed(spec: dict[str, Any]) -> dict[str, Any]:
    """같은 screen spec을 실행하고 판정 근거와 제외 이유를 함께 반환한다.

    기존 ``executeScreenSpec``의 멤버 테이블을 정본으로 유지한다. 설명 경로는
    동일 필드 로더로 전체 상장 유니버스의 PASS/FAIL/UNKNOWN을 평가해
    coverage, funnel, near miss를 더한다. explain opt-in에서만 실행되므로
    기존 DataFrame 반환과 실행 시간은 바뀌지 않는다.
    """
    from datetime import datetime, timezone

    from dartlab.scan.screen.verdict import summarizeVerdicts

    _validateScreenScope(spec)
    allMembers = _executeScreenSpec(spec, applyLimit=False)
    limit = int(spec.get("limit", 50))
    members = allMembers.head(limit)
    workSpec = {**spec, "_axisCache": {}}
    derivedValues, derivedUnits = _computeDerived(workSpec)
    if derivedValues:
        workSpec["_derivedValues"] = derivedValues
        workSpec["_derivedUnits"] = derivedUnits

    where = _ensureConditionList(spec.get("where", []), key="where")
    anyConditions = _ensureConditionList(spec.get("any", []), key="any")
    normalizedWhere: list[dict[str, Any]] = []
    normalizedAny: list[dict[str, Any]] = []
    framesByField: dict[str, pl.DataFrame] = {}
    kinds: dict[str, str] = {}

    for sourceConditions, targetConditions in ((where, normalizedWhere), (anyConditions, normalizedAny)):
        for cond in sourceConditions:
            field = _normalizeField(str(cond.get("field", "")))
            meta = _fieldMeta(field, workSpec)
            publicCondition = {**cond, "field": field}
            if field.startswith("docs."):
                values = _docsConditionValues(cond, workSpec)
                framesByField[field] = (
                    values.select("stockCode", pl.lit(True).alias(field))
                    if values is not None and not values.is_empty()
                    else pl.DataFrame({"stockCode": [], field: []})
                )
                kinds[field] = "boolean"
                publicCondition = {"field": field, "op": "==", "value": True, "query": cond.get("value")}
            else:
                framesByField.setdefault(field, _loadFieldValues(field, workSpec))
                kinds[field] = str(meta["kind"])
            targetConditions.append(publicCondition)

    conditions: list[Mapping[str, Any]] = normalizedWhere.copy()
    if normalizedAny:
        conditions.append({"field": "__any__", "op": "any", "alternatives": normalizedAny})

    universe = _screenUniverse()
    for field, frame in framesByField.items():
        if frame is None or frame.is_empty() or "stockCode" not in frame.columns or field not in frame.columns:
            continue
        universe = universe.join(frame.select("stockCode", field), on="stockCode", how="left")
        if field.startswith("docs."):
            universe = universe.with_columns(pl.col(field).fill_null(False).alias(field))

    rawRows = universe.to_dicts()
    summary = summarizeVerdicts(rawRows, conditions, kinds=kinds)
    nearMissCodes = set(summary.pop("nearMissCodes", []))
    byCode = {str(row.get("stockCode") or ""): row for row in rawRows}
    memberCodes = _stockCodes(allMembers)
    summary["memberCodes"] = memberCodes
    summary["memberCount"] = len(memberCodes)

    datasetAsOf = None
    gaps = []
    if datasetAsOf is None:
        gaps.append(
            {
                "code": "datasetAsOfUnavailable",
                "message": "spec에 asOf가 없어 각 prebuild 원천의 최신 스냅샷을 사용했습니다.",
            }
        )
    return {
        "schemaVersion": 1,
        "status": "partial" if gaps else "usable",
        "screen": {
            "id": spec.get("id"),
            "spec": _publicSpec(spec),
            "formula": {"all": where, "any": anyConditions, "missingPolicy": "UNKNOWN excluded"},
        },
        "universe": {
            "market": str(spec.get("market") or "KR").upper(),
            "source": "dartlab.listing",
            "count": summary["universe"],
        },
        "datasetAsOf": datasetAsOf,
        "executedAt": datetime.now(timezone.utc).date().isoformat(),
        "members": members.to_dicts(),
        "memberCount": allMembers.height,
        "returnedMemberCount": members.height,
        "membersTruncated": members.height < allMembers.height,
        "coverage": summary["coverage"],
        "funnel": summary["funnel"],
        "excluded": summary["excluded"],
        "nearMiss": [byCode[code] for code in nearMissCodes if code in byCode][:50],
        "gaps": gaps,
        "executionRef": {
            "engine": "scan",
            "axis": "screen",
            "specVersion": spec.get("schemaVersion", 1),
        },
    }


# screen spec 이 실제로 해석하는 최상위 키다. 이 목록 밖의 키는 조용히 무시되는 대신
# 즉시 거절된다. `_` 로 시작하는 키는 실행 중 붙이는 내부 캐시라 예외로 둔다.
_SCREEN_SPEC_KEYS = frozenset(
    {
        "where",
        "any",
        "select",
        "sort",
        "limit",
        "define",
        "id",
        "market",
        "asOf",
        "explain",
        "schemaVersion",
        "docsTopK",
        "start",
        "end",
        "windowDays",
        "indexName",
    }
)
_SCREEN_CONDITION_KEYS = ("where", "any", "select")


def _validateScreenScope(spec: dict[str, Any]) -> None:
    """현재 screen이 실제로 지키는 시장, 시점, spec 키 계약만 허용한다.

    옛 경로는 해석하지 않는 최상위 키를 조용히 버렸다. 그래서 조건을 ``all`` 이나
    ``filters`` 처럼 다르게 적은 spec 이 오류 대신 "0 종목" 으로 돌아왔고, 호출자는
    스크리닝 자체가 쓸모없다고 읽고 종목마다 개별 조회로 흩어졌다. 조건을 못 읽었으면
    빈 결과가 아니라 못 읽었다고 말해야 한다.
    """
    if not isinstance(spec, dict):
        raise ValueError("screen spec 은 dict 여야 합니다.")
    unknown = sorted(
        key for key in spec if isinstance(key, str) and not key.startswith("_") and key not in _SCREEN_SPEC_KEYS
    )
    if unknown:
        raise ValueError(
            f"screen spec 에 해석할 수 없는 키가 있습니다: {unknown}. "
            f"사용 가능한 키: {sorted(_SCREEN_SPEC_KEYS)}. "
            '조건은 where 에 넣습니다. 예: {"where": [{"field": "finance.ratio.roe", "op": ">=", "value": 15}]}'
        )
    market = str(spec.get("market") or "KR").strip().upper()
    if market not in {"KR", "DART"}:
        raise ValueError("screen spec은 현재 KR 시장만 지원합니다. US 결과를 KR 데이터로 대체하지 않습니다.")
    if spec.get("asOf") is not None:
        raise ValueError(
            "screen spec의 asOf 시점 고정은 아직 지원하지 않습니다. "
            "최신 prebuild를 사용하거나 시점 보존 데이터 경로를 먼저 제공하세요."
        )
    # 조건 부재는 가장 약한 신호라 맨 뒤에서 본다. 앞의 검사들이 더 구체적인 원인을 짚는다.
    if not any(spec.get(key) for key in _SCREEN_CONDITION_KEYS):
        raise ValueError(
            "screen spec 에 조건이 없습니다. where(AND), any(OR), select 중 최소 하나를 채우세요. "
            'dartlab.scan("fields", "키워드") 로 field 이름을 먼저 확인하면 됩니다.'
        )


def _screenUniverse() -> pl.DataFrame:
    """KR 상장 유니버스를 ``stockCode`` 단일 컬럼으로 반환한다."""
    from dartlab import listing

    raw = listing()
    if raw is None or raw.is_empty():
        return pl.DataFrame({"stockCode": []}, schema={"stockCode": pl.Utf8})
    stockColumn = next((column for column in ("stockCode", "종목코드", "stock_code") if column in raw.columns), None)
    if stockColumn is None:
        return pl.DataFrame({"stockCode": []}, schema={"stockCode": pl.Utf8})
    return raw.select(pl.col(stockColumn).cast(pl.Utf8).alias("stockCode")).drop_nulls().unique()


def _stockCodes(frame: pl.DataFrame) -> list[str]:
    if frame is None or frame.is_empty():
        return []
    column = next((name for name in ("stockCode", "종목코드") if name in frame.columns), None)
    return [str(value) for value in frame[column].to_list()] if column else []


def _publicSpec(spec: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in spec.items() if not str(key).startswith("_") and key != "explain"}


def _ensureConditionList(value: Any, *, key: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{key} 는 condition dict 리스트여야 합니다.")
    for cond in value:
        if not isinstance(cond, dict):
            raise ValueError(f"{key} 의 각 항목은 dict 여야 합니다.")
    return value


def _ensureStrList(value: Any, *, key: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{key} 는 문자열 리스트여야 합니다.")
    return [str(v) for v in value]


def _conditionFrame(cond: dict[str, Any], spec: dict[str, Any]) -> pl.DataFrame:
    field = _normalizeField(str(cond.get("field", "")))
    meta = _fieldMeta(field, spec)
    if meta["kind"] == "context":
        raise ValueError(
            f"{field!r} 는 시장 컨텍스트 필드라 종목 필터 조건으로 사용할 수 없습니다. select 에 넣으세요."
        )
    if "unit" in cond and str(cond["unit"]) != meta["unit"]:
        raise ValueError(f"{field!r} 단위는 {meta['unit']} 입니다. 받은 unit={cond['unit']!r}")
    if field.startswith("docs."):
        return _docsConditionValues(cond, spec)
    values = _loadFieldValues(field, spec)
    return _applyCondition(values, field, cond, meta)


def _normalizeField(field: str) -> str:
    f = field.strip()
    if not f:
        raise ValueError("condition field 가 비어 있습니다.")
    aliases = {
        "roe": "finance.ratio.roe",
        "roa": "finance.ratio.roa",
        "pbr": "valuation.pbr",
        "per": "valuation.per",
        "psr": "valuation.psr",
        "marketCap": "krx.marketCap",
        "시가총액": "krx.marketCap",
        "매출액": "finance.account.sales",
    }
    return aliases.get(f, f)


def _fieldMeta(field: str, spec: dict[str, Any] | None = None) -> dict[str, str]:
    if field.startswith("@"):
        name = field[1:]
        units = (spec or {}).get("_derivedUnits") or {}
        if name not in units:
            raise ValueError(f"미정의 파생 필드 {field!r}. spec.define 에 선언하세요.")
        return {
            "field": field,
            "label": field,
            "source": "derived",
            "kind": "number",
            "unit": units[name],
            "operatorSet": _NUMERIC_OPS,
            "coverage": "derived",
            "example": "",
            "notes": "spec.define 파생 필드",
        }
    catalog = _catalog()
    # note.<concept>@<항목명> 은 개념(note.<concept>) 메타로 해소 (항목은 값 로더가 처리).
    lookup = field.split("@", 1)[0] if field.startswith("note.") and "@" in field else field
    hit = catalog.filter(pl.col("field") == lookup)
    if hit.is_empty():
        examples = ", ".join(catalog["field"].head(8).to_list())
        raise ValueError(f"알 수 없는 scan field: {field!r}. dartlab.scan('fields') 로 확인하세요. 예: {examples}")
    meta = dict(hit.row(0, named=True))
    meta["field"] = field
    return meta


def _loadFieldValues(field: str, spec: dict[str, Any]) -> pl.DataFrame:
    field = _normalizeField(field)
    if field.startswith("@"):
        values = (spec or {}).get("_derivedValues") or {}
        name = field[1:]
        if name not in values:
            raise ValueError(f"미해소 파생 필드 {field!r} (spec.define 확인).")
        return values[name]
    if field.startswith("note."):
        _fieldMeta(field, spec)
        return _loadNote(field)
    if field.startswith("axis."):
        _fieldMeta(field, spec)
        return _loadCompositeAxis(field, spec)
    _fieldMeta(field, spec)
    if field.startswith("finance.account."):
        return _loadFinanceAccount(field)
    if field.startswith("finance.ratio."):
        return _loadFinanceRatio(field)
    if field.startswith("valuation."):
        return _loadValuation(field)
    if field.startswith("report."):
        return _loadReport(field)
    if field.startswith("docs."):
        raise ValueError("docs 필드는 where 조건의 value 로 검색어를 지정해야 합니다.")
    if field.startswith("krx."):
        return _loadKrx(field, spec)
    if field.startswith("krxIndex."):
        raise ValueError("krxIndex 필드는 select 전용 시장 컨텍스트입니다.")
    raise ValueError(f"지원하지 않는 field source: {field!r}")


def _loadFinanceAccount(field: str) -> pl.DataFrame:
    from dartlab.providers.dart.finance.scanAccount import scanAccount

    name = field.split(".", 2)[2]
    df = scanAccount(name)
    return _latestWideValue(df, field)


def _loadFinanceRatio(field: str) -> pl.DataFrame:
    from dartlab.providers.dart.finance.scanAccount import scanRatio

    name = field.split(".", 2)[2]
    df = scanRatio(name)
    return _latestWideValue(df, field)


def _latestWideValue(df: pl.DataFrame, field: str) -> pl.DataFrame:
    if df is None or df.is_empty() or "stockCode" not in df.columns:
        return pl.DataFrame({"stockCode": [], field: []})
    period_cols = sorted([c for c in df.columns if c != "stockCode"], reverse=True)
    if not period_cols:
        return pl.DataFrame({"stockCode": [], field: []})
    return df.select("stockCode", pl.coalesce([pl.col(c) for c in period_cols]).alias(field))


def _loadValuation(field: str) -> pl.DataFrame:
    name = field.split(".", 1)[1]
    if name != "psr":
        from dartlab.scan.io.parquet import loadValuationSnapshot

        raw, _snapshot_at = loadValuationSnapshot()
        if raw is not None and not raw.is_empty() and name in raw.columns:
            return raw.select("stockCode", pl.col(name).alias(field))

    from dartlab.scan.financial.valuation import scanValuation

    df = scanValuation(verbose=False)
    if df is None or df.is_empty() or name not in df.columns:
        return pl.DataFrame({"stockCode": [], field: []})
    return df.select("stockCode", pl.col(name).alias(field))


def _loadReport(field: str) -> pl.DataFrame:
    from dartlab.scan.io.parquet import scanParquets

    _, apiType, col = field.split(".", 2)
    if col == "__exists__":
        raw = _loadReportExists(apiType)
        if raw.is_empty():
            return pl.DataFrame({"stockCode": [], field: []})
        return raw.select("stockCode").unique().with_columns(pl.lit(True).alias(field))

    raw = scanParquets(apiType, ["stockCode", "year", "quarter", col])
    if raw.is_empty() or col not in raw.columns or "stockCode" not in raw.columns:
        return pl.DataFrame({"stockCode": [], field: []})
    raw = _latestByStock(raw)
    return raw.select("stockCode", pl.col(col).alias(field))


def _loadReportExists(apiType: str) -> pl.DataFrame:
    from dartlab.core.dataLoader import _dataDir
    from dartlab.scan.io.parquet import _ensureScanData

    scan_path = _ensureScanData() / "report" / f"{apiType}.parquet"
    if scan_path.exists():
        try:
            return pl.scan_parquet(str(scan_path)).select("stockCode").collect(engine="streaming")
        except (OSError, pl.exceptions.PolarsError):
            return pl.DataFrame()

    report_dir = Path(_dataDir("report"))
    frames = []
    for pf in sorted(report_dir.glob("*.parquet")):
        try:
            lf = pl.scan_parquet(str(pf))
            if "apiType" not in lf.collect_schema().names():
                continue
            frames.append(lf.filter(pl.col("apiType") == apiType).select("stockCode"))
        except (OSError, pl.exceptions.PolarsError):
            continue
    if not frames:
        return pl.DataFrame()
    return pl.concat(frames).collect(engine="streaming")


def _latestByStock(df: pl.DataFrame) -> pl.DataFrame:
    sort_cols = [c for c in ("stockCode", "year", "quarter") if c in df.columns]
    if "stockCode" not in sort_cols:
        return df
    return df.sort(sort_cols).group_by("stockCode").tail(1)


def _docsConditionValues(cond: dict[str, Any], spec: dict[str, Any]) -> pl.DataFrame:
    field = _normalizeField(str(cond.get("field", "")))
    op = str(cond.get("op", "contains"))
    if op not in {"contains", "=="}:
        raise ValueError("docs 조건은 contains 또는 == 만 지원합니다.")
    query = str(cond.get("value", "")).strip()
    if not query:
        raise ValueError("docs 조건 value 에 검색어가 필요합니다.")
    scope = "content" if field == "docs.content" else "title"
    top_k = int(cond.get("limit", spec.get("docsTopK", 500)))

    from dartlab.providers.dart.search import search

    hits = search(query, limit=top_k, scope=scope)
    if hits is None or hits.is_empty() or "info" in hits.columns:
        return pl.DataFrame({"stockCode": [], field: []})
    sc_col = "stock_code" if "stock_code" in hits.columns else "stockCode" if "stockCode" in hits.columns else None
    if sc_col is None:
        return pl.DataFrame({"stockCode": [], field: []})
    text_col = "text" if "text" in hits.columns else "section_title" if "section_title" in hits.columns else sc_col
    score_expr = (
        pl.col("score").max().alias("docsBestScore") if "score" in hits.columns else pl.lit(None).alias("docsBestScore")
    )
    url_expr = (
        pl.col("dartUrl").first().alias("dartUrl") if "dartUrl" in hits.columns else pl.lit(None).alias("dartUrl")
    )
    return (
        hits.rename({sc_col: "stockCode"})
        .group_by("stockCode")
        .agg(
            pl.len().alias("docsHitCount"),
            score_expr,
            pl.col(text_col).first().alias("docsSnippet"),
            url_expr,
        )
        .with_columns(pl.lit(True).alias(field))
    )


def _loadKrx(field: str, spec: dict[str, Any]) -> pl.DataFrame:
    name = field.split(".", 1)[1]
    start = spec.get("start")
    end = spec.get("end")
    if start is None and end is None and name in _KRX_FIELDS:
        raw = _loadKrxLatestYear()
    else:
        end_date = date.today()
        if start is None and end is None:
            start = (end_date - timedelta(days=int(spec.get("windowDays", 420)))).isoformat()
            end = end_date.isoformat()
        raw = _loadKrxWindow(start=start, end=end)
    if raw is None or raw.is_empty():
        return pl.DataFrame({"stockCode": [], field: []})
    return _finalizeKrxValues(raw, name, field)


def _loadKrxLatestYear(*, asof: str | None = None) -> pl.DataFrame:
    """Sprint 4 PR4 - asof 옵션 패스스루. default None → 기존 동작."""
    from dartlab.gather.bulkData.hfBulk import loadFiltered

    this_year = date.today().year
    raw = loadFiltered(year=this_year, adjustment="raw", asof=asof)
    if raw is None or raw.is_empty():
        raw = loadFiltered(year=this_year - 1, adjustment="raw", asof=asof)
    return raw


def _loadKrxWindow(*, start: str | None, end: str | None, asof: str | None = None) -> pl.DataFrame:
    """Sprint 4 PR4 - asof 옵션 패스스루. default None → 기존 동작."""
    from dartlab.gather.bulkData.hfBulk import loadFiltered

    return loadFiltered(start=start, end=end, adjustment="raw", asof=asof)


def _finalizeKrxValues(raw: pl.DataFrame, name: str, field: str) -> pl.DataFrame:
    from dartlab.gather.krx.krxApi import _KRX_TO_STD

    rename = {k: v for k, v in _KRX_TO_STD.items() if k in raw.columns}
    df = raw.rename(rename).sort(["stockCode", "date"])
    if name not in df.columns:
        from dartlab.gather.transforms.indicatorDispatch import computeIndicator

        df = df.with_columns(computeIndicator(df, name).alias(name))
    if name not in df.columns:
        raise ValueError(f"KRX field {field!r} 를 계산할 수 없습니다.")
    return df.group_by("stockCode").agg(pl.col(name).last().alias(field))


def _applyCondition(df: pl.DataFrame, field: str, cond: dict[str, Any], meta: dict[str, str]) -> pl.DataFrame:
    if df.is_empty():
        return df
    op = str(cond.get("op", "=="))
    allowed = set(meta["operatorSet"].split(","))
    if op not in allowed:
        raise ValueError(f"{field!r} 에서 op={op!r} 는 지원하지 않습니다. 가용: {meta['operatorSet']}")
    if op == "exists":
        return df.filter(pl.col(field).is_not_null())
    if op == "not_exists":
        return df.filter(pl.col(field).is_null())
    if "value" not in cond:
        raise ValueError(f"{field!r} 조건에는 value 가 필요합니다.")

    value = cond["value"]
    if meta["kind"] == "number":
        expr = _numericExpr(field)
        if op == ">":
            return df.filter(expr > float(value))
        if op == ">=":
            return df.filter(expr >= float(value))
        if op == "<":
            return df.filter(expr < float(value))
        if op == "<=":
            return df.filter(expr <= float(value))
        if op == "==":
            return df.filter(expr == float(value))
        if op == "!=":
            return df.filter(expr != float(value))
        if op == "between":
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise ValueError("between value 는 [min, max] 형태여야 합니다.")
            return df.filter(expr.is_between(float(value[0]), float(value[1])))

    text = pl.col(field).cast(pl.Utf8)
    if op == "contains":
        return df.filter(text.str.contains(str(value), literal=True))
    if op == "==":
        return df.filter(text == str(value))
    if op == "!=":
        return df.filter(text != str(value))
    raise ValueError(f"{field!r} 에서 op={op!r} 를 적용할 수 없습니다.")


def _numericExpr(field: str) -> pl.Expr:
    return (
        pl.col(field)
        .cast(pl.Utf8, strict=False)
        .str.replace_all(",", "")
        .str.replace_all("%", "")
        .str.replace_all("배", "")
        .cast(pl.Float64, strict=False)
    )


def _innerJoinOnStock(frames: list[pl.DataFrame]) -> pl.DataFrame:
    frames = [f for f in frames if f is not None]
    if not frames:
        return pl.DataFrame()
    result = frames[0]
    for frame in frames[1:]:
        result = result.join(frame, on="stockCode", how="inner")
    return result


def _unionOnStock(frames: list[pl.DataFrame]) -> pl.DataFrame:
    all_cols = sorted({c for frame in frames for c in frame.columns})
    padded = []
    for frame in frames:
        missing = [c for c in all_cols if c not in frame.columns]
        if missing:
            frame = frame.with_columns([pl.lit(None).alias(c) for c in missing])
        padded.append(frame.select(all_cols))
    return pl.concat(padded, how="diagonal_relaxed").unique(subset=["stockCode"], keep="first")


def _isContextField(field: str) -> bool:
    return _normalizeField(field).startswith("krxIndex.")


def _attachContextFields(df: pl.DataFrame, fields: list[str], spec: dict[str, Any]) -> pl.DataFrame:
    for field in dict.fromkeys(_normalizeField(f) for f in fields if f):
        if not field.startswith("krxIndex."):
            continue
        value = _loadKrxIndexScalar(field, spec)
        df = df.with_columns(pl.lit(value).alias(field))
    return df


def _loadKrxIndexScalar(field: str, spec: dict[str, Any]) -> float | int | str | None:
    _, market, name = field.split(".", 2)
    start = spec.get("start")
    end = spec.get("end")
    if start is None and end is None:
        year = date.today().year
        raw = _loadKrxIndexYear(market=market, year=year)
        if raw is None or raw.is_empty():
            raw = _loadKrxIndexYear(market=market, year=year - 1)
    else:
        from dartlab.gather.bulkData.hfIndexBulk import loadFiltered

        raw = loadFiltered(market=market, start=start, end=end)
    if raw is None or raw.is_empty():
        return None

    return _finalizeKrxIndexScalar(raw, name, spec)


def _loadKrxIndexYear(*, market: str, year: int) -> pl.DataFrame:
    from dartlab.gather.bulkData.hfIndexBulk import loadFiltered

    return loadFiltered(market=market, year=year)


def _finalizeKrxIndexScalar(raw: pl.DataFrame, name: str, spec: dict[str, Any]) -> float | int | str | None:
    from dartlab.gather.krx.krxIndex import _KRX_TO_STD

    rename = {k: v for k, v in _KRX_TO_STD.items() if k in raw.columns}
    df = raw.rename(rename).sort("date")
    target_index = spec.get("indexName")
    if target_index and "indexName" in df.columns:
        df = df.filter(pl.col("indexName") == target_index)
    if df.is_empty() or name not in df.columns:
        return None
    return df[name][-1]


# ── define: 폐쇄 vocabulary 파생 필드 AST (문자열 eval 금지, 단위 전파) ──


def _defineRefs(node: dict[str, Any]) -> list[str]:
    """define 노드가 참조하는 다른 파생 이름(@) 목록."""
    refs: list[str] = []
    for key in ("left", "right", "field"):
        v = node.get(key)
        if isinstance(v, str) and v.startswith("@"):
            refs.append(v[1:])
    return refs


def _topoSortDefines(defines: dict[str, Any]) -> list[str]:
    """define 위상정렬. 순환·미정의 참조는 즉시 ValueError."""
    order: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(n: str) -> None:
        """DFS 방문. 순환·미정의 검출 후 후위순으로 order 에 추가."""
        if n in visited:
            return
        if n in visiting:
            raise ValueError(f"define 순환 참조: @{n}")
        if n not in defines:
            raise ValueError(f"미정의 define 참조: @{n}")
        node = defines[n]
        if not isinstance(node, dict):
            raise ValueError(f"define @{n} 는 dict 노드여야 합니다.")
        visiting.add(n)
        for dep in _defineRefs(node):
            visit(dep)
        visiting.discard(n)
        visited.add(n)
        order.append(n)

    for n in defines:
        visit(n)
    return order


def _deriveUnit(op: str, lu: str, ru: str, name: str) -> str:
    """이항 연산 단위 대수. add/sub 동일단위 강제, div 동일단위는 배(무차원)."""
    if op in ("add", "sub"):
        if lu != ru:
            raise ValueError(f"@{name}: {op} 단위 불일치 ({lu} vs {ru}). 동일 단위만 가감 가능.")
        return lu
    if op == "mul":
        if ru in ("배", "무차원"):
            return lu
        if lu in ("배", "무차원"):
            return ru
        return f"{lu}·{ru}"
    # div
    if lu == ru:
        return "배"
    return f"{lu}/{ru}"


def _finiteOnly(df: pl.DataFrame) -> pl.DataFrame:
    """operand 의 ``_v`` 에서 NaN·무한대를 null 로 정규화한다 (Float64 캐스팅 동반).

    polars 의 ``is_not_null()`` 은 NaN 을 걸러내지 않는다. 지표 window 부족(예 ``krx.roc12`` 2984 종목 중
    NaN 15)이나 0 나눗셈이 만든 비유한값 하나가 group mean/std 와 quantile 을 통째로 NaN 으로 오염시켜
    zscore·winsorize 결과가 전 종목 NaN 이 된다(조용한 오답). 통계·순위 연산 전에 비유한값을 결측으로
    승격해 해당 종목만 정직한 gap 이 되게 한다 (missing > wrong).

    Args:
        df: ``_v`` 컬럼을 가진 operand 프레임.

    Returns:
        ``_v`` 가 Float64 이고 NaN/무한대가 null 로 바뀐 프레임. ``_v`` 부재 시 원본.

    Raises:
        없음.
    """
    if "_v" not in df.columns:
        return df
    v = pl.col("_v").cast(pl.Float64, strict=False)
    return df.with_columns(pl.when(v.is_finite()).then(v).otherwise(None).alias("_v"))


def _operandFrame(
    ref: Any, spec: dict[str, Any], values: dict[str, pl.DataFrame], units: dict[str, str]
) -> tuple[pl.DataFrame, str]:
    """define operand(필드 키 또는 @참조)을 ([stockCode, _v] 프레임, 단위)로. 리터럴 미지원.

    반환 전 ``_finiteOnly`` 로 NaN/무한대를 null 로 정규화한다 (통계·순위 오염 차단).
    """
    if isinstance(ref, bool) or isinstance(ref, (int, float)):
        raise ValueError("define operand 는 필드 키 또는 @참조만 (리터럴 미지원, 임계값은 where.value 로).")
    ref = str(ref)
    if ref.startswith("@"):
        nm = ref[1:]
        if nm not in values:
            raise ValueError(f"미해소 @참조: {ref}")
        return _finiteOnly(values[nm].rename({f"@{nm}": "_v"})), units[nm]
    meta = _fieldMeta(ref, spec)
    if meta["kind"] != "number":
        raise ValueError(f"define operand {ref!r} 는 수치 필드가 아닙니다 (kind={meta['kind']}).")
    vals = _loadFieldValues(ref, spec)
    if "stockCode" not in vals.columns or ref not in vals.columns:
        return pl.DataFrame({"stockCode": [], "_v": []}), meta["unit"]
    return _finiteOnly(vals.select("stockCode", _numericExpr(ref).alias("_v"))), meta["unit"]


_UNARY_OPS = frozenset({"abs", "log", "clip", "winsorize"})


def _asLiteral(operand: Any) -> float | None:
    """operand 가 수치 리터럴이면 float, 아니면 None (bool 은 리터럴 아님)."""
    if isinstance(operand, bool):
        return None
    if isinstance(operand, (int, float)):
        return float(operand)
    return None


def _scalarBinary(
    op: str,
    name: str,
    node: dict[str, Any],
    lLit: float | None,
    rLit: float | None,
    spec: dict[str, Any],
    values: dict[str, pl.DataFrame],
    units: dict[str, str],
) -> tuple[pl.DataFrame, str]:
    """한쪽이 리터럴 스칼라인 이항 연산 ([stockCode, @name], 단위).

    가중 다팩터 스코어 합성의 핵심 (예 ``0.6 * @zRoe``). mul/div 는 스칼라를 무차원 계수로 취급해
    base 단위를 보존하고, add/sub 는 동일단위 오프셋으로 base 단위를 보존한다. 리터럴/필드 나눗셈
    (스칼라 ÷ 필드) 은 역수 단위가 되어 단위 대수를 흐리므로 금지 (곱셈·필드÷스칼라 로 표현).

    Args:
        op: add/sub/mul/div 중 하나.
        name: 파생 필드 이름 (@name).
        node: define 노드 (left/right 중 하나가 리터럴).
        lLit: 좌변 리터럴 값 (좌변이 리터럴 아니면 None).
        rLit: 우변 리터럴 값 (우변이 리터럴 아니면 None).
        spec: screen spec.
        values: 지금까지 평가된 파생 값.
        units: 지금까지 평가된 파생 단위.

    Returns:
        ([stockCode, @name] 프레임, 결과 단위).

    Raises:
        ValueError: 리터럴/필드 나눗셈, 또는 0 으로 나눔.
    """
    fieldKey = f"@{name}"
    v = pl.col("_v")
    if lLit is not None:  # 리터럴 op 필드
        base, unit = _operandFrame(node["right"], spec, values, units)
        s = lLit
        if op == "add":
            expr = s + v
        elif op == "sub":
            expr = s - v
        elif op == "mul":
            expr = s * v
        else:  # div: 스칼라 ÷ 필드 = 역수 단위, 금지
            raise ValueError(
                f"@{name}: 리터럴 ÷ 필드 는 역수 단위라 미지원입니다 (곱셈 또는 필드 ÷ 리터럴 로 표현하세요)."
            )
    else:  # 필드 op 리터럴
        base, unit = _operandFrame(node["left"], spec, values, units)
        s = rLit if rLit is not None else 0.0
        if op == "add":
            expr = v + s
        elif op == "sub":
            expr = v - s
        elif op == "mul":
            expr = v * s
        else:  # div by scalar
            if s == 0:
                raise ValueError(f"@{name}: 0 으로 나눌 수 없습니다.")
            expr = v / s
    return base.select("stockCode", expr.alias(fieldKey)), unit


def _evalUnaryNode(
    name: str,
    node: dict[str, Any],
    spec: dict[str, Any],
    values: dict[str, pl.DataFrame],
    units: dict[str, str],
) -> tuple[pl.DataFrame, str]:
    """단항 변환 define 노드 ([stockCode, @name], 단위). 스코어 아웃라이어 방어·정규화용.

    abs/log 는 원소별 변환, clip 은 절대 경계 [min,max] 로 제한, winsorize 는 유니버스 분위
    [lower,upper] 로 꼬리 절단 (z-score 를 아웃라이어가 지배하는 것을 막는다). 모두 단조 변환이라
    base 단위를 보존한다 (랭킹 목적 스케일 의미 유지).

    Args:
        name: 파생 필드 이름.
        node: define 노드. field(원천/@참조) 필수. clip=min/max, winsorize=lower/upper.
        spec: screen spec.
        values: 평가된 파생 값.
        units: 평가된 파생 단위.

    Returns:
        ([stockCode, @name] 프레임, base 단위).

    Raises:
        ValueError: field 누락, clip 경계 전무, winsorize 분위 범위 오류.
    """
    op = node["op"]
    ref = node.get("field")
    if ref is None:
        raise ValueError(f"@{name}: 단항 op({op}) 는 field (원천 필드 또는 @참조) 가 필요합니다.")
    operand, unit = _operandFrame(ref, spec, values, units)
    fieldKey = f"@{name}"
    v = pl.col("_v")
    if op == "abs":
        expr = v.abs()
    elif op == "log":
        expr = pl.when(v > 0).then(v.log()).otherwise(None)
    elif op == "clip":
        lo = node.get("min")
        hi = node.get("max")
        if lo is None and hi is None:
            raise ValueError(f"@{name}: clip 은 min 또는 max 중 하나 이상이 필요합니다.")
        expr = v.clip(lower_bound=lo, upper_bound=hi)
    else:  # winsorize (유니버스 분위 절단)
        lower = float(node.get("lower", 0.01))
        upper = float(node.get("upper", 0.99))
        if not (0.0 <= lower < upper <= 1.0):
            raise ValueError(f"@{name}: winsorize 는 0<=lower<upper<=1 이어야 합니다 (받은 {lower}, {upper}).")
        clean = operand.filter(pl.col("_v").is_not_null())
        if clean.is_empty():
            return pl.DataFrame({"stockCode": [], fieldKey: []}), unit
        lo = clean["_v"].quantile(lower)
        hi = clean["_v"].quantile(upper)
        expr = v.clip(lower_bound=lo, upper_bound=hi)
    return operand.select("stockCode", expr.alias(fieldKey)), unit


def _evalDefineNode(
    name: str,
    node: dict[str, Any],
    spec: dict[str, Any],
    values: dict[str, pl.DataFrame],
    units: dict[str, str],
) -> tuple[pl.DataFrame, str]:
    """단일 define 노드를 평가해 ([stockCode, @name] 프레임, 단위)로.

    op 별 분기: 없음+field=패스스루, add/sub/mul/div=이항 산술(리터럴 스칼라 가중 포함),
    abs/log/clip/winsorize=단항 변환, yoy/cagr/slope/mean/min/max=시계열(연간 격자),
    percentile/zscore=상대(전체·업종 횡단).
    """
    fieldKey = f"@{name}"
    op = node.get("op")
    if op is None and "field" in node:
        df, unit = _operandFrame(node["field"], spec, values, units)
        return df.rename({"_v": fieldKey}), unit
    if op in _TEMPORAL_OPS:
        return _evalTemporalNode(name, node, spec)
    if op in _RELATIVE_OPS:
        return _evalRelativeNode(name, node, spec, values, units)
    if op in _UNARY_OPS:
        return _evalUnaryNode(name, node, spec, values, units)
    if op not in ("add", "sub", "mul", "div"):
        raise ValueError(
            f"@{name}: 지원하지 않는 define op {op!r} "
            "(산술 add/sub/mul/div · 단항 abs/log/clip/winsorize · 시계열 yoy/cagr/slope/mean/min/max · "
            "상대 percentile/zscore · 또는 field)."
        )
    if "left" not in node or "right" not in node:
        raise ValueError(f"@{name}: op 노드는 left/right 가 필요합니다.")
    lLit = _asLiteral(node["left"])
    rLit = _asLiteral(node["right"])
    if lLit is not None and rLit is not None:
        raise ValueError(f"@{name}: 양변 리터럴 연산은 미지원입니다 (필드/@참조가 최소 1개 필요).")
    if lLit is not None or rLit is not None:
        return _scalarBinary(op, name, node, lLit, rLit, spec, values, units)
    ldf, lu = _operandFrame(node["left"], spec, values, units)
    rdf, ru = _operandFrame(node["right"], spec, values, units)
    unit = _deriveUnit(op, lu, ru, name)
    joined = ldf.join(rdf, on="stockCode", how="inner", suffix="_r")
    lcol, rcol = pl.col("_v"), pl.col("_v_r")
    if op == "add":
        expr = lcol + rcol
    elif op == "sub":
        expr = lcol - rcol
    elif op == "mul":
        expr = lcol * rcol
    else:  # div (0 나눗셈은 null)
        expr = pl.when(rcol == 0).then(None).otherwise(lcol / rcol)
    return joined.select("stockCode", expr.alias(fieldKey)), unit


def _computeDerived(spec: dict[str, Any]) -> tuple[dict[str, pl.DataFrame], dict[str, str]]:
    """spec.define 전체를 위상순으로 평가. ({name: [stockCode, @name]}, {name: unit}) 반환."""
    defines = spec.get("define")
    if not defines:
        return {}, {}
    if not isinstance(defines, dict):
        raise ValueError("spec.define 은 {name: node} dict 여야 합니다.")
    order = _topoSortDefines(defines)
    values: dict[str, pl.DataFrame] = {}
    units: dict[str, str] = {}
    for name in order:
        df, unit = _evalDefineNode(name, defines[name], spec, values, units)
        values[name] = df
        units[name] = unit
    return values, units


# ── define Phase 3: 시계열(temporal) + 상대(relative) 노드 ──
# 시계열 = 종목별 연간 격자 위 단항 연산. 상대 = 유니버스(전체·업종) 횡단 순위.

_TEMPORAL_OPS = frozenset({"yoy", "cagr", "slope", "mean", "min", "max"})
_RELATIVE_OPS = frozenset({"percentile", "zscore"})


def _loadFieldSeries(field: str, n: int) -> tuple[pl.DataFrame, int]:
    """finance.account.* · finance.ratio.* 를 연간 시계열 [stockCode, _t0.._t{k-1}] 로.

    위치 컬럼은 오래된→최신 순(``_t0`` 이 가장 과거). 최근 ``n`` 개 연도만 정규화하며,
    시계열 격자가 없는 원천(valuation/krx/note)은 ValueError 로 조기 차단(조용한 오답 회피).
    반환은 (프레임, 실제 기간 수 k). 데이터 부재는 (빈 프레임, 0).
    """
    if field.startswith("finance.account."):
        from dartlab.providers.dart.finance.scanAccount import scanAccount

        df = scanAccount(field.split(".", 2)[2], freq="Y")
    elif field.startswith("finance.ratio."):
        from dartlab.providers.dart.finance.scanAccount import scanRatio

        df = scanRatio(field.split(".", 2)[2], freq="Y")
    else:
        raise ValueError(
            f"시계열 연산은 finance.account.* · finance.ratio.* 만 지원합니다 (연간 격자). 받은 field={field!r}."
        )
    if df is None or df.is_empty() or "stockCode" not in df.columns:
        return pl.DataFrame({"stockCode": []}), 0
    periods = sorted(c for c in df.columns if c != "stockCode")  # 오름차순 = 오래된 먼저
    if n and n > 0:
        periods = periods[-n:]
    if not periods:
        return pl.DataFrame({"stockCode": []}), 0
    out = df.select("stockCode", *[_numericExpr(p).alias(f"_t{i}") for i, p in enumerate(periods)])
    return out, len(periods)


def _temporalUnit(op: str, base: str) -> str:
    """시계열 op 결과 단위. yoy/cagr 는 무차원 성장(배), 축약·기울기는 원 단위."""
    if op in ("yoy", "cagr"):
        return "배"
    return base


def _slopeFrame(series: pl.DataFrame, cols: list[str], fieldKey: str) -> pl.DataFrame:
    """연간 격자의 OLS 회귀 기울기(null 무시). x=연도 위치(0..), y=값."""
    long = series.unpivot(index="stockCode", on=cols, variable_name="_p", value_name="_v")
    long = long.with_columns(pl.col("_p").str.slice(2).cast(pl.Int64).alias("_x")).filter(pl.col("_v").is_not_null())
    agg = long.group_by("stockCode").agg(
        pl.len().alias("_n"),
        pl.col("_x").mean().alias("_mx"),
        pl.col("_v").mean().alias("_mv"),
        (pl.col("_x") * pl.col("_v")).mean().alias("_mxv"),
        (pl.col("_x") * pl.col("_x")).mean().alias("_mxx"),
    )
    denom = pl.col("_mxx") - pl.col("_mx") ** 2
    slope = (
        pl.when((pl.col("_n") < 2) | (denom == 0))
        .then(None)
        .otherwise((pl.col("_mxv") - pl.col("_mx") * pl.col("_mv")) / denom)
    )
    return agg.select("stockCode", slope.alias(fieldKey))


def _evalTemporalNode(name: str, node: dict[str, Any], spec: dict[str, Any]) -> tuple[pl.DataFrame, str]:
    """시계열 define 노드(단항, 원천 필드의 연간 격자)를 평가."""
    op = node["op"]
    field = node.get("field")
    if not isinstance(field, str) or field.startswith("@"):
        raise ValueError(f"@{name}: 시계열 op({op}) 의 field 는 원천 시계열 필드 키여야 합니다 (@참조·리터럴 불가).")
    field = _normalizeField(field)
    meta = _fieldMeta(field, spec)
    if meta["kind"] != "number":
        raise ValueError(f"@{name}: 시계열 op 는 수치 필드만 가능합니다 (field={field!r}, kind={meta['kind']}).")
    years = int(node.get("years", 3))
    if years < 2:
        raise ValueError(f"@{name}: years 는 2 이상이어야 합니다 (받은 값 {years}).")
    want = 2 if op == "yoy" else years
    series, k = _loadFieldSeries(field, want)
    fieldKey = f"@{name}"
    unit = _temporalUnit(op, meta["unit"])
    if series.is_empty() or k < 2:
        if op in ("mean", "min", "max") and k == 1:  # 단일 기간이면 그 값 자체
            return series.select("stockCode", pl.col("_t0").alias(fieldKey)), unit
        return pl.DataFrame({"stockCode": [], fieldKey: []}), unit
    cols = [f"_t{i}" for i in range(k)]
    if op == "mean":
        expr = pl.mean_horizontal(cols)
    elif op == "min":
        expr = pl.min_horizontal(cols)
    elif op == "max":
        expr = pl.max_horizontal(cols)
    elif op == "yoy":
        prev, last = pl.col(f"_t{k - 2}"), pl.col(f"_t{k - 1}")
        expr = pl.when(prev.abs() == 0).then(None).otherwise((last - prev) / prev.abs())
    elif op == "cagr":
        first, last = pl.col("_t0"), pl.col(f"_t{k - 1}")
        expr = pl.when((first <= 0) | (last <= 0)).then(None).otherwise((last / first) ** (1.0 / (k - 1)) - 1.0)
    else:  # slope (OLS, null 무시)
        return _slopeFrame(series, cols, fieldKey), unit
    return series.select("stockCode", expr.alias(fieldKey)), unit


def _industryMap() -> pl.DataFrame:
    """[stockCode, _grp] 업종 매핑 (dartlab.listing 업종 컬럼). 미provision 시 빈 프레임."""
    try:
        from dartlab._listingDispatch import listing as _listing

        lst = _listing()
    except (ImportError, AttributeError, ValueError, RuntimeError):
        return pl.DataFrame({"stockCode": [], "_grp": []})
    if lst is None or lst.is_empty():
        return pl.DataFrame({"stockCode": [], "_grp": []})
    codeCol = "종목코드" if "종목코드" in lst.columns else ("stockCode" if "stockCode" in lst.columns else None)
    grpCol = "업종" if "업종" in lst.columns else None
    if codeCol is None or grpCol is None:
        return pl.DataFrame({"stockCode": [], "_grp": []})
    return lst.select(
        pl.col(codeCol).cast(pl.Utf8).alias("stockCode"),
        pl.col(grpCol).cast(pl.Utf8).alias("_grp"),
    ).drop_nulls()


def _evalRelativeNode(
    name: str,
    node: dict[str, Any],
    spec: dict[str, Any],
    values: dict[str, pl.DataFrame],
    units: dict[str, str],
) -> tuple[pl.DataFrame, str]:
    """상대 define 노드(횡단 순위). field=원천 필드 또는 @참조, by=업종/전체."""
    op = node["op"]
    ref = node.get("field")
    if ref is None:
        raise ValueError(f"@{name}: 상대 op({op}) 는 field(원천 필드 또는 @참조)가 필요합니다.")
    by = node.get("by")
    fieldKey = f"@{name}"
    unit = "백분위" if op == "percentile" else "표준편차"
    operand, _u = _operandFrame(ref, spec, values, units)
    operand = operand.filter(pl.col("_v").is_not_null())
    if operand.is_empty():
        return pl.DataFrame({"stockCode": [], fieldKey: []}), unit
    if by in ("industry", "sector", "업종"):
        imap = _industryMap()
        if imap.is_empty():
            raise ValueError(f"@{name}: by=industry 상대순위에 필요한 업종 매핑을 로드할 수 없습니다.")
        operand = operand.join(imap, on="stockCode", how="inner")
        if operand.is_empty():
            return pl.DataFrame({"stockCode": [], fieldKey: []}), unit
        grp = ["_grp"]
    elif by is None:
        operand = operand.with_columns(pl.lit(0).alias("_grp"))
        grp = ["_grp"]
    else:
        raise ValueError(f"@{name}: 지원하지 않는 by={by!r} (industry/sector 또는 생략).")
    if op == "percentile":
        cnt = pl.len().over(grp)
        rank = pl.col("_v").rank(method="average").over(grp)
        expr = pl.when(cnt < 2).then(None).otherwise((rank - 1.0) / (cnt - 1.0) * 100.0)
    else:  # zscore
        mean = pl.col("_v").mean().over(grp)
        std = pl.col("_v").std().over(grp)
        expr = pl.when((std == 0) | std.is_null()).then(None).otherwise((pl.col("_v") - mean) / std)
    return operand.select("stockCode", expr.alias(fieldKey)), unit


def _loadNote(field: str) -> pl.DataFrame:
    """note.<concept>@<항목명> 을 종목별 최신 valueNum 으로. 항목 미지정 시 ValueError."""
    from dartlab.scan.note import scanNote

    rest = field.split(".", 1)[1]
    concept, sep, account = rest.partition("@")
    if not sep or not account:
        raise ValueError(
            f"note 필드는 항목 지정이 필요합니다: note.{concept}@<항목명> (scan('note', '{concept}') 로 항목 확인)."
        )
    df = scanNote(concept)
    if df is None or df.is_empty() or "valueNum" not in df.columns or "account" not in df.columns:
        return pl.DataFrame({"stockCode": [], field: []})
    df = df.filter(pl.col("account") == account)
    if df.is_empty():
        return pl.DataFrame({"stockCode": [], field: []})
    df = df.sort(["stockCode", "period"]).group_by("stockCode").tail(1)
    return df.select("stockCode", pl.col("valueNum").alias(field))


def _loadCompositeAxis(field: str, spec: dict[str, Any]) -> pl.DataFrame:
    """axis.* 복합축 필드를 raw 스캐너 네이티브 컬럼에서 [stockCode, field] 로.

    ``_COMPOSITE_AXIS_FIELDS`` 정본의 (module, fn, col)로 raw 스캐너를 직접 호출(dispatch 한글 리네임 우회).
    같은 스캐너 결과는 ``spec['_axisCache']``에 캐시해 회사당 축 1회만 계산한다. 스캐너 실패/컬럼 부재는
    빈 프레임으로 흡수(축 무회귀).
    """
    reg = _COMPOSITE_AXIS_FIELDS.get(field)
    if reg is None:
        return pl.DataFrame({"stockCode": [], field: []})
    cache = spec.get("_axisCache") if isinstance(spec, dict) else None
    if cache is None:
        cache = {}
    key = (reg["module"], reg["fn"])
    if key not in cache:
        import importlib

        try:
            mod = importlib.import_module(reg["module"])
            cache[key] = getattr(mod, reg["fn"])(verbose=False)
        except (pl.exceptions.PolarsError, OSError, ValueError, ImportError, AttributeError):
            cache[key] = pl.DataFrame()
    df = cache[key]
    col = reg["col"]
    scCol = "stockCode" if "stockCode" in df.columns else ("종목코드" if "종목코드" in df.columns else None)
    if df.is_empty() or scCol is None or col not in df.columns:
        return pl.DataFrame({"stockCode": [], field: []})
    return df.select(pl.col(scCol).cast(pl.Utf8).alias("stockCode"), pl.col(col).alias(field))


__all__ = ["executeScreenSpec", "executeScreenSpecDetailed", "scanFields"]
