"""가정 격자 : 결합 가정 원장 + 벡터화 재조합 → 성과 행렬 (sweep 입력) (L2.5 simulate).

sweep 통계(PBO·DSR·강건 선정)는 이미 만들어진 성과 행렬을 소비한다. 이 모듈이 그 행렬을
만든다 (06 §5). 결합 가정(표면 가중 스킴·게이트 강도·합의 임계·지평)을 AssumptionLedgerRow
경량 계약으로 선언하고(단위·기간·source·status·반증조건 필수), 격자 수백 벌을 판독 행렬(주 1회
계산) 위의 재조합으로 벡터화한다. 주별로 각 config 의 표면 가중 행렬을 판독 기여에 곱해 합의를
내고 상위 K 를 뽑아 성과를 낸다. 격자가 커도 판독 행렬 재사용이라 replay 가 분 단위 (P0 실측:
17년 x 200벌 12.2초). 선정은 강건성(대다수 가정 median)이지 최고 가정이 아니다.

- ``AssumptionLedgerRow`` : 결합 가정 1행 계약 (반증조건=사전등록 protocol).
- ``assumptionGrid`` : 스킴 x 임계 x 지평 데카르트 격자 → config 목록.
- ``applyGrid`` : 판독 행렬 위 벡터화 재조합 → (perf configs x weeks, configScores codes x configs).
- ``sealAssumptions`` : 가정 벌 주간 봉인 (issuedLive, 과거 sweep 은 bootstrap 영구표기).

Layer: L2.5 simulate. numpy · polars · readingLedger(봉인) 만 의존.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path

import numpy as np
import polars as pl

ASSUMPTION_SUBDIR = "assumptions"


@dataclass(frozen=True)
class AssumptionLedgerRow:
    """결합 가정 1행. 단위·기간 필수, source·status·반증조건(사전등록 protocol) 필수 (02 §2.5 규율).

    Args:
        assumptionId: 가정 식별자 (config 내 고유).
        dimension: 가정 축 ("weightScheme"|"consensusTopK"|"minSurfaces"|"horizon"|"scenarioPreset").
        value: 가정 값 (문자열화).
        unit: 값의 단위 ("scheme"|"count"|"tradingDays"|"preset" 등). 필수.
        period: 적용 기간/빈도 ("weekly" 등). 필수.
        source: 근거 계보 (예 "certify:rwCertified" | "preset:adverse"). 필수.
        status: "candidate" | "live" | "bootstrap". bootstrap = 과거 sweep 영구표기.
        falsification: 반증조건 (사전등록 protocol. 예 "OOS median <= 0 3분기 연속"). 필수.
    """

    assumptionId: str
    dimension: str
    value: str
    unit: str
    period: str
    source: str
    status: str
    falsification: str


@dataclass(frozen=True)
class GridConfig:
    """가정 격자 1 config: 파라미터 + 그 config 를 구성하는 AssumptionLedgerRow 들."""

    configId: str
    weightScheme: str
    weights: dict
    topK: int
    minSurfaces: int
    horizon: int
    scenarioPreset: str
    rows: tuple[AssumptionLedgerRow, ...] = field(default_factory=tuple)


def assumptionGrid(
    weightSchemes: dict[str, dict],
    *,
    topKs: tuple[int, ...] = (10, 20),
    minSurfaces: tuple[int, ...] = (1, 2),
    horizons: tuple[int, ...] = (5,),
    scenarioPresets: tuple[str, ...] = ("baseline",),
    falsification: str = "OOS 중앙값 <= 0 3분기 연속",
) -> list[GridConfig]:
    """스킴 x topK x minSurfaces x 지평 x 프리셋 데카르트 격자 → config 목록 (각 가정 원장 포함).

    Args:
        weightSchemes: {schemeName: {surface: weight}} 표면 가중 스킴 (예 equal·certifiedOnly·tWeighted).
        topKs / minSurfaces / horizons / scenarioPresets: 격자 축.
        falsification: 사전등록 반증조건 (전 config 공통).

    Returns:
        GridConfig 목록. 각 config 는 5축 값을 AssumptionLedgerRow 로 선언한다.
    """
    configs: list[GridConfig] = []
    for scheme, topK, minS, hz, preset in product(weightSchemes, topKs, minSurfaces, horizons, scenarioPresets):
        cid = f"{scheme}|k{topK}|m{minS}|h{hz}|{preset}"
        rows = (
            AssumptionLedgerRow(
                cid, "weightScheme", scheme, "scheme", "weekly", f"scheme:{scheme}", "candidate", falsification
            ),
            AssumptionLedgerRow(cid, "consensusTopK", str(topK), "count", "weekly", "grid", "candidate", falsification),
            AssumptionLedgerRow(cid, "minSurfaces", str(minS), "count", "weekly", "grid", "candidate", falsification),
            AssumptionLedgerRow(cid, "horizon", str(hz), "tradingDays", "weekly", "grid", "candidate", falsification),
            AssumptionLedgerRow(
                cid, "scenarioPreset", preset, "preset", "weekly", f"preset:{preset}", "candidate", falsification
            ),
        )
        configs.append(GridConfig(cid, scheme, weightSchemes[scheme], topK, minS, hz, preset, rows))
    return configs


def applyGrid(readings: pl.DataFrame, labels: pl.DataFrame, configs: list[GridConfig]) -> dict:
    """판독 행렬 위 벡터화 재조합 → 성과 행렬. sweep(PBO·DSR·robust) 직결 입력.

    Args:
        readings: (code, week, surface, direction, score) 판독.
        labels: weeklyLabels (code, week, exNeutral).
        configs: assumptionGrid 산출.

    Returns:
        {"perf": (nConfigs x nWeeks) 주별 상위K 평균 초과, "configScores": (nCodes x nConfigs) 종목별
        선택 빈도, "weeks": [...], "codes": [...], "configIds": [...]}. 주별로 표면 가중 행렬을
        판독 기여에 곱해 합의를 내는 재조합 (판독 재계산 0).
    """
    surfaces = readings["surface"].unique().sort().to_list()
    sIdx = {s: i for i, s in enumerate(surfaces)}
    weightMat = np.array([[float(c.weights.get(s, 0.0)) for c in configs] for s in surfaces])  # (nSurfaces x nConfigs)
    topKs = np.array([c.topK for c in configs])
    minS = np.array([c.minSurfaces for c in configs])
    weeks = sorted(set(readings["week"].to_list()) & set(labels["week"].to_list()))
    codes = readings["code"].unique().sort().to_list()
    cIdx = {c: i for i, c in enumerate(codes)}
    nConfigs, nWeeks, nCodes = len(configs), len(weeks), len(codes)
    perf = np.full((nConfigs, nWeeks), np.nan)
    selectCount = np.zeros((nCodes, nConfigs))
    lab = labels.select("code", "week", "exNeutral")
    r = readings.with_columns(strength=(pl.col("score") - 0.5).abs() * 2 * pl.col("direction"))
    for wi, w in enumerate(weeks):
        rw = r.filter(pl.col("week") == w)
        if rw.height == 0:
            continue
        lw = lab.filter(pl.col("week") == w)
        exMap = dict(zip(lw["code"].to_list(), lw["exNeutral"].to_list()))
        wkCodes = rw["code"].unique().sort().to_list()
        localIdx = {c: i for i, c in enumerate(wkCodes)}
        contrib = np.zeros((len(wkCodes), len(surfaces)))
        nSurfHit = np.zeros((len(wkCodes), len(surfaces)))
        for row in rw.iter_rows(named=True):
            li, si = localIdx[row["code"]], sIdx[row["surface"]]
            contrib[li, si] = row["strength"]
            nSurfHit[li, si] = 1.0
        consensus = contrib @ weightMat  # (nWkCodes x nConfigs)
        nFired = nSurfHit @ (weightMat != 0).astype(float)  # config 별 발화 표면 수
        exVec = np.array([exMap.get(c, np.nan) for c in wkCodes])
        for ci in range(nConfigs):
            elig = nFired[:, ci] >= minS[ci]
            if elig.sum() == 0:
                continue
            score = np.where(elig, consensus[:, ci], -np.inf)
            k = min(int(topKs[ci]), int(elig.sum()))
            top = np.argsort(score)[::-1][:k]
            topEx = exVec[top]
            perf[ci, wi] = float(np.nanmean(topEx)) if np.isfinite(topEx).any() else np.nan
            for li in top:
                selectCount[cIdx[wkCodes[li]], ci] += 1.0
    return {
        "perf": perf,
        "configScores": selectCount / max(nWeeks, 1),
        "weeks": weeks,
        "codes": codes,
        "configIds": [c.configId for c in configs],
    }


def _assumptionDir(baseDir: Path | None) -> Path:
    if baseDir is not None:
        return baseDir / ASSUMPTION_SUBDIR
    root = os.environ.get("DARTLAB_DATA_DIR")
    return (Path(root) if root else Path("data")) / ASSUMPTION_SUBDIR


def sealAssumptions(
    configs: list[GridConfig],
    sweepStats: dict,
    *,
    week: int,
    issuedLive: bool,
    issuedAt: str,
    baseDir: Path | None = None,
) -> Path:
    """가정 벌 주간 봉인 → assumptions_{yyyy}.parquet append. 과거 sweep 은 issuedLive=False.

    Args:
        configs: 봉인할 격자.
        sweepStats: {configId: {"pbo","dsr","oosMedian",...}} config 별 sweep 산출.
        week / issuedLive / issuedAt: 봉인 메타. baseDir: 원장 루트 override.

    Returns:
        기록 경로. 판독 원장과 동형 규율 (append-only, issuedLive 권위=라이브만).
    """
    rows = []
    for c in configs:
        st = sweepStats.get(c.configId, {})
        rows.append(
            {
                "week": week,
                "configId": c.configId,
                "weightScheme": c.weightScheme,
                "topK": c.topK,
                "minSurfaces": c.minSurfaces,
                "horizon": c.horizon,
                "scenarioPreset": c.scenarioPreset,
                "pbo": float(st.get("pbo", float("nan"))),
                "dsr": float(st.get("dsr", float("nan"))),
                "oosMedian": float(st.get("oosMedian", float("nan"))),
                "issuedLive": issuedLive,
                "issuedAt": issuedAt,
                "falsification": c.rows[0].falsification if c.rows else "",
            }
        )
    base = _assumptionDir(baseDir)
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"assumptions_{week // 100}.parquet"
    new = pl.DataFrame(rows)
    if path.exists():
        new = pl.concat([pl.read_parquet(path), new.select(pl.read_parquet(path).columns)], how="vertical")
    tmp = path.with_suffix(".parquet.tmp")
    new.write_parquet(tmp)
    tmp.replace(path)
    return path
