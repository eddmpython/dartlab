"""표면 인증 : 다중검정 깔때기 (BH/BHY FDR + Hansen SPA + Romano-Wolf) (L2.5 simulate).

전수 스캔 우주에서 수백 표면을 채점하면 순전한 우연으로 |t|>3 이 나온다 (factor zoo). 이 모듈은
표면 승격을 2단 깔때기로 통제한다 (06 §4). ① 발굴 = 주단위 t 에 BH/BHY FDR (q 5~10%) + 운영
상수 t>3. ② 인증 = 전수 우주에 Hansen SPA + Romano-Wolf stepdown. 정상성 부트스트랩(Politis-
Romano)을 주 단위로 재표집해 타입 간 상관을 보존한다 (arch 미의존, numpy 자급, seed 결정론).
신규 표면 기여는 상관 클러스터 유효 검정수(Galwey Meff)로 수축해 이중 계산을 막는다.

- ``benjaminiHochberg`` / ``benjaminiYekutieli`` : FDR step-up (독립 / 임의 의존).
- ``hansenSpa`` : max 통계 초과확률 (least-favorable 재중심, 데이터 스누핑 통제 인증).
- ``romanoWolf`` : FWER stepdown (인증 표면 집합).
- ``corrClusterEffN`` / ``empiricalBayesShrink`` : 유효 검정수 · 수축 추정.
- ``certify`` : 표면 성적표 → verdict 인증/발굴/동물원구분불가/미검증.

Layer: L2.5 simulate. numpy 만 의존 (부트스트랩 자급).
"""

from __future__ import annotations

import math

import numpy as np
import polars as pl

from dartlab.simulate.reading import FACTOR_ZOO_T, SCORECARD_MIN_WEEKS

_DEFAULT_BOOT = 1000
_DEFAULT_MEAN_BLOCK = 5.0  # 정상성 부트스트랩 기대 블록 길이 (주). 주간 군집 보존.
_DEFAULT_SEED = 20260705


def _normalTwoSidedP(t: np.ndarray) -> np.ndarray:
    """양측 정규 근사 p-value. p = 2(1 - Φ(|t|))."""
    return np.array([2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(x) / math.sqrt(2)))) for x in t])


def benjaminiHochberg(pvals: np.ndarray, q: float = 0.10) -> np.ndarray:
    """BH step-up FDR (독립·양의 의존). → reject bool 배열. q = 허용 FDR."""
    p = np.asarray(pvals, dtype=float)
    m = p.size
    if m == 0:
        return np.zeros(0, dtype=bool)
    order = np.argsort(p)
    thresh = q * (np.arange(1, m + 1)) / m
    passed = p[order] <= thresh
    reject = np.zeros(m, dtype=bool)
    if passed.any():
        kMax = np.max(np.where(passed)[0])
        reject[order[: kMax + 1]] = True
    return reject


def benjaminiYekutieli(pvals: np.ndarray, q: float = 0.10) -> np.ndarray:
    """BY step-up FDR (임의 의존, c(m)=Σ1/i 보정). BH 보다 보수적."""
    m = np.asarray(pvals).size
    if m == 0:
        return np.zeros(0, dtype=bool)
    cm = float(np.sum(1.0 / np.arange(1, m + 1)))
    return benjaminiHochberg(pvals, q / cm)


def _widePanel(spreadLong: pl.DataFrame) -> tuple[list[str], np.ndarray]:
    """long (surface, week, spread) → (surfaces, W[T x L] NaN 격자). 주 정렬 공통 축."""
    if spreadLong.height == 0:
        return [], np.zeros((0, 0))
    wide = spreadLong.pivot(values="spread", index="week", on="surface", aggregate_function="first").sort("week")
    surfaces = [c for c in wide.columns if c != "week"]
    W = wide.select(surfaces).to_numpy().astype(float)
    return surfaces, W


def _statBootIdx(T: int, meanBlock: float, nBoot: int, rng: np.random.Generator) -> np.ndarray:
    """정상성 부트스트랩(Politis-Romano) 주 인덱스 행렬 (nBoot x T). 기하 블록으로 상관 보존."""
    p = 1.0 / meanBlock
    idx = np.empty((nBoot, T), dtype=int)
    idx[:, 0] = rng.integers(0, T, size=nBoot)
    newBlock = rng.random((nBoot, T)) < p
    starts = rng.integers(0, T, size=(nBoot, T))
    for t in range(1, T):
        idx[:, t] = np.where(newBlock[:, t], starts[:, t], (idx[:, t - 1] + 1) % T)
    return idx


def _bootMoments(W: np.ndarray, idx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """부트스트랩 표본별 표면 (평균, 표준오차) (각 nBoot x L). NaN 무시.

    studentized(pivotal) 부트스트랩용: 재표본마다 자기 se 로 스튜던트화해야 관측·null 이 같은
    척도가 된다 (부트스트랩 분산의 유한표본 하향편의를 상쇄). Romano-Wolf·SPA 권장 방식.
    """
    nBoot, L = idx.shape[0], W.shape[1]
    bMean = np.empty((nBoot, L))
    bSe = np.empty((nBoot, L))
    for b in range(nBoot):
        sample = W[idx[b]]
        cnt = np.sum(~np.isnan(sample), axis=0)
        bMean[b] = np.nanmean(sample, axis=0)
        sd = np.nanstd(sample, axis=0, ddof=1)
        bSe[b] = np.where(cnt > 1, sd / np.sqrt(np.maximum(cnt, 1)), np.nan)
    return bMean, bSe


def _surfaceStats(W: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """표면별 (n, 평균, 표준오차) NaN 무시."""
    n = np.sum(~np.isnan(W), axis=0).astype(float)
    mean = np.nanmean(W, axis=0)
    sd = np.nanstd(W, axis=0, ddof=1)
    se = np.where(n > 1, sd / np.sqrt(np.maximum(n, 1)), np.nan)
    return n, mean, se


def hansenSpa(
    W: np.ndarray, *, nBoot: int = _DEFAULT_BOOT, meanBlock: float = _DEFAULT_MEAN_BLOCK, seed: int = _DEFAULT_SEED
) -> dict:
    """Hansen SPA: 최고 표면이 벤치마크 0 을 진짜 이기는지 (데이터 스누핑 통제 초과확률).

    Args:
        W: (T x L) 표면별 주간 스프레드 (NaN 허용).
        nBoot: 정상성 부트스트랩 반복.
        meanBlock: 기대 블록 길이 (주).
        seed: 결정론 재현 seed.

    Returns:
        {"tSpa", "pConsistent", "nEffModels", "T"}. pConsistent = least-favorable 재중심 null 에서
        max 스튜던트화 통계가 관측치 이상일 확률 (작을수록 진짜 실력). 표면 0 이면 p=1.
    """
    T, L = W.shape
    if T < 2 or L == 0:
        return {"tSpa": 0.0, "pConsistent": 1.0, "nEffModels": L, "T": T}
    n, mean, se = _surfaceStats(W)
    tObs = np.where(se > 0, mean / se, 0.0)  # 표본 스튜던트화 t (정직한 t-통계)
    vObs = max(0.0, float(np.nanmax(tObs)))
    rng = np.random.default_rng(seed)
    idx = _statBootIdx(T, meanBlock, nBoot, rng)
    bMean, bSe = _bootMoments(W, idx)  # (nBoot, L) 각
    # 일치(consistent) 재중심: 매우 음인 표면만 자기 평균 유지, 나머지는 null 경계 0.
    thr = -math.sqrt(2 * math.log(math.log(max(T, 3))))
    muNull = np.where(tObs < thr, mean, 0.0)
    zStar = np.where(bSe > 0, (bMean - mean[None, :] + muNull[None, :]) / bSe, 0.0)  # pivotal 스튜던트
    vStar = np.maximum(0.0, np.nanmax(zStar, axis=1))
    p = float(np.mean(vStar >= vObs))
    return {"tSpa": vObs, "pConsistent": p, "nEffModels": L, "T": T}


def romanoWolf(
    W: np.ndarray,
    *,
    alpha: float = 0.05,
    nBoot: int = _DEFAULT_BOOT,
    meanBlock: float = _DEFAULT_MEAN_BLOCK,
    seed: int = _DEFAULT_SEED,
) -> np.ndarray:
    """Romano-Wolf stepdown (일측 >0, 스튜던트화 max) → 인증(reject) 표면 bool 배열. FWER<=alpha."""
    T, L = W.shape
    reject = np.zeros(L, dtype=bool)
    if T < 2 or L == 0:
        return reject
    _, mean, se = _surfaceStats(W)
    tObs = np.where(se > 0, mean / se, 0.0)
    rng = np.random.default_rng(seed)
    idx = _statBootIdx(T, meanBlock, nBoot, rng)
    bMean, bSe = _bootMoments(W, idx)
    z = np.where(bSe > 0, (bMean - mean[None, :]) / bSe, 0.0)  # pivotal 스튜던트 부트 (nBoot x L)
    active = np.ones(L, dtype=bool)
    while active.any():
        cols = np.where(active)[0]
        maxDist = np.nanmax(z[:, cols], axis=1)
        crit = float(np.quantile(maxDist, 1 - alpha))
        newRej = cols[tObs[cols] > crit]
        if newRej.size == 0:
            break
        reject[newRej] = True
        active[newRej] = False
    return reject


def _pairwiseCorr(W: np.ndarray) -> np.ndarray:
    """표면 간 상관행렬 (쌍별 공통 비결측 주). 겹침 부족은 상관 0."""
    L = W.shape[1]
    R = np.eye(L)
    for i in range(L):
        for j in range(i + 1, L):
            mask = ~np.isnan(W[:, i]) & ~np.isnan(W[:, j])
            if mask.sum() >= 3:
                a, b = W[mask, i], W[mask, j]
                if a.std() > 0 and b.std() > 0:
                    R[i, j] = R[j, i] = float(np.corrcoef(a, b)[0, 1])
    return R


def corrClusterEffN(W: np.ndarray) -> float:
    """Galwey 유효 검정수 Meff = (Σ√λ)² / Σλ (상관 클러스터 수축). DSR nEff·수축 입력."""
    L = W.shape[1]
    if L <= 1:
        return float(L)
    R = _pairwiseCorr(W)
    lam = np.linalg.eigvalsh(R)
    lam = np.clip(lam, 0, None)
    s = lam.sum()
    if s <= 0:
        return float(L)
    return float((np.sqrt(lam).sum() ** 2) / s)


def empiricalBayesShrink(means: np.ndarray, ses: np.ndarray) -> np.ndarray:
    """empirical-Bayes 수축: 표면 추정을 대평균으로 (모멘트법 τ²). 상위 표면 낙관 보정."""
    means = np.asarray(means, dtype=float)
    ses = np.asarray(ses, dtype=float)
    ok = ~np.isnan(means) & ~np.isnan(ses)
    if ok.sum() < 2:
        return means
    mu = float(np.mean(means[ok]))
    tau2 = max(0.0, float(np.var(means[ok], ddof=1) - np.mean(ses[ok] ** 2)))
    out = means.copy()
    b = ses[ok] ** 2 / (ses[ok] ** 2 + tau2 + 1e-18)
    out[ok] = mu + (1 - b) * (means[ok] - mu)
    return out


def certify(
    spreadLong: pl.DataFrame,
    *,
    q: float = 0.10,
    tHurdle: float = FACTOR_ZOO_T,
    alpha: float = 0.05,
    nBoot: int = _DEFAULT_BOOT,
    meanBlock: float = _DEFAULT_MEAN_BLOCK,
    seed: int = _DEFAULT_SEED,
) -> dict:
    """표면별 주간 스프레드 시계열 → 2단 깔때기 인증. → {"surfaces": df, "spaP", "nEff", "T"}.

    Args:
        spreadLong: readingScorecard.surfaceWeeklySpreads 산출 (surface, week, spread). net 인증은
            valueCol="netExNeutral" 로 만든 시계열을 넣는다 (통과 판정 net 기준).
        q: FDR 허용치 (BH/BHY). tHurdle: 운영 상수 t 허들. alpha: RW FWER.
        nBoot / meanBlock / seed: 정상성 부트스트랩 파라미터 (결정론).

    Returns:
        surfaces df (surface, weeks, mean, t, pRaw, fdrPass, byPass, rwCertified, shrunkMean, verdict)
        + spaP(전체 max 통계 초과확률) + nEff(Galwey 유효 검정수). verdict: "인증"(FDR+t허들+RW) |
        "발굴"(FDR+t허들, 미인증) | "동물원구분불가" | "미검증"(주<게이트).
    """
    surfaces, W = _widePanel(spreadLong)
    if not surfaces:
        empty = pl.DataFrame(
            schema={
                "surface": pl.Utf8,
                "weeks": pl.Int64,
                "mean": pl.Float64,
                "t": pl.Float64,
                "pRaw": pl.Float64,
                "fdrPass": pl.Boolean,
                "byPass": pl.Boolean,
                "rwCertified": pl.Boolean,
                "shrunkMean": pl.Float64,
                "verdict": pl.Utf8,
            }
        )
        return {"surfaces": empty, "spaP": 1.0, "nEff": 0.0, "T": 0}
    n, mean, se = _surfaceStats(W)
    tArr = np.where(se > 0, mean / se, 0.0)
    pRaw = _normalTwoSidedP(tArr)
    fdr = benjaminiHochberg(pRaw, q)
    byd = benjaminiYekutieli(pRaw, q)
    rw = romanoWolf(W, alpha=alpha, nBoot=nBoot, meanBlock=meanBlock, seed=seed)
    spa = hansenSpa(W, nBoot=nBoot, meanBlock=meanBlock, seed=seed)
    nEff = corrClusterEffN(W)
    shrunk = empiricalBayesShrink(mean, se)
    verdicts = []
    for k in range(len(surfaces)):
        if n[k] < SCORECARD_MIN_WEEKS:
            verdicts.append("미검증")
        elif fdr[k] and abs(tArr[k]) >= tHurdle and rw[k]:
            verdicts.append("인증")
        elif fdr[k] and abs(tArr[k]) >= tHurdle:
            verdicts.append("발굴")
        else:
            verdicts.append("동물원구분불가")
    df = pl.DataFrame(
        {
            "surface": surfaces,
            "weeks": n.astype(int),
            "mean": mean,
            "t": tArr,
            "pRaw": pRaw,
            "fdrPass": fdr,
            "byPass": byd,
            "rwCertified": rw,
            "shrunkMean": shrunk,
            "verdict": verdicts,
        }
    ).sort("t", descending=True)
    return {"surfaces": df, "spaP": spa["pConsistent"], "nEff": nEff, "T": W.shape[0]}
