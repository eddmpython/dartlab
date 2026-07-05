"""주간 오케스트레이션 : 판독 발행 → 봉인 → 해시체인 블록 (L2.5 simulate).

전 모듈을 주간 사이클로 묶는다 (06 §7b 공개 봉인 원장). 대상 주의 판독을 발행·봉인하고
(readingCycle), 성적표·파생 뷰를 산출한 뒤, 주 1블록 해시체인으로 봉인한다. 채점은 다음
블록에서 "직전 블록 + 공개 데이터"의 순수함수로 계산되므로 외부인이 replay 로 재검산 가능하다.
선택적 앵커(OpenTimestamps)는 운영 런북에서 블록 해시에 적용한다 (본 모듈은 해시체인까지).

블록 = {week, market, 판독 요약, 성적표, board, prevHash, 코드버전, issuedAt}. hash =
SHA256(정렬 JSON). 소급 편집은 후속 블록 해시를 전부 깨뜨린다 (git-like 변조 증거).

Layer: L2.5 simulate. readingCycle·readingScorecard·board·hashlib(stdlib) 만 의존.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from dartlab.simulate import board as _board
from dartlab.simulate import readingCycle as _cycle
from dartlab.simulate import readingLedger as _ledger
from dartlab.simulate import readingScorecard as _sc
from dartlab.simulate import table as _table

BLOCK_SUBDIR = "readingBlocks"
CODE_VERSION = "reading-v1"


def _nowUtc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="minutes")


def hashBlock(block: dict) -> str:
    """블록의 결정론 SHA256 (정렬 JSON, prevHash 포함이라 체인 변조 증거)."""
    canonical = json.dumps(block, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def buildBlock(
    week: int,
    market: str,
    readings: pl.DataFrame,
    scorecard: pl.DataFrame,
    boardTop: pl.DataFrame,
    *,
    prevHash: str = "",
    issuedAt: str | None = None,
) -> dict:
    """주간 블록 조립 + 해시. 판독은 요약(표면별 수·방향 분포)만 담아 블록을 가볍게 유지."""
    surfSummary = (
        {}
        if readings.height == 0
        else {
            r["surface"]: {"n": r["n"], "up": r["up"], "down": r["down"]}
            for r in readings.group_by("surface")
            .agg(
                n=pl.len(),
                up=(pl.col("direction") == 1).sum(),
                down=(pl.col("direction") == -1).sum(),
            )
            .iter_rows(named=True)
        }
    )
    body = {
        "week": week,
        "market": market,
        "codeVersion": CODE_VERSION,
        "issuedAt": issuedAt or _nowUtc(),
        "readingCount": readings.height,
        "surfaceSummary": surfSummary,
        "scorecard": scorecard.to_dicts() if scorecard.height else [],
        "boardTop": boardTop.select("code", "consensus").to_dicts() if boardTop.height else [],
        "prevHash": prevHash,
        "disclaimer": _board.DISCLAIMER,
    }
    body["hash"] = hashBlock(body)
    return body


def _blockDir(baseDir: Path | None) -> Path:
    root = _ledger.ledgerDir(baseDir).parent
    return root / BLOCK_SUBDIR


def _lastHash(blockDir: Path) -> str:
    files = sorted(blockDir.glob("block_*.json"))
    if not files:
        return ""
    return json.loads(files[-1].read_text(encoding="utf-8")).get("hash", "")


def runWeek(
    *,
    market: str = "KR",
    week: int | None = None,
    live: bool = True,
    baseDir: Path | None = None,
    dataDir: Path | None = None,
    matrices: tuple | None = None,
    labels: pl.DataFrame | None = None,
    surfaceWeights: dict[str, float] | None = None,
) -> dict:
    """대상 주 판독 발행·봉인 → 성적표·board → 해시체인 블록. 반환 = 블록 dict.

    Args:
        market: 시장 라벨.
        week: 대상 주 (None = 최신).
        live: False = backfill.
        baseDir: 원장/블록 루트 override.
        dataDir: 데이터 SSOT 루트 override.
        matrices: 주입 (weekMap, weekEnd, priceM, fundM, eventM) (테스트용).
        labels: 방향화·채점 라벨 (테스트용).
        surfaceWeights: board 합의 가중 (예 AdaHedge).

    Returns:
        봉인 블록 dict (hash·prevHash 포함). 미발행(판독 0)이면 readingCount=0 블록.
    """
    weekMap, weekEnd, priceM, fundM, eventM = matrices or _cycle._buildMatrices(dataDir)
    lab = labels if labels is not None else _sc.weeklyLabels(weekEnd, _table.dailyPrices(dataDir))
    directionByType = _sc.deriveEventDirections(eventM, lab)
    _cycle.issueReadings(
        market=market,
        week=week,
        live=live,
        baseDir=baseDir,
        matrices=(weekMap, weekEnd, priceM, fundM, eventM),
        directionByType=directionByType,
    )
    if week is None:
        led = _ledger.readReadings(baseDir=baseDir)
        week = int(led["week"].max()) if led is not None and led.height else 0
    weekReadings = _ledger.readReadings(week=week, baseDir=baseDir)
    if weekReadings is None:
        weekReadings = pl.DataFrame(
            schema={"code": pl.Utf8, "surface": pl.Utf8, "direction": pl.Int64, "score": pl.Float64}
        )
    if "code" not in weekReadings.columns and "stockCode" in weekReadings.columns:
        weekReadings = weekReadings.rename({"stockCode": "code"})
    card = (
        _sc.scorecard(weekReadings.select("code", "surface", "direction", "score").with_columns(week=pl.lit(week)), lab)
        if weekReadings.height
        else pl.DataFrame()
    )
    boardTop = (
        _board.board100(
            weekReadings.select("code", "surface", "direction", "score").with_columns(week=pl.lit(week)),
            surfaceWeights=surfaceWeights,
            n=100,
        )
        if weekReadings.height
        else pl.DataFrame(schema={"code": pl.Utf8, "consensus": pl.Float64})
    )
    blockDir = _blockDir(baseDir)
    blockDir.mkdir(parents=True, exist_ok=True)
    block = buildBlock(week, market, weekReadings, card, boardTop, prevHash=_lastHash(blockDir))
    (blockDir / f"block_{week}.json").write_text(json.dumps(block, ensure_ascii=False, indent=2), encoding="utf-8")
    return block
