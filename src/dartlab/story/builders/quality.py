"""story 블록 빌더 — quality 도메인 (debt-honesty P3-3 god-split). 공유 imports·상수·헬퍼는 _shared."""

from __future__ import annotations

from dartlab.story.builders._shared import (
    FlagBlock,
    HeadingBlock,
    MetricBlock,
    TableBlock,
    TextBlock,
    _enrichedFlagsBlock,
    _flagsBlock,
    _historyTable,
    _meta,
    _notesDetailBlocks,
    pl,
    unifyTableScale,
)

# ── 2-5 종합 평가 ──


def scorecardBlock(data: dict) -> list:
    """calcScorecard 결과 → 5영역 등급 테이블."""
    if not data:
        return []

    items = data.get("items", [])
    if not items:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("scorecard").label,
            level=2,
            helper="F 등급 영역을 최우선으로 개선 검토",
        )
    )

    rows = []
    for item in items:
        rows.append({"영역": item["area"], "등급": item["grade"]})
    blocks.append(TableBlock("", pl.DataFrame(rows)))

    profile = data.get("profile", "")
    if profile:
        blocks.append(TextBlock(f"재무 프로필: {profile}", style="dim", indent="h2"))

    return blocks


def piotroskiBlock(data: dict) -> list:
    """calcPiotroskiDetail 결과 → 9개 항목 상세."""
    if not data:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("piotroski").label,
            level=2,
            helper="9점 만점, 7+ 건전, 3- 심각",
        )
    )

    total = data.get("total", 0)
    interp = data.get("interpretation", "")
    interpKor = {"strong": "건전", "moderate": "보통", "weak": "취약"}.get(interp, interp)
    blocks.append(MetricBlock([("F-Score", f"{total}/9 ({interpKor})")]))

    items = data.get("items", [])
    if items:
        rows = []
        for item in items:
            rows.append(
                {
                    "항목": item["signal"],
                    "충족": "O" if item["pass"] else "X",
                }
            )
        blocks.append(TableBlock("", pl.DataFrame(rows)))

    return blocks


def summaryFlagsBlock(flags: list[str]) -> list:
    """calcSummaryFlags 결과 → FlagBlock."""
    if not flags:
        return []
    return [FlagBlock(flags, kind="warning")]


# ── 3-1 이익품질 ──


def accrualAnalysisBlock(data: dict) -> list:
    """calcAccrualAnalysis 결과 → 발생액 시계열."""
    cols = _historyTable(
        data,
        [
            ("sloanAccrualRatio", "Sloan 발생액비율", "{:.2f}"),
            ("accrualToRevenue", "발생액/매출(%)", "{:.1f}%"),
            ("ocfToNi", "영업CF/순이익(%)", "{:.0f}%"),
        ],
    )
    if cols is None:
        return []
    blocks: list = [
        HeadingBlock(
            _meta("accrualAnalysis").label,
            level=2,
            helper="발생액비율 0.10 이상 = 이익 현금화 부족",
        ),
        TableBlock("발생액 추이", pl.DataFrame(cols)),
    ]
    blocks.extend(_notesDetailBlocks(data, {"receivables": "매출채권 상세"}))
    return blocks


def earningsPersistenceBlock(data: dict) -> list:
    """calcEarningsPersistence 결과 → 이익 지속성."""
    if not data:
        return []

    cols = _historyTable(
        data,
        [
            ("operatingIncome", "영업이익", "amt"),
            ("nonOperatingIncome", "영업외손익", "amt"),
            ("nonOpRatio", "영업외비중(%)", "{:.1f}%"),
        ],
    )
    if cols is None:
        return []

    blocks: list = [
        HeadingBlock(
            _meta("earningsPersistence").label,
            level=2,
            helper="영업외비중 30%+ = 일회성 이익 의존",
        ),
        TableBlock("이익 구성 추이", pl.DataFrame(cols)),
    ]

    cv = data.get("earningsVolatility")
    if cv is not None:
        blocks.append(MetricBlock([("이익 변동계수(CV)", f"{cv:.2f}")]))

    return blocks


def beneishMScoreBlock(data: dict) -> list:
    """calcBeneishTimeline 결과 → M-Score 시계열."""
    cols = _historyTable(
        data,
        [
            ("mScore", "M-Score", "{:.2f}"),
        ],
    )
    if cols is None:
        return []

    blocks: list = [
        HeadingBlock(
            _meta("beneishMScore").label,
            level=2,
            helper="M-Score > -1.78 임계값 초과 = 이익 조작 가능성",
        ),
        TableBlock("M-Score 추이", pl.DataFrame(cols)),
    ]

    threshold = data.get("threshold")
    if threshold is not None:
        blocks.append(TextBlock(f"임계값: {threshold}", style="dim", indent="h2"))

    return blocks


def earningsQualityFlagsBlock(data) -> list:
    """calcEarningsQualityFlags 결과 → FlagBlock."""
    if isinstance(data, dict):
        return _enrichedFlagsBlock(data.get("flags", []), data.get("enrichedFlags"))
    # 하위호환: list[str] 직접 전달
    return _flagsBlock(data if isinstance(data, list) else [])


# ── 3-5 재무정합성 ──


def isCfDivergenceBlock(data: dict) -> list:
    """calcIsCfDivergence 결과 → IS-CF 괴리 시계열."""
    cols = _historyTable(
        data,
        [
            ("netIncome", "순이익", "amt"),
            ("ocf", "영업CF", "amt"),
            ("divergence", "괴리율(%)", "{:+.0f}%"),
            ("direction", "방향", "{}"),
        ],
    )
    if cols is None:
        return []
    return [
        HeadingBlock(
            _meta("isCfDivergence").label,
            level=2,
            helper="괴리 > 50% = 순이익 대비 현금흐름 극심한 차이",
        ),
        TableBlock("IS-CF 괴리 추이", pl.DataFrame(cols)),
    ]


def isBsDivergenceBlock(data: dict) -> list:
    """calcIsBsDivergence 결과 → IS-BS 괴리 시계열."""
    cols = _historyTable(
        data,
        [
            ("revenueGrowth", "매출성장(%)", "{:+.1f}%"),
            ("receivableGrowth", "매출채권성장(%)", "{:+.1f}%"),
            ("inventoryGrowth", "재고성장(%)", "{:+.1f}%"),
            ("revRecGap", "채권-매출 갭(%p)", "{:+.1f}%p"),
            ("revInvGap", "재고-매출 갭(%p)", "{:+.1f}%p"),
        ],
    )
    if cols is None:
        return []
    return [
        HeadingBlock(
            _meta("isBsDivergence").label,
            level=2,
            helper="채권/재고 성장이 매출보다 20%p+ 빠르면 의심",
        ),
        TableBlock("IS-BS 괴리 추이", pl.DataFrame(cols)),
    ]


def anomalyScoreBlock(data: dict) -> list:
    """calcAnomalyScore 결과 → 이상 점수 시계열."""
    if not data:
        return []
    history = data.get("history", [])
    if not history:
        return []

    blocks: list = [
        HeadingBlock(
            _meta("anomalyScore").label,
            level=2,
            helper="70점 이상 = 재무제표 신뢰성 주의",
        ),
    ]

    # 점수 시계열
    cols: dict[str, list[str]] = {"": ["종합 점수"]}
    for h in history:
        cols[h["period"]] = [f"{h['score']:.0f}"]
    blocks.append(TableBlock("이상 점수 추이", pl.DataFrame(cols)))

    # 최신 구성요소
    h0 = history[0]
    components = h0.get("components", {})
    if components:
        metrics = [(k, f"{v:.1f}") for k, v in components.items()]
        blocks.append(MetricBlock(metrics))

    return blocks


def effectiveTaxRateBlock(data: dict) -> list:
    """calcEffectiveTaxRate 결과 → 유효세율 시계열."""
    cols = _historyTable(
        data,
        [
            ("effectiveTaxRate", "유효세율(%)", "{:.1f}%"),
            ("statutoryRate", "법정세율(%)", "{:.0f}%"),
            ("taxGap", "세율갭(%p)", "{:+.1f}%p"),
        ],
    )
    if cols is None:
        return []
    return [
        HeadingBlock(
            _meta("effectiveTaxRate").label,
            level=2,
            helper="유효세율 < 10% 극저, > 35% 고세율",
        ),
        TableBlock("유효세율 추이", pl.DataFrame(cols)),
    ]


def deferredTaxBlock(data: dict) -> list:
    """calcDeferredTax 결과 → 이연법인세 시계열."""
    cols = _historyTable(
        data,
        [
            ("deferredTaxAsset", "이연법인세자산", "amt"),
            ("deferredTaxLiability", "이연법인세부채", "amt"),
            ("netDeferredTax", "순이연법인세", "amt"),
            ("dtaToTotalAssets", "DTA/총자산(%)", "{:.2f}%"),
        ],
    )
    if cols is None:
        return []
    return [
        HeadingBlock(
            _meta("deferredTax").label,
            level=2,
            helper="이연법인세자산 급증 = 미래 과세소득 가정 검토",
        ),
        TableBlock("이연법인세 추이", pl.DataFrame(cols)),
    ]


def crossStatementFlagsBlock(flags: list[str]) -> list:
    """교차검증+세금 플래그 통합 -> FlagBlock."""
    return _flagsBlock(flags)


def historicalRatiosBlock(data: dict) -> list:
    """calcHistoricalRatios -> 과거 구조 비율."""
    if not data:
        return []
    blocks: list = [
        HeadingBlock(
            _meta("historicalRatios").label,
            level=2,
            helper="Pro-Forma의 기반이 되는 과거 재무 비율",
        ),
    ]

    metrics = [
        ("매출총이익률", f"{data.get('grossMargin', 0):.1f}%"),
        ("판관비율", f"{data.get('sgaRatio', 0):.1f}%"),
        ("유효세율", f"{data.get('effectiveTaxRate', 0):.1f}%"),
        ("CAPEX/매출", f"{data.get('capexToRevenue', 0):.1f}%"),
        ("NWC/매출", f"{data.get('nwcToRevenue', 0):.1f}%"),
        ("배당성향", f"{data.get('dividendPayout', 0):.1f}%"),
        ("사용 연수", f"{data.get('yearsUsed', 0)}년"),
        ("신뢰도", data.get("confidence", "")),
    ]
    blocks.append(MetricBlock(metrics))

    for w in data.get("warnings", []):
        blocks.append(TextBlock(f"-- {w}", style="dim"))
    return blocks


def calibrationReportBlock(data: dict) -> list:
    """calcCalibrationReport -> Brier Score + bin 테이블."""
    if not data:
        return []
    blocks: list = [
        HeadingBlock(
            _meta("calibrationReport").label,
            level=2,
            helper="과거 예측 확률의 실제 적중률 검증 (Brier Score)",
        ),
    ]
    metrics = [
        ("Brier Score", f"{data['brierScore']:.4f}"),
        ("평가 건수", str(data.get("nRecords", 0))),
    ]
    blocks.append(MetricBlock(metrics))

    bins = data.get("bins", [])
    if bins:
        import polars as pl

        rows = [
            {
                "구간": f"{b['binLower']:.0%}~{b['binUpper']:.0%}",
                "평균 예측": f"{b['meanPredicted']:.1%}",
                "실제 적중": f"{b['meanActual']:.1%}",
                "괴리": f"{b['gap']:.1%}",
                "건수": str(b["count"]),
            }
            for b in bins
        ]
        blocks.append(TableBlock("확률 구간별 적중률", pl.DataFrame(rows)))

    return blocks


# ── Penman 분해 빌더 ──


def penmanDecompositionBlock(data: dict) -> list:
    """calcPenmanDecomposition → HeadingBlock + TableBlock."""
    if not data:
        return []
    history = data.get("history", [])
    if not history:
        return []

    rows = []
    for h in history:
        rows.append(
            {
                "기간": h["period"],
                "RNOA": f"{h['rnoa']:.1f}%" if h.get("rnoa") is not None else "-",
                "FLEV": f"{h['flev']:.2f}" if h.get("flev") is not None else "-",
                "NBC": f"{h['nbc']:.1f}%" if h.get("nbc") is not None else "-",
                "SPREAD": f"{h['spread']:.1f}%p" if h.get("spread") is not None else "-",
                "레버리지효과": f"{h['leverageEffect']:.1f}%p" if h.get("leverageEffect") is not None else "-",
                "ROCE": f"{h['roce']:.1f}%" if h.get("roce") is not None else "-",
            }
        )

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("penmanDecomposition").label,
            level=2,
            helper="RNOA > NBC이면 차입이 주주에게 유리 (양의 SPREAD)",
        )
    )
    blocks.append(TableBlock("", pl.DataFrame(rows)))
    return blocks


# ── Richardson 3계층 발생액 빌더 ──


def richardsonAccrualBlock(data: dict) -> list:
    """calcRichardsonAccrual → HeadingBlock + TableBlock."""
    if not data:
        return []
    history = data.get("history", [])
    if not history:
        return []

    rows = []
    for h in history:
        rows.append(
            {
                "기간": h["period"],
                "WCACC": h.get("wcacc"),
                "LTOACC": h.get("ltoacc"),
                "FINACC": h.get("finacc"),
                "총발생액": h.get("totalAccrual"),
                "신뢰도": h.get("reliabilityScore", "-"),
            }
        )

    valueCols = ["WCACC", "LTOACC", "FINACC", "총발생액"]
    unified = unifyTableScale(rows, "기간", valueCols, unit="millions")

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("richardsonAccrual").label,
            level=2,
            helper="LTOACC 비중이 높을수록 이익 지속성 낮음 (신뢰도↓)",
        )
    )
    blocks.append(TableBlock("", pl.DataFrame(unified)))
    return blocks


# ── CAGR 비교 빌더 ──


def cagrComparisonBlock(data: dict) -> list:
    """calcCagrComparison → HeadingBlock + TableBlock."""
    if not data:
        return []
    comparisons = data.get("comparisons", [])
    if not comparisons:
        return []

    rows = []
    for c in comparisons:
        rows.append(
            {
                "비교": c["label"],
                c["item1"]: f"{c['cagr1']:+.1f}%" if c.get("cagr1") is not None else "-",
                c["item2"]: f"{c['cagr2']:+.1f}%" if c.get("cagr2") is not None else "-",
                "갭": f"{c['gap']:+.1f}%p" if c.get("gap") is not None else "-",
                "시그널": c.get("signal", "-"),
            }
        )

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("cagrComparison").label,
            level=2,
            helper="매출 vs 이익 CAGR 갭 → 마진 방향, 자산 vs 매출 갭 → 효율 방향",
        )
    )
    blocks.append(TableBlock("", pl.DataFrame(rows)))
    return blocks


# ── BS-CF 정합성 빌더 ──


def articulationCheckBlock(data: dict) -> list:
    """calcArticulationCheck → HeadingBlock + TableBlock."""
    if not data:
        return []
    history = data.get("history", [])
    if not history:
        return []

    rows = []
    for h in history:
        rows.append(
            {
                "기간": h["period"],
                "PPE오차": f"{h['ppeError']:.1f}%" if h.get("ppeError") is not None else "-",
                "현금오차": f"{h['cashError']:.1f}%" if h.get("cashError") is not None else "-",
                "자본오차": f"{h['equityError']:.1f}%" if h.get("equityError") is not None else "-",
                "최대오차": f"{h['maxErrorPct']:.1f}%" if h.get("maxErrorPct") is not None else "-",
            }
        )

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("articulationCheck").label,
            level=2,
            helper="오차 > 10%이면 연결범위 변동/환율효과/재분류 의심",
        )
    )
    blocks.append(TableBlock("", pl.DataFrame(rows)))
    return blocks


def piotroskiFactorBlock(data) -> list:
    """calcPiotroskiFactor → strong/moderate/weak 분포 + 9 신호 평균 통과율."""
    if not data:
        return []
    grades = data.get("grades", {})
    metrics = [
        ("strong (F ≥ 7)", f"{grades.get('strong', {}).get('count', 0)}사 ({grades.get('strong', {}).get('pct', 0)}%)"),
        (
            "moderate (F 4~6)",
            f"{grades.get('moderate', {}).get('count', 0)}사 ({grades.get('moderate', {}).get('pct', 0)}%)",
        ),
        ("weak (F ≤ 3)", f"{grades.get('weak', {}).get('count', 0)}사 ({grades.get('weak', {}).get('pct', 0)}%)"),
    ]
    signalAvg = data.get("signalAvg", {})
    signal_labels = {
        "roaPositive": "ROA+",
        "ocfPositive": "OCF+",
        "roaIncreasing": "ROA↑",
        "cfGtNi": "CF>NI",
        "debtDecreasing": "부채↓",
        "currentRatioUp": "유동비↑",
        "noNewShares": "미희석",
        "grossMarginUp": "GM↑",
        "assetTurnoverUp": "회전↑",
    }
    if signalAvg:
        sig_str = ", ".join(f"{signal_labels.get(k, k)} {v:.0f}%" for k, v in signalAvg.items())
        metrics.append(("9 신호 시장 통과율", sig_str))
    return [
        HeadingBlock(
            _meta("piotroskiFactor").label,
            level=2,
            helper=f"Piotroski F-Score ({data.get('year')} vs {data.get('prevYear')}, {data.get('universe')}종목). {data.get('interpretation', '')}",
        ),
        MetricBlock(metrics),
    ]


def beneishFactorBlock(data) -> list:
    """calcBeneishFactor → red flag 비율 + top 의심 10."""
    if not data or data.get("status") != "ok":
        return []
    flags = data.get("flags", {})
    metrics = [
        (
            "red flag (M > -1.78)",
            f"{flags.get('redFlag', {}).get('count', 0)}사 ({flags.get('redFlag', {}).get('pct', 0)}%)",
        ),
        ("clean", f"{flags.get('clean', {}).get('count', 0)}사 ({flags.get('clean', {}).get('pct', 0)}%)"),
    ]
    topFlag = data.get("topFlag") or []
    if topFlag:
        metrics.append(("top 5 의심", ", ".join(f"{c}({m})" for c, m in topFlag[:5])))
    return [
        HeadingBlock(
            _meta("beneishFactor").label,
            level=2,
            helper=f"Beneish M-Score ({data.get('year')} vs {data.get('prevYear')}, {data.get('universe')}종목). {data.get('interpretation', '')}",
        ),
        MetricBlock(metrics),
    ]


def accrualsFactorBlock(data) -> list:
    """calcAccrualsFactor → high/neutral/low 분포."""
    if not data:
        return []
    groups = data.get("groups", {})
    metrics = [
        (
            "high accrual (> +5%)",
            f"{groups.get('high', {}).get('count', 0)}사 ({groups.get('high', {}).get('pct', 0)}%) — reversal risk",
        ),
        ("neutral", f"{groups.get('neutral', {}).get('count', 0)}사 ({groups.get('neutral', {}).get('pct', 0)}%)"),
        (
            "low (< -5%)",
            f"{groups.get('low', {}).get('count', 0)}사 ({groups.get('low', {}).get('pct', 0)}%) — cash quality premium",
        ),
    ]
    return [
        HeadingBlock(
            _meta("accrualsFactor").label,
            level=2,
            helper=f"Sloan Accrual ({data.get('year')}, {data.get('universe')}종목). {data.get('interpretation', '')}",
        ),
        MetricBlock(metrics),
    ]


def earningsSurpriseBlock(data) -> list:
    """calcEarningsSurprise → top positive/negative SUE."""
    if not data:
        return []
    topPos = data.get("topPos") or []
    topNeg = data.get("topNeg") or []
    metrics = []
    if topPos:
        metrics.append(("top positive SUE 5", ", ".join(f"{c}(z={z} g={g:+.0%})" for c, z, g in topPos[:5])))
    if topNeg:
        metrics.append(("top negative SUE 5", ", ".join(f"{c}(z={z} g={g:+.0%})" for c, z, g in topNeg[:5])))
    return [
        HeadingBlock(
            _meta("earningsSurprise").label,
            level=2,
            helper=f"Earnings Surprise ({data.get('year')} vs {data.get('prevYear')}, {data.get('universe')}종목). {data.get('interpretation', '')}",
        ),
        MetricBlock(metrics),
    ]
