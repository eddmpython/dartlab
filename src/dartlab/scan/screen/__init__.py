"""멀티팩터 스크리닝 -- 프리셋 또는 spec 조건으로 종목 필터링.

프리셋:
    value       -- 가치투자 후보 (저PBR + 이익 양호 + 부채 안전)
    dividend    -- 배당 성장 우량주 (연속증가/안정 + 부채 안전)
    growth      -- 균형 성장주 (고성장 + 수익 우수 + 이익 양호)
    risk        -- 위험 기업 (부채 고위험 OR 감사 고위험 OR 유동성 위험)
    quality     -- 퀄리티 팩터 (수익 우수 + 이익 우수 + 효율 우수)
    all         -- 전 프리셋 플래그 통합

사용법::

    dartlab.scan("screen")              # 프리셋 목록
    dartlab.scan("screen", "value")     # 가치투자 후보
    dartlab.scan("screen", "risk")      # 위험 기업
    dartlab.scan("screen", "all")       # 전체 플래그 통합
    dartlab.scan("screen", spec={
        "where": [{"field": "finance.ratio.roe", "op": ">", "value": 10}],
        "select": ["valuation.pbr", "krx.marketCap"],
        "sort": {"field": "finance.ratio.roe", "desc": True},
        "limit": 30,
    })
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from dartlab.core.logger import getLogger

_log = getLogger(__name__)

# 저장된 명명 스크린 config 거처 (운영자 수동 저작·review, accountMappings 급). scan 도메인 colocation.
_SCREENS_DIR = Path(__file__).resolve().parent.parent / "screens"


def listScreens() -> list[dict]:
    """저장된 명명 스크린 목록 (screens/*.json 메타). 미존재/파손 파일은 건너뛴다.

    Returns:
        [{id, title, tags, evidence, version}, ...] (id 정렬).

    Raises:
        없음. 디렉토리/파일 부재는 빈 목록으로 흡수.

    Example:
        >>> [s["id"] for s in listScreens()]  # doctest: +SKIP
    """
    out: list[dict] = []
    if not _SCREENS_DIR.is_dir():
        return out
    for p in sorted(_SCREENS_DIR.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        out.append(
            {
                "id": d.get("id", p.stem),
                "title": d.get("title", ""),
                "tags": d.get("tags", []),
                "evidence": d.get("evidence", ""),
                "version": d.get("version", 1),
            }
        )
    return out


def loadScreen(screenId: str) -> dict:
    """저장된 스크린의 실행 spec(dict)을 반환한다. 미존재/형식오류 시 ValueError.

    Args:
        screenId: screens/{id}.json 의 id (예 "financialStabilityDrawdown").

    Returns:
        executeScreenSpec 에 넣는 spec dict (define/where/any/select/sort/limit).

    Raises:
        ValueError: 미존재 id 또는 spec 누락/형식오류.

    Example:
        >>> loadScreen("financialStabilityDrawdown")["where"]  # doctest: +SKIP
    """
    p = _SCREENS_DIR / f"{screenId}.json"
    if not p.exists():
        avail = ", ".join(s["id"] for s in listScreens()) or "(없음)"
        raise ValueError(f"알 수 없는 저장 스크린: {screenId!r}. 가용: {avail}")
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(f"스크린 {screenId!r} 파싱 실패: {e}") from e
    spec = d.get("spec")
    if not isinstance(spec, dict):
        raise ValueError(f"스크린 {screenId!r} 에 spec dict 가 없습니다.")
    return spec


def watchedScreens() -> list[dict]:
    """왓처 구독 대상 스크린 목록 (JSON 의 ``notify: true`` opt-in). 운영자 제어.

    Returns:
        [{id, title}, ...] (notify=true 인 스크린만).

    Raises:
        없음. 디렉토리/파일 부재는 빈 목록.

    Example:
        >>> [s["id"] for s in watchedScreens()]  # doctest: +SKIP
    """
    out: list[dict] = []
    if not _SCREENS_DIR.is_dir():
        return out
    for p in sorted(_SCREENS_DIR.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if d.get("notify") is True:
            out.append({"id": d.get("id", p.stem), "title": d.get("title", "")})
    return out


def evaluateScreenMembers(screenId: str) -> list[dict]:
    """저장 스크린의 현재 멤버 종목을 평가한다 (왓처 구독 = 멤버십 스냅샷).

    ``executeScreenSpec(loadScreen(id))`` 를 돌려 현재 조건 충족 종목을 반환한다. 왓처가 스케줄마다 호출해
    직전 멤버셋과 diff(진입/이탈)를 낸다(허브 /active set-diff 커서). scan 은 stateless 평가만, 시간축 diff 는
    왓처가 소유한다(operation.notifyPipeline).

    Args:
        screenId: screens/{id}.json 의 id.

    Returns:
        [{stockCode, corpName}, ...] (현재 멤버). 데이터/스크린 부재 시 빈 목록.

    Raises:
        ValueError: 미존재 스크린 id (loadScreen 전파).

    Example:
        >>> evaluateScreenMembers("financialStabilityDrawdown")  # doctest: +SKIP
    """
    from dartlab.scan.builders.kr.report.fields import executeScreenSpec
    from dartlab.scan.rename import _enrichWithKorean

    spec = loadScreen(screenId)
    df = executeScreenSpec(spec)
    if df is None or df.is_empty() or "stockCode" not in df.columns:
        return []
    df = _enrichWithKorean(df)
    scCol = "종목코드" if "종목코드" in df.columns else "stockCode"
    nameCol = "종목명" if "종목명" in df.columns else None
    out: list[dict] = []
    for row in df.iter_rows(named=True):
        code = row.get(scCol)
        if not code:
            continue
        out.append({"stockCode": str(code), "corpName": row.get(nameCol) if nameCol else None})
    return out


_PRESETS = {
    "value": "가치투자 후보 (저PBR + 이익 양호 + 부채 안전)",
    "dividend": "배당 성장 우량주 (연속증가/안정 + 부채 안전)",
    "growth": "균형 성장주 (고성장 + 수익 우수 + 이익 양호)",
    "risk": "위험 기업 (부채 고위험 OR 감사 고위험 OR 유동성 위험)",
    "quality": "퀄리티 팩터 (수익 우수 + 이익 우수 + 효율 우수)",
    "cycle_recovery": "경기 회복 수혜 (경기민감 + 이익양호 + 저PBR)",
    "cycle_defensive": "경기 방어 (방어주 + 안정 재무 + 배당)",
    "all": "전 프리셋 플래그 통합",
}


def _loadAxis(name: str) -> pl.DataFrame:
    """scan 축 로드 (lazy import)."""
    import dartlab

    return dartlab.scan(name)


def _screenValue() -> pl.DataFrame:
    """가치투자 후보: 저PBR + 이익 양호+ + 부채 안전/관찰."""
    prof = _loadAxis("profitability")
    qual = _loadAxis("quality")
    debt = _loadAxis("debt")
    val = _loadAxis("valuation")

    goodProf = set(prof.filter(pl.col("등급").is_in(["우수", "양호", "보통"]))["종목코드"].to_list())
    goodQual = set(qual.filter(pl.col("등급").is_in(["우수", "양호"]))["종목코드"].to_list())
    safeDbt = set(debt.filter(pl.col("위험등급").is_in(["안전", "관찰"]))["종목코드"].to_list())
    lowPbr = set(
        val.filter((pl.col("PBR").is_not_null()) & (pl.col("PBR") > 0) & (pl.col("PBR") < 0.7))["종목코드"].to_list()
    )

    codes = goodProf & goodQual & safeDbt & lowPbr
    return val.filter(pl.col("종목코드").is_in(list(codes))).sort("PBR")


def _screenDividend() -> pl.DataFrame:
    """배당 성장 우량주: 연속증가/안정/증가 + 부채 안전/관찰."""
    div = _loadAxis("dividendTrend")
    debt = _loadAxis("debt")

    goodDiv = set(div.filter(pl.col("패턴").is_in(["연속증가", "안정", "증가"]))["종목코드"].to_list())
    safeDbt = set(debt.filter(pl.col("위험등급").is_in(["안전", "관찰"]))["종목코드"].to_list())

    codes = goodDiv & safeDbt
    return div.filter(pl.col("종목코드").is_in(list(codes))).sort("DPS성장", descending=True, nulls_last=True)


def _screenGrowth() -> pl.DataFrame:
    """균형 성장주: 고성장 + 수익 양호+ + 이익 양호+."""
    growth = _loadAxis("growth")
    prof = _loadAxis("profitability")
    qual = _loadAxis("quality")

    highGrowth = set(growth.filter(pl.col("등급").is_in(["고성장", "성장"]))["종목코드"].to_list())
    goodProf = set(prof.filter(pl.col("등급").is_in(["우수", "양호"]))["종목코드"].to_list())
    goodQual = set(qual.filter(pl.col("등급").is_in(["우수", "양호"]))["종목코드"].to_list())

    codes = highGrowth & goodProf & goodQual
    return growth.filter(pl.col("종목코드").is_in(list(codes))).sort("매출CAGR", descending=True, nulls_last=True)


def _screenRisk() -> pl.DataFrame:
    """위험 기업: 부채 고위험 OR 감사 고위험/주의 OR 유동성 위험."""
    debt = _loadAxis("debt")
    audit = _loadAxis("audit")
    liq = _loadAxis("liquidity")

    debtRisk = set(debt.filter(pl.col("위험등급") == "고위험")["종목코드"].to_list())
    auditRisk = set(audit.filter(pl.col("위험등급").is_in(["고위험", "주의"]))["종목코드"].to_list())
    liqRisk = set(liq.filter(pl.col("등급") == "위험")["종목코드"].to_list())

    allRisk = debtRisk | auditRisk | liqRisk

    rows: list[dict] = []
    for code in allRisk:
        flags = []
        if code in debtRisk:
            flags.append("부채")
        if code in auditRisk:
            flags.append("감사")
        if code in liqRisk:
            flags.append("유동성")
        # 형제 프리셋은 전부 '종목코드' 로 낸다. 이 자리만 'stockCode' 라서
        # 통합 프리셋(all)이 컬럼을 못 찾고 매 호출 죽었다.
        rows.append({"종목코드": code, "위험플래그": "+".join(flags), "위험수": len(flags)})

    if not rows:
        return pl.DataFrame()
    return pl.DataFrame(rows).sort("위험수", descending=True)


def _screenQuality() -> pl.DataFrame:
    """퀄리티 팩터: 수익 우수 + 이익 우수/양호 + 효율 우수/양호."""
    prof = _loadAxis("profitability")
    qual = _loadAxis("quality")
    eff = _loadAxis("efficiency")

    goodProf = set(prof.filter(pl.col("등급") == "우수")["종목코드"].to_list())
    goodQual = set(qual.filter(pl.col("등급").is_in(["우수", "양호"]))["종목코드"].to_list())
    goodEff = set(eff.filter(pl.col("등급").is_in(["우수", "양호"]))["종목코드"].to_list())

    codes = goodProf & goodQual & goodEff
    return prof.filter(pl.col("종목코드").is_in(list(codes))).sort("ROE", descending=True, nulls_last=True)


def _screenAll() -> pl.DataFrame:
    """전 프리셋 플래그 통합 - 종목별로 어떤 프리셋에 해당하는지."""
    vDf = _screenValue()
    dDf = _screenDividend()
    gDf = _screenGrowth()
    rDf = _screenRisk()
    qDf = _screenQuality()

    value = set(vDf["종목코드"].to_list()) if not vDf.is_empty() else set()
    dividend = set(dDf["종목코드"].to_list()) if not dDf.is_empty() else set()
    growth = set(gDf["종목코드"].to_list()) if not gDf.is_empty() else set()
    risk = set(rDf["종목코드"].to_list()) if not rDf.is_empty() else set()
    quality = set(qDf["종목코드"].to_list()) if not qDf.is_empty() else set()

    allCodes = value | dividend | growth | risk | quality
    rows: list[dict] = []
    for code in allCodes:
        flags = []
        if code in value:
            flags.append("value")
        if code in dividend:
            flags.append("dividend")
        if code in growth:
            flags.append("growth")
        if code in quality:
            flags.append("quality")
        if code in risk:
            flags.append("risk")
        rows.append({"stockCode": code, "프리셋": "+".join(flags), "프리셋수": len(flags)})

    if not rows:
        return pl.DataFrame()
    return pl.DataFrame(rows).sort("프리셋수", descending=True)


def _screenCycleRecovery() -> pl.DataFrame:
    """경기 회복 수혜: 경기민감(high beta) + 이익 양호 + 저PBR.

    실험 109-02: 회복기에 high cyclicality > defensive +51%p.
    macroBeta에서 GDP beta > 1.0 종목 = 경기민감.
    """
    try:
        macro = _loadAxis("macroBeta")
    except (ValueError, FileNotFoundError, OSError, pl.exceptions.PolarsError, ImportError):
        macro = pl.DataFrame()

    prof = _loadAxis("profitability")
    val = _loadAxis("valuation")
    debt = _loadAxis("debt")

    goodProf = set(prof.filter(pl.col("등급").is_in(["우수", "양호", "보통"]))["종목코드"].to_list())
    safeDbt = set(debt.filter(pl.col("위험등급").is_in(["안전", "관찰"]))["종목코드"].to_list())

    # macroBeta에서 경기민감 종목 (gdpBeta > 1.0)
    if not macro.is_empty() and "gdpBeta" in macro.columns:
        highBeta = set(macro.filter(pl.col("gdpBeta") > 1.0)["종목코드"].to_list())
    else:
        # macroBeta 데이터 없으면 profitability 전체로 fallback
        highBeta = goodProf

    # 저PBR
    lowPbr = set()
    if not val.is_empty() and "pbr" in val.columns:
        lowPbr = set(val.filter(pl.col("pbr") < 1.0)["종목코드"].to_list())
    elif not val.is_empty() and "PBR" in val.columns:
        lowPbr = set(val.filter(pl.col("PBR") < 1.0)["종목코드"].to_list())

    # 교집합 (저PBR이 있으면 포함, 없으면 경기민감+이익만)
    codes = highBeta & goodProf & safeDbt
    if lowPbr:
        codes = codes & lowPbr

    if not codes:
        return pl.DataFrame({"stockCode": [], "프리셋": []})
    return pl.DataFrame({"stockCode": sorted(codes), "프리셋": ["cycle_recovery"] * len(codes)})


def _screenCycleDefensive() -> pl.DataFrame:
    """경기 방어: 저베타(defensive) + 안정 재무 + 배당.

    실험 109-02: 둔화기에 defensive > high -7.4%p.
    macroBeta에서 GDP beta < 0.5 종목 = 방어주.
    """
    try:
        macro = _loadAxis("macroBeta")
    except (ValueError, FileNotFoundError, OSError, pl.exceptions.PolarsError, ImportError):
        macro = pl.DataFrame()

    debt = _loadAxis("debt")
    # 'dividend' 라는 축은 없다. 배당 패턴은 `dividendTrend` 가 '패턴' 컬럼으로 낸다.
    # 예전에는 없는 축 이름을 불러 이 프리셋이 매 호출 ValueError 로 죽었다.
    div_df = _loadAxis("dividendTrend")

    safeDbt = set(debt.filter(pl.col("위험등급").is_in(["안전", "관찰"]))["종목코드"].to_list())

    # 배당 안정 종목
    goodDiv = set()
    if not div_df.is_empty():
        for col in ["패턴", "분류", "유형"]:
            if col in div_df.columns:
                goodDiv = set(div_df.filter(pl.col(col).is_in(["연속증가", "안정", "증가"]))["종목코드"].to_list())
                break
        if not goodDiv:
            goodDiv = set(div_df["종목코드"].to_list())

    # 저베타 (defensive)
    if not macro.is_empty() and "gdpBeta" in macro.columns:
        lowBeta = set(macro.filter(pl.col("gdpBeta") < 0.5)["종목코드"].to_list())
    else:
        lowBeta = safeDbt  # fallback

    codes = lowBeta & safeDbt
    if goodDiv:
        codes = codes & goodDiv

    if not codes:
        return pl.DataFrame({"stockCode": [], "프리셋": []})
    return pl.DataFrame({"stockCode": sorted(codes), "프리셋": ["cycle_defensive"] * len(codes)})


_DISPATCH = {
    "value": _screenValue,
    "dividend": _screenDividend,
    "growth": _screenGrowth,
    "risk": _screenRisk,
    "quality": _screenQuality,
    "cycle_recovery": _screenCycleRecovery,
    "cycle_defensive": _screenCycleDefensive,
    "all": _screenAll,
}


def scanScreen(
    target: str | None = None,
    *,
    spec: dict | None = None,
    explain: bool = False,
    verbose: bool = True,
) -> pl.DataFrame | dict:
    """멀티팩터 스크리닝을 실행한다.

    Summary
    -------
    target 프리셋 또는 spec 조건으로 전종목 후보를 반환한다.

    Description
    -----------
    target 이 있으면 기존 value/dividend/growth/risk/quality 프리셋을 그대로
    실행한다. spec 이 있으면 `scan("fields")` 카탈로그의 field 키를 사용해
    where/select/sort/limit 조건을 실행한다. 두 경로는 분리되어 기존 프리셋
    동작을 바꾸지 않는다.

    Parameters
    ----------
    target : str | None
        프리셋 이름. None 이고 spec 도 None 이면 프리셋 목록을 반환한다.
    spec : dict | None
        조건형 스크리닝 명세. 예:
        ``{"where": [{"field": "finance.ratio.roe", "op": ">", "value": 10}]}``.
    explain : bool
        True면 멤버뿐 아니라 coverage, funnel, excluded, nearMiss, executionRef를
        포함한 설명 dict를 반환한다. 기본 False는 기존 DataFrame 계약을 유지한다.
    verbose : bool
        True 면 실행 로그를 logger.info 로 출력한다.

    Returns
    -------
    pl.DataFrame
        preset 목록 호출:
            preset : str - 프리셋 키.
            description : str - 프리셋 설명.
        preset 실행:
            stockCode/종목코드 : str - 후보 종목코드.
            축별 지표 컬럼 : object - 프리셋이 반환하는 지표.
        spec 실행:
            stockCode : str - 후보 종목코드.
            <field> : object - where/select/sort 에서 요청한 필드 값.
            docsHitCount : int - docs 조건 hit 수 (건), docs 조건 사용 시.
            docsBestScore : float - docs 최고 검색 점수 (점), docs 조건 사용 시.
            docsSnippet : str - 대표 공시 snippet (텍스트), docs 조건 사용 시.
        explain=True 실행:
            members : list[dict] - 기존 executor와 같은 후보.
            coverage/funnel/excluded/nearMiss : object - 3상태 판정 근거.

    Raises
    ------
    ValueError
        알 수 없는 프리셋, 잘못된 spec, 지원하지 않는 field/op/unit 인 경우.

    Examples
    --------
    >>> dartlab.scan("screen")
    >>> dartlab.scan("screen", "value")
    >>> dartlab.scan("screen", spec={
    ...     "where": [
    ...         {"field": "finance.ratio.roe", "op": ">", "value": 10},
    ...         {"field": "valuation.pbr", "op": "<", "value": 1},
    ...     ],
    ...     "select": ["krx.marketCap"],
    ...     "limit": 20,
    ... })

    Notes
    -----
    docs 조건은 검색 인덱스 hit 기반 후보 생성이다. 원문 전체 boolean scan 으로
    해석하지 않는다. krxIndex 필드는 종목별 값이 아니라 시장 컨텍스트라 select
    전용이다.

    Guide
    -----
    When: 시장 전체에서 후보 종목을 줄일 때.
    How: `scan("fields")` 로 필드를 찾고, 최소 3개 관점(finance/report/docs/krx
    등)을 조합한 뒤, 후보만 Company/analysis 로 심층 검증한다.
    Verified: 기존 프리셋 경로와 spec 경로가 같은 `scan("screen")` 진입점을 공유한다.

    Capabilities:
        - 8 프리셋 (value/dividend/growth/risk/quality/cycle_recovery/cycle_defensive/all) 또는
          custom spec 으로 멀티팩터 스크리닝. 프리셋은 여러 axis (profitability/quality/debt/
          valuation 등) 결과를 교집합으로 줄임.
        - spec 경로는 `executeScreenSpec` 위임 (`scan("fields")` 의 field 키 사용).

    AIContext:
        Agent 가 "저PBR + 부채 안전" 같은 multi-factor 질문 시 본 함수 dispatch. 프리셋
        있으면 그것 사용 - 새 조건이면 spec 으로 직접 구성 (먼저 `scan("fields")` 로
        field 가용성 확인 권장).

    Requires:
        - target 프리셋이 호출하는 모든 axis 의 prebuild parquet (profitability/quality/debt/
          valuation/...)
        - spec 사용 시 추가로 `scan("fields")` 카탈로그.

    See Also
    --------
    dartlab.scan("fields") : 조건에 사용할 field 검색.
    dartlab.scan("ratio") : 재무비율 primitive.
    dartlab.search : docs 텍스트 조건의 검색 인덱스.
    """
    if spec is not None:
        from dartlab.scan.builders.kr.fields import executeScreenSpec, executeScreenSpecDetailed

        if target is not None:
            raise ValueError("screen 은 target 프리셋과 spec 을 동시에 받을 수 없습니다.")
        if verbose:
            _log.info("screen(spec): 실행 중...")
        result = executeScreenSpecDetailed(spec) if explain else executeScreenSpec(spec)
        if verbose:
            count = result.get("memberCount", 0) if isinstance(result, dict) else result.shape[0]
            _log.info(f"screen(spec): {count}종목")
        return result

    if target is None:
        rows = [{"preset": k, "description": v} for k, v in _PRESETS.items()]
        rows += [{"preset": s["id"], "description": f"[저장] {s['title']}"} for s in listScreens()]
        return pl.DataFrame(rows)

    key = target.lower().strip()
    if key in _DISPATCH:
        if verbose:
            _log.info(f"screen({key}): 실행 중...")
        result = _DISPATCH[key]()
        if verbose:
            _log.info(f"screen({key}): {result.shape[0]}종목")
        return result

    # 프리셋이 아니면 저장된 명명 스크린(id 대소문자 보존) 실행. 미존재면 loadScreen 이 가용목록 포함 ValueError.
    from dartlab.scan.builders.kr.fields import executeScreenSpec, executeScreenSpecDetailed

    savedSpec = loadScreen(target.strip())
    if verbose:
        _log.info(f"screen({target}): 저장 스크린 실행")
    result = executeScreenSpecDetailed(savedSpec) if explain else executeScreenSpec(savedSpec)
    if verbose:
        count = result.get("memberCount", 0) if isinstance(result, dict) else result.shape[0]
        _log.info(f"screen({target}): {count}종목")
    return result


__all__ = ["evaluateScreenMembers", "listScreens", "loadScreen", "scanScreen", "watchedScreens"]
