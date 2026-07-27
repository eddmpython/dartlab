"""전종목 재무비율 시계열 — scanAccount.py 분할 (규칙 3 LoC).

`scanAccount.py` 1082 LoC 가 규칙 3 임계 (>800) 위반. scanRatio / scanRatioList /
`_calcSimpleRatio` / `_calcYoyRatio` 와 `_RATIO_DEFS` 카탈로그 (~480 줄) 를 본 모듈로
분리. 호출자 호환 — scanAccount.py 가 `_RATIO_DEFS` · scanRatio · scanRatioList 재내보내기.
"""

from __future__ import annotations

import polars as pl

from dartlab.providers.dart.finance.scanAccount import scanAccount

_RATIO_DEFS: dict[str, dict] = {
    "roe": {"numer": "net_income", "denom": "total_stockholders_equity", "pct": True, "label": "ROE"},
    "roa": {"numer": "net_income", "denom": "total_assets", "pct": True, "label": "ROA"},
    "operatingMargin": {
        "numer": "operating_profit",
        "denom": "sales",
        "pct": True,
        "label": "영업이익률",
    },
    "netMargin": {"numer": "net_income", "denom": "sales", "pct": True, "label": "순이익률"},
    "grossMargin": {"numer": "gross_profit", "denom": "sales", "pct": True, "label": "매출총이익률"},
    "debtRatio": {
        "numer": "total_liabilities",
        "denom": "total_stockholders_equity",
        "pct": True,
        "label": "부채비율",
    },
    "currentRatio": {
        "numer": "current_assets",
        "denom": "current_liabilities",
        "pct": True,
        "label": "유동비율",
    },
    "equityRatio": {
        "numer": "total_stockholders_equity",
        "denom": "total_assets",
        "pct": True,
        "label": "자기자본비율",
    },
    "revenueGrowth": {"base": "sales", "yoy": True, "pct": True, "label": "매출성장률"},
    "operatingProfitGrowth": {
        "base": "operating_profit",
        "yoy": True,
        "pct": True,
        "label": "영업이익성장률",
    },
    "netProfitGrowth": {
        "base": "net_income",
        "yoy": True,
        "pct": True,
        "label": "순이익성장률",
    },
    "totalAssetTurnover": {
        "numer": "sales",
        "denom": "total_assets",
        "pct": False,
        "label": "총자산회전율",
    },
    "operatingCfMargin": {
        "numer": "operating_cashflow",
        "denom": "sales",
        "pct": True,
        "label": "영업CF마진",
    },
}


def _emptyStockCodeFrame() -> pl.DataFrame:
    """scanRatio 빈 결과의 join key 타입을 고정한다."""
    return pl.DataFrame(schema={"stockCode": pl.Utf8})


def scanRatio(
    ratioName: str,
    *,
    fsPref: str = "CFS",
    freq: str = "Q",
) -> pl.DataFrame:
    """전종목 단일 재무비율 시계열 — scan 원자 primitive 2.

    Args:
        ratioName: 비율 키 (roe/operatingMargin/debtRatio 등 13 종).
            ``scanRatioList()`` 로 카탈로그 확인.
        fsPref: 연결 우선 ("CFS") 또는 별도 ("OFS").
        freq: "Q" (분기) 또는 "Y" (연간).

    Returns:
        pl.DataFrame — 2664 종목 × 기간 컬럼 wide 형식. stockCode 컬럼 + 기간별
        비율 값 (%·배). 단위는 ``_RATIO_DEFS[ratioName]["label"]`` 참조.

    Raises:
        ValueError: 지원하지 않는 ``ratioName`` 일 때 (PBR/PER 등 시가총액 기반은
            scanRatio 범위 밖 — ``scan("valuation")`` 사용).

    Example:
        >>> scanRatio("roe", freq="Y").sort("2025", descending=True).head(30)
        >>> dr = scanRatio("debtRatio", freq="Y").select(["stockCode", "2025"])

    SeeAlso:
        - ``scanAccount`` — primitive 1 (단일 계정 시계열).
        - ``scanRatioList`` — 지원 비율 카탈로그.
        - ``scan("valuation")`` — PBR/PER 등 시가총액 기반 비율.

    Requires:
        - dartlab
        - finance.parquet (prebuild)

    Capabilities:
        - 2664 종목 × 기간 wide DataFrame 단발 추출. polars vectorize — Python loop 0.
        - YoY 비율 (revenueGrowth 등) 은 부호 전환 시 None 정책.

    Guide:
        - 단일 축 한 번 돌리고 끝내지 말 것. "투자할만한 회사" 류는 ROE/operatingMargin/
          debtRatio/revenueGrowth 등 다축 join 후 교집합.
        - 지주사·금융업·라이센싱사는 operatingMargin 비정상치 (100 % 초과) 가능 — listing()
          섹터 필터 또는 ``c.panel("IS")`` 로 구조 확인.

    AIContext:
        scan 원자 primitive 2. 광역 발굴 질문에 ``scanAccount`` 와 자유 조합. 단일 종목
        지목 전까지 Company 호출 금지.

    LLM Specifications:
        AntiPatterns:
            - 단일 ratio 만으로 "좋은 회사" 결론 (다축 교집합 필수).
            - PBR/PER 시도 (``scan("valuation")`` 우회 의무).
        OutputSchema:
            - stockCode: str
            - 기간 컬럼들 (YYYY 또는 YYYYQN): float (% 또는 배).
        Prerequisites:
            - prebuild ``finance.parquet`` 존재.
        Freshness:
            - prebuild 파이프라인 갱신 시점 — 보통 분기 결산 1~2 주 후.
        Dataflow:
            - finance.parquet → polars lazy scan → pivot → ratio 계산 → wide DataFrame.
        TargetMarkets:
            - KR (DART) 한정.
    """
    if ratioName not in _RATIO_DEFS:
        available = ", ".join(sorted(_RATIO_DEFS))
        lower = ratioName.lower()
        hint = ""
        if lower in {"pbr", "per", "psr", "ev", "evEbitda".lower(), "ev_ebitda", "dividendyield", "dividend_yield"}:
            hint = (
                " — 시가총액 기반 밸류에이션 비율은 scanRatio 범위 밖이다. "
                "dartlab.scan('valuation') 을 사용하라 (네이버 시총 snapshot 경로)."
            )
        msg = f"지원하지 않는 비율: '{ratioName}'.{hint} 사용 가능: {available}"
        raise ValueError(msg)

    defn = _RATIO_DEFS[ratioName]

    if defn.get("yoy"):
        return _calcYoyRatio(defn, fsPref, freq=freq)
    return _calcSimpleRatio(defn, fsPref, freq=freq)


def scanRatioList() -> list[dict[str, str]]:
    """사용 가능한 scanRatio 비율 카탈로그.

    Args:
        없음.

    Returns:
        list[dict[str, str]] — `{name, label, unit}` 형식의 dict 리스트. ``name``
        은 ``scanRatio(ratioName=...)`` 에 넣는 정규 키, ``unit`` 은 ``%`` 또는 ``배``.

    Raises:
        없음.

    Example:
        >>> dartlab.scan("ratio")
        >>> [r["name"] for r in scanRatioList()]

    SeeAlso:
        - ``scanRatio`` — 카탈로그의 비율 1 종을 전종목 시계열로.
        - ``scanFields`` — 조건형 스크리닝 필드 카탈로그.
        - ``scan("ratio")`` — 본 함수 호출 shortcut.

    Requires:
        - dartlab

    Capabilities:
        - 13 종 비율 (수익성 5 / 안정성 3 / 성장 3 / 효율 1 / CF 1) 메타 반환.
        - ``_RATIO_DEFS`` 단일 원천 — 신규 비율 추가 시 본 함수가 자동 노출.

    Guide:
        - AI 가 사용자 질문에 맞는 비율 키를 먼저 본 함수로 확인 후 ``scanRatio`` 호출.

    AIContext:
        카탈로그 조회 함수. ``scan("fields")`` 의 finance ratio 행이 본 목록에서 생성.

    LLM Specifications:
        AntiPatterns:
            - PBR/PER/dividendYield 등 시가총액 기반 비율을 본 목록에서 찾기 (``scan("valuation")`` 별도 경로).
        OutputSchema:
            - list[dict[str, str]] — keys: name / label / unit.
        Prerequisites:
            - 없음 (in-memory dict 변환).
        Freshness:
            - 즉시 (모듈 import 시점 카탈로그).
        Dataflow:
            - 모듈 _RATIO_DEFS → list comprehension → dict 리스트.
        TargetMarkets:
            - KR (DART) 한정.
    """
    return [{"name": k, "label": v["label"], "unit": "%" if v.get("pct") else "배"} for k, v in _RATIO_DEFS.items()]


def _calcSimpleRatio(defn: dict, fsPref: str, *, freq: str = "Q") -> pl.DataFrame:
    """분자/분모 비율 계산."""
    numer = scanAccount(defn["numer"], fsPref=fsPref, freq=freq)
    denom = scanAccount(defn["denom"], fsPref=fsPref, freq=freq)

    numerYears = [c for c in numer.columns if c != "stockCode"]
    denomYears = [c for c in denom.columns if c != "stockCode"]
    commonYears = sorted(set(numerYears) & set(denomYears), reverse=True)

    if not commonYears:
        return _emptyStockCodeFrame()

    joined = numer.select(["stockCode"] + commonYears).join(
        denom.select(["stockCode"] + commonYears),
        on="stockCode",
        suffix="_d",
    )

    isPct = defn.get("pct", False)
    multiplier = 100.0 if isPct else 1.0

    resultExprs = [pl.col("stockCode")]
    for y in commonYears:
        expr = (
            pl.when((pl.col(f"{y}_d") != 0) & pl.col(f"{y}_d").is_not_null() & pl.col(y).is_not_null())
            .then((pl.col(y) / pl.col(f"{y}_d") * multiplier).round(2))
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias(y)
        )
        resultExprs.append(expr)

    # 종목코드로 정렬해 돌려준다. polars 의 병렬 조인은 행 순서를 보장하지 않아서, 같은
    # 질의를 두 번 돌리면 2,812 행이 매번 다른 순서로 나왔다. 사용자가 보는 표가 실행마다
    # 섞이는 것도 문제지만, 그 위에 얹힌 content seal 이 같은 내용에 매번 다른 식별자를
    # 붙이게 되는 것이 더 크다. 내용이 같으면 같은 식별자라는 것이 seal 의 존재 이유다.
    return joined.select(resultExprs).sort("stockCode")


def _calcYoyRatio(defn: dict, fsPref: str, *, freq: str = "Q") -> pl.DataFrame:
    """YoY 성장률 계산."""
    base = scanAccount(defn["base"], fsPref=fsPref, freq=freq)
    yearCols = sorted(c for c in base.columns if c != "stockCode")

    if len(yearCols) < 2:
        return _emptyStockCodeFrame()

    resultExprs = [pl.col("stockCode")]
    for i in range(1, len(yearCols)):
        cur = yearCols[i]
        prev = yearCols[i - 1]
        expr = (
            pl.when(
                (pl.col(prev) != 0) & pl.col(prev).is_not_null() & pl.col(cur).is_not_null() & (pl.col(prev).abs() > 0)
            )
            .then(((pl.col(cur) - pl.col(prev)) / pl.col(prev).abs() * 100).round(2))
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias(cur)
        )
        resultExprs.append(expr)

    yoyCols = [yearCols[i] for i in range(1, len(yearCols))]
    return base.select(resultExprs).select(["stockCode"] + list(reversed(yoyCols)))
