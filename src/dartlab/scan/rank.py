"""종목 규모 랭크.

전체 시장 + 섹터 내 순위를 산출한다.
첫 호출 시 전체 종목을 순회해서 스냅샷을 생성하고 로컬 캐시에 저장.
이후 호출은 캐시에서 조회 (빌드 2분 → 조회 즉시).
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from dartlab.core.dataConfig import DATA_RELEASES


@dataclass
class RankInfo:
    """단일 종목의 랭크 정보."""

    stockCode: str
    corpName: str
    sector: str
    industryGroup: str

    revenue: Optional[float] = None
    totalAssets: Optional[float] = None
    revenueGrowth3Y: Optional[float] = None

    revenueRank: Optional[int] = None
    revenueTotal: int = 0
    revenueRankInSector: Optional[int] = None
    revenueSectorTotal: int = 0

    assetRank: Optional[int] = None
    assetTotal: int = 0
    assetRankInSector: Optional[int] = None
    assetSectorTotal: int = 0

    growthRank: Optional[int] = None
    growthTotal: int = 0
    growthRankInSector: Optional[int] = None
    growthSectorTotal: int = 0

    sizeClass: str = ""

    def __repr__(self):
        revStr = f"매출 {self.revenueRank}/{self.revenueTotal}" if self.revenueRank else "매출 N/A"
        secStr = f"섹터 {self.revenueRankInSector}/{self.revenueSectorTotal}" if self.revenueRankInSector else ""
        return f"RankInfo({self.corpName}, {revStr}, {secStr}, {self.sizeClass})"


def _cacheDir() -> Path:
    from dartlab import config

    return Path(config.dataDir) / "_cache"


def _cachePath() -> Path:
    return _cacheDir() / "rank_snapshot.json"


def _financeExists(stockCode: str) -> bool:
    from dartlab import config

    dataDir = Path(config.dataDir) / DATA_RELEASES["finance"]["dir"]
    return (dataDir / f"{stockCode}.parquet").exists()


def buildSnapshot(*, verbose: bool = True) -> dict[str, RankInfo]:
    """전체 종목 랭크 스냅샷 생성 및 캐시 저장.

    Returns:
        stockCode → RankInfo 매핑 dict.
    """
    from dartlab.core.sector import classify
    from dartlab.core.finance.ratios import calcRatios
    from dartlab.gather.listing import getKindList
    from dartlab.providers.dart.finance.pivot import buildAnnual

    kindDf = getKindList()
    codes = kindDf["종목코드"].to_list()
    names = kindDf["회사명"].to_list()
    industries = kindDf["업종"].to_list() if "업종" in kindDf.columns else [None] * len(codes)
    products = kindDf["주요제품"].to_list() if "주요제품" in kindDf.columns else [None] * len(codes)

    records: list[dict] = []
    for i, code in enumerate(codes):
        if verbose and i % 500 == 0:
            logger.info("[rank] %d/%d...", i, len(codes))

        info = classify(names[i], industries[i], products[i])

        rec = {
            "stockCode": code,
            "corpName": names[i],
            "sector": info.sector.value,
            "industryGroup": info.industryGroup.value,
            "revenue": None,
            "totalAssets": None,
            "revenueGrowth3Y": None,
        }

        if _financeExists(code):
            aResult = buildAnnual(code)
            if aResult is not None:
                aSeries, _ = aResult
                ratios = calcRatios(aSeries)
                if ratios.revenueTTM and ratios.revenueTTM > 0:
                    rec["revenue"] = ratios.revenueTTM
                rec["totalAssets"] = ratios.totalAssets
                rec["revenueGrowth3Y"] = ratios.revenueGrowth3Y

        records.append(rec)

    revSorted = sorted(
        [r for r in records if r["revenue"] is not None],
        key=lambda x: x["revenue"],
        reverse=True,
    )
    assetSorted = sorted(
        [r for r in records if r["totalAssets"] is not None and r["totalAssets"] > 0],
        key=lambda x: x["totalAssets"],
        reverse=True,
    )
    growthSorted = sorted(
        [r for r in records if r["revenueGrowth3Y"] is not None],
        key=lambda x: x["revenueGrowth3Y"],
        reverse=True,
    )

    nRev = len(revSorted)
    nAsset = len(assetSorted)
    nGrowth = len(growthSorted)

    revRank = {r["stockCode"]: i + 1 for i, r in enumerate(revSorted)}
    assetRank = {r["stockCode"]: i + 1 for i, r in enumerate(assetSorted)}
    growthRank = {r["stockCode"]: i + 1 for i, r in enumerate(growthSorted)}

    from collections import defaultdict

    sectorRevLists: dict[str, list[str]] = defaultdict(list)
    sectorAssetLists: dict[str, list[str]] = defaultdict(list)
    sectorGrowthLists: dict[str, list[str]] = defaultdict(list)

    for r in revSorted:
        sectorRevLists[r["sector"]].append(r["stockCode"])
    for r in assetSorted:
        sectorAssetLists[r["sector"]].append(r["stockCode"])
    for r in growthSorted:
        sectorGrowthLists[r["sector"]].append(r["stockCode"])

    sectorRevRank: dict[str, tuple[int, int]] = {}
    for sector, codeList in sectorRevLists.items():
        for i, c in enumerate(codeList):
            sectorRevRank[c] = (i + 1, len(codeList))

    sectorAssetRank: dict[str, tuple[int, int]] = {}
    for sector, codeList in sectorAssetLists.items():
        for i, c in enumerate(codeList):
            sectorAssetRank[c] = (i + 1, len(codeList))

    sectorGrowthRank: dict[str, tuple[int, int]] = {}
    for sector, codeList in sectorGrowthLists.items():
        for i, c in enumerate(codeList):
            sectorGrowthRank[c] = (i + 1, len(codeList))

    result: dict[str, RankInfo] = {}
    for rec in records:
        code = rec["stockCode"]
        rr = revRank.get(code)
        ar = assetRank.get(code)
        gr = growthRank.get(code)
        srr = sectorRevRank.get(code)
        sar = sectorAssetRank.get(code)
        sgr = sectorGrowthRank.get(code)

        sizeClass = ""
        if rr is not None:
            pct = rr / nRev
            sizeClass = "large" if pct <= 0.10 else "mid" if pct <= 0.30 else "small"

        ri = RankInfo(
            stockCode=code,
            corpName=rec["corpName"],
            sector=rec["sector"],
            industryGroup=rec["industryGroup"],
            revenue=rec["revenue"],
            totalAssets=rec["totalAssets"],
            revenueGrowth3Y=rec["revenueGrowth3Y"],
            revenueRank=rr,
            revenueTotal=nRev,
            revenueRankInSector=srr[0] if srr else None,
            revenueSectorTotal=srr[1] if srr else 0,
            assetRank=ar,
            assetTotal=nAsset,
            assetRankInSector=sar[0] if sar else None,
            assetSectorTotal=sar[1] if sar else 0,
            growthRank=gr,
            growthTotal=nGrowth,
            growthRankInSector=sgr[0] if sgr else None,
            growthSectorTotal=sgr[1] if sgr else 0,
            sizeClass=sizeClass,
        )
        result[code] = ri

    cacheDir = _cacheDir()
    cacheDir.mkdir(parents=True, exist_ok=True)
    cachePath = _cachePath()
    serializable = {code: asdict(ri) for code, ri in result.items()}
    cachePath.write_text(json.dumps(serializable, ensure_ascii=False), encoding="utf-8")

    if verbose:
        logger.info("[rank] %d종목 스냅샷 저장: %s", len(result), cachePath)

    return result


def _loadCache() -> dict[str, RankInfo] | None:
    cachePath = _cachePath()
    if not cachePath.exists():
        return None
    raw = json.loads(cachePath.read_text(encoding="utf-8"))
    result = {}
    for code, data in raw.items():
        result[code] = RankInfo(**data)
    return result


_SNAPSHOT: dict[str, RankInfo] | None = None
_SNAPSHOT_LOCK = threading.Lock()


def _ensureSnapshot() -> dict[str, RankInfo] | None:
    global _SNAPSHOT
    if _SNAPSHOT is not None:
        return _SNAPSHOT
    with _SNAPSHOT_LOCK:
        if _SNAPSHOT is not None:
            return _SNAPSHOT
        _SNAPSHOT = _loadCache()
    return _SNAPSHOT


def getRank(stockCode: str) -> RankInfo | None:
    """종목 랭크 정보 조회. 스냅샷이 없으면 None."""
    snap = _ensureSnapshot()
    if snap is None:
        return None
    return snap.get(stockCode)


def getRankOrBuild(stockCode: str, *, verbose: bool = True) -> RankInfo | None:
    """종목 랭크 정보 조회. 스냅샷이 없으면 빌드 후 조회."""
    global _SNAPSHOT
    snap = _ensureSnapshot()
    if snap is None:
        if verbose:
            logger.info("[dartlab] 랭크 스냅샷이 없습니다. 전체 종목 빌드를 시작합니다...")
        _SNAPSHOT = buildSnapshot(verbose=verbose)
    return _SNAPSHOT.get(stockCode)
