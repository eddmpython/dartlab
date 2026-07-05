"""연장 밴드 : 횡단면 split conformal x 시간축 ACI (적응형 커버리지) (L2.5 simulate).

시뮬 산출(원천 동형 연장·판독 forward 예측)의 불확실성을 채점 가능한 밴드로 낸다 (06 §5c 4계약
③). "80% 밴드" 선언 자체가 매주 채점되는 약속이 되게 한다. ① 횡단면 분할 conformal: 주별
전종목 nonconformity 점수 풀 + 종목 변동성 표준화 + Mondrian(사이즈 버킷)별 분위. ② 시간축 ACI
(Gibbs-Candes Adaptive Conformal Inference): 지난 주 실측 커버리지로 유효 α 를 피드백 제어
(α_{t+1}=α_t+γ(α목표 - 미커버율)). 분포 이동과 무관하게 장기 커버리지가 선언값에 수렴한다.
③ 채점: 적중 여부 + Winkler 구간 점수 + 버킷별 커버리지 병기 (전체 80% 가 소형주 60% 를
숨기는 것 차단). 주장 규율: 장기 수렴만 보장, 개별 주 커버리지 주장 금지.

Layer: L2.5 simulate. numpy · polars 만 의존.
"""

from __future__ import annotations

import numpy as np
import polars as pl

_MIN_CALIB = 20  # 밴드 산출 최소 캘리브레이션 점수 수
_DEFAULT_WINDOW = 52  # 롤링 캘리브레이션 창 (주). 분포 이동 적응.


def splitConformalQ(calibScores: np.ndarray, alpha: float) -> float:
    """분할 conformal 분위: 캘리브레이션 nonconformity 점수의 (1-α)(1+1/n) 분위 (유한표본 보정)."""
    s = np.asarray(calibScores, dtype=float)
    s = s[~np.isnan(s)]
    n = s.size
    if n == 0:
        return float("inf")
    level = min(1.0, (1 - alpha) * (1 + 1.0 / n))
    return float(np.quantile(s, level, method="higher"))


def winklerScore(lo: np.ndarray, hi: np.ndarray, y: np.ndarray, alpha: float) -> np.ndarray:
    """Winkler 구간 점수: 폭 + 미달/초과 페널티 (2/α). 좁고 적중하는 구간이 낮음 (낮을수록 좋음)."""
    lo, hi, y = np.asarray(lo), np.asarray(hi), np.asarray(y)
    width = hi - lo
    below = (y < lo) * (2.0 / alpha) * (lo - y)
    above = (y > hi) * (2.0 / alpha) * (y - hi)
    return width + below + above


def _bucketByWeek(size: np.ndarray, nBuckets: int) -> np.ndarray:
    """주 내 사이즈 랭크 → Mondrian 버킷 인덱스 (0..nBuckets-1). 결측은 중앙 버킷."""
    valid = ~np.isnan(size)
    out = np.full(size.shape, nBuckets // 2, dtype=int)
    if valid.sum() == 0:
        return out
    ranks = np.argsort(np.argsort(size[valid])) / max(valid.sum() - 1, 1)
    out[valid] = np.clip((ranks * nBuckets).astype(int), 0, nBuckets - 1)
    return out


def aciBands(
    panel: pl.DataFrame,
    *,
    alpha0: float = 0.2,
    gamma: float = 0.05,
    calibWindow: int = _DEFAULT_WINDOW,
    minCalib: int = _MIN_CALIB,
    nBuckets: int = 5,
) -> dict:
    """패널 (week, code, pred, actual, scale, size) → ACI 적응 밴드 + 커버리지 채점.

    Args:
        panel: (week, code, pred 점예측, actual 실측, scale 표준화 척도, size 사이즈).
        alpha0: 선언 미커버 목표 (0.2 = 80% 밴드).
        gamma: ACI 학습률 (α 피드백 보폭).
        calibWindow: 롤링 캘리브레이션 창 (주).
        minCalib: 밴드 산출 최소 캘리브 점수. 미달 주-버킷은 밴드 미발행(NaN).
        nBuckets: Mondrian 사이즈 버킷 수.

    Returns:
        {"bands": (week, code, bucket, lo, hi, covered, winkler),
         "coverageCurve": (week, coverage, alpha), "coverage": 전체 커버리지,
         "winkler": 평균 Winkler, "byBucket": (bucket, coverage, n), "declared": 1-alpha0}.
        ACI 는 버킷별 α_t 를 실측 미커버율로 갱신 (분포 이동에도 장기 커버리지 수렴).
    """
    df = panel.sort("week")
    weeks = df["week"].unique().sort().to_list()
    alpha = np.full(nBuckets, alpha0)  # 버킷별 유효 α_t
    calib: list[list[np.ndarray]] = [[] for _ in range(nBuckets)]  # 버킷별 최근 주 점수 (롤링)
    bandRows, covRows = [], []
    for w in weeks:
        wk = df.filter(pl.col("week") == w)
        pred = wk["pred"].to_numpy().astype(float)
        actual = wk["actual"].to_numpy().astype(float)
        scale = wk["scale"].to_numpy().astype(float) if "scale" in wk.columns else np.ones(wk.height)
        scale = np.where((scale > 0) & np.isfinite(scale), scale, 1.0)
        size = wk["size"].to_numpy().astype(float) if "size" in wk.columns else np.zeros(wk.height)
        codes = wk["code"].to_list()
        bucket = _bucketByWeek(size, nBuckets)
        lo = np.full(wk.height, np.nan)
        hi = np.full(wk.height, np.nan)
        for b in range(nBuckets):
            past = np.concatenate(calib[b]) if calib[b] else np.zeros(0)
            if past.size < minCalib:
                continue
            q = splitConformalQ(past, alpha[b])
            m = bucket == b
            lo[m] = pred[m] - q * scale[m]
            hi[m] = pred[m] + q * scale[m]
        covered = (actual >= lo) & (actual <= hi)
        # 이번 주 nonconformity 점수 (표준화 절대잔차) → 롤링 캘리브 갱신, α_t ACI 피드백.
        score = np.abs(actual - pred) / scale
        for b in range(nBuckets):
            m = bucket == b
            if m.sum() == 0:
                continue
            calib[b].append(score[m])
            if len(calib[b]) > calibWindow:
                calib[b].pop(0)
            banded = m & ~np.isnan(lo)
            if banded.sum() > 0:
                miscov = 1.0 - float(covered[banded].mean())
                alpha[b] = float(np.clip(alpha[b] + gamma * (alpha0 - miscov), 1e-3, 0.999))
        wnk = winklerScore(np.where(np.isnan(lo), 0, lo), np.where(np.isnan(hi), 0, hi), actual, alpha0)
        for i in range(wk.height):
            if np.isnan(lo[i]):
                continue
            bandRows.append(
                {
                    "week": w,
                    "code": codes[i],
                    "bucket": int(bucket[i]),
                    "lo": float(lo[i]),
                    "hi": float(hi[i]),
                    "covered": bool(covered[i]),
                    "winkler": float(wnk[i]),
                }
            )
        banded = ~np.isnan(lo)
        if banded.sum() > 0:
            covRows.append({"week": w, "coverage": float(covered[banded].mean()), "alpha": float(alpha.mean())})
    bands = pl.DataFrame(bandRows) if bandRows else _emptyBands()
    coverageCurve = (
        pl.DataFrame(covRows)
        if covRows
        else pl.DataFrame(schema={"week": pl.Int64, "coverage": pl.Float64, "alpha": pl.Float64})
    )
    overall = float(bands["covered"].mean()) if bands.height else float("nan")
    winkler = float(bands["winkler"].mean()) if bands.height else float("nan")
    byBucket = (
        bands.group_by("bucket").agg(coverage=pl.col("covered").mean(), n=pl.len()).sort("bucket")
        if bands.height
        else pl.DataFrame(schema={"bucket": pl.Int64, "coverage": pl.Float64, "n": pl.Int64})
    )
    return {
        "bands": bands,
        "coverageCurve": coverageCurve,
        "coverage": overall,
        "winkler": winkler,
        "byBucket": byBucket,
        "declared": 1 - alpha0,
    }


def _emptyBands() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "week": pl.Int64,
            "code": pl.Utf8,
            "bucket": pl.Int64,
            "lo": pl.Float64,
            "hi": pl.Float64,
            "covered": pl.Boolean,
            "winkler": pl.Float64,
        }
    )
