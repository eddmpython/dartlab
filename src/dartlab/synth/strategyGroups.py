"""40 전략을 열한 묶음으로 나눠 판정하는 그룹 판정기.

`strategyRules` 는 아홉 개 하위 dict 를 풀어 이 판정기들을 순서대로 이어 붙이기만 한다.
전략 번호 순서가 공개 계약이라 묶음은 절대 겹치지 않는 연속 구간으로만 나눈다.

묶음을 가르는 기준은 "이 구간이 어느 하위 dict 를 읽는가, 그리고 중간에 만든 값이 구간
밖으로 새는가" 다. 새지 않으면 그 구간은 닫힌 판정이고 따로 뗄 수 있다.

구간을 넘나드는 파생값(금리 방향, 국면, 물가 등)은 인자로 실어 나르지 않고 각 판정기가
원본 dict 에서 다시 읽는다. 같은 `.get` 사슬이 앞 판정기에서 이미 성공했으므로 다시 읽어도
예외가 나지 않고 값도 같다. 문맥 객체를 만들어 돌리면 판정기가 순수 함수가 아니게 된다.
"""

from __future__ import annotations

from dartlab.synth.strategyTypes import StrategySignal, _exportProfitDirection, _matchDirection, _sig


def _growthLinkageSignals(rates: dict, forecast: dict, trade: dict) -> list[StrategySignal]:
    """A 그룹 전반부(전략 1~5): 성장률 신호를 금리/주가/환율로 번역하는 묶음.

    다섯 전략이 모두 "성장 신호 하나를 어느 자산 방향으로 읽나" 라는 같은 질문을
    공유하고, 입력도 rates/forecast/trade 셋으로 닫힌다. 사이클 국면(cycle)은
    여기서 쓰이지 않아 뒤 그룹으로 넘긴다.
    """
    results: list[StrategySignal] = []

    # 전략 1: 금리 추이는 전기비 성장률에 의해 결정된다
    rp = forecast.get("recessionProb") or {}
    rate_dir = (rates.get("outlook") or {}).get("direction")
    prob_val = rp.get("probability", 0.5)
    results.append(
        _sig(
            1,
            "금리 = 전기비 성장률 결정",
            active=rate_dir is not None,
            direction=_matchDirection(rate_dir, bullish=("cut",), bearish=("hike",)),
            description=f"금리방향: {rate_dir or '판별불가'}, 침체확률: {prob_val}",
            strength=min(1.0, abs(prob_val - 0.5) * 2) if isinstance(prob_val, (int, float)) else 0.5,
            confidence="high" if rate_dir in ("cut", "hike") else "low",
        )
    )

    # 전략 2: 주가지수 ≈ 명목GDP
    nowcast = forecast.get("nowcast") or {}
    gdp_est = nowcast.get("gdpEstimate")
    # 이상값 검증: GDP 추정이 -10~20% 범위 밖이면 무효
    if gdp_est is not None and not (-10 <= gdp_est <= 20):
        gdp_est = None
        nowcast = {}
    nc_active = gdp_est is not None
    results.append(
        _sig(
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
        _sig(
            3,
            "GDP 상대강도 → 환율",
            active=rs.get("fxDirection") is not None,
            direction=_matchDirection(rs.get("fxDirection"), bullish=("krw_strengthen",), bearish=("krw_weaken",)),
            description=rs.get("description", "데이터 부족"),
        )
    )

    # 전략 4: 금리 = 미래 인플레 베팅
    inf = rates.get("inflation") or {}
    results.append(
        _sig(
            4,
            "금리 = 미래 인플레 베팅",
            active=inf.get("state") is not None,
            direction=_matchDirection(inf.get("state"), bullish=("cool", "cold"), bearish=("hot",)),
            description=f"물가: {inf.get('stateLabel', '?')}",
        )
    )

    # 전략 5: 한국주가 ≈ 미국소비
    usc = trade.get("usConsumptionLink") or {}
    results.append(
        _sig(
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

    return results


def _cyclePhaseSignals(cycle: dict, inventory: dict) -> list[StrategySignal]:
    """A 그룹 후반부(전략 6~9): 경기 국면과 재고 순환으로 판정하는 묶음.

    넷 다 "지금 사이클 어디쯤인가" 하나만 물어서, 입력이 국면(cycle.phase)과
    재고 국면(inventory.inventoryPhase) 둘로 닫힌다. 앞의 1~5 가 성장률 수치를
    번역하는 것과 달리 여기는 국면 라벨 자체가 판정 재료다.
    """
    results: list[StrategySignal] = []

    # 전략 6~9: 사이클 관련
    phase = cycle.get("phase", "")
    results.append(
        _sig(
            6,
            "실물투자 → 경기변동",
            active=phase != "",
            direction="bullish" if phase in ("recovery", "expansion") else "bearish",
            description=f"사이클: {cycle.get('phaseLabel', '?')}",
        )
    )

    ip = inventory.get("inventoryPhase") or {}
    results.append(
        _sig(
            7,
            "재고흐름 → 서프라이즈",
            active=ip.get("phase") is not None,
            direction=ip.get("equityImplication", "neutral"),
            description=ip.get("description", "데이터 부족"),
        )
    )
    results.append(
        _sig(
            8,
            "재고순환 → 주가예측",
            active=ip.get("phase") is not None,
            direction=ip.get("equityImplication", "neutral"),
            description=f"재고비율: {ip.get('ratio', '?')}, {ip.get('phaseLabel', '?')}",
        )
    )
    results.append(
        _sig(
            9,
            "침체탈출 = 정부지출",
            active=phase == "recovery",
            direction="bullish" if phase == "recovery" else "neutral",
            description="경기 회복 시 정부지출 역할 활성",
        )
    )

    return results


def _tradeConditionSignals(trade: dict, inventory: dict) -> list[StrategySignal]:
    """B 그룹(전략 10~14): 교역조건과 수출 채산성이 한국 주가로 오는 묶음.

    다섯 전략 모두 trade 의 교역 관련 sub-dict 를 읽고, ISM 자산배분(전략 13)만
    inventory 를 빌린다. 국내 경기 국면(A 그룹)과 달리 "밖에서 들어오는 신호" 를
    본다는 점이 갈라지는 지점이다.
    """
    results: list[StrategySignal] = []
    rs = trade.get("leadingRelativeStrength") or {}

    # 전략 10: 한국주가 = 수출기업
    ep = trade.get("exportProfit") or {}
    results.append(
        _sig(
            10,
            "한국주가 = 수출기업",
            active=ep.get("signal") is not None,
            direction=_exportProfitDirection(ep),
            description=ep.get("description", "데이터 부족"),
        )
    )

    # 전략 11-12: 교역조건
    tot = trade.get("termsOfTrade") or {}
    results.append(
        _sig(
            11,
            "교역조건 = 최선행",
            active=tot.get("direction") is not None,
            direction=_matchDirection(tot.get("direction"), bullish=("improving",), bearish=("deteriorating",)),
            description=tot.get("description", "데이터 부족"),
        )
    )

    tp = trade.get("totProxy") or {}
    results.append(
        _sig(
            12,
            "ToT대용치 = 환율-유가",
            active=tp.get("value") is not None,
            direction=_matchDirection(tp.get("direction"), bullish=("improving",), bearish=("deteriorating",)),
            description=tp.get("description", "데이터 부족"),
        )
    )

    # 전략 13: ISM 바로미터
    ism_alloc = inventory.get("ismAllocation") or {}
    results.append(
        _sig(
            13,
            "ISM = 자산배분 바로미터",
            active=ism_alloc.get("stance") is not None,
            direction=_matchDirection(ism_alloc.get("stance"), bullish=("risk_on",), bearish=("risk_off",)),
            description=ism_alloc.get("description", "데이터 부족"),
        )
    )

    # 전략 14: 양국 선행지수 → 환율
    results.append(
        _sig(
            14,
            "양국 선행지수 → 환율",
            active=rs.get("fxDirection") is not None,
            direction="bearish" if rs.get("fxDirection") == "krw_weaken" else "bullish",
            description=rs.get("description", "데이터 부족"),
        )
    )

    return results


def _leadingIndicatorSignals(rates: dict, forecast: dict, trade: dict) -> list[StrategySignal]:
    """C 그룹 전반부(전략 15~18): 선행/후행 지표와 물가 압력을 읽는 묶음.

    LEI 후행 모멘텀, 선행+후행 합성, 고용, 환율+유가발 물가압력 넷은 모두
    "정책이 움직이기 전에 먼저 흔들리는 지표" 를 본다. 넷이 쓰는 파생값
    (lei/emp/tot_comps)이 이 묶음 밖에서는 쓰이지 않아 경계가 깔끔하다.
    """
    results: list[StrategySignal] = []

    # 전략 15: 후행지수 상승 + 120일선 반등
    lei = forecast.get("lei") or {}
    lag_m = lei.get("lagMomentum")
    results.append(
        _sig(
            15,
            "후행상승 + 120일선 반등",
            active=lag_m is not None and lag_m > 0,
            direction="bullish" if lag_m is not None and lag_m > 0 else "neutral",
            description=f"후행지수 모멘텀 {lag_m:+.2f}" if lag_m is not None else "후행지수 데이터 없음",
        )
    )

    # 전략 16: 전기비성장률 = 선행+후행
    results.append(
        _sig(
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
        _sig(
            17,
            "고용지표 주목",
            active=emp.get("state") is not None,
            direction=_matchDirection(emp.get("state"), bullish=("strong",), bearish=("weak",)),
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
            _sig(
                18,
                "한국물가 = 환율+유가",
                active=True,
                direction="bearish" if inf_pressure > 0.5 else "bullish" if inf_pressure < -0.5 else "neutral",
                description=f"환율({fx_yoy:+.1f}%)+유가({oil_yoy:+.1f}%) → 물가압력 {inf_pressure:+.1f}%p",
            )
        )
    else:
        results.append(
            _sig(18, "한국물가 = 환율+유가", active=False, direction="neutral", description="환율/유가 데이터 없음")
        )

    return results


def _monetaryPolicySignals(rates: dict, assets: dict) -> list[StrategySignal]:
    """C 그룹 후반부(전략 19~22): 통화정책 방향과 장단기차를 읽는 묶음.

    넷 다 정책금리 방향(rate_dir)이나 그 방향이 만드는 커브(spread2y)를 출발점
    으로 삼는다. 앞 그룹의 선행지표 판정과 재료가 완전히 갈려 따로 뗐다.
    """
    results: list[StrategySignal] = []
    rate_dir = (rates.get("outlook") or {}).get("direction")
    inf = rates.get("inflation") or {}

    # 전략 19~22: 금리/통화정책
    results.append(
        _sig(
            19,
            "통화정책 = 투자 마일스톤",
            active=rate_dir is not None,
            direction=_matchDirection(rate_dir, bullish=("cut",), bearish=("hike",)),
            description=f"통화정책 방향: {rate_dir or '?'}",
        )
    )

    # 전략 20: 장단기차. rates 에서 term spread 변화
    expect = rates.get("expectation") or {}
    spread2y = expect.get("spread2yFf")
    results.append(
        _sig(
            20,
            "금리정책 전후 장단기차",
            active=spread2y is not None,
            direction="bullish"
            if rate_dir == "cut" and spread2y is not None and spread2y < -0.5
            else "bearish"
            if rate_dir == "hike" and spread2y is not None and spread2y > 0.5
            else "neutral",
            description=f"2Y-FF 스프레드 {spread2y:+.2f}%p" if spread2y is not None else "데이터 없음",
        )
    )

    # 전략 21: 금리↔주가 역학
    asset_signals = assets.get("signals") or []
    any(s.get("direction") == "up" for s in asset_signals if isinstance(s, dict) and s.get("asset") == "equity")
    results.append(
        _sig(
            21,
            "금리↔주가 역학관계",
            active=rate_dir is not None,
            direction=_matchDirection(rate_dir, bullish=("cut",), bearish=("hike",)),
            description=f"금리 {rate_dir or '?'} — 금리/주가 역학",
        )
    )

    results.append(
        _sig(
            22,
            "물가과열 → 긴축 → 선행하락",
            active=inf.get("state") is not None,
            direction="bearish" if inf.get("state") == "hot" else "neutral",
            description=f"물가 {inf.get('stateLabel', '?')} — {'과열→긴축 체인 활성' if inf.get('state') == 'hot' else '안정'}",
        )
    )

    return results


def _dollarStrengthSignals(crisis: dict) -> list[StrategySignal]:
    """D 그룹 전반부(전략 23~24): 달러 3 개월 변화 하나로 갈리는 쌍둥이 규칙.

    둘은 같은 dxyChange3m 을 임계값 -2% 와 +2% 로 뒤집어 읽는 대칭 규칙이라
    입력이 crisis 하나로 닫힌다. 나란히 두어야 대칭이 눈에 보이고, 임계값이
    바뀔 때 한쪽만 고치는 사고를 막는다.
    """
    results: list[StrategySignal] = []

    # 전략 23~24: 환율/달러
    dsh = crisis.get("dollarSafeHaven") or {}
    dxy_chg = dsh.get("dxyChange3m")

    results.append(
        _sig(
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
        _sig(
            24,
            "달러강세 → 미국국채",
            active=dxy_chg is not None,
            direction="bullish" if dxy_chg is not None and dxy_chg > 2 else "neutral",
            description=f"달러 {dxy_chg:+.1f}% — {'미국국채 유리' if dxy_chg is not None and dxy_chg > 2 else '해당없음'}"
            if dxy_chg is not None
            else "달러 데이터 없음",
        )
    )

    return results


def _currencyLinkedSignals(rates: dict, assets: dict, trade: dict) -> list[StrategySignal]:
    """D 그룹 후반부(전략 25~27): 달러가 금/물가/원화를 거쳐 자산으로 오는 묶음.

    앞의 23~24 가 달러 지수 하나만 보는 반면 여기 셋은 달러를 상대편(금, 신흥국
    물가, 원화)과 짝지어 읽는다. 입력이 assets/rates/trade 로 벌어져 달러 단독
    판정기와 갈랐다.
    """
    results: list[StrategySignal] = []
    inf = rates.get("inflation") or {}
    tot_proxy = trade.get("totProxy") or {}
    tot_comps = tot_proxy.get("components") or {}

    # 전략 25: 달러↔금. assets 금 3요인에서 dollarEffect
    gold_drivers = assets.get("goldDrivers") or {}
    dollar_eff = gold_drivers.get("dollarEffect")
    results.append(
        _sig(
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
        _sig(
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
        _sig(
            27,
            "원/달러 하락 → 내수주",
            active=usdkrw_proxy is not None,
            direction="bullish" if usdkrw_proxy is not None and usdkrw_proxy < -3 else "neutral",
            description=f"USDKRW YoY {usdkrw_proxy:+.1f}% — {'원화강세→내수주 유리' if usdkrw_proxy is not None and usdkrw_proxy < -3 else '해당없음'}"
            if usdkrw_proxy is not None
            else "환율 데이터 없음",
        )
    )

    return results


def _creditCycleSignals(cycle: dict, rates: dict, forecast: dict) -> list[StrategySignal]:
    """E 그룹 전반부(전략 28~30): 금리와 경기 국면을 맞대어 보는 묶음.

    셋 다 "지금 금리 수준이 경기가 감당할 만한가" 를 묻는다. 금리 방향, 사이클
    국면, 장단기차라는 같은 세 재료를 서로 다른 각도로 조합할 뿐이라 한 판정기로
    묶었다. 재료는 앞 그룹과 겹치지만 값 전달 대신 rates/cycle 에서 다시 읽는다.
    """
    results: list[StrategySignal] = []
    rate_dir = (rates.get("outlook") or {}).get("direction")
    phase = cycle.get("phase", "")
    spread2y = (rates.get("expectation") or {}).get("spread2yFf")
    lei = forecast.get("lei") or {}

    # 전략 28: 금리상승 = 경기회복 전제
    results.append(
        _sig(
            28,
            "금리상승 = 경기회복 전제",
            active=rate_dir is not None and phase != "",
            direction="bearish" if rate_dir == "hike" and phase not in ("recovery", "expansion") else "neutral",
            description=f"금리 {rate_dir or '?'} + 사이클 {cycle.get('phaseLabel', '?')} — {'경기 뒷받침 없는 금리상승 경고' if rate_dir == 'hike' and phase not in ('recovery', 'expansion') else '정상'}",
        )
    )

    # 전략 29: 한국금리 = 내수
    results.append(
        _sig(
            29,
            "한국금리 = 내수반영",
            active=phase != "",
            direction=_matchDirection(phase, bullish=("recovery", "expansion"), bearish=("contraction",)),
            description=f"사이클 {cycle.get('phaseLabel', '?')} → 한국 내수 {'확장' if phase in ('recovery', 'expansion') else '수축'}",
        )
    )

    # 전략 30: 장단기차 → CLI 선행
    lei.get("cliMomentum")
    results.append(
        _sig(
            30,
            "장단기차 → CLI 선행",
            active=spread2y is not None,
            direction="bullish"
            if spread2y is not None and spread2y > 0
            else "bearish"
            if spread2y is not None and spread2y < -0.5
            else "neutral",
            description=f"금리차 {spread2y:+.2f}%p → CLI 방향 선행" if spread2y is not None else "데이터 없음",
        )
    )

    return results


def _capexPressureSignals(crisis: dict, inventory: dict, trade: dict) -> list[StrategySignal]:
    """E 그룹 후반부(전략 31~33): 신용 여건이 설비투자와 도산으로 번지는 묶음.

    수출이익, 신용스프레드발 설비투자 압력, 공급과잉 도산 셋은 "돈줄이 조이면
    실물이 어디서 먼저 부러지나" 라는 한 줄기 인과를 나눠 본다. 특히 전략 33 은
    앞 두 전략이 각각 읽는 재고 국면과 설비투자 압력을 곱해 쓰므로, 셋을 한
    판정기에 두면 ip/cp 를 한 번만 읽고 돌려쓸 수 있다.
    """
    results: list[StrategySignal] = []
    ep = trade.get("exportProfit") or {}
    ip = inventory.get("inventoryPhase") or {}

    # 전략 31: ToT → 수출이익
    results.append(
        _sig(
            31,
            "ToT대용치 → 수출이익",
            active=ep.get("signal") is not None,
            direction=_exportProfitDirection(ep),
            description=ep.get("description", "데이터 부족"),
        )
    )

    # 전략 32: 신용스프레드 → 설비투자
    cp = crisis.get("capexPressure") or {}
    results.append(
        _sig(
            32,
            "신용스프레드 = 설비투자 압력",
            active=cp.get("pressure") is not None,
            direction=_matchDirection(cp.get("pressure"), bullish=("easing",), bearish=("tightening",)),
            description=cp.get("description", "데이터 부족"),
        )
    )

    # 전략 33: 공급과잉 → 도산. 재고 적극감축 + HY 스프레드 상승
    inv_phase = ip.get("phase", "")
    capex_pr = cp.get("pressure", "")
    results.append(
        _sig(
            33,
            "공급과잉 → 도산",
            active=inv_phase == "active_destock" or capex_pr == "tightening",
            direction="bearish" if inv_phase == "active_destock" and capex_pr == "tightening" else "neutral",
            description=f"재고 {ip.get('phaseLabel', '?')} + 설비투자 {cp.get('pressureLabel', '?')}",
        )
    )

    return results


def _ismLiquiditySignals(
    cycle: dict,
    rates: dict,
    crisis: dict,
    inventory: dict,
    assets: dict,
    liquidity: dict,
) -> list[StrategySignal]:
    """F 그룹(전략 34~39): 경기 온도계와 유동성 환경이 금리/달러로 번지는 묶음.

    ISM 수준, 국내 신용위험, 구리/금, 산업생산+물가, 안전자산 선호, 유동성
    국면 여섯이 모두 "지금 돈과 수요가 어디로 흐르나" 를 서로 다른 계기판으로
    읽는 규칙이다. 앞 그룹이 이미 읽은 inf/phase/dsh 는 값을 넘겨받는 대신
    원본 dict 에서 다시 읽는다. 그래야 그룹 사이에 파생값 배선이 생기지 않고
    각 판정기가 sub-dict 만 입력으로 받는 순수 함수로 남는다.
    """
    results: list[StrategySignal] = []
    inf = rates.get("inflation") or {}
    phase = cycle.get("phase", "")
    dsh = crisis.get("dollarSafeHaven") or {}

    # 전략 34: ISM<55 → 인상종결
    ism_bar = inventory.get("ismBarometer") or {}
    results.append(
        _sig(
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
        _sig(
            35,
            "국내신용위험 ↔ CPI",
            active=kr_cr.get("cpiYoy") is not None,
            direction="bearish" if (kr_cr.get("cpiYoy") or 0) > 4 else "neutral",
            description=kr_cr.get("signal", "KR 전용"),
        )
    )

    # 전략 36: 중국 통화 → 원자재. 구리 가격으로 프록시
    # 중국 M2 직접 접근 불가. 구리 = 중국 수요 프록시
    copper_gold = assets.get("copperGold") or {}
    cg_impl = copper_gold.get("implication")
    results.append(
        _sig(
            36,
            "중국 통화 → 원자재",
            active=cg_impl is not None,
            direction=_matchDirection(cg_impl, bullish=("expansion",), bearish=("contraction",)),
            description=copper_gold.get("description", "Cu/Au 데이터로 프록시"),
        )
    )

    # 전략 37: 산업생산+물가 → 금리
    results.append(
        _sig(
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
        _sig(
            38,
            "금융위험 → 달러상승",
            active=dsh.get("status") is not None,
            direction="bearish" if dsh.get("status") == "active" else "neutral",
            description=dsh.get("description", "데이터 부족"),
        )
    )

    # 전략 39: 은행대출 → 금리. 유동성 환경으로 프록시
    liq_regime = liquidity.get("regime", "")
    results.append(
        _sig(
            39,
            "은행대출 → 금리상승",
            active=liq_regime != "",
            direction=_matchDirection(liq_regime, bullish=("tight",), bearish=("abundant",)),
            description=f"유동성 {liquidity.get('regimeLabel', '?')} — {'신용 팽창→금리상승 압력' if liq_regime == 'abundant' else '긴축→금리하락 압력' if liq_regime == 'tight' else '중립'}",
        )
    )

    return results


def _financeSpreadSignals(rates: dict) -> list[StrategySignal]:
    """G 그룹(전략 40): 장단기차가 금융업 수익성을 가르는 규칙.

    은행 예대마진이 곧 장단기차라 입력(rates.expectation)도 판정 논리도 다른
    그룹과 겹치지 않는다. 그룹 사이로 값을 실어 나르는 대신 같은 dict 를 다시
    읽어, 판정기마다 필요한 sub-dict 만 받는 좁은 입력면을 유지한다.
    """
    results: list[StrategySignal] = []
    expect = rates.get("expectation") or {}
    spread2y = expect.get("spread2yFf")

    # 전략 40: 금융업주가 ← 장단기차
    results.append(
        _sig(
            40,
            "금융업주가 ← 장단기차",
            active=spread2y is not None,
            direction="bullish"
            if spread2y is not None and spread2y > 0.5
            else "bearish"
            if spread2y is not None and spread2y < -0.5
            else "neutral",
            description=f"장단기차 {spread2y:+.2f}%p → 금융업 {'유리' if spread2y is not None and spread2y > 0.5 else '불리' if spread2y is not None and spread2y < -0.5 else '중립'}"
            if spread2y is not None
            else "데이터 없음",
        )
    )

    return results
