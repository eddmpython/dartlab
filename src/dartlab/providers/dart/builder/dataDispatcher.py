"""DART Company 의 finance 통계표 dispatch core.

공개 ``c.show`` + docs 농장 은퇴 후 finance-only — ``_showImpl`` 은 panel facade(``c.panel``)
가 주입하는 강한 소스 callable 이며 BS/IS/CF/CIS/SCE/ratios 만 dispatch. 정형 비재무·sections
토픽은 panel raw 공시 검색이 표면(facade 폴백). report/finance source 는 viewer(textDocument)
가 ``showReportTopic``/``showFinanceTopic`` 으로 직접 소비.

Module-level functions:
    showImpl              — 강한 소스 진입점 (panel facade 주입 callable)
    showFinanceStatement  — finance topic (BS/IS/CF/CIS/SCE/ratios/ratioSeries/sceMatrix)
    showFinanceTopic      — finance source 실제 데이터 (viewer)
    traceFinanceTopic     — finance authoritative provenance
    showReportTopic       — report source 실제 데이터 (viewer)
    reportFrame           — report apiType DataFrame
    reportFrameInner      — report apiType 정제 DataFrame
    isStrongTopic         — panel facade 강한 소스 라우팅 SSOT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import polars as pl

from dartlab.providers.dart.checks import _isPeriodColumn

if TYPE_CHECKING:
    from dartlab.providers.dart.company import Company


SHOW_FINANCE_TOPICS = frozenset({"BS", "IS", "CF", "CIS", "SCE", "ratios", "ratioSeries", "sceMatrix"})
FINANCE_CLEAN_TOPICS = frozenset({"IS", "BS", "CIS", "CF", "SCE"})


# ── finance source ─────────────────────────────────────────────────


def showFinanceTopic(
    company: Company,
    topic: str,
    *,
    period: str | None = None,
    freq: str = "Q",
    scope: str = "consolidated",
) -> pl.DataFrame | None:
    """finance source topic 의 실제 데이터 반환 (show 진입점).

    ``c.panel("IS", freq="Y", scope="separate")`` 같은 사용자 호출이 여기로 들어와서
    freq/scope 에 따라 빌드.

    Args:
        company: Company 인스턴스.
        topic: BS/IS/CF/CIS/SCE/ratios/ratioSeries/sceMatrix 중 하나.
        period: 단일 기간 필터.
        freq: ``"Q"``/``"Y"``/``"YTD"``.
        scope: ``"consolidated"``/``"separate"``.

    Returns:
        wide DataFrame 또는 None.

    Raises:
        없음.

    Example:
        >>> showFinanceTopic(c, "IS", freq="Y")
    """
    if topic == "ratios":
        return company._applyPeriodFilter(company._buildRatios(), period)
    if topic == "ratioSeries":
        # dict 구조 — DataFrame 으로 변환 어려움. None 반환 + 사용자 안내.
        # 사용자는 c.panel("ratios") DataFrame 사용 권장.
        return None
    if topic in {"BS", "IS", "CF", "CIS"}:
        df = company._financeOrDocsStatement(topic, freq=freq, scope=scope)
        return company._applyPeriodFilter(df, period) if df is not None else None
    if topic == "SCE":
        return company._applyPeriodFilter(company._sce(), period)
    if topic == "sceMatrix":
        # 3차원 dict — DataFrame 변환 X. 사용자는 SCE topic.
        return None
    return None


def traceFinanceTopic(company: Company, topic: str, *, period: str | None = None) -> dict[str, Any] | None:
    """finance authoritative topic provenance 를 facts 빌드 없이 직접 계산.

    Args:
        company: Company 인스턴스.
        topic: BS/IS/CF/CIS/SCE 중 하나.
        period: 특정 기간 필터.

    Returns:
        ``{topic, period, primarySource, fallbackSources, ...}`` dict 또는 None.

    Raises:
        없음.

    Example:
        >>> traceFinanceTopic(c, "BS", period="2024")
    """
    from dartlab.providers.dart.sectionPeriod import rawPeriod

    requestedPeriod = rawPeriod(period) if isinstance(period, str) else period
    rows: list[tuple[str, str]] = []

    def collect(series: dict[str, list[Any]] | None, years: list[Any], payloadTopic: str) -> None:
        """series → rows in-place 축적 — period 필터 적용.

        Args:
            series: ``{item: [value...], ...}`` dict 또는 None.
            years: period 리스트.
            payloadTopic: payloadRef prefix.

        Returns:
            None (in-place ``rows`` mutation).

        Raises:
            없음.

        Example:
            >>> collect({"sales": [1000]}, [2024], "IS")  # nested function example
        """
        if not series:
            return
        for item, values in series.items():
            for idx, year in enumerate(years):
                if requestedPeriod is not None and str(year) != requestedPeriod:
                    continue
                value = values[idx] if idx < len(values) else None
                if value is None:
                    continue
                rows.append((f"finance:{payloadTopic}:{item}", f"{item}={value}"))

    if topic in {"BS", "IS", "CF"}:
        annual = company._buildFinanceSeries(freq="Y")
        if annual is None:
            return None
        series, years = annual
        collect(series.get(topic), years, topic)
    elif topic == "CIS":
        annual = company._financeCisAnnual()
        if annual is None:
            return None
        series, years = annual
        collect(series.get("CIS"), years, "CIS")
    elif topic == "SCE":
        annual = company._sceSeriesAnnual()
        if annual is None:
            return None
        series, years = annual
        collect(series.get("SCE"), years, "SCE")
    else:
        return None

    if not rows:
        return None

    payloadRef, summary = rows[0]
    return {
        "topic": topic,
        "period": requestedPeriod,
        "primarySource": "finance",
        "fallbackSources": [],
        "selectedPayloadRef": payloadRef,
        "availableSources": [
            {
                "source": "finance",
                "rows": len(rows),
                "payloadRef": payloadRef,
                "summary": summary,
                "priority": 300,
            }
        ],
        "whySelected": "finance authoritative priority",
    }


# ── report source ──────────────────────────────────────────────────


def showReportTopic(
    company: Company, topic: str, *, period: str | None = None, raw: bool = False
) -> pl.DataFrame | None:
    """report source topic 의 실제 데이터 반환.

    Args:
        company: Company 인스턴스.
        topic: report topic 이름 (예: ``"dividend"``).
        period: 기간 필터.
        raw: True 면 영문 컬럼 그대로, False 면 한글 매핑.

    Returns:
        DataFrame 또는 None.

    Raises:
        없음.

    Example:
        >>> showReportTopic(c, "dividend", period="2024")
    """
    return company._applyPeriodFilter(reportFrame(company, topic, raw=raw), period)


def reportFrame(company: Company, topic: str, *, raw: bool = False) -> pl.DataFrame | None:
    """report apiType DataFrame — topic → apiType 변환 + 정제.

    Args:
        company: Company 인스턴스.
        topic: report topic 이름.
        raw: True 면 영문 컬럼 그대로.

    Returns:
        정제 DataFrame 또는 None (apiType 미존재 / report 부재).

    Raises:
        없음 (Polars exception 모두 None 반환).

    Example:
        >>> reportFrame(c, "dividend")
    """
    if company._report is None:
        return None
    from dartlab.providers.dart.company import _apiTypeForTopic

    apiType = _apiTypeForTopic(topic)
    try:
        if apiType not in company._report.apiTypes:
            return None
        return reportFrameInner(company, apiType, topic, raw=raw)
    except (
        pl.exceptions.ColumnNotFoundError,
        pl.exceptions.InvalidOperationError,
        pl.exceptions.SchemaError,
        RuntimeError,
    ):
        return None


def reportFrameInner(company: Company, apiType: str, topic: str, *, raw: bool = False) -> pl.DataFrame | None:
    """report apiType 의 정제된 DataFrame 반환 (``reportAccessor`` 위임).

    Args:
        company: Company 인스턴스 (stockCode 추출용).
        apiType: OpenDART apiType 키.
        topic: topic 이름 (호환용).
        raw: True 면 영문 컬럼.

    Returns:
        정제 DataFrame 또는 None.

    Raises:
        없음.

    Example:
        >>> reportFrameInner(c, "dividend", "dividend")
    """
    from dartlab.providers.dart.accessor.reportAccessor import reportFrameInner as _reportFrameInner

    return _reportFrameInner(company.stockCode, apiType, topic, raw=raw)


# ── show 진입점 ────────────────────────────────────────────────────


def showImpl(
    company: Company,
    topic: str,
    block: int | None = None,
    *,
    period: str | list[str] | None = None,
    freq: str = "Q",
    scope: str = "consolidated",
    raw: bool = False,
) -> pl.DataFrame | None:
    """topic 의 데이터를 반환 — 사용자 ``c.show`` 의 내부 구현.

    Q1.5 dispatcher: alias 해석 → 5 사례 분기 (list period / segments / finance /
    notes / sections).

    Args:
        company: Company 인스턴스.
        topic: topic 이름 또는 alias.
        block: blockOrder (None 이면 전체).
        period: 단일 기간 또는 기간 리스트 (vertical 변환).
        freq: ``"Q"``/``"Y"``/``"YTD"``.
        scope: ``"consolidated"``/``"separate"``.
        raw: True 면 영문 컬럼.

    Returns:
        DataFrame 또는 None.

    Raises:
        없음.

    Example:
        >>> showImpl(c, "IS", freq="Y", scope="separate")
    """
    from dartlab.providers.dart.builder.dataShapeUtils import transposeToVertical
    from dartlab.providers.dart.company import _resolveTopic

    # 공개 show/docs 농장 은퇴 — showImpl 은 finance 통계표(BS/IS/CF/CIS/SCE/ratios)만 dispatch.
    # 정형 비재무·report·sections·notes·segments 토픽은 panel raw 공시 검색이 표면(facade 폴백) → None.
    topic = _resolveTopic(topic)

    if isinstance(period, list):
        wide = company._showImpl(topic, block, freq=freq, scope=scope, raw=raw)
        if wide is None or not isinstance(wide, pl.DataFrame):
            return None
        return transposeToVertical(wide, period)

    if topic in SHOW_FINANCE_TOPICS:
        return showFinanceStatement(company, topic, block, period=period, freq=freq, scope=scope)

    return None


def showFinanceStatement(
    company: Company,
    topic: str,
    block: int | None,
    *,
    period: str | None,
    freq: str,
    scope: str,
) -> pl.DataFrame | None:
    """finance topic (BS/IS/CF/CIS/SCE/ratios/ratioSeries/sceMatrix) 조회.

    ``block`` 이 지정되면 (not None and not 0) None. BS/IS/CIS/CF/SCE 는 clean 적용.

    Args:
        company: Company 인스턴스.
        topic: finance topic.
        block: blockOrder (None / 0 이외는 None 반환).
        period: 기간 필터.
        freq: ``"Q"``/``"Y"``/``"YTD"``.
        scope: ``"consolidated"``/``"separate"``.

    Returns:
        wide DataFrame 또는 None.

    Raises:
        없음.

    Example:
        >>> showFinanceStatement(c, "IS", None, period="2024Q4", freq="Q", scope="consolidated")
    """
    from dartlab.providers.dart.builder.dataShapeUtils import cleanFinanceDataFrame

    if block not in (None, 0):
        return None
    result = showFinanceTopic(company, topic, period=period, freq=freq, scope=scope)
    if topic in FINANCE_CLEAN_TOPICS and isinstance(result, pl.DataFrame) and result.width > 0:
        result = cleanFinanceDataFrame(result, topic)
    return result if isinstance(result, pl.DataFrame) else None


def isStrongTopic(topic: str) -> bool:
    """topic 이 finance/notes/report 강한 소스인지 — c.panel facade 주입 라우팅 SSOT.

    panel facade(``c.panel``)가 ``c.panel("IS")`` 같은 호출을 raw 공시(panel) vs 강한 소스
    (finance/report — XBRL 정규화 숫자·정형 공시)로 가른다. 본 함수가 그 단일 판정 — show 와
    동일 분류 기준(``SHOW_FINANCE_TOPICS`` · ``_NOTES_DISPATCH`` · registry apiType)을 재사용해
    panel·show 가 한 SSOT 를 공유한다(분류 중복 0).

    Args:
        topic: 토픽 이름 (BS/IS/CF/ratios/inventory/dividend/canonicalKey/한글 섹션명 등).

    Returns:
        True 면 강한 소스(finance/notes/report — c.show 위임 대상), False 면 raw 공시(panel 행).

    Raises:
        없음 — registry 조회 실패는 False.

    Example:
        >>> isStrongTopic("IS")  # doctest: +SKIP
        True
        >>> isStrongTopic("NT_D826380")  # doctest: +SKIP  (canonicalKey → raw panel)
        False

    SeeAlso:
        - ``showImpl`` — 강한 소스의 실제 dispatch (finance/notes/report).
        - ``providers.dart.panel.Panel.__call__`` — 본 판정을 facade 주입으로 받아 라우팅.

    Requires:
        - dartlab. registry (report 판정).

    Capabilities:
        - panel·show 분류 SSOT — finance(BS/IS/…) · notes(inventory/…) · report(dividend/…) 식별.

    Guide:
        - facade(Company.panel)가 ``_strongFn`` 으로 주입. panel.py 는 직접 import 안 함(주입만).

    AIContext:
        - 순수 판정 — finance set ∪ notes dispatch ∪ (apiType 매핑되는) report.

    LLM Specifications:
        AntiPatterns:
            - panel.py 에서 직접 import 금지 — facade 가 _strongFn 으로 주입(panel 은 finance 모름).
            - 분류 중복 정의 금지 — SHOW_FINANCE_TOPICS·_NOTES_DISPATCH SSOT 재사용.
        OutputSchema:
            - ``bool``.
        Prerequisites:
            - registry (report apiType 판정).
        Freshness:
            - registry 변경 시 반영.
        Dataflow:
            - _resolveTopic → finance set / notes dispatch / apiType 매핑 → bool.
        TargetMarkets:
            - KR (DART). US 후속.
    """
    from dartlab.providers.dart.company import _getModuleEntries, _resolveTopic
    from dartlab.providers.dart.notes import _NOTES_DISPATCH

    t = _resolveTopic(topic)
    if t in SHOW_FINANCE_TOPICS or t in _NOTES_DISPATCH:
        return True
    # report/notes/finance category = 정규화된 강한 소스 (dividend 등 정형 공시). disclosure(서술
    # docs)·canonicalKey·한글 섹션명은 raw 공시(panel 본분) → False.
    strongCats = {"finance", "report", "notes"}
    return any(e.name == t and getattr(e, "category", None) in strongCats for e in _getModuleEntries())
