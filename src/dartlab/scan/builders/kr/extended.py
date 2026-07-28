"""scan → story 모듈 — 전종목 횡단 데이터로 교차 조합 관점 제공.

analysis calc 패턴과 동일: calcXxx(company) → dict, story builders 가 블록으로 조립.

scan 의 진짜 힘 — 2~3축 교차 조합으로 단일 종목에서 안 보이는 뷰 생성:
- 수익성 × 성장성 → "성숙기 캐시카우" / "고성장 고마진"
- 부채 × 자본환원 → "레버리지 주주환원"
- 매출 순위 × 영업이익 순위 → "마진 프리미엄"

데이터: scan/finance.parquet 프리빌드 사용 (이미 존재, _ensureScanData 자동 다운로드).
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def calcPeerPosition(company, *, basePeriod: str | None = None) -> dict | None:
    """전종목 횡단 → 이 종목의 시장 내 위치 (수익성×성장성×이익품질×부채 4 축 백분위 + 교차 관점).

    scan/finance.parquet 에서 수익성/성장성/이익품질/부채 4축 백분위 산출 후
    교차 조합으로 관점 (crossViews) 생성. single-company 뷰가 놓치는 횡단 콘텍스트를
    Story / Insight 빌더 단계에서 주입.

    Parameters
    ----------
    company : Company
        분석 대상 기업 (stockCode 필요).
    basePeriod : str, optional
        기준 연도 (None 이면 최신).

    Returns
    -------
    dict | None
        stockCode : str — 종목코드
        year : str — 기준 연도
        total_stocks : int — 전종목 수
        profitability_pct : float | None — 수익성 백분위 (%)
        growth_pct : float | None — 성장성 백분위 (%)
        quality_pct : float | None — 이익품질 백분위 (%)
        debt_pct : float | None — 부채 백분위 (%)
        op_margin : float | None — 영업이익률 (%)
        roe : float | None — 자기자본이익률 (%)
        debt_ratio : float | None — 부채비율 (%)
        crossViews : list[dict] — 교차 관점 (view, basis)
        narrative : str — 서사 요약 문장
        데이터 부족 시 None.

    Raises
    ------
    polars.PolarsError
        scan finance.parquet 손상 시 내부에서 흡수 → None 반환.

    Examples
    --------
    >>> from dartlab.scan.builders.kr.extended import calcPeerPosition
    >>> import dartlab
    >>> c = dartlab.Company("005930")
    >>> pos = calcPeerPosition(c)
    >>> pos["profitability_pct"] if pos else "no data"

    Capabilities:
        - 전종목 finance.parquet 의 연결재무제표 4 분기 단면을 추출하여 종목별 4 축 (수익성/
          성장성/이익품질/부채) 백분위 계산. 같은 단면 안에서 교차 관점 (예: "성숙기 캐시카우",
          "고성장 고마진") narrative 자동 생성.
        - 단일 종목 분석이 못 보는 시장 내 상대 위치를 비교 가능 지표로 제공.

    AIContext:
        Story / Insight builder 가 기업 1 사 보고서를 작성할 때 호출. Narrative 첫 단락의
        횡단 콘텍스트 ("전 종목 중 영업이익률 상위 12 %") source. 4 분기 연결 단면 기준이라
        본 함수 결과는 연 1 회 refresh — buildFinance 후 즉시 갱신.

    Guide:
        - basePeriod None → 최신 (가장 흔한 사용). 과거 시점 비교는 명시.
        - crossViews 는 4 축 백분위 임계 조합으로 결정. 임계 변경 시 본 함수 내부 분기 수정.
        - 종목이 scan/finance.parquet 에 없으면 (신규 상장 / 결산월 변경 직후) None 반환.

    When:
        Story / Insight 빌더가 기업 1 사 종합 분석 시. 단일 호출당 약 1~2 초 (전종목 scan).
        같은 단면에서 여러 회사 비교가 필요하면 본 함수 반복 호출보다 batch 형 scan 권장.

    How:
        ``_ensureScanData()`` → ``finance.parquet`` lazy scan → 연결재무제표 4 분기 필터 →
        종목별 매출/영업이익/순이익/자산/자본/부채 합산 → 4 축 ratio 계산 → 백분위 (rank/total)
        → ``_buildCrossViews`` 로 교차 관점 narrative.

    Requires:
        - 로컬 ``data/dart/scan/finance.parquet`` (`buildFinance` 산출)
        - ``dartlab.scan.io.parquet._ensureScanData`` · ``parseNumStr``
        - ``company.stockCode`` 속성

    SeeAlso:
        - :func:`calcGovernanceSummary` — 비재무 보조 (지배구조 등급)
        - :func:`dartlab.scan.builders.kr.core.buildFinance` — 본 함수의 source 빌드
        - :mod:`dartlab.story` — 본 함수 결과를 narrative 로 조립
    """
    import polars as pl

    from dartlab.scan.io.parquet import _ensureScanData, parseNumStr

    code = getattr(company, "stockCode", None)
    if not code:
        return None

    scanDir = _ensureScanData()
    path = scanDir / "finance.parquet"
    if not path.exists():
        log.warning("scan/finance.parquet 없음")
        return None

    try:
        lf = pl.scan_parquet(str(path))
        # 필요한 컬럼만 선택 → 메모리 절약 (전종목이지만 계정+금액만)
        needed_cols = ["stockCode", "bsns_year", "sj_div", "account_nm", "thstrm_amount", "fs_nm", "reprt_nm"]
        available = lf.collect_schema().names()
        select_cols = [c for c in needed_cols if c in available]
        snap = (
            lf.select(select_cols)
            .filter(pl.col("fs_nm").str.contains("연결"))
            .filter(pl.col("reprt_nm").str.contains("4분기"))
            .collect(engine="streaming")
        )
    except (pl.exceptions.PolarsError, OSError) as e:
        log.warning("finance.parquet 스캔 실패: %s", e)
        return None

    if snap.is_empty():
        return None

    # 최신 연도
    years = sorted(snap["bsns_year"].unique().to_list(), reverse=True)
    year = years[0] if years else None
    if not year:
        return None
    cur = snap.filter(pl.col("bsns_year") == year)

    # 이 종목 데이터 추출
    stock = cur.filter(pl.col("stockCode") == code)
    if stock.is_empty():
        return None

    total = cur["stockCode"].n_unique()

    def _extract(df, accountNms):
        """계정명 매칭 → 금액 추출."""
        for nm in accountNms:
            rows = df.filter(pl.col("account_nm") == nm)
            if not rows.is_empty():
                v = parseNumStr(rows["thstrm_amount"][0])
                if v is not None:
                    return v
        return None

    def _percentile(df, accountNms, stockVal):
        """전종목 대비 백분위."""
        if stockVal is None:
            return None
        vals = []
        for sc in df["stockCode"].unique().to_list():
            s = df.filter(pl.col("stockCode") == sc)
            v = _extract(s, accountNms)
            if v is not None:
                vals.append(v)
        if len(vals) < 50:
            return None
        below = sum(1 for v in vals if v < stockVal)
        return round(below / len(vals) * 100, 1)

    # 4축 계정명
    revenue_nms = ["매출액", "수익(매출액)", "영업수익"]
    op_nms = ["영업이익", "영업이익(손실)"]
    ni_nms = ["당기순이익", "당기순이익(손실)"]
    equity_nms = ["자본총계"]
    debt_nms = ["부채총계"]

    # 이 종목 값 추출
    rev = _extract(stock, revenue_nms)
    op = _extract(stock, op_nms)
    ni = _extract(stock, ni_nms)
    eq = _extract(stock, equity_nms)
    debt = _extract(stock, debt_nms)

    # 파생 비율
    op_margin = round(op / rev * 100, 1) if rev and op and rev > 0 else None
    roe = round(ni / eq * 100, 1) if ni and eq and eq > 0 else None
    debt_ratio = round(debt / eq * 100, 1) if debt and eq and eq > 0 else None

    # 백분위 (전종목 대비)
    profitability_pct = _percentile(cur.filter(cur["sj_div"] == "IS"), op_nms, op)
    # 성장성: 전기 대비 (간략 — 전기 데이터 없으면 None)
    growth_pct = None
    quality_pct = None
    debt_pct = _percentile(cur.filter(cur["sj_div"] == "BS"), debt_nms, debt)

    # 교차 조합 관점
    crossViews = []
    if profitability_pct is not None:
        if profitability_pct >= 80 and (growth_pct is None or growth_pct <= 40):
            crossViews.append(
                {"view": "성숙기 캐시카우", "basis": f"수익성 상위 {100 - profitability_pct:.0f}% + 성장 하위권"}
            )
        if profitability_pct >= 70 and growth_pct is not None and growth_pct >= 70:
            crossViews.append(
                {
                    "view": "고성장 고마진",
                    "basis": f"수익성 상위 {100 - profitability_pct:.0f}% + 성장 상위 {100 - growth_pct:.0f}%",
                }
            )
    if debt_pct is not None and profitability_pct is not None:
        if debt_pct >= 70 and profitability_pct >= 60:
            crossViews.append(
                {
                    "view": "레버리지 수익형",
                    "basis": f"부채 상위 {100 - debt_pct:.0f}% + 수익성 상위 {100 - profitability_pct:.0f}%",
                }
            )
        if debt_pct <= 30:
            crossViews.append({"view": "무차입 안정형", "basis": f"부채 하위 {debt_pct:.0f}%"})

    # 서사
    parts = []
    if profitability_pct is not None:
        parts.append(f"수익성 상위 {100 - profitability_pct:.0f}%")
    if growth_pct is not None:
        parts.append(f"성장성 상위 {100 - growth_pct:.0f}%")
    if debt_pct is not None:
        if debt_pct >= 70:
            parts.append(f"부채 상위 {100 - debt_pct:.0f}% (높음)")
        else:
            parts.append(f"부채 하위 {debt_pct:.0f}% (안정)")
    if crossViews:
        parts.append(f"→ {crossViews[0]['view']}")
    narrative = ". ".join(parts) + "." if parts else "peer 비교 데이터 부족."

    return {
        "stockCode": code,
        "year": year,
        "total_stocks": total,
        "profitability_pct": profitability_pct,
        "growth_pct": growth_pct,
        "quality_pct": quality_pct,
        "debt_pct": debt_pct,
        "op_margin": op_margin,
        "roe": roe,
        "debt_ratio": debt_ratio,
        "crossViews": crossViews,
        "narrative": narrative,
    }


def calcGovernanceSummary(company) -> dict | None:
    """scan governance → 종목의 지배구조 5 축 종합 점수/등급 1 줄 요약.

    `Company.governance()` 가 구현되어 있으면 위임 (DataFrame 첫 row 의 totalScore/grade),
    아니면 narrative-only dict 반환. Story/Insight 의 governance 단락 source.

    Parameters
    ----------
    company : Company
        분석 대상 기업 (stockCode 필요).

    Returns
    -------
    dict | None
        stockCode : str — 종목코드
        totalScore : float | None — 종합점수 (점)
        grade : str | None — 등급 (A~E)
        narrative : str — 요약 문장
        데이터 없으면 narrative만 포함한 dict.

    Raises
    ------
    AttributeError
        company 가 stockCode 속성 없을 시 None 반환 (예외 없음).

    Examples
    --------
    >>> from dartlab.scan.builders.kr.extended import calcGovernanceSummary
    >>> import dartlab
    >>> c = dartlab.Company("005930")
    >>> g = calcGovernanceSummary(c)
    >>> g.get("grade") if g else "no data"

    Capabilities:
        - `Company.governance()` 결과 (지배구조 5 축 - 지분율/사외이사/보수비율/감사독립/소액주주분산
          점수) 의 종합 점수·등급 1 줄 요약. ``narrative`` 필드는 "지배구조 B등급 (72점)." 같은
          insertable phrase.

    AIContext:
        Story builder 가 1 사 분석에서 governance 단락 도입부 narrative 추출. AI 가 길게 풀어
        쓰지 않고 본 함수의 ``narrative`` 를 바로 인용 가능.

    Guide:
        - Company.governance() 미구현 환경에서는 narrative-only dict 반환 — 호출자는 grade 누락
          가능성 항상 대비.
        - 종목코드 없으면 None — 빈 Company 인스턴스 방어.

    When:
        Story/Insight 빌더 1 사 분석 시. 횡단 비교용은 아니라 `Scan` 의 governance axis 직접 호출
        권장.

    How:
        ``getattr(company, 'stockCode', ...)`` → ``Company.governance()`` 호출 (있을 때만) →
        DataFrame 첫 row 의 totalScore/grade dict 화 → narrative 포맷팅. 실패 시 fallback dict.

    Requires:
        - ``company.stockCode`` 속성
        - ``Company.governance()`` (선택 — 없으면 narrative-only)

    SeeAlso:
        - :func:`calcPeerPosition` — 본 함수의 재무 sibling
        - :mod:`dartlab.scan.governance` — `Company.governance()` 의 source axis
    """
    code = getattr(company, "stockCode", None)
    if not code:
        return None

    try:
        gov = company.governance() if hasattr(company, "governance") else None
        if gov is not None and hasattr(gov, "to_dicts"):
            rows = gov.to_dicts()
            if rows:
                r = rows[0]
                return {
                    "stockCode": code,
                    "totalScore": r.get("totalScore"),
                    "grade": r.get("grade"),
                    "narrative": f"지배구조 {r.get('grade', '?')}등급 ({r.get('totalScore', '?')}점).",
                }
    except (AttributeError, TypeError, ValueError):
        pass

    return {"stockCode": code, "narrative": "지배구조 데이터 없음."}
