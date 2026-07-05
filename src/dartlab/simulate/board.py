"""파생 뷰 : 판독 합의 → board100 / top10 + red-flag·net-of-cost 게이트 (L2.5 simulate).

봉인 판독 위에 제품 표면을 얹는다 (06 §6). board100 = 표면 가중 합의 상위 100 + 표면별 의견
분해, top10 = red-flag 게이트(희석 사슬·거버넌스·감사지연·시장조치) + net-of-cost 게이트를
통과한 최상위. 판독은 봉인 이후라 selection bias 없음: 여기서는 이미 봉인된 것을 투영만 한다.

주장 규율: "규칙 기반 후보. 투자 추천·자문 아님. 성과 보장 없음. 가격수익 기준" (never-claim
상속). 미달 주는 그 수만 발행 (억지로 10개 채우기 금지).

Layer: L2.5 simulate. reading·profile 만 의존 (하향).
"""

from __future__ import annotations

import polars as pl

# never-claim 발간 문구 (파생 뷰 상속).
DISCLAIMER = "규칙 기반 후보. 투자 추천·자문 아님. 성과 보장 없음. 가격수익(배당·정조정 제외) 기준."


def combineReadings(readings: pl.DataFrame, surfaceWeights: dict[str, float] | None = None) -> pl.DataFrame:
    """표면 판독을 가중 합의로 → (code, consensus, nSurfaces). 가중 없으면 균등.

    Args:
        readings: (code, week, surface, direction, score) 한 주 판독.
        surfaceWeights: {surface: weight} (예 AdaHedge finalWeights 또는 성적표 t). None = 균등.

    Returns:
        (code, consensus, nSurfaces) consensus = sum(weight * direction * strength).
        strength = |score-0.5|*2 (중립 0, 극단 1). nSurfaces = 판독 발행 표면 수.
    """
    if readings.height == 0:
        return pl.DataFrame(schema={"code": pl.Utf8, "consensus": pl.Float64, "nSurfaces": pl.Int64})
    w = readings["surface"].unique().to_list()
    weights = surfaceWeights or {s: 1.0 for s in w}
    wdf = pl.DataFrame({"surface": list(weights), "w": [float(v) for v in weights.values()]})
    j = readings.join(wdf, on="surface", how="left").with_columns(pl.col("w").fill_null(1.0))
    j = j.with_columns(contrib=pl.col("w") * pl.col("direction") * ((pl.col("score") - 0.5).abs() * 2))
    return j.group_by("code").agg(consensus=pl.col("contrib").sum(), nSurfaces=pl.col("surface").n_unique())


def board100(readings: pl.DataFrame, *, surfaceWeights: dict[str, float] | None = None, n: int = 100) -> pl.DataFrame:
    """합의 상위 n + 표면별 의견 분해. → (code, consensus, nSurfaces, bySurface).

    Args:
        readings: 한 주 판독.
        surfaceWeights: 표면 가중.
        n: 상위 수 (기본 100).

    Returns:
        상위 n 종목 (consensus 내림차순) + 표면별 방향 분해 dict.
    """
    consensus = combineReadings(readings, surfaceWeights)
    if consensus.height == 0:
        return consensus.with_columns(bySurface=pl.lit(None, dtype=pl.Utf8))
    top = consensus.sort("consensus", descending=True).head(n)
    # 표면별 의견 분해 = "surface:direction" 문자열 요약 (판독 rank 나열 아님, 근거 투영).
    decomp = (
        readings.filter(pl.col("code").is_in(top["code"].to_list()))
        .with_columns(sd=pl.col("surface") + ":" + pl.col("direction").cast(pl.Utf8))
        .group_by("code")
        .agg(bySurface=pl.col("sd").str.join(" "))
    )
    return top.join(decomp, on="code", how="left")


def applyGates(
    board: pl.DataFrame,
    *,
    redFlagCodes: set[str] | None = None,
    netPositiveCodes: set[str] | None = None,
    n: int = 10,
) -> pl.DataFrame:
    """top10: red-flag 제외 + net-of-cost 통과만 상위 n. 미달이면 그 수만 (억지 채움 금지).

    Args:
        board: board100 산출.
        redFlagCodes: 제외할 red-flag 종목 (희석 사슬·거버넌스·감사지연·시장조치).
        netPositiveCodes: net-of-cost 양(+) 기대 종목 (없으면 게이트 미적용).
        n: 최대 수.

    Returns:
        게이트 통과 상위 n (없으면 그 수만). DISCLAIMER 상속은 호출측 발간에서.
    """
    out = board
    if redFlagCodes:
        out = out.filter(~pl.col("code").is_in(list(redFlagCodes)))
    if netPositiveCodes is not None:
        out = out.filter(pl.col("code").is_in(list(netPositiveCodes)))
    return out.sort("consensus", descending=True).head(n)
