"""40개 투자전략 룰엔진 — 순수 판정 함수.

각 전략은 매크로 데이터로부터 "활성/비활성/해당없음"을 판별하는 순수 함수다.
core/ 계층 소속 — macro/summary에서 소비.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategySignal:
    """투자전략 판정 결과."""

    id: int  # 전략 번호 (1-40)
    name: str  # 전략 이름
    active: bool | None  # True=활성, False=비활성, None=판별불가
    direction: str  # "bullish" | "bearish" | "neutral" | "na"
    description: str  # 현재 상황 해석


def evaluateStrategies(macroData: dict) -> list[StrategySignal]:
    """40개 투자전략 일괄 평가.

    Args:
        macroData: summary에서 수집된 전체 축 결과.
            keys: cycle, rates, assets, sentiment, liquidity,
                  forecast, crisis, inventory, trade

    Returns:
        list[StrategySignal]: 40개 전략별 활성/비활성 판정
    """
    results: list[StrategySignal] = []

    cycle = macroData.get("cycle") or {}
    rates = macroData.get("rates") or {}
    sentiment = macroData.get("sentiment") or {}
    liquidity = macroData.get("liquidity") or {}
    forecast = macroData.get("forecast") or {}
    crisis = macroData.get("crisis") or {}
    inventory = macroData.get("inventory") or {}
    trade = macroData.get("trade") or {}
    assets = macroData.get("assets") or {}

    # ── A. 경기순환 ──

    # 전략 1: 금리 추이는 전기비 성장률에 의해 결정된다
    rp = forecast.get("recessionProb") or {}
    rate_dir = (rates.get("outlook") or {}).get("direction")
    results.append(
        StrategySignal(
            1,
            "금리 = 전기비 성장률 결정",
            active=rate_dir is not None,
            direction="bearish" if rate_dir == "hike" else ("bullish" if rate_dir == "cut" else "neutral"),
            description=f"금리방향: {rate_dir or '판별불가'}, 침체확률: {rp.get('probability', '?')}",
        )
    )

    # 전략 2: 주가지수 ≈ 명목GDP
    nowcast = forecast.get("nowcast") or {}
    nc_active = nowcast.get("gdpEstimate") is not None
    results.append(
        StrategySignal(
            2,
            "주가 ≈ 명목GDP",
            active=nc_active,
            direction="bullish"
            if (nowcast.get("gdpEstimate") or 0) > 2
            else "bearish"
            if (nowcast.get("gdpEstimate") or 0) < 0
            else "neutral",
            description=nowcast.get("description", "nowcast 데이터 없음") if nc_active else "GDP nowcast 대기",
        )
    )

    # 전략 3: GDP 상대강도 → 환율
    rs = trade.get("leadingRelativeStrength") or {}
    results.append(
        StrategySignal(
            3,
            "GDP 상대강도 → 환율",
            active=rs.get("fxDirection") is not None,
            direction="bearish"
            if rs.get("fxDirection") == "krw_weaken"
            else "bullish"
            if rs.get("fxDirection") == "krw_strengthen"
            else "neutral",
            description=rs.get("description", "데이터 부족"),
        )
    )

    # 전략 4: 금리 = 미래 인플레 베팅
    inf = rates.get("inflation") or {}
    results.append(
        StrategySignal(
            4,
            "금리 = 미래 인플레 베팅",
            active=inf.get("state") is not None,
            direction="bearish"
            if inf.get("state") == "hot"
            else "bullish"
            if inf.get("state") in ("cool", "cold")
            else "neutral",
            description=f"물가: {inf.get('stateLabel', '?')}",
        )
    )

    # 전략 5: 한국주가 ≈ 미국소비
    usc = trade.get("usConsumptionLink") or {}
    results.append(
        StrategySignal(
            5,
            "한국주가 ≈ 미국소비",
            active=usc.get("usRetailYoy") is not None,
            direction="bullish"
            if (usc.get("usRetailYoy") or 0) > 5
            else "bearish"
            if (usc.get("usRetailYoy") or 0) < -2
            else "neutral",
            description=usc.get("implication", "데이터 부족"),
        )
    )

    # 전략 6~9: 사이클 관련
    phase = cycle.get("phase", "")
    results.append(
        StrategySignal(
            6,
            "실물투자 → 경기변동",
            active=phase != "",
            direction="bullish" if phase in ("recovery", "expansion") else "bearish",
            description=f"사이클: {cycle.get('phaseLabel', '?')}",
        )
    )

    ip = inventory.get("inventoryPhase") or {}
    results.append(
        StrategySignal(
            7,
            "재고흐름 → 서프라이즈",
            active=ip.get("phase") is not None,
            direction=ip.get("equityImplication", "neutral"),
            description=ip.get("description", "데이터 부족"),
        )
    )
    results.append(
        StrategySignal(
            8,
            "재고순환 → 주가예측",
            active=ip.get("phase") is not None,
            direction=ip.get("equityImplication", "neutral"),
            description=f"재고비율: {ip.get('ratio', '?')}, {ip.get('phaseLabel', '?')}",
        )
    )
    results.append(
        StrategySignal(
            9,
            "침체탈출 = 정부지출",
            active=phase == "recovery",
            direction="bullish" if phase == "recovery" else "neutral",
            description="경기 회복 시 정부지출 역할 활성",
        )
    )

    # 전략 10: 한국주가 = 수출기업
    ep = trade.get("exportProfit") or {}
    results.append(
        StrategySignal(
            10,
            "한국주가 = 수출기업",
            active=ep.get("signal") is not None,
            direction="bullish"
            if ep.get("signal", "").startswith("positive") or ep.get("signal", "").startswith("strong_positive")
            else "bearish"
            if "negative" in ep.get("signal", "")
            else "neutral",
            description=ep.get("description", "데이터 부족"),
        )
    )

    # 전략 11-12: 교역조건
    tot = trade.get("termsOfTrade") or {}
    results.append(
        StrategySignal(
            11,
            "교역조건 = 최선행",
            active=tot.get("direction") is not None,
            direction="bullish"
            if tot.get("direction") == "improving"
            else "bearish"
            if tot.get("direction") == "deteriorating"
            else "neutral",
            description=tot.get("description", "데이터 부족"),
        )
    )

    tp = trade.get("totProxy") or {}
    results.append(
        StrategySignal(
            12,
            "ToT대용치 = 환율-유가",
            active=tp.get("value") is not None,
            direction="bullish"
            if tp.get("direction") == "improving"
            else "bearish"
            if tp.get("direction") == "deteriorating"
            else "neutral",
            description=tp.get("description", "데이터 부족"),
        )
    )

    # 전략 13: ISM 바로미터
    ism_alloc = inventory.get("ismAllocation") or {}
    results.append(
        StrategySignal(
            13,
            "ISM = 자산배분 바로미터",
            active=ism_alloc.get("stance") is not None,
            direction="bullish"
            if ism_alloc.get("stance") == "risk_on"
            else "bearish"
            if ism_alloc.get("stance") == "risk_off"
            else "neutral",
            description=ism_alloc.get("description", "데이터 부족"),
        )
    )

    # 전략 14: 양국 선행지수 → 환율
    results.append(
        StrategySignal(
            14,
            "양국 선행지수 → 환율",
            active=rs.get("fxDirection") is not None,
            direction="bearish" if rs.get("fxDirection") == "krw_weaken" else "bullish",
            description=rs.get("description", "데이터 부족"),
        )
    )

    # 전략 15: 후행지수 상승 + 120일선 반등
    lei = forecast.get("lei") or {}
    lag_m = lei.get("lagMomentum")
    results.append(
        StrategySignal(
            15,
            "후행상승 + 120일선 반등",
            active=lag_m is not None and lag_m > 0,
            direction="bullish" if lag_m is not None and lag_m > 0 else "neutral",
            description=f"후행지수 모멘텀 {lag_m:+.2f}" if lag_m is not None else "후행지수 데이터 없음",
        )
    )

    # 전략 16: 전기비성장률 = 선행+후행
    results.append(
        StrategySignal(
            16,
            "전기비성장률 = 선행+후행",
            active=lei.get("signal") is not None or lei.get("growthSignal") is not None,
            direction="bullish"
            if lei.get("signal") == "expansion" or lei.get("growthSignal") == "expanding"
            else "bearish"
            if lei.get("signal") == "recession_warning" or lei.get("growthSignal") == "contracting"
            else "neutral",
            description=lei.get("description", lei.get("growthLabel", "데이터 부족")),
        )
    )

    # 전략 17: 고용지표
    emp = rates.get("employment") or {}
    results.append(
        StrategySignal(
            17,
            "고용지표 주목",
            active=emp.get("state") is not None,
            direction="bullish"
            if emp.get("state") == "strong"
            else "bearish"
            if emp.get("state") == "weak"
            else "neutral",
            description=f"고용: {emp.get('stateLabel', '?')}",
        )
    )

    # 전략 18: 한국물가 = 환율+유가
    tot_proxy = trade.get("totProxy") or {}
    tot_comps = tot_proxy.get("components") or {}
    fx_yoy = tot_comps.get("fxYoy")
    oil_yoy = tot_comps.get("oilYoy")
    if fx_yoy is not None and oil_yoy is not None:
        inf_pressure = fx_yoy * 0.06 + oil_yoy * 0.03
        results.append(
            StrategySignal(
                18,
                "한국물가 = 환율+유가",
                active=True,
                direction="bearish" if inf_pressure > 0.5 else "bullish" if inf_pressure < -0.5 else "neutral",
                description=f"환율({fx_yoy:+.1f}%)+유가({oil_yoy:+.1f}%) → 물가압력 {inf_pressure:+.1f}%p",
            )
        )
    else:
        results.append(
            StrategySignal(
                18, "한국물가 = 환율+유가", active=False, direction="neutral", description="환율/유가 데이터 없음"
            )
        )

    # 전략 19-22: 금리/통화정책
    results.append(
        StrategySignal(
            19,
            "통화정책 = 투자 마일스톤",
            active=rate_dir is not None,
            direction="bullish" if rate_dir == "cut" else "bearish" if rate_dir == "hike" else "neutral",
            description=f"통화정책 방향: {rate_dir or '?'}",
        )
    )

    # 전략 20: 장단기차 — rates에서 term spread 변화
    expect = rates.get("expectation") or {}
    spread_2y = expect.get("spread2yFf")
    results.append(
        StrategySignal(
            20,
            "금리정책 전후 장단기차",
            active=spread_2y is not None,
            direction="bullish"
            if rate_dir == "cut" and spread_2y is not None and spread_2y < -0.5
            else "bearish"
            if rate_dir == "hike" and spread_2y is not None and spread_2y > 0.5
            else "neutral",
            description=f"2Y-FF 스프레드 {spread_2y:+.2f}%p" if spread_2y is not None else "데이터 없음",
        )
    )

    # 전략 21: 금리↔주가 역학
    asset_signals = assets.get("signals") or []
    equity_up = any(
        s.get("direction") == "up" for s in asset_signals if isinstance(s, dict) and s.get("asset") == "equity"
    )
    results.append(
        StrategySignal(
            21,
            "금리↔주가 역학관계",
            active=rate_dir is not None,
            direction="bearish" if rate_dir == "hike" else "bullish" if rate_dir == "cut" else "neutral",
            description=f"금리 {rate_dir or '?'} — 금리/주가 역학",
        )
    )

    results.append(
        StrategySignal(
            22,
            "물가과열 → 긴축 → 선행하락",
            active=inf.get("state") is not None,
            direction="bearish" if inf.get("state") == "hot" else "neutral",
            description=f"물가 {inf.get('stateLabel', '?')} — {'과열→긴축 체인 활성' if inf.get('state') == 'hot' else '안정'}",
        )
    )

    # 전략 23-27: 환율/달러
    dsh = crisis.get("dollarSafeHaven") or {}
    dxy_chg = dsh.get("dxyChange3m")

    results.append(
        StrategySignal(
            23,
            "달러하락 → 신흥국",
            active=dxy_chg is not None,
            direction="bullish" if dxy_chg is not None and dxy_chg < -2 else "neutral",
            description=f"달러 {dxy_chg:+.1f}% — {'신흥국 유리' if dxy_chg is not None and dxy_chg < -2 else '해당없음'}"
            if dxy_chg is not None
            else "달러 데이터 없음",
        )
    )
    results.append(
        StrategySignal(
            24,
            "달러강세 → 미국국채",
            active=dxy_chg is not None,
            direction="bullish" if dxy_chg is not None and dxy_chg > 2 else "neutral",
            description=f"달러 {dxy_chg:+.1f}% — {'미국국채 유리' if dxy_chg is not None and dxy_chg > 2 else '해당없음'}"
            if dxy_chg is not None
            else "달러 데이터 없음",
        )
    )

    # 전략 25: 달러↔금 — assets 금 3요인에서 dollarEffect
    gold_drivers = assets.get("goldDrivers") or {}
    dollar_eff = gold_drivers.get("dollarEffect")
    results.append(
        StrategySignal(
            25,
            "달러↔금 대체",
            active=dollar_eff is not None,
            direction="bullish"
            if dollar_eff is not None and dollar_eff < 0
            else "bearish"
            if dollar_eff is not None and dollar_eff > 0
            else "neutral",
            description=f"달러효과 {dollar_eff:+.2f}" if dollar_eff is not None else "금 3요인 없음",
        )
    )

    # 전략 26: EM 물가 → 달러
    kr_inf_state = inf.get("state", "")
    results.append(
        StrategySignal(
            26,
            "신흥국 물가 → 달러상승",
            active=kr_inf_state != "",
            direction="bearish" if kr_inf_state == "hot" else "neutral",
            description=f"KR 물가 {inf.get('stateLabel', '?')} — {'EM 물가 압력→달러 강세' if kr_inf_state == 'hot' else '안정'}",
        )
    )

    # 전략 27: 원/달러 하락 → 내수주
    usdkrw_proxy = tot_comps.get("fxYoy")
    results.append(
        StrategySignal(
            27,
            "원/달러 하락 → 내수주",
            active=usdkrw_proxy is not None,
            direction="bullish" if usdkrw_proxy is not None and usdkrw_proxy < -3 else "neutral",
            description=f"USDKRW YoY {usdkrw_proxy:+.1f}% — {'원화강세→내수주 유리' if usdkrw_proxy is not None and usdkrw_proxy < -3 else '해당없음'}"
            if usdkrw_proxy is not None
            else "환율 데이터 없음",
        )
    )

    # 전략 28: 금리상승 = 경기회복 전제
    results.append(
        StrategySignal(
            28,
            "금리상승 = 경기회복 전제",
            active=rate_dir is not None and phase != "",
            direction="bearish" if rate_dir == "hike" and phase not in ("recovery", "expansion") else "neutral",
            description=f"금리 {rate_dir or '?'} + 사이클 {cycle.get('phaseLabel', '?')} — {'경기 뒷받침 없는 금리상승 경고' if rate_dir == 'hike' and phase not in ('recovery', 'expansion') else '정상'}",
        )
    )

    # 전략 29: 한국금리 = 내수
    results.append(
        StrategySignal(
            29,
            "한국금리 = 내수반영",
            active=phase != "",
            direction="bullish"
            if phase in ("recovery", "expansion")
            else "bearish"
            if phase == "contraction"
            else "neutral",
            description=f"사이클 {cycle.get('phaseLabel', '?')} → 한국 내수 {'확장' if phase in ('recovery', 'expansion') else '수축'}",
        )
    )

    # 전략 30: 장단기차 → CLI 선행
    cli_mom = lei.get("cliMomentum")
    results.append(
        StrategySignal(
            30,
            "장단기차 → CLI 선행",
            active=spread_2y is not None,
            direction="bullish"
            if spread_2y is not None and spread_2y > 0
            else "bearish"
            if spread_2y is not None and spread_2y < -0.5
            else "neutral",
            description=f"금리차 {spread_2y:+.2f}%p → CLI 방향 선행" if spread_2y is not None else "데이터 없음",
        )
    )

    # 전략 31: ToT → 수출이익
    results.append(
        StrategySignal(
            31,
            "ToT대용치 → 수출이익",
            active=ep.get("signal") is not None,
            direction="bullish"
            if ep.get("signal", "").startswith("positive") or ep.get("signal", "").startswith("strong_positive")
            else "bearish"
            if "negative" in ep.get("signal", "")
            else "neutral",
            description=ep.get("description", "데이터 부족"),
        )
    )

    # 전략 32: 신용스프레드 → 설비투자
    cp = crisis.get("capexPressure") or {}
    results.append(
        StrategySignal(
            32,
            "신용스프레드 = 설비투자 압력",
            active=cp.get("pressure") is not None,
            direction="bullish"
            if cp.get("pressure") == "easing"
            else "bearish"
            if cp.get("pressure") == "tightening"
            else "neutral",
            description=cp.get("description", "데이터 부족"),
        )
    )

    # 전략 33: 공급과잉 → 도산 — 재고 적극감축 + HY 스프레드 상승
    inv_phase = ip.get("phase", "")
    capex_pr = cp.get("pressure", "")
    results.append(
        StrategySignal(
            33,
            "공급과잉 → 도산",
            active=inv_phase == "active_destock" or capex_pr == "tightening",
            direction="bearish" if inv_phase == "active_destock" and capex_pr == "tightening" else "neutral",
            description=f"재고 {ip.get('phaseLabel', '?')} + 설비투자 {cp.get('pressureLabel', '?')}",
        )
    )

    # 전략 34: ISM<55 → 인상종결
    ism_bar = inventory.get("ismBarometer") or {}
    results.append(
        StrategySignal(
            34,
            "ISM<55 → 인상종결",
            active=ism_bar.get("rateImplication") == "hike_end",
            direction="bullish" if ism_bar.get("rateImplication") == "hike_end" else "neutral",
            description=f"ISM: {ism_bar.get('level', '?')}, 금리: {ism_bar.get('rateLabel', '해당없음')}",
        )
    )

    # 전략 35: 국내신용위험 ↔ CPI
    kr_cr = crisis.get("krCreditRisk") or {}
    results.append(
        StrategySignal(
            35,
            "국내신용위험 ↔ CPI",
            active=kr_cr.get("cpiYoy") is not None,
            direction="bearish" if (kr_cr.get("cpiYoy") or 0) > 4 else "neutral",
            description=kr_cr.get("signal", "KR 전용"),
        )
    )

    # 전략 36: 중국 통화 → 원자재 — 구리 가격으로 프록시
    # 중국 M2 직접 접근 불가. 구리 = 중국 수요 프록시
    copper_gold = assets.get("copperGold") or {}
    cg_impl = copper_gold.get("implication")
    results.append(
        StrategySignal(
            36,
            "중국 통화 → 원자재",
            active=cg_impl is not None,
            direction="bullish" if cg_impl == "expansion" else "bearish" if cg_impl == "contraction" else "neutral",
            description=copper_gold.get("description", "Cu/Au 데이터로 프록시"),
        )
    )

    # 전략 37: 산업생산+물가 → 금리
    results.append(
        StrategySignal(
            37,
            "산업생산+물가 → 금리",
            active=inf.get("state") is not None and phase != "",
            direction="bearish"
            if inf.get("state") == "hot" and phase in ("expansion",)
            else "bullish"
            if inf.get("state") in ("cool", "cold")
            else "neutral",
            description=f"물가 {inf.get('stateLabel', '?')} + 사이클 {cycle.get('phaseLabel', '?')} → 금리 {'상승' if inf.get('state') == 'hot' else '안정/하락'}",
        )
    )

    # 전략 38: 금융위험 → 달러상승
    results.append(
        StrategySignal(
            38,
            "금융위험 → 달러상승",
            active=dsh.get("status") is not None,
            direction="bearish" if dsh.get("status") == "active" else "neutral",
            description=dsh.get("description", "데이터 부족"),
        )
    )

    # 전략 39: 은행대출 → 금리 — 유동성 환경으로 프록시
    liq_regime = liquidity.get("regime", "")
    results.append(
        StrategySignal(
            39,
            "은행대출 → 금리상승",
            active=liq_regime != "",
            direction="bearish" if liq_regime == "abundant" else "bullish" if liq_regime == "tight" else "neutral",
            description=f"유동성 {liquidity.get('regimeLabel', '?')} — {'신용 팽창→금리상승 압력' if liq_regime == 'abundant' else '긴축→금리하락 압력' if liq_regime == 'tight' else '중립'}",
        )
    )

    # 전략 40: 금융업주가 ← 장단기차
    results.append(
        StrategySignal(
            40,
            "금융업주가 ← 장단기차",
            active=spread_2y is not None,
            direction="bullish"
            if spread_2y is not None and spread_2y > 0.5
            else "bearish"
            if spread_2y is not None and spread_2y < -0.5
            else "neutral",
            description=f"장단기차 {spread_2y:+.2f}%p → 금융업 {'유리' if spread_2y is not None and spread_2y > 0.5 else '불리' if spread_2y is not None and spread_2y < -0.5 else '중립'}"
            if spread_2y is not None
            else "데이터 없음",
        )
    )

    return results
