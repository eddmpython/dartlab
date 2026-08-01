"""story 블록 빌더 — valuation 도메인 (debt-honesty P3-3 god-split). 공유 imports·상수·헬퍼는 _shared."""

from __future__ import annotations

from dartlab.story.builders._shared import (
    FlagBlock,
    HeadingBlock,
    MetricBlock,
    TableBlock,
    TextBlock,
    _flagsBlock,
    _meta,
    narrateLifeCycle,
    narrateValuation,
    narrateValuationSins,
    pl,
)


def scenarioSensitivityBlock(data: dict | None) -> list:
    """calcScenarioSensitivity 결과 → shock별 지표 변화 + 해석."""
    if not data:
        return []

    base = data.get("baseCase", {})
    shocks = data.get("shocks", {})
    if not shocks:
        return []

    blocks: list = [
        HeadingBlock(
            _meta("scenarioSensitivity").label,
            level=2,
            helper="핵심 가정이 무너지면 어떻게 되는가 — 3가지 하방 shock",
        ),
    ]

    # Base case metrics
    base_metrics = []
    if base.get("opm") is not None:
        base_metrics.append(("현재 OPM", f"{base['opm']:.1f}%"))
    if base.get("roe") is not None:
        base_metrics.append(("현재 ROE", f"{base['roe']:.1f}%"))
    if base.get("interestCoverage") is not None:
        base_metrics.append(("이자보상배율", f"{base['interestCoverage']:.1f}x"))
    if base_metrics:
        blocks.append(MetricBlock(base_metrics))

    # Shock table
    rows = []
    shock_labels = {
        "opm_minus_5pp": "OPM -5%p",
        "revenue_minus_15pct": "매출 -15%",
        "interest_plus_2pp": "금리 +2%p",
    }
    for key, label in shock_labels.items():
        s = shocks.get(key)
        if not s:
            continue
        row: dict = {"시나리오": label}
        if s.get("roe") is not None:
            row["ROE"] = f"{s['roe']:.1f}%"
        if s.get("interestCoverage") is not None:
            row["이자보상"] = f"{s['interestCoverage']:.1f}x"
        row["판정"] = s.get("verdict", "")
        rows.append(row)

    if rows:
        blocks.append(TableBlock("하방 시나리오 영향", pl.DataFrame(rows)))

    # breakdown point
    bp = data.get("breakdownPoint")
    if bp and bp.get("value") is not None:
        safety = bp.get("safetyMargin")
        txt = f"**손익분기점**: OPM {bp['value']:.1f}% ({bp['meaning']})"
        if safety is not None:
            txt += f" — 현재 안전마진 {safety:.1f}%p"
        blocks.append(TextBlock(txt))

    # 인과 연쇄 narrate — OPM shock에서 파생 지표 변화 자동 문장
    opm_shock = shocks.get("opm_minus_5pp", {})
    if opm_shock and base:
        from dartlab.story.narrate import narrateCausalChain

        metrics = {}
        if base.get("opm") is not None and opm_shock.get("opm") is not None:
            metrics["opm_delta"] = opm_shock["opm"] - base["opm"]
        if base.get("roe") is not None and opm_shock.get("roe") is not None:
            base_roe = base["roe"]
            metrics["debt_delta_pp"] = opm_shock["roe"] - base_roe  # ROE 변화를 proxy로
        chain = narrateCausalChain(metrics)
        if chain:
            blocks.append(TextBlock(chain))

    return blocks


# ── 4부: 가치평가 빌더 ──


def dcfValuationBlock(data: dict) -> list:
    """calcDcf 결과 -> HeadingBlock + MetricBlock + TableBlock."""
    if not data:
        return []
    blocks: list = [
        HeadingBlock(
            _meta("dcfValuation").label,
            level=2,
            helper="FCF 기반 기업가치 추정 -- 할인율과 성장률 가정 확인 필수",
        ),
    ]
    metrics = []
    if data.get("perShareValue") is not None:
        metrics.append(("적정가", f"{data['perShareValue']:,.0f}"))
    if data.get("currentPrice") is not None:
        metrics.append(("현재가", f"{data['currentPrice']:,.0f}"))
    if data.get("marginOfSafety") is not None:
        metrics.append(("안전마진", f"{data['marginOfSafety']:.1f}%"))
    if data.get("discountRate") is not None:
        metrics.append(("할인율", f"{data['discountRate']:.1f}%"))
    if data.get("terminalGrowth") is not None:
        metrics.append(("영구성장률", f"{data['terminalGrowth']:.1f}%"))
    if metrics:
        blocks.append(MetricBlock(metrics))

    # FCF 추정 테이블
    projections = data.get("fcfProjections", [])
    if projections:
        rows = [{"연차": f"Y{i + 1}", "FCF(조원)": round(v / 1e12, 1)} for i, v in enumerate(projections)]
        blocks.append(TableBlock("FCF 추정", pl.DataFrame(rows)))

    for w in data.get("warnings", []):
        blocks.append(TextBlock(f"-- {w}", style="dim"))
    return blocks


def ddmValuationBlock(data: dict) -> list:
    """calcDdm 결과 -> MetricBlock."""
    if not data:
        return []
    if data.get("modelUsed") == "N/A":
        return [
            HeadingBlock(_meta("ddmValuation").label, level=2),
            TextBlock("DDM 적용 불가 (무배당 또는 데이터 부족)", style="dim"),
        ]

    blocks: list = [
        HeadingBlock(
            _meta("ddmValuation").label,
            level=2,
            helper="배당 기반 가치 -- 배당 지속성이 핵심 가정",
        ),
    ]
    metrics: list[tuple[str, str]] = []
    if data.get("intrinsicValue") is not None:
        metrics.append(("적정가", f"{data['intrinsicValue']:,.0f}"))
    if data.get("dividendPerShare") is not None:
        metrics.append(("주당배당금", f"{data['dividendPerShare']:,.0f}"))
    if data.get("dividendGrowth") is not None:
        metrics.append(("배당성장률", f"{data['dividendGrowth']:.1f}%"))
    if data.get("payoutRatio") is not None:
        metrics.append(("배당성향", f"{data['payoutRatio']:.1f}%"))
    if metrics:
        blocks.append(MetricBlock(metrics))
    return blocks


def residualIncomeBlock(data: dict) -> list:
    """calcResidualIncome 결과 -> MetricBlock."""
    if not data:
        return []
    blocks: list = [
        HeadingBlock(
            _meta("residualIncome").label,
            level=2,
            helper="BPS + 초과이익 현가 -- 자기자본비용 대비 초과수익 평가",
        ),
    ]
    metrics: list[tuple[str, str]] = []
    if data.get("bps"):
        metrics.append(("BPS", f"{data['bps']:,.0f}원"))
    if data.get("coe") is not None:
        metrics.append(("자기자본비용", f"{data['coe']:.1f}%"))
    if data.get("intrinsicValue") is not None:
        metrics.append(("적정가", f"{data['intrinsicValue']:,.0f}원"))
    if data.get("upside") is not None:
        metrics.append(("업사이드", f"{data['upside']:+.1f}%"))
    if metrics:
        blocks.append(MetricBlock(metrics))
    return blocks


def priceTargetBlock(data: dict) -> list:
    """calcPriceTarget 결과 -> MetricBlock + TableBlock(시나리오)."""
    if not data:
        return []
    blocks: list = [
        HeadingBlock(
            _meta("priceTarget").label,
            level=2,
            helper="5개 거시 시나리오 x DCF + Monte Carlo 분포",
        ),
    ]
    metrics: list[tuple[str, str]] = []
    if data.get("weightedTarget") is not None:
        metrics.append(("가중 목표가", f"{data['weightedTarget']:,.0f}원"))
    if data.get("currentPrice"):
        metrics.append(("현재가", f"{data['currentPrice']:,.0f}원"))
    if data.get("upside") is not None:
        metrics.append(("업사이드", f"{data['upside']:+.1f}%"))
    metrics.append(("투자 신호", data.get("signal", "-")))
    metrics.append(("신뢰도", data.get("confidence", "-")))
    blocks.append(MetricBlock(metrics))

    # 시나리오 테이블
    scenarios = data.get("scenarios", [])
    if scenarios:
        rows = []
        for s in scenarios:
            rows.append(
                {
                    "시나리오": s["name"],
                    "확률": f"{s['probability'] * 100:.0f}%",
                    "목표가(원)": f"{s['perShareValue']:,.0f}",
                }
            )
        blocks.append(TableBlock("시나리오별 목표가", pl.DataFrame(rows)))

    # Monte Carlo 백분위
    pctls = data.get("percentiles", {})
    if pctls:
        rows = [{"백분위": k, "주가(원)": f"{v:,.0f}"} for k, v in sorted(pctls.items())]
        blocks.append(TableBlock("Monte Carlo 분포", pl.DataFrame(rows)))
    return blocks


def reverseImpliedBlock(data: dict) -> list:
    """calcReverseImplied 결과 -> MetricBlock."""
    if not data:
        return []
    blocks: list = [
        HeadingBlock(
            _meta("reverseImplied").label,
            level=2,
            helper="현재 시가총액이 내재하는 매출 성장률 -- 시장 기대와 엔진 예측 비교",
        ),
    ]
    metrics: list[tuple[str, str]] = []
    if data.get("impliedGrowthRate") is not None:
        metrics.append(("내재성장률", f"{data['impliedGrowthRate']:.1f}%"))
    if data.get("latestRevenue") is not None:
        metrics.append(("최근 매출", f"{data['latestRevenue'] / 1e8:,.0f}억"))
    if data.get("assumedWacc") is not None:
        metrics.append(("가정 WACC", f"{data['assumedWacc']:.1f}%"))
    signal = data.get("signal")
    if signal:
        metrics.append(("신호", signal))
    if metrics:
        blocks.append(MetricBlock(metrics))
    return blocks


# ── dFV (dartlab Fair Value) ──


def dFVBlock(data: dict | None) -> list:
    """calcDFV v2 → dartlab 적정주가 블록 (anchor + 삼각검증)."""
    if not data:
        return []

    from dartlab.story.narrate import narrateDFV

    blocks: list = [HeadingBlock(_meta("dFV").label, level=2, helper="dartlab 적정주가 — DCF Anchor + 삼각검증")]

    status = data.get("assessmentStatus") or data.get("status")
    if status == "blocked":
        reason = data.get("blockedReason") or "입력 근거가 부족해 가치평가 발행이 차단되었습니다."
        blocks.append(TextBlock(f"**가치평가 차단**: {reason}"))
        metrics = [("평가 상태", "blocked")]
        if data.get("basePeriod") is not None:
            metrics.append(("요청 기준기간", str(data["basePeriod"])))
        blocks.append(MetricBlock(metrics))
        return blocks

    narration = narrateDFV(data)
    if narration:
        blocks.append(TextBlock(narration))

    metrics = []
    if data.get("dFV"):
        metrics.append(("dFV 적정주가", f"{data['dFV']:,}원"))
    if data.get("currentPrice"):
        metrics.append(("현재가", f"{data['currentPrice']:,}원"))
    if data.get("upside") is not None:
        metrics.append(("업사이드", f"{data['upside']:+.1f}%"))
    metrics.append(("투자 의견", data.get("opinion", "")))
    metrics.append(("신뢰도", data.get("confidence", "")))
    primaryModel = data.get("primaryModel")
    if primaryModel:
        metrics.append(("Primary 모델", str(primaryModel).upper()))
    sc = data.get("scenarios", {})
    if sc and all(sc.get(key) is not None for key in ("bull", "base", "bear")):
        metrics.append(("시나리오", f"Bull {sc['bull']:,} / Base {sc['base']:,} / Bear {sc['bear']:,}"))
    if metrics:
        blocks.append(MetricBlock(metrics))

    # DDM floor
    floor = data.get("dividendFloor")
    if floor:
        blocks.append(TextBlock(f"**배당 하한**: {floor['value']:,}원 — {floor['meaning']}"))

    return blocks


def methodFitnessBlock(data: dict | None) -> list:
    """삼각검증 + 모든 방법론 참고용 테이블."""
    if not data:
        return []

    blocks: list = [HeadingBlock(_meta("methodFitness").label, level=2, helper="Primary 모델 + 삼각검증 결과")]

    # 삼각검증
    tri = data.get("triangulation", {})
    checks = tri.get("checks", [])
    if checks:
        rows = []
        for c in checks:
            rows.append(
                {
                    "검증 모델": c["method"].upper(),
                    "적정가": f"{c['value']:,}원",
                    "괴리": f"{c['divergence']:.1f}%",
                    "판정": c["verdict"],
                }
            )
        blocks.append(TableBlock("삼각검증", pl.DataFrame(rows)))

    # 전체 방법론 참고
    all_m = data.get("allMethods", {})
    if all_m:
        primary = data.get("primaryModel", "")
        ref_rows = []
        for k, v in all_m.items():
            role = "**Primary**" if k == primary else "참고"
            ref_rows.append({"방법론": k.upper(), "적정가": f"{v:,}원", "역할": role})
        blocks.append(TableBlock("전체 방법론 (참고용)", pl.DataFrame(ref_rows)))

    return blocks


def qualityFactorsBlock(data: dict | None) -> list:
    """Quality-Adjusted WACC 요인 분해."""
    if not data:
        return []
    qw = data.get("qualityWACC", {})
    factors = qw.get("factors", [])
    if not factors:
        return []

    rows = []
    for f in factors:
        sp = f.get("spread", 0)
        label = f"{sp:+.1f}%p" if sp != 0 else "—"
        rows.append({"요인": f.get("name", ""), "WACC 가감": label, "근거": f.get("reason", "")})

    blocks: list = [
        HeadingBlock(_meta("qualityFactors").label, level=2, helper="4엔진 데이터 → WACC 가감 (Fernandez 방식)"),
        TableBlock("Quality WACC", pl.DataFrame(rows)),
    ]
    total = qw.get("totalSpread", 0)
    blocks.append(
        MetricBlock(
            [
                ("기본 WACC", f"{qw.get('baseWACC', 0):.1f}%"),
                ("질적 가감", f"{total:+.1f}%p"),
                ("조정 WACC", f"{qw.get('adjustedWACC', 0):.1f}%"),
            ]
        )
    )
    return blocks


def sensitivityBlock(data: dict) -> list:
    """calcSensitivity 결과 -> TableBlock(그리드)."""
    if not data:
        return []
    blocks: list = [
        HeadingBlock(
            _meta("sensitivity").label,
            level=2,
            helper="WACC x 영구성장률 조합별 적정가 변화",
        ),
    ]

    grid = data.get("grid", [])
    if not grid:
        return blocks

    # 피벗: 행=WACC, 열=성장률
    waccVals = sorted({g["wacc"] for g in grid})
    growthVals = sorted({g["terminalGrowth"] for g in grid})

    lookup = {(g["wacc"], g["terminalGrowth"]): g.get("perShareValue") for g in grid}

    rows = []
    for wacc in waccVals:
        row: dict = {"WACC": f"{wacc:.1f}%"}
        for tg in growthVals:
            val = lookup.get((wacc, tg))
            colName = f"g={tg:.1f}%"
            row[colName] = f"{val:,.0f}원" if val is not None else "-"
        rows.append(row)

    if rows:
        blocks.append(TableBlock("WACC x 성장률 민감도 (주당 적정가)", pl.DataFrame(rows)))

    baseVal = data.get("baseValue")
    if baseVal is not None:
        blocks.append(MetricBlock([("기준 적정가", f"{baseVal:,.0f}원")]))

    # heatmap ChartBlock
    if grid:
        from dartlab.story.blocks import ChartBlock
        from dartlab.viz.generators import specSensitivityHeatmap

        hm_grid = [
            {"wacc": g["wacc"], "g": g.get("terminalGrowth", 0), "fairValue": g.get("perShareValue")} for g in grid
        ]
        hm = specSensitivityHeatmap(hm_grid)
        if hm:
            blocks.append(ChartBlock(spec=hm))

        # 자동 문장: 편차 범위
        vals = [g.get("perShareValue") for g in grid if g.get("perShareValue") is not None]
        if vals and baseVal:
            min_v, max_v = min(vals), max(vals)
            pct_range = (max_v - min_v) / baseVal * 100 if baseVal > 0 else 0
            label = "높음" if pct_range > 80 else "보통" if pct_range > 40 else "낮음"
            blocks.append(
                TextBlock(
                    f"가정 민감도: 적정가 편차 {pct_range:.0f}% ({label}) — 가정 변화에 가치가 크게 흔들리{'면 주의' if label == '높음' else '지 않음'}"
                )
            )
    return blocks


def valuationSynthesisBlock(data: dict, priceTargetData: dict | None = None) -> list:
    """calcValuationSynthesis 결과 -> MetricBlock + TextBlock.

    priceTargetData 인자를 받아 두 모델 (synthesis 보수적 vs priceTarget 시나리오
    가중) 차이를 narration 으로 자동 추가하여 사용자 혼란을 해소한다.
    """
    if not data:
        return []
    blocks: list = [
        HeadingBlock(
            _meta("valuationSynthesis").label,
            level=2,
            helper="DCF + DDM + 상대가치 종합 -- 모델 간 범위와 판정",
        ),
    ]

    narration = narrateValuation(data)
    if narration:
        blocks.append(TextBlock(narration))

    fvr = data.get("fairValueRange")
    metrics: list[tuple[str, str]] = []
    if fvr:
        metrics.append(("적정가 범위", f"{fvr[0]:,.0f}원 ~ {fvr[1]:,.0f}원"))
    if data.get("currentPrice"):
        metrics.append(("현재가", f"{data['currentPrice']:,.0f}원"))
    metrics.append(("판정", data.get("verdict", "-")))
    blocks.append(MetricBlock(metrics))

    # 모델별 추정치
    estimates = data.get("estimates", [])
    if estimates:
        rows = [{"모델": e["method"], "적정가(원)": f"{e['value']:,.0f}"} for e in estimates]
        blocks.append(TableBlock("모델별 적정가", pl.DataFrame(rows)))

    # 두 모델 통합 narration
    if priceTargetData:
        synthFair = data.get("weightedFairValue")
        ptFair = priceTargetData.get("weightedTarget")
        if synthFair and ptFair and synthFair > 0 and ptFair > 0:
            divergence = abs(ptFair - synthFair) / synthFair * 100
            ratio = ptFair / synthFair
            if divergence > 30:
                if ptFair > synthFair:
                    direction = (
                        f"시장 기대가 모델 평균보다 **{ratio:.1f}배 낙관적**. "
                        f"확률가중 목표가 ({ptFair:,.0f}원) 가 모델 종합 적정가 ({synthFair:,.0f}원) 를 크게 상회"
                    )
                else:
                    direction = (
                        f"시장 기대가 모델 평균보다 **{1 / ratio:.1f}배 보수적**. "
                        f"확률가중 목표가 ({ptFair:,.0f}원) 가 모델 종합 적정가 ({synthFair:,.0f}원) 보다 낮음"
                    )
                blocks.append(
                    TextBlock(
                        f"두 모델 차이 {divergence:.0f}%: {direction}. "
                        f"종합 적정가는 DCF/DDM/RIM/상대가치 모델 평균(보수적), "
                        f"확률가중 목표가는 5개 거시 시나리오 시뮬레이션(시장 기대 기반)."
                    )
                )
            else:
                blocks.append(
                    TextBlock(
                        f"두 모델 수렴 (차이 {divergence:.0f}%): "
                        f"종합 적정가 {synthFair:,.0f}원 vs 확률가중 목표가 {ptFair:,.0f}원. "
                        f"보수적 모델 평균과 시장 기대 시나리오가 일치 — 신뢰도 높음."
                    )
                )

    return blocks


def valuationFlagsBlock(flags: list[dict]) -> list:
    """calcValuationFlags 결과 -> FlagBlock."""
    if not flags:
        return []
    flagTexts = []
    for f in flags:
        prefix = {"warning": "[!]", "opportunity": "[+]", "info": "[i]"}.get(f.get("signal", ""), "")
        flagTexts.append(f"{prefix} {f.get('label', '')}")
    return _flagsBlock(flagTexts)


def companyCyclePositionBlock(crisisData: dict | None) -> list:
    """현재 매크로 환경의 역사적 유사 에포크 표시.

    crisis dict 내부의 historicalContext → historicalEvents 리스트를 표로 전개.
    '지금과 비슷했던 과거'와 '그때 어떻게 흘러갔는지'를 나란히 놓는다.
    """
    if not crisisData:
        return []

    hc = crisisData.get("historicalContext") or {}
    events = hc.get("historicalEvents") or []
    scenario = hc.get("suggestedScenario")
    reason = hc.get("suggestedScenarioReason")
    overall = hc.get("overallAssessment") or crisisData.get("verdict")

    if not events and not scenario and not overall:
        return []

    blocks: list = [
        HeadingBlock(
            _meta("companyCyclePosition").label,
            level=2,
            helper="지금과 비슷했던 과거 에포크. 역사가 반복되는 건 아니지만 운율은 맞는다.",
        ),
    ]

    if overall:
        blocks.append(TextBlock(str(overall)))

    if events:
        rows = []
        for e in events[:5]:
            if isinstance(e, dict):
                rows.append(
                    {
                        "사건": e.get("eventName", ""),
                        "시점": e.get("eventDate", ""),
                        "유사도": e.get("similarity", ""),
                        "맥락": e.get("context", ""),
                        "귀결": e.get("outcome", ""),
                    }
                )
        if rows:
            blocks.append(TableBlock("유사 역사적 에포크", pl.DataFrame(rows)))

    if scenario:
        blocks.append(TextBlock(f"**다음 장 추정 시나리오**: {scenario}" + (f" — {reason}" if reason else "")))

    return blocks


def valuationBandBlock(data: dict) -> list:
    """calcValuationBand 결과 → PER/PBR 밴드."""
    if not data:
        return []

    bands = data.get("bands", {})
    overall = data.get("overallZone", "적정")

    if not bands:
        return []

    metrics = []
    for key, band in bands.items():
        m = band["metric"]
        metrics.append((f"{m} 현재", f"{band['current']:.1f}x"))
        metrics.append((f"{m} 평균", f"{band['mean']:.1f}x (±{band['std']:.1f})"))
        metrics.append((f"{m} 백분위", f"{band['percentile']:.0f}%"))
        metrics.append((f"{m} 판정", band["zoneLabel"]))

    metrics.append(("종합", overall))

    return [
        HeadingBlock(
            _meta("valuationBand").label,
            level=2,
            helper="과거 PER/PBR 정규분포에서 현재 위치. -1σ 이하=저평가, +1σ 이상=고평가",
        ),
        MetricBlock(metrics),
    ]


# ── Damodaran 흡수 블록들 ──


def lifeCycleStageBlock(data: dict) -> list:
    """calcLifeCycle 결과 → HeadingBlock + TextBlock + MetricBlock.

    Damodaran Corporate Life Cycle 단계 표시 + 핵심 지표 + 권고 모델.
    """
    if not data or not data.get("phase"):
        return []

    narration = narrateLifeCycle(data)
    signals = data.get("signals") or {}
    inflection = data.get("inflection") or {}

    metrics: list[tuple[str, str]] = []
    if signals.get("revenueCAGR") is not None:
        metrics.append(("매출 CAGR", f"{signals['revenueCAGR']:.1f}%"))
    if signals.get("roicWACCSpread") is not None:
        metrics.append(("ROIC - WACC", f"{signals['roicWACCSpread']:+.1f}%p"))
    if signals.get("fcfPositiveStreak") is not None:
        metrics.append(("FCF 양수 연속", f"{signals['fcfPositiveStreak']}기"))
    if signals.get("dividendPayout") is not None:
        metrics.append(("배당성향", f"{signals['dividendPayout']:.0f}%"))
    if signals.get("marginDirection"):
        metrics.append(("마진 방향", signals["marginDirection"]))
    metrics.append(("신뢰도", f"{data.get('phaseConfidence', 0):.0%}"))
    if inflection.get("towards"):
        metrics.append(("전환 신호", f"{inflection['towards']} (score {inflection.get('score', 0):.2f})"))
    metrics.append(("권고 모델", data.get("modelHint", "dcf")))

    blocks: list = [
        HeadingBlock(
            _meta("lifeCycleStage").label,
            level=2,
            helper="Damodaran Corporate Life Cycle (2024) — storyTemplate 과 직교 축",
        ),
    ]
    if narration:
        blocks.append(TextBlock(narration, indent="h2"))
    if metrics:
        blocks.append(MetricBlock(metrics))
    return blocks


def valuationSinsBlock(data: dict) -> list:
    """calcValuationSins 결과 → HeadingBlock + TextBlock + FlagBlock.

    Damodaran 7 Sins + CF Consistency 규칙 위반 표시.
    """
    if not data:
        return []

    narration = narrateValuationSins(data)
    flags = data.get("flags") or []

    blocks: list = [
        HeadingBlock(
            _meta("valuationSins").label,
            level=2,
            helper="Damodaran 밸류에이션 정합성 규칙 검증 (Probable Test)",
        ),
    ]
    if narration:
        blocks.append(TextBlock(narration, indent="h2"))

    if flags:
        flag_items: list[str] = []
        for f in flags:
            severity = f.get("severity", "info")
            key = f.get("key", "")
            reason = f.get("reason", "")
            flag_items.append(f"{severity}: [{key}] {reason}")
        blocks.append(FlagBlock(flag_items))

    return blocks


def plausibilityBandBlock(data: dict) -> list:
    """calcPlausibilityBand → HeadingBlock + TextBlock + MetricBlock.

    섹터 피어 분포 대비 현재 forecast 위치 (Plausible Test).
    """
    if not data:
        return []

    peer_stats = data.get("peerStats") or {}
    band = data.get("band", "unknown")
    growth_pct = data.get("growthPercentile")
    margin_pct = data.get("marginPercentile")

    if growth_pct is None and margin_pct is None:
        return []

    text_parts = [f"피어 분포 대비 위치: **{band}**."]
    if growth_pct is not None:
        text_parts.append(f"매출 성장률 상위 {100 - growth_pct:.0f}%.")
    if margin_pct is not None:
        text_parts.append(f"영업마진 상위 {100 - margin_pct:.0f}%.")

    metrics: list[tuple[str, str]] = []
    if peer_stats.get("growthMedian") is not None:
        metrics.append(("피어 성장률 중앙값", f"{peer_stats['growthMedian']:.1f}%"))
    if peer_stats.get("growthP75") is not None:
        metrics.append(("피어 성장률 상위 25%", f"{peer_stats['growthP75']:.1f}%"))
    if peer_stats.get("growthP95") is not None:
        metrics.append(("피어 성장률 상위 5%", f"{peer_stats['growthP95']:.1f}%"))
    if peer_stats.get("marginMedian") is not None:
        metrics.append(("피어 영업마진 중앙값", f"{peer_stats['marginMedian']:.1f}%"))
    if peer_stats.get("marginP75") is not None:
        metrics.append(("피어 영업마진 상위 25%", f"{peer_stats['marginP75']:.1f}%"))
    if peer_stats.get("count") is not None:
        metrics.append(("피어 수", f"{peer_stats['count']}개사"))

    return [
        HeadingBlock(
            _meta("plausibilityBand").label,
            level=2,
            helper="Damodaran Plausible Test — 피어 분포 percentile",
        ),
        TextBlock(" ".join(text_parts), indent="h2"),
        MetricBlock(metrics) if metrics else TextBlock("피어 데이터 부족", style="dim", indent="h2"),
    ]


def macroSensitivityBlock(data: dict | None) -> list:
    """calcMacroSensitivity 결과 → 매크로 민감도 블록.

    Returns
    -------
    list[Block]
        HeadingBlock + MetricBlock(지표별 R²/영향) + TextBlock(종합 방향).
    """
    if not data:
        return []

    blocks: list = [
        HeadingBlock(
            _meta("macroSensitivity").label,
            level=2,
            helper="거시 지표 민감도 — 금리/환율/유가 등이 이 회사에 미치는 영향",
        )
    ]

    selected = data.get("selected") or []
    if selected:
        metrics: list[tuple[str, str]] = []
        for ind in selected[:5]:
            label = ind.get("label", "")
            r2 = ind.get("rSquared", 0)
            impact = ind.get("impact", "")
            change = ind.get("latestChange")
            desc = f"R²={r2:.2f} · {impact}"
            if change is not None:
                desc += f" · 최근 {change:+.1f}%"
            metrics.append((label, desc))
        blocks.append(MetricBlock(metrics))

    net = data.get("netDirectionLabel", "")
    source = data.get("selectedSource", "")
    if net:
        blocks.append(TextBlock(f"종합 방향: {net} ({source} 기준)"))

    return blocks
