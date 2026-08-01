"""story 블록 빌더 — asset 도메인 (debt-honesty P3-3 god-split). 공유 imports·상수·헬퍼는 _shared."""

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
    _meta,
    _notesDetailBlocks,
    _timelineTable,
    pl,
)

# ── 자산구조 (asset) 빌더 ──


def assetStructureBlock(data: dict) -> list:
    """calcAssetStructure 결과 → 영업/비영업 재분류 시계열."""
    if not data:
        return []

    history = data.get("history", [])
    if not history:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("assetStructure").label,
            level=2,
            helper="영업자산 = 사업에 투입된 자산, 비영업 = 현금/투자/금융자산",
        )
    )

    # 비중 시계열 테이블
    rows = ["총자산", "영업자산", "비영업자산", "순영업자산(NOA)", "순운전자본", "고정영업자산"]
    cols = {"": rows}
    for h in history:
        ta = h.get("totalAssets")
        cols[h["period"]] = [
            _fmtAmtShort(ta),
            f"{_fmtAmtShort(h['opAssets'])} ({h['opAssetsPct']:.0f}%)",
            f"{_fmtAmtShort(h['nonOpAssets'])} ({h['nonOpAssetsPct']:.0f}%)",
            _fmtAmtShort(h["noa"]),
            _fmtAmtShort(h["wc"]),
            _fmtAmtShort(h["fixedOp"]),
        ]
    blocks.append(TableBlock("자산 재분류 추이", pl.DataFrame(cols)))

    # 세부 구성 시계열 (영업+비영업 주요 항목)
    detailRows = ["매출채권", "재고자산", "유형자산", "무형자산+영업권", "건설중인자산", "현금성자산", "투자자산"]
    detailCols = {"": detailRows}
    for h in history:
        intangibles = h.get("intangibles")
        goodwill = h.get("goodwill")
        intGw = intangibles + goodwill if intangibles is not None and goodwill is not None else None
        detailCols[h["period"]] = [
            _fmtAmtShort(h.get("receivables")),
            _fmtAmtShort(h.get("inventory")),
            _fmtAmtShort(h.get("ppe")),
            _fmtAmtShort(intGw),
            _fmtAmtShort(h.get("cip")),
            _fmtAmtShort(h.get("cash")),
            _fmtAmtShort(h.get("investments")),
        ]
    blocks.append(TableBlock("자산 구성 상세 추이", pl.DataFrame(detailCols)))

    # 진단
    diagnosis = data.get("diagnosis")
    if diagnosis:
        blocks.append(TextBlock(diagnosis, style="dim", indent="h2"))

    blocks.extend(
        _notesDetailBlocks(
            data, {"inventory": "재고자산 상세", "tangibleAsset": "유형자산 변동", "intangibleAsset": "무형자산 상세"}
        )
    )

    return blocks


def capexBlock(data: dict) -> list:
    """calcCapexPattern 결과 → CAPEX/감가상각 + 건설중인자산."""
    if not data:
        return []

    latest = data.get("latest")
    if not latest:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("capexPattern").label,
            level=2,
            helper="CAPEX/감가상각 > 1 → 성장 투자, < 1 → 유지/수확",
        )
    )

    metrics = [
        ("CAPEX", _fmtAmtShort(latest["capex"])),
        ("감가상각", _fmtAmtShort(latest["depreciation"])),
    ]
    ratio = latest.get("capexToDepRatio")
    if ratio is not None:
        metrics.append(("CAPEX/감가상각", f"{ratio:.1f}배"))
    cip = latest.get("cip")
    if cip is not None and cip > 0:
        metrics.append(("건설중인자산", f"{_fmtAmtShort(cip)} ({latest['cipPct']:.0f}%)"))
    blocks.append(MetricBlock(metrics))

    investType = latest.get("investmentType")
    if investType:
        blocks.append(TextBlock(investType, style="dim", indent="h2"))

    # 시계열 (행=항목, 열=기간)
    history = data.get("history", [])
    if len(history) >= 2:
        cols = {"": ["CAPEX", "감가상각", "CAPEX/감가상각", "건설중인자산"]}
        for h in history:
            r = h.get("capexToDepRatio")
            cols[h["period"]] = [
                _fmtAmtShort(h["capex"]),
                _fmtAmtShort(h["depreciation"]),
                f"{r:.1f}배" if r is not None else "-",
                _fmtAmtShort(h["cip"]),
            ]
        blocks.append(TableBlock("CAPEX 추이", pl.DataFrame(cols)))

    return blocks


def assetEfficiencyBlock(data: dict) -> list:
    """calcAssetEfficiency 결과 → 회전율 시계열."""
    if not data:
        return []

    history = data.get("history", [])
    if len(history) < 2:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("assetEfficiency").label,
            level=2,
            helper="회전율이 높을수록 같은 자산으로 매출을 더 뽑는다",
        )
    )

    cols = {"": ["총자산회전율", "유형자산회전율"]}
    for h in history:
        ta = h.get("totalAssetTurnover")
        ppe = h.get("ppeTurnover")
        cols[h["period"]] = [
            f"{ta:.2f}회" if ta is not None else "-",
            f"{ppe:.2f}회" if ppe is not None else "-",
        ]
    blocks.append(TableBlock("회전율 추이", pl.DataFrame(cols)))

    return blocks


def assetFlagsBlock(flags: list[str]) -> list:
    """calcAssetFlags 결과 → FlagBlock."""
    if not flags:
        return []
    return [FlagBlock(flags, kind="warning")]


# ── 2-4 효율성 ──


def turnoverTrendBlock(data: dict) -> list:
    """calcTurnoverTrend 결과 → 회전율 시계열."""
    if not data:
        return []

    cols = _timelineTable(
        [
            (_extractSeries(data, "totalAssetTurnover"), "{:.2f}회"),
            (_extractSeries(data, "receivablesTurnover"), "{:.2f}회"),
            (_extractSeries(data, "inventoryTurnover"), "{:.2f}회"),
        ],
        ["총자산회전율", "매출채권회전율", "재고회전율"],
    )
    if cols is None:
        return []

    return [
        HeadingBlock(
            _meta("turnoverTrend").label,
            level=2,
            helper="회전율 상승 = 같은 자산으로 매출을 더 뽑는다",
        ),
        TableBlock("회전율 추이", pl.DataFrame(cols)),
    ]


def cccTrendBlock(data: dict) -> list:
    """calcTurnoverTrend 결과 → CCC 구성요소 시계열."""
    if not data:
        return []

    cols = _timelineTable(
        [
            (_extractSeries(data, "dso"), "{:.0f}일"),
            (_extractSeries(data, "dio"), "{:.0f}일"),
            (_extractSeries(data, "dpo"), "{:.0f}일"),
            (_extractSeries(data, "ccc"), "{:.0f}일"),
        ],
        ["DSO(매출채권일)", "DIO(재고일)", "DPO(매입채무일)", "CCC"],
    )
    if cols is None:
        return []

    return [
        HeadingBlock(
            _meta("cccTrend").label,
            level=2,
            helper="CCC = DSO + DIO - DPO, 마이너스면 운전자본 유리",
        ),
        TableBlock("CCC 추이", pl.DataFrame(cols)),
    ]


def efficiencyFlagsBlock(flags: list[str]) -> list:
    """calcEfficiencyFlags 결과 → FlagBlock."""
    return _flagsBlock(flags)


def assetSignalsBlock(data: dict) -> list:
    """calcAssetSignals 결과 → 5대 자산 해석."""
    if not data:
        return []

    assets = data.get("assets", [])
    if not assets:
        return []

    blocks: list = [
        HeadingBlock(
            _meta("assetSignals").label,
            level=2,
            helper="금리·환율·금·VIX 현재 상태와 해석",
        ),
    ]

    for a in assets:
        line = f"{a['label']}: {a['interpretation']}"
        relevance = a.get("companyRelevance")
        if relevance:
            line += f" → {relevance}"
        blocks.append(TextBlock(line))

    return blocks
