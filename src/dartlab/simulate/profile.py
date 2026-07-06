"""회사 프로파일러 : PIT 버전드 형질 상태 (L2.5 simulate, 골격).

프로파일은 예측이 아니라 상태다 (11 §2). 봉인·채점 대상이 아니라 형질마다 기준일(asOf)과
출처가 붙은 사실이며, 검증은 재현성(같은 asOf 재계산 = 동일)과 look-ahead 카나리아(asOf 이후
데이터 미참조)로 한다. 형질 조건부 실측(유상증자 x CB발행 이력 = 드리프트 1.5배)이 프로파일러
예측 기여의 실증이다.

깊이 원칙: 형질 등재는 손 선별이 아니라 전수 (11 §2 8축). 8 축(사업구조·관계그래프·자본조달·
거버넌스·노출벡터·시장미시·노동설비·서사)을 전부 등재하고, 어떤 축·형질이 예측에 기여하는지는
성적표(형질 버킷)가 도태시킨다. 죽은 형질도 목록에서 안 사라진다. 데이터 배선이 얕은 축(관계
상대방 파싱·매크로 베타·서사)은 값 대신 미가용 라벨로 격리(프로파일 재현성 보존).

검증: 재현성(replayIdentical = 같은 asOf 재계산 byte 일치) + look-ahead 카나리아(asOf 이후 데이터
미참조, 전 형질 asOf 필터). 프로파일은 예측이 아니라 상태라 봉인·채점 대상이 아니다 (11 §2).

Layer: L2.5 simulate. table 벌크 직독 + frame.inventory/narrative 소비 (Company 객체 0). asOf 이전만.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from dartlab.core.extractionCatalog import CATEGORIES, getConcept, getExtractionConcepts
from dartlab.simulate import estimate as _estimate
from dartlab.simulate import markets as _markets
from dartlab.simulate import table as _table
from dartlab.simulate.surfaces import FINANCING_EVENTS

# 자금조달·거버넌스 형질용 이벤트 타입 (희석·연쇄 신호). v2 정규화 하위타입 기준.
_FINANCING_EVENTS = FINANCING_EVENTS["KR"]  # SSOT = surfaces (credit 피드와 공유)
_GOVERNANCE_EVENTS = ("최대주주변경", "불성실공시법인지정", "감자결정")
# 관계 그래프(축2) 엣지 원천 이벤트 (계열·지분·대주주 신호).
_RELATIONSHIP_EVENTS = ("최대주주변경", "주식등의대량보유상황보고서", "임원ㆍ주요주주특정증권등소유상황보고서")
# 시장별 이벤트 형질 타입 (US = EDGAR form 정규화 타입, tableUs._US_FORM_EVENT 파생).
_EVENT_TRAIT_TYPES: dict[str, dict[str, tuple[str, ...]]] = {
    "KR": {"financing": _FINANCING_EVENTS, "governance": _GOVERNANCE_EVENTS, "relationship": _RELATIONSHIP_EVENTS},
    "US": {"financing": FINANCING_EVENTS["US"], "governance": ("auditDelay",), "relationship": ("largeHolding",)},
}
# 사업 구조(축1)·노동설비(축7) 형질 원천 카탈로그 카테고리.
_BUSINESS_CATEGORIES = ("segment",)
_LABOR_CATEGORIES = ("workforce", "segment")
_TRAIT_LOOKBACK_DAYS = 730  # 자금조달 이력 집계 창 (형질 실측 근거와 동일)
_BETA_WINDOW = 250  # 노출 벡터 베타 추정 트레일링 거래일 창


def traitCatalog() -> dict[str, int]:
    """형질 축 카탈로그: extractionCatalog 9 대분류별 개념 수 (전수 축 정의, 손 선별 0).

    Returns:
        {category: conceptCount}. 프로파일러의 형질 축은 이 카탈로그가 정하며 (11 §2 8축 골격),
        어떤 축·개념이 예측에 기여하는지는 성적표(형질 버킷)가 도태시킨다.
    """
    return {cat: len(getExtractionConcepts(category=cat)) for cat in CATEGORIES}


def profile(
    code: str,
    asOf: str,
    *,
    baseDir: Path | None = None,
    dataDir: Path | None = None,
    includeInventory: bool = False,
    marketNs: str = "kr",
) -> dict:
    """한 회사의 PIT 형질 상태를 낸다 (asOf 'YYYYMMDD' 기준, 이후 데이터 미참조).

    Args:
        code: 6자리 종목코드.
        asOf: 기준일 'YYYYMMDD'. 이 날짜 이하로 공개된 데이터만 참조 (PIT).
        baseDir: (미사용, 시그니처 통일용).
        dataDir: 데이터 SSOT 루트 override.
        includeInventory: True 면 사업보고서 전수 인벤토리 census 를 카탈로그 9축으로 그룹화해
            추가한다 (frame.inventory 경유, 현재 보고 상태 = live, PIT-replay 아님. 명시 라벨).
        marketNs: "kr" | "us" (인벤토리 census 시장).

    Returns:
        형질 dict (11 §2 8축): businessStructure·relationship·financing·governance·exposure·
        market·laborCapex·narrative + catalogAxes(9 대분류 정의) + fund + 선택 inventory.
        각 형질에 값·출처·라벨. 결손은 None (0 대체 금지). 얕은 축은 미가용 라벨.
    """
    out = {
        "code": code,
        "asOf": asOf,
        "catalogAxes": traitCatalog(),
        # 8 축 전수 (11 §2, 손 선별 0). 어떤 축·형질이 판독을 가르는지는 형질 성적표가 도태.
        "businessStructure": _businessStructure(code, marketNs),  # 축1
        "relationship": _relationshipEdges(code, asOf, dataDir),  # 축2
        "financing": _eventTraits(code, asOf, _FINANCING_EVENTS, dataDir),  # 축3
        "governance": _eventTraits(code, asOf, _GOVERNANCE_EVENTS, dataDir),  # 축4
        "exposure": _exposureVector(code, asOf, dataDir),  # 축5
        "market": _marketTraits(code, asOf, dataDir),  # 축6
        "laborCapex": _laborCapex(code, marketNs),  # 축7
        "narrative": _narrative(code, asOf, dataDir),  # 축8
        "fund": _fundTraits(code, asOf, dataDir),
    }
    if includeInventory:
        out["inventory"] = _inventoryCensus(code, marketNs)
    return out


def profileAll(asOf: str, *, dataDir: Path | None = None, market: str = "KR") -> pl.DataFrame:
    """전종목 프로파일 벌크 한 방 → (code, industry, mktcap, sizePctile, fundStalenessDays,
    <factor>Beta..., counterpartyCount, financingCount, governanceCount, relationshipCount,
    revenueE/netIncomeE ± 밴드).

    운영자 요구 "기업별 프로파일 모두 바로": per-company profile() 루프(회사당 수 초 + Panel 2GB)
    대신 벌크 스캔 5회로 전 유니버스 형질을 한 번에 세운다 (Company 객체 0, PIT = asOf 이전만).
    팩터 베타 열은 factors 레지스트리 전수 = 팩터 추가 자동흡수. E 열 = estimate 다음 분기 연장
    (p50 + p5/p95 밴드, 실적 뒤에 붙는 연장선의 프로파일 투영). census 축(inventory·narrative =
    Panel 로드 필요)은 미포함 명시 (개별 profile(code) 온디맨드, 정직 라벨).

    Args:
        asOf: 기준일 'YYYYMMDD'. dataDir: 데이터 SSOT 루트 override.
        market: "KR"|"US". US 는 industry(kindList)·베타(KR 가격상)·counterparty(allFilings) 축이
            미배선이라 그 열이 없다 (정직 부재, 채우면 자동 등장).

    Returns:
        전 유니버스(asOf 최근 거래일 시총 보유 종목) wide 형질 행렬. 결측 = null (0 대체 금지).

    Guide:
        - 전종목 형질: profileAll("20260612") -> 형질 버킷·조건부 성적표·cascade 입력.
        - US: profileAll("20260612", market="US").
    """
    tblM = _markets.tableModule(market) or _table
    # 축6 시장: asOf 최근일 시총 + 분위 (유니버스 정의)
    caps = tblM.marketCap(dataDir).filter(pl.col("date") <= asOf)
    if caps.height == 0:
        return pl.DataFrame(schema={"code": pl.Utf8})
    day = caps.filter(pl.col("date") == caps["date"].max())
    out = day.select("code", "mktcap").with_columns(sizePctile=pl.col("mktcap").rank() / day.height)
    if market == "KR":  # 축1 산업 (kindList, US 미배선)
        out = out.join(_table.industryMap(dataDir), on="code", how="left")
    # 축3·4·2 이벤트 형질: eventWeekly 1 스캔 → 회고창 타입군 카운트 (per-company 루프 0)
    weekMap, _ = tblM.weekCalendar(dataDir)
    ev = tblM.eventWeekly(weekMap, dataDir)
    asOfWeek = weekMap.filter(pl.col("date") <= asOf)["week"]
    types = _EVENT_TRAIT_TYPES.get(market, _EVENT_TRAIT_TYPES["KR"])
    if asOfWeek.len():
        maxW = int(asOfWeek.max())
        minW = maxW - int(_TRAIT_LOOKBACK_DAYS / 7)
        sub = ev.filter((pl.col("week") <= maxW) & (pl.col("week") >= minW))
        counts = sub.group_by("code").agg(
            financingCount=pl.col("reportType").is_in(list(types["financing"])).sum(),
            governanceCount=pl.col("reportType").is_in(list(types["governance"])).sum(),
            relationshipCount=pl.col("reportType").is_in(list(types["relationship"])).sum(),
        )
        out = out.join(counts, on="code", how="left")
    # 재무 신선도: scanFinanceGrid 1 스캔 → 종목별 최신 접수 경과일
    grid = tblM.scanFinanceGrid(dataDir).filter(pl.col("rceptDate") <= asOf)
    if grid.height:
        stale = (
            grid.group_by("code")
            .agg(latest=pl.col("rceptDate").max())
            .with_columns(
                fundStalenessDays=(
                    pl.lit(asOf).str.to_date("%Y%m%d") - pl.col("latest").str.to_date("%Y%m%d")
                ).dt.total_days()
            )
            .select("code", "fundStalenessDays")
        )
        out = out.join(stale, on="code", how="left")
    # 축5 노출: 전종목 전팩터 베타 (레지스트리 전수 = 자동흡수. 매크로 시리즈 글로벌 공유,
    # US 는 tableUs 가격 주입으로 동일 베타 축 확보 = 격자 오버레이 입력)
    pxInject = None if market == "KR" else tblM.dailyPrices(dataDir)
    out = out.join(_table.macroBetaByCodeWide(asOf, baseDir=dataDir, prices=pxInject), on="code", how="left")
    if market == "KR":
        # 축2 상대방: allFilings 1 스캔 distinct flr_nm (US flr 필드 미배선)
        out = out.join(_table.counterpartyCountsBulk(asOf, dataDir), on="code", how="left")
    # E 연장 투영: 다음 분기(h=1) 매출·순이익 E (p50 + p5/p95). 그리드 재사용 (추가 스캔 0).
    if grid.height:
        e = _estimate.estimateQuarters(grid, asOf=asOf, horizonQ=1, accounts=("revenue", "netIncome"))
        for acct, pfx in (("revenue", "revenueE"), ("netIncome", "netIncomeE")):
            sub = e.filter(pl.col("account") == acct).select(
                "code",
                pl.col("p50").alias(pfx),
                pl.col("p5").alias(f"{pfx}Lo"),
                pl.col("p95").alias(f"{pfx}Hi"),
                pl.col("period").alias(f"{pfx}Period"),
            )
            out = out.join(sub, on="code", how="left")
    return out.sort("code")


def replayHash(profileDict: dict) -> str:
    """프로파일 상태의 결정론 해시 (replay 항등성 검증: 같은 asOf 재계산 = 같은 해시, 06 §5c)."""
    import hashlib

    canonical = json.dumps(profileDict, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def replayIdentical(code: str, asOf: str, *, dataDir: Path | None = None, marketNs: str = "kr") -> bool:
    """같은 (code, asOf) 재계산이 byte 일치인지 (PIT replay 항등성 가드, 11 §2)."""
    a = profile(code, asOf, dataDir=dataDir, marketNs=marketNs)
    b = profile(code, asOf, dataDir=dataDir, marketNs=marketNs)
    return replayHash(a) == replayHash(b)


def marketBeta(retCode: np.ndarray, retMkt: np.ndarray) -> float:
    """시장 베타 = cov(code, mkt)/var(mkt) (노출 벡터 축5, OLS). 표본·분산 부족은 nan.

    cov·var 동일 ddof=0 = OLS 기울기 불편 (np.cov 기본 ddof=1 과 .var() 기본 ddof=0 혼용 시
    N/(N-1) 편향이라 명시 통일). 완전 상관이면 계수 정확 복원.
    """
    r, m = np.asarray(retCode, dtype=float), np.asarray(retMkt, dtype=float)
    ok = np.isfinite(r) & np.isfinite(m)
    if ok.sum() < 20 or m[ok].var() <= 0:
        return float("nan")
    return float(np.cov(r[ok], m[ok], ddof=0)[0, 1] / m[ok].var())


def _inventoryCensus(code: str, marketNs: str) -> dict:
    """사업보고서 전수 인벤토리를 카탈로그 9 대분류로 그룹화 (현재 보고 상태 = live, PIT 아님).

    frame.inventory.reportInventory 경유. 단위마다 conceptId 태깅을 카테고리로 접어 축별 단위
    수를 낸다. 실제 값 추출은 table.py 카탈로그 구동 라우팅 (핸들 소비). 실패/부재는 빈 census.
    """
    try:
        from dartlab.frame.inventory import reportInventory

        inv = reportInventory(code, marketNs=marketNs)
    except (ValueError, KeyError, AttributeError, TypeError, OSError, ImportError):
        return {"total": 0, "byCategory": {}, "note": "인벤토리 부재/실패"}
    byCat: dict[str, int] = dict.fromkeys(CATEGORIES, 0)
    for u in inv.get("units", []):
        cid = u.get("conceptId")
        concept = getConcept(cid) if cid else None
        cat = concept.category if concept else "filingMeta"
        byCat[cat] = byCat.get(cat, 0) + 1
    return {
        "total": inv.get("summary", {}).get("total", 0),
        "cataloguedUnits": inv.get("summary", {}).get("cataloguedUnits", 0),
        "byCategory": byCat,
        "pitLabel": "live(현재 보고 상태, PIT-replay 아님)",
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


def _businessStructure(code: str, marketNs: str) -> dict:
    """축1 사업 구조: 세그먼트 매출/이익·제품·수주잔고 형질 (사업보고서 인벤토리 census).

    extractionCatalog segment 카테고리 개념 단위 수를 인벤토리에서 열거 (현재 보고 상태 = live 라벨).
    실제 세그먼트 값 추출은 카탈로그 구동 라우팅 (핸들 소비). 부재/실패는 빈 형질.
    """
    try:
        from dartlab.frame.inventory import reportInventory

        inv = reportInventory(code, marketNs=marketNs)
    except (ValueError, KeyError, AttributeError, TypeError, OSError, ImportError):
        return {"segmentUnits": 0, "concepts": [], "pitLabel": "인벤토리 부재"}
    concepts: dict[str, int] = {}
    for u in inv.get("units", []):
        cid = u.get("conceptId")
        concept = getConcept(cid) if cid else None
        if concept and concept.category in _BUSINESS_CATEGORIES:
            concepts[cid] = concepts.get(cid, 0) + 1
    return {
        "segmentUnits": sum(concepts.values()),
        "concepts": sorted(concepts),
        "pitLabel": "live(현재 보고 상태, PIT-replay 아님)",
    }


def _relationshipEdges(code: str, asOf: str, dataDir: Path | None) -> dict:
    """축2 관계 그래프: 계열/지분·대주주·공급 엣지 + 상대방 실명 (11 §2). 전파 층(cascade) 입력.

    관계 이벤트 타입별 건수(엣지 밀도) + 대량보유·임원소유·최대주주변경 공시 제출인(flr_nm)을
    상대방 실명으로 파싱(table.counterpartyFilings). asOf 이전만 참조. cascade 축2 전파의 노드 원천.
    """
    counts = _eventTraits(code, asOf, _RELATIONSHIP_EVENTS, dataDir)
    cps = _table.counterpartyFilings(code, asOf, dataDir)
    counterparties = [
        {"counterparty": r["counterparty"], "count": int(r["count"])} for r in cps.head(10).iter_rows(named=True)
    ]
    edges = [{"type": t, "count": c} for t, c in counts.items() if c]
    return {
        "edgeCount": sum(counts.values()),
        "edges": edges,
        "counterparties": counterparties,
        "distinctCounterparties": cps.height,
    }


def _macroBetas(oneRet: pl.DataFrame, dataDir: Path | None) -> dict:
    """종목 일수익(oneRet: date, ret) vs 금리·환율·유가 변화 단변량 베타 (11 §2 축5 macroBeta).

    거시 팩터(table.macroDaily)를 종목 거래일에 forward-fill 후 팩터별 변화에 대한 OLS 베타.
    금리는 수준 차분(%p), 환율·유가는 수익률. 표본<20 또는 매크로 부재는 None (0 대체 금지).
    """
    from dartlab.simulate.factors import factorBetaMap, macroChange

    macro = _table.macroDaily(dataDir)
    facMap = factorBetaMap()  # 레지스트리 SSOT (팩터 추가 = 축5 자동흡수)
    if macro.height == 0:
        return dict.fromkeys(facMap.values(), None)
    ffill = [pl.col(f).forward_fill() for f in facMap if f in macro.columns]
    fac = oneRet.join(macro, on="date", how="left").sort("date").with_columns(ffill)
    out: dict = {}
    for factor, key in facMap.items():
        if factor not in fac.columns:
            out[key] = None
            continue
        d = fac.select("ret", dfac=macroChange(factor)).drop_nulls()
        b = marketBeta(d["ret"].to_numpy(), d["dfac"].to_numpy()) if d.height >= 20 else float("nan")
        # 팩터 무변동(금리 window flat 등) = var 0 = nan → None (0 대체 금지, replay 결정론 유지).
        out[key] = None if b != b else b
    return out


def _exposureVector(code: str, asOf: str, dataDir: Path | None) -> dict:
    """축5 노출 벡터: 시장 베타 + 금리·환율·유가 macroBeta + 수익 변동성 (PIT 트레일링, 11 §2).

    가격 자급 시장 베타(등가중 대비) + 거시 3팩터 단변량 베타(table.macroDaily). asOf 이전 거래일만,
    트레일링 _BETA_WINDOW. 노출은 상태(형질)라 봉인·채점 아님 = 형질 조건부 성적표가 예측 기여 도태.
    """
    px = _table.dailyPrices(dataDir).filter((pl.col("close") > 0) & (pl.col("date") <= asOf)).sort(["code", "date"])
    px = px.with_columns(ret=(pl.col("close") / pl.col("close").shift(1).over("code") - 1))
    mkt = px.group_by("date").agg(mktRet=pl.col("ret").median()).sort("date")
    one = px.filter(pl.col("code") == code).select("date", "ret").join(mkt, on="date", how="inner").tail(_BETA_WINDOW)
    if one.height < 20:
        return {
            "marketBeta": None,
            "retVol": None,
            "nDays": one.height,
            "rateBeta": None,
            "fxBeta": None,
            "oilBeta": None,
        }
    beta = marketBeta(one["ret"].to_numpy(), one["mktRet"].to_numpy())
    vol = float(one["ret"].std() or 0.0)
    macroBetas = _macroBetas(one.select("date", "ret"), dataDir)
    return {"marketBeta": beta, "retVol": vol, "nDays": one.height, **macroBetas}


def _laborCapex(code: str, marketNs: str) -> dict:
    """축7 노동·설비: 직원 수·capex·생산능력 형질 (workforce/segment 카탈로그 개념 census)."""
    try:
        from dartlab.frame.inventory import reportInventory

        inv = reportInventory(code, marketNs=marketNs)
    except (ValueError, KeyError, AttributeError, TypeError, OSError, ImportError):
        return {"workforceUnits": 0, "concepts": [], "pitLabel": "인벤토리 부재"}
    concepts: dict[str, int] = {}
    for u in inv.get("units", []):
        cid = u.get("conceptId")
        concept = getConcept(cid) if cid else None
        if concept and concept.category in _LABOR_CATEGORIES:
            concepts[cid] = concepts.get(cid, 0) + 1
    return {
        "workforceUnits": sum(concepts.values()),
        "concepts": sorted(concepts),
        "pitLabel": "live(현재 보고 상태, PIT-replay 아님)",
    }


def _narrative(code: str, asOf: str, dataDir: Path | None) -> dict:
    """축8 서사 형질: 리스크 문단 변화·신사업 키워드 (frame/narrative). 부재/실패는 미가용 라벨.

    frame.narrative 는 정성 단일 메커니즘(panel-extraction-workbench-ssot)이라 API 시그니처가
    갱신될 수 있어, 실패는 예외 아니라 미가용 라벨로 격리한다 (프로파일 전체 재현성 보존).
    """
    try:
        from dartlab.frame.narrative import listNarrativeConcepts
    except ImportError:
        return {"available": False, "reason": "frame.narrative 미배선"}
    try:
        concepts = listNarrativeConcepts()
    except (ValueError, KeyError, AttributeError, TypeError, OSError) as e:
        return {"available": False, "reason": type(e).__name__}
    ids = [c.get("conceptId") for c in concepts if c.get("conceptId")]
    return {
        "available": True,
        "conceptCount": len(ids),
        "concepts": sorted(ids),
        "note": "서사 개념 census. 본문 추출은 extractNarrative(code, conceptId) 온디맨드(panel).",
    }
