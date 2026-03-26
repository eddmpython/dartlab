from dartlab.providers.dart.docs.finance.summary.constants import BREAKPOINT_THRESHOLD
from dartlab.providers.dart.docs.finance.summary.types import BridgeResult, Segment


def detectBreakpoints(
    pairResults: list[BridgeResult],
    sortedYears: list[str],
    threshold: float = BREAKPOINT_THRESHOLD,
) -> tuple[list[Segment], list[BridgeResult]]:
    """전환점 탐지 + 구간 분리. 매칭률이 threshold 미만이면 전환점으로 판정."""
    segments: list[dict] = [{"years": [sortedYears[0]], "pairs": []}]
    breakpoints: list[BridgeResult] = []

    for pr in pairResults:
        isBreak = pr.rate < threshold
        if isBreak:
            breakpoints.append(pr)
            segments.append({"years": [pr.prevYear], "pairs": []})
        else:
            segments[-1]["years"].append(pr.prevYear)
            segments[-1]["pairs"].append(pr)

    segmentStats: list[Segment] = []
    for seg in segments:
        if not seg["pairs"]:
            segmentStats.append(
                Segment(
                    startYear=seg["years"][0],
                    endYear=seg["years"][-1],
                    nYears=len(seg["years"]),
                    matched=0,
                    total=0,
                    rate=None,
                )
            )
            continue
        segMatched = sum(p.matched for p in seg["pairs"])
        segTotal = sum(p.total for p in seg["pairs"])
        segRate = segMatched / segTotal if segTotal > 0 else 0.0
        segmentStats.append(
            Segment(
                startYear=seg["years"][0],
                endYear=seg["years"][-1],
                nYears=len(seg["years"]),
                matched=segMatched,
                total=segTotal,
                rate=segRate,
            )
        )

    return segmentStats, breakpoints
