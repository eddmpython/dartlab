"""story 블록 빌더 — capital 도메인 (debt-honesty P3-3 god-split). 공유 imports·상수·헬퍼는 _shared."""

from __future__ import annotations

from dartlab.story.builders._shared import (
    FlagBlock,
    HeadingBlock,
    MetricBlock,
    TableBlock,
    TextBlock,
    _extractSeries,
    _flagsBlock,
    _fmtAmtShort,
    _historyTable,
    _meta,
    _notesDetailBlocks,
    _timelineTable,
    _tupleFlags,
    _unitForCurrency,
    narrateDistress,
    narrateLeverage,
    pl,
    unifyTableScale,
)

# ── 자금구조 (capital) 빌더 ──


def fundingSourcesBlock(data: dict) -> list:
    """calcFundingSources 결과 → 조달원 비중 테이블 + 시계열."""
    if not data:
        return []

    latest = data.get("latest")
    if not latest:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("fundingSources").label,
            level=2,
            helper="내부유보 = 사업으로 번 돈, 금융차입 = 이자 붙는 빚, 영업조달 = 자연 발생 자금",
        )
    )

    # 최신 비중 메트릭
    fmtAmt = _fmtAmtShort(latest["totalAssets"])
    metrics = [("총자산", fmtAmt)]
    metrics.append(("내부유보 (이익잉여금)", f"{_fmtAmtShort(latest['retained'])} ({latest['retainedPct']:.0f}%)"))
    metrics.append(("외부-주주 (자본금+잉여금)", f"{_fmtAmtShort(latest['paidIn'])} ({latest['paidInPct']:.0f}%)"))
    metrics.append(("외부-금융차입", f"{_fmtAmtShort(latest['finDebt'])} ({latest['finDebtPct']:.0f}%)"))
    if latest["opFundingPct"] > 0.5:
        metrics.append(
            ("영업조달 (매입채무·선수금 등)", f"{_fmtAmtShort(latest['opFunding'])} ({latest['opFundingPct']:.0f}%)")
        )
    blocks.append(MetricBlock(metrics))

    # 시계열 테이블 (행=항목, 열=기간)
    history = data.get("history", [])
    if len(history) >= 2:
        cols = {"": ["내부유보", "주주자본", "금융차입", "영업조달"]}
        for h in history:
            cols[h["period"]] = [
                f"{h['retainedPct']:.0f}%",
                f"{h['paidInPct']:.0f}%",
                f"{h['finDebtPct']:.0f}%",
                f"{h['opFundingPct']:.0f}%",
            ]
        blocks.append(TableBlock("조달원 비중 추이", pl.DataFrame(cols)))

    # 보충 지표 (순차입금/EBITDA, 암묵적 차입금리)
    suppMetrics = []
    ndEbitda = data.get("netDebtEbitda")
    if ndEbitda is not None:
        if ndEbitda == 0:
            suppMetrics.append(("순차입금/EBITDA", "순현금 (차입 없음)"))
        else:
            suppMetrics.append(("순차입금/EBITDA", f"{ndEbitda:.1f}배"))
    impliedRate = data.get("impliedBorrowingRate")
    if impliedRate is not None:
        suppMetrics.append(("암묵적 차입금리", f"{impliedRate:.1f}%"))
    if suppMetrics:
        blocks.append(MetricBlock(suppMetrics))

    # 진단 + 비중 변화 방향
    diagnosis = data.get("diagnosis", "")
    leverageTrend = data.get("leverageTrend")
    diagParts = [p for p in [diagnosis, leverageTrend] if p]
    if diagParts:
        blocks.append(TextBlock(" | ".join(diagParts), style="dim", indent="h2"))

    blocks.extend(_notesDetailBlocks(data, {"borrowings": "차입금 상세"}))

    return blocks


def capitalOverviewBlock(data: dict) -> list:
    """calcCapitalOverview 결과 → MetricBlock."""
    if not data:
        return []
    metrics = data.get("metrics", [])
    if not metrics:
        return []
    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("capitalOverview").label,
            level=2,
            helper="부채비율 100% 이하 안정, 순현금이면 재무 여유",
        )
    )
    blocks.append(MetricBlock(metrics))
    return blocks


def capitalTimelineBlock(data: dict) -> list:
    """calcCapitalTimeline 결과 → TableBlock."""
    if not data:
        return []
    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("capitalTimeline").label,
            level=2,
            helper="이익잉여금 = 사업으로 번 돈, 자본금+잉여금 = 외부 조달",
        )
    )
    for label, tableRows, cols in data.get("tables", []):
        if tableRows and cols:
            unified = unifyTableScale(tableRows, "", cols, unit=_unitForCurrency())
            blocks.append(TableBlock(label, pl.DataFrame(unified)))
    if len(blocks) <= 1:
        return []
    return blocks


def debtTimelineBlock(data: dict) -> list:
    """calcDebtTimeline 결과 → TableBlock."""
    if not data:
        return []
    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("debtTimeline").label,
            level=2,
            helper="영업부채 = 자연 발생, 금융부채 = 이자 붙는 차입",
        )
    )
    for label, tableRows, cols in data.get("tables", []):
        if tableRows and cols:
            unified = unifyTableScale(tableRows, "", cols, unit=_unitForCurrency())
            blocks.append(TableBlock(label, pl.DataFrame(unified)))
    if len(blocks) <= 1:
        return []
    return blocks


def interestBurdenBlock(data: dict) -> list:
    """calcInterestBurden 결과 → MetricBlock."""
    if not data:
        return []
    metrics = data.get("metrics", [])
    if not metrics:
        return []
    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("interestBurden").label,
            level=2,
            helper="이자보상배율 3배 이상 안정, 1.5배 이하 주의",
        )
    )
    blocks.append(MetricBlock(metrics))
    return blocks


def liquidityBlock(data: dict) -> list:
    """calcLiquidity 결과 → MetricBlock."""
    if not data:
        return []
    metrics = data.get("metrics", [])
    if not metrics:
        return []
    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("liquidity").label,
            level=2,
            helper="유동비율 100% 이하 → 단기 지급 리스크",
        )
    )
    blocks.append(MetricBlock(metrics))
    return blocks


def distressBlock(data: dict) -> list:
    """calcDistressIndicators 결과 → MetricBlock."""
    if not data:
        return []
    metrics = data.get("metrics", [])
    if not metrics:
        return []
    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("distressIndicators").label,
            level=2,
            helper="Altman 계열은 표시된 모델명과 고유 임계값으로 판정, Piotroski F ≥ 7 건전",
        )
    )
    blocks.append(MetricBlock(metrics))
    return blocks


def capitalFlagsBlock(flags: list[tuple[str, str]]) -> list:
    """calcCapitalFlags 결과 → FlagBlock.

    조립 규칙은 `_shared._tupleFlags` 가 갖는다. 예전에는 같은 일곱 줄이 이 파일과
    revenue 와 _shared 세 곳에 있었고, 공용 자리가 이미 있는데도 둘이 자기 사본을 썼다.
    """
    return _tupleFlags(flags)


def workingCapitalBlock(data: dict) -> list:
    """calcWorkingCapital 결과 → 운전자본 + CCC."""
    if not data:
        return []

    latest = data.get("latest")
    if not latest:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("workingCapital").label,
            level=2,
            helper="CCC = 재고회전일 + 매출채권회전일 - 매입채무회전일",
        )
    )

    metrics = [
        ("순운전자본", _fmtAmtShort(latest["wc"])),
    ]
    for label, key, suffix in [
        ("매출채권 회전일", "receivableDays", "일"),
        ("재고 회전일", "inventoryDays", "일"),
        ("매입채무 회전일", "payableDays", "일"),
        ("CCC", "ccc", "일"),
    ]:
        val = latest.get(key)
        if val is not None:
            metrics.append((label, f"{val:.0f}{suffix}"))
    blocks.append(MetricBlock(metrics))

    # CCC 시계열 (행=항목, 열=기간)
    history = data.get("history", [])
    if len(history) >= 2:
        hasData = any(h.get("ccc") is not None for h in history)
        if hasData:
            cols = {"": ["매출채권일", "재고일", "매입채무일", "CCC"]}
            for h in history:
                cols[h["period"]] = [
                    f"{h['receivableDays']:.0f}" if h.get("receivableDays") is not None else "-",
                    f"{h['inventoryDays']:.0f}" if h.get("inventoryDays") is not None else "-",
                    f"{h['payableDays']:.0f}" if h.get("payableDays") is not None else "-",
                    f"{h['ccc']:.0f}" if h.get("ccc") is not None else "-",
                ]
            blocks.append(TableBlock("CCC 추이", pl.DataFrame(cols)))

    return blocks


# ── 2-3 안정성 ──


def leverageTrendBlock(data: dict) -> list:
    """calcLeverageTrend 결과 → 레버리지 시계열."""
    if not data:
        return []

    cols = _timelineTable(
        [
            (_extractSeries(data, "debtRatio"), "{:.0f}%"),
            (_extractSeries(data, "netDebtRatio"), "{:.0f}%"),
            (_extractSeries(data, "equityRatio"), "{:.0f}%"),
        ],
        ["부채비율", "순부채비율", "자기자본비율"],
    )
    if cols is None:
        return []

    blocks: list = [
        HeadingBlock(
            _meta("leverageTrend").label,
            level=2,
            helper="부채비율 200% 이상 위험, 50% 이하 매우 안정",
        ),
    ]

    narration = narrateLeverage(data)
    if narration:
        blocks.append(TextBlock(narration))

    blocks.append(TableBlock("레버리지 추이", pl.DataFrame(cols)))
    blocks.extend(_notesDetailBlocks(data, {"borrowings": "차입금 구성", "lease": "리스부채"}))

    history = data.get("history", [])
    if history:
        from dartlab.story.blocks import ChartBlock
        from dartlab.viz.generators import specLeverageTrend

        chart = specLeverageTrend(history)
        if chart:
            blocks.append(ChartBlock(spec=chart))
    return blocks


def coverageTrendBlock(data: dict) -> list:
    """calcCoverageTrend 결과 → 이자보상배율 시계열."""
    if not data:
        return []

    cols = _timelineTable(
        [(_extractSeries(data, "interestCoverage"), "{:.1f}배")],
        ["이자보상배율"],
    )
    if cols is None:
        return []

    return [
        HeadingBlock(
            _meta("coverageTrend").label,
            level=2,
            helper="이자보상배율 3배 이상 안정, 1배 미만 이자 지급 불능",
        ),
        TableBlock("이자보상 추이", pl.DataFrame(cols)),
    ]


def distressScoreBlock(data: dict) -> list:
    """calcDistressScore 결과 → Z-Score 시계열 + 등급."""
    if not data or data.get("status") != "ok":
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("distressScore").label,
            level=2,
            helper="비금융 Z'' > 2.6 안전, 1.1~2.6 회색, < 1.1 위험",
        )
    )

    narration = narrateDistress(data)
    if narration:
        blocks.append(TextBlock(narration))

    metrics = []
    latest = data.get("latestScore")
    zone = data.get("zone", "")
    if latest is not None:
        metrics.append(("최신 Z-Score", f"{latest:.2f}"))
    if zone:
        metrics.append(("판정", zone))
    if metrics:
        blocks.append(MetricBlock(metrics))

    cols = _timelineTable(
        [(_extractSeries(data, "zScore"), "{:.2f}")],
        ["Altman Z''-Score"],
    )
    if cols is not None:
        blocks.append(TableBlock("Z-Score 추이", pl.DataFrame(cols)))

    # 충당부채 주석은 위험/회색 구간일 때만 표시
    zone = data.get("zone", "")
    if zone in ("위험", "회색"):
        blocks.extend(_notesDetailBlocks(data, {"provisions": "충당부채 상세"}))

    return blocks


# ── 3-3 자본배분 ──


def dividendPolicyBlock(data: dict) -> list:
    """calcDividendPolicy 결과 → 배당 정책 시계열."""
    if not data:
        return []

    cols = _historyTable(
        data,
        [
            ("dividendsPaid", "배당금", "amt"),
            ("payoutRatio", "배당성향(%)", "{:.1f}%"),
            ("dividendGrowth", "배당성장률(%)", "{:+.1f}%"),
        ],
    )
    if cols is None:
        return []

    blocks: list = [
        HeadingBlock(
            _meta("dividendPolicy").label,
            level=2,
            helper="배당성향 100%+ = 이익 초과 배당",
        ),
        TableBlock("배당 추이", pl.DataFrame(cols)),
    ]

    consecutive = data.get("consecutiveYears", 0)
    if consecutive > 0:
        blocks.append(MetricBlock([("연속 배당", f"{consecutive}년")]))

    return blocks


def fcfUsageBlock(data: dict) -> list:
    """calcFcfUsage 결과 → FCF 사용처 시계열."""
    cols = _historyTable(
        data,
        [
            ("fcf", "FCF", "amt"),
            ("dividendsPaid", "배당", "amt"),
            ("debtRepaid", "부채상환", "amt"),
            ("residual", "잔여", "amt"),
        ],
    )
    if cols is None:
        return []
    return [
        HeadingBlock(
            _meta("fcfUsage").label,
            level=2,
            helper="잔여 = FCF - 배당 - 부채상환 (현금 축적 또는 투자)",
        ),
        TableBlock("FCF 사용처 추이", pl.DataFrame(cols)),
    ]


def treasuryStockStatusBlock(data: dict | None) -> list:
    """calcTreasuryStockStatus 결과 → 자사주 현황 테이블."""
    if not data:
        return []
    rows = data.get("rows", [])
    if not rows:
        return []

    table_rows = []
    for r in rows:
        row: dict = {"구분": r.get("method", "")}
        if r.get("acquired") is not None:
            row["취득"] = f"{r['acquired']:,.0f}"
        if r.get("disposed") is not None:
            row["처분"] = f"{r['disposed']:,.0f}"
        if r.get("retired") is not None:
            row["소각"] = f"{r['retired']:,.0f}"
        if r.get("endShares") is not None:
            row["잔량"] = f"{r['endShares']:,.0f}"
        table_rows.append(row)

    if not table_rows:
        return []

    source = data.get("source", "")
    helper = "자사주 취득/처분/소각 현황"
    if source == "XBRL":
        helper += " (EDGAR XBRL 기반)"

    return [
        HeadingBlock(_meta("treasuryStockStatus").label, level=2, helper=helper),
        TableBlock("자사주 현황", pl.DataFrame(table_rows)),
    ]


def capitalAllocationFlagsBlock(flags: list[str]) -> list:
    """calcCapitalAllocationFlags 결과 → FlagBlock."""
    return _flagsBlock(flags)


def dividendSustainabilityBlock(divData: dict | None, shData: dict | None) -> list:
    """배당 지속성 — 성향 5Y 평균 + FCF 커버리지 + 변동성.

    두 calc 결과(calcDividendPolicy, calcShareholderReturn)를 조합해 파생 지표를 만든다.
    엔진은 history만 반환, review가 조합/요약.
    """
    if not divData and not shData:
        return []

    divHist = (divData or {}).get("history", []) or []
    shHist = (shData or {}).get("history", []) or []

    if not divHist and not shHist:
        return []

    payouts = [h.get("payoutRatio") for h in divHist if h.get("payoutRatio") is not None]
    returnToFcfs = [h.get("returnToFcf") for h in shHist if h.get("returnToFcf") is not None]

    avgPayout = sum(payouts) / len(payouts) if payouts else None
    avgFcfCover = sum(returnToFcfs) / len(returnToFcfs) if returnToFcfs else None

    payoutVol = None
    if len(payouts) >= 2:
        mean = sum(payouts) / len(payouts)
        var = sum((p - mean) ** 2 for p in payouts) / len(payouts)
        payoutVol = var**0.5

    metrics: list[tuple[str, str]] = []
    if avgPayout is not None:
        metrics.append(("5Y 평균 배당성향", f"{avgPayout:.1f}%"))
    if avgFcfCover is not None:
        verdict = "지속 가능" if avgFcfCover <= 80 else "여유 부족" if avgFcfCover <= 100 else "FCF 초과"
        metrics.append(("5Y 평균 환원/FCF", f"{avgFcfCover:.0f}% ({verdict})"))
    if payoutVol is not None:
        metrics.append(("성향 변동성(σ)", f"{payoutVol:.1f}%p"))

    consecutive = (divData or {}).get("consecutiveYears")
    if consecutive and consecutive > 0:
        metrics.append(("연속 배당", f"{consecutive}년"))

    if not metrics:
        return []

    return [
        HeadingBlock(
            _meta("dividendSustainability").label,
            level=2,
            helper="환원/FCF 80% 이하 = 여유, 100% 초과 = FCF 초과 환원",
        ),
        MetricBlock(metrics),
    ]


def macroLiquidityBlock(data: dict) -> list:
    """macro 유동성 결과 → 유동성 환경."""
    if not data:
        return []

    regime = data.get("regime", "")
    if not regime:
        return []

    _REGIME_LABELS = {"abundant": "풍부", "normal": "보통", "tight": "긴축"}
    metrics: list[tuple[str, str]] = [
        ("유동성 국면", _REGIME_LABELS.get(regime, regime)),
    ]

    fci = data.get("fci")
    if isinstance(fci, dict):
        fci_val = fci.get("value")
        fci_label = fci.get("label", "")
        if fci_val is not None:
            metrics.append(("FCI", f"{fci_val:+.2f} ({fci_label})"))
    elif isinstance(fci, (int, float)):
        label = "완화" if fci < 0 else "긴축"
        metrics.append(("FCI", f"{fci:+.2f} ({label})"))

    nfci = data.get("nfci")
    if isinstance(nfci, dict):
        nfci_val = nfci.get("value")
        if nfci_val is not None:
            metrics.append(("NFCI", f"{nfci_val:+.2f}"))
    elif isinstance(nfci, (int, float)):
        metrics.append(("NFCI", f"{nfci:+.2f}"))

    capex = data.get("capexPressure")
    if isinstance(capex, dict):
        level = capex.get("level", "")
        if level:
            metrics.append(("설비투자 압력", level))

    return [
        HeadingBlock(
            _meta("macroLiquidity").label,
            level=2,
            helper="유동성 환경 + FCI → 기업 자금 접근성",
        ),
        MetricBlock(metrics),
    ]
