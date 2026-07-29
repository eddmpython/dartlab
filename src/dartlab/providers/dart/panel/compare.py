"""compare — N 회사 panel 을 회사 간 시점 비교 wide 로 정렬."""

from __future__ import annotations

import re
from dataclasses import dataclass

import polars as pl

from dartlab.core.market import detectMarket, isKrStockCode, normalizeKrCode

from .canonical import canonicalRankExpr
from .period import isPeriodColumn, sortPeriods
from .read import readWide

_MAX_COMPARE = 6
# 행 식별 컬럼 (readWide 출력 — read._INDEX_COLS 동형, leafSeq 제외).
_IDENT = ["chapter", "sectionLeaf", "blockLeaf", "leafType", "disclosureKey", "scope"]
_SEP = "␟"  # ␟ — 셀 컬럼 namespace 구분자 ({code}␟{period})

# 재무제표 토픽 — 셀(항목) 단위 비교(acode 정렬 + 원 환산). 통짜 표 병치 대신.
_FIN_KEYS = frozenset({"bs", "is", "cf", "cis", "sce"})
_VALID_FREQ = frozenset({"quarter", "year", "ytd"})
# 입력·셀 wide 기간 열은 연간(YYYY)과 분기(YYYYQn)를 모두 받는다 (단위 배율 SSOT=build.cell).
_PERIOD_RE = re.compile(r"^\d{4}(?:Q[1-4])?$")
_US_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")


def _displayCodes(codes: list[str] | str | None) -> list[str]:
    """진단 표시용 codes 정규화 — 검증 없이 str→[str], strip, US ticker upper."""
    if isinstance(codes, str):
        codes = [codes]
    out: list[str] = []
    for c in codes or []:
        # KR 코드(영숫자 포함)·US ticker 모두 대문자 표기가 정본이라 분기 없이 정규화한다.
        c = normalizeKrCode(c)
        if c:
            out.append(c)
    return out


def _normCodes(codes: list[str] | str | None) -> list[str]:
    """codes 정규화·검증 — KR 6자리 또는 US ticker 만 허용."""
    out = _displayCodes(codes)
    invalid = [c for c in out if not (isKrStockCode(c) or _US_TICKER_RE.fullmatch(c))]
    if invalid:
        raise ValueError("codes 는 한국 6자리 종목코드 또는 미국 ticker 여야 합니다.")
    if len(out) != len(set(out)):
        raise ValueError("codes 에 중복 종목코드가 있습니다. 비교 대상은 서로 다른 회사여야 합니다.")
    return out


def _normScope(scope: str | None) -> str | None:
    """사용자 scope 어휘 → wide 의 scope 값('consolidated'/'standalone')."""
    if scope is None:
        return None
    s = str(scope).strip().lower()
    if s in {"consolidated", "연결", "c"}:
        return "consolidated"
    if s in {"separate", "standalone", "별도", "s"}:
        return "standalone"
    raise ValueError("scope 는 consolidated/standalone(연결/별도) 중 하나여야 합니다.")


def _normTopic(topic: str | None) -> str | None:
    """topic 입력 정규화 — None 또는 비어있지 않은 문자열."""
    if topic is None:
        return None
    value = str(topic).strip()
    if not value:
        raise ValueError("topic 은 비어 있지 않은 문자열이어야 합니다.")
    return value


def _normFreq(freq: str) -> str:
    """freq 정규화 — 재무 셀모드 입도 명시."""
    f = str(freq).strip().lower()
    if f not in _VALID_FREQ:
        raise ValueError("freq 는 quarter/year/ytd 중 하나여야 합니다.")
    return f


def _normPeriod(period: list[str] | str | None) -> list[str] | str | None:
    """period 입력 검증·정렬 — YYYY 또는 YYYYQn, list 는 최신순."""
    if period is None:
        return None
    single = isinstance(period, str)
    raw = [period] if single else period
    if not isinstance(raw, list):
        raise ValueError("period 는 YYYY/YYYYQn 문자열 또는 그 리스트여야 합니다.")
    if len(raw) == 0:
        raise ValueError("period 는 YYYY/YYYYQn 문자열 또는 비어 있지 않은 리스트여야 합니다.")
    vals: list[str] = []
    for p in raw:
        val = str(p).strip()
        if not _PERIOD_RE.fullmatch(val):
            raise ValueError("period 는 YYYY 또는 YYYYQn 형식이어야 합니다.")
        vals.append(val)
    vals = list(dict.fromkeys(vals))
    if single:
        return vals[0] if vals else None
    return sortPeriods(vals, descending=True)


def _detectUnitScalesByStatement(
    code: str, marketNs: str, statements: tuple[str, ...] | None = None
) -> dict[str, dict[str, int]]:
    """statement×period caption 단위 → 원 배율 map. 미발견=백만원."""
    from dartlab.core.dataLoader import readParquetSafe  # WASM 세이프 read (pyodide=pyarrow 경유)
    from dartlab.providers.dart.panel.build.cell import CELL_STATEMENTS
    from dartlab.providers.dart.parse.amount import detectUnitScale

    from .read import _panelDir, ensurePanelFromHf

    ensurePanelFromHf(code, marketNs)
    flat = _panelDir(code, marketNs).parent / f"{code}.parquet"
    if not flat.exists():
        return {}
    df = readParquetSafe(str(flat), columns=["disclosureKey", "contentRaw", "period"])
    targetStatements = statements or tuple(CELL_STATEMENTS)
    stmt = df.filter(pl.col("disclosureKey").is_in(list(targetStatements)))
    if stmt.is_empty():
        return {}
    out: dict[str, dict[str, int]] = {}
    for statement in targetStatements:
        scoped = stmt.filter(pl.col("disclosureKey") == statement)
        if scoped.is_empty():
            continue
        byPeriod: dict[str, int] = {}
        periods = [str(p) for p in scoped.select("period").unique()["period"].to_list() if p]
        for period in periods:
            # 같은 statement/period의 ACODE 없는 caption leaf만 단위 근거로 쓴다.
            cap = scoped.filter(
                (pl.col("period") == period) & ~pl.col("contentRaw").str.contains("ACODE=", literal=True)
            )
            scale = 1_000_000
            for r in cap.iter_rows(named=True):
                detectedScale = detectUnitScale(r["contentRaw"])
                if detectedScale is not None:
                    scale = detectedScale
                    break
            byPeriod[period] = scale
        out[statement] = byPeriod
    return out


def _financePeriodLabel(period: str, freq: str) -> str:
    """사용자 period 입력 → finance wide 컬럼 라벨."""
    p = str(period).strip()
    if freq == "year":
        m = re.fullmatch(r"(\d{4})(?:Q[1-4])?", p)
        return m.group(1) if m else p
    if re.fullmatch(r"\d{4}", p):
        return f"{p}Q4"
    return p


def _financePanelPeriod(period: str) -> str:
    """사용자 period 입력 → panel filing period prune 라벨."""
    p = str(period).strip()
    if re.fullmatch(r"\d{4}", p):
        return f"{p}Q4"
    return p


def _financeTargets(period: list[str] | str | None, freq: str) -> tuple[list[str] | None, list[str] | None]:
    """finance mode period 입력을 출력 라벨과 panel prune 라벨로 분리."""
    if period is None:
        return None, None
    raw = [period] if isinstance(period, str) else list(period)
    labels = list(dict.fromkeys(_financePeriodLabel(str(p), freq) for p in raw))
    panelPeriods = list(dict.fromkeys(_financePanelPeriod(str(p)) for p in raw))
    return labels, panelPeriods


def _companyCellsByPeriodEdgar(
    code: str,
    statement: str,
    freq: str,
    scope: str,
    *,
    targetLabels: list[str] | None = None,
    panelPeriods: list[str] | None = None,
) -> dict[str, dict[str, tuple[str, float]]]:
    """{period: {account: (label, USD 실값)}} — EDGAR native 셀 비교 재료 (KR 경로 미러).

    DART KR 경로(``_companyCellsByPeriod``)의 EDGAR 어댑터. 식별키는 ``acode`` 대신 native
    ``account``(EdgarMapper snakeId, 매핑 실패 시 raw concept). EDGAR 값은 USD 실값이라 원
    환산(scale) 없이 그대로 쓴다(``_detectUnitScalesByStatement`` 미호출 — 그건 KR 백만원 캡션 전용).
    ``STATEMENT_VARIANTS`` 로 is↔cis 폴백(포괄손익표만 내는 미국 회사 흡수). import 는 함수 lazy
    (모듈 top-level 로 올리면 edgar.panel ↔ dart.panel.compare 초기화 cycle).
    """
    from dartlab.core.utils.helpers import parseNumStr
    from dartlab.providers.edgar.panel.native import _cellsFromPanel as _edgarCells
    from dartlab.providers.edgar.panel.native import _statementWideVariants

    cells = _edgarCells(code, panelPeriods)
    if cells is None:
        return {}
    w = _statementWideVariants(cells, logical=statement.lower(), freq=freq, scope=scope)
    if w is None or w.is_empty():
        return {}
    wanted = set(targetLabels) if targetLabels is not None else None
    periods = [c for c in w.columns if _PERIOD_RE.fullmatch(c)]
    if wanted is not None:
        periods = [p for p in periods if p in wanted]
    out: dict[str, dict[str, tuple[str, float]]] = {}
    for p in periods:
        bucket = out.setdefault(p, {})
        for r in w.iter_rows(named=True):
            acc = r.get("account")
            raw = r.get(p)
            lab = r.get("label") or ""
            # account 첫 등장 우선. EDGAR native 는 이미 axisPath=="" depth-1 만 담는다.
            if acc and raw is not None and acc not in bucket:
                num = parseNumStr(str(raw))
                if num is not None:
                    bucket[acc] = (str(lab), num)  # USD 실값 (단위배율 1, 무스케일)
    return out


def _companyCellsByPeriod(
    code: str,
    statement: str,
    freq: str,
    scope: str,
    marketNs: str,
    *,
    targetLabels: list[str] | None = None,
    panelPeriods: list[str] | None = None,
) -> dict[str, dict[str, tuple[str, float]]]:
    """{period: {acode: (label, 원환산값)}} — statement 변형 union, depth-1 라인아이템.

    KR(DART)은 acode×period 셀(원 환산), US(EDGAR)는 native account×period 셀(USD 실값)로 갈린다 —
    셀 스키마가 시장마다 다르므로(``acode``/``axisPath`` vs ``account``) marketNs 로 어댑터를 분기한다.
    """
    if marketNs == "us":
        return _companyCellsByPeriodEdgar(
            code, statement, freq, scope, targetLabels=targetLabels, panelPeriods=panelPeriods
        )

    from dartlab.core.utils.helpers import parseNumStr

    from . import cell as _cell

    cells = _cell._cellsFromPanel(code, marketNs=marketNs, periods=panelPeriods)
    if cells is None:
        return {}
    variants = _cell.STATEMENT_VARIANTS.get(statement, (statement.upper(),))
    unitScalesByStatement = _detectUnitScalesByStatement(code, marketNs, variants)
    wanted = set(targetLabels) if targetLabels is not None else None
    out: dict[str, dict[str, tuple[str, float]]] = {}
    for v in variants:
        w = _cell._cellWideFromCells(cells, statement=v, freq=freq, scope=scope)
        if w is None or w.is_empty():
            continue
        # 연간(YYYY)+분기(YYYYQn) 둘 다 — isPeriodColumn(YYYYQn 전용)은 year 열 거부(freq="year" 전멸 버그).
        periods = [c for c in w.columns if _PERIOD_RE.fullmatch(c)]
        if wanted is not None:
            periods = [p for p in periods if p in wanted]
        if not periods:
            continue
        for p in periods:
            scale = unitScalesByStatement.get(v, {}).get(_financePanelPeriod(p), 1_000_000)
            bucket = out.setdefault(p, {})
            for r in w.sort("axisPath").iter_rows(named=True):
                ac = r.get("acode")
                ax = r.get("axisPath") or ""
                raw = r.get(p)
                lab = r.get("label") or ""
                # depth-1(파이프 없음 = top-level 라인아이템), acode 첫 등장 우선.
                if ac and raw is not None and "|" not in ax and ac not in bucket:
                    num = parseNumStr(str(raw))
                    if num is not None:
                        bucket[ac] = (str(lab), num * scale)
    return out


def _chooseFinanceTargets(per: dict[str, dict[str, dict[str, tuple[str, float]]]]) -> list[str]:
    """회사별 finance period map 에서 최신 공통 period, 없으면 최신 union period 1개."""
    periodSets = [set(byPeriod) for byPeriod in per.values() if byPeriod]
    if not periodSets:
        return []
    common = set.intersection(*periodSets) if len(periodSets) > 1 else periodSets[0]
    pool = common or set().union(*periodSets)
    return [sorted(pool, reverse=True)[0]] if pool else []


def _compareCellsResult(
    codes: list[str],
    *,
    statement: str,
    freq: str,
    scope: str | None,
    marketNs: str,
    period: list[str] | str | None,
) -> tuple[pl.DataFrame, list[str]]:
    """N사 재무 frame 과 실제 period 를 함께 만든다.

    이름 정렬(IS 6%)이 라벨 drift 로 실패하는 곳을 acode(IS 37%+)가 해소. scope 고정(자동폴백 금지 —
    연결↔별도 혼선 차단), freq 일치(분기↔연간 기간 착시 차단), 원 환산(단위 착시 차단)을 강제한다.
    """
    scope = _normScope(scope) or "consolidated"  # 비교는 scope 명시 고정
    targetLabels, panelPeriods = _financeTargets(period, freq)
    per: dict[str, dict[str, dict[str, tuple[str, float]]]] = {}
    for c in codes:
        cc = _companyCellsByPeriod(
            c, statement, freq, scope, marketNs, targetLabels=targetLabels, panelPeriods=panelPeriods
        )
        if cc:
            per[c] = cc
    targets = targetLabels or _chooseFinanceTargets(per)
    if not targets:
        return pl.DataFrame(), []
    single = len(targets) == 1
    # acode union (첫 등장 라벨 대표 — acode 가 정체성, label 은 표시용)
    reprLabel: dict[str, str] = {}
    order: list[str] = []
    for c in codes:
        for p in targets:
            for ac, (lab, _v) in per.get(c, {}).get(p, {}).items():
                if ac not in reprLabel:
                    reprLabel[ac] = lab
                    order.append(ac)
    if not order:
        return pl.DataFrame(), targets
    rows: list[dict[str, object]] = []
    for ac in order:
        row: dict[str, object] = {"acode": ac, "label": reprLabel[ac], "scope": scope}
        for c in codes:
            for p in targets:
                key = c if single else f"{c}{_SEP}{p}"
                row[key] = per.get(c, {}).get(p, {}).get(ac, (None, None))[1]  # 원 환산값 or None(honest-gap)
        rows.append(row)
    return pl.DataFrame(rows), targets


def _companyLong(code: str, wide: pl.DataFrame, scope: str | None) -> pl.DataFrame | None:
    """한 회사 wide → long (joinKey·code·식별·period·value). content-bearing(비빈 셀)만."""
    if scope is not None and "scope" in wide.columns:
        wide = wide.filter(pl.col("scope") == scope)
    if wide.is_empty():
        return None
    periodCols = [c for c in wide.columns if isPeriodColumn(c)]
    idCols = [c for c in _IDENT if c in wide.columns]
    if not periodCols or "disclosureKey" not in wide.columns:
        return None
    # keyed = (disclosureKey, scope, leafType); narrative = 회사·행 고유(절대 병합 안 됨).
    scopeCol = pl.col("scope").cast(pl.Utf8).fill_null("") if "scope" in idCols else pl.lit("")
    leafCol = pl.col("leafType").cast(pl.Utf8).fill_null("") if "leafType" in idCols else pl.lit("")
    keyed = pl.col("disclosureKey").cast(pl.Utf8) + _SEP + scopeCol + _SEP + leafCol
    narr = pl.lit(f"NARR{_SEP}{code}{_SEP}") + pl.col("_ri").cast(pl.Utf8)
    wide = wide.with_row_index("_ri").with_columns(
        pl.lit(code).alias("_code"),
        pl.when(pl.col("disclosureKey").is_not_null()).then(keyed).otherwise(narr).alias("_joinKey"),
    )
    long = wide.unpivot(
        index=["_joinKey", "_code", *idCols], on=periodCols, variable_name="_period", value_name="_value"
    )
    return long.filter(pl.col("_value").is_not_null() & (pl.col("_value").str.strip_chars() != ""))


def _matchTopic(df: pl.DataFrame, topic: str) -> pl.DataFrame:
    """topic 필터 — disclosureKey exact | native 표(BS/IS/CF/CIS/EF/SCE) | sectionLeaf/blockLeaf substring.

    ``Panel.__call__`` 의 key 흡수 규칙과 동형 (topic vs disclosureKey 인자 분리 금지).
    """
    up = topic.upper()
    natives = {"BS", "IS", "CF", "CIS", "EF", "SCE"}
    dk = pl.col("disclosureKey").cast(pl.Utf8)
    mask = dk == topic
    if up in natives:
        mask = mask | (dk == up)
    for c in ("sectionLeaf", "blockLeaf"):
        if c in df.columns:
            mask = mask | pl.col(c).cast(pl.Utf8).str.contains(topic, literal=True)
    return df.filter(mask.fill_null(False))


def _orderedCellColumns(present: list[str], targets: list[str], *, single: bool) -> list[str]:
    """출력 셀 컬럼 순서 — 단일=회사, 다기간=회사(codes 순)×기간(최신순)."""
    if single:
        return list(present)
    periods = sortPeriods(list(dict.fromkeys(targets)), descending=True)
    return [f"{code}{_SEP}{period}" for code in present for period in periods]


def _ensureCellColumns(out: pl.DataFrame, ordered: list[str]) -> pl.DataFrame:
    """topic 필터 후 한 회사가 전부 결손이어도 비교 컬럼을 null 로 보존."""
    missing = [c for c in ordered if c not in out.columns]
    if not missing:
        return out
    return out.with_columns([pl.lit(None, dtype=pl.Utf8).alias(c) for c in missing])


def _rowLongFrame(
    codes: list[str],
    *,
    marketNs: str,
    scopeVal: str | None,
    period: list[str] | str | None,
    topic: str | None,
) -> tuple[pl.DataFrame | None, list[str]]:
    """row 모드 입력 panel 을 topic 적용 long frame 으로 정규화."""
    periodArg = [period] if isinstance(period, str) else period  # readWide 파일 prune
    longs: list[pl.DataFrame] = []
    present: list[str] = []
    for c in codes:
        wide = readWide(c, marketNs=marketNs, periods=periodArg, tag=False)
        if wide is None or wide.is_empty():
            continue
        lg = _companyLong(c, wide, scopeVal)
        if lg is not None and not lg.is_empty():
            longs.append(lg)
            present.append(c)
    if not longs:
        return None, present
    long = pl.concat(longs, how="diagonal_relaxed")
    if topic:
        # topic 이 있을 때는 period 선택 전에 먼저 좁힌다. 전체 패널 최신 공통분기가
        # topic 을 담지 않으면 직전 사업보고서 주석이 빈 표로 사라진다.
        long = _matchTopic(long, topic)
        if long.is_empty():
            return None, present
    return long, present


def _chooseRowTargets(long: pl.DataFrame, present: list[str], period: list[str] | str | None) -> list[str]:
    """row 모드 실제 비교 시점 — 명시 period 또는 최신 공통(없으면 union 최신)."""
    if isinstance(period, str):
        return [period]
    if isinstance(period, list):
        return sortPeriods(list(dict.fromkeys(period)), descending=True)
    perByCode = {c: set(long.filter(pl.col("_code") == c)["_period"].to_list()) for c in present}
    common = set.intersection(*perByCode.values()) if perByCode else set()
    pool = common or set().union(*perByCode.values())
    return [sortPeriods(list(pool), descending=True)[0]] if pool else []


def _normRowPeriod(period: list[str] | str | None) -> list[str] | str | None:
    """row 모드 period 입력을 panel 열 라벨로 정규화 — 연도 ``YYYY`` → ``YYYYQ4``.

    row panel 열은 항상 ``YYYYQn`` 이라 bare 연도는 어느 열과도 안 맞아 조용히 빈 결과가 됐다.
    finance 경로(``_financePanelPeriod``)와 동형으로 연도를 연말 분기로 정규화한다.
    """
    if period is None:
        return None
    if isinstance(period, str):
        return _financePanelPeriod(period)
    return [_financePanelPeriod(p) for p in period]


def _compareRows(
    codes: list[str],
    *,
    marketNs: str,
    scopeVal: str | None,
    period: list[str] | str | None,
    topic: str | None,
) -> tuple[pl.DataFrame, list[str], str | None]:
    """row 모드 compare 결과와 실제 period/emptyReason 을 한 번에 만든다."""
    period = _normRowPeriod(period)
    long, present = _rowLongFrame(codes, marketNs=marketNs, scopeVal=scopeVal, period=period, topic=topic)
    if long is None:
        if topic:
            unfiltered, _ = _rowLongFrame(codes, marketNs=marketNs, scopeVal=scopeVal, period=period, topic=None)
            return pl.DataFrame(), [], "noPanelRows" if unfiltered is None else "topicFilteredEmpty"
        return pl.DataFrame(), [], "noPanelRows"

    targets = _chooseRowTargets(long, present, period)
    if not targets:
        return pl.DataFrame(), [], "noComparablePeriods"
    long = long.filter(pl.col("_period").is_in(targets))
    if long.is_empty():
        return pl.DataFrame(), targets, "periodFilteredEmpty"

    single = len(targets) == 1
    long = long.with_columns((pl.col("_code") if single else pl.col("_code") + _SEP + pl.col("_period")).alias("_cell"))

    # 대표 식별(같은 joinKey 의 라벨 drift → 첫 등장 1개) + 셀 pivot.
    idCols = [c for c in _IDENT if c in long.columns]
    reprIdent = long.group_by("_joinKey", maintain_order=True).agg([pl.col(c).first() for c in idCols])
    grid = long.pivot("_cell", index="_joinKey", values="_value", aggregate_function="first")
    out = reprIdent.join(grid, on="_joinKey", how="left").drop("_joinKey")

    # 행 정렬 — canonical chapter rank → 절 번호 → sectionLeaf → disclosureKey (셀 컬럼은 보존).
    out = out.with_columns(
        canonicalRankExpr("chapter").alias("_cr") if "chapter" in out.columns else pl.lit(0).alias("_cr"),
        pl.col("sectionLeaf").cast(pl.Utf8).str.extract(r"^\s*(\d+)", 1).cast(pl.Int64).alias("_sn")
        if "sectionLeaf" in out.columns
        else pl.lit(None, dtype=pl.Int64).alias("_sn"),
    )
    sortCols = ["_cr", "_sn", *([c for c in ("sectionLeaf", "disclosureKey") if c in out.columns])]
    out = out.sort(sortCols, nulls_last=True).drop("_cr", "_sn")

    # 컬럼 순서 — 식별 먼저, 셀은 회사(codes 순) → 기간 최신순. topic 필터 후 한 회사가 전부 결손이어도
    # 컬럼을 null 로 보존해야 honest-gap 이 화면/API 에 남는다.
    ordered = _orderedCellColumns(codes, targets, single=single)
    out = _ensureCellColumns(out, ordered)
    return out.select([*idCols, *ordered]), targets, None


@dataclass
class _Resolved:
    """compare 입력 해소 결과 — 정규화·검증·시장·모드 SSOT (compare/diagnostics 공유)."""

    codes: list[str]
    topic: str | None
    period: list[str] | str | None
    scope: str | None
    freq: str
    marketNs: str
    mode: str  # "finance" | "row"


def _resolveInputs(
    codes: list[str] | str,
    *,
    topic: str | None,
    period: list[str] | str | None,
    scope: str | None,
    freq: str,
) -> _Resolved:
    """compare 입력 정규화·계약 가드 SSOT. 위반 시 ValueError (compare/diagnostics 동일 메시지)."""
    norm = _normCodes(codes)
    if len(norm) < 2:
        raise ValueError(
            "compare 는 2개 이상 종목코드가 필요합니다 (예: dartlab.compare(['005930','000660'])). "
            "단일 종목은 Company(code).panel 사용."
        )
    if len(norm) > _MAX_COMPARE:
        raise ValueError(f"compare 는 최대 {_MAX_COMPARE}개 종목까지만 지원합니다.")
    periodVal = _normPeriod(period)
    topicVal = _normTopic(topic)
    freqVal = _normFreq(freq)
    scopeVal = _normScope(scope)
    markets = {detectMarket(c) for c in norm}
    if len(markets) > 1:
        raise ValueError(
            f"KO↔US 혼합 비교는 불가 ({markets}). 같은 시장 종목끼리만 — cross-market 은 후속(crossMarket)."
        )
    marketNs = "us" if markets == {"US"} else "kr"
    mode = "finance" if topicVal and topicVal.lower() in _FIN_KEYS else "row"
    if mode == "finance" and marketNs not in ("kr", "us"):
        raise ValueError(f"재무 compare 미지원 시장: {marketNs}.")
    return _Resolved(
        codes=norm, topic=topicVal, period=periodVal, scope=scopeVal, freq=freqVal, marketNs=marketNs, mode=mode
    )


def _runCompare(r: _Resolved) -> tuple[pl.DataFrame, list[str], str | None]:
    """해소된 입력으로 finance/row 실행 — (df, resolvedPeriods, emptyReason). compare/diagnostics 공유."""
    if r.mode == "finance":
        # 재무 토픽 = 셀(항목) 단위 비교(acode 정렬 + 원 환산). scope 명시 고정(자동폴백 금지).
        scope = r.scope or "consolidated"
        df, periods = _compareCellsResult(
            r.codes, statement=str(r.topic).lower(), freq=r.freq, scope=scope, marketNs=r.marketNs, period=r.period
        )
        return df, periods, ("insufficientFinanceCells" if df.height == 0 else None)
    return _compareRows(r.codes, marketNs=r.marketNs, scopeVal=r.scope, period=r.period, topic=r.topic)


def compare(
    codes: list[str] | str,
    *,
    topic: str | None = None,
    period: list[str] | str | None = None,
    scope: str | None = None,
    freq: str = "quarter",
) -> pl.DataFrame:
    """N 회사 공시 panel 을 회사 간 비교 wide 로 정렬한다.

    Args:
        codes: 종목코드 2~6개. KR은 6자리 코드, US는 ticker.
        topic: None이면 전체 격자. ``bs/is/cf/cis/sce``는 재무 셀 비교 모드.
        period: None, ``"2025Q4"``, ``"2025"``, 또는 리스트.
        scope: None, ``"consolidated"``, ``"separate"``, ``"연결"``, ``"별도"``.
        freq: 재무 셀모드 입도. ``"quarter"``/``"year"``/``"ytd"``.

    Returns:
        ``pl.DataFrame`` — 식별 컬럼 + 회사별 셀. 다기간 열은 ``{code}␟{period}``.

    Raises:
        ValueError: 대상 수, code/period/scope/freq 오타, 시장 혼합, US finance compare 시도.

    Example:
        >>> import dartlab
        >>> dartlab.compare(["005930", "000660"], topic="재고")  # doctest: +SKIP
    """
    df, _, _ = _runCompare(_resolveInputs(codes, topic=topic, period=period, scope=scope, freq=freq))
    return df


def _periodValue(period: list[str] | str | None) -> list[str] | None:
    """diagnostics 용 period 입력 정규화."""
    if isinstance(period, str):
        return [period]
    if period is None:
        return None
    return [str(p) for p in period]


def _isFilled(value: object) -> bool:
    """셀 값 존재 판정 — 결손 0 채움 없이 빈 문자열만 결손."""
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    return True


def _cellColumns(columns: list[str], codes: list[str]) -> list[str]:
    """compare 출력에서 회사 셀 컬럼만 추출."""
    out: list[str] = []
    for col in columns:
        if col in codes or any(col.startswith(f"{code}{_SEP}") for code in codes):
            out.append(col)
    return out


def _identityColumns(columns: list[str], cellCols: list[str]) -> list[str]:
    """compare 출력에서 회사 셀을 제외한 행 식별 컬럼만 추출."""
    cellSet = set(cellCols)
    return [col for col in columns if col not in cellSet]


def _cellColumnShape(cellCols: list[str]) -> str:
    """회사 셀 컬럼 형태 — empty/singlePeriod/multiPeriod."""
    if not cellCols:
        return "empty"
    return "multiPeriod" if any(_SEP in col for col in cellCols) else "singlePeriod"


def _codeHasValue(row: dict[str, object], code: str) -> bool:
    """단일 행에서 특정 회사가 직접/다기간 셀 중 하나라도 값을 갖는지."""
    if _isFilled(row.get(code)):
        return True
    prefix = f"{code}{_SEP}"
    return any(col.startswith(prefix) and _isFilled(value) for col, value in row.items())


def _shareStats(df: pl.DataFrame, codes: list[str]) -> tuple[list[str], int, int, int]:
    """회사별 존재와 shared/partial/solo 행수를 계산."""
    presentSeen = {code: False for code in codes}
    sharedRows = 0
    partialRows = 0
    soloRows = 0
    for row in df.iter_rows(named=True):
        filledCodes = 0
        for code in codes:
            if _codeHasValue(row, code):
                presentSeen[code] = True
                filledCodes += 1
        if filledCodes == len(codes):
            sharedRows += 1
        elif filledCodes >= 2:
            partialRows += 1
        elif filledCodes == 1:
            soloRows += 1
    presentCodes = [code for code in codes if presentSeen[code]]
    return presentCodes, sharedRows, partialRows, soloRows


def _compareDiagnostics(
    codes: list[str] | str,
    *,
    topic: str | None = None,
    period: list[str] | str | None = None,
    scope: str | None = None,
    freq: str = "quarter",
) -> dict[str, object]:
    """N 회사 compare 실행 상태를 내부 소비자/테스트용으로 진단한다.

    Args:
        codes: 비교할 종목코드 2~6개.
        topic: compare 와 동일한 topic.
        period: compare 와 동일한 period 입력.
        scope: compare 와 동일한 연결/별도 scope.
        freq: compare 와 동일한 재무 셀모드 입도.

    Returns:
        ``dict[str, object]`` — 입력 정규화, 시장, 실행 모드, 출력 행/열,
        회사별 존재, resolvedPeriods, emptyReason 등을 담은 payload.

    Raises:
        없음. 입력 계약 오류도 ``ok=False`` 와 ``reason="invalidInput"`` 으로 반환한다.

    공개 호출계약은 ``dartlab.compare(...)`` 하나다. 이 helper 는 뷰어/엔진이
    DataFrame 컬럼을 재추론하지 않아야 할 때 내부에서만 쓴다.
    """
    displayCodes = _displayCodes(codes)
    diag: dict[str, object] = {
        "ok": False,
        "reason": None,
        "mode": None,
        "codes": displayCodes,
        "requestedCodeCount": len(displayCodes),
        "maxCompare": _MAX_COMPARE,
        "marketNs": None,
        "topic": topic,
        "period": None,
        "resolvedPeriods": None,
        "scope": scope,
        "freq": freq,
        "rowCount": 0,
        "columns": [],
        "identityColumns": [],
        "cellColumns": [],
        "cellColumnShape": "empty",
        "valueUnit": None,
        "presentCodes": [],
        "missingCodes": displayCodes,
        "sharedRows": 0,
        "partialRows": 0,
        "soloRows": 0,
        "emptyReason": None,
        "error": None,
    }
    try:
        r = _resolveInputs(codes, topic=topic, period=period, scope=scope, freq=freq)
        df, resolvedPeriods, emptyReason = _runCompare(r)
    except ValueError as exc:
        diag["reason"] = "invalidInput"
        diag["emptyReason"] = "invalidInput"
        diag["error"] = str(exc)
        return diag

    actualScope = (r.scope or "consolidated") if r.mode == "finance" else r.scope
    columns = list(df.columns)
    cellCols = _cellColumns(columns, r.codes)
    presentCodes, sharedRows, partialRows, soloRows = _shareStats(df, r.codes)
    rowCount = df.height

    diag.update(
        {
            "ok": rowCount > 0,
            "reason": "ready" if rowCount > 0 else "emptyResult",
            "mode": r.mode,
            "codes": r.codes,
            "requestedCodeCount": len(r.codes),
            "marketNs": r.marketNs,
            "topic": r.topic,
            "period": _periodValue(r.period),
            "resolvedPeriods": resolvedPeriods,
            "scope": actualScope,
            "freq": r.freq,
            "rowCount": rowCount,
            "columns": columns,
            "identityColumns": _identityColumns(columns, cellCols),
            "cellColumns": cellCols,
            "cellColumnShape": _cellColumnShape(cellCols),
            "valueUnit": (("USD" if r.marketNs == "us" else "KRW") if r.mode == "finance" else None),
            "presentCodes": presentCodes,
            "missingCodes": [c for c in r.codes if c not in presentCodes],
            "sharedRows": sharedRows,
            "partialRows": partialRows,
            "soloRows": soloRows,
            "emptyReason": emptyReason,
        }
    )
    return diag


__all__ = ["compare"]
