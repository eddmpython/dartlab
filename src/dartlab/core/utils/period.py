"""period 포맷 표준화 + fiscal↔calendar 앵커링 SSOT.

모든 시장(KR/US/CN/JP)의 분기 period 를 통일된 캘린더 기준으로 생성/파싱.

표준 포맷: YYYY-QN (예: "2024-Q1", "2024-Q4")
연도 포맷: YYYY (예: "2024")

기간 라벨은 **항상 캘린더 기준** — end_date 의 캘린더 연도·분기 (Capital IQ 규칙).
XBRL fiscal fy/fp 그대로 쓰지 않음 (회사별 결산월 차이로 cross-company 비교 깨짐).
4 비교 가능성 (회사내/회사간/시장내/시장간) 의 근본 전제.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any


def formatPeriod(year: str | int, quarter: int) -> str:
    """연도 + 분기 → 표준 period 문자열.

    Args:
        year: 연도 (문자열 또는 정수)
        quarter: 분기 (1~4)

    Returns:
        "YYYY-QN" 형식 문자열.
    """
    return f"{year}-Q{quarter}"


def parsePeriod(period: str) -> tuple[str, int]:
    """period 문자열 → (연도, 분기).

    "2024-Q1" → ("2024", 1)
    "2024_Q1" → ("2024", 1)  (하위호환)

    Args:
        period: "YYYY-QN" 또는 "YYYY_QN" 형식.

    Returns:
        (연도 문자열, 분기 정수).
    """
    sep = "-" if "-" in period else "_"
    parts = period.split(sep, 1)
    year = parts[0]
    quarter = int(parts[1].replace("Q", ""))
    return year, quarter


def extractYear(period: str) -> str:
    """period에서 연도만 추출.

    "2024-Q1" → "2024"
    "2024_Q1" → "2024"  (하위호환)
    """
    sep = "-" if "-" in period else "_"
    return period.split(sep, 1)[0]


# ══════════════════════════════════════════════════════════════════
# fiscal → calendar 앵커링 SSOT
# ══════════════════════════════════════════════════════════════════


def calendarQuarterFromEnd(endDate: date) -> tuple[int, int]:
    """end_date → (calendarYear, calendarQuarter).

    Capital IQ 캘린더라이제이션 end-month 규칙:
        Nov/Dec/Jan → Q4 (Jan 은 전년도 Q4)
        Feb/Mar/Apr → Q1
        May/Jun/Jul → Q2
        Aug/Sep/Oct → Q3

    Args:
        endDate: 3개월 duration 이 끝난 날짜 (period_end).

    Returns:
        (calendarYear, calendarQuarter) 튜플.
        Q=1/2/3/4, year 는 Jan 종료 시 전년도로 shift.

    Example::

        calendarQuarterFromEnd(date(2025, 12, 31))  # (2025, 4)  — MNST Q4 / UA FY26 Q3
        calendarQuarterFromEnd(date(2026, 2, 28))   # (2026, 1)  — NKE FY26 Q3
        calendarQuarterFromEnd(date(2026, 1, 31))   # (2025, 4)  — Walmart FY26 Q4
        calendarQuarterFromEnd(date(2025, 3, 31))   # (2025, 1)  — UA FY25 FY
    """
    m = endDate.month
    y = endDate.year
    if m in (2, 3, 4):
        return (y, 1)
    if m in (5, 6, 7):
        return (y, 2)
    if m in (8, 9, 10):
        return (y, 3)
    if m == 1:
        return (y - 1, 4)
    return (y, 4)  # 11, 12


def fiscalToCalendarLabel(endDate: date, fp: str) -> str:
    """end_date + fp → 캘린더 기준 period 라벨.

    Args:
        endDate: period_end 날짜.
        fp: fiscal period ("Q1", "Q2", "Q3", "Q4", "FY").

    Returns:
        "YYYY-QN" (분기) 또는 "YYYY-FY" (연간 aggregate, end 연도 기준).
    """
    if fp == "FY":
        return f"{endDate.year}-FY"
    cy, cq = calendarQuarterFromEnd(endDate)
    return formatPeriod(cy, cq)


def _detectFiscalYearEndMonth(df) -> int | None:
    """fp="FY" 가장 최근 3개 회계연도의 end 월 최빈값 → FY 결산월.

    SEC companyfacts 는 한 filing 에 current + comparative 여러 end 가
    동일 (fy, fp) 태그로 붙음. 최근 fy 기준 가장 흔한 end month 가 현재 결산월.
    (UA 2024 Dec→Mar 전환 등 이력 노이즈에도 최근 기준 올바르게 판정.)
    """
    from collections import Counter

    import polars as pl

    fyDf = df.filter(pl.col("fp") == "FY").filter(pl.col("end").is_not_null())
    if isinstance(fyDf, pl.LazyFrame):
        fyDf = fyDf.collect()
    if fyDf.is_empty():
        return None
    maxFy = fyDf["fy"].max()
    if maxFy is None:
        return None
    recent = fyDf.filter(pl.col("fy") >= maxFy - 2)
    months = [d.month for d in recent["end"].to_list() if d is not None]
    if not months:
        return None
    return Counter(months).most_common(1)[0][0]


def _expectedQuarterEndMonth(fyEndMonth: int, qnum: int) -> int:
    """FY 결산월 기준 Q_n 종료월 (1-12).

    FY X 종료 = (X, fyEndMonth, 말일). Q_n 종료 = FY 종료 - (4-n)*3 개월.
    """
    monthsBack = (4 - qnum) * 3
    m = fyEndMonth - monthsBack
    while m <= 0:
        m += 12
    while m > 12:
        m -= 12
    return m


def _expectedQuarterEndYearOffset(fyEndMonth: int, qnum: int) -> int:
    """FY 결산월 기준 Q_n 종료가 fy 기준 몇 년 offset 인지 (-1 또는 0).

    fyEndMonth - (4-qnum)*3 이 양수면 같은 회계연도(offset=0), 음수면 전 해(-1).
    예: UA Mar end, Q1 → 3-9=-6 → offset=-1 (Q1 FY26 end Jun 2025, fy=2026)
    """
    monthsBack = (4 - qnum) * 3
    raw = fyEndMonth - monthsBack
    return 0 if raw > 0 else -1


def buildFiscalToCalendarMap(rawFacts) -> dict[str, str]:
    """Raw XBRL facts → fiscal label → calendar label 매핑 dict.

    SEC companyfacts / DART finance.parquet 등 원시 fact 테이블에서
    (fy, fp, end) 조합 중 **fiscal quarter 의 current period 가 맞는 end**
    만 골라 매핑 생성. pivot 후 column rename 에 사용.

    SEC companyfacts 는 한 filing 에 current period + comparative + balance
    snapshot 다 동일 (fy, fp) 태그로 저장하므로 max end 선택은 부정확.
    → FY 결산월 감지 후 **Q_n 예상 종료월** 에 매칭하는 end 만 채택.

    Capital IQ end-month 규칙 (``calendarQuarterFromEnd``) 단일 적용.
    12월 결산 기업은 대부분 identity — 변화 없음 수준.

    Args:
        rawFacts: polars DataFrame 또는 polars LazyFrame. 필수 컬럼:
            ``fy`` (int), ``fp`` (str in {Q1,Q2,Q3,FY}), ``end`` (date).

    Returns:
        dict. key = "{fy}-{fp}" (fiscal, pivot 내부 라벨),
              value = "{calYear}-Q{calQ}" 또는 "{calYear}-FY" (캘린더 라벨).
        fiscal == calendar identity 엔트리 제외 (안전한 no-op).
        Q4 synth 라벨 ("{fy}-Q4") 은 FY end 기준으로 자동 추가.
    """
    import polars as pl

    if not isinstance(rawFacts, (pl.DataFrame, pl.LazyFrame)):
        return {}

    df = rawFacts.lazy() if isinstance(rawFacts, pl.DataFrame) else rawFacts
    required = {"fy", "fp", "end"}
    schema = df.collect_schema()
    if not required.issubset(set(schema.names())):
        return {}

    # FY rows 는 duration >= 300 일 (≈1년) 만 통과 — Q 를 fp=FY 로 오태깅한
    # SEC 노이즈 (start=Jan end=Mar 같은 3개월 row) 제거.
    # Q rows 는 duration 필터 없음 — BS instant (duration=0) 도 포함해야 함.
    # 대신 Q 는 expected month+year offset 으로 current period 판별.
    schemaNames = set(schema.names())
    hasStart = "start" in schemaNames
    baseFilter = df.filter(pl.col("fp").is_in(["Q1", "Q2", "Q3", "FY"])).filter(pl.col("end").is_not_null())
    if hasStart:
        durExpr = (pl.col("end") - pl.col("start")).dt.total_days()
        baseFilter = baseFilter.with_columns(durExpr.alias("_dur"))
        # FY 만 duration >= 300 강제. Q 는 duration 무관 (BS instant 포함).
        baseFilter = baseFilter.filter((pl.col("fp") != "FY") | ((pl.col("fp") == "FY") & (pl.col("_dur") >= 300)))
    allRows = baseFilter.select("fy", "fp", "end").unique().collect()
    if allRows.is_empty():
        return {}

    # 회계연도 전환 기업 (UA 2024 Dec→Mar 등) 은 fy 별 결산월이 다르고,
    # SEC companyfacts 에는 filing-date-like 이상치 (e.g. AAPL fy=2009 end=2009-10-16)
    # 도 fp=FY 로 섞여 있음. 방어 전략:
    # 1. 전역 fyEndMonth 감지 (최근 3년 최빈 월)
    # 2. 각 fy: 전역 월 일치 end 우선, 없으면 그 fy max end fallback (전환 경계)
    # 3. 아직 FY 미공시 fy (NKE FY26 5월 결산 — 아직 Q3 만 공시) 도 전역 월로 추정
    globalEndMonth = _detectFiscalYearEndMonth(df)
    if globalEndMonth is None:
        return {}

    # 12월 결산 기업: fiscal == calendar 이므로 매핑 불필요 (성능/안전)
    if globalEndMonth == 12:
        return {}

    # 전환 이전 era (globalEndMonth != 12 인데 더 이전엔 12월 결산이던 UA 등) 는
    # 매핑에서 제외해야 comparative 오염을 피할 수 있음.
    # 전환 시작 fy = FY row end month 가 globalEndMonth 로 처음 바뀌는 fy.
    fyRows = allRows.filter(pl.col("fp") == "FY")
    fyEndsByYear: dict[int, list[date]] = {}
    for row in fyRows.iter_rows(named=True):
        fy = row.get("fy")
        end = row.get("end")
        if fy is None or end is None:
            continue
        fyEndsByYear.setdefault(int(fy), []).append(end)

    # 각 fy 에서 globalEndMonth 일치 end 최신 (전환 후 era 진입한 fy 만 자격).
    # SEC companyfacts 는 한 filing 에 복수 end (comparative/YTD) 를 fp=FY 로 저장하므로
    # **end.year == fy** 까지 요구해 cross-year 참조 오염 차단.
    fyEndPerYear: dict[int, date] = {}
    for fy, ends in fyEndsByYear.items():
        matching = [e for e in ends if e.month == globalEndMonth and e.year == fy]
        if matching:
            fyEndPerYear[fy] = max(matching)

    if not fyEndPerYear:
        # FY 공시 없지만 최신 fy Q_n 이 globalEndMonth 기반 예상월과 맞는지 확인
        fyEndMonthPerYear: dict[int, int] = {}
    else:
        fyEndMonthPerYear = {fy: globalEndMonth for fy in fyEndPerYear}

    # FY row 없는 최신 fy (NKE FY26 처럼 아직 FY 미공시) — 조건부 추가.
    # 해당 fy 의 Q_n 이 전환 이후 era 로 들어왔음을 확인 (예상월 일치 존재).
    # 전환 이전 era 의 잔존 fy 는 자동으로 제외됨 (예상월 불일치).
    maxFy = allRows["fy"].max()
    if maxFy is not None:
        maxFy = int(maxFy)
        for fy in range(maxFy, maxFy - 3, -1):
            if fy in fyEndMonthPerYear:
                continue
            fyQRows = allRows.filter((pl.col("fy") == fy) & (pl.col("fp") != "FY"))
            hasMatch = False
            for row in fyQRows.iter_rows(named=True):
                fp = row.get("fp")
                end = row.get("end")
                if fp is None or end is None:
                    continue
                qnum = int(fp[1])
                expected = _expectedQuarterEndMonth(globalEndMonth, qnum)
                if end.month == expected:
                    hasMatch = True
                    break
            if hasMatch:
                fyEndMonthPerYear[fy] = globalEndMonth

    # 예상 월 매칭 row 만 후보 → 그 중 max end 선택.
    # 각 fy 의 자체 결산월 기준으로 Q_n 예상 종료월 계산.
    result: dict[str, str] = {}
    candidates: dict[tuple[int, str], date] = {}

    # 각 fy 의 예상 Q_n 종료일을 fyEnd 기준 (4-n)*3 개월 전으로 계산.
    # ±45 일 윈도우로 매칭하면 AAPL 52-week 달력 등 month boundary shift 수용.
    def _shiftMonths(d: date, delta: int) -> date:
        m = d.month + delta
        y = d.year
        while m <= 0:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1
        # day 는 말일 기준 clip (2월 29일 예외)
        import calendar as _cal

        lastDay = _cal.monthrange(y, m)[1]
        return date(y, m, min(d.day, lastDay))

    for row in allRows.iter_rows(named=True):
        fy = row.get("fy")
        fp = row.get("fp")
        end = row.get("end")
        if fy is None or fp is None or end is None:
            continue
        fy = int(fy)
        fyEnd = fyEndPerYear.get(fy)
        fyMonth = fyEndMonthPerYear.get(fy)
        if fyMonth is None:
            continue
        if fp == "FY":
            if end.month != fyMonth or end.year != fy:
                continue
        else:
            qnum = int(fp[1])
            # 예상 end = fyEnd - (4-qnum)*3 months. fyEnd 미상이면 (fy, fyMonth, 말일) 가상.
            if fyEnd is not None:
                expectedEnd = _shiftMonths(fyEnd, -(4 - qnum) * 3)
            else:
                import calendar as _cal

                virtual = date(fy, fyMonth, _cal.monthrange(fy, fyMonth)[1])
                expectedEnd = _shiftMonths(virtual, -(4 - qnum) * 3)
            # ±45 일 윈도우 (52-week 달력, month boundary shift 수용)
            if abs((end - expectedEnd).days) > 45:
                continue
        key = (fy, fp)
        cur = candidates.get(key)
        if cur is None or end > cur:
            candidates[key] = end

    for (fy, fp), end in candidates.items():
        fiscal = f"{fy}-{fp}"
        cal = fiscalToCalendarLabel(end, fp)
        if cal != fiscal:
            result[fiscal] = cal

    # Q4 synth 보완: pivot._computeQ4 가 만드는 "{fy}-Q4" 라벨.
    # Q4 end == 그 fy 의 FY end.
    fyEnds = fyEndPerYear

    # Q4 synth 보완: pivot._computeQ4 가 만드는 "{fy}-Q4" 라벨.
    # Q4 end == FY end (4번째 분기가 FY 마지막 3개월).
    for fy, fyEnd in fyEnds.items():
        q4Fiscal = f"{fy}-Q4"
        if q4Fiscal in result:
            continue
        q4Cal = fiscalToCalendarLabel(fyEnd, "Q4")
        if q4Cal != q4Fiscal:
            result[q4Fiscal] = q4Cal

    return result


# ─── Phase 15 B1: 최신 기간 자동 감지 ────────────────────────────


def resolveLatestPeriod(periods: list[str] | set[str] | None) -> str | None:
    """기간 컬럼 중 최신을 자동 결정.

    - 분기 우선: "2025Q4" > "2025Q3" > "2024" (연간은 분기 뒤)
    - 연간 있으면: "2024" > "2023"
    - 둘 다 섞이면 분기 최신 선호 (공시 최신성 기준)

    Args:
        periods: 기간 컬럼 iterable (예: isParsed[1])

    Returns:
        가장 최신 기간 문자열. 없으면 None.
    """
    if not periods:
        return None
    pool = [p for p in periods if p and isinstance(p, str)]
    if not pool:
        return None

    def _sortKey(p: str) -> tuple:
        # YYYYQN: (year, quarter, is_quarter)
        # YYYY: (year, 0, False) — 분기 뒤
        if "Q" in p:
            year = p[:4]
            # 분기 숫자는 언제나 'Q' 뒤에 있다. 예전에는 대시가 있으면 `p[5:]` 로
            # 잘랐는데, 이 모듈이 `formatPeriod` 로 만드는 표준형이 바로 '2024-Q1'
            # 이라 그 경우 'Q1' 을 int 로 넘겨 ValueError 가 났다. 그러면 키가 전부
            # (0,0,0) 으로 같아져 max 가 입력 첫 원소를 돌려줬고, 호출부가 set 을
            # list 로 넘기기 때문에 실행마다 답이 달라졌다.
            q = p[p.index("Q") + 1 :]
            try:
                return (int(year), int(q), 1)
            except ValueError:
                return (0, 0, 0)
        if len(p) == 4 and p.isdigit():
            return (int(p), 0, 0)
        return (0, 0, 0)

    return max(pool, key=_sortKey)


_ASOF_QUARTER_RE = re.compile(r"^(\d{4})[Qq]([1-4])$")
_ASOF_DATE_RE = re.compile(r"^(\d{4})-(\d{1,2})-\d{1,2}$")
_ASOF_YEAR_RE = re.compile(r"^(\d{4})$")


def parseAsOfPeriod(value: str) -> tuple[int | None, int | None]:
    """as-of 표기를 (연도, 분기) 로 읽는다. 못 읽으면 (None, None).

    받는 표기는 셋이다. "2024Q3" 처럼 붙여 쓴 분기, "2024-06-30" 같은 ISO 날짜,
    "2024" 같은 연도. 연도만 오면 분기는 None 이고, 그것은 "그 해 전체" 를 뜻한다.

    `parsePeriod` 와 다르다. 그쪽은 이 모듈이 만드는 표준형 "2024-Q1" 을 읽는다.
    이쪽은 사용자와 표 머리글에서 오는 흔들리는 표기를 받는다.

    Args:
        value: as-of 표기 또는 표 컬럼 머리글.

    Returns:
        (연도, 분기). 분기를 알 수 없으면 두 번째가 None. 표기를 못 읽으면 둘 다 None.
    """
    raw = str(value or "").strip()
    if not raw:
        return None, None
    match = _ASOF_QUARTER_RE.match(raw)
    if match:
        return int(match.group(1)), int(match.group(2))
    match = _ASOF_DATE_RE.match(raw)
    if match:
        month = int(match.group(2))
        return int(match.group(1)), (month - 1) // 3 + 1
    match = _ASOF_YEAR_RE.match(raw)
    if match:
        return int(match.group(1)), None
    return None, None


def dropPeriodsAfter(df: Any, asOf: str) -> Any:
    """as-of 시점 이후의 기간 컬럼을 떨군다. 미래 정보 누설 차단.

    가로형 재무 표는 컬럼 머리글이 곧 기간이다 ("2025Q4", "2024"). 시점 X 의 분석을
    재현할 때 X 이후 컬럼이 그대로 남으면 그 답은 그때 알 수 없던 것을 본 답이 된다.

    기간으로 읽히지 않는 머리글(항목명, snakeId 같은 것)은 그대로 둔다. as-of 자체를
    못 읽으면 아무것도 떨구지 않는다. 못 읽은 것을 미래로 단정하면 멀쩡한 표가 빈다.

    Args:
        df: 가로형 polars DataFrame.
        asOf: as-of 표기. `parseAsOfPeriod` 가 읽는 셋 중 하나.

    Returns:
        기간 컬럼이 걸러진 DataFrame. 떨굴 것이 없으면 입력 그대로.
    """
    asOfYear, asOfQuarter = parseAsOfPeriod(asOf)
    if asOfYear is None:
        return df
    keepCols: list[str] = []
    for col in df.columns:
        colYear, colQuarter = parseAsOfPeriod(col)
        if colYear is None:
            keepCols.append(col)
            continue
        if colYear < asOfYear:
            keepCols.append(col)
        elif colYear == asOfYear and (colQuarter is None or asOfQuarter is None or colQuarter <= asOfQuarter):
            keepCols.append(col)
    return df.select(keepCols) if len(keepCols) < len(df.columns) else df
