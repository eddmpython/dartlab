"""DART Company 의 scan-related 메서드 backend.

Company.network / governance / workforce / capital / debt 5 진입점은 모두
``dartlab.scan`` 의 프리빌드 결과를 조회한다. Company facade 가 본 모듈의 build*
함수에 thin delegate.

Module-level helper:
    _ensureNetwork / _ensureGovernance / _ensureWorkforce / _ensureCapital /
    _ensureDebt 는 ``Company._cache`` 에 prebuild 결과 lazy 저장.

Module-level builders:
    buildScanNetwork / buildScanGovernance / buildScanWorkforce /
    buildScanCapital / buildScanDebt — 각 진입점의 본체 구현.

분리 이유: company.py 5040 LOC 의 facade 책임 분산. scan-related 영역 ~450 LOC
가 외부 의존 (dartlab.scan.* prebuild) 이 강해 별도 모듈 분리가 자연스럽다.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

import polars as pl

from dartlab.core.memory import _CACHE_MISSING
from dartlab.core.polarsUtil import isEmptyDf

if TYPE_CHECKING:
    from dartlab.providers.dart.company import Company


# ── ensure helpers (Company._cache lazy 저장) ──────────────────────
# atomic lazy build — cache.get + 로컬 var. set 직후 BoundedCache 의 FATAL 분기
# (just_set_key 보존 없음) 가 unpinned 전부 evict 해도 로컬 var 영향 없음.
# 5 질문 batch audit 의 ``tool debt failed: '_debt'`` race window fix.


@lru_cache(maxsize=1)
def _marketGraph() -> tuple[dict, dict]:
    """시장 전체 출자 관계 그래프 (data, full). 프로세스 안에서 한 번만 만든다.

    입력이 회사와 무관한 시장 단위 파이프라인이고 실측 737 초가 걸린다 (노드 1,289,
    순환출자 49). 회사별로 다시 만들 이유가 없다. 로컬 parquet 를 읽어 만드는 순수
    계산이라 결과를 프로세스 안에 들고 있어도 되며 굽는 산출물은 남기지 않는다.
    """
    import importlib

    network = importlib.import_module("dartlab.scan.network")
    data = network.buildGraph(verbose=False)
    return data, network.exportFull(data)


def _ensureNetwork(company: Company) -> tuple[dict, dict] | None:
    """network 파이프라인 캐싱 → (data, full).

    Company 캐시는 같은 인스턴스 안에서의 재조회를 막고, 그 아래 프로세스 캐시가 회사가
    바뀔 때의 재빌드를 막는다. 예전에는 앞엣것만 있어 회사마다 12 분씩 다시 만들었다.
    """
    data = company._cache.get("_network_data", _CACHE_MISSING)
    full = company._cache.get("_network_full", _CACHE_MISSING)
    if data is _CACHE_MISSING or full is _CACHE_MISSING:
        data, full = _marketGraph()
        company._cache["_network_data"] = data
        company._cache["_network_full"] = full
    return data, full


def buildNetworkEgo(company: Company, *, hops: int = 1) -> dict | None:
    """회사 중심 ego 관계망을 직렬화 가능한 dict 로 낸다. 그래프가 없으면 None.

    ``_ensureNetwork`` 는 이 모듈 안쪽 캐시 헬퍼다. 예전에는 Company 메서드였고 서버
    엔드포인트가 ``company._ensureNetwork()`` 로 불렀는데, 모듈 함수로 옮겨진 뒤 그 자리가
    안 고쳐졌다. 서버는 AttributeError 를 흡수해 모든 회사에 관계망 없음을 돌려주었다.
    그래프 쌍의 주인이 여기이므로 이름 있는 진입점을 두어 소비자가 안쪽을 짚지 않게 한다.

    Capabilities:
        - 그래프 prebuild 캐시 후 exportEgo 로 노드/엣지 dict 산출.

    Args:
        company: Company 인스턴스.
        hops: ego 깊이. 기본 1.

    Returns:
        ``exportEgo`` 결과 dict. 그래프 prebuild 가 없으면 ``None``.

    Raises:
        없음이 보장되지는 않는다. 그래프 빌드 예외는 그대로 올라간다.

    Example:
        >>> buildNetworkEgo(company, hops=2) is None or True
        True

    SeeAlso:
        - :func:`dartlab.scan.network.export.exportEgo` : ego 뷰 본체.
        - :func:`buildScanNetwork` : 같은 그래프의 사람용 view.

    AIContext:
        관계망 질문의 JSON 응답 source. 서버 ``/api/company/{code}/network`` 가 소비.
    """
    import importlib

    result = _ensureNetwork(company)
    if result is None:
        return None
    data, full = result
    exportEgo = importlib.import_module("dartlab.scan.network").exportEgo
    return exportEgo(data, full, company.stockCode, hops=hops)


_SCAN_AXES: dict[str, tuple[str, str]] = {
    "governance": ("dartlab.scan.governance", "scanGovernance"),
    "workforce": ("dartlab.scan.workforce", "scanWorkforce"),
    "capital": ("dartlab.scan.capital", "scanCapital"),
    "debt": ("dartlab.scan.debt", "scanDebt"),
}


@lru_cache(maxsize=len(_SCAN_AXES))
def _marketScan(axis: str) -> pl.DataFrame | None:
    """축 하나의 전종목 스캔 결과. 프로세스 안에서 축마다 한 번만 만든다.

    네 축 모두 회사 인자를 받지 않는 시장 단위 스캔이다. 결과를 회사별로 걸러 쓸 뿐인데
    Company 인스턴스 캐시에만 담고 있어서 회사가 바뀌면 시장 전체를 다시 훑었다. capital
    축은 실측 회사당 8 초라, 주당 지표가 필요한 밸류에이션 입력이 회사마다 그 값을 물었다.
    로컬 parquet 를 읽는 순수 계산이라 프로세스 안에 들고 있어도 되며 굽는 산출물은 없다.
    """
    import importlib

    module, fn = _SCAN_AXES[axis]
    return getattr(importlib.import_module(module), fn)(verbose=False)


def _ensureScanAxis(company: Company, axis: str) -> pl.DataFrame | None:
    """축 스캔을 Company 캐시 뒤에 프로세스 캐시를 두고 가져온다."""
    key = f"_{axis}"
    val = company._cache.get(key, _CACHE_MISSING)
    if val is _CACHE_MISSING:
        val = _marketScan(axis)
        company._cache[key] = val
    return val


def _ensureGovernance(company: Company) -> pl.DataFrame | None:
    return _ensureScanAxis(company, "governance")


def _ensureWorkforce(company: Company) -> pl.DataFrame | None:
    return _ensureScanAxis(company, "workforce")


def _ensureCapital(company: Company) -> pl.DataFrame | None:
    return _ensureScanAxis(company, "capital")


def _ensureDebt(company: Company) -> pl.DataFrame | None:
    return _ensureScanAxis(company, "debt")


# ── view 공통 헬퍼 ─────────────────────────────────────────────────


def companyScanView(company: Company, df: pl.DataFrame | None, view: str | None) -> pl.DataFrame | None:
    """scan DataFrame 의 view 별 필터 공통 헬퍼 — governance/workforce/capital/debt 4 builder 공용.

    Capabilities:
        - view=None → ``종목코드``/``stockCode`` 컬럼으로 본 회사 row 만 필터.
        - view="all" → 전체 DataFrame 그대로.
        - view="market" → 시장 (KOSPI/KOSDAQ/기타) 별 요약 통계 (``_scanMarketSummary`` 위임).
        - df 가 None 또는 비어있음 → None.

    Args:
        company: Company 인스턴스 (stockCode 추출).
        df: scan DataFrame. None/empty → None.
        view: None / "all" / "market".

    Returns:
        pl.DataFrame | None — 필터된 결과. df 빈 경우 None.

    Example:
        >>> # companyScanView(c, df, view="market")

    Guide:
        - "이 회사 governance 한 row" → view=None.
        - "전체 상장사 governance" → view="all".
        - "시장 별 평균/중간값" → view="market".

    SeeAlso:
        - ``buildScanGovernance`` / ``buildScanWorkforce`` / ``buildScanCapital`` /
          ``buildScanDebt`` — 본 함수의 호출자.
        - ``_scanMarketSummary`` — view="market" 의 본체.

    Requires:
        - polars — DataFrame.
        - dartlab.core.polarsUtil — isEmptyDf.

    AIContext:
        4 scan builder 의 view 분기 표준화. AI 가 cross-market 비교 ("KOSPI vs KOSDAQ 인력
        평균") 시 view="market" 호출. None view 는 회사 1 행 — 단일 회사 답변 표준.

    LLM Specifications:
        AntiPatterns:
            - 종목코드 컬럼이 한국어 ("종목코드") 또는 영문 ("stockCode") 혼재 — 본 함수가
              자동 인식. 다른 컬럼명은 미지원.
            - view 가 정의된 3 외 (예 "industry") → 본 회사 row fallback.
        OutputSchema:
            - view=None: 1 row DataFrame.
            - view="all": 입력 그대로.
            - view="market": 시장 별 요약 (시장 + 종목수 + 컬럼별 평균/중간값).
        Prerequisites:
            - df 가 stockCode 또는 종목코드 컬럼 보유.
        Freshness:
            - df 의 source (scan 모듈 prebuild) 시점.
        Dataflow:
            - scan prebuild → ensure* → 본 함수 → builder → c.governance/workforce/...
        TargetMarkets:
            - KR (DART) 한정.

    Raises:
        없음.
    """
    if isEmptyDf(df):
        return None
    assert df is not None  # narrowing
    if view == "all":
        return df
    if view == "market":
        return _scanMarketSummary(df)
    # 기본: 이 회사 행
    code = company.stockCode
    codeCol = "종목코드" if "종목코드" in df.columns else "stockCode"
    row = df.filter(pl.col(codeCol) == code)
    return row if not row.is_empty() else None


def _scanMarketSummary(df: pl.DataFrame) -> pl.DataFrame:
    """시장별 요약 통계."""
    import importlib

    loadListing = importlib.import_module("dartlab.scan.io.parquet").loadListing
    _, _, _, listing_meta = loadListing()
    code_to_market = {code: meta.get("market", "") for code, meta in listing_meta.items()}
    codeCol = "종목코드" if "종목코드" in df.columns else "stockCode"
    df_with_market = df.with_columns(
        pl.col(codeCol)
        .replace_strict(code_to_market, default="미분류")
        .replace("", "미분류")
        .fill_null("미분류")
        .alias("시장")
    )
    numeric_cols = [c for c in df.columns if c != "종목코드" and df[c].dtype in (pl.Float64, pl.Int64)]
    if not numeric_cols:
        return df_with_market.group_by("시장").len()
    aggs = [pl.len().alias("종목수")]
    for c in numeric_cols:
        aggs.append(pl.col(c).mean().alias(f"{c}_평균"))
        aggs.append(pl.col(c).median().alias(f"{c}_중간값"))
    return df_with_market.group_by("시장").agg(aggs).sort("시장")


# ── network ───────────────────────────────────────────────────────


def buildScanNetwork(company: Company, view: str | None = None, *, hops: int = 1):
    """``c.network()`` 구현 — 그룹 내 회사 네트워크 그래프 빌드 + view 별 표현.

    Capabilities:
        - ``_ensureNetwork(company)`` 로 그래프 prebuild (cache) → (data, full).
        - view=None → 회사 중심 ego 그래프 → ``htmlRenderer.renderNetwork`` 로 HTML 시각화.
        - view="members" → 같은 그룹 계열사 목록 DataFrame.
        - view="edges" → 이 회사의 출자/피출자 연결 DataFrame.
        - view="cycles" → 이 회사가 포함된 순환출자 경로 list.
        - view="peers" → ego 그래프 노드 list DataFrame.
        - hops 로 ego 깊이 조절 (None/peers view 한정).

    Args:
        company: Company 인스턴스.
        view: None / "members" / "edges" / "cycles" / "peers". None 은 HTML 시각화.
        hops: ego 깊이. 기본 1.

    Returns:
        view 에 따라 가변 — HTML 문자열 (None) / DataFrame (members/edges/peers) / DataFrame
        (cycles) / None.

    Example:
        >>> # html = buildScanNetwork(c)  # view=None → HTML 시각화
        >>> # df = buildScanNetwork(c, view="members")  # 그룹 계열사

    Guide:
        - "삼성 그룹 계열사 목록" → ``c.network(view="members")``.
        - "출자/피출자 관계" → ``c.network(view="edges")``.
        - "순환출자 여부" → ``c.network(view="cycles")``.
        - "이 회사 중심 네트워크 시각화" → ``c.network()`` (HTML 반환).

    SeeAlso:
        - ``_ensureNetwork`` / ``_networkMembers`` / ``_networkEdges`` / ``_networkCycles`` /
          ``_networkPeers`` (모듈 private) — view 별 본체.
        - ``dartlab.scan.network.buildGraph`` / ``exportFull`` / ``exportEgo`` — 그래프 source.
        - ``dartlab.core.htmlRenderer.renderNetwork`` — HTML 시각화.

    Requires:
        - polars — DataFrame.
        - dartlab.scan.network — 그래프 prebuild (lazy import).
        - dartlab.core.htmlRenderer — HTML 시각화 (view=None 시).
        - dartlab.core.memory._CACHE_MISSING — cache sentinel.

    AIContext:
        Workbench "삼성그룹/LG그룹 어떤 회사 있냐" / "순환출자 있냐" 질문 entry. view=None 은
        HTML 반환 — 노트북 또는 Workbench UI 에서만 의미. text 답변 필요 시 view="members"
        등 명시.

    LLM Specifications:
        AntiPatterns:
            - view=None + 비 노트북 (text only) 환경 → HTML 문자열 그대로 답변 → 사용자 혼란.
              AI 가 view="members" 등 자동 선택 권장.
            - 회사가 그룹에 속하지 않음 (단독) → group = corpName, members 비어있음 가능.
            - cycles 가 없는 회사 → 빈 DataFrame.
            - view 가 정의된 5 외 → None.
        OutputSchema:
            - view=None: HTML str.
            - view="members": DataFrame (종목코드/회사명/시장/업종/자기).
            - view="edges": DataFrame (종목코드/회사명/유형/방향/목적/지분율/그룹).
            - view="cycles": DataFrame (번호/경로/길이).
            - view="peers": DataFrame (종목코드/회사명/그룹/업종/연결수/자기).
        Prerequisites:
            - dartlab.scan.network prebuild 가능 (KR 상장사 지분 데이터 수집).
        Freshness:
            - scan.network prebuild 시점 + cache.
        Dataflow:
            - 지분 데이터 → scan.network.buildGraph → cache → 본 함수 → AI/UI.
        TargetMarkets:
            - KR (DART) 상장사 한정.

    Raises:
        없음.
    """
    result = _ensureNetwork(company)
    if result is None:
        return None
    data, full = result
    code = company.stockCode
    group = data["code_to_group"].get(code, company.corpName or code)

    if view is None:
        import importlib

        exportEgo = importlib.import_module("dartlab.scan.network").exportEgo
        from dartlab.core.htmlRenderer import getHtmlRenderer

        ego = exportEgo(data, full, code, hops=hops)
        center_name = data["code_to_name"].get(code, code)
        renderer = getHtmlRenderer()
        if renderer is None:
            return None
        return renderer.renderNetwork(
            ego["nodes"],
            ego["edges"],
            f"{center_name} 관계 네트워크",
            centerId=code,
        )
    if view == "members":
        return _networkMembers(data, code, group)
    if view == "edges":
        return _networkEdges(full, code)
    if view == "cycles":
        return _networkCycles(data, code)
    if view == "peers":
        return _networkPeers(data, full, code, hops=hops)
    return None


def _networkMembers(data: dict, code: str, group: str) -> pl.DataFrame:
    """같은 그룹 계열사 목록."""
    members = [n for n in data["all_node_ids"] if data["code_to_group"].get(n) == group]
    rows = []
    for m in sorted(members):
        meta = data["listing_meta"].get(m, {})
        rows.append(
            {
                "종목코드": m,
                "회사명": meta.get("name", m),
                "시장": meta.get("market", ""),
                "업종": meta.get("industry", ""),
                "자기": m == code,
            }
        )
    return pl.DataFrame(rows)


def _networkEdges(full: dict, code: str) -> pl.DataFrame:
    """이 회사의 출자/지분 연결."""
    node_map = {n["id"]: n for n in full["nodes"]}
    rows = []
    for e in full["edges"]:
        if e["type"] == "person_shareholder":
            continue
        if e["source"] == code:
            target = e["target"]
            node = node_map.get(target)
            rows.append(
                {
                    "종목코드": target,
                    "회사명": node["label"] if node else target,
                    "유형": e["type"],
                    "방향": "출자 →",
                    "목적": e.get("purpose", ""),
                    "지분율": e.get("ownershipPct"),
                    "그룹": node["group"] if node else "",
                }
            )
        elif e["target"] == code:
            source = e["source"]
            node = node_map.get(source)
            rows.append(
                {
                    "종목코드": source,
                    "회사명": node["label"] if node else source,
                    "유형": e["type"],
                    "방향": "← 피출자",
                    "목적": e.get("purpose", ""),
                    "지분율": e.get("ownershipPct"),
                    "그룹": node["group"] if node else "",
                }
            )
    if not rows:
        return pl.DataFrame(
            schema={
                "종목코드": pl.Utf8,
                "회사명": pl.Utf8,
                "유형": pl.Utf8,
                "방향": pl.Utf8,
                "목적": pl.Utf8,
                "지분율": pl.Float64,
                "그룹": pl.Utf8,
            }
        )
    return pl.DataFrame(rows).sort("지분율", descending=True, nulls_last=True)


def _networkCycles(data: dict, code: str) -> pl.DataFrame:
    """이 회사가 포함된 순환출자 경로."""
    rows = []
    for i, cy in enumerate(data["cycles"]):
        if code not in cy:
            continue
        path = " → ".join(data["code_to_name"].get(c, c) for c in cy)
        rows.append({"번호": i + 1, "경로": path, "길이": len(cy) - 1})
    if not rows:
        return pl.DataFrame(schema={"번호": pl.Int64, "경로": pl.Utf8, "길이": pl.Int64})
    return pl.DataFrame(rows)


def _networkPeers(data: dict, full: dict, code: str, *, hops: int = 1) -> pl.DataFrame:
    """이 회사 중심 서브그래프 (ego 뷰) → DataFrame."""
    import importlib

    exportEgo = importlib.import_module("dartlab.scan.network").exportEgo
    ego = exportEgo(data, full, code, hops=hops)
    rows = []
    for n in ego["nodes"]:
        if n["type"] != "company":
            continue
        rows.append(
            {
                "종목코드": n["id"],
                "회사명": n["label"],
                "그룹": n["group"],
                "업종": n.get("industry", ""),
                "연결수": n["degree"],
                "자기": n["id"] == code,
            }
        )
    if not rows:
        return pl.DataFrame(
            schema={
                "종목코드": pl.Utf8,
                "회사명": pl.Utf8,
                "그룹": pl.Utf8,
                "업종": pl.Utf8,
                "연결수": pl.Int64,
                "자기": pl.Boolean,
            }
        )
    df = pl.DataFrame(rows)
    return df.sort("연결수", descending=True)


# ── 4 simple builders (governance/workforce/capital/debt) ─────────


def buildScanGovernance(company: Company, view: str | None = None) -> pl.DataFrame | None:
    """``c.governance()`` 구현 — 지배구조 scan view (이사회/지분 구조).

    Capabilities:
        - ``_ensureGovernance(company)`` 로 prebuild DataFrame 로드 (cache).
        - ``companyScanView`` 로 view 분기 (회사 row / 전체 / 시장 별 요약).
        - 빈 결과 → None.

    Args:
        company: Company 인스턴스.
        view: None / "all" / "market".

    Returns:
        pl.DataFrame | None.

    Example:
        >>> # df = buildScanGovernance(c, view="market")

    Guide:
        - "이 회사 지배구조" → ``c.governance()``.
        - "시장 별 거버넌스 평균" → ``c.governance(view="market")``.

    SeeAlso:
        - ``_ensureGovernance`` — prebuild cache 헬퍼.
        - ``companyScanView`` — view 분기 공통.
        - ``dartlab.scan.governance.scanGovernance`` — prebuild source.

    Requires:
        - polars — DataFrame.
        - dartlab.scan.governance — scanGovernance (lazy import).

    AIContext:
        Workbench "이 회사 거버넌스" / "이사회 구성" 질문 entry. None view 1 row → 자연어 변환.

    LLM Specifications:
        AntiPatterns:
            - scanGovernance prebuild 결락 → None. 운영자 의무.
            - view="market" 결과는 통계 — 개별 회사 데이터 손실.
        OutputSchema:
            - companyScanView 결과 의존.
        Prerequisites:
            - dartlab.scan.governance prebuild 가능.
        Freshness:
            - prebuild + cache 시점.
        Dataflow:
            - dartlab.scan.governance → ensure cache → 본 함수 → c.governance().
        TargetMarkets:
            - KR (DART) 상장사 한정.

    Raises:
        없음.
    """
    return companyScanView(company, _ensureGovernance(company), view)


def buildScanWorkforce(company: Company, view: str | None = None) -> pl.DataFrame | None:
    """``c.workforce()`` 구현 — 인력 scan view (직원 수/평균 급여/연봉 분포).

    Capabilities:
        - ``_ensureWorkforce(company)`` prebuild → ``companyScanView`` view 분기.

    Args:
        company: Company 인스턴스.
        view: None / "all" / "market".

    Returns:
        pl.DataFrame | None.

    Example:
        >>> # buildScanWorkforce(c, view="market")

    Guide:
        - "이 회사 직원 수" → ``c.workforce()``.
        - "시장 별 평균 급여" → ``c.workforce(view="market")``.

    SeeAlso:
        - ``_ensureWorkforce`` / ``companyScanView``.
        - ``dartlab.scan.workforce.scanWorkforce``.

    Requires:
        - polars + dartlab.scan.workforce.

    AIContext:
        "이 회사 직원수 / 인건비" 질문 entry.

    LLM Specifications:
        AntiPatterns:
            - scanWorkforce 미빌드 → None.
        OutputSchema:
            - companyScanView 결과 의존.
        Prerequisites:
            - dartlab.scan.workforce prebuild.
        Freshness:
            - prebuild + cache.
        Dataflow:
            - dartlab.scan.workforce → ensure → 본 함수 → c.workforce().
        TargetMarkets:
            - KR 상장사 한정.

    Raises:
        없음.
    """
    return companyScanView(company, _ensureWorkforce(company), view)


def buildScanCapital(company: Company, view: str | None = None) -> pl.DataFrame | None:
    """``c.capital()`` 구현 — 자본 scan view (자본금/자본총계/이익잉여금).

    Capabilities:
        - ``_ensureCapital(company)`` prebuild → ``companyScanView``.

    Args:
        company: Company 인스턴스.
        view: None / "all" / "market".

    Returns:
        pl.DataFrame | None.

    Example:
        >>> # buildScanCapital(c)

    Guide:
        - "이 회사 자본 규모" → ``c.capital()``.
        - "시장 별 자본금 분포" → ``c.capital(view="market")``.

    SeeAlso:
        - ``_ensureCapital`` / ``companyScanView``.
        - ``dartlab.scan.capital.scanCapital``.

    Requires:
        - polars + dartlab.scan.capital.

    AIContext:
        "자본총계 / 이익잉여금" 질문 entry. BS 의 자본 항목과 일관.

    LLM Specifications:
        AntiPatterns:
            - scanCapital 미빌드 → None.
        OutputSchema:
            - companyScanView 결과 의존.
        Prerequisites:
            - dartlab.scan.capital prebuild.
        Freshness:
            - prebuild + cache.
        Dataflow:
            - dartlab.scan.capital → ensure → 본 함수 → c.capital().
        TargetMarkets:
            - KR 상장사 한정.

    Raises:
        없음.
    """
    return companyScanView(company, _ensureCapital(company), view)


def buildScanDebt(company: Company, view: str | None = None) -> pl.DataFrame | None:
    """``c.debt()`` 구현 — 부채 scan view (부채총계/장단기/이자보상배율).

    Capabilities:
        - ``_ensureDebt(company)`` prebuild → ``companyScanView``.

    Args:
        company: Company 인스턴스.
        view: None / "all" / "market".

    Returns:
        pl.DataFrame | None.

    Example:
        >>> # buildScanDebt(c)

    Guide:
        - "이 회사 부채 비율" → ``c.debt()``.
        - "시장 별 평균 부채" → ``c.debt(view="market")``.

    SeeAlso:
        - ``_ensureDebt`` / ``companyScanView``.
        - ``dartlab.scan.debt.scanDebt``.

    Requires:
        - polars + dartlab.scan.debt.

    AIContext:
        "부채 비율 / 신용 위험" 질문 entry. credit 엔진과 보완.

    LLM Specifications:
        AntiPatterns:
            - scanDebt 미빌드 → None.
        OutputSchema:
            - companyScanView 결과 의존.
        Prerequisites:
            - dartlab.scan.debt prebuild.
        Freshness:
            - prebuild + cache.
        Dataflow:
            - dartlab.scan.debt → ensure → 본 함수 → c.debt().
        TargetMarkets:
            - KR 상장사 한정.

    Raises:
        없음.
    """
    return companyScanView(company, _ensureDebt(company), view)
