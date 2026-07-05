"""회사 프로파일러 : PIT 버전드 형질 상태 (L2.5 simulate, 골격).

프로파일은 예측이 아니라 상태다 (11 §2). 봉인·채점 대상이 아니라 형질마다 기준일(asOf)과
출처가 붙은 사실이며, 검증은 재현성(같은 asOf 재계산 = 동일)과 look-ahead 카나리아(asOf 이후
데이터 미참조)로 한다. 형질 조건부 실측(유상증자 x CB발행 이력 = 드리프트 1.5배)이 프로파일러
예측 기여의 실증이다.

깊이 원칙: 형질 등재는 손 선별이 아니라 전수 (11 §2 8축). 본 골격은 축별 대표 형질만 채우고
(자금조달 이력·재무 비율·시장 미시), 전수 카탈로그 열거는 R4 확장. 어떤 형질이 예측에
기여하는지는 성적표(형질 버킷)가 도태시킨다.

Layer: L2.5 simulate. table 벌크 직독만 소비 (Company 객체 0). asOf 이전 데이터만 참조.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.simulate import table as _table

# 자금조달·거버넌스 형질용 이벤트 타입 (희석·연쇄 신호). v2 정규화 하위타입 기준.
_FINANCING_EVENTS = ("전환사채권발행결정", "유상증자결정", "신주인수권부사채권발행결정")
_GOVERNANCE_EVENTS = ("최대주주변경", "불성실공시법인지정", "감자결정")
_TRAIT_LOOKBACK_DAYS = 730  # 자금조달 이력 집계 창 (형질 실측 근거와 동일)


def profile(code: str, asOf: str, *, baseDir: Path | None = None, dataDir: Path | None = None) -> dict:
    """한 회사의 PIT 형질 상태를 낸다 (asOf 'YYYYMMDD' 기준, 이후 데이터 미참조).

    Args:
        code: 6자리 종목코드.
        asOf: 기준일 'YYYYMMDD'. 이 날짜 이하로 공개된 데이터만 참조 (PIT).
        baseDir: (미사용, 시그니처 통일용).
        dataDir: 데이터 SSOT 루트 override.

    Returns:
        형질 dict. 각 형질에 값·출처·기준일(staleness). 결손은 None (0 대체 금지).
        {"code", "asOf", "fund": {...}, "financing": {...}, "governance": {...}, "market": {...}}.
    """
    return {
        "code": code,
        "asOf": asOf,
        "fund": _fundTraits(code, asOf, dataDir),
        "financing": _eventTraits(code, asOf, _FINANCING_EVENTS, dataDir),
        "governance": _eventTraits(code, asOf, _GOVERNANCE_EVENTS, dataDir),
        "market": _marketTraits(code, asOf, dataDir),
    }


def _fundTraits(code: str, asOf: str, dataDir: Path | None) -> dict:
    """재무 형질: asOf 이전 최신 공시 재무 + staleness (경과일)."""
    grid = _table.scanFinanceGrid(dataDir).filter((pl.col("code") == code) & (pl.col("rceptDate") <= asOf))
    if grid.height == 0:
        return {"latestRceptDate": None, "stalenessDays": None, "accounts": {}}
    latest = grid["rceptDate"].max()
    latestRows = grid.filter(pl.col("rceptDate") == latest)
    accounts = {r["account"]: r["amount"] for r in latestRows.iter_rows(named=True)}
    staleness = (pl.Series([asOf]).str.to_date("%Y%m%d")[0] - pl.Series([latest]).str.to_date("%Y%m%d")[0]).days
    return {"latestRceptDate": latest, "stalenessDays": staleness, "accounts": accounts}


def _eventTraits(code: str, asOf: str, types: tuple[str, ...], dataDir: Path | None) -> dict:
    """이벤트 형질: 회고창 내 해당 타입 공시 건수 (자금조달 연쇄·거버넌스 리스크)."""
    weekMap, _ = _table.weekCalendar(dataDir)
    ev = _table.eventWeekly(weekMap, dataDir)  # (code, week, reportType). 날짜는 weekMap 경유 주 근사.
    asOfWeek = weekMap.filter(pl.col("date") <= asOf)["week"]
    if asOfWeek.len() == 0:
        return dict.fromkeys(types, 0)
    maxWeek = int(asOfWeek.max())
    minWeek = maxWeek - int(_TRAIT_LOOKBACK_DAYS / 7)
    sub = ev.filter(
        (pl.col("code") == code)
        & (pl.col("week") <= maxWeek)
        & (pl.col("week") >= minWeek)
        & pl.col("reportType").is_in(list(types))
    )
    counts = {r["reportType"]: r["len"] for r in sub.group_by("reportType").len().iter_rows(named=True)}
    return {t: counts.get(t, 0) for t in types}


def _marketTraits(code: str, asOf: str, dataDir: Path | None) -> dict:
    """시장 미시 형질: asOf 시총 + 그날 전체 대비 시총 분위 (사이즈 형질)."""
    caps = _table.marketCap(dataDir).filter(pl.col("date") <= asOf)
    if caps.height == 0:
        return {"mktcap": None, "sizePctile": None, "asOfDate": None}
    latestDate = caps["date"].max()
    day = caps.filter(pl.col("date") == latestDate)
    row = day.filter(pl.col("code") == code)
    if row.height == 0:
        return {"mktcap": None, "sizePctile": None, "asOfDate": latestDate}
    mktcap = row["mktcap"][0]
    pctile = float((day["mktcap"] <= mktcap).mean())
    return {"mktcap": mktcap, "sizePctile": pctile, "asOfDate": latestDate}
